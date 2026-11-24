"""One-variable M6 experiment: cross-encoder reranking (DECISION-022).

Evaluation-only. The baseline is production E5 retrieval exactly as
``benchmark.py`` runs it. The candidate changes exactly one variable:
the E5 top-20 pool is re-ordered by a cross-encoder scoring
(query, chunk text) pairs, and the top-5 is taken from that order.
Provider, artifacts, chunking, Top-K, and cases are unchanged. No
production wiring is touched.

Adoption bar (DECISION-022): Hit@5 must not regress and MRR must
improve by more than ~0.02 over the reproduced E5 baseline
(Hit@1 20/46, Hit@5 36/46, MRR 0.5583).

Run:
  .venv/Scripts/python -m clinivault_ai.evaluation.rerank_experiment
"""

from __future__ import annotations

import time

from . import metrics
from .benchmark import _load_store, _make_provider, _search
from .cases import CASES, BenchmarkCase

POOL = 20
TOP_K = 5
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _load_reranker(model_name: str = RERANK_MODEL):
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:  # pragma: no cover - environment guard
        raise RuntimeError(
            "sentence-transformers is required: uv sync --extra semantic"
        ) from exc
    return CrossEncoder(model_name)


def _movement(baseline_rr: float, candidate_rr: float) -> str:
    if candidate_rr > baseline_rr:
        return "improved"
    if candidate_rr < baseline_rr:
        return "regressed"
    return "unchanged"


def _score_case(store, provider, reranker, case: BenchmarkCase) -> dict:
    pool = _search(store, provider, case.query, POOL, {})
    rel = list(case.expected_chunk_ids)

    baseline_ranked = [r["chunk_id"] for r in pool[:TOP_K]]
    started = time.perf_counter()
    scores = reranker.predict([(case.query, r["text"]) for r in pool])
    rerank_seconds = time.perf_counter() - started
    order = sorted(range(len(pool)), key=lambda i: -float(scores[i]))
    candidate_ranked = [pool[i]["chunk_id"] for i in order[:TOP_K]]

    base_rr = metrics.reciprocal_rank(baseline_ranked, rel)
    cand_rr = metrics.reciprocal_rank(candidate_ranked, rel)
    movement = _movement(base_rr, cand_rr)
    return {
        "case_id": case.case_id,
        "document_id": case.document_id,
        "baseline_top5": baseline_ranked,
        "candidate_top5": candidate_ranked,
        "baseline_rr": base_rr,
        "candidate_rr": cand_rr,
        "baseline_hit1": metrics.hit_at_k(baseline_ranked, rel, 1),
        "candidate_hit1": metrics.hit_at_k(candidate_ranked, rel, 1),
        "baseline_hit5": metrics.hit_at_k(baseline_ranked, rel, TOP_K),
        "candidate_hit5": metrics.hit_at_k(candidate_ranked, rel, TOP_K),
        "movement": movement,
        "rerank_seconds": rerank_seconds,
    }


def run_experiment(cases: tuple[BenchmarkCase, ...] = CASES,
                   model_name: str = RERANK_MODEL) -> dict:
    provider = _make_provider("e5")
    reranker = _load_reranker(model_name)
    stores: dict[str, object] = {}
    results = []
    for case in cases:
        if case.document_id not in stores:
            stores[case.document_id] = _load_store(case.document_id, "e5")
        results.append(_score_case(stores[case.document_id], provider,
                                   reranker, case))

    def aggregate(key_prefix: str) -> dict:
        return {
            "hit1": sum(r[f"{key_prefix}_hit1"] for r in results),
            "hit5": sum(r[f"{key_prefix}_hit5"] for r in results),
            "mrr": metrics.mrr([r[f"{key_prefix}_rr"] for r in results]),
        }

    movements = {"improved": 0, "regressed": 0, "unchanged": 0}
    for r in results:
        movements[r["movement"]] += 1
    return {
        "model": model_name,
        "pool": POOL,
        "n_cases": len(results),
        "baseline": aggregate("baseline"),
        "candidate": aggregate("candidate"),
        "movements": movements,
        "mean_rerank_seconds": (sum(r["rerank_seconds"] for r in results)
                                / len(results)),
        "results": results,
    }


def main() -> int:
    report = run_experiment()
    b, c = report["baseline"], report["candidate"]
    n = report["n_cases"]
    print(f"model={report['model']} pool={report['pool']} cases={n}")
    print(f"baseline (E5):        Hit@1={b['hit1']}/{n}  "
          f"Hit@5={b['hit5']}/{n}  MRR={b['mrr']:.4f}")
    print(f"candidate (reranked): Hit@1={c['hit1']}/{n}  "
          f"Hit@5={c['hit5']}/{n}  MRR={c['mrr']:.4f}")
    print(f"movements: {report['movements']}")
    print(f"mean rerank time per query: "
          f"{report['mean_rerank_seconds'] * 1000:.0f} ms (CPU, pool of "
          f"{report['pool']})")
    for r in report["results"]:
        if r["movement"] != "unchanged":
            print(f"{r['case_id']}: {r['movement']} "
                  f"rr {r['baseline_rr']:.4f} -> {r['candidate_rr']:.4f}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
