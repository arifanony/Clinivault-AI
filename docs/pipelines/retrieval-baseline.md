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

## Verification Performed

Recorded 2026-09-13 from the repository's actual test suite, committed
artifacts, and deterministic reproduction runs. This documents the
evidence that justified moving from baseline retrieval to context
construction. Functional verification is NOT the same claim as
retrieval-quality evaluation.

### 1. Automated Verification

- **19 focused retrieval tests** in `tests/test_retrieval.py`, covering
  these categories of functional behavior and invariants:
  - index build with exact chunk<->embedding ID join (both directions)
  - duplicate embedding/chunk IDs rejected; missing and orphaned
    embedding records rejected (no silent drops)
  - document identity mismatch rejected; empty artifacts rejected
  - malformed vectors rejected (all-zero, non-numeric, non-finite,
    wrong length); embedding/model dimension mismatch rejected
  - identical query vector ranks that chunk first with score 1.0
  - deterministic ranking; ties broken deterministically by `chunk_id`
  - exact cosine score ordering on crafted vectors (1.0 / 0.6 / 0.0)
  - top-k exactness and validation (non-int, < 1, exceeding index size)
  - empty/whitespace/non-string queries rejected; query-dimension
    mismatch rejected; provider failures propagate unchanged
  - exact result contract `{chunk_id, document_id, page_number, score,
    text}` with returned text matching the chunk artifact
- These tests verify functional behavior and invariants only. They do
  not and cannot prove real-world retrieval quality.
- Full test suite at the verification checkpoint: **86/86 passing**
  (reader 16, ingestion 9, chunking 11, embedding 19, retrieval 19,
  context 12).

### 2. Real-Artifact Verification

Reproducible verification against the committed T2D-001 artifacts
(rerun read-only on 2026-09-13):

- Document: **T2D-001**; **107 chunks**, **107 embedding records**,
  **107 indexed records**; embedding dimension **256**; provider
  `clinivault-baseline-hash-v1`.
- Three representative queries (top-3 observed):

  1. "criteria for the diagnosis of diabetes" - p14 (0.6018), p2
     (0.5851), p23 (0.5814)
  2. "classification of diabetes types" - p15 (0.5027), p4 (0.4919),
     p1 (0.4768)
  3. "gestational diabetes screening in pregnancy" - p23 (0.5940),
     p23 (0.5609), p22 (0.5377)

- Every returned result passed provenance/integrity checks: returned
  chunk text matched the source chunk artifact exactly, and `chunk_id`,
  `document_id`, and `page_number` remained consistent with it; scores
  were within [-1, 1].
- Scores were deterministic: a later read-only reproduction produced
  identical chunk IDs, page numbers, and scores.
- This is representative real-artifact verification of functional
  behavior, NOT a formal quality benchmark.

### 3. What Was Observed

- Deterministic ranking (identical results across independent runs).
- Provenance preservation end-to-end (chunk text, IDs, pages).
- Mathematically correct cosine ranking behavior (crafted-vector tests:
  identical vector -> 1.0; orthogonal -> 0.0; partial overlap -> 0.6).
- Relevant/on-topic chunks retrieved for representative queries that
  share content tokens with chunk text (e.g. "classification of diabetes
  types" -> the "Diabetes is classified conventionally..." chunk).
- The baseline behaves lexically: retrieval is token overlap, not
  semantic understanding.
- Common terms (e.g. "diabetes") can reduce score discrimination.
- Reference-heavy/token-dense chunks can sometimes outrank shorter body
  chunks.
- No claim of semantic relevance is made or supported.

### 4. What Was Not Yet Validated

- No labeled retrieval evaluation dataset exists.
- No Recall@K, MRR, or equivalent quality metrics were computed.
- Semantic retrieval quality is not proven (the current provider is a
  hashed bag-of-words baseline by design).
- Multi-document indexing at scale has not been validated.
- Large-corpus performance has not been validated.
- Hybrid retrieval / reranking alternatives have not been evaluated.

**"Functionally verified" does not mean "retrieval quality proven."**

### 5. Why We Moved Forward

Baseline retrieval was considered sufficient to proceed to Context
Construction because:

1. Functional invariants were covered by automated tests (see section 1).
2. Real committed artifacts produced deterministic,
   provenance-preserving Top-K results (see section 2).
3. Representative queries returned relevant/on-topic evidence.
4. Known limitations were identified and documented (this section and
   the Honest quality note above) rather than hidden.
5. Context Construction packages retrieval evidence and does not claim
   to improve retrieval quality.

The move to Context Construction was justified as a functional pipeline
progression. Systematic retrieval-quality evaluation remains a future
validation step (the project brief requires baseline measurements before
any retrieval improvement work).

## Out of scope

LLM generation, answers, prompts, context windows, chat UI, production
vector databases, hybrid/rerank retrieval, metadata filtering.
