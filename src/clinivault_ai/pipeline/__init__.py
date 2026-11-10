"""Baseline end-to-end pipeline execution with full trace collection.

Minimal glue: retrieval + context construction + generation, collecting
three observability traces (retrieval, context, generation) plus the
generation result and one small structured execution record (M4, the
Errata contract). No new algorithms and no evaluation -- this exists so
a single real run can be reconstructed from one JSON-serializable
structure.
"""

from __future__ import annotations

from clinivault_ai.context import build_context
from clinivault_ai.generation import generate_answer
from clinivault_ai.pipeline.records import (
    append_execution_record,
    build_execution_record,
    resolve_run_log_path,
)
from clinivault_ai.retrieval import search


def run_query(
    store,
    query: str,
    embedding_provider,
    generation_provider,
    *,
    top_k: int = 5,
    run_log_path=None,
    max_chars: int | None = None,
) -> dict:
    """Run retrieval -> context -> generation, collecting all traces.

    Returns a JSON-serializable dict:

        {query,
         retrieval_trace,   # populated by retrieval.search
         context_trace,     # populated by context.build_context
         generation_trace,  # populated by generation.generate_answer
         result,            # the generation result dict
         run_id,            # unique id for this run (M4)
         timestamp,         # UTC ISO-8601 time of this run (M4)
         execution_record}  # small Errata-contract record (M4, M5)

    Does not change any stage behavior; each stage behaves exactly as
    when called directly. Provider and context errors propagate
    unchanged. ``max_chars`` is passed to ``context.build_context``
    (M5 budget; default None keeps everything).

    Persistence: the small execution record (never prompts, vectors,
    keys, or environment values) is appended as one JSON line to
    ``run_log_path`` when given, else to ``$CLINIVAULT_RUN_LOG`` when
    set. The default writes nothing. Log-write errors propagate.
    """
    retrieval_trace: dict = {}
    context_trace: dict = {}
    generation_trace: dict = {}

    results = search(store, query, embedding_provider, top_k, trace=retrieval_trace)
    bundle = build_context(results, query, trace=context_trace, max_chars=max_chars)
    result = generate_answer(
        bundle, generation_provider, trace=generation_trace
    )
    execution_record = build_execution_record(
        query=query,
        top_k=top_k,
        results=results,
        bundle=bundle,
        result=result,
    )

    log_path = resolve_run_log_path(run_log_path)
    if log_path is not None:
        append_execution_record(execution_record, log_path)

    return {
        "query": query,
        "retrieval_trace": retrieval_trace,
        "context_trace": context_trace,
        "generation_trace": generation_trace,
        "result": result,
        "run_id": execution_record["run_id"],
        "timestamp": execution_record["timestamp"],
        "execution_record": execution_record,
    }
