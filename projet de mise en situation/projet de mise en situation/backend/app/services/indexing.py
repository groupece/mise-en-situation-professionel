from __future__ import annotations
from typing import List, Tuple
from sqlmodel import select
from ..db import get_session
from ..models import Chunk
from .embedding import Retriever
from ..config import INDEX_DIR, TOP_K

import os


def _index_path_for_version(version_id: int) -> str:
    return str(INDEX_DIR / f"{version_id}.pkl")


def build_index_for_version(version_id: int, session=None) -> str:
    own_session = False
    if session is None:
        own_session = True
        session_gen = get_session()
        session = next(session_gen)
    try:
        chunks = session.exec(select(Chunk).where(Chunk.doc_version_id == version_id).order_by(Chunk.chunk_index)).all()
        texts = [c.content for c in chunks]
        retriever = Retriever(mode="tfidf")
        retriever.fit(texts)
        path = _index_path_for_version(version_id)
        retriever.save(path)
        # Persist vector path on chunks (optional meta)
        for c in chunks:
            c.vector_path = path
            session.add(c)
        session.commit()
        return path
    finally:
        if own_session:
            session.close()


def search_versions(query: str, version_ids: List[int], k: int = TOP_K, session=None) -> List[Tuple[int, int, float]]:
    own_session = False
    if session is None:
        own_session = True
        session_gen = get_session()
        session = next(session_gen)
    try:
        results: List[Tuple[int, int, float]] = []  # (version_id, chunk_index_in_version, score)
        for vid in version_ids:
            chunks = session.exec(select(Chunk).where(Chunk.doc_version_id == vid).order_by(Chunk.chunk_index)).all()
            if not chunks:
                continue
            texts = [c.content for c in chunks]
            path = _index_path_for_version(vid)
            from .embedding import Retriever
            retriever = Retriever.load(path) if os.path.exists(path) else None
            if retriever is None:
                retriever = Retriever(mode="tfidf")
                retriever.fit(texts)
            hits = retriever.search(query, texts, top_k=k)
            for idx, score in hits:
                results.append((vid, idx, score))
        # sort by score desc and trim
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:k]
    finally:
        if own_session:
            session.close() 