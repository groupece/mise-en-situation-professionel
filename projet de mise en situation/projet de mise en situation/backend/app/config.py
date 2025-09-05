from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Security
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///docuhelp.db")

# CORS
_raw = os.getenv("CORS_ORIGINS", "*")
CORS_ORIGINS = [o.strip() for o in _raw.split(",")] if _raw else ["*"]

# Paths
BASE_DIR: Path = Path(__file__).resolve().parents[1]
STORAGE_DIR: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage" / "docs"))).resolve()
INDEX_DIR: Path = Path(os.getenv("INDEX_DIR", str(BASE_DIR / "storage" / "index"))).resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# Retrieval
EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
USE_SEMANTIC: str = os.getenv("USE_SEMANTIC", "auto")  # auto | on | off
TOP_K: int = int(os.getenv("TOP_K", "5"))

# Seed admin (dev only)
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_ROLE: str = os.getenv("ADMIN_ROLE", "admin") 