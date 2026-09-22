"""Document classification via Jev (TypeSafe AI's System One model).

One API call per document: a single `Choice` question with the 3 categories
as criteria — System One returns a typed label with calibrated
probabilities directly, no need for multiple yes/no questions per document.

The document text is untrusted input (README §2.3): passed as the `state`
(data for the model to evaluate), never as an instruction.
"""
import os
import time

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

load_dotenv()

LABELS = ["facture", "contrat", "rapport"]

CRITERIA = {
    "facture": "Facture commerciale : montants, TVA, ICE, fournisseur, lignes de produits/services facturés",
    "contrat": "Contrat juridique entre deux parties : articles, clauses, engagements, signatures",
    "rapport": "Rapport ou compte-rendu narratif : audit, activité, mission, réunion, incident, analyse",
}

INSTRUCTIONS = "Quel type de document marocain est ceci ?"

_client = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        api_key = os.environ.get("TYPESAFE_API_KEY")
        if not api_key:
            raise RuntimeError("TYPESAFE_API_KEY manquant (voir .env)")
        _client = TypeSafeClient(api_key=api_key)
    return _client


def _build_state(text: str, few_shot_examples: list[dict] | None) -> str:
    if not few_shot_examples:
        return text
    parts = ["Exemples déjà classés :\n"]
    for ex in few_shot_examples:
        parts.append(f"--- Exemple ({ex['doc_type']}) ---\n{ex['text'][:800]}\n")
    parts.append("\nDocument à classer :\n")
    parts.append(text)
    return "\n".join(parts)


def classify_with_jev(
    text: str,
    few_shot_examples: list[dict] | None = None,
    model: str | None = None,
) -> dict:
    client = _get_client()
    t0 = time.time()
    resp = client.system_one(
        state=_build_state(text, few_shot_examples),
        questions={
            "doc_type": Choice(instructions=INSTRUCTIONS, criteria=CRITERIA),
        },
        model=model,
    )
    latency = time.time() - t0
    answer = resp.answers["doc_type"]
    return {
        "label": answer.choice,
        "scores": dict(answer.probabilities),
        "latency": latency,
        "usage": {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
        },
    }
