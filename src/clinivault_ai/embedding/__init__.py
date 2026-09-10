"""Baseline embedding generation for Clinivault AI.

Takes validated chunk output and produces validated embedding records
that preserve the exact relationship document -> page -> chunk ->
embedding. Every record carries its chunk_id (the join key), the
document/page provenance pair, and the vector; model identity and
reproducibility parameters are recorded in the artifact header.

Out of scope (deliberately): vector storage, similarity search,
retrieval, query embedding. Choosing a semantic embedding model is a
future decision; the baseline provider is a deterministic in-repo
hashed bag-of-words (see provider.py).
"""

from __future__ import annotations

from .embedder import generate_embeddings
from .errors import EmbeddingError
from .provider import (
    BaselineHashEmbeddingProvider,
    EmbeddingProvider,
)

__all__ = [
    "generate_embeddings",
    "EmbeddingError",
    "BaselineHashEmbeddingProvider",
    "EmbeddingProvider",
]
