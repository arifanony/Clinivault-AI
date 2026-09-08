"""Page-level PDF text extraction via pdfplumber (DECISION-006).

Extraction output is recorded exactly as the parser produced it. No
cleaning, normalization, or semantic processing happens in this phase.
A failing page is captured as a page record with ``extraction_status``
``"failed"`` — it is never silently dropped.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber


def _page_record(document_id: str, filename: str, page_number: int) -> dict:
    """A page record skeleton that always carries full provenance."""
    return {
        "document_id": document_id,
        "filename": filename,
        "page_number": page_number,
        "text": "",
        "text_sha256": None,
        "char_count": 0,
        "word_count": 0,
        "page_width": None,
        "page_height": None,
        "extraction_status": "failed",
        "extraction_error": None,
    }


def parse_pages(path: str | Path, document_id: str, filename: str) -> list[dict]:
    """Extract text page by page.

    ``filename`` is recorded as given (so relative paths stay portable) and
    is part of every page's provenance alongside ``document_id`` and
    ``page_number``.
    """
    records: list[dict] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            record = _page_record(document_id, filename, page_number)
            try:
                text = page.extract_text() or ""
                record.update(
                    text=text,
                    text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    char_count=len(text),
                    word_count=len(text.split()),
                    page_width=float(page.width),
                    page_height=float(page.height),
                    extraction_status="ok" if text.strip() else "empty",
                )
            except Exception as exc:  # noqa: BLE001 - per-page isolation
                record["extraction_error"] = f"{type(exc).__name__}: {exc}"
            records.append(record)
    return records
