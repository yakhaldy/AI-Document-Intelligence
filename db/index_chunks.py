"""Chunk + embed already-ingested documents, store in document_chunks.

Usage:
    python -m db.index_chunks

Reuses the OCR text already computed in Étape 1 (docs/eval/_raw/tesseract-fra.json)
for invoices. One embedding API call per document (batched across its chunks).
"""
import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models import Document, DocumentChunk
from src.rag.chunking import chunk_by_section
from src.rag.embeddings import embed_batch

load_dotenv()


def already_indexed(session: Session, document_id: int) -> bool:
    existing = session.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    ).first()
    return existing is not None


def index_document(session: Session, document: Document, text: str) -> int:
    if already_indexed(session, document.id):
        return 0
    chunks = chunk_by_section(text)
    if not chunks:
        return 0
    try:
        vectors = embed_batch(chunks)
    except RuntimeError as exc:
        print(f"  document {document.id}: embedding en échec ({exc}), ignoré pour cette passe")
        return 0
    for content, vector in zip(chunks, vectors):
        session.add(DocumentChunk(document_id=document.id, content=content, embedding=vector))
    return len(chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-raw", default="docs/eval/_raw/tesseract-fra.json")
    parser.add_argument("--request-delay", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant (voir .env)")
    engine = create_engine(database_url)

    with open(args.ocr_raw, encoding="utf-8") as fh:
        ocr_by_id = {r["id"]: r["hypothesis"] for r in json.load(fh)}

    total_chunks, total_docs = 0, 0
    with Session(engine) as session:
        documents = session.execute(select(Document)).scalars().all()
        if args.limit:
            documents = documents[:args.limit]
        for i, document in enumerate(documents):
            inv_id = Path(document.file_path).stem
            text = ocr_by_id.get(inv_id)
            if text is None:
                print(f"  {inv_id}: pas de texte OCR trouvé, ignoré")
                continue
            n = index_document(session, document, text)
            if n:
                total_chunks += n
                total_docs += 1
                session.commit()
            if (i + 1) % 20 == 0 or i == len(documents) - 1:
                print(f"{i + 1}/{len(documents)} documents (indexés={total_docs}, chunks={total_chunks})")
            if args.request_delay and n:
                time.sleep(args.request_delay)

    print(f"Terminé : {total_docs} documents indexés, {total_chunks} chunks au total.")


if __name__ == "__main__":
    main()
