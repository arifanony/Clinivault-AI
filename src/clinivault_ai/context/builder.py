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
- Every provenance field is copied verbatim -- nothing is discarded or
  reformatted. Chunk text stays per-item and intact unless the caller
  passes ``max_chars`` (M5): then the lowest-rank tail is dropped whole
  items at a time and every dropped ``chunk_id`` is reported in
  ``truncated_chunk_ids``. Items are never cut mid-text.
- Rank 1 is always kept when results are non-empty: an empty bundle
  means empty retrieval, never a budget. (Whether to answer or abstain
  belongs to the generation stage.)
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
    if "document_name" in item:
        name = item["document_name"]
        if not isinstance(name, str) or not name:
            raise ContextError(
                f"result {index} ({item['chunk_id']}) has an invalid document_name"
            )
    return item


def build_context(
    results,
    query: str | None = None,
    trace: dict | None = None,
    max_chars: int | None = None,
) -> dict:
    """Package ranked retrieval results into an inspectable evidence bundle.

    ``results`` is the best-first output of ``retrieval.search``. The
    order is preserved; rank is explicit. Raises ContextError on
    malformed input; empty results yield an explicit empty bundle.

    ``max_chars`` (M5) is an optional total budget over evidence text
    length: the best-first prefix that fits is kept and the lowest-rank
    tail is dropped whole items at a time, reported in the bundle's
    ``truncated_chunk_ids``. ``None`` (default) keeps everything and
    preserves the pre-M5 behavior exactly. Rank 1 is always kept, so a
    budget alone can never produce an empty bundle from non-empty
    results. Non-positive or non-integer budgets raise ContextError.

    If *trace* is provided (a dict), it is populated with observability
    metadata: input query, input retrieval count, constructed evidence
    (with exact text and provenance), the documents summary, evidence
    count, the budget, the truncated chunk ids, and construction
    timing. The returned bundle is unchanged, preserving backward
    compatibility with downstream callers.
    """
    import time as _time

    if not isinstance(results, (list, tuple)):
        raise ContextError("results must be a list of retrieval results")
    if max_chars is not None and (
        isinstance(max_chars, bool)
        or not isinstance(max_chars, int)
        or max_chars < 1
    ):
        raise ContextError("max_chars must be a positive integer or None")

    t_start = _time.perf_counter()

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
        document_name = validated.get("document_name")
        if isinstance(document_name, str) and document_name:
            summary.setdefault("document_name", document_name)
        entry: dict = {
            "rank": index + 1,
            "chunk_id": chunk_id,
            "document_id": document_id,
            "page_number": validated["page_number"],
            "score": validated["score"],
            "text": validated["text"],
        }
        if isinstance(document_name, str) and document_name:
            entry["document_name"] = document_name
        evidence.append(entry)

    truncated_chunk_ids = _apply_char_budget(evidence, max_chars)
    if truncated_chunk_ids:
        dropped = set(truncated_chunk_ids)
        evidence = [item for item in evidence if item["chunk_id"] not in dropped]
        for doc_id in list(documents):
            kept = [item for item in evidence if item["document_id"] == doc_id]
            if kept:
                documents[doc_id]["chunk_count"] = len(kept)
                documents[doc_id]["pages"] = {item["page_number"] for item in kept}
            else:
                del documents[doc_id]

    documents_summary = []
    for doc in documents.values():
        summary_item: dict = {
            "document_id": doc["document_id"],
            "chunk_count": doc["chunk_count"],
            "pages": sorted(doc["pages"]),
        }
        if isinstance(doc.get("document_name"), str) and doc["document_name"]:
            summary_item["document_name"] = doc["document_name"]
        documents_summary.append(summary_item)

    bundle = {
        "query": query,
        "evidence_count": len(evidence),
        "documents": documents_summary,
        "evidence": evidence,
        "truncated_chunk_ids": truncated_chunk_ids,
    }

    if trace is not None:
        trace["query"] = query
        trace["input_retrieval_count"] = len(results)
        trace["evidence_count"] = len(evidence)
        trace["documents"] = documents_summary
        trace["evidence"] = evidence
        trace["max_chars"] = max_chars
        trace["truncated_chunk_ids"] = truncated_chunk_ids
        trace["context_ms"] = (_time.perf_counter() - t_start) * 1000.0

    return bundle


def _apply_char_budget(evidence: list[dict], max_chars: int | None) -> list[str]:
    """Return the chunk ids the budget drops (best-first prefix is kept).

    ``None`` drops nothing. Rank 1 (index 0) is always kept so a budget
    alone never empties a non-empty bundle. Items are dropped whole
    from the tail; text is never cut mid-item.
    """
    if max_chars is None:
        return []
    kept_chars = 0
    cutoff = len(evidence)
    for index, item in enumerate(evidence):
        text = item.get("text")
        size = len(text) if isinstance(text, str) else 0
        if index > 0 and kept_chars + size > max_chars:
            cutoff = index
            break
        kept_chars += size
    return [item["chunk_id"] for item in evidence[cutoff:]]
