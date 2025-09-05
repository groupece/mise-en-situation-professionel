from __future__ import annotations
from typing import List, Dict


def chunk_text(text: str, max_chars: int = 800, overlap: int = 80) -> List[Dict]:
    if not text:
        return []
    chunks: List[Dict] = []
    n = len(text)
    start = 0
    while start < n:
        end = min(start + max_chars, n)
        content = text[start:end]
        chunks.append({"content": content, "start_char": start, "end_char": end})
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def chunk_pages(pages: List[str], max_chars: int = 800, overlap: int = 80) -> List[Dict]:
    out: List[Dict] = []
    for i, page_text in enumerate(pages):
        page_num = i + 1
        for c in chunk_text(page_text, max_chars=max_chars, overlap=overlap):
            c["page"] = page_num
            out.append(c)
    return out 