"""Offline benchmark runner over the persisted corpus artifacts.

Uses only persisted parsed + embedding artifacts, the existing
BaselineHashEmbeddingProvider, VectorStore, and search(). Top-K=5
(production value, unchanged). For cases whose expected evidence is
absent from Top-5, a full-ranking inspection (top_k = index size) is
performed as DIAGNOSTIC MEASUREMENT ONLY — the production Top-K is not
changed. No network, no generation, deterministic.

Run: .venv/Scripts/python -m clinivault_ai.evaluation.benchmark
"""

from __future__ import annotations

import json
from pathlib import Path

from .cases import CASES, BenchmarkCase
from . import metrics

DATA = Path("data")
PARSED = DATA / "parsed" / "stage-1-clean-baseline-corpus"
EMBEDDED = DATA / "embedded" / "stage-1-clean-baseline-corpus"
TOP_K = 5


def _load_store(document_id: str):
    from clinivault_ai.chunking import chunk_pages, default_config
    from clinivault_ai.retrieval.store import VectorStore

    parsed = json.loads((PARSED / document_id / f"{document_id}.parsed.json")
                        .read_text(encoding="utf-8"))
    chunks = chunk_pages(parsed, default_config())
    art = json.loads((EMBEDDED / document_id / f"{document_id}.embeddings.json")
                     .read_text(encoding="utf-8"))
    return VectorStore.from_artifacts(art, chunks)


def run_benchmark(cases: tuple[BenchmarkCase, ...] = CASES,
                  top_k: int = TOP_K) -> dict:
    """Run every case offline and return the aggregate + per-case results."""
    from clinivault_ai.embedding import BaselineHashEmbeddingProvider

    provider = BaselineHashEmbeddingProvider()
    stores: dict[str, object] = {}
    results = []
    for case in cases:
        if case.document_id not in stores:
            stores[case.document_id] = _load_store(case.document_id)
        store = stores[case.document_id]

        trace: dict = {}
        top = _search(store, provider, case.query, top_k, trace)
        ranked = [r["chunk_id"] for r in top]
        rel = list(case.expected_chunk_ids)

        first_rank = metrics.first_relevant_rank(ranked, rel)
        record = {
            "case_id": case.case_id,
            "document_id": case.document_id,
            "query": case.query,
            "expected": rel,
            "top5": ranked,
            "top5_scores": [round(r["score"], 4) for r in top],
            "hit1": metrics.hit_at_k(ranked, rel, 1),
            "hit5": metrics.hit_at_k(ranked, rel, top_k),
            "reciprocal_rank": metrics.reciprocal_rank(ranked, rel),
            "first_relevant_rank": first_rank,
            "all_relevant_ranks_in_top5": metrics.all_relevant_ranks(ranked, rel),
            "ambiguous": case.ambiguous,
            "note": case.note,
            "label_source": case.label_source,
        }
        if first_rank is None:
            full = _search(store, provider, case.query, len(store.records), {})
            full_ranked = [r["chunk_id"] for r in full]
            record["full_rank_of_expected"] = {
                cid: (full_ranked.index(cid) + 1 if cid in full_ranked else None)
                for cid in rel
            }
        results.append(record)

    rrs = [r["reciprocal_rank"] for r in results]
    return {
        "n_cases": len(results),
        "documents": sorted({r["document_id"] for r in results}),
        "hit1": sum(r["hit1"] for r in results),
        "hit5": sum(r["hit5"] for r in results),
        "mrr": metrics.mrr(rrs),
        "results": results,
    }


def _search(store, provider, query, top_k, trace):
    from clinivault_ai.retrieval import search
    return search(store, query, provider, top_k, trace=trace)


def main() -> int:
    report = run_benchmark()
    print(f"cases={report['n_cases']} docs={len(report['documents'])}")
    print(f"Hit@1={report['hit1']}/{report['n_cases']}  "
          f"Hit@5={report['hit5']}/{report['n_cases']}  MRR={report['mrr']:.4f}")
    for r in report["results"]:
        flag = " [AMBIGUOUS]" if r["ambiguous"] else ""
        print(f"{r['case_id']}: hit5={r['hit5']} hit1={r['hit1']} "
              f"rr={r['reciprocal_rank']:.4f} first_rel_rank={r['first_relevant_rank']}{flag}")
        if "full_rank_of_expected" in r:
            print(f"    full-ranking inspection: {r['full_rank_of_expected']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
