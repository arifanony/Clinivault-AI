"""Offline benchmark runner over the persisted corpus artifacts.

Uses persisted parsed + embedding artifacts, VectorStore, and search().
Top-K=5 (production value, unchanged). Default ``--provider hash`` keeps
the historical hash numbers runnable. ``--provider e5`` reads the
EVAL-HF durable tree and uses ``E5EmbeddingProvider`` (DECISION-017).

Run:
  .venv/Scripts/python -m clinivault_ai.evaluation.benchmark
  .venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cases import CASES, BenchmarkCase
from . import metrics

DATA = Path("data")
PARSED = DATA / "parsed" / "stage-1-clean-baseline-corpus"
HASH_EMBEDDED = DATA / "embedded" / "stage-1-clean-baseline-corpus"
E5_EMBEDDED = DATA / "embedded-intfloat--e5-small-v2" / "stage-1-clean-baseline-corpus"
TOP_K = 5


def _embedding_dir(provider_name: str) -> Path:
    if provider_name == "e5":
        return E5_EMBEDDED
    if provider_name == "hash":
        return HASH_EMBEDDED
    raise ValueError(f"unknown provider {provider_name!r}")


def _make_provider(provider_name: str):
    from clinivault_ai.embedding import BaselineHashEmbeddingProvider, E5EmbeddingProvider

    if provider_name == "e5":
        return E5EmbeddingProvider()
    if provider_name == "hash":
        return BaselineHashEmbeddingProvider()
    raise ValueError(f"unknown provider {provider_name!r}")


def _load_store(document_id: str, provider_name: str = "hash"):
    from clinivault_ai.chunking import chunk_pages, default_config
    from clinivault_ai.retrieval.store import VectorStore

    parsed = json.loads((PARSED / document_id / f"{document_id}.parsed.json")
                        .read_text(encoding="utf-8"))
    chunks = chunk_pages(parsed, default_config())
    embedded = _embedding_dir(provider_name)
    art = json.loads((embedded / document_id / f"{document_id}.embeddings.json")
                     .read_text(encoding="utf-8"))
    return VectorStore.from_artifacts(art, chunks)


def run_benchmark(cases: tuple[BenchmarkCase, ...] = CASES,
                  top_k: int = TOP_K,
                  provider_name: str = "hash") -> dict:
    """Run every case offline and return the aggregate + per-case results."""
    provider = _make_provider(provider_name)
    stores: dict[str, object] = {}
    results = []
    for case in cases:
        if case.document_id not in stores:
            stores[case.document_id] = _load_store(case.document_id, provider_name)
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
    parser = argparse.ArgumentParser(description="Clinivault retrieval benchmark")
    parser.add_argument("--provider", choices=("hash", "e5"), default="hash")
    args = parser.parse_args()
    report = run_benchmark(provider_name=args.provider)
    print(f"provider={args.provider} cases={report['n_cases']} docs={len(report['documents'])}")
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
