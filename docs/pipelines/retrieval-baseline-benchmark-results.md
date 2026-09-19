# Controlled Baseline Retrieval Benchmark â€” Measured Results

Status: **baseline measurement complete** (offline, deterministic, reads-only).

This document records the exact measured results of the 21-case controlled
retrieval benchmark defined in `docs/pipelines/retrieval-baseline-benchmark.md`.
It is a single offline run of `python -m clinivault_ai.evaluation.benchmark`
against the persisted corpus artifacts under `data/parsed/` and
`data/embedded/`.

## How to reproduce

```
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark
```

Environment: no network, no generation, no API keys. Uses persisted
`BaselineHashEmbeddingProvider` (clinivault-baseline-hash-v1, 256-dim) vectors
and cosine similarity at Top-K=5.

## Aggregate results

| Metric | Value |
|---|---|
| Cases | 21 |
| Documents | 9 (T2D-004 excluded - blocked) |
| Hit@1 | 8 / 21 |
| Hit@5 | 16 / 21 |
| MRR | 0.5095 |

5 of 21 cases miss Top-5: `T2D-001-hba1c`, `T2D-006-second-line`,
`T2D-009-statins`, `T2D-010-ckd-screening`, `T2D-010-kidney-protection`.

## Per-case results

### T2D-001

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-001-diagnosis | p014-c003, p002-c002, p002-c003 | 1 | 1 | 1.0 | 1 |
| T2D-001-classification | p015-c002, p004-c003, p013-c003 | 1 | 1 | 1.0 | 1 |
| T2D-001-gdm | p023-c001, p023-c004 | 1 | 1 | 1.0 | 1 |
| T2D-001-hba1c (AMB) | p002-c002, p002-c003 | 0 | 0 | 0.0 | None; full-rank: 48, 322 |

### T2D-002

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-002-screening | p007-c003, p002-c001, p004-c002 | 1 | 1 | 1.0 | 1 |

### T2D-003

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank | Notes |
|---|---|---|---|---|---|---|
| T2D-003-hba1c-accuracy | p008-c002, p008-c001 | 1 | 1 | 1.0 | 1 | verified verbatim |
| T2D-003-quadas (AMB) | p001-c002, p004-c003 | 1 | 0 | 0.3333 | 3 | label covers QUADAS-2 half only |

### T2D-005

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-005-a1c-goal | p001-c001 | 1 | 0 | 0.2 | 5 |
| T2D-005-hypoglycemia | p004-c003 | 1 | 1 | 1.0 | 1 |

### T2D-006

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-006-glp1-sglt2 | p010-c002, p008-c003 | 1 | 0 | 0.25 | 4 |
| T2D-006-second-line | p015-c004 | 0 | 0 | 0.0 | None; full-rank: 6 |

### T2D-007

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-007-first-line | p003-c002 | 1 | 0 | 0.3333 | 3 |
| T2D-007-add-on | p009-c001, p008-c002, p002-c002 | 1 | 1 | 1.0 | 1 |

### T2D-008

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank | Notes |
|---|---|---|---|---|---|---|
| T2D-008-weight (AMB) | p001-c002 | 1 | 0 | 0.25 | 4 | label covers weight half only |
| T2D-008-harms | p013-c004, p001-c004 | 1 | 0 | 0.3333 | 3 | SGLT2 harms chunk outside Top-5 |
| T2D-008-harms-variant | p001-c004 | 1 | 0 | 0.5 | 2 | OR 3.29 verified |

### T2D-009

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank |
|---|---|---|---|---|---|
| T2D-009-bp | p003-c002, p006-c001, p006-c003 | 1 | 1 | 1.0 | 1 |
| T2D-009-statins | p008-c003, p008-c004, p009-c001 | 0 | 0 | 0.0 | None; full-rank: 42, 988, 21 |
| T2D-009-statin-variant | p008-c003, p009-c002 | 1 | 0 | 0.5 | 2 |

### T2D-010

| Case | Expected chunks | Hit5 | Hit1 | RR | Rank | Notes |
|---|---|---|---|---|---|---|
| T2D-010-ckd-screening | p001-c002 | 0 | 0 | 0.0 | None; full-rank: 19 | parsing-confounded, section 11.1 |
| T2D-010-kidney-protection | p006-c004, p006-c003 | 0 | 0 | 0.0 | None; full-rank: 11, 122 | parsing-confounded, section 11.13 |

Both T2D-010 cases miss Top-5 significantly. T2D-010 weakness is documented in
the retrieval-ranking investigation and confounded by a multi-column
text-interleaving defect (see `docs/engineering-log/2026-09-16-t2d-010-column-interleaving.md`).
These results are recorded after regenerating the T2D-010 artifacts against the
current reader (see below).

## Artifact changes made in this run

T2D-010's committed embedding artifact was found **stale** relative to the
current reader (post-commit `896c7af`, "guard table internal gutter candidates"):

- Committed T2D-010 embedding: **71 records** including `p011-c005`.
- Current reader produces **70 chunks** - the table gutter guard eliminated the
  spurious `p011-c005` fragment.
- The other 8 documents were verified consistent (chunk count == embedding count,
  0 vector changes).

**Remediation:** T2D-010 parsed + chunk + embedding artifacts were regenerated
in-place using the existing, unchanged pipeline functions
(`chunk_pages` + `generate_embeddings` + `BaselineHashEmbeddingProvider`).
The regenerated artifact contains 70 records.

This regeneration restores chunk/embedding count consistency (required to pass
the `VectorStore.from_artifacts` no-silent-drops invariant) but does **not**
resolve the T2D-010 retrieval weakness, which is a scoring/specificity issue on
reference-heavy content (per the forensic investigation).

## Comparison with documented baseline

Results match the values in `docs/pipelines/retrieval-baseline-benchmark.md`.
The aggregate is Hit@1 = 8/21, Hit@5 = 16/21, MRR = 0.5095.
