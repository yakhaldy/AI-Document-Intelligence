"""Compare TF-IDF+LogReg, LLM (zero/few-shot), and Jev (zero/few-shot) on the
same test split.

TF-IDF is free/instant — evaluated on the FULL test split. The LLM/Jev
methods cost real money and are rate-limited, so they run on a deterministic
stratified subsample of the test split (sizes below), never cherry-picked.
Few-shot examples are drawn from the DEV split only, fixed indices — never
selected from or tuned against the test set.

Usage:
    python -m src.classification.evaluate --data data/synthetic --out docs/eval
"""
import argparse
import json
import time
from datetime import date
from pathlib import Path

from src.classification.dataset import load_classification_dataset
from src.classification.jev_classifier import classify_with_jev
from src.classification.llm_classifier import classify_with_llm
from src.classification.metrics import evaluate_classification
from src.classification.tfidf_baseline import predict as tfidf_predict
from src.classification.tfidf_baseline import train as tfidf_train

LABELS = ["facture", "contrat", "rapport"]
LLM_SUBSAMPLE_PER_CLASS = {"facture": 15, "contrat": 13, "rapport": 16}  # contrat/rapport: all of them
FEW_SHOT_PER_CLASS = 1


def stratified_subsample(items, per_class, seed_key=lambda i: i["id"]):
    by_class = {}
    for item in items:
        by_class.setdefault(item["doc_type"], []).append(item)
    subsample = []
    for label, items_of_class in by_class.items():
        items_of_class = sorted(items_of_class, key=seed_key)
        n = per_class.get(label, len(items_of_class))
        subsample.extend(items_of_class[:n])
    return subsample


def pick_few_shot_examples(dev_items, n_per_class=FEW_SHOT_PER_CLASS):
    by_class = {}
    for item in dev_items:
        by_class.setdefault(item["doc_type"], []).append(item)
    examples = []
    for label in LABELS:
        for item in sorted(by_class[label], key=lambda i: i["id"])[:n_per_class]:
            examples.append(item)
    return examples


def run_tfidf(dev_items, test_items):
    vectorizer, model = tfidf_train([i["text"] for i in dev_items], [i["doc_type"] for i in dev_items])
    t0 = time.time()
    results = tfidf_predict(vectorizer, model, [i["text"] for i in test_items])
    total_latency = time.time() - t0
    preds = [r["label"] for r in results]
    golds = [i["doc_type"] for i in test_items]
    metrics = evaluate_classification(preds, golds, LABELS)
    metrics["latency_mean"] = total_latency / len(test_items)
    metrics["latency_median"] = metrics["latency_mean"]  # single batched call, no per-doc distribution
    metrics["cost_usd_total"] = 0.0
    metrics["cost_usd_mean"] = 0.0
    metrics["n_evaluated"] = len(test_items)
    return metrics


def run_llm_method(classify_fn, items, few_shot_examples=None, method_name="method"):
    preds, latencies, costs, failures = [], [], [], []
    for item in items:
        try:
            result = classify_fn(item["text"], few_shot_examples=few_shot_examples)
            preds.append(result["label"])
            latencies.append(result["latency"])
            cost = result["usage"].get("cost_usd")
            if cost is not None:
                costs.append(cost)
        except Exception as exc:
            failures.append({"id": item["id"], "error": str(exc)})
            preds.append(None)
        time.sleep(0.5)

    golds = [i["doc_type"] for i in items]
    evaluated = [(p, g) for p, g in zip(preds, golds) if p is not None]
    metrics = evaluate_classification(
        [p for p, _ in evaluated], [g for _, g in evaluated], LABELS
    ) if evaluated else {"accuracy": 0.0, "macro_f1": 0.0, "per_class": {}, "confusion_matrix": {}, "n": 0}
    latencies_sorted = sorted(latencies)
    metrics["latency_mean"] = sum(latencies) / len(latencies) if latencies else None
    metrics["latency_median"] = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else None
    metrics["cost_usd_total"] = sum(costs) if costs else None
    metrics["cost_usd_mean"] = (sum(costs) / len(costs)) if costs else None
    metrics["n_evaluated"] = len(items)
    metrics["failures"] = failures
    return metrics


def write_raw(out_dir: Path, name: str, payload):
    raw_dir = out_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"classification-{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def write_report(out_dir: Path, results: dict, subsample_sizes: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-classification-baseline.md"
    lines = [
        "# Classification de documents — facture / contrat / rapport",
        "",
        f"Date : {date.today().isoformat()}",
        "TF-IDF+LogReg évalué sur le split test complet (gratuit, instantané). "
        "LLM/Jev évalués sur un sous-échantillon stratifié déterministe du split test "
        f"({subsample_sizes}) pour limiter le coût — jamais choisi à la main, jamais "
        "le split dev, jamais utilisé pour ajuster les prompts.",
        "Few-shot : 1 exemple par classe, tiré du split dev (jamais du test).",
        "",
        "| Méthode | N | Accuracy | Macro F1 | Latence moy. (s) | Latence médiane (s) | Coût total ($) | Coût moy./doc ($) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, m in results.items():
        cost_total = f"{m['cost_usd_total']:.6f}" if m["cost_usd_total"] is not None else "n/d"
        cost_mean = f"{m['cost_usd_mean']:.6f}" if m["cost_usd_mean"] is not None else "n/d"
        lat_mean = f"{m['latency_mean']:.3f}" if m["latency_mean"] is not None else "n/d"
        lat_med = f"{m['latency_median']:.3f}" if m["latency_median"] is not None else "n/d"
        lines.append(
            f"| {name} | {m['n_evaluated']} | {m['accuracy']:.3f} | {m['macro_f1']:.3f} "
            f"| {lat_mean} | {lat_med} | {cost_total} | {cost_mean} |"
        )
    lines.append("")

    for name, m in results.items():
        lines.append(f"## {name} — détail par classe")
        lines.append("")
        lines.append("| Classe | Précision | Rappel | F1 | Support |")
        lines.append("|---|---|---|---|---|")
        for label, pm in m["per_class"].items():
            lines.append(f"| {label} | {pm['precision']:.2f} | {pm['recall']:.2f} | {pm['f1']:.2f} | {pm['support']} |")
        lines.append("")
        lines.append("Matrice de confusion (lignes = vrai, colonnes = prédit) :")
        lines.append("")
        header = "| vrai\\prédit | " + " | ".join(LABELS) + " |"
        lines.append(header)
        lines.append("|" + "---|" * (len(LABELS) + 1))
        for gold in LABELS:
            row = [str(m["confusion_matrix"][gold][pred]) for pred in LABELS]
            lines.append(f"| {gold} | " + " | ".join(row) + " |")
        lines.append("")
        if m.get("failures"):
            lines.append(f"⚠️ {len(m['failures'])} échec(s) d'appel : {[f['id'] for f in m['failures']]}")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/synthetic")
    parser.add_argument("--out", default="docs/eval")
    args = parser.parse_args()

    items = load_classification_dataset(args.data)
    dev_items = [i for i in items if i["split"] == "dev"]
    test_items = [i for i in items if i["split"] == "test"]
    few_shot_examples = pick_few_shot_examples(dev_items)
    llm_test_subsample = stratified_subsample(test_items, LLM_SUBSAMPLE_PER_CLASS)

    print(f"dev={len(dev_items)} test={len(test_items)} llm_subsample={len(llm_test_subsample)}")

    results = {}

    print("TF-IDF + LogReg (split test complet)...")
    results["tfidf_logreg"] = run_tfidf(dev_items, test_items)

    print(f"LLM zero-shot ({len(llm_test_subsample)} docs)...")
    results["llm_zero_shot"] = run_llm_method(classify_with_llm, llm_test_subsample)

    print(f"LLM few-shot ({len(llm_test_subsample)} docs)...")
    results["llm_few_shot"] = run_llm_method(classify_with_llm, llm_test_subsample, few_shot_examples)

    print(f"Jev zero-shot ({len(llm_test_subsample)} docs)...")
    results["jev_zero_shot"] = run_llm_method(classify_with_jev, llm_test_subsample)

    print(f"Jev few-shot ({len(llm_test_subsample)} docs)...")
    results["jev_few_shot"] = run_llm_method(classify_with_jev, llm_test_subsample, few_shot_examples)

    out_dir = Path(args.out)
    write_raw(out_dir, "results", results)
    subsample_sizes = {label: sum(1 for i in llm_test_subsample if i["doc_type"] == label) for label in LABELS}
    report_path = write_report(out_dir, results, subsample_sizes)
    print(f"Rapport écrit dans {report_path}")


if __name__ == "__main__":
    main()
