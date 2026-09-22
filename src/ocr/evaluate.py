"""Run an OCR engine baseline over data/synthetic and report CER by scan profile.

Usage:
    python -m src.ocr.evaluate --engine tesseract --data data/synthetic --lang fra --out docs/eval
    python -m src.ocr.evaluate --engine paddleocr --data data/synthetic --lang fr  --out docs/eval

Tesseract needs the `.venv` environment; PaddleOCR needs the dedicated
`.venv-paddle` environment (see docs/eval report for why).
Each run also writes the raw per-invoice CER to docs/eval/_raw/{engine}-{lang}.json,
consumed by `src.ocr.compare` to build the cross-tool table.
"""
import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from src.ocr.metrics import compute_cer
from src.ocr.reference_text import extract_reference_text

ENGINES = {}


def _load_engine(name):
    if name == "tesseract":
        from src.ocr.tesseract_ocr import run_tesseract
        return run_tesseract
    if name == "paddleocr":
        from src.ocr.paddleocr_engine import run_paddleocr
        return run_paddleocr
    raise ValueError(f"Moteur OCR inconnu : {name}")


def load_manifest(data_dir: Path):
    with open(data_dir / "manifest.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def evaluate(data_dir: Path, engine: str, lang: str):
    run_ocr = _load_engine(engine)
    rows = load_manifest(data_dir)
    results = []
    for row in rows:
        inv_id = row["id"]
        with open(data_dir / "labels" / f"{inv_id}.json", encoding="utf-8") as fh:
            label = json.load(fh)
        reference = extract_reference_text(data_dir / "pdf" / f"{inv_id}.pdf")
        hypothesis = run_ocr(data_dir / "images" / f"{inv_id}.jpg", lang=lang)
        cer = compute_cer(reference, hypothesis)
        results.append({
            "id": inv_id,
            "split": row["split"],
            "scan_profile": label["scan_profile"]["kind"],
            "cer": cer,
            "hypothesis": hypothesis,
        })
    return results


def aggregate_by_profile(results):
    buckets = defaultdict(list)
    for r in results:
        buckets[r["scan_profile"]].append(r["cer"])
    return {profile: sum(cers) / len(cers) for profile, cers in buckets.items()}


def write_raw_results(out_dir: Path, engine: str, lang: str, results):
    raw_dir = out_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{engine}-{lang}.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return raw_path


def write_report(out_dir: Path, engine: str, lang: str, results, by_profile):
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-ocr-{engine}-baseline.md"
    overall_cer = sum(r["cer"] for r in results) / len(results)

    lines = [
        f"# OCR baseline — {engine} (`--lang {lang}`)",
        "",
        f"Date : {date.today().isoformat()}",
        f"Méthode : `{engine}` (lang={lang}) sur `data/synthetic/images/*.jpg`, "
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
    parser.add_argument("--engine", required=True, choices=["tesseract", "paddleocr"])
    parser.add_argument("--data", default="data/synthetic")
    parser.add_argument("--lang", required=True)
    parser.add_argument("--out", default="docs/eval")
    args = parser.parse_args()

    data_dir = Path(args.data)
    results = evaluate(data_dir, args.engine, args.lang)
    by_profile = aggregate_by_profile(results)
    out_dir = Path(args.out)
    raw_path = write_raw_results(out_dir, args.engine, args.lang, results)
    report_path = write_report(out_dir, args.engine, args.lang, results, by_profile)
    print(f"Résultats bruts : {raw_path}")
    print(f"Rapport écrit dans {report_path}")


if __name__ == "__main__":
    main()
