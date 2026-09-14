"""
Baseline generation orchestration for Clinivault AI.

Responsibility:
- Receive a context bundle + a GenerationProvider.
- Build the prompt (pure function, in prompt.py).
- Call the provider.
- Return a plain-dict result preserving query, answer, provenance,
  timings, and provider usage when available.

Fail loudly on malformed input. Do not fabricate answers.
"""

from __future__ import annotations

import time
from typing import Any

from clinivault_ai.generation.errors import GenerationError
from clinivault_ai.generation.prompt import build_prompt


def generate_answer(
    bundle: dict[str, Any],
    provider: Any,
    *,
    trace: dict | None = None,
    measure_nested: bool = False,
) -> dict[str, Any]:
    """Generate a grounded answer from a context bundle and provider.

    Args:
        bundle: output of ``clinivault_ai.context.build_context``.
        provider: an object implementing ``GenerationProvider``.
        trace: if provided (a dict), populated with observability
            metadata for the run: provider/model, query, evidence,
            prompt text, answer, status, timings, usage, and whether
            the provider was actually called. The return value is
            unchanged, preserving backward compatibility.
        measure_nested: if True, also measure query embedding /
            retrieval / context-construction latencies supplied via
            ``bundle[_nested_timings]`` and mirror them into the
            result for end-to-end reporting. Does not call retrieval
            or context code itself.

    Returns:
        A dict containing at least:
            query, answer, status, provider, model, evidence,
            prompt_text, timings, usage, nested_timings.

    Raises:
        GenerationError on malformed input or provider failure.
    """

    if not isinstance(bundle, dict):
        raise GenerationError("bundle must be a dict")

    query = bundle.get("query")

    if not isinstance(query, str) or not query.strip():
        raise GenerationError("bundle missing a usable 'query'")

    evidence = bundle.get("evidence")
    if evidence is None:
        raise GenerationError("bundle missing 'evidence'")
    if not isinstance(evidence, list):
        raise GenerationError("bundle 'evidence' must be a list")

    # Total generation-stage timing.
    total_begin = time.perf_counter()

    # Prompt construction timing.
    prompt_begin = time.perf_counter()
    try:
        prompt_text = build_prompt(bundle)
    except ValueError as exc:
        raise GenerationError(f"malformed context bundle: {exc}") from exc
    prompt_ms = (time.perf_counter() - prompt_begin) * 1000.0

    if not evidence:
        total_ms = (time.perf_counter() - total_begin) * 1000.0
        if trace is not None:
            trace.update(
                {
                    "provider": getattr(provider, "name", None),
                    "model": getattr(provider, "model", None),
                    "query": query,
                    "evidence": evidence,
                    "prompt_text": prompt_text,
                    "answer": None,
                    "status": "no_evidence",
                    "provider_called": False,
                    "timings": {
                        "prompt_construction_ms": prompt_ms,
                        "llm_generation_ms": 0.0,
                        "total_ms": total_ms,
                    },
                    "usage": None,
                    "nested_timings": _extract_nested_timings(bundle),
                }
            )
        return {
            "query": query,
            "status": "no_evidence",
            "answer": None,
            "provider": getattr(provider, "name", None),
            "model": getattr(provider, "model", None),
            "evidence": evidence,
            "prompt_text": prompt_text,
            "timings": {
                "prompt_construction_ms": prompt_ms,
                "llm_generation_ms": 0.0,
                "total_ms": total_ms,
            },
            "usage": None,
            "nested_timings": _extract_nested_timings(bundle),
        }

    # LLM generation timing.
    llm_begin = time.perf_counter()
    response = provider.generate(prompt_text)
    llm_ms = (time.perf_counter() - llm_begin) * 1000.0

    total_ms = (time.perf_counter() - total_begin) * 1000.0

    text = response.get("text")
    if not isinstance(text, str) or not text.strip():
        raise GenerationError("LLM returned an empty response")

    usage = response.get("usage") or None

    result = {
        "query": query,
        "status": "ok",
        "answer": text.strip(),
        "provider": getattr(provider, "name", None),
        "model": getattr(provider, "model", None),
        "evidence": evidence,
        "prompt_text": prompt_text,
        "timings": {
            "prompt_construction_ms": prompt_ms,
            "llm_generation_ms": llm_ms,
            "total_ms": total_ms,
        },
        "usage": usage,
        "nested_timings": _extract_nested_timings(bundle),
    }

    if trace is not None:
        trace.update(result)
        trace["provider_called"] = True

    return result


def _extract_nested_timings(bundle: dict[str, Any]) -> dict[str, Any] | None:
    """Optionally surface nested timings supplied by the caller.

    This is a reporting convenience only. It does not trigger any
    retrieval, embedding, or context work.
    """
    nested = bundle.get("_nested_timings")
    if not isinstance(nested, dict):
        return None
    return dict(nested)
