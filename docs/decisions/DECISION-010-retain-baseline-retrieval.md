# Engineering Decision: Retain the Baseline Retrieval Representation (Controlled Comparison Outcome)

## Status

Replaced by [DECISION-016](./DECISION-016-retrieval-representation.md) on
2026-09-23 after the frozen benchmark expanded to 46 cases and the local
semantic-model evaluation completed. This record remains the historical
decision for the earlier 21-case comparison.

## Date

2026-09-18 (evidence committed in `d0dc40c`; measured results recorded in
`b705d60` on 2026-09-19)

## Problem

The ranking investigation (`d2155a4`) showed that for 4 of 13 validation queries
the relevant evidence sat outside Top-5, and identified a plausible mechanism
(function-word mass plus hash collisions in the lexical baseline). It
recommended, explicitly, a controlled benchmark **before** any architecture
change. The question this decision answers: does the measured evidence justify
replacing the production retrieval representation?

## What Was Measured

Three approaches, identical corpus, chunks, queries, relevance labels, Top-K=5,
and metric implementation (`d0dc40c`; `retrieval-controlled-comparison.md`):

| Arm | Representation | Hit@1 | Hit@5 | MRR | excl. T2D-010 (Hit@1/Hit@5/MRR) |
|---|---|---|---|---|---|
| A (baseline) | `clinivault-baseline-hash-v1`, 256-dim | **8/21** | **16/21** | **0.5095** | 8/19 / 16/19 / 0.5632 |
| B | IDF-weighted hash (`clinivault-experiment-idf-hash-v1`) | 7/21 | 13/21 | 0.4460 | 7/19 / 13/19 / 0.4930 |
| C | `models/gemini-embedding-001`, 3072-dim (retrieval task types) | 6/21 | 17/21 | 0.4571 | 5/19 / 15/19 / 0.4263 |

**No arm beat the baseline on Hit@1 or MRR.** Arm C gained Hit@5 (+1) while
losing Hit@1 (−2) and MRR (−0.05), and part of that gain rests on the
T2D-010 ingestion confound. Arm B — the direct fix for the observed mechanism —
was worse on every aggregate and regressed 8 otherwise-good cases.

## Options We Considered

1. **Replace production retrieval with the semantic provider (arm C)** — rejected:
   not supported by Hit@1/MRR, adds a network/credential quota dependency, and
   its only aggregate gain is confounded.
2. **Replace with IDF term weighting (arm B)** — rejected: net-negative on every
   aggregate.
3. **Adopt a hybrid/reranked design** — rejected as premature: the controlled
   evidence does not identify a mechanism that reranking would fix.
4. **Keep the baseline unchanged, do not measure anything** — rejected: the
   repository's baseline-first rule requires measurement before and after.
5. **Keep the baseline unchanged *and* fix the one non-ranking failure class
   first (chosen).**

## Decision

The production retrieval representation stays exactly as it is — baseline hash
embeddings, cosine similarity, in-memory index, Top-K=5
(see [DECISION-009](./DECISION-009-retrieval-baseline-representation.md)). The
term-weighted and semantic implementations remain **evaluation-only** modules; they
are not wired into any pipeline stage and are not a production default.

Before any future representation decision: the T2D-010 ingestion confound must be
resolved (parser-level multi-column handling for that document class), and any
comparison must either exclude ingestion-defective cases or report them
separately, with a larger labeled case set.

## Why We Chose It

- The measured weaknesses are real but **narrow**: one 1-rank near miss
  (T2D-006) and one lexical coverage gap; both counterfactuals trade those fixes
  for broader regressions (8 and 9 cases respectively).
- The baseline is deterministic, offline, cost-free, and bit-reproducible; the
  alternatives are not (arm C was rate-limited and therefore single-pass).
- Part of arm C's apparent improvement is explained by ingestion damage in
  T2D-010, not by better retrieval, so the evidence is weaker than the raw
  aggregate suggests.
- The repository's rule is to change architecture only when measured evidence
  justifies it — here the evidence points the other way.

## Trade-offs Accepted

- The documented ranking weaknesses remain in the product; they manifest as
  **coverage loss (no answer)** rather than wrong answers, because the generation
  layer refuses when evidence is missing — the safe direction for a clinical tool,
  but a real usability cap on reference-heavy guideline chapters.
- A demonstrably working semantic provider is left unused in production.
- The alternative paths stay in the repository as evaluation code that must be
  maintained or explicitly archived later.

## Limitations of the Evidence

- 21 hand-labeled cases; a small sample. Not a statistical evaluation.
- Arm C is single-pass (Gemini free-tier 429 limits) — network/quota dependent,
  not fully reproducible.
- Arm B is **one** parameterization (`1 + ln IDF`); the comparison does not claim
  all term-weighting schemes behave identically.
- T2D-010 cases carry the documented ingestion confound and are reported both
  ways.

## Consequences

- Production retrieval, embeddings, Top-K, chunking, and the frozen benchmark are
  unchanged by this unit.
- The T2D-010 ingestion confound becomes the gating item for any future retrieval
  comparison (`t2d-010-ingestion-quality-investigation.md`); the parser
  remediation for that document class is a **separate** unit.
- Any future "we improved retrieval" claim must reproduce the baseline first and
  change one variable at a time.

## Evidence

- `docs/pipelines/retrieval-controlled-comparison.md` — objective, exact methods,
  results, per-case rank changes, reproducibility notes, interpretation.
- `docs/pipelines/retrieval-baseline-benchmark.md` +
  `retrieval-baseline-benchmark-results.md` — the frozen baseline protocol and
  measured baseline reproduced before any comparison.
- `docs/pipelines/retrieval-ranking-investigation.md` — the mechanism analysis
  that justified the benchmark.
- `docs/pipelines/t2d-010-ingestion-quality-investigation.md` (`346c86e`) — the
  confound.
- Temporary experiment artifacts (result JSONs, probe scripts) were deleted after
  the evidence was transcribed; no experiment artifact was persisted under
  `data/` (per the storage contract).

## How We Will Validate This

- Re-run `python -m clinivault_ai.evaluation.benchmark` and confirm 8/21, 16/21,
  0.5095 from the canonical committed artifacts.
- Re-measure after the ingestion remediation lands, on a corpus whose extraction
  is trustworthy.

## When We Should Revisit It

- After T2D-010-class ingestion defects are fixed and the benchmark re-measured.
- If a larger labeled case set shows the semantic arm winning on Hit@1/MRR.
- If latency/cost evidence makes a semantic provider attractive for other
  reasons.
- If a measured K-sweep or chunking change alters the retrieval picture.

## Related Documents

- [DECISION-009: baseline retrieval representation](./DECISION-009-retrieval-baseline-representation.md) — what was retained and why.
- [DECISION-007: generation provider](./DECISION-007-generation-provider.md) — the provider whose quota limited the semantic arm's reproducibility.
- [Engineering log: T2D-010 multi-column interleaving](../engineering-log/2026-09-16-t2d-010-column-interleaving.md).
- [Engineering log: stale T2D-010 embedding artifact](../engineering-log/2026-09-19-stale-t2d-010-embedding-artifact.md) — an artifact-consistency issue in the same document's artifact chain, unrelated to representation choice.

## Related Commits

`d2155a4` (ranking investigation), `1984724` (benchmark), `6307999` (record
corrections), `346c86e` (ingestion-quality isolation), `d0dc40c` (comparison),
`b705d60` (recorded results).