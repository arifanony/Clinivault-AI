# Architecture

Status: living snapshot (last reconciled 2026-10-06) — written as
components actually exist. Clinivault is still evolving; this is not a
final architecture.

Foundational rules live in
[DECISION-001: repository architecture](../decisions/DECISION-001-repository-architecture.md):
layered stage packages in strict data-flow order, plain-dict
JSON-serializable stage contracts, one fail-loud error type per stage,
and abstraction seams only where current requirements justify
replaceability (currently the `EmbeddingProvider` and `GenerationProvider`
seams exist; other components stay concrete until a demonstrated need justifies
abstraction). The generation stage and its seam are described in
[generation-baseline.md](../pipelines/generation-baseline.md).

## Implemented now

```
Clinical PDF
  -> ingestion/source.py      verify SHA-256, encryption, page count
  -> ingestion/parsing.py     column-aware text extraction (chunking/reader.py)
  -> ingestion/validation.py  mechanical checks + statistics
  -> <DOC-ID>.parsed.json     {provenance, pages}
  -> chunking/chunker.py      page-pure structural chunks
  -> chunking/validate.py     mechanical chunk-contract checks
  -> embedding/embedder.py    provider seam -> validated embedding records
  -> data/embedded/...json    {document_id, model, statistics, embeddings}
  -> retrieval/store.py       in-memory cosine index, one doc or merged corpus (M2)
  -> retrieval/search.py      query embedding + deterministic top-k
  -> context/builder.py       inspectable evidence bundle (+ M5 max_chars budget)
  -> generation/generator.py  grounded prompt + provider seam -> answer (+ M5 citation/sentinel/attempts checks)
  -> pipeline/__init__.py     run_query: retrieval -> context -> generation traces + execution record (M4, M5)
  -> pipeline/records.py      execution record builder + opt-in JSONL log (M4, M5)
  -> ui/app.py                observability console; nine-doc index loaded once (M2)
  -> api/app.py               FastAPI query API over run_query; index loaded once at startup (M7)
```

Stage contracts (all plain dicts, JSON-serializable):

| Stage | Input | Output |
|---|---|---|
| ingestion | verified PDF | `{provenance, pages:[{document_id, filename, page_number, text, text_sha256, char_count, word_count, page_width, page_height, extraction_status, extraction_error}]}` |
| chunking | parsed document | `{document_id, config, statistics, chunks:[{chunk_id, document_id, page_number, chunk_index, text}]}` |
| embedding | chunk output | `{document_id, model, statistics, embeddings:[{chunk_id, document_id, page_number, vector}]}` |
| retrieval | chunk output + embedding artifact | `[{chunk_id, document_id, page_number, score, text}]` (best first; plus optional `document_name` for catalogued documents) |
| context | retrieval results (+ optional query, optional max_chars) | `{query, evidence_count, documents, evidence:[{rank, chunk_id, document_id, page_number, score, text}], truncated_chunk_ids}` (each level carries optional `document_name` when the result had it; M5 budget drops the lowest-rank tail whole items at a time, rank 1 always kept) |
| generation | evidence bundle + provider | `{query, answer, status ∈ ok/no_evidence/abstained, provider, model, evidence, prompt_text, timings, usage, attempts, invalid_citations}` (M5: ABSTAIN: sentinel refusal, citation-ref checks, 429/5xx provider retry) |
| ingestion report | parsed document + chunk output + embedding artifact | `{document_id, total_pages, parsed_pages, failed_pages, total_chunks, embedded_chunks, indexed_chunks, ingestion_status}` under `data/ingestion-report/<corpus-version>/<DOC-ID>/` |
| execution record | run_query outputs (results + bundle + result) | `{run_id, timestamp, query, retrieval:{top_k, chunks}, context:{chunk_ids_used, truncated_chunk_ids}, generation:{model, answer, abstained, status}, sources}` appended as JSONL only when `run_log_path` or `CLINIVAULT_RUN_LOG` is set (default: no write; `runs/` gitignored) |

Provenance survives every boundary: document -> page -> chunk ->
embedding -> retrieval result -> evidence bundle. Each stage re-validates
its input and raises its own error type instead of dropping records.

Detailed stage behavior lives in the pipeline docs
([pipelines/](../pipelines/README.md)); the engineering log records the
problems that shaped this architecture (reader.py reading-order work).
The canonical artifact directory structure, naming, and persistence rules
are defined in [artifact-storage.md](artifact-storage.md), which also tracks
the current per-document artifact state.

## Deliberately replaceable

- Embedding model (via the `EmbeddingProvider` seam; production retrieval
  is raw `intfloat/e5-small-v2` per DECISION-017; `clinivault-baseline-hash-v1`
  remains the deterministic contract baseline and comparison path, NOT a
  semantic model).
- Generation provider (via the `GenerationProvider` seam; baseline is
  Gemini `gemini-2.5-flash` per DECISION-007, behind the grounded
  generation contract of DECISION-011).

## Deliberately concrete (for now, per DECISION-001's seam principle)

- PDF parsing wrapper (pdfplumber per DECISION-006).
- Vector store (in-memory index over the embedding artifact).
- Context builder (packaging logic over retrieval results).

## The two-products rule

Clinivault is a standalone clinical evidence product; Errata is a
separate, reusable AI evaluation product that lives in its own
repository. Clinivault preserves the structured evidence, provenance, and
execution records that would let Errata evaluate this pipeline later
through a shared contract — but integration is not a current MVP goal,
and no Errata logic lives here.

## Not yet built

Claim-level grounding verification and `section` detection (deferred
in M3 until a deterministic detector is measured). Catalog titles and
ingestion reports are done (M3, DECISION-018); per-query execution
records are done (M4, DECISION-019); deterministic answer-reliability
checks are done (M5, DECISION-020); the production query API,
container, and CI are done (M7, DECISION-021). The ordered roadmap for the rest
lives in the audit plan milestones M1–M7 and is tracked as Genesis
tasks.
