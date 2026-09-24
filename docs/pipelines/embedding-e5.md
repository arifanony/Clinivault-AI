# Pipeline: Production raw E5 retrieval embeddings

Status: **implemented** (DECISION-017 / M1). The observability UI's
T2D-001 path and `benchmark --provider e5` use this representation.
`generate_embeddings()` still defaults to the hash provider.

## 1. What problem does this pipeline solve?

Replace hashed bag-of-words query/corpus vectors in **production
retrieval** with the frozen EVAL-HF winner so live search matches the
46-case E5 scores, without overwriting hash artifacts or importing the
evaluation-only Hugging Face module.

## 2. What goes in?

- Query string (UI / `search()`).
- Committed E5 embedding JSON under
  `data/embedded-intfloat--e5-small-v2/stage-1-clean-baseline-corpus/<DOC>/`.
- Matching parsed JSON so `VectorStore.from_artifacts` can join chunk
  text.

## 3. What happens, step by step?

```
INPUT query + E5 artifact + parsed pages
  ↓
[Load] VectorStore.from_artifacts (384-d, single document_id)
  ↓
[Query encode] E5EmbeddingProvider.embed_texts([query])[0]
  — raw, no query:/passage: prefixes (search.py has no embed_query)
  — local_files_only=True; missing extra/cache → EmbeddingError
  ↓
[Retrieve] cosine Top-K=5 (DECISION-009; unchanged)
  ↓
OUTPUT ranked hits for context construction / generation
```

## 4. What comes out?

The same retrieval list contract as the hash baseline:
`[{chunk_id, document_id, page_number, score, text}, ...]` (best first).
Query vectors are 384-d. Hash vs E5 mismatch fails on dimension.

## 5. Which components are involved?

- `clinivault_ai.embedding.E5EmbeddingProvider`
- `clinivault_ai.retrieval.search` / `VectorStore` (still one document)
- `clinivault_ai.ui.app.default_paths` (T2D-001 E5 JSON)
- `clinivault_ai.evaluation.benchmark --provider e5`

Not involved: `evaluation.hf_semantic.HFEmbeddingProvider`.

## 6. Which metadata is created or preserved?

Artifact `model` records `name`, `dimension`, `input_formatting: raw`,
empty prefixes. Hash trees under `data/embedded/` are not rewritten.

## 7. What can fail?

- `sentence-transformers` not installed (`uv sync --extra semantic`).
- Local Hugging Face cache missing `intfloat/e5-small-v2`.
- Empty/whitespace query text.
- Artifact model name neither E5 nor hash (UI does not fall back).

## 8. How do we detect failure?

`EmbeddingError` with an install/cache message. Unittest live E5 tests
skip unless extra + cache are present. Hash tests never load E5.

## 9. What evidence or logs does it produce?

- Unittest: `.venv/Scripts/python -m unittest discover -s tests`
- Gate: `.venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5`
  → Hit@1 20/46, Hit@5 36/46, MRR 0.5583
- Engineering log: `docs/engineering-log/2026-09-25-e5-production-integration.md`

## 10. What consumes the output next?

Context construction and grounded generation (unchanged). Corpus-wide
indexing is not this pipeline.

## Related decisions

- [DECISION-017](../decisions/DECISION-017-production-e5-retrieval.md) —
  production representation
- [DECISION-016](../decisions/DECISION-016-retrieval-representation.md) —
  direction record
- [DECISION-009](../decisions/DECISION-009-retrieval-baseline-representation.md) —
  Top-K, cosine, fail-loud
- [DECISION-008](../decisions/DECISION-008-artifact-storage-contract.md) —
  artifact paths

## Known limitations

- Live UI still searches **T2D-001 only**.
- `generate_embeddings()` default remains hash so regenerating the
  baseline tree does not silently write E5.
- E5-intended prefixes were measured worse (EVAL-HF-003) and are not used.
