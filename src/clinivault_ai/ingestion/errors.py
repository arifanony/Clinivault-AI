"""Ingestion-specific errors."""

from __future__ import annotations


class IngestionError(Exception):
    """Raised when ingestion cannot proceed (missing source, checksum
    mismatch, unreadable PDF, ...). Deliberately distinct from per-page
    extraction problems, which are captured in page records instead."""
