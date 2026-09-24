# Artifact Storage Contract

Status: established 2026-09-16 after the artifact-storage audit; the missing
artifacts were persisted in the follow-up durability unit. This document
distinguishes the **canonical rule** from the **current actual state**: the rule
is permanent, the state is a snapshot (§J). The section order was normalized on
2026-09-16 after an earlier edit left sections out of sequence; no wording was
changed by that normalization.

## A. Purpose

Make artifact location, naming, persistence status, and provenance
unambiguous so that:

- any validation result can be reproduced from stated artifact paths;
- an artifact is never reported as persisted unless it actually is;
- documents and corpus versions cannot silently collide or overwrite;
- downstream stages never build on unverifiable upstream artifacts.

## B. Canonical directory structure

```
data/
├── raw/
│   └── <corpus-version>/
│       └── <document-id>/
│           └── <document-id>.pdf
├── parsed/
│   └── <corpus-version>/
│       └── <document-id>/
│           ├── <document-id>.parsed.json
│           └── <document-id>.validation.json
├── embedded/
│   └── <corpus-version>/
│       └── <document-id>/
│           └── <document-id>.embeddings.json
```

Current corpus version: `stage-1-clean-baseline-corpus`. Reserved future
versions (directories already reserved in `data/raw/`):
`stage-2-domain-evidence-corpus`, `stage-3-stress-evaluation-corpus`.

## C. Stage semantics (existing contracts; no fields invented)

- **RAW** — the original source document (verified PDF), plus any source-level
  artifact associated with it. Raw PDFs are committed for the current corpus.
- **PARSED** — validated ingestion output: `<DOC>.parsed.json` with
  `{provenance, pages:[{document_id, filename, page_number, text, text_sha256,
  char_count, word_count, page_width, page_height, extraction_status,
  extraction_error}]}` (per `ingestion/validation.py`), plus the mechanical
  validation record `<DOC>.validation.json`.
- **EMBEDDED** — validated embedding artifact `<DOC>.embeddings.json` with
  `{document_id, model:{name, dimension, ...provider params}, statistics,
  embeddings:[{chunk_id, document_id, page_number, vector}]}` (per
  `embedding/embedder.py`). Chunk text is NOT duplicated here; the `chunk_id`
  join to the parsed/chunking output is the provenance mapping.

## D. Naming conventions

- Embedding artifact filename: `<document-id>.embeddings.json`.
- Parsed artifact filename: `<document-id>.parsed.json`; validation record
  `<document-id>.validation.json`.
- `<document-id>` is the existing corpus identifier (T2D-001, T2D-003, ...).
- `chunk_id` remains `<document-id>-p<page>-c<index>` as already defined by the
  chunking contract.
- Corpus-version directory name: `stage-<n>-<descriptor>-corpus`.
- Raw source layout under the rule: one `<document-id>/` directory per document,
  matching the parsed and embedded directories. The current raw corpus predates
  this contract and is stored flat (`<DOC>-<slug>.pdf`) — recorded as a known
  deviation in §J, not as compliance.

## E. Durable vs temporary artifacts

**DURABLE** — artifacts needed to reproduce/validate the pipeline: everything
under the canonical structure above; committed where repository policy allows
(all `data/parsed` and `data/embedded` JSON artifacts and the raw PDFs of the
current corpus are committed); exact paths referenced by validation evidence.

**TEMPORARY** — one-off evaluation/probe scripts, temporary trace dumps
(e.g. the `_t2d*.json` trace files of the generalization-validation unit),
scratch outputs, debugging files. These live outside `data/`, are never
committed, and are deleted after the unit — and any report that relied on them
must say so.

A validation run that computes chunks/embeddings **in memory** has produced
temporary, non-durable artifacts by definition. If its results matter, the
artifacts must be written to the canonical path and committed (or the report
must state that they were not persisted).

**Evaluation outputs.** Evaluation/benchmark runs persist **no** artifacts by
default — the controlled baseline retrieval benchmark
(`docs/pipelines/retrieval-baseline-benchmark.md`) reads canonical artifacts and
writes nothing. If an evaluation output must become durable it requires its own
stage directory `data/evaluation/<corpus-version>/<run-id>/`; evaluation outputs
must never be written into `data/parsed/` or `data/embedded/`.

## F. Document-level isolation

Each document gets its own stage-specific directory. No document's artifact may
be written into another document's directory, and no tooling may merge or
overwrite artifacts across documents.

## G. Corpus-version isolation

The `<corpus-version>` path segment is mandatory. Artifacts from different
corpus generations (stage-1 / stage-2 / stage-3) must never share a directory or
a filename.

## H. Validation/reporting requirements

- Every meaningful validation or final report MUST state the exact artifact
  path(s) used, and whether each was read from the canonical location or
  generated in memory.
- Persistence claims must be verified against the filesystem and Git
  (`git status`, `git ls-files`) — not inferred from tooling output.
- Temporary artifacts must be labeled temporary; if deleted, say so.
- Before a downstream stage runs, the upstream durable artifact must be verified
  to exist at its canonical path.

## I. Security rule

Never store secrets, API keys, `.env` contents, or credentials in any data
artifact. Data artifacts contain corpus content and pipeline provenance only.

## J. Current known corpus artifact state (snapshot 2026-09-16)

CANONICAL RULE vs CURRENT ACTUAL STATE — §B–§I are the contract; this section is
what actually exists on disk and in Git. The original audit found only T2D-001
durable (the other documents' embeddings had been computed in memory during
validation and never written; T2D-002 had never been parsed to disk). The
durability unit of 2026-09-16 regenerated and persisted the missing artifacts
using the unchanged baseline implementation
(`docs/pipelines/artifact-persistence.md`); all are committed.

| Document | Raw | Parsed | Validation | Embedded | Verification |
|---|---|---|---|---|---|
| T2D-001 | OK | OK | OK | OK (pre-existing) | re-embedded bit-identical (determinism check), 107×256 |
| T2D-002 | OK | OK | OK | OK | validated (8 pages, 50,445 chars, 34×256, 1:1) |
| T2D-003 | OK | OK | OK | OK | validated (44×256, 1:1) |
| T2D-005 | OK | OK | OK | OK | validated (84×256, 1:1) |
| T2D-006 | OK | OK | OK | OK | validated (142×256, 1:1) |
| T2D-007 | OK | OK | OK | OK | validated (38×256, 1:1) |
| T2D-008 | OK | OK | OK | OK | validated (66×256, 1:1) |
| T2D-009 | OK | OK | OK | OK | validated (142×256, 1:1) |
| T2D-010 | OK | OK | OK | OK | validated (71×256, 1:1) |

T2D-004 remains blocked and has NO artifacts at any stage.

Exact paths — RAW (actual layout, committed):

- `data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-002-uspstf-2021-prediabetes-t2d-screening.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-003-kaur-2020-diagnostic-accuracy-sr-meta.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-005-ada-2026-soc-06-glycemic-goals.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-006-ada-2026-soc-09-pharmacologic.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-007-acp-2024-newer-pharmacologic-t2d.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-008-nong-2025-t2d-medications-living-nma.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-009-ada-2026-soc-10-cardiovascular.pdf`
- `data/raw/stage-1-clean-baseline-corpus/T2D-010-ada-2026-soc-11-ckd.pdf`

Exact paths — PARSED and EMBEDDED (per-document directories, committed), for
`<DOC>` in T2D-001, T2D-002, T2D-003, T2D-005, T2D-006, T2D-007, T2D-008,
T2D-009, T2D-010:

- `data/parsed/stage-1-clean-baseline-corpus/<DOC>/<DOC>.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/<DOC>/<DOC>.validation.json`
- `data/embedded/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json`

**Production E5 embeddings (DECISION-017, EVAL-HF durable tree).** Hash
JSON under `data/embedded/` is unchanged. Production UI (T2D-001) and
`benchmark --provider e5` read:

- `data/embedded-intfloat--e5-small-v2/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json`

These are 384-d vectors, `model.name` = `intfloat/e5-small-v2`,
`input_formatting` = `raw`. Pair them only with `E5EmbeddingProvider`
(query encoding uses `embed_texts`, no prefixes). Other EVAL-HF trees
(`data/embedded-<org>--<model>/`) remain evaluation-only.

**Known deviation (raw stage).** The canonical rule (§B) requires a
per-document directory at every stage, but the raw PDFs above are stored flat as
`<DOC>-<slug>.pdf` inside the corpus-version directory. This is recorded as a
deviation, not compliance. Normalization is deferred until raw artifacts are
next touched deliberately; no raw artifact may be moved or renamed merely to
match the rule (that would break the manifest hashes and prior ingestion
evidence).

Historical note (preserved): the corpus-generalization validation unit generated
the T2D-003..T2D-010 embeddings in memory; that run's results were valid, but its
embedding artifacts were transient until the later persistence unit.
Reproducibility evidence: re-embedding T2D-001 from its committed parsed
artifact with the unchanged baseline provider reproduced the committed artifact
bit-for-bit (identical chunk IDs, vectors, model metadata, statistics); all
persisted chunk counts match the previously documented validation figures
exactly (T2D-002: 34, T2D-003: 44, T2D-005: 84, T2D-006: 142, T2D-007: 38,
T2D-008: 66, T2D-009: 142, T2D-010: 71).

Consumers: the controlled retrieval baseline benchmark
(`docs/pipelines/retrieval-baseline-benchmark.md`) reads the parsed and embedded
artifacts above directly and performs no network access and no generation.
