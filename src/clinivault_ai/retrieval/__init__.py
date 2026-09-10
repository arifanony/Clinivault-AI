"""Baseline vector storage and similarity retrieval for Clinivault AI.

Builds an in-memory cosine index from validated chunk output + its
validated embedding artifact (joined by chunk_id, re-validated on
build), embeds queries through the existing EmbeddingProvider seam, and
returns deterministic top-k results with full provenance:

    {chunk_id, document_id, page_number, score, text}

Out of scope (deliberately): LLM generation, answer construction,
context windows, chat UI, production vector databases, hybrid/rerank
retrieval. This is the working retrieval baseline the project brief
prescribes before any improvement work.
"""

from __future__ import annotations

from .errors import RetrievalError
from .search import search
from .store import VectorStore

__all__ = ["VectorStore", "search", "RetrievalError"]
