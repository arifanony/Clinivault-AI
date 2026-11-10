"""Production query API package (M7, DECISION-021).

Thin FastAPI layer over :func:`clinivault_ai.pipeline.run_query`.
The stdlib observability UI stays the inspector; this package is the
machine-facing deploy slice.
"""

from __future__ import annotations

from clinivault_ai.api.app import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    configure_logging,
    create_app,
)

__all__ = [
    "QueryRequest",
    "QueryResponse",
    "HealthResponse",
    "configure_logging",
    "create_app",
]
