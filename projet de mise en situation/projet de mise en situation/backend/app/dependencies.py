from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import select
from .auth import decode_token
from .db import get_session
from .models import User

def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()

def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session = Depends(get_session)
) -> User:
    token = _extract_bearer_token(authorization)
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_role(required: str):
    def _dep(user: User = Depends(get_current_user)) -> User:
        roles_order = {"admin": 3, "support": 2, "user": 1}
        if roles_order.get(user.role, 0) < roles_order.get(required, 0):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return _dep 