"""BM25 keyword search over document_chunks.content."""
import re

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import DocumentChunk

TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def build_bm25_index(session: Session):
    chunks = session.execute(select(DocumentChunk)).scalars().all()
    corpus = [tokenize(c.content or "") for c in chunks]
    return BM25Okapi(corpus), list(chunks)


def bm25_search(bm25_index: BM25Okapi, chunks: list[DocumentChunk], query: str, k: int = 5) -> list[dict]:
    scores = bm25_index.get_scores(tokenize(query))
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)[:k]
    return [{"chunk": chunk, "score": float(score)} for chunk, score in ranked]
