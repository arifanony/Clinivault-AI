"""Structural chunking for Clinivault AI.

Takes parsed page data and produces retrievable evidence units (chunks)
that preserve clinical meaning and full provenance.

Two-stage pipeline:
  1. Reading-order correction (optional, column-aware re-extraction)
  2. Structural chunking (headings, recommendations, paragraphs, tables, references)

Chunk IDs are deterministic: {document_id}-p{page:03d}-c{chunk_index:03d}
"""

from .chunker import (
    chunk_pages,
    ChunkConfig,
    ChunkOutput,
    default_config,
)
from .reader import (
    extract_page_text_column_aware,
    DEFAULT_COLUMN_GAP_THRESHOLD,
    DEFAULT_COLUMN_MARGIN,
)
from .validate import validate_chunks

__all__ = [
    "chunk_pages",
    "ChunkConfig",
    "ChunkOutput",
    "default_config",
    "extract_page_text_column_aware",
    "DEFAULT_COLUMN_GAP_THRESHOLD",
    "DEFAULT_COLUMN_MARGIN",
    "validate_chunks",
]
