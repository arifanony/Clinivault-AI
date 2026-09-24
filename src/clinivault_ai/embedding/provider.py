"""Embedding provider boundary (smallest seam required by the repository).

The project brief requires the embedding model to be replaceable without
rewriting the system, and DECISION-003 forbids recurring API costs during
MVP development. This module therefore defines one small protocol plus the
deterministic, dependency-free baseline provider:

- ``EmbeddingProvider``: anything that turns a list of texts into a list
  of equal-length numeric vectors, in input order, and reports its model
  identity. This is the whole seam -- no plugin framework.
- ``BaselineHashEmbeddingProvider``: hashed bag-of-words via
  ``hashlib.blake2b`` (stable across runs and processes, unlike builtin
  ``hash()``), L2-normalized. NOT semantic: it exists to establish and
  test the contract end-to-end with zero dependencies, zero network, and
  zero cost. DECISION-017 selects raw ``intfloat/e5-small-v2`` as the
  production retrieval representation; this hash provider remains the
  default of ``generate_embeddings()`` and the comparison baseline.

DECISION-017 implements that production choice behind this seam.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from clinivault_ai.embedding.errors import EmbeddingError

DEFAULT_BASELINE_DIMENSION = 256
E5_MODEL_NAME = "intfloat/e5-small-v2"
E5_EXPECTED_DIMENSION = 384
E5_INPUT_FORMATTING = "raw"

_TOKEN_SPLIT = re.compile(r"\s+")


class EmbeddingProvider(Protocol):
    """The provider seam: batch-in, batch-out, order-preserving."""

    name: str
    dimension: int

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed texts in order. Raises EmbeddingError on bad input."""
        ...  # pragma: no cover - protocol


def params(provider: EmbeddingProvider) -> dict:
    """Reproducibility parameters of a provider (recorded in the artifact)."""
    extra = getattr(provider, "provider_params", None)
    return dict(extra()) if callable(extra) else {}


class BaselineHashEmbeddingProvider:
    """Deterministic hashed bag-of-words baseline (see module docstring)."""

    name = "clinivault-baseline-hash-v1"

    def __init__(self, dimension: int = DEFAULT_BASELINE_DIMENSION):
        if dimension <= 0:
            raise ValueError("dimension must be a positive integer")
        self.dimension = int(dimension)

    def provider_params(self) -> dict:
        return {
            "method": "hashed-bag-of-words",
            "hash": "blake2b",
            "tokenizer": "whitespace-lowercase",
            "norm": "l2",
        }

    def _token_index(self, token: str) -> int:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        return int.from_bytes(digest, "big") % self.dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            if not text or not text.strip():
                raise EmbeddingError(
                    "cannot embed empty or whitespace-only text"
                )
            tokens = [t for t in _TOKEN_SPLIT.split(text.lower()) if t]
            counts = [0.0] * self.dimension
            for token in tokens:
                counts[self._token_index(token)] += 1.0
            norm = math.sqrt(sum(c * c for c in counts))
            if norm > 0:
                counts = [c / norm for c in counts]
            vectors.append(counts)
        return vectors


class E5EmbeddingProvider:
    """Production local dense provider: raw ``intfloat/e5-small-v2``.

    Retrieval embeds queries with ``embed_texts([query])[0]`` (search.py),
    so corpus and query paths must stay unprefixed (DECISION-016/017).
    """

    name = E5_MODEL_NAME

    def __init__(self, *, device: str = "cpu", local_files_only: bool = True):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers is not installed; "
                "run `uv sync --extra semantic`"
            ) from exc
        try:
            self.model = SentenceTransformer(
                E5_MODEL_NAME,
                device=device,
                trust_remote_code=True,
                local_files_only=local_files_only,
            )
        except Exception as exc:
            raise EmbeddingError(
                f"could not load local model {E5_MODEL_NAME!r} "
                f"(local_files_only={local_files_only}): {exc}"
            ) from exc
        self.device = device
        dim_fn = getattr(
            self.model, "get_embedding_dimension",
            self.model.get_sentence_embedding_dimension,
        )
        self.dimension = int(dim_fn())
        if self.dimension != E5_EXPECTED_DIMENSION:
            raise EmbeddingError(
                f"{E5_MODEL_NAME} dimension {self.dimension} != "
                f"{E5_EXPECTED_DIMENSION}"
            )

    def provider_params(self) -> dict:
        return {
            "method": "hf-sentence-transformers",
            "model": E5_MODEL_NAME,
            "device": self.device,
            "dimension": self.dimension,
            "external": False,
            "input_formatting": E5_INPUT_FORMATTING,
            "query_prefix": "",
            "passage_prefix": "",
        }

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingError("cannot embed empty or whitespace-only text")
        import torch

        with torch.no_grad():
            embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [[float(v) for v in row] for row in embeddings]
