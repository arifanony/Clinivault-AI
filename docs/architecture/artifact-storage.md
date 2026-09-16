# Artifact Storage Contract

Status: established 2026-09-16 after the artifact-storage audit (see the
reconciliation in §J). This document distinguishes the **canonical rule**
from the **current actual state**; the rule is permanent, the state is a
snapshot and is currently incomplete.

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
│       └── <document-id>.pdf
├── parsed/
│   └── <corpus-version>/
│       └── <document-id>/
│           ├── <document-id>.parsed.json
│           └── <document-id>.validation.json
└── embedded/
    └── <corpus-version>/
        └── <document-id>/
            └── <document-id>.embeddings.json
```

Current corpus version: `stage-1-clean-baseline-corpus` (further versions:
`stage-2-domain-evidence-corpus`, `stage-3-stress-evaluation-corpus`).

## C. Stage semantics (existing contracts; no fields invented)

- **RAW** — the original source document (verified PDF), plus any
  source-level artifact associated with it. Raw PDFs are committed for the
  current corpus.
- **PARSED** — validated ingestion output:
  `<DOC>.parsed.json` with `{provenance, pages:[{document_id, filename,
  page_number, text, text_sha256, char_count, word_count, page_width,
  page_height, extraction_status, extraction_error}]}` (per
  `ingestion/validation.py`), plus the mechanical validation record
  `<DOC>.validation.json`.
- **EMBEDDED** — validated embedding artifact `<DOC>.embeddings.json` with
  `{document_id, model:{name, dimension, ...provider params}, statistics,
  embeddings:[{chunk_id, document_id, page_number, vector}]}` (per
  `embedding/embedder.py`). Chunk text is NOT duplicated here; the
  chunk_id join to the parsed/chunking output is the provenance mapping.

## D. Naming conventions

- Embedding artifact filename: `<document-id>.embeddings.json`.
- Parsed artifact filename: `<document-id>.parsed.json`;
  validation record: `<document-id>.validation.json`.
- `<document-id>` is the existing corpus identifier (T2D-001, T2D-003, ...).
- `chunk_id` remains `<document-id>-p<page>-c<index>` as already defined by
  the chunking contract.

## E. Durable vs temporary artifacts

**DURABLE** — artifacts needed to reproduce/validate the pipeline:
everything under the canonical structure above; committed where repository

## H. Validation/reporting requirements

- Every meaningful validation or final report MUST state the exact
  artifact path(s) used, and whether each was read from the canonical
  location or generated in memory.
- Persistence claims must be verified against the filesystem and Git
  (`git status`, `git ls-files`) — not inferred from tooling output.
- Temporary artifacts must be labeled temporary; if deleted, say so.
- Before a downstream stage runs, the upstream durable artifact must be
  verified to exist at its canonical path.

## I. Security rule

Never store secrets, API keys, `.env` contents, or credentials in any data
artifact. Data artifacts contain corpus content and pipeline provenance
only.

## J. Current known corpus artifact state (audit 2026-09-16)

CANONICAL RULE vs CURRENT ACTUAL STATE — the rule above is the contract;
the table below is what actually exists (verified: filesystem recursion +
`git ls-tree -r HEAD`):

| Document | RAW (PDF) | PARSED (parsed+validation.json) | EMBEDDED |
|---|---|---|---|
| T2D-001 | present, committed | present, committed | **present, committed** |
| T2D-002 | present, committed | **missing** | **missing** |
| T2D-003 | present, committed | present, committed (e190b22) | **missing** |
| T2D-005 | present, committed | present, committed (e190b22) | **missing** |
| T2D-006 | present, committed | present, committed (e190b22) | **missing** |
| T2D-007 | present, committed | present, committed (e190b22) | **missing** |
| T2D-008 | present, committed | present, committed (e190b22) | **missing** |
| T2D-009 | present, committed | present, committed (e190b22) | **missing** |
| T2D-010 | present, committed | present, committed (e190b22) | **missing** |

The only embedding artifact in the entire worktree is
`data/embedded/stage-1-clean-baseline-corpus/T2D-001/T2D-001.embeddings.json`
(587,624 B, tracked, present in HEAD). No `*.embeddings.json` exists
anywhere else, tracked or untracked.

Explanation of the discrepancy: the document-generalization and
corpus-generalization validation units computed chunking and embeddings
**in memory** (chunk_pages + generate_embeddings feeding VectorStore
directly) and never wrote embedding artifacts to `data/embedded/`. The
validation results themselves are valid (deterministic pipeline, replayed
and confirmed), but their embedding artifacts were transient. T2D-002's
parsed artifact was likewise never persisted.

Consequence: regeneration of the missing embedding artifacts (T2D-002's
parsed artifact too) is required in a SEPARATE implementation unit. This
audit intentionally did not regenerate, move, or rewrite any artifact.

policy allows (all `data/parsed` and `data/embedded` JSON artifacts and raw
PDFs of the current corpus are committed); exact paths referenced by
validation evidence.

**TEMPORARY** — one-off evaluation/probe scripts, temporary trace dumps
(e.g. the `_t2d*.json` trace files of the generalization-validation unit),
scratch outputs, debugging files. These live outside `data/`, are never
committed, and are deleted after the unit — and any report that relied on
them must say so.

A validation run that computes chunks/embeddings **in memory** has produced
temporary, non-durable artifacts by definition. If its results matter, the
artifacts must be written to the canonical path and committed (or the report
must state that they were not persisted).

## F. Document-level isolation

Each document gets its own stage-specific directory. No document's artifact
may be written into another document's directory, and no tooling may merge
or overwrite artifacts across documents.

## G. Corpus-version isolation

The `<corpus-version>` path segment is mandatory. Artifacts from different
corpus generations (stage-1 / stage-2 / stage-3) must never share a
directory or a filename.
