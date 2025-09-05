from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, String

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    password_hash: str = Field(nullable=False)
    role: str = Field(default="user")  # "admin" | "support" | "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    name: str
    filename: str
    path: str
    mime: str
    size: int
    sha256: str
    status: str = Field(default="uploaded")  # "uploaded" | "processed"
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_version_id: Optional[int] = Field(default=None, foreign_key="documentversion.id")

class DocumentVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    version: int = Field(default=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    text_len: int = Field(default=0)
    chunk_count: int = Field(default=0)
    embedding_model: str = Field(default="")
    doc_sha256: str = Field(default="")

class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doc_version_id: int = Field(foreign_key="documentversion.id", index=True)
    chunk_index: int = Field(index=True)
    content: str = Field(nullable=False)
    page: Optional[int] = Field(default=None)
    start_char: Optional[int] = Field(default=None)
    end_char: Optional[int] = Field(default=None)
    vector_path: Optional[str] = Field(default=None)

class Query(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    question: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Answer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="query.id", index=True)
    text: str = Field(nullable=False)
    confidence: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnswerCitation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    answer_id: int = Field(foreign_key="answer.id", index=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    version: int = Field(default=1)
    page: int = Field(default=1)
    score: float = Field(default=0.0)
    snippet: str = Field(default="")

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    action: str = Field(nullable=False)
    resource: str = Field(nullable=False)
    ref_id: Optional[int] = Field(default=None)
    meta: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) 