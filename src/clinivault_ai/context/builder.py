"""Context construction: ranked retrieval results -> inspectable evidence bundle.

Responsibility boundary (deliberately separate from retrieval):

- Retrieval answers: "Which evidence appears relevant?"
- Context construction answers: "How is that evidence packaged and
  represented for the next stage?"

Input is the best-first list returned by ``retrieval.search`` (each item
``{chunk_id, document_id, page_number, score, text}``) plus an optional
query string. Output is one plain-dict bundle (repository conventions):

    {query,
     evidence_count,
     documents: [{document_id, chunk_count, pages}],
     evidence: [{rank, chunk_id, document_id, page_number, score, text}]}

Invariants:

- Retrieval order is preserved exactly; ``rank`` is the explicit 1-based
  position in that order.
- Every provenance field is copied verbatim -- nothing is discarded,
  reformatted, or truncated. Chunk text stays per-item and intact
  (context limits are a generation-stage concern, not packaging).
- The bundle is multi-document safe: evidence is grouped per
  ``document_id`` in the ``documents`` summary, and no code assumes a
  single document exists.
- Empty retrieval results produce an explicit empty bundle (a legitimate
  outcome; whether to answer or abstain belongs to the generation stage).
- Malformed input raises ContextError and produces no bundle.

The bundle is inspectable and self-describing: a future generation stage
receives it without needing to rediscover where any piece of evidence
came from (document -> page -> chunk -> retrieved evidence).
"""

from __future__ import annotations

from clinivault_ai.context.errors import ContextError

REQUIRED_FIELDS = ("chunk_id", "document_id", "page_number", "score", "text")


def _validate_result(item, index: int) -> dict:
    """Validate one retrieval result; fail clearly, never reinterpret."""
    if not isinstance(item, dict):
        raise ContextError(f"result {index} is not a dict")
    for field in REQUIRED_FIELDS:
        if field not in item:
            raise ContextError(f"result {index} is missing field {field!r}")
    if not isinstance(item["chunk_id"], str) or not item["chunk_id"]:
        raise ContextError(f"result {index} has an invalid chunk_id")
    if not isinstance(item["document_id"], str) or not item["document_id"]:
        raise ContextError(
            f"result {index} ({item['chunk_id']}) has an invalid document_id"
        )
    if isinstance(item["page_number"], bool) or not isinstance(item["page_number"], int):
        raise ContextError(
            f"result {index} ({item['chunk_id']}) has a non-integer page_number"
        )
    if isinstance(item["score"], bool) or not isinstance(item["score"], (int, float)):
        raise ContextError(
            f"result {index} ({item['chunk_id']}) has a non-numeric score"
        )
    if not isinstance(item["text"], str):
        raise ContextError(f"result {index} ({item['chunk_id']}) has non-string text")
    return item


def build_context(results, query: str | None = None) -> dict:
    """Package ranked retrieval results into an inspectable evidence bundle.

    ``results`` is the best-first output of ``retrieval.search``. The
    order is preserved; rank is explicit. Raises ContextError on
    malformed input; empty results yield an explicit empty bundle.
    """
    if not isinstance(results, (list, tuple)):
        raise ContextError("results must be a list of retrieval results")

    evidence = []
    seen: set[str] = set()
    documents: dict[str, dict] = {}
    for index, item in enumerate(results):
        validated = _validate_result(item, index)
        chunk_id = validated["chunk_id"]
        if chunk_id in seen:
            raise ContextError(f"duplicate chunk_id in retrieval results: {chunk_id}")
        seen.add(chunk_id)
        document_id = validated["document_id"]
        summary = documents.setdefault(
            document_id, {"document_id": document_id, "chunk_count": 0, "pages": set()}
        )
        summary["chunk_count"] += 1
        summary["pages"].add(validated["page_number"])
        evidence.append(
            {
                "rank": index + 1,
                "chunk_id": chunk_id,
                "document_id": document_id,
                "page_number": validated["page_number"],
                "score": validated["score"],
                "text": validated["text"],
            }
        )

    return {
        "query": query,
        "evidence_count": len(evidence),
        "documents": [
            {
                "document_id": doc["document_id"],
                "chunk_count": doc["chunk_count"],
                "pages": sorted(doc["pages"]),
            }
            for doc in documents.values()
        ],
        "evidence": evidence,
    }
