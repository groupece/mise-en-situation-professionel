from __future__ import annotations
import hashlib
from uuid import uuid4
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from ..config import STORAGE_DIR
from ..db import get_session
from ..models import Document, DocumentVersion, User
from ..dependencies import get_current_user
from ..services.audit import log as audit_log

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentRead(BaseModel):
    id: int
    name: str
    type: str
    size: int
    uploaded_at: str
    status: str


class DocumentDetail(DocumentRead):
    filename: str
    version: int


ALLOWED_MIME = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXT = {".pdf", ".txt", ".docx"}
MAX_SIZE_MB = 25


def _safe_name(name: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in name)
    return keep.strip() or f"file_{uuid4().hex}"


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


# --- Nouveau: schéma pour le renommage ---
class RenameRequest(BaseModel):
    new_name: str


def _guess_type(upload: UploadFile) -> str:
    t = (upload.content_type or "").split(";")[0].strip()
    return t or "application/octet-stream"


@router.post("", response_model=DocumentDetail, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    ext = Path(file.filename).suffix.lower()
    ctype = _guess_type(file)
    if ext not in ALLOWED_EXT and ctype not in ALLOWED_MIME:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type")
    content = file.file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=422, detail="Empty file")
    if size > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (> {MAX_SIZE_MB} MB)")

    digest = _sha256_bytes(content)
    doc_dir = STORAGE_DIR / uuid4().hex
    doc_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(file.filename or "document")
    dest = doc_dir / safe
    with open(dest, "wb") as f:
        f.write(content)

    doc = Document(
        owner_id=user.id,
        name=safe,
        filename=file.filename or safe,
        path=str(dest),
        mime=ctype,
        size=size,
        sha256=digest,
        status="uploaded",
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    ver = DocumentVersion(
        document_id=doc.id,
        version=1,
        text_len=0,
        chunk_count=0,
        embedding_model="",
        doc_sha256=digest,
    )
    session.add(ver)
    session.commit()
    session.refresh(ver)

    doc.current_version_id = ver.id
    session.add(doc)
    session.commit()
    session.refresh(doc)

    audit_log(user.id, "upload", "document", doc.id, {"mime": ctype, "size": size})

    return DocumentDetail(
        id=doc.id,
        name=doc.name,
        type=doc.mime,
        size=doc.size,
        uploaded_at=doc.uploaded_at.isoformat(),
        status=doc.status,
        filename=doc.filename,
        version=ver.version,
    )


@router.get("", response_model=List[DocumentRead])
def list_documents(
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    docs = session.exec(select(Document).where(Document.owner_id == user.id).order_by(Document.uploaded_at.desc())).all()
    return [
        DocumentRead(
            id=d.id,
            name=d.name,
            type=d.mime,
            size=d.size,
            uploaded_at=d.uploaded_at.isoformat(),
            status=d.status,
        )
        for d in docs
    ]


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    doc = session.get(Document, doc_id)
    if not doc or (doc.owner_id != user.id and user.role not in ("admin", "support")):
        raise HTTPException(status_code=404, detail="Document not found")
    ver = session.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    return DocumentDetail(
        id=doc.id,
        name=doc.name,
        type=doc.mime,
        size=doc.size,
        uploaded_at=doc.uploaded_at.isoformat(),
        status=doc.status,
        filename=doc.filename,
        version=(ver.version if ver else 1),
    )


# --- Nouveau: endpoint rename ---
@router.put("/{doc_id}/rename", response_model=DocumentDetail)
def rename_document(
    doc_id: int,
    payload: RenameRequest,
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    # 1) contrôle d'accès : même règle que get_document
    doc = session.get(Document, doc_id)
    if not doc or (doc.owner_id != user.id and user.role not in ("admin", "support")):
        raise HTTPException(status_code=404, detail="Document not found")

    # 2) validation payload (voix étudiante: on évite les renommages vides qui embrouillent l'UI)
    raw = (payload.new_name or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail="new_name is required")

    # 3) calcul du nouveau nom en conservant l'extension d'origine
    #    (voix étudiante: on force l'extension source pour ne pas casser les viewers)
    orig_ext = Path(doc.name).suffix or Path(doc.filename).suffix or Path(doc.path).suffix
    base = Path(_safe_name(raw)).stem  # on nettoie et on retire toute extension fournie
    candidate_name = f"{base}{orig_ext}"

    current_path = Path(doc.path)
    parent_dir = current_path.parent
    candidate_path = parent_dir / candidate_name

    # 4) éviter les collisions: suffixes _1.._100
    if candidate_name != current_path.name and candidate_path.exists():
        found = False
        for i in range(1, 101):
            trial_name = f"{base}_{i}{orig_ext}"
            trial_path = parent_dir / trial_name
            if not trial_path.exists():
                candidate_name = trial_name
                candidate_path = trial_path
                found = True
                break
        if not found:
            # on renonce côté FS, mais on pourra toujours mettre à jour le nom d'affichage
            candidate_path = current_path  # évite tentative de rename

    # 5) tentative de renommage physique (best-effort)
    fs_renamed = False
    if current_path.exists() and candidate_path != current_path:
        try:
            current_path.rename(candidate_path)
            fs_renamed = True
        except Exception:
            fs_renamed = False

    # 6) mise à jour DB
    doc.name = candidate_name
    if fs_renamed:
        doc.path = str(candidate_path)
    session.add(doc)
    session.commit()
    session.refresh(doc)

    audit_log(user.id, "rename", "document", doc.id, {"fs_renamed": fs_renamed, "new_name": candidate_name})

    ver = session.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    return DocumentDetail(
        id=doc.id,
        name=doc.name,
        type=doc.mime,
        size=doc.size,
        uploaded_at=doc.uploaded_at.isoformat(),
        status=doc.status,
        filename=doc.filename,
        version=(ver.version if ver else 1),
    )


# --- Nouveau: suppression d'un document ---
@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    user: User = Depends(get_current_user),
    session = Depends(get_session),
):
    # 1) contrôle d'accès et existence
    doc = session.get(Document, doc_id)
    if not doc or (doc.owner_id != user.id and user.role not in ("admin", "support")):
        raise HTTPException(status_code=404, detail="Document not found")

    # Note étudiante: on détache d'abord la version courante pour éviter un souci de FK sur certaines DB.
    doc.current_version_id = None
    session.add(doc)
    session.commit()

    # 2) collecter et supprimer les versions liées
    versions = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == doc.id)).all()
    n_versions = len(versions)

    # Option: suppression d'artefacts d'index par version (best-effort, sans dépendance)
    from ..config import INDEX_DIR
    index_removed = 0
    for ver in versions:
        try:
            idx_path = INDEX_DIR / f"{ver.id}.pkl"
            if idx_path.exists():
                idx_path.unlink(missing_ok=True)  # Py3.8+: on garde try/except de toute façon
                index_removed += 1
        except Exception:
            pass
        session.delete(ver)
    session.commit()

    # 3) suppression du fichier sur disque (best-effort)
    had_file = False
    fs_removed = False
    try:
        p = Path(doc.path)
        if p.exists() and p.is_file():
            had_file = True
            # Note étudiante: on tolère l'absence du fichier (il peut avoir été nettoyé manuellement).
            p.unlink(missing_ok=True)
            fs_removed = True
    except Exception:
        fs_removed = False

    # 4) supprimer le document
    session.delete(doc)
    session.commit()

    # Note étudiante: on supprime aussi les versions/artefacts pour éviter des traces fantômes dans la recherche.
    try:
        audit_log(user.id, "document.delete", "document", doc_id, {"had_file": had_file, "fs_removed": fs_removed, "versions": n_versions, "index_removed": index_removed})
    except Exception:
        pass

    return None 