from __future__ import annotations
from pathlib import Path
from typing import List
import chardet


def _read_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def extract_txt(path: Path) -> List[str]:
    data = _read_bytes(path)
    enc = chardet.detect(data).get("encoding") or "utf-8"
    text = data.decode(enc, errors="replace")
    return [text]


def extract_docx(path: Path) -> List[str]:
    from docx import Document
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
    return [text]


def extract_pdf(path: Path) -> List[str]:
    import fitz  # PyMuPDF
    pages: List[str] = []
    with fitz.open(str(path)) as pdf:
        for page in pdf:
            text = page.get_text("text")
            pages.append(text or "")
    return pages


def normalize(text: str) -> str:
    return " ".join(text.replace("\r", "\n").split())


def extract_by_mime(path: Path, mime: str) -> List[str]:
    mime = (mime or "").lower()
    suffix = path.suffix.lower()
    if "pdf" in mime or suffix == ".pdf":
        pages = extract_pdf(path)
    elif "word" in mime or suffix == ".docx":
        pages = extract_docx(path)
    elif "text" in mime or suffix == ".txt":
        pages = extract_txt(path)
    else:
        pages = extract_txt(path)
    return [normalize(p) for p in pages] 