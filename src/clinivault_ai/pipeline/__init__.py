"""Baseline end-to-end pipeline execution with full trace collection.

Minimal glue: retrieval + context construction + generation, collecting
three observability traces (retrieval, context, generation) plus the
generation result. No new algorithms, no persistence, no evaluation --
this exists so a single real run can be reconstructed from one
JSON-serializable structure.
"""

from __future__ import annotations

from clinivault_ai.context import build_context
from clinivault_ai.generation import generate_answer
from clinivault_ai.retrieval import search


def run_query(
    store,
    query: str,
    embedding_provider,
    generation_provider,
    *,
    top_k: int = 5,
) -> dict:
    """Run retrieval -> context -> generation, collecting all traces.

    Returns a JSON-serializable dict:

        {query,
         retrieval_trace,   # populated by retrieval.search
         context_trace,     # populated by context.build_context
         generation_trace,  # populated by generation.generate_answer
         result}            # the generation result dict

    Does not change any stage behavior; each stage behaves exactly as
    when called directly. Provider and context errors propagate
    unchanged.
    """
    retrieval_trace: dict = {}
    context_trace: dict = {}
    generation_trace: dict = {}

    results = search(store, query, embedding_provider, top_k, trace=retrieval_trace)
    bundle = build_context(results, query, trace=context_trace)
    result = generate_answer(
        bundle, generation_provider, trace=generation_trace
    )

    return {
        "query": query,
        "retrieval_trace": retrieval_trace,
        "context_trace": context_trace,
        "generation_trace": generation_trace,
        "result": result,
    }
