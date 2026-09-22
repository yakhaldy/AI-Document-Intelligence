"""Embeddings via OpenRouter (openai/text-embedding-3-small, 1024 dims).

Switched from Gemini's gemini-embedding-001 (Étape 4) after its free-tier
daily quota (1000 req/day) ran out mid-session. IMPORTANT: a vector store
must use ONE embedding model consistently — mixing two models' vectors in
the same column silently breaks similarity search (different vector
spaces), even at the same dimension. db/index_chunks.py re-embeds
everything with this provider rather than only filling the gap.

Batched per document (one API call for all of a document's chunks).
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIM = 1024  # matches db/models.py DocumentChunk.embedding — README §3 VECTOR(1024)


def _api_key() -> str:
    key = os.environ.get("LLM_OPNEROUTER_API_KEY")
    if not key:
        raise RuntimeError("LLM_OPNEROUTER_API_KEY manquant (voir .env)")
    return key


def embed_batch(texts: list[str], retries: int = 3) -> list[list[float]]:
    if not texts:
        return []
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {"model": EMBEDDING_MODEL, "input": texts, "dimensions": EMBEDDING_DIM}

    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            by_index = sorted(data["data"], key=lambda d: d["index"])
            return [d["embedding"] for d in by_index]
        except (requests.RequestException, KeyError) as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Échec de l'appel d'embedding après {retries} tentatives : {last_error}")


def embed_query(text: str) -> list[float]:
    return embed_batch([text])[0]
