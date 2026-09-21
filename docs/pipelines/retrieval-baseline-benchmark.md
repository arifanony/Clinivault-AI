# Controlled Baseline Retrieval Benchmark

Status: baseline measurement complete. No retrieval implementation change was
made in this unit.

Related documents:

- `docs/pipelines/retrieval-ranking-investigation.md` (forensic diagnosis of
  the known weak cases)
- `docs/pipelines/corpus-generalization-validation.md` (per-document
  validation that supplied the queries)
- `docs/pipelines/representative-evaluation.md` (five original evaluation
  cases; see the EVAL-5 reconciliation note)
- `docs/architecture/artifact-storage.md` (canonical artifact paths)
- `docs/engineering-log/2026-09-16-eval5-retrieval-record-not-reproducible.md`

## A. Objective

Quantify the behaviour of the CURRENT baseline retrieval system on a small,
explicitly labeled, reproducible set of real clinical queries:

> How often does the baseline retrieve known relevant evidence within Top-K,
> and how highly does it rank that evidence?

This is a **controlled baseline retrieval benchmark** — a measurement
instrument for an evidence-based decision about whether a retrieval
architecture change is justified. It is **not** proof of retrieval quality,
and it is not a production evaluation framework.

Explicitly out of scope for this unit: reranking, hybrid retrieval, BM25,
IDF, stopword removal, semantic embeddings, Top-K changes, chunking/parsing
changes, query rewriting, generation, UI.

## B. Dataset / cases

46 cases across 9 documents (T2D-004 excluded — blocked). Expanded under TASK EVAL-EXPAND-001 (DECISION-014).

| Document | Baseline 21-Case Count | Expanded 46-Case Count | Cases |
|---|---|---|---|
| T2D-001 | 4 | 7 | `diagnosis`, `classification`, `gdm`, `hba1c`, `type1-autoantibody`, `diagnosis-criteria-table`, `prediabetes-screening` |
| T2D-002 | 1 | 3 | `screening`, `lifestyle-outcomes`, `metformin-prediabetes` |
| T2D-003 | 2 | 4 | `hba1c-accuracy`, `quadas`, `fpg-optimal-cutoff`, `hba1c-optimal-threshold` |
| T2D-005 | 2 | 5 | `a1c-goal`, `hypoglycemia`, `cgm-targets`, `glycemic-deintensification`, `dka-prevention` |
| T2D-006 | 2 | 5 | `glp1-sglt2`, `second-line`, `insulin-initiation`, `metformin-first-line`, `initial-combination` |
| T2D-007 | 2 | 5 | `first-line`, `add-on`, `dpp4-against`, `sglt2-cv-ckd-outcomes`, `hypoglycemia-risk` |
| T2D-008 | 3 | 6 | `weight`, `harms`, `harms-variant`, `tirzepatide-weight`, `finerenone-mortality`, `sglt2-kidney-nma` |
| T2D-009 | 3 | 6 | `bp`, `statins`, `statin-variant`, `aspirin-primary`, `sglt2-heart-failure`, `icosapent-ethyl` |
| T2D-010 | 2 | 5 | `ckd-screening`, `kidney-protection`, `albuminuria-classification`, `finerenone-ckd`, `protein-restriction` |
| **TOTAL** | **21** | **46** | **21 original + 25 expanded cases** |

Queries are taken from prior validated runs; none were invented for this
benchmark. Provenance was checked programmatically: **20 of 21 queries appear
verbatim** in one of the three source documents (T2D-001/002 in
`representative-evaluation.md`; T2D-003/005/006/007/008/009/010 in
`corpus-generalization-validation.md`; the four weakness queries also appear in
`retrieval-ranking-investigation.md`). The single exception is
`T2D-003-quadas`, which is a composed query covering the two aspects
documented for that document (optimal-FPG cut-off and quality-assessment tool);
it is one of the ambiguous cases. The four known weakness cases are
deliberately included (`T2D-006-second-line`, `T2D-009-statins`,
`T2D-010-ckd-screening`, `T2D-010-kidney-protection`), together with previously
successful cases so the set is not biased toward failures. Documents with only
one defensible labeled query contribute one case (T2D-002); T2D-001 contributes
four (all of the representative evaluation's cases) and T2D-008/T2D-009
contribute three each, because their documented evidence supports an additional
reformulated query.

Benchmark definition (static, code-level):
`src/clinivault_ai/evaluation/cases.py` — each case records `case_id`,
`document_id`, `query`, `expected_chunk_ids`, `label_source` (the exact
document the label came from), an `ambiguous` flag and a `note`.

## C. Labeling method

Labels are expected-relevant **chunk IDs** derived only from existing
documented evidence:

1. `docs/pipelines/corpus-generalization-validation.md` — per-document
   queries and the chunk IDs that carried the supported claims.
2. `docs/pipelines/retrieval-ranking-investigation.md` — the exact expected
   chunks for the four known weakness cases (including the full-ranking
   positions recorded there).
3. `docs/pipelines/representative-evaluation.md` — the original five cases.

Rules applied:

- No label was derived from a generated answer.
- No label was assigned for semantic similarity alone.
- Chunk-text presence was **verified programmatically** for CV-flagged
  evidence before use (e.g. `0.654`/`0.945` in T2D-003, `OR 3.29` in
  T2D-008, recommendations `9.21`/`9.22` in T2D-006).
- Where prior evidence was not strong enough, the case is marked
  `ambiguous=True` rather than given an invented ground truth.

Labels are **not** exhaustive: a passage can span multiple chunks, and a
document may contain several genuinely relevant chunks that are not labeled.
See section L.

Three cases are ambiguous:

| Case | Why ambiguous |
|---|---|
| `T2D-001-hba1c` | EVAL-5's recorded Top-5 does not reproduce against the persisted baseline (actual full ranks 48 and 32) and its quoted evidence phrase `"either A1C or glucose criteria"` is absent from the corpus-wide chunk text. Label provenance only partially verified. |
| `T2D-003-quadas` | Label covers the quality-assessment half of the query only; the optimal-FPG cut-off half was documented as not answered from the supplied Top-5. |
| `T2D-008-weight` | Label covers the body-weight half only; no documented relevant chunk exists for the A1C-comparative half (the model refused it). |

## D. Baseline configuration

Unchanged from the production baseline. Nothing was tuned for this benchmark.

| Component | Value |
|---|---|
| Embedding provider | `clinivault-baseline-hash-v1` |
| Embedding method | `hashed-bag-of-words` (blake2b hash, whitespace-lowercase tokenizer, L2 norm) |
| Dimension | 256 |
| Similarity | cosine |
| Retriever | `clinivault_ai.retrieval.search` over `VectorStore` |
| Top-K | 5 (production value, unchanged) |
| Ordering | deterministic |
| Generation | not used |
| Network | not used |

Exact artifacts consumed (canonical storage rule,
`docs/architecture/artifact-storage.md`):

- `data/parsed/stage-1-clean-baseline-corpus/T2D-001/T2D-001.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-002/T2D-002.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-003/T2D-003.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-005/T2D-005.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-006/T2D-006.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-007/T2D-007.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-008/T2D-008.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-009/T2D-009.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-010/T2D-010.parsed.json`
- `data/embedded/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json`
  for the same nine documents (e.g.
  `data/embedded/stage-1-clean-baseline-corpus/T2D-006/T2D-006.embeddings.json`).

Run:

```
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark
```

The runner also accepts an explicit `cases` tuple and `top_k` argument for
offline tests; the default call is the measured baseline.

## E. Metrics definitions

Computed by `src/clinivault_ai/evaluation/metrics.py` (pure functions over
ranked chunk-ID lists; deterministic; validates non-empty duplicate-free
inputs).

| Metric | Definition |
|---|---|
| Hit@1 | 1 if at least one expected relevant chunk is ranked 1, else 0 |
| Hit@5 | 1 if at least one expected relevant chunk appears in Top-5, else 0 |
| Reciprocal rank | `1 / rank` of the highest-ranked expected relevant chunk; 0 if none is ranked |
| MRR | mean of reciprocal ranks across cases |
| First relevant rank | rank of the highest-ranked expected relevant chunk (None if absent) |

Multiple relevant chunks per query: Hit@5 is 1 if ANY expected chunk is in
Top-5; reciprocal rank uses the HIGHEST-ranked relevant chunk; all relevant
ranks within Top-5 are recorded separately. No relevance weights are used.

Full-rank inspection: for cases where the first relevant rank is None, the
runner performs a diagnostic call with `top_k = index size` to establish
where the expected evidence actually sits. This is measurement only — the
production Top-K stays 5, and the same `search()` function is used.
## F. Aggregate results (exact measured values)

```
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark
cases=21 docs=9
Hit@1=8/21  Hit@5=16/21  MRR=0.5095
```

| Metric | All cases (n=21) | Excluding ambiguous (n=18) |
|---|---|---|
| Hit@1 | 8/21 = 0.3810 | 8/18 = 0.4444 |
| Hit@5 | 16/21 = 0.7619 | 14/18 = 0.7778 |
| MRR | 0.5095 | 0.5620 |

First-relevant-rank distribution (all 21 cases):

| First relevant rank | Cases |
|---|---|
| 1 | 8 |
| 2 | 2 |
| 3 | 3 |
| 4 | 2 |
| 5 | 1 |
| not in Top-5 | 5 |

## G. Per-query results

Top-5 scores are cosine similarities from the shared hash embedding space and
are context-dependent (document-mean similarity differs per document), so they
are only comparable within a document.

### T2D-001 (107 candidates)

All 107 candidates were searched. `diagnosis`, `classification` and `gdm`
reproduce their documented Top-5 exactly (representative evaluation
EVAL-1/EVAL-2/EVAL-3, identical chunk IDs, order and scores); `hba1c` does not —
see section H and the engineering-log entry.

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `diagnosis` | criteria for the diagnosis of diabetes | p014-c003, p002-c002, p002-c003 | 1:p014-c003:0.6018, 2:p002-c002:0.5851, 3:p023-c006:0.5814, 4:p002-c003:0.5680, 5:p017-c003:0.5641 | 1 | 1 | 1.0000 | 1 |
| `classification` | classification of diabetes types | p015-c002, p004-c003, p013-c003 | 1:p015-c002:0.5027, 2:p004-c003:0.4919, 3:p001-c001:0.4768, 4:p013-c003:0.4470, 5:p020-c003:0.4406 | 1 | 1 | 1.0000 | 1 |
| `gdm` | gestational diabetes screening in pregnancy | p023-c001, p023-c004 | 1:p023-c001:0.5940, 2:p023-c004:0.5609, 3:p022-c005:0.5377, 4:p021-c001:0.5259, 5:p021-c003:0.5207 | 1 | 1 | 1.0000 | 1 |
| `hba1c` (AMBIGUOUS) | HbA1c test to diagnose diabetes | p002-c002, p002-c003 | 1:p012-c002:0.3959, 2:p009-c004:0.3651, 3:p012-c001:0.3361, 4:p004-c003:0.3333, 5:p023-c004:0.3272 | 0 | 0 | 0.0000 | none — full rank p002-c003=32, p002-c002=48 |

### T2D-002 (34 candidates)

Reproduces the documented representative-evaluation EVAL-4 Top-5 exactly; all
three labeled chunks are inside Top-5 (ranks 1–3).

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `screening` | screening recommendations for prediabetes and type 2 diabetes | p007-c003, p002-c001, p004-c002 | 1:p007-c003:0.6092, 2:p002-c001:0.5493, 3:p004-c002:0.4790, 4:p001-c001:0.4657, 5:p008-c001:0.4603 | 1 | 1 | 1.0000 | 1 |

### T2D-003 (44 candidates)

Scores are low overall because both queries are long and number-dense, yet the
labeled chunks are still retrieved: ranks 1 and 4 (`hba1c-accuracy`), ranks 3
and 4 (`quadas`).

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `hba1c-accuracy` | What were the pooled sensitivity and specificity of HbA1c at 6.5% for diagnosing diabetes? | p008-c002, p008-c001 | 1:p008-c002:0.2942, 2:p007-c002:0.2513, 3:p017-c002:0.2004, 4:p008-c001:0.1759, 5:p003-c002:0.1637 | 1 | 1 | 1.0000 | 1 |
| `quadas` (AMBIGUOUS) | What was the optimal cut-off for fasting plasma glucose and what quality assessment tool was used? | p001-c002, p004-c003 | 1:p018-c002:0.2223, 2:p019-c001:0.2132, 3:p001-c002:0.1412, 4:p004-c003:0.1348, 5:p005-c002:0.1279 | 0 | 1 | 0.3333 | 3 |

### T2D-005 (84 candidates)

`a1c-goal` is a boundary retrieval: the single labeled chunk arrives in the last
Top-K slot (rank 5).

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `a1c-goal` | What is the recommended A1C goal for most adults with diabetes? | p005-c001 | 1:p002-c001:0.4293, 2:p004-c002:0.3886, 3:p002-c004:0.3685, 4:p002-c002:0.3586, 5:p005-c001:0.3481 | 0 | 1 | 0.2000 | 5 |
| `hypoglycemia` | How should hypoglycemia be treated and what glucose threshold defines clinically significant hypoglycemia? | p010-c002, p008-c001, p010-c004 | 1:p010-c002:0.3705, 2:p010-c004:0.3406, 3:p005-c002:0.3394, 4:p009-c004:0.3228, 5:p008-c001:0.3213 | 1 | 1 | 1.0000 | 1 |

### T2D-006 (142 candidates)

`second-line` is the documented near miss: the labeled chunk sits one rank
beyond the cutoff (rank 6; rank-5 score 0.3860). `glp1-sglt2` retrieves both of
its labeled chunks but at ranks 4 and 5.

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `glp1-sglt2` | When should GLP-1 receptor agonists or SGLT2 inhibitors be used in type 2 diabetes treatment? | p010-c002, p008-c003 | 1:p029-c001:0.4310, 2:p029-c002:0.4303, 3:p030-c002:0.4288, 4:p010-c002:0.4283, 5:p008-c003:0.4233 | 0 | 1 | 0.2500 | 4 |
| `second-line` | What factors guide the choice of second-line medication after metformin? | p015-c004 | 1:p024-c005:0.4438, 2:p023-c003:0.4017, 3:p025-c005:0.3978, 4:p023-c004:0.3938, 5:p024-c004:0.3860 | 0 | 0 | 0.0000 | none — full rank p015-c004=6 |

### T2D-007 (38 candidates)

Both cases retrieve a labeled chunk; `first-line` places its single labeled
chunk at rank 3.

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `first-line` | What does the ACP guideline recommend for first-line treatment of type 2 diabetes? | p003-c002 | 1:p012-c001:0.4001, 2:p004-c001:0.3945, 3:p003-c002:0.3801, 4:p005-c002:0.3682, 5:p010-c001:0.3668 | 0 | 1 | 0.3333 | 3 |
| `add-on` | When should an SGLT2 inhibitor or GLP-1 receptor agonist be added to metformin? | p009-c001, p008-c002, p002-c002 | 1:p009-c001:0.4384, 2:p009-c002:0.4095, 3:p008-c002:0.3474, 4:p002-c002:0.3380, 5:p003-c002:0.3126 | 1 | 1 | 1.0000 | 1 |

### T2D-008 (66 candidates)

`weight` and `harms` target the same comparative-effectiveness material yet
produce different Top-5 lists. In the `harms` run `p013-c004` is retrieved at
rank 3 while `p001-c004` sits at full rank 39; the reworded `harms-variant`
(naming the specific harm) retrieves `p001-c004` at rank 2. `weight`'s labeled
chunk `p001-c002` sits at rank 4.

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `weight` (AMBIGUOUS) | Which medication classes most effectively reduce A1C and body weight in adults with type 2 diabetes? | p001-c002 | 1:p002-c003:0.3622, 2:p015-c005:0.3518, 3:p005-c002:0.3517, 4:p001-c002:0.3513, 5:p015-c006:0.3396 | 0 | 1 | 0.2500 | 4 |
| `harms` | What are the main harms of SGLT2 inhibitors and GLP-1 receptor agonists reported in the review? | p013-c004, p001-c004 | 1:p004-c002:0.5528, 2:p015-c001:0.5011, 3:p013-c004:0.4859, 4:p015-c004:0.4785, 5:p005-c001:0.4694 | 0 | 1 | 0.3333 | 3 |
| `harms-variant` | SGLT2 inhibitors increase genital infections odds ratio medication-specific harms | p001-c004 | 1:p002-c004:0.2449, 2:p001-c004:0.2399, 3:p012-c004:0.1949, 4:p005-c002:0.1705, 5:p015-c006:0.1647 | 0 | 1 | 0.5000 | 2 |

### T2D-009 (142 candidates)

`statins` is the worst case: labeled evidence sits at full ranks 21/42/98 while
the Top-5 is filled with front-matter and citation-heavy chunks. The reworded
`statin-variant` retrieves the same evidence at ranks 2 and 5.

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `bp` | What blood pressure goal is recommended for adults with diabetes and how should hypertension be treated? | p003-c002, p006-c001, p006-c003 | 1:p003-c002:0.4829, 2:p006-c001:0.4707, 3:p002-c003:0.4698, 4:p006-c003:0.4550, 5:p002-c004:0.4509 | 1 | 1 | 1.0000 | 1 |
| `statins` | When are statins recommended for cardiovascular risk reduction in type 2 diabetes? | p008-c003, p008-c004, p009-c001 | 1:p001-c002:0.5343, 2:p016-c001:0.4311, 3:p029-c004:0.4214, 4:p030-c005:0.4206, 5:p018-c003:0.4096 | 0 | 0 | 0.0000 | none — full rank p009-c001=21, p008-c003=42, p008-c004=98 |
| `statin-variant` | For which patients is high-intensity statin therapy recommended, including age and primary versus secondary prevention? | p008-c003, p009-c002 | 1:p002-c003:0.3563, 2:p009-c002:0.3491, 3:p008-c002:0.3350, 4:p013-c003:0.3280, 5:p008-c003:0.3265 | 0 | 1 | 0.5000 | 2 |

### T2D-010 (71 candidates)

`kidney-protection` is an index-level near miss (full ranks 12/13 of 71);
`ckd-screening` is genuinely distant (rank 28), consistent with the documented
T2D-010 parsing-quality issue
(`docs/engineering-log/2026-09-16-t2d-010-column-interleaving.md`).

| Case | Query | Expected | Top-5 (rank:chunk:score) | Hit@1 | Hit@5 | RR | First rank |
|---|---|---|---|---|---|---|---|
| `ckd-screening` | How should chronic kidney disease be screened and monitored in adults with diabetes? | p001-c002 | 1:p012-c003:0.4905, 2:p015-c004:0.4826, 3:p015-c003:0.4561, 4:p008-c001:0.4521, 5:p010-c001:0.4358 | 0 | 0 | 0.0000 | none — full rank p001-c002=28 |
| `kidney-protection` | When are ACE inhibitors, ARBs, SGLT2 inhibitors, or finerenone recommended for kidney protection in diabetes? | p006-c004, p006-c003 | 1:p011-c003:0.3447, 2:p004-c003:0.3385, 3:p014-c006:0.3298, 4:p015-c006:0.3293, 5:p012-c005:0.3207 | 0 | 0 | 0.0000 | none — full rank p006-c004=12, p006-c003=13 |

## H. Cases where expected evidence was outside Top-5

| Case | Expected chunk | Full rank | Distance from Top-5 |
|---|---|---|---|
| `T2D-006-second-line` | T2D-006-p015-c004 | 6 | 1 (near miss) |
| `T2D-010-kidney-protection` | T2D-010-p006-c004 | 12 | 7 |
| `T2D-010-kidney-protection` | T2D-010-p006-c003 | 13 | 8 |
| `T2D-009-statins` | T2D-009-p009-c001 | 21 | 16 |
| `T2D-010-ckd-screening` | T2D-010-p001-c002 | 28 | 23 |
| `T2D-001-hba1c` (AMBIGUOUS) | T2D-001-p002-c003 | 32 | 27 |
| `T2D-009-statins` | T2D-009-p008-c003 | 42 | 37 |
| `T2D-001-hba1c` (AMBIGUOUS) | T2D-001-p002-c002 | 48 | 43 |
| `T2D-009-statins` | T2D-009-p008-c004 | 98 | 93 |

Severity is not uniform: one case is a 1-rank miss, three are shallow
(single-digit/low-twenty-ish), and the T2D-009 `statins` pair is deep (42/98).

## I. OBSERVED findings

1. **Baseline retrieval retrieves labeled evidence for 16/21 cases (Hit@5 =
   0.7619) and ranks it first for 8/21 (Hit@1 = 0.3810); MRR = 0.5095.**
   Excluding the three ambiguous cases: Hit@1 8/18, Hit@5 14/18, MRR 0.5620.
2. **The failures are not one document.** The five Top-5 misses span four
   documents (T2D-001, T2D-006, T2D-009, T2D-010) and three different
   mechanisms (deep ranking loss, near miss, boilerplate domination).
3. **One failure is a single-rank miss.** `T2D-006-second-line` needs the
   labeled chunk at rank 6, one slot beyond the production cutoff (rank-5 score
   0.3860; the labeled chunk scores 0.3842 per
   `retrieval-ranking-investigation.md`).
4. **Two failures are index-level near misses.** `T2D-010-kidney-protection`
   labels sit at full ranks 12/13 of 71.
5. **Two failures are genuine coverage failures at depth.**
   `T2D-009-statins` (ranks 42/98/21) and `T2D-010-ckd-screening` (rank 28)
   place evidence far outside Top-5 while generic/citation chunks are returned.
6. **Terminology variation changes outcomes measurably.** For the T2D-009
   statin topic, the reworded query moved `p008-c003` from full rank 42 to
   rank 5 and `p009-c002` to rank 2. For T2D-008, naming the specific harm
   moved `p001-c004` from full rank 39 to rank 2.
7. **Two formulations of one topic can rank differently.** T2D-008
   `weight` and `harms` both target the review's comparative-effectiveness
   material, yet their Top-5 lists share no chunks (top-1 `0.3622` vs
   `0.5528`); only the reworded `harms-variant` lifts the labeled chunk from
   rank 3 to rank 2, and `weight`'s labeled chunk sits at rank 4.
8. **Document-scale differences are visible in score levels.** Top-1 cosine
   scores range from 0.2223 (T2D-003 long number-dense query) to 0.6092
   (T2D-002), i.e. absolute scores are not comparable across documents.
9. **The previously documented records are reproduced where they concern
   this benchmark's ranges.** Representative evaluation Top-5s reproduced
   exactly for EVAL-1/EVAL-2/EVAL-3 (T2D-001) and EVAL-4 (T2D-002), and the
   full-rank positions recorded in `retrieval-ranking-investigation.md`
   reproduced exactly for `T2D-006-second-line` (rank 6), `T2D-009-statins`
   (21/42/98), `T2D-010-ckd-screening` (28) and `T2D-010-kidney-protection`
   (12/13). The only record not reproduced is EVAL-5's recorded Top-5 (see §C's
   ambiguous-case table and the engineering-log entry); no other divergence
   was found.
10. **Reproducibility: two consecutive full runs are byte-identical.** Serializing
    the report as `json.dumps(report, sort_keys=True)` (UTF-8) yields SHA-256
    `ED98F678F8770EA1F02276E3CAAF00130907BB9DE56D4255CBF2ED612D88A093` on both
    runs. The committed T2D-001 embedding artifact also reproduces bit-for-bit
    (0/107 vectors differ) when re-embedded from its parsed artifact. A full
    benchmark run performs no network access and no generation call.

## J. INFERENCES

1. The baseline is **adequate but brittle**: it usually surfaces the right
   section, while depending on exact query wording for *where* the relevant
   chunk lands.
2. The dominant failure mechanism is **unweighted lexical mass**: generic
   clinical/function words and citation-dense chunks accumulate cosine mass
   that a short query cannot discriminate against. This is consistent with the
   documented design of `clinivault-baseline-hash-v1` (no IDF, no stopword
   handling, bag-of-words) and with the ranking investigation. It is a
   representational limitation, not an implementation defect.
3. Failure severity appears related to **query specificity vs document
   reference density**: the two deep failures (T2D-009 `statins`, T2D-010
   `ckd-screening`) are both in reference-heavy guideline documents.
4. Because one failure is a 1-rank miss, retrieval quality could plausibly be
   improved by relatively small scoring changes — but this benchmark cannot
   distinguish which change (IDF/stopword weighting vs semantic provider vs
   structure-aware filtering) would help, and T2D-010 also has an independent
   parsing-quality defect.
5. The EVAL-5 discrepancy is an artefact of a historical validation record,
   not of the current implementation: three sibling queries and the embedding
   artifacts reproduce exactly.

## K. NOT YET VALIDATED

1. Behaviour on questions **not** in this labeled set (no unseen-question test).
2. **Semantic embedding** comparison — no alternative provider was run.
3. Statistically significant differences; n=21 is far too small, and labels are
   not exhaustive.
4. Corpus-wide relevance quality beyond these 21 labeled queries.
5. Whether reweighting (IDF/stopwords) or structure-aware filtering would move
   the observed ranks — requires a controlled experiment, out of scope here.
6. T2D-010's parsing defect's exact contribution to its retrieval failures
   (partially overlapping causes: parsing quality vs hash genericity).
7. Multi-document / cross-corpus retrieval (still single-document indexing).

## L. Limitations

- **Qualitative, manually selected labels.** Labels come from prior validation
  evidence, not an exhaustive relevance annotation; other genuinely relevant
  chunks may exist and are unlabeled, so Hit@5/MRR are **lower bounds of a
  specific label set**, not absolute retrieval quality.
- **Non-exhaustive per-query labels.** A query's answer may span several
  chunks; only documented ones are labeled.
- **3 of 21 cases are explicitly ambiguous** (`T2D-001-hba1c`,
  `T2D-003-quadas`, `T2D-008-weight`), reported separately as well as excluded.
- **Small sample.** 21 queries / 9 documents — no statistical claims.
- **Query wording is uncontrolled** in origin (taken from prior runs); some
  queries are long/number-dense (T2D-003) and score scales differ per document.
- **No generation or grounding evaluation** in this unit.
- **T2D-004 excluded** (blocked); corpus is 9 of 10 documents.
- **Full-rank inspection** uses the same `search()` with a larger `top_k` for
  diagnosis only; production Top-K remains 5.
- This document must be read as a **controlled baseline benchmark**, not as
  proof of retrieval quality.
## M. Evidence-based next-step recommendation

The measurement supports a **controlled, bounded next experiment**, not a
retrieval redesign.

**Recommended (justified by the evidence in this document):** add a small,
controlled **retrieval scoring comparison** on exactly this 21-case labeled
set, measuring the *same* metrics and reporting both distributions, for at most
two candidate changes — (a) term weighting (IDF/stopword handling) and
(b) a semantic embedding provider — against the unchanged baseline
(hash / 256 / cosine / Top-K=5). This is justified because 5/21 cases lose
labeled evidence from Top-5, one by a single rank, and because the failures
cluster in reference-heavy documents where unweighted lexical mass dominates.

**Not recommended now:**

- Reranking, hybrid retrieval, vector databases, persistence, agentic or
  corrective RAG — no measured evidence distinguishes these.
- Any change based on the T2D-001 grounding incident — already resolved.
- Changing Top-K — one failure is a 1-rank miss, but four are ≥7 ranks away, so
  Top-K alone is not a principled fix (and T2D-010 evidence is still deeper
  than any reasonable K).

**Sequencing constraint (OBSERVED):** T2D-010's retrieval failures are
confounded by a known parsing-quality defect
(`docs/engineering-log/2026-09-16-t2d-010-column-interleaving.md`). A
T2D-010-focused ingestion-quality check should precede or accompany any
retrieval comparison, otherwise that document's result cannot be attributed.

If the comparison does not materially move these metrics, the correct
conclusion is that the baseline is acceptable for current scope.

## Implementation and testing notes

- Implementation: `src/clinivault_ai/evaluation/` (`metrics.py` pure metric
  functions, `cases.py` static labeled cases, `benchmark.py` offline runner).
  No retrieval, embedding, chunking, parsing, generation or UI code changed.
- Tests: `tests/test_evaluation_metrics.py` — 20 focused offline tests covering
  Hit@1, Hit@5, reciprocal rank, MRR, multiple relevant chunks, no relevant
  chunk, input validation (empty/duplicate labels, invalid `k`) and
  deterministic output, using synthetic ranked lists only (no corpus access,
  no network, no generation).
- Full suite: `.venv/Scripts/python -m unittest discover -s tests` →
  `Ran 190 tests` / `OK` (170 before this unit, 20 added; no existing test
  modified).
- Artifact usage: this unit **reads** the canonical parsed/embedded artifacts
  listed in §D and persists **no** artifacts of its own; no benchmark output is
  written, and nothing was added under `data/parsed/` or `data/embedded/`
  (canonical storage rule, `docs/architecture/artifact-storage.md`).