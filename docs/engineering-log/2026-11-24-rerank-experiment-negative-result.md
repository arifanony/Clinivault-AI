# Cross-encoder reranking experiment — negative result, not adopted

## Date

2026-11-24

## Where It Happened

Retrieval evaluation (`src/clinivault_ai/evaluation/rerank_experiment.py`,
task EVAL-RERANK-001), frozen 46-case benchmark. Evaluation-only; no
production code was touched.

## What We Expected

DECISION-022's failure-class analysis showed 22 of 26 imperfect cases
hold a relevant chunk inside the E5 top-20, with near-tie cosine gaps.
A cross-encoder was expected to separate those ties systematically:
Hit@5 held or improved, MRR up by more than ~0.02 (the pre-registered
adoption bar).

## What Actually Happened

The candidate re-ordered confidently in both directions. Aggregate:
Hit@1 20/46 → 21/46, **Hit@5 36/46 → 35/46 (regression)**, MRR
0.5583 → 0.5652 (+0.0069, below the bar). Movement: 10 improved,
8 regressed, 28 unchanged. Both adoption conditions failed, so
DECISION-023 records the candidate as rejected and production stays
on DECISION-017.

## Evidence

Module run, 2026-11-24 (`cross-encoder/ms-marco-MiniLM-L-6-v2`,
pool 20, CPU):

```
baseline (E5):        Hit@1=20/46  Hit@5=36/46  MRR=0.5583
candidate (reranked): Hit@1=21/46  Hit@5=35/46  MRR=0.5652
movements: {'improved': 10, 'regressed': 8, 'unchanged': 28}
mean rerank time per query: 6081 ms (CPU, pool of 20)
```

Changed cases (reciprocal rank, baseline → candidate):

| Case | Movement | RR |
|---|---|---|
| T2D-005-dka-prevention | improved | 0.0000 → 1.0000 |
| T2D-007-add-on | improved | 0.5000 → 1.0000 |
| T2D-001-type1-autoantibody | improved | 0.5000 → 1.0000 |
| T2D-002-lifestyle-outcomes | improved | 0.5000 → 1.0000 |
| T2D-003-hba1c-accuracy | improved | 0.0000 → 0.5000 |
| T2D-008-weight | improved | 0.2000 → 0.5000 |
| T2D-003-hba1c-optimal-threshold | improved | 0.2500 → 0.5000 |
| T2D-008-sglt2-kidney-nma | improved | 0.2000 → 0.5000 |
| T2D-007-first-line | improved | 0.2500 → 0.3333 |
| T2D-006-insulin-initiation | improved | 0.0000 → 0.2500 |
| T2D-009-statins | regressed | 1.0000 → 0.0000 |
| T2D-009-aspirin-primary | regressed | 1.0000 → 0.0000 |
| T2D-005-cgm-targets | regressed | 1.0000 → 0.2500 |
| T2D-001-gdm | regressed | 0.5000 → 0.2500 |
| T2D-010-ckd-screening | regressed | 0.3333 → 0.0000 |
| T2D-003-fpg-optimal-cutoff | regressed | 0.2000 → 0.0000 |
| T2D-010-kidney-protection | regressed | 0.5000 → 0.3333 |
| T2D-009-sglt2-heart-failure | regressed | 0.5000 → 0.3333 |

## What We Investigated

- Whether the movement was concentrated in the RANKING/NEAR_MISS
  classes DECISION-022 targeted (partly — dka-prevention and
  insulin-initiation were NEAR_MISS recoveries).
- Whether regressions were mild (they were not: three cases fell
  from RR 1.0, two of them out of the top-5 entirely).

## What We Tried

Exactly the one authorised variable: cross-encoder ordering of the
top-20 pool. No threshold tuning, no blend with cosine scores, no
second model — each would have been a different experiment.

## What Failed

The candidate, against its pre-registered bar. Likely mechanism: the
model is trained on MS MARCO web-search passages; clinical guideline
chunks are out of its distribution, so its pairwise preferences are
confident but unreliable on this corpus. The shape of the result —
symmetric churn with rank-1 destruction — matches the project's
earlier controlled-comparison lesson (2026-09-21): counterfactuals
that fixed narrow cases while regressing broader ones.

## The Fix

None to production — that is the outcome. DECISION-023 retains
DECISION-017 unchanged and closes EVAL-HYBRID-001 as not run
(DECISION-022's lexical-class condition remains unmet).

## Why This Fix

The adoption bar existed to make this call mechanical. Changing the
criteria after seeing the numbers, or shopping for a friendlier
reranker inside the same unit, would convert a measurement back into
an opinion.

## Impact

Evaluation code and docs only: the experiment module, its tests,
DECISION-023, this log. Production retrieval, artifacts, labels, and
the frozen benchmark are unchanged; the experiment's baseline arm
reproduced 20/46 · 36/46 · 0.5583 inside the same run.

## Prevention / Lesson Learned

Pre-register the adoption bar in the authorising decision, and judge
rerankers on rank-1 destruction, not just aggregate MRR: a candidate
that moves 18 of 46 cases to gain +0.007 MRR is churning, not
improving. A future rerank attempt starts from a domain-appropriate
model and its own decision.
