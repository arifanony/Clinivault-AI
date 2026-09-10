"""Retrieval-stage errors: inconsistent inputs fail clearly, never silently."""

from __future__ import annotations


class RetrievalError(Exception):
    """An index or query is malformed, inconsistent, or out of range.

    Raised instead of dropping, padding, or silently reinterpreting data:
    a failed index build or search produces no results at all.
    """
