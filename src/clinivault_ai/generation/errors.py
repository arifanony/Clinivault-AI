"""Baseline generation errors for Clinivault AI.

Fail-loud convention consistent with the rest of the pipeline:
a malformed input or a provider failure should raise, not produce a
misleading answer.
"""

from __future__ import annotations


class GenerationError(Exception):
    """Raised when generation cannot proceed safely."""

    pass
