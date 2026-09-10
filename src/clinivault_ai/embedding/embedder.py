"""Baseline embedding generation: validated chunks -> validated embedding records.

Contract (smallest artifact consistent with repository conventions):

    {document_id,
     model: {name, dimension, ...reproducibility params},
     statistics: {...},
     embeddings: [{chunk_id, document_id, page_number, vector}, ...]}

Every record maps unambiguously to exactly one existing chunk via its
``chunk_id`` (the join key); ``document_id`` and ``page_number`` are the
cheap provenance pair matching the chunk contract. Chunk text is NOT
duplicated here -- attaching text is the vector-storage layer's concern
(project brief). Record order is exactly the input chunk order.

Generation is all-or-nothing: a provider failure, a count mismatch, a
wrong-length vector, a non-numeric value, a non-finite value, or an
all-zero vector raises EmbeddingError and produces no artifact (nothing
is silently dropped, padded, or partially written).

Batching: the provider API is batch-level (embed_texts over all chunk
texts), so ordering and chunk-to-vector mapping are preserved by
construction; no separate batching layer exists in this unit.
"""

from __future__ import annotations

import math

from clinivault_ai.embedding.errors import EmbeddingError
from clinivault_ai.embedding.provider import (
    BaselineHashEmbeddingProvider,
    EmbeddingProvider,
    params as provider_params,
)


def _validate_response(
    vectors: list, expected_count: int, dimension: int, provider_name: str
) -> None:
    """Reject malformed provider responses before any record is built."""
    if not isinstance(vectors, list):
        raise EmbeddingError(
            f"{provider_name}: response is not a list (got {type(vectors).__name__})"
        )
    if len(vectors) != expected_count:
        raise EmbeddingError(
            f"{provider_name}: response count {len(vectors)} != input count "
            f"{expected_count} -- refusing to drop or pad records"
        )
    for index, vector in enumerate(vectors):
        if not isinstance(vector, list):
            raise EmbeddingError(
                f"{provider_name}: vector {index} is not a list"
            )
        if len(vector) != dimension:
            raise EmbeddingError(
                f"{provider_name}: vector {index} has length {len(vector)}, "
                f"expected dimension {dimension}"
            )
        for value in vector:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise EmbeddingError(
                    f"{provider_name}: vector {index} contains a non-numeric "
                    f"value ({value!r})"
                )
            if not math.isfinite(value):
                raise EmbeddingError(
                    f"{provider_name}: vector {index} contains a non-finite "
                    f"value ({value!r})"
                )
        if all(float(v) == 0.0 for v in vector):
            raise EmbeddingError(
                f"{provider_name}: vector {index} is all-zero (empty signal)"
            )


def generate_embeddings(
    chunk_output: dict,
    provider: EmbeddingProvider | None = None,
) -> dict:
    """Generate one validated embedding record per chunk, in chunk order.

    ``chunk_output`` is the output of ``chunker.chunk_pages``. Returns the
    embedding artifact (plain dicts, JSON-serializable, repository
    conventions). Raises EmbeddingError on any malformed response; no
    partial artifact is ever produced.
    """
    active = provider if provider is not None else BaselineHashEmbeddingProvider()
    chunks = chunk_output.get("chunks", [])
    if not chunks:
        raise EmbeddingError("no chunks in input -- nothing to embed")

    document_id = chunk_output.get("document_id")
    if not document_id:
        raise EmbeddingError("chunk output has no document_id")

    for chunk in chunks:
        if chunk.get("document_id") != document_id:
            raise EmbeddingError(
                f"chunk {chunk.get('chunk_id')} has document_id "
                f"{chunk.get('document_id')!r}, expected {document_id!r}"
            )

    texts = [chunk.get("text") or "" for chunk in chunks]
    vectors = active.embed_texts(texts)
    _validate_response(vectors, len(chunks), active.dimension, active.name)

    records = [
        {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "page_number": chunk["page_number"],
            "vector": vector,
        }
        for chunk, vector in zip(chunks, vectors)
    ]

    pages_covered = sorted({r["page_number"] for r in records})
    return {
        "document_id": document_id,
        "model": {
            "name": active.name,
            "dimension": active.dimension,
            **provider_params(active),
        },
        "statistics": {
            "embedding_count": len(records),
            "chunk_count": len(chunks),
            "dimension": active.dimension,
            "pages_covered": pages_covered,
        },
        "embeddings": records,
    }
