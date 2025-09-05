from __future__ import annotations
import time
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from ..db import get_session
from ..models import Document, DocumentVersion, Chunk, User
from ..dependencies import get_current_user
from ..services.indexing import search_versions
from ..services.audit import log as audit_log
from ..config import TOP_K

router = APIRouter(tags=["search"])


class SearchResult(BaseModel):
    doc_id: int
    title: str
    version: int
    page: int
    snippet: str
    score: float


class SearchEnvelope(BaseModel):
    results: List[SearchResult]
    total_results: int
    query_time: float


@router.get("/search", response_model=SearchEnvelope)
def search(q: str = Query(...), k: int = Query(TOP_K), user: User = Depends(get_current_user), session = Depends(get_session)):
    t0 = time.time()
    docs = session.exec(select(Document).where((Document.owner_id == user.id) | (user.role.in_(["admin", "support"])))).all()
    version_ids = [d.current_version_id for d in docs if d.current_version_id]
    hits = search_versions(q, version_ids, k=k, session=session) if version_ids else []
    out: List[SearchResult] = []
    for vid, idx, score in hits:
        ver = session.get(DocumentVersion, vid)
        if not ver:
            continue
        doc = session.get(Document, ver.document_id)
        if not doc:
            continue
        ch = session.exec(select(Chunk).where((Chunk.doc_version_id == vid) & (Chunk.chunk_index == idx))).first()
        snippet = ch.content[:240] if ch else ""
        out.append(SearchResult(doc_id=doc.id, title=doc.name, version=ver.version, page=(ch.page if ch and ch.page else 1), snippet=snippet, score=float(score)))
    elapsed = time.time() - t0
    audit_log(user.id, "search", "document", None, {"q": q, "k": k, "t": elapsed, "hits": len(out)})
    return SearchEnvelope(results=out, total_results=len(out), query_time=elapsed) 