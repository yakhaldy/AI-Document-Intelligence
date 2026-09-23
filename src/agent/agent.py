"""Agent orchestrator: routes a question to the right tool via OpenRouter
function-calling. Never computes a figure itself (README §1) — every number
in the final answer must come from query_sql or calculate.
"""
import json
import os

import requests
from dotenv import load_dotenv
from langfuse import observe
from sqlalchemy.orm import Session

from src.agent.calculate import calculate
from src.agent.query_sql import (
    count_by_payment_status,
    invoice_lookup,
    top_suppliers_by_total,
    total_by_payment_status,
)
from src.agent.search_documents import search_documents

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_INSTRUCTION = (
    "Tu es un agent qui répond à des questions sur des factures marocaines. "
    "Choisis TOUJOURS l'outil approprié :\n"
    "- search_documents : question sur le contenu textuel d'un document "
    "(qui, quoi, quand, sur une facture précise).\n"
    "- total_by_payment_status / count_by_payment_status / top_suppliers_by_total "
    "/ invoice_lookup : tout chiffre agrégé ou exact depuis la base de "
    "données (totaux, comptages, classements).\n"
    "- calculate : toute opération arithmétique sur des nombres que tu as "
    "déjà obtenus.\n"
    "Ne calcule JAMAIS un montant toi-même, même une simple addition — "
    "utilise toujours calculate. N'invente aucun chiffre : s'il ne vient "
    "pas d'un outil, ne l'affirme pas."
)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Recherche dans le texte des documents (RAG) et répond avec citation de source.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "total_by_payment_status",
            "description": "Somme des montants TTC des factures payées ou impayées, avec filtre optionnel année/mois.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["paid", "unpaid"]},
                    "year": {"type": "integer"},
                    "month": {"type": "integer"},
                },
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_by_payment_status",
            "description": "Nombre de factures payées ou impayées.",
            "parameters": {
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["paid", "unpaid"]}},
                "required": ["status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "invoice_lookup",
            "description": "Détails d'une facture par son numéro exact.",
            "parameters": {
                "type": "object",
                "properties": {"invoice_number": {"type": "string"}},
                "required": ["invoice_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_suppliers_by_total",
            "description": "Classement des fournisseurs par montant total facturé (ex. 'à qui doit-on le plus ?').",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer"},
                    "payment_status": {"type": "string", "enum": ["paid", "unpaid"]},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Évalue une expression arithmétique exacte (+ - * /).",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    },
]


def _api_key() -> str:
    key = os.environ.get("LLM_OPNEROUTER_API_KEY")
    if not key:
        raise RuntimeError("LLM_OPNEROUTER_API_KEY manquant (voir .env)")
    return key


def _execute_tool(session: Session, tenant_id, name: str, args: dict):
    if name == "search_documents":
        return search_documents(session, args["query"])
    if name == "total_by_payment_status":
        return total_by_payment_status(tenant_id, args["status"], args.get("year"), args.get("month"))
    if name == "count_by_payment_status":
        return count_by_payment_status(tenant_id, args["status"])
    if name == "invoice_lookup":
        return invoice_lookup(tenant_id, args["invoice_number"])
    if name == "top_suppliers_by_total":
        return top_suppliers_by_total(tenant_id, args.get("limit", 5), args.get("payment_status"))
    if name == "calculate":
        return calculate(args["expression"])
    raise ValueError(f"outil inconnu : {name}")


@observe(name="agent.ask", as_type="agent")
def ask_agent(session: Session, tenant_id, question: str, model: str | None = None, max_rounds: int = 4) -> dict:
    model = model or os.environ.get("LLM_OPNEROUTER_MODEL", "openai/gpt-4o-mini")
    headers = {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": question},
    ]
    tools_used = []

    for _ in range(max_rounds):
        resp = requests.post(
            API_URL,
            headers=headers,
            json={"model": model, "messages": messages, "tools": TOOL_SCHEMAS, "temperature": 0},
            timeout=60,
        )
        resp.raise_for_status()
        message = resp.json()["choices"][0]["message"]
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return {"answer": message["content"], "tools_used": tools_used}

        messages.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            tools_used.append({"name": name, "args": args})
            try:
                result = _execute_tool(session, tenant_id, name, args)
            except Exception as exc:
                result = {"error": str(exc)}
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

    return {"answer": "Nombre maximal d'étapes atteint sans réponse finale.", "tools_used": tools_used}
