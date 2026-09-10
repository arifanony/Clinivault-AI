# Pipeline: Embedding — Baseline Embedding Generation

Status: **implemented** (baseline; verified end-to-end on T2D-001 with the
in-repo baseline provider).

## What this stage does

Transform validated chunks into validated embedding records while
preserving the exact relationship:

```
document -> page -> chunk -> embedding
```

## Input contract

The output of `chunker.chunk_pages` (`{document_id, config, statistics,
chunks}`), where every chunk carries `chunk_id`, `document_id`,
`page_number`, `text`.

## What happens

```
validated chunks
  -> embedding input preparation (texts in chunk order)
  -> embedding provider (batch-level, order-preserving seam)
  -> response validation (count, dimension, numeric, finite, non-zero)
  -> embedding artifact with model provenance
```

## Output contract

`{document_id, model: {name, dimension, ...reproducibility params},
statistics, embeddings: [{chunk_id, document_id, page_number, vector}]}`

- `chunk_id` is the join key: every record maps to exactly one chunk.
- Chunk text is NOT duplicated here (attaching text is the vector-storage
  layer's concern).
- Generation is all-or-nothing: any malformed response raises and no
  artifact is produced (nothing dropped, padded, or partially written).

## Provider boundary

`embedding/provider.py` defines the only seam (`EmbeddingProvider`:
name + dimension + `embed_texts(texts) -> vectors`). The baseline
provider (`clinivault-baseline-hash-v1`) is a deterministic in-repo
hashed bag-of-words (blake2b, whitespace-lowercase tokens, L2-normalized,
256 dims): no network, no API cost, no dependencies. It is NOT semantic —
it establishes and tests the contract. Choosing a real embedding model
is a future decision (explicitly not made in this unit); DECISION-003
forbids recurring API costs during MVP development.

## Verified on T2D-001

107 chunks in -> 107 embeddings out; IDs identical and in order; 0
duplicates; all vectors 256-dim and L2 norm 1.0; deterministic across
runs; artifact JSON reload-equivalent
(`data/embedded/stage-1-clean-baseline-corpus/T2D-001/`).

## Out of scope

Vector database, similarity search, retrieval, query embedding, semantic
model selection, batching optimization (the provider seam is
batch-level; a real provider may add batching behind it later).
