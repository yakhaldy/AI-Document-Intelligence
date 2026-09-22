"""Unified 3-class classification dataset: facture / contrat / rapport.

Facture text is the clean PDF-extracted reference text (not noisy OCR
output), so all three classes are compared on clean text — otherwise
facture would be unfairly handicapped relative to the cleanly-generated
contrat/rapport text.
"""
import csv
from pathlib import Path

from src.ocr.reference_text import extract_reference_text


def load_facture_items(data_dir: Path) -> list[dict]:
    with open(data_dir / "manifest.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    items = []
    for row in rows:
        text = extract_reference_text(data_dir / "pdf" / f"{row['id']}.pdf")
        items.append({"id": row["id"], "doc_type": "facture", "split": row["split"], "text": text})
    return items


def load_text_corpus(corpus_dir: Path, doc_type: str) -> list[dict]:
    with open(corpus_dir / "manifest.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    items = []
    for row in rows:
        text = (corpus_dir / "texts" / f"{row['id']}.txt").read_text(encoding="utf-8")
        items.append({"id": row["id"], "doc_type": doc_type, "split": row["split"], "text": text})
    return items


def load_classification_dataset(data_dir: str | Path = "data/synthetic") -> list[dict]:
    data_dir = Path(data_dir)
    items = load_facture_items(data_dir)
    items += load_text_corpus(data_dir / "contracts", "contrat")
    items += load_text_corpus(data_dir / "reports", "rapport")
    return items
