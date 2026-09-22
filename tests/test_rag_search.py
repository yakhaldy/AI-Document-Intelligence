from types import SimpleNamespace

from src.rag.bm25_search import bm25_search, tokenize
from src.rag.hybrid_search import reciprocal_rank_fusion
from rank_bm25 import BM25Okapi


def test_tokenize_lowercases_and_splits_on_punctuation():
    assert tokenize("Facture N° FAC/2025-001, TVA 20%") == [
        "facture", "n", "fac", "2025", "001", "tva", "20",
    ]


def _fake_chunk(id_, content):
    return SimpleNamespace(id=id_, content=content)


def test_bm25_search_ranks_matching_chunk_first():
    chunks = [
        _fake_chunk(1, "Contrat de bail commercial entre les parties"),
        _fake_chunk(2, "Facture ICE TVA Total HT Total TTC montant"),
        _fake_chunk(3, "Rapport d'audit interne constats recommandations"),
    ]
    index = BM25Okapi([tokenize(c.content) for c in chunks])
    results = bm25_search(index, chunks, "quel est le montant total de la facture TTC", k=2)
    assert results[0]["chunk"].id == 2


def test_reciprocal_rank_fusion_boosts_items_agreed_on_by_both_lists():
    a = _fake_chunk(1, "")
    b = _fake_chunk(2, "")
    c = _fake_chunk(3, "")
    vector_results = [{"chunk": a, "score": 0.9}, {"chunk": b, "score": 0.8}]
    bm25_results = [{"chunk": b, "score": 5.0}, {"chunk": c, "score": 4.0}]
    fused = reciprocal_rank_fusion(vector_results, bm25_results, k=3)
    # b appears rank 2 in vector and rank 1 in bm25 -> highest combined score
    assert fused[0]["chunk"].id == 2


def test_reciprocal_rank_fusion_respects_k_limit():
    chunks = [_fake_chunk(i, "") for i in range(10)]
    ranked = [{"chunk": c, "score": 1.0} for c in chunks]
    fused = reciprocal_rank_fusion(ranked, k=3)
    assert len(fused) == 3
