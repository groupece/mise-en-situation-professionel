from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import select
from ..db import get_session
from ..models import AuditLog, User
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/audits", tags=["audits"])


class AuditRead(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: str
    ref_id: Optional[int]
    meta: Optional[str]
    created_at: datetime


@router.get("", response_model=List[AuditRead])
def list_audits(
    user: Optional[int] = Query(default=None),
    doc: Optional[int] = Query(default=None),
    session = Depends(get_session),
    current: User = Depends(require_role("support")),
):
    q = select(AuditLog)
    # simple filters
    if user is not None:
        q = q.where(AuditLog.user_id == user)
    if doc is not None:
        q = q.where(AuditLog.ref_id == doc)
    q = q.order_by(AuditLog.created_at.desc())
    rows = session.exec(q).all()
    return [AuditRead(id=r.id, user_id=r.user_id, action=r.action, resource=r.resource, ref_id=r.ref_id, meta=r.meta, created_at=r.created_at) for r in rows] 