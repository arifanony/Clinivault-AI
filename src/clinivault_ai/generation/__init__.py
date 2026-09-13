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
evaluation, streaming, retries, or conversational memory.
"""

from clinivault_ai.generation.errors import GenerationError
from clinivault_ai.generation.generator import generate_answer
from clinivault_ai.generation.prompt import build_prompt
from clinivault_ai.generation.provider import (
    GenerationProvider,
    GeminiProvider,
)

__all__ = [
    "GenerationError",
    "GenerationProvider",
    "GeminiProvider",
    "build_prompt",
    "generate_answer",
]
