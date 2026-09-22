"""Hybrid search: Reciprocal Rank Fusion of vector + BM25 result lists.

RRF score(d) = sum over each ranked list L containing d of 1 / (K + rank_L(d))
K=60 is the standard default from the original RRF paper (Cormack et al.).
"""
K_CONST = 60


def reciprocal_rank_fusion(*ranked_lists: list[dict], k: int = 5) -> list[dict]:
    scores: dict[int, float] = {}
    chunks_by_id = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            chunk = item["chunk"]
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1 / (K_CONST + rank)
            chunks_by_id[chunk.id] = chunk

    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
    return [{"chunk": chunks_by_id[chunk_id], "score": score} for chunk_id, score in ordered]
