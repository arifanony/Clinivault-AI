"""Failure-class analysis of the frozen 46-case retrieval benchmark.

Reopens M6 the way ``docs/engineering-log/2026-11-10-m6-deferred.md``
requires: before any retrieval experiment, classify every imperfect case
so the weakness is measured, not guessed. Uses the identical protocol to
``benchmark.py`` (same per-document stores, same ``search()``), so the
classes describe the frozen benchmark exactly.

Classes, by the full-corpus rank of the best-ranked expected chunk:

  HIT1       rank 1 — no failure.
  RANKING    rank 2-5 — relevant evidence is retrieved inside the
             production top-5 but ordered below other chunks.
             Candidate fix: reranking.
  NEAR_MISS  rank 6-20 — outside the production top-5 but inside a
             practical rerank pool. Candidate fix: rerank a wider pool.
  DEEP_MISS  rank >20 or absent — semantic/lexical gap, chunking, or a
             label problem. Candidate fixes: hybrid retrieval, chunking,
             or label review. Reranking a top-20 pool cannot fix these.

Two heuristic evidence flags are attached for human review (they are
signals, not verdicts):

  BOUNDARY_SUSPECT — a chunk adjacent to the best expected chunk carries
             at least two query content terms the expected chunk itself
             lacks, suggesting the answer may span a chunk boundary.
  LABEL_REVIEW — the case was already recorded ``ambiguous`` in
             ``cases.py``; its labels are known to be partial.

Run:
  .venv/Scripts/python -m clinivault_ai.evaluation.failure_analysis --provider e5
"""

from __future__ import annotations

import argparse
import re

from .benchmark import _load_store, _make_provider, _search
from .cases import CASES, BenchmarkCase

RERANK_POOL = 20

_STOPWORDS = frozenset({
    "a", "an", "the", "of", "for", "in", "on", "to", "and", "or", "is",
    "are", "with", "what", "which", "how", "does", "do", "should", "be",
    "by", "at", "from", "as", "it", "its", "this", "that",
})


def classify_rank(first_rank: int | None) -> str:
    """Map the best expected chunk's full rank to its failure class."""
    if first_rank is None:
        return "DEEP_MISS"
    if first_rank == 1:
        return "HIT1"
    if first_rank <= 5:
        return "RANKING"
    if first_rank <= RERANK_POOL:
        return "NEAR_MISS"
    return "DEEP_MISS"


def _content_terms(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower())
            if t not in _STOPWORDS and len(t) > 2}


def analyse_case(store, provider, case: BenchmarkCase) -> dict:
    """Full-ranking inspection of one case against its document store."""
    full = _search(store, provider, case.query, len(store.records), {})
    ranked_ids = [r["chunk_id"] for r in full]
    scores = {r["chunk_id"]: r["score"] for r in full}
    by_id = {r["chunk_id"]: r for r in store.records}

    expected = list(case.expected_chunk_ids)
    ranks = {cid: (ranked_ids.index(cid) + 1 if cid in ranked_ids else None)
             for cid in expected}
    present = {cid: r for cid, r in ranks.items() if r is not None}
    best_id = min(present, key=present.get) if present else None
    first_rank = present[best_id] if best_id else None
    failure_class = classify_rank(first_rank)

    query_terms = _content_terms(case.query)
    flags: list[str] = []
    detail: dict = {"expected_ranks": ranks,
                    "best_expected_chunk": best_id,
                    "score_gap_to_rank1": None,
                    "boundary_terms_in_neighbours": []}
    if best_id is not None:
        detail["score_gap_to_rank1"] = round(
            full[0]["score"] - scores[best_id], 4)
        expected_terms = _content_terms(by_id[best_id]["text"])
        detail["query_terms_missing_from_expected"] = sorted(
            query_terms - expected_terms)
        # Boundary heuristic: query terms carried by an adjacent chunk
        # but absent from the expected chunk itself.
        order = [r["chunk_id"] for r in store.records]
        pos = order.index(best_id)
        neighbour_terms: set[str] = set()
        for neighbour_pos in (pos - 1, pos + 1):
            if 0 <= neighbour_pos < len(order):
                neighbour_terms |= _content_terms(
                    by_id[order[neighbour_pos]]["text"])
        boundary_terms = sorted((query_terms & neighbour_terms)
                                - expected_terms)
        detail["boundary_terms_in_neighbours"] = boundary_terms
        if len(boundary_terms) >= 2:
            flags.append("BOUNDARY_SUSPECT")
    if case.ambiguous:
        flags.append("LABEL_REVIEW")

    return {
        "case_id": case.case_id,
        "document_id": case.document_id,
        "query": case.query,
        "class": failure_class,
        "first_relevant_rank": first_rank,
        "flags": flags,
        **detail,
    }


def run_analysis(provider_name: str = "e5",
                 cases: tuple[BenchmarkCase, ...] = CASES) -> dict:
    provider = _make_provider(provider_name)
    stores: dict[str, object] = {}
    results = []
    for case in cases:
        if case.document_id not in stores:
            stores[case.document_id] = _load_store(case.document_id,
                                                   provider_name)
        results.append(analyse_case(stores[case.document_id], provider, case))
    counts: dict[str, int] = {}
    for r in results:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    return {"provider": provider_name, "n_cases": len(results),
            "counts": counts, "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clinivault retrieval failure-class analysis")
    parser.add_argument("--provider", choices=("hash", "e5"), default="e5")
    args = parser.parse_args()
    report = run_analysis(provider_name=args.provider)
    print(f"provider={args.provider} cases={report['n_cases']}")
    print("class counts: " + "  ".join(
        f"{k}={v}" for k, v in sorted(report["counts"].items())))
    for r in report["results"]:
        if r["class"] == "HIT1":
            continue
        flags = f" flags={','.join(r['flags'])}" if r["flags"] else ""
        print(f"{r['case_id']}: {r['class']} rank={r['first_relevant_rank']} "
              f"gap={r['score_gap_to_rank1']}{flags}")
        print(f"    expected_ranks={r['expected_ranks']}")
        if r["boundary_terms_in_neighbours"]:
            print(f"    boundary_terms={r['boundary_terms_in_neighbours']}")
        if r.get("query_terms_missing_from_expected"):
            print(f"    query_terms_missing_from_expected="
                  f"{r['query_terms_missing_from_expected']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
