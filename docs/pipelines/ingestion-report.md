# Ingestion reports (M3)

Each Stage-1 document has one brief-shaped ingestion report answering the
project-brief evidence question: what was seen, parsed, chunked, embedded,
and indexed.

## Location

`data/ingestion-report/stage-1-clean-baseline-corpus/<DOC-ID>/<DOC-ID>.ingestion-report.json`

Reports live here only — never inside `parsed/` or `embedded/` trees, and
report generation never overwrites hash or E5 embedding JSON.

## Shape

```json
{
  "document_id": "T2D-001",
  "total_pages": 23,
  "parsed_pages": 23,
  "failed_pages": [],
  "total_chunks": 107,
  "embedded_chunks": 107,
  "indexed_chunks": 107,
  "ingestion_status": "success"
}
```

- `total_pages`: pages in the parsed document.
- `parsed_pages`: pages whose `extraction_status` is not `"failed"`.
- `failed_pages`: sorted page numbers with `extraction_status == "failed"`.
- `total_chunks` / `embedded_chunks`: lengths of the chunk and embedding
  lists. A mismatch raises `IngestionError` instead of dropping records.
- `indexed_chunks`: chunks available to the index (equals `total_chunks`
  when the build succeeds).
- `ingestion_status`: `"success"` when no page failed, else `"partial"`.

## How reports are built

`clinivault_ai.ingestion.report.build_ingestion_report(document_id,
parsed_document, chunk_output, embedding_artifact)` derives the report from
artifacts already on disk. It checks that all three inputs agree on
`document_id`, then counts. `write_ingestion_report(report, path)` writes
indented JSON, creating parent directories; `report_path(repo_root,
corpus_version, document_id)` returns the canonical path above.

## Current values (hash baseline, 2026-11-10)

All nine documents report `success` with zero failed pages (181 pages, 727
chunks total):

| Document | Pages | Chunks |
|---|---|---|
| T2D-001 | 23 | 107 |
| T2D-002 | 8 | 34 |
| T2D-003 | 19 | 44 |
| T2D-005 | 18 | 84 |
| T2D-006 | 33 | 142 |
| T2D-007 | 19 | 38 |
| T2D-008 | 16 | 66 |
| T2D-009 | 30 | 142 |
| T2D-010 | 15 | 70 |

Chunk counts are identical in the `data/embedded/` (hash) and
`data/embedded-intfloat--e5-small-v2/` (E5) trees.

## Metadata passthrough (same milestone)

`src/clinivault_ai/corpus/catalog.py` holds the nine catalog entries
transcribed from `docs/corpus/corpus-manifest.md` (`document_id`,
`document_name`, `source`, `publication_date`, `version`,
`ingestion_date`). The retrieval store attaches `document_name` to
in-memory records for catalogued documents only; `search()` propagates it
to results and trace candidates, and `context.build_context()` preserves it
in evidence entries and the documents summary. Synthetic and legacy records
with unknown IDs keep their exact historical contract (no extra key).

`section` is deliberately absent: there is no measured deterministic
detector, and invented headings would corrupt provenance (DECISION-018).
