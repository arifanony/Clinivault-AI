"""Baseline embedding generation for Clinivault AI.

Takes validated chunk output and produces validated embedding records
that preserve the exact relationship document -> page -> chunk ->
embedding. Every record carries its chunk_id (the join key), the
document/page provenance pair, and the vector; model identity and
reproducibility parameters are recorded in the artifact header.

Out of scope (deliberately): vector storage, similarity search,
retrieval, query embedding. Production retrieval uses
``E5EmbeddingProvider`` (DECISION-017); ``generate_embeddings()`` still
defaults to the deterministic in-repo hashed bag-of-words (see
provider.py).
"""

from __future__ import annotations

from .embedder import generate_embeddings
from .errors import EmbeddingError
from .provider import (
    BaselineHashEmbeddingProvider,
    E5EmbeddingProvider,
    EmbeddingProvider,
    E5_INPUT_FORMATTING,
    E5_MODEL_NAME,
)

__all__ = [
    "generate_embeddings",
    "EmbeddingError",
    "BaselineHashEmbeddingProvider",
    "E5EmbeddingProvider",
    "EmbeddingProvider",
    "E5_INPUT_FORMATTING",
    "E5_MODEL_NAME",
]
