# E5 failure-class analysis — M6's missing prerequisite, measured

## Date

2026-11-24

## Where It Happened

Retrieval evaluation (`src/clinivault_ai/evaluation/`), frozen 46-case
benchmark, production E5 provider. New read-only analysis module
`failure_analysis.py` (task EVAL-FAILURE-CLASS-001); no retrieval,
embedding, chunking, Top-K, or label state was changed.

## What We Expected

Per the 2026-11-10 M6 deferral log, the residual E5 misses (10/46
outside Hit@5, 26/46 outside Hit@1) had never been attributed to a
mechanism. The expectation was that classifying them would show which
single M6 experiment, if any, the evidence supports.

## What Actually Happened

**OBSERVED:** The frozen E5 benchmark was first reproduced live on
this machine (2026-11-24 end-to-end validation): Hit@1 20/46, Hit@5
36/46, MRR 0.5583 — exact. The analysis then computed the full
per-document ranking for every case under the identical protocol.

**OBSERVED:** Class counts — HIT1 20, RANKING 16, NEAR_MISS 6,
DEEP_MISS 4. The dominant failure is ordering: 16 cases hold a
relevant chunk at ranks 2–5 with cosine gaps to rank 1 of
0.0004–0.0194, and 22 of the 26 imperfect cases have a relevant chunk
inside the top 20.

**OBSERVED:** Only 4 cases are deep misses, and they are not lexical
gaps: their expected chunks largely lack the query's content terms
(paraphrase-style questions), so a term-based method has no signal
there either. One of the four is the label `cases.py` already records
as having non-reproducible provenance.

## Evidence

Class counts: `DEEP_MISS=4  HIT1=20  NEAR_MISS=6  RANKING=16`
(module run, provider e5, 2026-11-24).

RANKING (16) — case: best rank, score gap to rank 1:

| Case | Rank | Gap | Flags |
|---|---|---|---|
| T2D-007-add-on | 2 | 0.0004 | |
| T2D-010-kidney-protection | 2 | 0.0015 | |
| T2D-009-sglt2-heart-failure | 2 | 0.0032 | |
| T2D-002-lifestyle-outcomes | 2 | 0.0047 | BOUNDARY_SUSPECT |
| T2D-001-gdm | 2 | 0.0059 | |
| T2D-001-type1-autoantibody | 2 | 0.0074 | |
| T2D-006-initial-combination | 3 | 0.0080 | BOUNDARY_SUSPECT |
| T2D-010-ckd-screening | 3 | 0.0043 | |
| T2D-008-harms | 3 | 0.0194 | |
| T2D-009-statin-variant | 3 | 0.0167 | |
| T2D-002-screening | 4 | 0.0100 | |
| T2D-003-hba1c-optimal-threshold | 4 | 0.0067 | BOUNDARY_SUSPECT |
| T2D-007-first-line | 4 | 0.0136 | |
| T2D-003-fpg-optimal-cutoff | 5 | 0.0096 | |
| T2D-008-sglt2-kidney-nma | 5 | 0.0045 | |
| T2D-008-weight | 5 | 0.0126 | LABEL_REVIEW |

NEAR_MISS (6):

| Case | Rank | Gap | Flags |
|---|---|---|---|
| T2D-005-dka-prevention | 6 | 0.0109 | BOUNDARY_SUSPECT |
| T2D-006-glp1-sglt2 | 9 | 0.0153 | |
| T2D-006-insulin-initiation | 9 | 0.0122 | BOUNDARY_SUSPECT |
| T2D-009-icosapent-ethyl | 12 | 0.0145 | BOUNDARY_SUSPECT |
| T2D-003-hba1c-accuracy | 13 | 0.0186 | BOUNDARY_SUSPECT |
| T2D-003-quadas | 17 | 0.0324 | LABEL_REVIEW |

DEEP_MISS (4):

| Case | Rank | Gap | Flags | Note |
|---|---|---|---|---|
| T2D-001-hba1c | 24 | 0.0171 | LABEL_REVIEW | Label provenance recorded non-reproducible in `cases.py` |
| T2D-008-tirzepatide-weight | 31 | 0.0386 | BOUNDARY_SUSPECT | Expected ranks 38/31 |
| T2D-006-second-line | 33 | 0.0304 | | Query terms largely absent from expected chunk |
| T2D-001-diagnosis | 39 | 0.0365 | | Expected ranks 47/39/55 — semantic mismatch |

Strongest boundary signal: T2D-009-icosapent-ethyl — every query
content term missing from the expected chunk (`added, adults,
diabetes, icosapent, therapy, when`) is present in its neighbouring
chunk. Recorded for human label review; no label was changed.

## What We Investigated

- Full rankings and per-chunk cosine scores for all 46 cases.
- Query content terms present/absent in each best expected chunk, and
  in its immediate neighbours (the BOUNDARY_SUSPECT heuristic).
- The pre-existing `ambiguous` flags and label provenance notes in
  `cases.py`.

## What We Tried

The classification itself is the work product: a reusable module
(`evaluation/failure_analysis.py`, runnable like the benchmark) plus
unit tests for the class boundaries (`tests/test_failure_analysis.py`).

## What Failed

Nothing in the run. The earlier hypothesis that a lexical (BM25)
method would address the deep misses did not survive the evidence:
the deep-miss chunks do not contain the query terms a lexical ranker
would need.

## The Fix

No production fix in this unit — by design. The output is a decision:
DECISION-022 authorises exactly one experiment (cross-encoder
reranking of the top-20 pool) and records why hybrid, Top-K, and
re-chunking are not run.

## Why This Fix

M6's rule is one variable against measured weakness. The measured
weakness is ordering inside the top 20 (22/26 cases), so reranking is
the experiment the evidence names; everything else would be guessing
with a larger blast radius.

## Impact

Docs and evaluation code only: DECISION-022, this log, the analysis
module and its tests. Production retrieval is unchanged and still
reproduces 20/46 · 36/46 · 0.5583. Genesis task EVAL-FAILURE-CLASS-001
carries the state; EVAL-RERANK-001 is the authorised next step;
EVAL-HYBRID-001 stays parked unless a later residual analysis shows a
lexical class.

## Prevention / Lesson Learned

A benchmark total (MRR 0.5583) hides the mechanism; the class
breakdown is what turns "retrieval could be better" into a named,
testable experiment. Run the classification before debating remedies —
and re-run it after each adopted change, because the class proportions
are the real progress measure.
