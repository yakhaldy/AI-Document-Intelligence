"""Build the CER-by-profile-and-tool comparison table from raw eval results.

Usage:
    python -m src.ocr.compare --out docs/eval --run tesseract:fra --run paddleocr:fr
"""
import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path


def load_raw(out_dir: Path, engine: str, lang: str):
    path = out_dir / "_raw" / f"{engine}-{lang}.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def cer_by_profile(results):
    buckets = defaultdict(list)
    for r in results:
        buckets[r["scan_profile"]].append(r["cer"])
    return {profile: sum(cers) / len(cers) for profile, cers in buckets.items()}


def build_table(runs, out_dir: Path):
    per_run = {}
    profiles = set()
    for engine, lang in runs:
        results = load_raw(out_dir, engine, lang)
        by_profile = cer_by_profile(results)
        overall = sum(r["cer"] for r in results) / len(results)
        per_run[(engine, lang)] = (by_profile, overall, len(results))
        profiles.update(by_profile)

    lines = [
        "# Comparatif OCR — CER par profil de scan et par outil",
        "",
        f"Date : {date.today().isoformat()}",
        "",
        "| Outil | N | clean | scan | bad | Global |",
        "|---|---|---|---|---|---|",
    ]
    for (engine, lang), (by_profile, overall, n) in per_run.items():
        row = [f"{engine} (`{lang}`)", str(n)]
        for profile in ("clean", "scan", "bad"):
            row.append(f"{by_profile[profile]:.4f}" if profile in by_profile else "—")
        row.append(f"{overall:.4f}")
        lines.append("| " + " | ".join(row) + " |")

    report_path = out_dir / f"{date.today().isoformat()}-ocr-comparison.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/eval")
    parser.add_argument(
        "--run", action="append", required=True,
        help="engine:lang, ex. tesseract:fra — répétable",
    )
    args = parser.parse_args()
    runs = [tuple(r.split(":", 1)) for r in args.run]
    report_path = build_table(runs, Path(args.out))
    print(f"Comparatif écrit dans {report_path}")


if __name__ == "__main__":
    main()
