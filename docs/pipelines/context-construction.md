# Pipeline: Context Construction — Baseline Evidence Bundling

Status: **implemented** (baseline; verified end-to-end on T2D-001 through
the real retrieval layer).

## What this stage does

Transforms ranked retrieval results into a clean, inspectable,
provenance-preserving evidence bundle for a future generation layer.

Responsibility boundary (deliberately separate from retrieval):

- Retrieval: "Which evidence appears relevant?"
- Context construction: "How is that evidence packaged and represented
  for the next stage?"

## Input contract

The best-first list returned by `retrieval.search` — each item
`{chunk_id, document_id, page_number, score, text}` — plus an optional
query string (the query is not part of the retrieval result contract, so
the caller records it here).

## What happens

```
ranked retrieval results
  -> per-item contract validation (fields, types, unique chunk_ids)
  -> explicit 1-based rank per evidence item
  -> per-document provenance summary
  -> evidence bundle
```

## Output contract

```
{query,
 evidence_count,
 documents: [{document_id, chunk_count, pages}],
 evidence: [{rank, chunk_id, document_id, page_number, score, text}]}
```

- Retrieval order is preserved exactly; `rank` is the explicit position.
- All provenance fields are copied verbatim; chunk text stays per item
  and intact (no concatenation, no truncation — context limits are a
  generation-stage concern, not packaging).
- Multi-document safe: the `documents` summary groups by `document_id`;
  no single-document assumptions.
- Empty retrieval results produce an explicit empty bundle (a legitimate
  outcome; whether to answer or abstain belongs to the generation stage).
- Malformed input raises `ContextError` and produces no bundle.

## Out of scope

LLM/answer generation, prompt text, model providers, context-limit or
truncation policies, reranking, abstention, pass-through of unknown
retrieval fields.
