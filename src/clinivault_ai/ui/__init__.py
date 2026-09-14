"""Clinivault AI observability UI (V1, Manual Query Mode).

Developer/debug console over the existing backend trace contract:
run_query() -> RunTrace -> render. No new pipeline behavior, no
persistence, no authentication. Stdlib http.server only; no new
dependencies.
"""

from .app import ObservabilityUI, create_trace_response, main
from .page import PAGE_HTML

__all__ = ["ObservabilityUI", "create_trace_response", "main", "PAGE_HTML"]
