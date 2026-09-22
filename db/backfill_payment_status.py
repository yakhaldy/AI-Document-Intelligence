"""Backfill invoices.payment_status from the synthetic dataset's ground truth.

Not a cheat: payment_status is a business fact ("has this actually been
paid"), not necessarily something visible on the document text — the
generator itself distinguishes "payment_status" (business truth) from
"payment_status_visible" (whether a paid stamp appears on the page). A real
system would get this from the accounting/ERP system, not by re-parsing the
invoice PDF. Étape 2's extraction never attempted this field, so it's NULL
for all 200 ingested invoices until this runs once.

Usage:
    python -m db.backfill_payment_status
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.models import Document, Invoice

load_dotenv()


def main():
    database_url = os.environ.get("DATABASE_URL")
    engine = create_engine(database_url)
    data_dir = Path("data/synthetic")

    updated = 0
    with Session(engine) as session:
        rows = session.execute(
            select(Invoice, Document).join(Document, Invoice.document_id == Document.id)
        ).all()
        for invoice, document in rows:
            inv_id = Path(document.file_path).stem
            label_path = data_dir / "labels" / f"{inv_id}.json"
            if not label_path.exists():
                continue
            label = json.loads(label_path.read_text(encoding="utf-8"))
            status = label.get("payment_status")
            if status in ("paid", "unpaid") and invoice.payment_status != status:
                invoice.payment_status = status
                updated += 1
        session.commit()

    print(f"payment_status mis à jour pour {updated} factures")


if __name__ == "__main__":
    main()
