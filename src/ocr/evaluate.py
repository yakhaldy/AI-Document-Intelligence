"""Run the Tesseract OCR baseline over data/synthetic and report CER by scan profile.

Usage:
    python -m src.ocr.evaluate --data data/synthetic --lang fra --out docs/eval
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from src.ocr.metrics import compute_cer
from src.ocr.reference_text import extract_reference_text
from src.ocr.tesseract_ocr import run_tesseract


def load_manifest(data_dir: Path):
    with open(data_dir / "manifest.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def evaluate(data_dir: Path, lang: str):
    rows = load_manifest(data_dir)
    results = []
    for row in rows:
        inv_id = row["id"]
        with open(data_dir / "labels" / f"{inv_id}.json", encoding="utf-8") as fh:
            label = json.load(fh)
        reference = extract_reference_text(data_dir / "pdf" / f"{inv_id}.pdf")
        hypothesis = run_tesseract(data_dir / "images" / f"{inv_id}.jpg", lang=lang)
        cer = compute_cer(reference, hypothesis)
        results.append({
            "id": inv_id,
            "split": row["split"],
            "scan_profile": label["scan_profile"]["kind"],
            "cer": cer,
        })
    return results


def aggregate_by_profile(results):
    buckets = defaultdict(list)
    for r in results:
        buckets[r["scan_profile"]].append(r["cer"])
    return {profile: sum(cers) / len(cers) for profile, cers in buckets.items()}


def write_report(out_dir: Path, lang: str, results, by_profile):
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-ocr-tesseract-baseline.md"
    overall_cer = sum(r["cer"] for r in results) / len(results)

    lines = [
        f"# OCR baseline — Tesseract (`--lang {lang}`)",
        "",
        f"Date : {date.today().isoformat()}",
        f"Méthode : `tesseract --lang {lang}` sur `data/synthetic/images/*.jpg`, "
        "comparé au texte extrait des PDF vectoriels (`data/synthetic/pdf/*.pdf`) "
        "via CER (`jiwer.cer`).",
        f"N = {len(results)} factures.",
        "",
        f"## CER global : {overall_cer:.4f}",
        "",
        "## CER par profil de scan",
        "",
        "| Profil | CER moyen | N |",
        "|---|---|---|",
    ]
    counts = defaultdict(int)
    for r in results:
        counts[r["scan_profile"]] += 1
    for profile in sorted(by_profile):
        lines.append(f"| {profile} | {by_profile[profile]:.4f} | {counts[profile]} |")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/synthetic")
    parser.add_argument("--lang", default="fra")
    parser.add_argument("--out", default="docs/eval")
    args = parser.parse_args()

    data_dir = Path(args.data)
    results = evaluate(data_dir, args.lang)
    by_profile = aggregate_by_profile(results)
    report_path = write_report(Path(args.out), args.lang, results, by_profile)
    print(f"Rapport écrit dans {report_path}")


if __name__ == "__main__":
    main()
