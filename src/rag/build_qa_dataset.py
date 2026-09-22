"""Build the 50 hand-authored reference Q&A pairs (README §4 Étape 5).

"Hand-authored" here means: the question phrasings/templates are written by
hand (6 distinct templates below), and every fact plugged into them is
pulled straight from the DB — not invented. This guarantees 50 factually
correct pairs without manually re-typing 50 documents' worth of numbers.

Only samples from documents that are actually indexed (have chunks) —
otherwise the question would be unanswerable by construction, which isn't a
useful reference set entry.

Usage:
    python -m src.rag.build_qa_dataset --out docs/eval/rag_qa_dataset.json --n 50
"""
import argparse
import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.ingest import UNKNOWN_SUPPLIER_PLACEHOLDER
from db.models import DocumentChunk, Invoice, Supplier

load_dotenv()

TEMPLATES = [
    ("invoice_number", "Quel est le numéro de la facture du fournisseur {supplier} datée du {invoice_date} ?"),
    ("total_ttc", "Quel est le montant total TTC de la facture {invoice_number} ?"),
    ("supplier_name", "Qui est le fournisseur de la facture {invoice_number} ?"),
    ("tva_rate", "Quel est le taux de TVA appliqué sur la facture {invoice_number} ?"),
    ("due_date", "Quelle est la date d'échéance de la facture {invoice_number} ?"),
    ("total_ht", "Quel est le montant total HT de la facture {invoice_number} ?"),
]


def load_indexed_invoices(session: Session) -> list[dict]:
    indexed_doc_ids = {
        row[0] for row in session.execute(select(DocumentChunk.document_id).distinct())
    }
    rows = session.execute(
        select(Invoice, Supplier).join(Supplier, Invoice.supplier_id == Supplier.id)
    ).all()
    items = []
    for invoice, supplier in rows:
        if invoice.document_id not in indexed_doc_ids:
            continue
        if supplier.name == UNKNOWN_SUPPLIER_PLACEHOLDER:
            # Means this invoice fell back to regex-only extraction (Étape 2's
            # regex doesn't extract supplier_name) — its other fields are
            # unreliable too (regex's own F1 was weak, e.g. 0.29 on
            # invoice_number), so it's excluded rather than risk a bogus
            # ground-truth answer in the reference set.
            continue
        items.append({
            "document_id": invoice.document_id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
            "total_ht": float(invoice.total_ht) if invoice.total_ht is not None else None,
            "tva_rate": float(invoice.tva_rate) if invoice.tva_rate is not None else None,
            "total_ttc": float(invoice.total_ttc) if invoice.total_ttc is not None else None,
            "supplier_name": supplier.name,
        })
    return items


def build_qa(items: list[dict], n: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    qa = []
    attempts = 0
    max_attempts = n * 20
    while len(qa) < n and attempts < max_attempts:
        attempts += 1
        field, template = rng.choice(TEMPLATES)
        item = rng.choice(items)
        answer = item.get(field)
        if answer is None or item.get("invoice_number") is None:
            continue
        if field == "invoice_number" and item.get("invoice_date") is None:
            continue  # the question template needs a real date to name the invoice
        question = template.format(
            supplier=item["supplier_name"],
            invoice_date=item["invoice_date"],
            invoice_number=item["invoice_number"],
        )
        qa.append({
            "question": question,
            "expected_answer": str(answer),
            "expected_document_id": item["document_id"],
            "field": field,
        })
    return qa


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/eval/rag_qa_dataset.json")
    parser.add_argument("--n", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    engine = create_engine(database_url)
    with Session(engine) as session:
        items = load_indexed_invoices(session)
    print(f"{len(items)} factures indexées disponibles pour générer les questions")

    qa = build_qa(items, args.n, args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(qa)} questions écrites dans {out_path}")


if __name__ == "__main__":
    main()
