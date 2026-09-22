"""Agent tool-selection and correctness evaluation (README §4 Étape 6).

For each question: is the RIGHT tool picked, and is the final answer
correct (checked against a known ground-truth substring, itself pulled
from query_sql/calculate directly — not invented)?

Usage:
    python -m src.agent.evaluate --out docs/eval
"""
import argparse
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import default_tenant_id
from src.agent.agent import ask_agent

load_dotenv()

TEST_CASES = [
    {
        "question": "Quel est le montant total des factures impayées ?",
        "expected_tool": "total_by_payment_status",
        "expected_answer_contains": "1 542 744,82",
    },
    {
        "question": "Quel est le montant total des factures payées ?",
        "expected_tool": "total_by_payment_status",
        "expected_answer_contains": "4 634 305,27",
    },
    {
        "question": "Combien de factures sont impayées ?",
        "expected_tool": "count_by_payment_status",
        "expected_answer_contains": "40",
    },
    {
        "question": "Quels sont les 2 fournisseurs auxquels on doit le plus au total ?",
        "expected_tool": "top_suppliers_by_total",
        "expected_answer_contains": "Doukkala Hygiène",
    },
    {
        "question": "Quel est le montant TTC de la facture FA-000089 ?",
        "expected_tool": "invoice_lookup",
        "expected_answer_contains": "1026",
    },
    {
        "question": "Combien font 43302.70 plus 1026.00 plus 8138.87 ?",
        "expected_tool": "calculate",
        "expected_answer_contains": "52467",
    },
    {
        "question": "Quelle est l'adresse du fournisseur sur la facture FAC/2025/00291 ?",
        "expected_tool": "search_documents",
        "expected_answer_contains": None,  # not in the DB schema, must go to RAG
    },
]


def run(session, tenant_id) -> list[dict]:
    results = []
    for case in TEST_CASES:
        result = ask_agent(session, tenant_id, case["question"])
        tools_called = [t["name"] for t in result["tools_used"]]
        tool_ok = case["expected_tool"] in tools_called
        answer_ok = (
            case["expected_answer_contains"] is None
            or case["expected_answer_contains"] in result["answer"]
        )
        results.append({
            "question": case["question"],
            "expected_tool": case["expected_tool"],
            "tools_called": tools_called,
            "tool_ok": tool_ok,
            "answer": result["answer"],
            "answer_ok": answer_ok,
        })
    return results


def write_report(out_dir: Path, results: list[dict]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{date.today().isoformat()}-agent-tool-selection.md"
    n = len(results)
    tool_acc = sum(r["tool_ok"] for r in results) / n
    answer_acc = sum(r["answer_ok"] for r in results) / n

    lines = [
        "# Agent — sélection d'outil et exactitude des réponses",
        "",
        f"Date : {date.today().isoformat()}",
        f"N = {n} questions.",
        "",
        f"**Bon outil choisi : {tool_acc:.0%}**  |  **Réponse correcte : {answer_acc:.0%}**",
        "",
        "| Question | Outil attendu | Outils appelés | Outil OK | Réponse OK |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['question']} | {r['expected_tool']} | {', '.join(r['tools_called']) or '—'} "
            f"| {'✓' if r['tool_ok'] else '✗'} | {'✓' if r['answer_ok'] else '✗'} |"
        )
    lines.append("")
    for r in results:
        lines.append(f"**{r['question']}**")
        lines.append(f"> {r['answer']}")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/eval")
    args = parser.parse_args()

    engine = create_engine(os.environ["DATABASE_URL"])
    tenant_id = default_tenant_id()
    with Session(engine) as session:
        results = run(session, tenant_id)

    out_dir = Path(args.out)
    (out_dir / "_raw").mkdir(parents=True, exist_ok=True)
    (out_dir / "_raw" / "agent-evaluation.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report_path = write_report(out_dir, results)
    print(f"Rapport écrit dans {report_path}")


if __name__ == "__main__":
    main()
