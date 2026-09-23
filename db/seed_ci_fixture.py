"""Minimal fixture data for CI only — one invoice inserted directly (no OCR,
no LLM call) so list-endpoint tests (`total > 0`) don't need the real
200-invoice dataset or a live LLM API key. Never run this against the real
dev/prod database — it's a fake, arbitrary invoice.

Usage:
    python -m db.seed_ci_fixture
"""
import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Document, Invoice, Supplier, default_tenant_id


def seed_ci_fixture(session: Session) -> None:
    tenant_id = default_tenant_id()
    supplier = Supplier(tenant_id=tenant_id, name="Fournisseur CI", ice="000000000000000")
    session.add(supplier)
    session.flush()

    document = Document(tenant_id=tenant_id, file_path="ci-fixture.pdf", doc_type="invoice")
    session.add(document)
    session.flush()

    invoice = Invoice(
        document_id=document.id,
        supplier_id=supplier.id,
        invoice_number="CI-0001",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 2, 1),
        total_ht=100,
        tva_rate=20,
        total_tva=20,
        total_ttc=120,
        currency="MAD",
        payment_status="unpaid",
    )
    session.add(invoice)
    session.commit()
    print(f"Fixture CI insérée : document={document.id}, invoice={invoice.id}")


def main():
    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])
    with Session(engine) as session:
        seed_ci_fixture(session)


if __name__ == "__main__":
    main()
