from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import select
from ..db import get_session
from ..models import Document, DocumentVersion, Chunk, Query as QueryModel, Answer as AnswerModel, AnswerCitation as AnswerCitationModel, User
from ..dependencies import get_current_user
from ..services.indexing import search_versions
from ..services.audit import log as audit_log
from ..config import TOP_K

router = APIRouter(prefix="/answers", tags=["answers"])


class AnswerRequest(BaseModel):
    question: str


class Citation(BaseModel):
    doc_id: int
    title: str
    version: int
    page: int
    score: float


class AnswerResponse(BaseModel):
    text: str
    confidence: float
    citations: List[Citation]


@router.post("", response_model=AnswerResponse)
def answer(req: AnswerRequest, user: User = Depends(get_current_user), session = Depends(get_session)):
    q = QueryModel(user_id=user.id, question=req.question)
    session.add(q)
    session.commit()
    session.refresh(q)

    docs = session.exec(select(Document).where((Document.owner_id == user.id) | (user.role.in_(["admin", "support"])))).all()
    version_ids = [d.current_version_id for d in docs if d.current_version_id]

    hits = search_versions(req.question, version_ids, k=TOP_K, session=session) if version_ids else []
    citations: List[Citation] = []
    texts: List[str] = []
    scores: List[float] = []

    for vid, idx, score in hits[: max(2, min(2, len(hits)) )]:
        ver = session.get(DocumentVersion, vid)
        if not ver:
            continue
        doc = session.get(Document, ver.document_id)
        ch = session.exec(select(Chunk).where((Chunk.doc_version_id == vid) & (Chunk.chunk_index == idx))).first()
        if not ch or not doc:
            continue
        citations.append(Citation(doc_id=doc.id, title=doc.name, version=ver.version, page=(ch.page or 1), score=float(score)))
        texts.append(ch.content)
        scores.append(float(score))

    # Synthèse extractive simple: concaténation des meilleurs passages
    summary = "\n\n".join(texts[:2]) if texts else "Aucun passage pertinent trouvé."
    confidence = float(sum(scores) / len(scores)) if scores else 0.0

    ans = AnswerModel(query_id=q.id, text=summary, confidence=confidence)
    session.add(ans)
    session.commit()
    session.refresh(ans)

    for c in citations:
        session.add(AnswerCitationModel(answer_id=ans.id, document_id=c.doc_id, version=c.version, page=c.page, score=c.score, snippet=""))
    session.commit()

    audit_log(user.id, "answer", "qa", ans.id, {"q": req.question, "confidence": confidence, "citations": len(citations)})

    return AnswerResponse(text=summary, confidence=confidence, citations=citations) 