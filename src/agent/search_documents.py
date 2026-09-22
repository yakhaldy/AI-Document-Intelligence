"""search_documents tool: wraps the Étape 5 RAG pipeline (hybrid+rerank, the
retained method — see docs/eval/2026-09-22-rag-comparison.md) as one call.
"""
from sqlalchemy.orm import Session

from src.rag.bm25_search import build_bm25_index
from src.rag.generate import generate_answer
from src.rag.retrieve import retrieve

_bm25_cache = {}


def _get_bm25_index(session: Session):
    key = id(session.bind)
    if key not in _bm25_cache:
        _bm25_cache[key] = build_bm25_index(session)
    return _bm25_cache[key]


def search_documents(session: Session, query: str, k: int = 5) -> dict:
    bm25_index, bm25_chunks = _get_bm25_index(session)
    retrieved = retrieve(session, bm25_index, bm25_chunks, query, method="hybrid_rerank", k=k)
    return generate_answer(query, retrieved)
