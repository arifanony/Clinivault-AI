# Engineering Decision: Failure-class analysis of E5 residual misses — M6 reopened for one reranking experiment

## Status

Chosen

## Date

2026-11-24

## Problem

M6 was deferred on 2026-11-10 because no failure-class breakdown of
E5's residual benchmark misses existed: nothing on record attributed
the 26 imperfect cases (of the frozen 46) to a mechanism that hybrid
retrieval, reranking, BM25, or a Top-K change would fix, as opposed to
label scope, chunking, or query phrasing. The deferral log named that
breakdown as the prerequisite evidence that would reopen M6.

That analysis now exists (Genesis task EVAL-FAILURE-CLASS-001,
`clinivault_ai.evaluation.failure_analysis`, engineering log
2026-11-24). This decision records what it found and authorises
exactly one follow-up experiment.

## What This Part of the System Does

- What goes in: the frozen 46 benchmark cases, the persisted parsed and
  E5 embedding artifacts, production `search()` — the identical
  protocol to `evaluation/benchmark.py`.
- What happens inside: for each case, the full per-document ranking is
  computed and the best-ranked expected chunk is classified HIT1
  (rank 1), RANKING (2–5), NEAR_MISS (6–20), or DEEP_MISS (>20/absent).
  Two heuristic flags are attached for human review: BOUNDARY_SUSPECT
  (an adjacent chunk carries ≥2 query content terms the expected chunk
  lacks) and LABEL_REVIEW (the case was already recorded `ambiguous`
  in `cases.py`).
- What comes out: per-case classes, ranks, and score gaps; class
  counts; the evidence base for this decision.
- Where the output goes next: this decision, the M6 experiment task it
  authorises, and the engineering log.

## Requirements

- Reproduce the frozen E5 numbers exactly before classifying anything
  (Hit@1 20/46, Hit@5 36/46, MRR 0.5583 — reproduced live 2026-11-24).
- Change no retrieval, embedding, chunking, Top-K, or label state.
- Every class assignment must be backed by a computed rank, not an
  impression.

## Options We Considered

- Option A: Cross-encoder reranking of the E5 top-20 pool down to the
  production top-5 (one variable, experiment only).
- Option B: Hybrid dense + BM25 rank fusion.
- Option C: Widen production Top-K.
- Option D: Re-chunking (overlap or section-aware boundaries).
- Option E: Do nothing further; keep M6 deferred.

## Comparison

Measured class counts on the frozen 46 (E5): HIT1 20, RANKING 16,
NEAR_MISS 6, DEEP_MISS 4.

- **RANKING is the dominant failure class.** 16 cases already retrieve
  a relevant chunk inside the top-5 but order it below other chunks,
  with cosine score gaps to rank 1 of only 0.0004–0.0194 — near-ties
  that a pairwise cross-encoder is designed to separate. Together with
  the 6 NEAR_MISS cases, **22 of the 26 imperfect cases have a relevant
  chunk inside a top-20 pool**, so a rerank pool of 20 covers them.
- **The lexical-gap hypothesis is not supported.** Only 4 cases are
  DEEP_MISS, and their expected chunks largely *lack* the query's
  content terms (paraphrase-style questions, e.g. T2D-006-second-line,
  best rank 33; T2D-008-tirzepatide-weight, best rank 31). BM25 ranks
  by those same absent terms and has no signal to exploit there. One
  of the four (T2D-001-hba1c, rank 24) is the case whose label
  provenance `cases.py` itself records as not reproducible.
  T2D-001-diagnosis (expected chunks at ranks 39/47/55) is a genuine
  semantic mismatch, not a lexical one.
- **Top-K widening** redefines the frozen Hit@5 gate and enlarges the
  M5 generation context budget; it treats the metric, not the failure.
- **Re-chunking** invalidates every committed artifact and baseline on
  the strength of a heuristic flag (BOUNDARY_SUSPECT on 8 cases) that
  is a signal for human label review, not proof of a chunking defect.
- **Doing nothing** leaves the measured dominant class unaddressed
  even though the prerequisite evidence M6 demanded now exists.

## Decision

Run exactly one M6 experiment: cross-encoder reranking of the E5
top-20 pool to top-5, as an evaluation-only comparison on the frozen
46 cases (task EVAL-RERANK-001). Adoption into production retrieval
requires its own decision and the bar in *How We Will Validate This*.
Do not run hybrid/BM25 now. Make no chunking, Top-K, or label changes.

## Why We Chose It

The measured failure mass sits in ordering, not in absence: 22 of 26
imperfect cases are reachable by reordering a top-20 pool, and the
RANKING score gaps are small enough that dense cosine has effectively
tied the candidates. Reranking is the only candidate that targets the
dominant class. It is also the cheapest to test honestly: one variable,
no artifact regeneration, fully reversible.

## Trade-offs

- A cross-encoder adds a second local model, per-query latency over
  20 pairs, and a new dependency to the retrieval path if adopted.
- The rerank experiment cannot fix the 4 DEEP_MISS cases; the ceiling
  on this experiment is Hit@1 42/46 and MRR ≈ 0.91, and a real
  cross-encoder will land below that ceiling.
- The frozen 46 is a small sample: one case is ~2.2 points of Hit@1,
  so small movements are noise. The adoption bar therefore requires a
  clear MRR gain, not a one-case shuffle.

## What We Did Not Choose

- Hybrid/BM25: no measured lexical class for it to fix (see
  Comparison). Reopen only if a post-rerank residual analysis shows
  one.
- Top-K change: redefines the gate and the M5 context budget.
- Re-chunking: disproportionate blast radius for a heuristic signal.
- Label edits: labels are frozen evidence; editing them to fit
  results would corrupt the benchmark. The 8 BOUNDARY_SUSPECT and 3
  LABEL_REVIEW flags among imperfect cases are recorded for a future
  human label review, which would be its own decision with the
  benchmark re-frozen openly, never silently.

## Assumptions

- The per-document benchmark protocol remains the project's frozen
  gate; production merged-corpus behaviour is a separate question.
- A small open cross-encoder can run locally on CPU at acceptable
  experiment cost, as the E5 screen (EVAL-HF-002) did for embeddings.
- The committed E5 artifacts remain the production baseline until an
  adoption decision replaces DECISION-017.

## How We Will Validate This

- The experiment reports Hit@1, Hit@5, and MRR on the frozen 46
  against the reproduced E5 baseline (20/46, 36/46, 0.5583), with
  per-case movement (improved / regressed / unchanged), in the style
  of the EVAL-HF-003 controlled comparison.
- Adoption bar: Hit@5 must not regress and MRR must improve by a
  margin larger than a one-case shuffle (> ~0.02). Anything less is
  recorded as a negative result and production stays on DECISION-017.
- The full unittest gate passes; the unchanged production path still
  reproduces 20/46 · 36/46 · 0.5583.

## When We Should Revisit It

- After the rerank experiment: a residual failure-class analysis of
  whatever misses remain decides whether hybrid, chunking, or label
  review is next — each still one variable, each with its own
  decision.
- If the corpus grows materially (Stage 2), re-run this analysis on
  the enlarged benchmark before assuming these class proportions hold.
