# Architecture

Status: living snapshot (2026-09-13) — written as components actually
exist. Clinivault is still evolving; this is not a final architecture.

Foundational rules live in
[DECISION-001: repository architecture](../decisions/DECISION-001-repository-architecture.md):
layered stage packages in strict data-flow order, plain-dict
JSON-serializable stage contracts, one fail-loud error type per stage,
and abstraction seams only where current requirements justify
replaceability (currently `EmbeddingProvider` is the only seam; other
components stay concrete until a demonstrated need justifies abstraction).

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
  -> retrieval/store.py       in-memory cosine index (joined by chunk_id)
  -> retrieval/search.py      query embedding + deterministic top-k
  -> context/builder.py       inspectable evidence bundle
```

Stage contracts (all plain dicts, JSON-serializable):

| Stage | Input | Output |
|---|---|---|
| ingestion | verified PDF | `{provenance, pages:[{document_id, filename, page_number, text, text_sha256, char_count, word_count, page_width, page_height, extraction_status, extraction_error}]}` |
| chunking | parsed document | `{document_id, config, statistics, chunks:[{chunk_id, document_id, page_number, chunk_index, text}]}` |
| embedding | chunk output | `{document_id, model, statistics, embeddings:[{chunk_id, document_id, page_number, vector}]}` |
| retrieval | chunk output + embedding artifact | `[{chunk_id, document_id, page_number, score, text}]` (best first) |
| context | retrieval results (+ optional query) | `{query, evidence_count, documents, evidence:[{rank, chunk_id, document_id, page_number, score, text}]}` |

Provenance survives every boundary: document -> page -> chunk ->
embedding -> retrieval result -> evidence bundle. Each stage re-validates
its input and raises its own error type instead of dropping records.

Detailed stage behavior lives in the pipeline docs
([pipelines/](../pipelines/README.md)); the engineering log records the
problems that shaped this architecture (reader.py reading-order work).

## Deliberately replaceable

- Embedding model (via the `EmbeddingProvider` seam; the current
  `clinivault-baseline-hash-v1` is a deterministic contract baseline, NOT
  a semantic model — model choice is still an undecided decision).

## Deliberately concrete (for now, per DECISION-001's seam principle)

- PDF parsing wrapper (pdfplumber per DECISION-006).
- Vector store (in-memory index over the embedding artifact).
- Context builder (packaging logic over retrieval results).
- No generation/LLM abstraction exists yet — generation is not built.

## The two-products rule

Clinivault is a standalone clinical evidence product; Errata is a
separate, reusable AI evaluation product that lives in its own
repository. Clinivault preserves the structured evidence, provenance, and
execution records that would let Errata evaluate this pipeline later
through a shared contract — but integration is not a current MVP goal,
and no Errata logic lives here.

## Not yet built

Generation (LLM/provider, prompts, answers), abstention, retrieval
evaluation, multi-document corpus ingestion (pipeline supports the
contracts; only T2D-001 is ingested), persistence beyond artifacts,
deployment/infrastructure.
