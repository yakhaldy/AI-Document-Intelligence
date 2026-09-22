"""Ingestion pipeline: OCR text (already computed) -> extraction -> DB insert.

Usage:
    python -m db.ingest --ocr-raw docs/eval/_raw/tesseract-fra.json --data data/synthetic

Reuses the OCR output already computed in Étape 1 (docs/eval/_raw/tesseract-fra.json,
covers all 200 invoices) rather than re-running Tesseract. Extraction reuses
Étape 2's regex + LLM + combine logic exactly (src/extraction).

Known gaps, left NULL rather than faked:
  - documents.ocr_confidence: not computed by the current OCR wrapper
  - suppliers.city, invoices.payment_status: not in the Étape 2 extraction
    field set (no regex/LLM attempts them yet)
  - invoice_lines: line-item extraction isn't implemented (Étape 2 scope was
    header fields only) — table stays empty for now
"""
import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models import Base, Document, Invoice, Supplier, default_tenant_id
from src.extraction.evaluate import combine
from src.extraction.llm_extractor import extract_with_llm
from src.extraction.regex_extractor import extract_fields as extract_with_regex

load_dotenv()


def parse_iso_date(value: str | None):
    return date.fromisoformat(value) if value else None


UNKNOWN_SUPPLIER_PLACEHOLDER = "Fournisseur inconnu"


def get_or_create_supplier(session: Session, tenant_id, fields: dict) -> Supplier:
    ice = fields.get("supplier_ice")
    if ice:
        existing = session.execute(
            select(Supplier).where(Supplier.tenant_id == tenant_id, Supplier.ice == ice)
        ).scalar_one_or_none()
        if existing:
            # Self-heal: an earlier invoice for this supplier may have had a
            # failed/null extraction (regex doesn't extract supplier_name at
            # all) and left the placeholder here — don't let that permanently
            # poison every other invoice from the same supplier once a good
            # name comes along.
            name = fields.get("supplier_name")
            if existing.name == UNKNOWN_SUPPLIER_PLACEHOLDER and name:
                existing.name = name
            return existing
    supplier = Supplier(
        tenant_id=tenant_id,
        name=fields.get("supplier_name") or UNKNOWN_SUPPLIER_PLACEHOLDER,
        ice=ice,
        if_number=fields.get("supplier_if"),
        rc=fields.get("supplier_rc"),
    )
    session.add(supplier)
    session.flush()
    return supplier


def already_ingested(session: Session, tenant_id, file_path: str) -> bool:
    existing = session.execute(
        select(Document).where(Document.tenant_id == tenant_id, Document.file_path == file_path)
    ).scalar_one_or_none()
    return existing is not None


def ingest_invoice(
    session: Session, tenant_id, inv_id: str, ocr_text: str, pdf_path: Path
) -> tuple[Invoice | None, bool]:
    """Returns (invoice, used_regex_fallback). invoice is None if this
    file_path was already ingested for this tenant (idempotent)."""
    file_path = str(pdf_path)
    if already_ingested(session, tenant_id, file_path):
        return None, False

    regex_pred = extract_with_regex(ocr_text)
    used_regex_fallback = False
    try:
        llm_pred = extract_with_llm(ocr_text)
    except RuntimeError as exc:
        print(f"  {inv_id}: extraction LLM en échec ({exc}), regex seul utilisé")
        llm_pred = dict(regex_pred)
        llm_pred.setdefault("supplier_name", None)
        used_regex_fallback = True
    fields = combine(llm_pred, regex_pred)

    document = Document(tenant_id=tenant_id, file_path=file_path, doc_type="invoice")
    session.add(document)
    session.flush()

    supplier = get_or_create_supplier(session, tenant_id, fields)

    invoice = Invoice(
        document_id=document.id,
        supplier_id=supplier.id,
        invoice_number=fields.get("invoice_number"),
        invoice_date=parse_iso_date(fields.get("invoice_date")),
        due_date=parse_iso_date(fields.get("due_date")),
        total_ht=fields.get("total_ht"),
        tva_rate=fields.get("tva_rate"),
        total_tva=fields.get("total_tva"),
        total_ttc=fields.get("total_ttc"),
        currency="MAD",
    )
    session.add(invoice)
    session.flush()
    return invoice, used_regex_fallback


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-raw", default="docs/eval/_raw/tesseract-fra.json")
    parser.add_argument("--data", default="data/synthetic")
    parser.add_argument("--request-delay", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL manquant (voir .env)")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)  # no-op if Alembic already applied it

    with open(args.ocr_raw, encoding="utf-8") as fh:
        ocr_results = json.load(fh)
    if args.limit:
        ocr_results = ocr_results[:args.limit]

    tenant_id = default_tenant_id()
    data_dir = Path(args.data)
    inserted, skipped = 0, 0

    with Session(engine) as session:
        for i, r in enumerate(ocr_results):
            pdf_path = data_dir / "pdf" / f"{r['id']}.pdf"
            invoice, _used_fallback = ingest_invoice(session, tenant_id, r["id"], r["hypothesis"], pdf_path)
            if invoice is None:
                skipped += 1
            else:
                inserted += 1
                session.commit()
            if (i + 1) % 20 == 0 or i == len(ocr_results) - 1:
                print(f"{i + 1}/{len(ocr_results)} (insérés={inserted}, déjà présents={skipped})")
            if args.request_delay and i < len(ocr_results) - 1:
                time.sleep(args.request_delay)

    print(f"Terminé : {inserted} factures insérées, {skipped} déjà présentes.")


if __name__ == "__main__":
    main()
