"""Baseline vector store: committed artifacts -> joined, validated index.

Storage choice (smallest correct solution for this project stage):

- Nothing new is stored. The committed embedding artifact IS the vector
  storage; the index is an in-memory view over it, joined to chunk text
  through ``chunk_id``.
- No production vector database: the decisions index lists vector
  storage as undecided, the repository has no vector dependency, and the
  project brief prescribes a simple, reliable baseline first.

The index re-validates everything on build (it must never trust an
artifact it did not create): document identity, vector dimensions,
numeric/finite/non-zero values, duplicate chunk IDs, and exact
chunk<->embedding ID agreement in BOTH directions. Any mismatch raises
RetrievalError -- records are never silently dropped.

A store holds one document (``from_artifacts``) or one merged corpus
index (``from_corpus``). Every record carries its own ``document_id``;
a corpus store carries ``document_id=None`` itself because no single
document owns the index.
"""

from __future__ import annotations

import math

from clinivault_ai.retrieval.errors import RetrievalError


def _validate_vector(vector, dimension: int, label: str) -> list[float]:
    """Shared strict vector validation for stored records and queries."""
    if not isinstance(vector, list):
        raise RetrievalError(f"{label}: vector is not a list")
    if len(vector) != dimension:
        raise RetrievalError(
            f"{label}: vector length {len(vector)} != index dimension {dimension}"
        )
    for value in vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RetrievalError(f"{label}: non-numeric vector value ({value!r})")
        if not math.isfinite(value):
            raise RetrievalError(f"{label}: non-finite vector value ({value!r})")
    if all(float(v) == 0.0 for v in vector):
        raise RetrievalError(f"{label}: all-zero vector (no signal)")
    return [float(v) for v in vector]


class VectorStore:
    """In-memory cosine index over validated chunk embeddings + chunk text."""

    def __init__(
        self, document_id: str | None, dimension: int, records: list[dict]
    ):
        self.document_id = document_id
        self.dimension = dimension
        # records: chunk_id, document_id, page_number, text, vector (floats), norm
        self.records = records

    @classmethod
    def from_artifacts(
        cls, embedding_artifact: dict, chunk_output: dict
    ) -> "VectorStore":
        """Build the index from chunker output + its embedding artifact."""
        emb_records = embedding_artifact.get("embeddings", [])
        chunks = chunk_output.get("chunks", [])
        if not emb_records:
            raise RetrievalError("embedding artifact contains no records")
        if not chunks:
            raise RetrievalError("chunk output contains no chunks")

        emb_doc = embedding_artifact.get("document_id")
        chunk_doc = chunk_output.get("document_id")
        if not emb_doc or not chunk_doc:
            raise RetrievalError("artifacts must both carry a document_id")
        if emb_doc != chunk_doc:
            raise RetrievalError(
                f"document_id mismatch: embeddings {emb_doc!r} vs chunks {chunk_doc!r}"
            )

        dimension = (embedding_artifact.get("model") or {}).get("dimension")
        if not isinstance(dimension, int) or dimension <= 0:
            raise RetrievalError(
                f"embedding artifact has invalid model dimension: {dimension!r}"
            )

        seen: set[str] = set()
        validated: list[dict] = []
        for record in emb_records:
            chunk_id = record.get("chunk_id")
            if not chunk_id:
                raise RetrievalError("embedding record without chunk_id")
            if chunk_id in seen:
                raise RetrievalError(f"duplicate chunk_id in embeddings: {chunk_id}")
            seen.add(chunk_id)
            vector = _validate_vector(
                record.get("vector"), dimension, f"embedding {chunk_id}"
            )
            validated.append({"chunk_id": chunk_id, "vector": vector})
        emb_by_id = {v["chunk_id"]: v["vector"] for v in validated}

        seen_chunks: set[str] = set()
        records: list[dict] = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                raise RetrievalError("chunk record without chunk_id")
            if chunk_id in seen_chunks:
                raise RetrievalError(f"duplicate chunk_id in chunks: {chunk_id}")
            seen_chunks.add(chunk_id)
            if chunk_id not in emb_by_id:
                raise RetrievalError(
                    f"chunk {chunk_id} has no embedding record (no silent drops)"
                )
            if chunk.get("document_id") != emb_doc:
                raise RetrievalError(
                    f"chunk {chunk_id} document_id mismatch with index"
                )
            vector = emb_by_id[chunk_id]
            norm = math.sqrt(sum(v * v for v in vector))
            records.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": emb_doc,
                    "page_number": chunk["page_number"],
                    "text": chunk.get("text") or "",
                    "vector": vector,
                    "norm": norm,
                }
            )

        missing = sorted(seen - seen_chunks)
        if missing:
            raise RetrievalError(
                f"embedding record(s) without a chunk: {missing} (no silent drops)"
            )

        return cls(document_id=emb_doc, dimension=dimension, records=records)

    @classmethod
    def from_corpus(
        cls, pairs: list[tuple[dict, dict]]
    ) -> "VectorStore":
        """Build one merged index from (embedding_artifact, chunk_output) pairs.

        Each pair is validated exactly as in ``from_artifacts``; the merged
        index additionally requires one shared embedding dimension and
        globally unique ``chunk_id`` values. The store itself carries
        ``document_id=None``; per-result provenance comes from each record's
        own ``document_id`` (see ``search()``).
        """
        if not pairs:
            raise RetrievalError(
                "corpus contains no (embedding_artifact, chunk_output) pairs"
            )
        for index, pair in enumerate(pairs):
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                raise RetrievalError(
                    f"corpus pair #{index} must be "
                    "(embedding_artifact, chunk_output)"
                )
        singles = [cls.from_artifacts(emb, chk) for emb, chk in pairs]

        dimension = singles[0].dimension
        for single in singles[1:]:
            if single.dimension != dimension:
                raise RetrievalError(
                    f"corpus dimension mismatch: {single.document_id!r} has "
                    f"dimension {single.dimension} != index dimension {dimension}"
                )

        seen: set[str] = set()
        records: list[dict] = []
        for single in singles:
            for record in single.records:
                if record["chunk_id"] in seen:
                    raise RetrievalError(
                        f"duplicate chunk_id across corpus: {record['chunk_id']}"
                    )
                seen.add(record["chunk_id"])
                records.append(record)

        return cls(document_id=None, dimension=dimension, records=records)

    def __len__(self) -> int:
        return len(self.records)
