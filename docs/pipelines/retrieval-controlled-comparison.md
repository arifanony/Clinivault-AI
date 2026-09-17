# Retrieval Controlled Comparison — Baseline vs Term-Weighted vs Semantic

## Objective

Answer, with controlled evidence: does changing the retrieval
representation/scoring improve retrieval performance over the existing
deterministic hash-embedding baseline?

Three approaches compared on the EXACT same corpus, chunks, queries,
relevance labels, Top-K=5, and metric implementation:

- **A. Baseline** — existing `clinivault-baseline-hash-v1` (256-dim),
  unchanged.
- **B. Term-weighted** — evaluation-only IDF-weighted hashed bag-of-words
  (`clinivault-experiment-idf-hash-v1`).
- **C. Semantic** — evaluation-only `models/gemini-embedding-001`
  (3072-dim) via the Gemini API.

This is a measurement instrument, not a production redesign. Nothing in
this unit changed production retrieval, embeddings, Top-K, chunking, or
the frozen 21-case benchmark.

## Frozen baseline (reproduced before any comparison)

`.venv\Scripts\python -m clinivault_ai.evaluation.benchmark` reproduced
the documented benchmark exactly:

- Hit@1 **8/21**, Hit@5 **16/21**, MRR **0.5095**; per-case ranks match
  the frozen benchmark records. The baseline was frozen before any
  experimental run.

## Exact experimental methods

### B. Term-weighted (`src/clinivault_ai/evaluation/termweighted.py`)

The smallest counterfactual justified by the ranking investigation
(`d2155a4`, which observed that generic function-word mass decides the
baseline ranking):

- Tokenization IDENTICAL to baseline: lowercase, whitespace split.
- Hashing IDENTICAL: `blake2b(digest_size=8) mod 256`.
- ONLY change: per-token weight `w(t) = 1 + ln(N / df(t))`, N = corpus
  chunk count, df(t) = corpus chunks containing t (unseen → df=1).
  Ubiquitous tokens get weight ≈1; rare tokens larger. L2-normalized.
- No stopword list, no stemming, no semantic component — one variable at
  a time. Deterministic, offline, implements the existing
  EmbeddingProvider seam. Provider name
  `clinivault-experiment-idf-hash-v1`, dimension 256.

### C. Semantic (`src/clinivault_ai/evaluation/semantic.py`)

- Model: `models/gemini-embedding-001` (catalog-verified current stable
  embedding model after `text-embedding-004` retirement), 3072-dim.
- Task types: `RETRIEVAL_DOCUMENT` for chunks, `RETRIEVAL_QUERY` for
  queries (API-documented retrieval pairing).
- Batch size 32 with bounded documented retry/backoff on 429.
- Credentials read ONLY from process env / git-ignored `.env`
  (`GOOGLE_API_KEY`); never printed, logged, or persisted.
- Evaluation-only; production default provider unchanged.

## Results (21 cases, identical protocol)

| Approach | Hit@1 | Hit@5 | MRR | Hit@1 excl. T2D-010 | Hit@5 excl. | MRR excl. |
|---|---|---|---|---|---|---|
| A. Baseline | **8/21** | **16/21** | **0.5095** | 8/19 | 16/19 | 0.5632 |
| B. Term-weighted | 7/21 | 13/21 | 0.4460 | 7/19 | 13/19 | 0.4930 |
| C. Semantic | 6/21 | 17/21 | 0.4571 | 5/19 | 15/19 | 0.4263 |

**No approach beat the baseline on Hit@1 or MRR.** The semantic provider
gains Hit@5 (+1) but loses Hit@1 (−2) and MRR (−0.05); the term-weighted
counterfactual is worse on every aggregate.


## Per-case first-relevant-rank changes

(`none` = relevant evidence not in Top-5; `+` improvement, `−` regression
vs baseline.)

| Case | Base | TW | Sem | Change |
|---|---|---|---|---|
| T2D-001-diagnosis | 1 | 3 | 4 | TW− SEM− |
| T2D-001-classification | 1 | 1 | 1 | unchanged |
| T2D-001-gdm | 1 | 1 | none | SEM− |
| T2D-001-hba1c | none | none | none | unchanged |
| T2D-002-screening | 1 | 1 | 5 | SEM− |
| T2D-003-hba1c-accuracy | 1 | 1 | 3 | SEM− |
| T2D-003-quadas | 3 | 3 | none | SEM− |
| T2D-005-a1c-goal | 5 | none | 3 | TW− SEM+ |
| T2D-005-hypoglycemia | 1 | none | 1 | TW− |
| T2D-006-glp1-sglt2 | 4 | none | none | TW− SEM− |
| T2D-006-second-line | none | 2 | 4 | TW+ SEM+ |
| T2D-007-first-line | 3 | 5 | 3 | TW− |
| T2D-007-add-on | 1 | 2 | 2 | TW− SEM− |
| T2D-008-weight | 4 | none | 5 | TW− SEM− |
| T2D-008-harms | 3 | 1 | 1 | TW+ SEM+ |
| T2D-008-harms-variant | 2 | 1 | 1 | TW+ SEM+ |
| T2D-009-bp | 1 | 1 | 2 | SEM− |
| T2D-009-statins | none | none | 1 | SEM+ |
| T2D-009-statin-variant | 2 | 2 | 5 | SEM− |
| T2D-010-ckd-screening | none | none | 1 | SEM+ |
| T2D-010-kidney-protection | none | none | 2 | SEM+ |

Net: TW improves 4 cases and regresses 8; SEM improves 5 and regresses 9.


## Weak-case analysis

### T2D-006 q2 (`T2D-006-second-line`)
Relevant chunk was rank 6 (one-rank near miss). **Both counterfactuals
fix the near miss** (TW rank 2, SEM rank 4) — consistent with the
investigated mechanism: IDF weighting reduces generic-token mass that
was outranking the substantive chunk.

### T2D-009 q2 (`T2D-009-statins`)
Relevant chunks at ranks 21/42/98 — a true coverage failure of the
Top-5. **Only the semantic provider fixes it (rank 1)**; term weighting
does not (still none), because the query/document share almost no
lexical tokens — a representational gap IDF cannot bridge.

### T2D-010 (KNOWN INGESTION/PARSING CONFOUND — do not over-read)
Both T2D-010 cases improve **only under the semantic provider** (ranks 1
and 2). Per `346c86e`, T2D-010 has genuine multi-column interleaving
corruption and missing 11.4-series recommendation text, so these
improvements are **not** clean retrieval-model evidence. Excluding
T2D-010, the semantic Hit@1/MRR drop further (5/19, 0.4263) — i.e. part
of its apparent gain rests on confounded cases.

## Reproducibility

- **Baseline**: two benchmark runs byte-identical (already verified when
  frozen); reproduces documented 8/16/0.5095.
- **Term-weighted**: run twice; result JSONs byte-identical
  (`_twA.json` == `_twB.json`). Fully deterministic, offline.
- **Semantic**: depends on an external network service. The recorded run
  (hit1=6, hit5=17, mrr=0.4571) is arithmetically consistent with its
  per-case ranks (sum of 1/rank over hits = 0.4571). A full second pass
  was attempted but was repeatedly rate-limited (HTTP 429, free-tier
  per-minute limits) even with documented backoff; a lightweight
  query-level determinism check was used instead of a full second pass.
  **Limitation recorded, not hidden**: semantic results are
  single-pass evidence subject to API availability/quota.

## Interpretation

1. **The baseline hash embedding is not trivially replaceable.** The
   IDF counterfactual — the direct fix for the observed generic-token
   mechanism — is net-negative: it fixes the T2D-006 near miss and the
   harms cases but regresses 8 otherwise-good cases (weighting shifts
   mass toward rare tokens that are not always the clinically decisive
   ones, e.g. document-specific vocabulary).
2. **The semantic provider addresses the two hardest lexical-gap cases
   (T2D-009-statins, and the confounded T2D-010 cases) but loses
   Hit@1/MRR overall** and regresses 9 cases, including cases the
   baseline ranks at 1. Its Hit@5 gain (+1) is the only aggregate
   improvement, and part of it rests on the T2D-010 confound.
3. **Evidence-based conclusion**: the frozen benchmark does NOT justify
   changing the production retrieval representation. The observed
   weaknesses are real but narrow (a 1-rank near miss and one lexical
   coverage gap out of 21), and both counterfactuals trade those
   fixes for broader regressions.

## Limitations

- 21 cases, hand-labeled from prior validation records; small sample.
- Semantic arm is single-pass, network/quota dependent, and external.
- T2D-010 cases carry the documented ingestion confound (reported both
  ways in the aggregate table).
- Term-weighted method is ONE parameterization (1+ln IDF); the experiment
  does not claim all term-weighting schemes behave identically.
- Experiment modules are evaluation-only and are NOT wired into any
  pipeline stage; production default provider is unchanged.

## Experiment artifacts

Result JSONs (`_baseA.json`, `_twA.json`, `_twB.json`, `_semA.json`) and
probe scripts were temporary experiment artifacts and were deleted after
the evidence was transcribed into this document. No semantic embedding
artifact was persisted; per the artifact-storage contract, no experiment
artifact was written under `data/`.

## Recommendation for the NEXT bounded unit

Do NOT change production retrieval based on this evidence. Recommended
next unit: **resolve the T2D-010 ingestion confound** (parser-level
column handling for that document class), because (a) it is the only
failure class that is not purely a ranking matter, and (b) any future
retrieval comparison would otherwise remain polluted by it. A semantic
re-ranking/representation decision should only be revisited after the
corpus extraction is trustworthy and with a larger labeled case set.
