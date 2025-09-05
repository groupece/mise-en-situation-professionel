from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from ..db import get_session
from ..models import Document, DocumentVersion, Chunk, User
from ..dependencies import get_current_user
from ..services.extract import extract_by_mime
from ..services.chunking import chunk_pages
from ..services.indexing import build_index_for_version
from ..services.audit import log as audit_log

router = APIRouter(prefix="/documents", tags=["ingest"])  # share prefix


class IngestResult(BaseModel):
    document_id: int
    pages_processed: int
    chunk_count: int
    text_len: int
    status: str


@router.post("/{doc_id}/ingest", response_model=IngestResult)
def ingest_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    doc = session.get(Document, doc_id)
    if not doc or (doc.owner_id != user.id and user.role not in ("admin", "support")):
        raise HTTPException(status_code=404, detail="Document not found")

    path = Path(doc.path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Stored file not found")

    pages = extract_by_mime(path, doc.mime)
    chunks = chunk_pages(pages, max_chars=800, overlap=80)

    last_version_num = 1
    if doc.current_version_id:
        current_ver = session.get(DocumentVersion, doc.current_version_id)
        if current_ver:
            last_version_num = (current_ver.version or 1)
    new_version_num = last_version_num + 1 if doc.status == "processed" else 1

    ver = DocumentVersion(
        document_id=doc.id,
        version=new_version_num,
        text_len=sum(len(p or "") for p in pages),
        chunk_count=len(chunks),
        embedding_model="",
        doc_sha256=doc.sha256,
    )
    session.add(ver)
    session.commit()
    session.refresh(ver)

    for idx, c in enumerate(chunks):
        session.add(Chunk(
            doc_version_id=ver.id,
            chunk_index=idx,
            content=c["content"],
            page=c.get("page"),
            start_char=c.get("start_char"),
            end_char=c.get("end_char"),
            vector_path=None,
        ))
    session.commit()

    doc.status = "processed"
    doc.current_version_id = ver.id
    session.add(doc)
    session.commit()
    session.refresh(doc)

    build_index_for_version(ver.id, session=session)

    audit_log(user.id, "ingest", "document", doc.id, {"version": ver.version, "chunks": len(chunks)})

    return IngestResult(
        document_id=doc.id,
        pages_processed=len(pages),
        chunk_count=len(chunks),
        text_len=ver.text_len,
        status=doc.status,
    ) 