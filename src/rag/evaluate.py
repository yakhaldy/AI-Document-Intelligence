"""Compare vector-only / hybrid / hybrid+rerank on the 50-question reference
set (docs/eval/rag_qa_dataset.json).

Usage:
    python -m src.rag.evaluate --qa docs/eval/rag_qa_dataset.json --out docs/eval
"""
import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.rag.bm25_search import build_bm25_index
from src.rag.generate import generate_answer
from src.rag.metrics import judge_answer, recall_at_k
from src.rag.retrieve import METHODS, retrieve

load_dotenv()


def run_one(session, bm25_index, bm25_chunks, qa_item: dict, method: str, k: int = 5) -> dict:
    t0 = time.time()
    retrieved = retrieve(session, bm25_index, bm25_chunks, qa_item["question"], method=method, k=k)
    retrieval_latency = time.time() - t0

    hit = recall_at_k(retrieved, qa_item["expected_document_id"])
    answer = generate_answer(qa_item["question"], retrieved)
    context = "\n\n".join(r["chunk"].content for r in retrieved)
    judge = judge_answer(qa_item["question"], answer["answer"], context)
    total_latency = time.time() - t0

    return {
        "recall_hit": hit,
        "faithfulness": judge["faithfulness"],
        "answer_relevancy": judge["answer_relevancy"],
        "retrieval_latency": retrieval_latency,
        "total_latency": total_latency,
        "answer": answer["answer"],
    }


def aggregate(results: list[dict]) -> dict:
    n = len(results)
    return {
        "recall@5": sum(r["recall_hit"] for r in results) / n,
        "faithfulness": sum(r["faithfulness"] for r in results) / n,
        "answer_relevancy": sum(r["answer_relevancy"] for r in results) / n,
        "retrieval_latency_mean": sum(r["retrieval_latency"] for r in results) / n,
        "total_latency_mean": sum(r["total_latency"] for r in results) / n,
        "n": n,
    }


def write_report(out_dir: Path, summary: dict, n_questions: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-rag-comparison.md"
    lines = [
        "# RAG — vecteur seul vs hybride vs hybride+rerank",
        "",
        f"Date : {date.today().isoformat()}",
        f"N = {n_questions} questions (docs/eval/rag_qa_dataset.json, k=5).",
        "Métriques faithfulness/answer_relevancy : implémentation maison "
        "inspirée de RAGAS (LLM-juge OpenRouter), pas le package `ragas` "
        "— voir src/rag/metrics.py pour pourquoi.",
        "",
        "| Méthode | recall@5 | faithfulness | answer_relevancy | latence retrieval (s) | latence totale (s) |",
        "|---|---|---|---|---|---|",
    ]
    for method, m in summary.items():
        lines.append(
            f"| {method} | {m['recall@5']:.2f} | {m['faithfulness']:.2f} "
            f"| {m['answer_relevancy']:.2f} | {m['retrieval_latency_mean']:.3f} "
            f"| {m['total_latency_mean']:.3f} |"
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="docs/eval/rag_qa_dataset.json")
    parser.add_argument("--out", default="docs/eval")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    with open(args.qa, encoding="utf-8") as fh:
        qa_items = json.load(fh)
    if args.limit:
        qa_items = qa_items[:args.limit]

    engine = create_engine(os.environ["DATABASE_URL"])
    all_results = {}
    raw_by_method = {}
    with Session(engine) as session:
        bm25_index, bm25_chunks = build_bm25_index(session)
        for method in METHODS:
            print(f"=== {method} ({len(qa_items)} questions) ===")
            results = []
            for i, qa in enumerate(qa_items):
                try:
                    results.append(run_one(session, bm25_index, bm25_chunks, qa, method, k=args.k))
                except Exception as exc:
                    print(f"  {qa['question'][:50]!r}: échec ({exc})")
                if (i + 1) % 10 == 0:
                    print(f"  {i + 1}/{len(qa_items)}")
            raw_by_method[method] = results
            all_results[method] = aggregate(results)

    out_dir = Path(args.out)
    raw_dir = out_dir / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "rag-comparison.json").write_text(
        json.dumps(raw_by_method, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_path = write_report(out_dir, all_results, len(qa_items))
    print(f"Rapport écrit dans {report_path}")


if __name__ == "__main__":
    main()
