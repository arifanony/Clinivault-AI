"""Context-stage errors: malformed retrieval results fail clearly."""

from __future__ import annotations


class ContextError(Exception):
    """Retrieval results cannot be packaged into a valid evidence bundle.

    Raised instead of silently dropping fields, reordering, or inventing
    provenance: a failed context build produces no bundle at all.
    """
