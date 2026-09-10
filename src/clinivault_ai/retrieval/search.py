"""Baseline similarity search: query text -> top-k chunks with provenance.

Flow (the provider seam is REUSED -- no second embedding implementation):

    query text
      -> existing EmbeddingProvider (query embedding)
      -> cosine similarity against the in-memory index
      -> deterministic ranking, top-k
      -> results with chunk_id + document_id + page_number + score + text

Similarity metric: **cosine**. The baseline provider emits L2-normalized
vectors, where cosine equals the dot product; cosine is chosen anyway so
the metric stays mathematically correct for any (non-zero) provider
vectors, not only normalized ones.

Determinism: scores are plain float arithmetic; ranking is
``(-score, chunk_id)`` so ties break deterministically by chunk_id.
Ranking is brute force -- deliberately, at this scale and stage.

top_k is explicit: values < 1 or exceeding the number of indexed records
raise RetrievalError rather than being clamped silently.
"""

from __future__ import annotations

from clinivault_ai.retrieval.errors import RetrievalError
from clinivault_ai.retrieval.store import VectorStore, _validate_vector


def search(
    store: VectorStore,
    query: str,
    provider,
    top_k: int,
) -> list[dict]:
    """Embed ``query`` via the provider seam and return the top-k matches.

    Results are ordered best-first, each:
    ``{chunk_id, document_id, page_number, score, text}``.

    Provider failures (e.g. EmbeddingError) propagate unchanged; query
    vectors are re-validated against the index dimension.
    """
    if not isinstance(query, str) or not query.strip():
        raise RetrievalError("query must be a non-empty string")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise RetrievalError(f"top_k must be a positive integer, got {top_k!r}")
    if top_k > len(store.records):
        raise RetrievalError(
            f"top_k {top_k} exceeds the number of indexed records ({len(store.records)})"
        )

    query_vector = provider.embed_texts([query])[0]
    query_vector = _validate_vector(
        query_vector, store.dimension, f"query {query!r}"
    )
    query_norm = sum(v * v for v in query_vector) ** 0.5

    scored = []
    for record in store.records:
        dot = sum(a * b for a, b in zip(query_vector, record["vector"]))
        score = dot / (query_norm * record["norm"])
        scored.append((score, record["chunk_id"], record))

    # Deterministic ranking: descending score, ties broken by chunk_id.
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        {
            "chunk_id": chunk_id,
            "document_id": store.document_id,
            "page_number": record["page_number"],
            "score": score,
            "text": record["text"],
        }
        for score, chunk_id, record in scored[:top_k]
    ]
