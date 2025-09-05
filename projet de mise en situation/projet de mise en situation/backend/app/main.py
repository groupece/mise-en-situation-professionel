from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from .db import create_db_and_tables, get_session
from .config import CORS_ORIGINS, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_ROLE
from .models import User
from .auth import hash_password
from .routers import auth as auth_router
from .routers import documents as documents_router
from .routers import ingest as ingest_router
from .routers import search as search_router
from .routers import answers as answers_router
from .routers import audits as audits_router

app = FastAPI(title="DocuHelp Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    # seed admin if no user
    session_gen = get_session()
    session = next(session_gen)
    try:
        any_user = session.exec(select(User)).first()
        if not any_user:
            admin = User(email=ADMIN_EMAIL.lower(), password_hash=hash_password(ADMIN_PASSWORD), role=ADMIN_ROLE)
            session.add(admin)
            session.commit()
    finally:
        session.close()

# mount routers
app.include_router(auth_router.router)
app.include_router(documents_router.router)
app.include_router(ingest_router.router)
app.include_router(search_router.router)
app.include_router(answers_router.router)
app.include_router(audits_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "DocuHelp backend API — ready. Swagger: /docs"} 