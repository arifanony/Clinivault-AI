"""Baseline structural chunking of parsed page data (first working layer).

This is deliberately the SIMPLEST chunker that establishes a correct,
testable contract -- it is not the final production chunking strategy.

Input: the parsed document produced by the ingestion pipeline
(``{provenance, pages}``, as serialized in ``<DOC-ID>.parsed.json``).
Output: one chunk list per document, where every chunk is traceable to
``(document_id, page_number)`` back to the raw PDF via the corpus manifest.

Baseline behavior (all deterministic, no ML, no external dependencies):

- Chunks never span pages: provenance is exact, and text from different
  pages is never mixed inside one chunk.
- Natural boundaries are preferred: page text is split into paragraph
  pieces on blank lines; consecutive pieces are accumulated up to
  ``target_chars``.
- No word is ever split: a piece longer than ``max_chars`` is divided on
  sentence boundaries first, then -- only as a last resort -- on whitespace.
- Tiny trailing fragments are merged into the previous chunk on the same
  page when the result still fits within ``max_chars``.

Chunk IDs are deterministic and unique:
``{document_id}-p{page:03d}-c{chunk_index:03d}`` with ``chunk_index``
starting at 1 on every page (repository convention, see the
``clinivault_ai.chunking`` docstring).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

DEFAULT_TARGET_CHARS = 1200
"""Accumulated chunk size (characters) the chunker aims for. Not tuned --
a baseline value only; measured evidence must drive any future change."""

DEFAULT_MAX_CHARS = 1800
"""Hard upper bound (characters) for a single chunk."""

DEFAULT_MIN_CHARS = 200
"""Chunks shorter than this are merged into the previous chunk on the same
page when the merge stays within ``max_chars`` (avoids tiny fragments)."""

_BLANK_LINE_SPLIT = re.compile(r"\n[ \t]*\n+")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class ChunkConfig:
    """Parameters of the baseline chunker (recorded in the output)."""

    target_chars: int = DEFAULT_TARGET_CHARS
    max_chars: int = DEFAULT_MAX_CHARS
    min_chars: int = DEFAULT_MIN_CHARS


def default_config() -> ChunkConfig:
    """The baseline configuration, as a distinct object per call."""
    return ChunkConfig()


@dataclass(frozen=True)
class ChunkOutput:
    """One retrievable evidence unit with full provenance.

    ``chunk_id`` is deterministic:
    ``{document_id}-p{page:03d}-c{chunk_index:03d}``.
    """

    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    text: str

    def to_dict(self) -> dict:
        return asdict(self)


def make_chunk_id(document_id: str, page_number: int, chunk_index: int) -> str:
    """Single source of truth for the deterministic chunk ID format."""
    return f"{document_id}-p{page_number:03d}-c{chunk_index:03d}"


def _split_paragraphs(text: str) -> list[str]:
    """Split page text into paragraph pieces on blank lines.

    Whitespace-only pieces are dropped (they carry no content); all other
    pieces are passed through verbatim -- the chunker never rewrites text.
    """
    return [p for p in _BLANK_LINE_SPLIT.split(text) if p.strip()]


def _hard_split_at_whitespace(piece: str, max_chars: int) -> list[str]:
    """Last-resort split of one oversized piece at whitespace boundaries.

    Never splits inside a word; output pieces are each <= max_chars
    (a single word longer than max_chars is emitted alone, intact).
    """
    pieces: list[str] = []
    current = ""
    for token in piece.split(" "):
        candidate = token if not current else current + " " + token
        if current and len(candidate) > max_chars:
            pieces.append(current)
            current = token
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def _split_oversized(piece: str, max_chars: int) -> list[str]:
    """Split a piece longer than max_chars: sentences first, then words."""
    if len(piece) <= max_chars:
        return [piece]
    sentences = [s for s in _SENTENCE_SPLIT.split(piece) if s.strip()]
    if len(sentences) <= 1:
        return _hard_split_at_whitespace(piece, max_chars)
    # Group whole sentences into pieces that each fit within max_chars.
    grouped: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = sentence if not current else current + " " + sentence
        if current and len(candidate) > max_chars:
            grouped.append(current)
            current = sentence
        else:
            current = candidate
    if current:
        grouped.append(current)
    # A group can still exceed max_chars only if one sentence does.
    final: list[str] = []
    for group in grouped:
        final.extend(_split_oversized(group, max_chars))
    return final


def _group_pieces(pieces: list[str], config: ChunkConfig) -> list[str]:
    """Accumulate pieces into chunks: aim for target, never exceed max."""
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    def flush() -> None:
        nonlocal buffer, buffer_len
        if buffer:
            chunks.append("\n\n".join(buffer))
            buffer = []
            buffer_len = 0

    for piece in pieces:
        if buffer and buffer_len + len(piece) + 2 > config.target_chars:
            flush()
        buffer.append(piece)
        buffer_len += len(piece) + 2
    flush()

    # Merge a tiny trailing fragment into the previous chunk when the
    # result still fits within max_chars.
    if len(chunks) >= 2:
        last = chunks[-1]
        if len(last) < config.min_chars:
            merged = chunks[-2] + "\n\n" + last
            if len(merged) <= config.max_chars:
                chunks = chunks[:-2] + [merged]
    return chunks


def chunk_page_text(
    text: str, page_number: int, document_id: str, config: ChunkConfig
) -> list[ChunkOutput]:
    """Chunk the text of ONE page. Deterministic; chunks never span pages."""
    pieces: list[str] = []
    for paragraph in _split_paragraphs(text):
        pieces.extend(_split_oversized(paragraph, config.max_chars))
    texts = _group_pieces(pieces, config)
    return [
        ChunkOutput(
            chunk_id=make_chunk_id(document_id, page_number, index),
            document_id=document_id,
            page_number=page_number,
            chunk_index=index,
            text=chunk_text,
        )
        for index, chunk_text in enumerate(texts, start=1)
    ]


def chunk_pages(document: dict, config: ChunkConfig | None = None) -> dict:
    """Baseline chunking of a parsed document (``{provenance, pages}``).

    Returns ``{document_id, config, statistics, chunks}`` where ``chunks``
    is a list of plain dicts (JSON-serializable, ingestion conventions).
    Pages with status ``failed`` or with no text yield no chunks and are
    recorded in ``statistics.pages_without_chunks`` -- nothing disappears
    silently.
    """
    cfg = config or default_config()
    pages = document.get("pages", [])
    document_id = (document.get("provenance") or {}).get("document_id") or (
        pages[0].get("document_id") if pages else None
    )
    if not document_id:
        raise ValueError("document has no document_id (provenance or pages)")

    chunks: list[ChunkOutput] = []
    pages_with_chunks: list[int] = []
    pages_without_chunks: list[dict] = []
    for page in sorted(pages, key=lambda p: p["page_number"]):
        status = page.get("extraction_status")
        text = page.get("text") or ""
        if status == "failed":
            pages_without_chunks.append(
                {"page_number": page["page_number"], "reason": "failed"}
            )
            continue
        if not text.strip():
            pages_without_chunks.append(
                {"page_number": page["page_number"], "reason": "empty"}
            )
            continue
        page_chunks = chunk_page_text(text, page["page_number"], document_id, cfg)
        if page_chunks:
            pages_with_chunks.append(page["page_number"])
        chunks.extend(page_chunks)

    return {
        "document_id": document_id,
        "config": asdict(cfg),
        "statistics": {
            "chunk_count": len(chunks),
            "pages_with_chunks": pages_with_chunks,
            "pages_without_chunks": pages_without_chunks,
        },
        "chunks": [chunk.to_dict() for chunk in chunks],
    }

