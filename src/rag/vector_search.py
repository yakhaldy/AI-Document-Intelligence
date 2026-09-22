"""Cosine-similarity search over document_chunks (pgvector)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DocumentChunk


def vector_search(session: Session, query_embedding: list[float], k: int = 5) -> list[dict]:
    distance = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    stmt = (
        select(DocumentChunk, distance)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(distance)
        .limit(k)
    )
    rows = session.execute(stmt).all()
    return [
        {"chunk": chunk, "score": 1 - dist}  # cosine similarity, higher is better
        for chunk, dist in rows
    ]
