from __future__ import annotations
import json
from typing import Optional, Dict, Any
from ..db import get_session
from ..models import AuditLog


def log(user_id: Optional[int], action: str, resource: str, ref_id: Optional[int] = None, meta: Optional[Dict[str, Any]] = None) -> None:
    session_gen = get_session()
    session = next(session_gen)
    try:
        entry = AuditLog(user_id=user_id, action=action, resource=resource, ref_id=ref_id, meta=(json.dumps(meta) if meta else None))
        session.add(entry)
        session.commit()
    finally:
        session.close() 