"""Embeddings via the Gemini API (gemini-embedding-001), batched per document
— one API call for all of a document's chunks, not one call per chunk.
"""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 1024  # matches db/models.py DocumentChunk.embedding — README §3 VECTOR(1024)


def _api_key() -> str:
    key = os.environ.get("LLM_API_KEY")
    if not key:
        raise RuntimeError("LLM_API_KEY manquant (voir .env)")
    return key


def embed_batch(texts: list[str], retries: int = 3) -> list[list[float]]:
    if not texts:
        return []
    url = f"{API_BASE}/{EMBEDDING_MODEL}:batchEmbedContents?key={_api_key()}"
    payload = {
        "requests": [
            {
                "model": f"models/{EMBEDDING_MODEL}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": EMBEDDING_DIM,
            }
            for text in texts
        ]
    }

    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            data = resp.json()
            return [e["values"] for e in data["embeddings"]]
        except (requests.RequestException, KeyError) as exc:
            last_error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Échec de l'appel d'embedding après {retries} tentatives : {last_error}")
