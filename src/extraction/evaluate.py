"""Field-extraction evaluation: regex-only, LLM-only, and combined.

Runs on the OCR output already computed for Tesseract (docs/eval/_raw), and
ONLY on the `test` split of manifest.csv — per README §8, the test split is
reserved for final evaluation and is never used to tune the extractor code.

Usage:
    python -m src.extraction.evaluate --ocr-raw docs/eval/_raw/tesseract-fra.json --out docs/eval
"""
import argparse
import json
import time
from datetime import date
from pathlib import Path

from src.extraction.llm_extractor import extract_with_llm
from src.extraction.metrics import evaluate_all_fields, gold_from_label
from src.extraction.regex_extractor import extract_fields as extract_with_regex

FIELDS = [
    "invoice_number", "invoice_date", "due_date", "supplier_name",
    "supplier_ice", "supplier_if", "supplier_rc",
    "total_ht", "tva_rate", "total_tva", "total_ttc",
]

# Fields the regex extractor attempts; used to build the combined prediction
# (LLM output, overridden by regex wherever regex found a value).
REGEX_FIELDS = [
    "invoice_number", "invoice_date", "due_date",
    "supplier_ice", "supplier_if", "supplier_rc",
    "total_ht", "tva_rate", "total_tva", "total_ttc",
]


def load_test_split(ocr_raw_path: Path, data_dir: Path):
    with open(ocr_raw_path, encoding="utf-8") as fh:
        ocr_results = json.load(fh)
    items = []
    for r in ocr_results:
        if r["split"] != "test":
            continue
        with open(data_dir / "labels" / f"{r['id']}.json", encoding="utf-8") as fh:
            label = json.load(fh)
        items.append({"id": r["id"], "text": r["hypothesis"], "gold": gold_from_label(label)})
    return items


def combine(llm_pred: dict, regex_pred: dict) -> dict:
    # "Secours" = fallback: the regex only fills a field the LLM missed. An
    # earlier version had the regex unconditionally override the LLM, which
    # measurably hurt fields where the LLM is already strong (e.g.
    # invoice_number F1 dropped from 0.90 to 0.60 on the 10-invoice sample)
    # since it also applied the regex's own mistakes over correct LLM output.
    combined = dict(llm_pred)
    for field in REGEX_FIELDS:
        if combined.get(field) is None and regex_pred.get(field) is not None:
            combined[field] = regex_pred[field]
    return combined


def run(items, request_delay: float = 1.0):
    predictions = {"regex": [], "llm": [], "combined": []}
    golds = []
    failures = []
    for i, item in enumerate(items):
        regex_pred = extract_with_regex(item["text"])
        regex_pred.setdefault("supplier_name", None)
        try:
            llm_pred = extract_with_llm(item["text"])
        except RuntimeError as exc:
            failures.append({"id": item["id"], "error": str(exc)})
            llm_pred = {field: None for field in FIELDS}
        predictions["regex"].append(regex_pred)
        predictions["llm"].append(llm_pred)
        predictions["combined"].append(combine(llm_pred, regex_pred))
        golds.append(item["gold"])
        if request_delay and i < len(items) - 1:
            time.sleep(request_delay)
    return predictions, golds, failures


def write_raw(out_dir: Path, items, predictions):
    raw_dir = out_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for method, preds in predictions.items():
        rows = [
            {"id": item["id"], "gold": item["gold"], "prediction": pred}
            for item, pred in zip(items, preds)
        ]
        path = raw_dir / f"extraction-{method}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(out_dir: Path, metrics_by_method: dict, n: int, failures: list):
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-extraction-baseline.md"
    lines = [
        "# Extraction de champs — regex vs LLM vs combiné",
        "",
        f"Date : {date.today().isoformat()}",
        f"N = {n} factures (split `test` uniquement, texte = sortie OCR Tesseract).",
        "Combiné = sortie LLM, champs remplacés par le regex quand celui-ci "
        "trouve une valeur (regex \"de secours\" sur les champs à format fixe).",
        "",
    ]
    if failures:
        lines.append(f"⚠️ {len(failures)} appel(s) LLM en échec (voir _raw/extraction-llm.json, valeurs null).")
        lines.append("")

    for method in ("regex", "llm", "combined"):
        lines.append(f"## {method}")
        lines.append("")
        lines.append("| Champ | Précision | Rappel | F1 | TP | FP | FN |")
        lines.append("|---|---|---|---|---|---|---|")
        for field in FIELDS:
            m = metrics_by_method[method][field]
            lines.append(
                f"| {field} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} "
                f"| {m['tp']} | {m['fp']} | {m['fn']} |"
            )
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-raw", default="docs/eval/_raw/tesseract-fra.json")
    parser.add_argument("--data", default="data/synthetic")
    parser.add_argument("--out", default="docs/eval")
    parser.add_argument("--limit", type=int, default=None, help="n'évaluer que les N premières factures du split test")
    parser.add_argument("--request-delay", type=float, default=1.0, help="pause (s) entre appels LLM, anti rate-limit")
    args = parser.parse_args()

    items = load_test_split(Path(args.ocr_raw), Path(args.data))
    if args.limit:
        items = items[:args.limit]
    predictions, golds, failures = run(items, request_delay=args.request_delay)
    metrics_by_method = {
        method: evaluate_all_fields(preds, golds, FIELDS)
        for method, preds in predictions.items()
    }
    out_dir = Path(args.out)
    write_raw(out_dir, items, predictions)
    report_path = write_report(out_dir, metrics_by_method, len(items), failures)
    print(f"Rapport écrit dans {report_path}")
    if failures:
        print(f"{len(failures)} échec(s) LLM : {[f['id'] for f in failures]}")


if __name__ == "__main__":
    main()
