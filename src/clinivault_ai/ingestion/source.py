"""PDF source verification: existence, checksum, open check, page count.

This module answers one question: *is this file the PDF we think it is?*
It never parses text and never modifies the file.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from .errors import IngestionError

_CHUNK_SIZE = 1024 * 1024


def compute_sha256(path: Path) -> str:
    """Stream the file and return its uppercase SHA-256 hex digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest().upper()


@dataclass(frozen=True)
class SourceInfo:
    """Verified facts about the raw PDF. The raw file is never modified."""

    path: Path
    sha256: str
    page_count: int
    encrypted: bool
    metadata: dict[str, str | None] = field(default_factory=dict)


def _read_metadata(reader: PdfReader) -> dict[str, str | None]:
    """Best-effort raw PDF metadata; recorded, never trusted."""
    keys = ("title", "author", "subject", "creator", "producer",
            "creation_date_raw", "mod_date_raw")
    try:
        info = reader.metadata
    except Exception:  # noqa: BLE001 - metadata problems must not kill ingestion
        info = None
    if info is None:
        return {key: None for key in keys}
    # Attribute names vary across pypdf versions; read defensively.
    values: dict[str, str | None] = {}
    for key in keys:
        try:
            value = getattr(info, key, None)
            values[key] = str(value) if value is not None else None
        except Exception:  # noqa: BLE001 - one bad field must not kill ingestion
            values[key] = None
    return values


def verify_source(
    path: str | Path,
    expected_sha256: str,
    expected_pages: int,
) -> SourceInfo:
    """Verify the raw PDF against the corpus manifest's recorded facts.

    Raises IngestionError when the file is missing, the checksum does not
    match, the PDF cannot be opened, or the page count differs.
    """
    pdf_path = Path(path)
    if not pdf_path.is_file():
        raise IngestionError(f"source PDF not found: {pdf_path}")

    sha256 = compute_sha256(pdf_path)
    if sha256 != expected_sha256.upper():
        raise IngestionError(
            "source SHA-256 mismatch: "
            f"expected {expected_sha256.upper()}, found {sha256} for {pdf_path}"
        )

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - any pypdf failure means "cannot open"
        raise IngestionError(f"could not open PDF {pdf_path}: {exc}") from exc

    encrypted = bool(reader.is_encrypted)
    if encrypted:
        raise IngestionError(f"PDF is encrypted; ingestion refused: {pdf_path}")

    try:
        page_count = len(reader.pages)
    except Exception as exc:  # noqa: BLE001
        raise IngestionError(f"could not read page count of {pdf_path}: {exc}") from exc

    if page_count != expected_pages:
        raise IngestionError(
            f"page count mismatch for {pdf_path}: "
            f"expected {expected_pages}, found {page_count}"
        )

    return SourceInfo(
        path=pdf_path,
        sha256=sha256,
        page_count=page_count,
        encrypted=encrypted,
        metadata=_read_metadata(reader),
    )
