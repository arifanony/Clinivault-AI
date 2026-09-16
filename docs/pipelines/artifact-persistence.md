# Artifact Persistence — Validated Corpus Artifacts

Unit: durability only. No change to embeddings, chunking, parsing,
retrieval, generation, Top-K, or any pipeline behavior.

## A. Objective

The artifact-storage audit (`docs/architecture/artifact-storage.md`, commit
`8ce9420`) established that the corpus validation units had computed
chunking and embeddings **in memory** and never persisted them: only
T2D-001's embedding artifact existed durably, and T2D-002 had no persisted
parsed artifact at all. This unit makes all previously validated artifacts
durable at the canonical paths, without regenerating anything beyond what
the deterministic baseline already implies.

## B. Previous state

- RAW: 9/9 PDFs committed.
- PARSED: T2D-001, T2D-003, T2D-005–T2D-010 committed; T2D-002 missing.
- EMBEDDED: only `T2D-001.embeddings.json` committed; T2D-002, 003, 005–010
  existed only as in-memory results of validation runs.

## C. Action

- T2D-002: ingested with the **existing, unchanged** `clinivault_ai.ingestion`
  CLI using the corpus-manifest SHA-256
  (`D523E5447FE6592727B1C66A5F7D9F256042011CFB410C93695AF1C08F8F451F`,
  verified against the committed PDF) and expected page count (8).
- All eight missing embedding artifacts: generated with the unchanged
  `chunk_pages` + `generate_embeddings` functions
  (`clinivault-baseline-hash-v1`, 256-dim) from each document's committed
  parsed artifact, and written with the existing `write_json` serializer.
- T2D-001 was NOT rewritten; it was re-generated in memory purely as a
  determinism check (see F).

## D. Exact artifact inventory (all verified on disk, then committed)

Parsed (T2D-002, new):

- `data/parsed/stage-1-clean-baseline-corpus/T2D-002/T2D-002.parsed.json`
- `data/parsed/stage-1-clean-baseline-corpus/T2D-002/T2D-002.validation.json`

Embedded (all eight new; T2D-001 pre-existing):

- `data/embedded/stage-1-clean-baseline-corpus/T2D-002/T2D-002.embeddings.json` (188,393 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-003/T2D-003.embeddings.json` (188,092 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-005/T2D-005.embeddings.json` (455,959 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-006/T2D-006.embeddings.json` (777,464 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-007/T2D-007.embeddings.json` (200,154 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-008/T2D-008.embeddings.json` (355,501 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-009/T2D-009.embeddings.json` (766,826 B)
- `data/embedded/stage-1-clean-baseline-corpus/T2D-010/T2D-010.embeddings.json` (388,987 B)

## E. Validation (reloaded from disk after writing)

For every artifact: valid JSON; `document_id` correct; embedding count ==
chunk count; chunk IDs exactly equal the chunking output's IDs in order; no
duplicate chunk IDs; all vectors 256-dim; all values finite; no zero
vectors; model metadata `clinivault-baseline-hash-v1`/256; provenance
(document_id + page_number) preserved per record. All checks passed for all
eight artifacts (script log verified, then the script deleted as temporary).

Chunk counts (matching the previously documented validation figures
exactly): T2D-002: 34, T2D-003: 44, T2D-005: 84, T2D-006: 142, T2D-007: 38,
T2D-008: 66, T2D-009: 142, T2D-010: 71. Chunk↔embedding agreement: 1:1 for
every document. T2D-002 ingestion result: 8 pages, 50,445 chars, 0 empty,
0 failed, overall status `pass` — identical to the historical validation.

## F. Reproducibility

For the deterministic hash provider, re-embedding T2D-001 from its
committed parsed artifact reproduced the committed
`T2D-001.embeddings.json` **bit-for-bit**: same chunk IDs, identical
vectors, identical model metadata, identical statistics. This establishes
that the persisted artifacts correspond to the same deterministic embedding
process used during the earlier validation runs. Additional evidence: every
persisted chunk count matches the counts recorded in the corpus-generalization
validation document.

## G. Limitations

- T2D-004 remains blocked and has no artifacts at any stage (not forced).
- This unit changes no embedding/retrieval/quality behavior — the artifacts
  are the same deterministic outputs the pipeline already produced in
  memory.
- The persisted embeddings remain the `clinivault-baseline-hash-v1` lexical
  baseline with its documented ranking limitations (see
  `retrieval-ranking-investigation.md`); persistence does not improve them.
- Extraction quality issues (e.g., T2D-010 multi-column interleaving) are
  inherited as-is from the committed parsed artifacts.
- The generator script used to write the artifacts was temporary and was
  deleted after verification; the capability now lives entirely in the
  existing `generate_embeddings` + `write_json` functions.
