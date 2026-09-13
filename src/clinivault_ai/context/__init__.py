"""Baseline context construction for Clinivault AI.

Packages ranked retrieval results into a clean, inspectable,
provenance-preserving evidence bundle for a future generation layer:

    ranked retrieval results -> evidence bundle

Out of scope (deliberately): LLM/answer generation, prompt text, model
providers, context-limit/truncation policies, reranking, abstention.
"""

from __future__ import annotations

from .builder import build_context
from .errors import ContextError

__all__ = ["build_context", "ContextError"]
