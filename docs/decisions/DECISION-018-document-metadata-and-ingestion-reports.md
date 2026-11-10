# Engineering Decision: Document metadata passthrough and ingestion reports

## Status

Chosen

## Date

2026-11-10

## Problem

Retrieval results, context bundles, and traces carry only
`(document_id, page_number, chunk_id)`. Brief-level fields from the corpus
manifest (document title, source, publication date, version) never reach the
evidence the UI shows, and there is no per-document ingestion record matching
the project-brief evidence shape (`document_id, total_pages, parsed_pages,
failed_pages, total_chunks, embedded_chunks, indexed_chunks,
ingestion_status`). The M1–M7 guide names this the M3 gap (DECISION-018).

## What This Part of the System Does

- What goes in: the Stage-1 catalog (nine obtained documents), parsed page
  records with `extraction_status`, chunk outputs, and embedding artifacts.
- What happens inside: `clinivault_ai.corpus.catalog` joins brief-level
  metadata onto in-memory retrieval records at index time;
  `clinivault_ai.ingestion.report.build_ingestion_report` derives one
  brief-shaped report per document and fails loud on identity or
  chunk/embedding count mismatches.
- What comes out: retrieval results and context bundles with optional
  `document_name`; one `<DOC>.ingestion-report.json` per document under
  `data/ingestion-report/stage-1-clean-baseline-corpus/<DOC>/`.
- Where the output goes next: the observability UI trace and any future
  Errata contract can read titles and ingestion evidence without
  rediscovering the manifest.

## Requirements

- Fields come from `docs/corpus/corpus-manifest.md` only: `document_id`,
  `document_name` (Title), `source`, `publication_date`, `version`,
  `ingestion_date`. Nothing is guessed from PDF text.
- `section` stays absent: there is no measured deterministic detector, and
  inventing headings would corrupt provenance.
- `document_name` is optional at every stage boundary; synthetic and legacy
  records (unknown IDs) keep their exact historical contract.
- Chunk count must equal embedding count, or the report fails instead of
  dropping records silently.
- Reports live under `data/ingestion-report/` — never inside `parsed/` or
  `embedded/` trees, and never overwriting hash or E5 embedding JSON.

## Options We Considered

- Option A: catalog module joined at index time + report builder (chosen).
- Option B: rewrite parsed/chunk/embedding artifacts to embed titles.
  Rejected: it would regenerate durable artifacts and risk overwriting hash
  JSON for no retrieval gain.
- Option C: infer `section` headings from PDF text now. Rejected: no
  deterministic detector exists; invented headings are worse than absence.

## Comparison

Option A is the smallest change that closes the measured gap: no artifact
regeneration, no new dependencies, backward-compatible optional fields, and
the brief evidence shape produced from data already on disk.

## Decision

M3 implements the catalog module (`src/clinivault_ai/corpus/catalog.py`),
`build_ingestion_report` / `write_ingestion_report`
(`src/clinivault_ai/ingestion/report.py`), optional `document_name`
passthrough in `retrieval/store.py`, `retrieval/search.py` (results and
trace candidates), and `context/builder.py` (evidence entries and documents
summary, with type validation), plus nine committed ingestion reports.

## Why We Chose It

OBSERVED: the nine Stage-1 documents parse to 181 pages and chunk to 727
units (T2D-001 107, T2D-002 34, T2D-003 44, T2D-005 84, T2D-006 142,
T2D-007 38, T2D-008 66, T2D-009 142, T2D-010 70), with identical counts in
the hash and E5 embedding trees and zero failed pages. The catalog values
are transcribed from the manifest record for each document; T2D-004 is
blocked-access and has no entry by design.

## Trade-offs

Chunk artifacts on disk stay title-free; titles exist in the catalog and in
memory at index time. Reports record counts, not the embedding provider, so
a future provider switch does not invalidate them.

## What We Did Not Choose

Rewriting durable artifacts to embed titles. Inventing `section` headings.
A vector database, hybrid retrieval, or reranking — M6 remains deferred
until a measured weakness appears after M1–M5.

## Assumptions

The manifest remains the source of truth for brief-level fields. Chunking
stays page-pure, so `failed_pages` derived from `extraction_status` keeps
its meaning.

## How We Will Validate This

- `python -m unittest tests.test_metadata` (14 tests: catalog, passthrough,
  report shape, mismatch fail-loud, writer round-trip).
- Full gate `python -m unittest discover -s tests` with no new failures
  beyond the known sandbox-proxy loopback error.
- Nine reports on disk under `data/ingestion-report/`, all `success`.

## When We Should Revisit It

When a deterministic `section` detector is measured, or when Stage 2 adds
documents (each new document gets a catalog entry and a report).
