# Pipeline: Retrieval — Baseline Vector Storage and Similarity Search

Status: **implemented** (baseline; verified end-to-end on T2D-001 with the
in-repo baseline provider).

## What this stage does

```
validated chunks + validated embeddings
  -> in-memory cosine index (joined by chunk_id, re-validated on build)
  -> query text
  -> query embedding via the existing EmbeddingProvider seam
  -> deterministic top-k results with full provenance
```

## Input contract

- The output of `chunker.chunk_pages` (chunk text + provenance).
- The embedding artifact from the embedding stage
  (`data/embedded/...`, `chunk_id`-keyed records).

## Storage

Nothing new is stored: the committed embedding artifact IS the vector
storage; the index (`retrieval/store.py`) is an in-memory view joined to
chunk text through `chunk_id`. No production vector database: vector
storage is an undecided decision, the repository has no vector
dependency, and the project brief prescribes a simple reliable baseline
first. The index re-validates everything on build (document identity,
dimensions, numeric/finite/non-zero vectors, duplicate IDs, exact
chunk<->embedding agreement in BOTH directions) and raises
`RetrievalError` on any mismatch -- records are never silently dropped.

## Output contract

Per result: `{chunk_id, document_id, page_number, score, text}` — best
first. `text` is the exact chunk text joined via `chunk_id`; the score
is cosine similarity.

## Similarity metric

**Cosine.** The baseline provider emits L2-normalized vectors, where
cosine equals the dot product; cosine is used anyway so the metric stays
correct for any non-zero provider vectors. Ranking is `(-score,
chunk_id)` — deterministic ties. Brute force, deliberately, at this
scale. `top_k` is explicit: values < 1 or exceeding the index size raise
`RetrievalError` (no silent clamping).

## Query embedding

Reuses the existing `EmbeddingProvider` seam — no second embedding
implementation; query vectors are re-validated against the index
dimension; provider errors propagate unchanged.

## Honest quality note

The current provider (`clinivault-baseline-hash-v1`) is a hashed
bag-of-words: retrieval is lexical-token overlap, NOT semantic. Verified
behavior on T2D-001: queries sharing content tokens with chunk text
(e.g. "classification of diabetes types" -> the "Diabetes is classified
conventionally..." chunk) retrieve on-topic chunks; generic tokens
("diabetes") dominate scores everywhere; reference-heavy and token-dense
chunks can outrank short body chunks. Semantic quality requires a real
embedding model — a future decision, unchanged in this unit.

## Out of scope

LLM generation, answers, prompts, context windows, chat UI, production
vector databases, hybrid/rerank retrieval, metadata filtering.
