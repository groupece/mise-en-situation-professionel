from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import os
import numpy as np

USE_SEMANTIC = os.getenv("USE_SEMANTIC", "auto")
MODEL_NAME = os.getenv("EMBEDDINGS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_sentence_model = None
_nn = None
_vectorizer = None
_matrix = None


def _try_load_sentence_model():
    global _sentence_model
    if _sentence_model is not None:
        return _sentence_model
    if USE_SEMANTIC.lower() == "off":
        return None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _sentence_model = SentenceTransformer(MODEL_NAME)
        return _sentence_model
    except Exception:
        return None


@dataclass
class Retriever:
    mode: str  # "semantic"|"tfidf"

    def fit(self, texts: List[str]) -> None:
        global _nn, _vectorizer, _matrix
        model = _try_load_sentence_model()
        if model and USE_SEMANTIC.lower() in ("auto", "on"):
            # Semantic mode
            embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            from sklearn.neighbors import NearestNeighbors  # type: ignore
            _nn = NearestNeighbors(metric="cosine")
            _nn.fit(embeddings)
            self.mode = "semantic"
            _matrix = embeddings
            _vectorizer = None
        else:
            # TF-IDF fallback
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            from sklearn.metrics.pairwise import cosine_similarity  # noqa: F401  # type: ignore
            _vectorizer = TfidfVectorizer(max_df=0.9, min_df=1)
            _matrix = _vectorizer.fit_transform(texts)
            _nn = None
            self.mode = "tfidf"

    def search(self, query: str, texts: List[str], top_k: int = 5) -> List[Tuple[int, float]]:
        global _nn, _vectorizer, _matrix
        if self.mode == "semantic" and _nn is not None and _matrix is not None:
            model = _try_load_sentence_model()
            q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
            distances, indices = _nn.kneighbors(q, n_neighbors=min(top_k, len(texts)))
            scores = 1.0 - distances[0]
            return [(int(i), float(s)) for i, s in zip(indices[0], scores)]
        else:
            # TF-IDF
            from sklearn.metrics.pairwise import linear_kernel  # type: ignore
            q_vec = _vectorizer.transform([query])
            sims = linear_kernel(q_vec, _matrix).ravel()
            top_idx = sims.argsort()[::-1][: min(top_k, len(texts))]
            return [(int(i), float(sims[i])) for i in top_idx]

    def save(self, path: str) -> None:
        import pickle
        with open(path, "wb") as f:
            pickle.dump({
                "mode": self.mode,
                "matrix": _matrix,
                "vectorizer": _vectorizer,
            }, f)

    @staticmethod
    def load(path: str) -> "Retriever":
        import pickle
        obj = Retriever(mode="tfidf")
        with open(path, "rb") as f:
            data = pickle.load(f)
        global _matrix, _vectorizer, _nn
        _matrix = data.get("matrix")
        _vectorizer = data.get("vectorizer")
        _nn = None
        obj.mode = data.get("mode", "tfidf")
        return obj 