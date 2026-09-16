# 2026-09-16 — EVAL-5 recorded retrieval is not reproducible

## Category

Validation-record integrity (no source-code change made). Discovered while
labeling the controlled baseline retrieval benchmark
(`docs/pipelines/retrieval-baseline-benchmark.md`).

## Discovery

The benchmark needed a defensible expected-evidence label for the
`representative-evaluation.md` EVAL-5 case (T2D-001, "HbA1c test to
diagnose diabetes"). Replaying that exact query against the persisted
baseline did not reproduce the recorded Top-5.

OBSERVED — recorded in `docs/pipelines/representative-evaluation.md`
(EVAL-5):

```
1:T2D-001-p002-c002:0.5472, 2:T2D-001-p002-c003:0.5335,
3:T2D-001-p014-c003:0.5178, 4:T2D-001-p023-c004:0.5140,
5:T2D-001-p017-c003:0.5107   (107 total candidates)
```

OBSERVED — actual replay of the same query, same persisted artifacts,
same provider, same code, Top-K=5:

```
1:T2D-001-p012-c002:0.3959, 2:T2D-001-p009-c004:0.3651,
3:T2D-001-p012-c001:0.3361, 4:T2D-001-p004-c003:0.3333,
5:T2D-001-p023-c004:0.3272   (107 total candidates)
```

Only rank 5 (`p023-c004`) is common; the recorded rank 1/2 chunks
(`p002-c002`, `p002-c003`) sit at full ranks **48** and **32**.

## What was ruled out (OBSERVED)

- Not an artifact problem: the committed T2D-001 embedding artifact
  reproduces **bit-for-bit** — re-embedding its 107 chunks with the
  current provider produced **0/107** differing vectors, and counts
  (107/107) and dimension (256) match.
- Not an environment/ordering problem: EVAL-1, EVAL-2 and EVAL-3 replay
  the recorded Top-5 **exactly** (e.g. EVAL-1:
  `0.6018 / 0.5851 / 0.5814 / 0.5680 / 0.5641`), with the same code path
  and the same store instance used for EVAL-5.
- Not a query-text problem: the query string, document, and stored
  candidate count (107) are identical in both records.

## Second inconsistency in the same record

The EVAL-5 claim table cites the evidence phrase
`"either A1C or glucose criteria"` as "present verbatim" in
`T2D-001-p002-c002`. That phrase is **absent from the entire T2D-001
chunk text** (whitespace-normalized corpus-wide search: `False`; the
narrower `"A1C or glucose criteria"` is also `False`; `"glucose
criteria"` alone is `True`). By contrast, EVAL-1's programmatic checks
`"repeat testing"` and `"IADPSG"` **do** verify.

## Classification

Historical validation-record inconsistency, **not** a retrieval
implementation defect. The current retrieval implementation is
deterministic and self-consistent; three of four T2D-001 queries replay
exactly and the embedding artifacts are reproducible. The recorded
EVAL-5 retrieval numbers and one quoted substring cannot be reproduced
from the current durable corpus state, so their provenance is
unverifiable (consistent with class F of the artifact audit: a report
claim exceeding what the current state can support).

## Impact

- EVAL-5's *generation* findings are unaffected in substance: the
  model's documented behaviour (correctly stating the A1C cut-off gap
  rather than inventing values) does not depend on the disputed Top-5.
- The benchmark marks the `T2D-001-hba1c` label **AMBIGUOUS** and
  reports aggregate metrics both with and without it.
- `docs/pipelines/representative-evaluation.md` EVAL-5 has been
  annotated with a reconciliation note; the historical text is
  preserved, not rewritten.

## Action

Recorded. No code change. Before EVAL-5's recorded retrieval numbers are
used as evidence in any future decision, they should be re-measured from
the durable artifacts.
