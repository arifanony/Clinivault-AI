"""Citation reference parsing and validation for Clinivault AI (M5).

Pure functions: answer text + evidence list -> parsed refs and the
invalid ones. No provider, no retrieval, no network.

The prompt stamps each evidence item with stable identifiers
(``EVIDENCE_ITEM_RANK: <n>`` and ``EVIDENCE_ITEM_CHUNK_ID: <id>``), so a
grounded answer can cite them. These helpers recover those references
from free-form answer text and check them against the evidence bundle
that was actually supplied:

- a rank ref is valid exactly when ``1 <= rank <= len(evidence)``
- a chunk-id ref is valid exactly when it equals the ``chunk_id`` of
  one evidence item

Anything else is returned as ``{"kind": "rank" | "chunk_id",
"value": ...}`` so callers (and the labeled M5 set) can measure
citation validity. Duplicated refs are reported once, in order of
first appearance.
"""

from __future__ import annotations

import re
from typing import Any

_RANK_PATTERN = r"EVIDENCE_ITEM_RANK\s*:\s*(\d+)"
_CHUNK_PATTERN = r"EVIDENCE_ITEM_CHUNK_ID\s*:\s*([\w][\w\-]*)"
_REF_PATTERN = re.compile(
    rf"(?:{_RANK_PATTERN})|(?:{_CHUNK_PATTERN})"
)


def parse_citation_refs(answer: str) -> dict[str, list]:
    """Extract cited ranks and chunk ids from answer text, in order.

    Returns ``{"ranks": [int, ...], "chunk_ids": [str, ...]}`` with
    duplicates removed (first appearance wins). Non-string input
    yields empty lists; it never raises.
    """
    ranks: list[int] = []
    chunk_ids: list[str] = []
    if not isinstance(answer, str):
        return {"ranks": ranks, "chunk_ids": chunk_ids}
    for match in _REF_PATTERN.finditer(answer):
        rank, chunk_id = match.group(1), match.group(2)
        if rank is not None:
            value = int(rank)
            if value not in ranks:
                ranks.append(value)
        elif chunk_id is not None and chunk_id not in chunk_ids:
            chunk_ids.append(chunk_id)
    return {"ranks": ranks, "chunk_ids": chunk_ids}


def validate_citation_refs(
    refs: dict[str, list], evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return the invalid refs: ``[{"kind", "value"}, ...]``.

    Malformed ``refs``/``evidence`` shapes are treated as "nothing to
    check" and yield ``[]``; malformed evidence items are the context
    stage's contract to reject, not this module's.
    """
    if not isinstance(refs, dict) or not isinstance(evidence, list):
        return []
    known_chunks = {
        item["chunk_id"]
        for item in evidence
        if isinstance(item, dict) and isinstance(item.get("chunk_id"), str)
    }
    invalid: list[dict[str, Any]] = []
    ranks = refs.get("ranks")
    if isinstance(ranks, list):
        for rank in ranks:
            if (
                isinstance(rank, bool)
                or not isinstance(rank, int)
                or not 1 <= rank <= len(evidence)
            ):
                invalid.append({"kind": "rank", "value": rank})
    chunk_ids = refs.get("chunk_ids")
    if isinstance(chunk_ids, list):
        for chunk_id in chunk_ids:
            if chunk_id not in known_chunks:
                invalid.append({"kind": "chunk_id", "value": chunk_id})
    return invalid


def check_citations(
    answer: str, evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Parse *answer* and return its invalid citation refs (``[]`` if clean)."""
    return validate_citation_refs(parse_citation_refs(answer), evidence)
