"""Page-level PDF text extraction (DECISION-006) with region-aware reading order.

Text is extracted through the column-aware reader
(``clinivault_ai.chunking.reader``): text regions are detected from the
page-relative line-coverage profile and read region by region, falling
back to plain top-then-x0 ordering when a page has no valid gutter. The
parsed page record keeps its exact schema -- only the text source changed.

Extraction output is recorded exactly as the parser produced it. No
cleaning, normalization, or semantic processing happens in this phase.
A failing page is captured as a page record with ``extraction_status``
``"failed"`` -- it is never silently dropped.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from clinivault_ai.chunking.reader import extract_page_text_column_aware


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
    """Extract text page by page in region-aware reading order.

    ``filename`` is recorded as given (so relative paths stay portable) and
    is part of every page's provenance alongside ``document_id`` and
    ``page_number``. The reader re-opens the PDF by path for each page (it
    owns its file lifecycle); the handle opened here supplies page
    dimensions. Per-page exceptions stay isolated (status ``"failed"``,
    never silently dropped).
    """
    records: list[dict] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            record = _page_record(document_id, filename, page_number)
            try:
                # Region-aware extraction (reader.py) re-opens the PDF by
                # path and owns its own file lifecycle; page dimensions
                # still come from the open handle this loop holds.
                extraction = extract_page_text_column_aware(str(path), page_number)
                text = extraction.get("text") or ""
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
