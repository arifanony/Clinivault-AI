"""Benchmark metrics: pure functions over ranked chunk-ID lists.

All functions treat ``ranked`` as a best-first list of chunk IDs and
``relevant`` as a set-like iterable of expected-relevant chunk IDs.
Validation: ``relevant`` must be non-empty and duplicate-free; ``ranked``
must be duplicate-free. Deterministic: no randomness, no timestamps.
"""

from __future__ import annotations


def _validate(ranked: list[str], relevant: list[str]) -> set[str]:
    if not relevant:
        raise ValueError("relevant set must be non-empty")
    if len(set(relevant)) != len(relevant):
        raise ValueError(f"duplicate relevant ids: {relevant}")
    if len(set(ranked)) != len(ranked):
        raise ValueError(f"duplicate ranked ids: {ranked}")
    return set(relevant)


def first_relevant_rank(ranked: list[str], relevant: list[str]) -> int | None:
    """1-based rank of the highest-ranked relevant id, or None if absent."""
    rel = _validate(ranked, relevant)
    for rank, chunk_id in enumerate(ranked, 1):
        if chunk_id in rel:
            return rank
    return None


def all_relevant_ranks(ranked: list[str], relevant: list[str]) -> list[int]:
    """Sorted 1-based ranks of every relevant id present in ``ranked``."""
    rel = _validate(ranked, relevant)
    return [r for r, cid in enumerate(ranked, 1) if cid in rel]


def hit_at_k(ranked: list[str], relevant: list[str], k: int) -> int:
    """1 if at least one relevant id appears within the first k ranks."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError(f"k must be a positive integer, got {k!r}")
    rank = first_relevant_rank(ranked, relevant)
    return 1 if rank is not None and rank <= k else 0


def reciprocal_rank(ranked: list[str], relevant: list[str]) -> float:
    """1 / rank of the first relevant id; 0.0 if no relevant id is ranked."""
    rank = first_relevant_rank(ranked, relevant)
    return 0.0 if rank is None else 1.0 / rank


def mrr(reciprocal_ranks: list[float]) -> float:
    """Mean of reciprocal ranks; raises on empty input (no silent mean)."""
    if not reciprocal_ranks:
        raise ValueError("reciprocal_ranks must be non-empty")
    return sum(reciprocal_ranks) / len(reciprocal_ranks)
