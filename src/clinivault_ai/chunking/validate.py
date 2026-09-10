"""Mechanical chunk validation (repository contract: imported by __init__).

This module exists because ``clinivault_ai.chunking.__init__`` imports
``validate_chunks`` -- the package API cannot import without it. It is a
MINIMAL mechanical checker of the chunk contract itself (IDs, provenance
fields, ordering, non-empty text, size bound). It does not judge chunk
quality and is not the full ingestion-style validation framework.
"""

from __future__ import annotations

import re

_CHUNK_ID_PATTERN = re.compile(r"^(?P<doc>.+)-p(?P<page>\d{3})-c(?P<index>\d{3})$")

REQUIRED_FIELDS = ("chunk_id", "document_id", "page_number", "chunk_index", "text")


def validate_chunks(output: dict, max_chars: int | None = None) -> dict:
    """Mechanically validate the output of ``chunker.chunk_pages``.

    Returns ``{"checks": [...], "overall_status": "pass"|"fail"}`` in the
    same check-record style as the ingestion validation report.
    """
    chunks = output.get("chunks", [])
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append(
            {
                "name": name,
                "status": "pass" if ok else "fail",
                "detail": detail,
            }
        )

    record("chunks_present", bool(chunks), f"{len(chunks)} chunks in output")

    fields_ok = all(
        isinstance(c, dict) and all(f in c for f in REQUIRED_FIELDS) for c in chunks
    )
    record(
        "required_fields_present",
        fields_ok,
        f"every chunk carries {', '.join(REQUIRED_FIELDS)}",
    )

    id_ok = True
    for c in chunks:
        m = _CHUNK_ID_PATTERN.match(c.get("chunk_id", "") or "")
        if (
            not m
            or m.group("doc") != str(c.get("document_id"))
            or int(m.group("page")) != c.get("page_number")
            or int(m.group("index")) != c.get("chunk_index")
        ):
            id_ok = False
            break
    record(
        "chunk_id_matches_provenance",
        id_ok,
        "chunk_id == {document_id}-p{page:03d}-c{index:03d} of its own fields",
    )

    ids = [c.get("chunk_id") for c in chunks if isinstance(c, dict)]
    record(
        "chunk_ids_unique",
        len(ids) == len(set(ids)),
        "no chunk_id appears twice",
    )

    order_ok = True
    seen_pages: dict[int, int] = {}
    for c in chunks:
        page = c.get("page_number")
        index = c.get("chunk_index")
        expected = seen_pages.get(page, 0) + 1
        if index != expected:
            order_ok = False
            break
        seen_pages[page] = expected
    record(
        "chunk_index_contiguous_per_page",
        order_ok,
        "chunk_index is 1..n in output order on every page",
    )

    empty = [
        c.get("chunk_id") for c in chunks if not str(c.get("text", "") or "").strip()
    ]
    record("no_empty_chunks", not empty, f"empty chunks: {empty or 'none'}")

    if max_chars is not None:
        oversized = [
            c.get("chunk_id")
            for c in chunks
            if len(str(c.get("text", "") or "")) > max_chars
        ]
        record(
            "size_within_max",
            not oversized,
            f"chunks over {max_chars} chars: {oversized or 'none'}",
        )

    overall = "pass" if all(c["status"] == "pass" for c in checks) else "fail"
    return {"checks": checks, "overall_status": overall}
