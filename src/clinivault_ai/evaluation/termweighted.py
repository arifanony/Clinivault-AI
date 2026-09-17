"""Evaluation-only term-weighted counterfactual (controlled comparison unit).

This module exists ONLY for the retrieval controlled-comparison experiment
(docs/pipelines/retrieval-controlled-comparison.md). It is NOT the
production embedding provider and is not wired into any pipeline stage.

Method (deliberately the smallest counterfactual justified by the ranking
investigation, which observed that generic function-word mass decides the
baseline ranking):

- Tokenization is IDENTICAL to the baseline: lowercase, whitespace split.
- Hashing is IDENTICAL: blake2b(digest_size=8) mod dimension (256).
- The ONLY change is per-token weighting: weight(t) = 1 + ln(N / df(t)),
  where N is the number of chunks in the document's corpus and df(t) the
  number of corpus chunks containing t (unseen tokens use df=1).
  Ubiquitous tokens (e.g. "the", "of") get weight ~1; rare informative
  tokens get larger weights. Vectors are L2-normalized.
- No stopword list, no stemming, no semantic component: one variable
  changes at a time relative to the baseline.

The document frequency table is fit on the document's chunk texts at
construction time, mirroring the per-document VectorStore layout.

Deterministic: pure float arithmetic, no randomness, no network.
Implements the existing EmbeddingProvider seam (batch-in, batch-out) so
it works with generate_embeddings() and VectorStore.from_artifacts()
unchanged.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter

from clinivault_ai.embedding.errors import EmbeddingError

DEFAULT_DIMENSION = 256

_TOKEN_SPLIT = re.compile(r"\s+")


class TermWeightedProvider:
    """IDF-weighted hashed bag-of-words (evaluation-only counterfactual)."""

    name = "clinivault-experiment-idf-hash-v1"

    def __init__(self, corpus_texts: list[str], dimension: int = DEFAULT_DIMENSION):
        if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension <= 0:
            raise ValueError(f"dimension must be a positive integer, got {dimension!r}")
        if not corpus_texts:
            raise EmbeddingError("corpus_texts must be non-empty")
        df: Counter[str] = Counter()
        for text in corpus_texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingError(
                    "corpus contains an empty or non-string text"
                )
            df.update({t for t in _TOKEN_SPLIT.split(text.lower()) if t})
        self.dimension = int(dimension)
        self._n_docs = len(corpus_texts)
        self._df = df

    def provider_params(self) -> dict:
        return {
            "method": "idf-weighted-bag-of-words",
            "idf": "1+ln(N/df)",
            "hash": "blake2b",
            "tokenizer": "whitespace-lowercase",
            "norm": "l2",
            "corpus_chunks": self._n_docs,
        }

    def _weight(self, token: str) -> float:
        return 1.0 + math.log(self._n_docs / self._df.get(token, 1))

    def _token_index(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            if not isinstance(text, str) or not text or not text.strip():
                raise EmbeddingError(
                    "cannot embed empty or whitespace-only text"
                )
            tokens = [t for t in _TOKEN_SPLIT.split(text.lower()) if t]
            counts = [0.0] * self.dimension
            for token in tokens:
                counts[self._token_index(token)] += self._weight(token)
            norm = math.sqrt(sum(c * c for c in counts))
            if norm > 0:
                counts = [c / norm for c in counts]
            vectors.append(counts)
        return vectors