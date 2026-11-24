# Engineering Decision: Cross-encoder reranking experiment (M6) — not adopted; production retrieval unchanged

## Status

Chosen

(The choice: retain DECISION-017 production retrieval. The candidate
reranking configuration evaluated here is Rejected.)

## Date

2026-11-24

## Problem

DECISION-022 authorised exactly one M6 experiment — cross-encoder
reranking of the E5 top-20 pool — with the adoption bar fixed in
advance: Hit@5 must not regress, and MRR must improve by more than
~0.02 over the reproduced E5 baseline (Hit@1 20/46, Hit@5 36/46,
MRR 0.5583). The experiment has now run (task EVAL-RERANK-001,
`clinivault_ai.evaluation.rerank_experiment`). This decision records
the outcome.

## What This Part of the System Does

- What goes in: the frozen 46 cases, production E5 top-20 pools,
  chunk texts.
- What happens inside: a cross-encoder
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`, local, CPU) scores each
  (query, chunk) pair in the pool; the pool is re-ordered by that
  score and the top-5 is taken. One variable: ordering only.
- What comes out: baseline vs candidate Hit@1 / Hit@5 / MRR and
  per-case reciprocal-rank movement.
- Where the output goes next: this decision and the engineering log.
  Production code paths were never touched.

## Requirements

- One variable against the frozen 46, per §M6 and DECISION-022.
- Judge only against the pre-registered bar, not post-hoc criteria.

## Options We Considered

- Option A: Adopt reranking into production retrieval.
- Option B: Do not adopt; keep production on DECISION-017 and record
  the negative result.
- Option C: Immediately try a different reranker model.

## Comparison

| Metric | E5 baseline | Reranked candidate | Bar |
|---|---|---|---|
| Hit@1 | 20/46 | 21/46 | — |
| Hit@5 | 36/46 | **35/46** | must not regress — **failed** |
| MRR | 0.5583 | 0.5652 (+0.0069) | must improve > ~0.02 — **failed** |

Per-case movement: 10 improved, 8 regressed, 28 unchanged. The churn
is symmetric, not a systematic gain, and the regressions include the
pattern this project has seen before — narrow fixes traded for
broader damage:

- Destroyed rank-1 placements: T2D-009-statins RR 1.0000 → 0.0000
  (relevant chunk pushed out of the top-5 entirely),
  T2D-009-aspirin-primary 1.0000 → 0.0000, T2D-005-cgm-targets
  1.0000 → 0.2500.
- Real improvements: T2D-005-dka-prevention 0.0000 → 1.0000,
  T2D-007-add-on 0.5000 → 1.0000, T2D-001-type1-autoantibody
  0.5000 → 1.0000, T2D-002-lifestyle-outcomes 0.5000 → 1.0000.

Interpretation: this cross-encoder is trained on MS MARCO web-search
passages, not clinical guideline text. On this corpus it re-orders
confidently but not reliably — it separates the near-ties
DECISION-022 identified, in both directions.

Cost side: mean rerank time was ~6.1 s per query on the experiment
machine (1.5 shared vCPU, pool of 20). The absolute number is
hardware-dependent; the structural point is not — a cross-encoder
adds material per-query compute, so adoption needed a clear quality
win, not a wash.

## Decision

Do not adopt reranking. Production retrieval remains raw
`intfloat/e5-small-v2` exactly as DECISION-017 specifies. Do not run
the hybrid/BM25 experiment: DECISION-022's condition for it (a
measured lexical failure class) remains unmet, and this outcome does
not create one — task EVAL-HYBRID-001 is closed as not run, with this
reasoning as its record.

## Why We Chose It

The bar was set before the experiment precisely so this decision
would not be a matter of taste. The candidate failed both conditions.
Adopting it would trade a known Hit@5 for noise-level MRR movement
and add a second model plus per-query latency to the production path.

## Trade-offs

- The genuine improvements (dka-prevention to rank 1, three cases to
  RR 1.0) are left on the table. They are evidence that ordering help
  exists for specific cases, but not through this model.
- M6 closes with no production change. That is the correct outcome of
  a measured experiment, and it is recorded as such rather than
  quietly dropped.

## What We Did Not Choose

- Option C (another reranker immediately): a second model is a second
  experiment, not a continuation of this one. §M6's one-variable rule
  and this project's history both argue for stopping, recording, and
  letting any retry be its own decision with its own bar.
- Hybrid/BM25: still no measured lexical class (DECISION-022).

## Assumptions

- The frozen 46 remains the gate; a 1-case Hit@5 movement is within
  noise on its own, which is why the bar required both conditions.
- The experiment machine's latency figure is indicative, not a
  production measurement.

## How We Will Validate This

- The unchanged production path still reproduces the frozen numbers
  (verified in this unit: the experiment's own baseline arm ran
  20/46 · 36/46 · 0.5583, and the full unittest gate passes in the
  project's CI configuration).
- The experiment module and its output remain in the repo so the
  result is reproducible and auditable.

## When We Should Revisit It

- A reranker trained or selected for biomedical/guideline text (for
  example a BGE-family cross-encoder) may be proposed as a new
  experiment with its own decision; it must be judged especially on
  rank-1 destruction, the failure pattern seen here.
- If the benchmark grows (Stage-2 corpus), effects of this size
  become measurable rather than arguable; re-run the DECISION-022
  failure-class analysis first.
- The residual 4 DEEP_MISS cases point at label review and
  query-side questions, not at another ranker swap.
