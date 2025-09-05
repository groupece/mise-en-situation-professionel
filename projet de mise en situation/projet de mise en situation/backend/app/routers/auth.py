from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlmodel import SQLModel, Field, select
from ..db import get_session
from ..models import User
from ..auth import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user
from ..services.audit import log as audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(SQLModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"


class UserRead(SQLModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime


class LoginRequest(SQLModel):
    email: EmailStr
    password: str


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, session = Depends(get_session)):
    exists = session.exec(select(User).where(User.email == str(payload.email).lower())).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=payload.role or "user",
        created_at=datetime.now(timezone.utc),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    audit_log(user.id, "register", "auth", user.id, {"email": user.email})
    return UserRead(id=user.id, email=user.email, role=user.role, created_at=user.created_at)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == str(payload.email).lower())).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    audit_log(user.id, "login", "auth", user.id, {"email": user.email})
    return TokenResponse(access_token=token, role=user.role, expires_in=3600)


@router.get("/me", response_model=UserRead)
def me(current: User = Depends(get_current_user)):
    return UserRead(id=current.id, email=current.email, role=current.role, created_at=current.created_at) 