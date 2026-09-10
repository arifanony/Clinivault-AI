"""Embedding-stage errors: malformed responses fail clearly, never silently."""

from __future__ import annotations


class EmbeddingError(Exception):
    """An embedding response is malformed, inconsistent, or incomplete.

    Raised instead of dropping or padding records: a failed embedding run
    produces no artifact at all (no silent partial output).
    """
