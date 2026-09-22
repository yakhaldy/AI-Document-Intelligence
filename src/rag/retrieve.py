"""Unified retrieval entry point: vector-only / hybrid / hybrid+rerank."""
from sqlalchemy.orm import Session

from src.rag.bm25_search import bm25_search
from src.rag.embeddings import embed_query
from src.rag.hybrid_search import reciprocal_rank_fusion
from src.rag.reranker import rerank
from src.rag.vector_search import vector_search

METHODS = ("vector", "hybrid", "hybrid_rerank")


def retrieve(
    session: Session,
    bm25_index,
    bm25_chunks: list,
    query: str,
    method: str,
    k: int = 5,
    candidate_k: int = 15,
) -> list[dict]:
    if method not in METHODS:
        raise ValueError(f"méthode inconnue : {method} (attendu : {METHODS})")

    if method == "vector":
        query_embedding = embed_query(query)
        return vector_search(session, query_embedding, k=k)

    query_embedding = embed_query(query)
    vector_results = vector_search(session, query_embedding, k=candidate_k)
    bm25_results = bm25_search(bm25_index, bm25_chunks, query, k=candidate_k)
    fused = reciprocal_rank_fusion(vector_results, bm25_results, k=candidate_k)

    if method == "hybrid":
        return fused[:k]
    return rerank(query, fused, top_k=k)
