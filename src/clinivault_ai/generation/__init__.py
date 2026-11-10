"""
Baseline grounded generation for Clinivault AI.

This stage consumes a context bundle and a GenerationProvider and
returns a generation result preserving query, answer, provenance,
timings, and provider usage where available.

Responsibility boundary (see DECISION-001):
- Retrieval answers "which evidence appears relevant?"
- Context construction answers "how should that evidence be packaged?"
- This stage answers: "given this evidence, what answer does the
  selected LLM produce?"

This stage does NOT improve retrieval quality. It does not add
evaluation, streaming, or conversational memory. It does retry
transient Gemini failures (429/5xx only) inside the provider and
checks answer reliability (citation refs, ABSTAIN sentinel, attempts)
in the generator (M5, DECISION-020).
"""

from clinivault_ai.generation.citations import (
    check_citations,
    parse_citation_refs,
    validate_citation_refs,
)
from clinivault_ai.generation.errors import GenerationError
from clinivault_ai.generation.generator import ABSTAIN_SENTINEL, generate_answer
from clinivault_ai.generation.prompt import build_prompt
from clinivault_ai.generation.provider import (
    GenerationProvider,
    GeminiProvider,
)

__all__ = [
    "ABSTAIN_SENTINEL",
    "GenerationError",
    "GenerationProvider",
    "GeminiProvider",
    "build_prompt",
    "check_citations",
    "generate_answer",
    "parse_citation_refs",
    "validate_citation_refs",
]
