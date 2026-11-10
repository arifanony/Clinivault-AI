"""Baseline generation provider seam for Clinivault AI.

Minimal abstraction justified by DECISION-001 and DECISION-007.

- The project brief treats the LLM as a replaceable component.
- Tests require a fake provider regardless of which real provider is
  chosen, so two implementations exist from day one.
- This means a seam is justified by current requirements, not added
  speculatively.

Only ONE real implementation is provided here: Google Gemini
(gemini-2.5-flash), on the Gemini Developer API.

The API key is read from the environment at runtime. It must never be
hardcoded, committed, or printed.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol, runtime_checkable

from clinivault_ai.generation.errors import GenerationError

API_ROOT = "https://generativelanguage.googleapis.com"
GENERATE_CONTENT_PATH = "/v1beta/models/{model}:generateContent"

RETRYABLE_STATUS_CODES = frozenset({429})
RETRYABLE_STATUS_FLOOR = 500
RETRYABLE_STATUS_CEILING = 599


def _is_retryable_status(status: Any) -> bool:
    """True only for 429 and 5xx (never 401/403 or non-HTTP failures)."""
    if isinstance(status, bool) or not isinstance(status, int):
        return False
    return status in RETRYABLE_STATUS_CODES or (
        RETRYABLE_STATUS_FLOOR <= status <= RETRYABLE_STATUS_CEILING
    )


@runtime_checkable
class GenerationProvider(Protocol):
    """Smallest useful generation provider seam."""

    name: str
    model: str

    def generate(self, prompt: str, timeout: float = 60.0) -> dict[str, Any]:
        """Return a generation response dict.

        The dict must contain at least:
            {"text": "...", "usage": {...}}  on success,
        or raise on failure.
        """
        ...


def _env_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY")
    if not key or not key.strip():
        raise GenerationError("GOOGLE_API_KEY is absent or empty")
    return key.strip()


def _generation_error(message: str, status: int | None) -> GenerationError:
    """Build a GenerationError carrying its HTTP status (None if non-HTTP).

    The ``status`` attribute lets the retry loop tell 429/5xx (retry)
    from 401/403 (fail now) without parsing message text. It is purely
    additive: message text and raise sites are unchanged.
    """
    error = GenerationError(message)
    error.status = status
    return error


def _raise_generation_error(exc: urllib.error.HTTPError, body: bytes) -> None:
    try:
        parsed = json.loads(body)
    except Exception:
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        message = parsed["error"].get("message")
        if message:
            raise _generation_error(
                f"Gemini API error response (status {exc.code}): {message}",
                exc.code,
            ) from exc
        raise _generation_error(
            f"Gemini API error response (HTTP {exc.code})" f" from {API_ROOT}",
            exc.code,
        ) from exc
    raise _generation_error(
        f"Gemini API error response (HTTP {exc.code})" f" from {API_ROOT}",
        exc.code,
    ) from exc


def _coerce_usage(value: Any) -> dict[str, Any]:
    """Return a usage dict, leaving the original intact when it is a dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {"raw": value}


def _post_json(
    url: str, payload: dict[str, Any], timeout: float, *, api_key: str
) -> dict[str, Any]:
    """POST JSON to *url* and return the parsed JSON body.

    The API key travels only in the ``x-goog-api-key`` request header so it
    never appears in URLs, proxy logs, or error messages.

    Raises:
        GenerationError (via _raise_generation_error) on HTTP errors.
        GenerationError on non-JSON responses.
    """
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "ClinivaultAI/0.1 (baseline-generation)",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body_bytes = resp.read()
    except urllib.error.HTTPError as exc:
        try:
            body_bytes = exc.read()
        except Exception:
            body_bytes = b""
        _raise_generation_error(exc, body_bytes)

    try:
        return json.loads(body_bytes)
    except Exception as exc:
        raise GenerationError(
            f"Gemini API returned non-JSON response: {exc}"
        ) from exc


def _parse_generate_content_response(
    response: dict[str, Any], model: str
) -> dict[str, Any]:
    """Extract a normalized generation result dict from a Gemini response.

    Expects the Gemini ``generateContent`` response shape:
        {"candidates": [{"content": {"parts": [{"text": "..."}}]}],
         ...usage/usageMetadata...}
    or a ``candidates`` list with a simple ``text`` field.

    Returns:
        {"text": "...", "usage": {...}} on success.

    Raises:
        GenerationError on missing content, empty candidates, or unexpected
        shapes.
    """
    candidates = response.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        text = response.get("text")
        if isinstance(text, str) and text.strip():
            usage = response.get("usageMetadata") or response.get("usage") or {}
            return {"text": text, "usage": _coerce_usage(usage), "model": model}
        raise GenerationError(
            "Gemini API response had no usable 'candidates' or 'text' field"
        )

    first = candidates[0]
    if not isinstance(first, dict):
        raise GenerationError("unexpected Gemini candidate shape")

    content = first.get("content") or {}
    if not isinstance(content, dict):
        raise GenerationError("unexpected Gemini content shape")

    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise GenerationError("Gemini API response had empty 'parts' in the "
                              "first candidate")

    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            t = part.get("text")
            texts.append(t if isinstance(t, str) else "")
        elif isinstance(part, str):
            texts.append(part)
        else:
            texts.append("")

    text = "".join(texts)
    if not text.strip():
        raise GenerationError("Gemini API returned an empty response")

    usage = response.get("usageMetadata")
    usage = _coerce_usage(usage)
    return {"text": text, "usage": usage, "model": model}


class GeminiProvider:
    """Google Gemini generation provider for gemini-2.5-flash.

    Reads ``GOOGLE_API_KEY`` from the environment at request time.
    For local UI / request-scoped use, an API key may be supplied at
    construction time; that key is used only for that provider instance
    and is never written to disk, the environment, or the trace.

    Transient failures (HTTP 429 and 5xx) are retried up to
    ``max_attempts`` total tries with doubling backoff starting at
    ``retry_backoff_s`` seconds; anything else (401/403, malformed
    responses, non-HTTP errors) raises at once. Every success reports
    ``attempts``; every failure carries it as an exception attribute.
    """

    name: str = "google_gemini"
    model: str = "gemini-2.5-flash"

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
        max_attempts: int = 3,
        retry_backoff_s: float = 1.0,
    ) -> None:
        if model:
            self.model = model
        self.timeout = timeout
        self._api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise GenerationError("GeminiProvider max_attempts must be an integer")
        if max_attempts < 1:
            raise GenerationError("GeminiProvider max_attempts must be at least 1")
        if (
            isinstance(retry_backoff_s, bool)
            or not isinstance(retry_backoff_s, (int, float))
            or retry_backoff_s < 0
        ):
            raise GenerationError("GeminiProvider retry_backoff_s must be non-negative")
        self.max_attempts = max_attempts
        self.retry_backoff_s = float(retry_backoff_s)

    def generate(self, prompt: str, timeout: float | None = None) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise GenerationError("GeminiProvider.generate requires a non-empty prompt string")

        t = float(timeout) if timeout is not None else self.timeout
        if t <= 0:
            raise GenerationError("GeminiProvider timeout must be positive")

        api_key = self._api_key or _env_api_key()
        url = (
            f"{API_ROOT}{GENERATE_CONTENT_PATH.format(model=urllib.parse.quote(self.model, safe=''))}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ],
                }
            ],
        }

        attempts = 0
        while True:
            attempts += 1
            try:
                response = _post_json(url, payload, t, api_key=api_key)
            except GenerationError as exc:
                if attempts < self.max_attempts and _is_retryable_status(
                    getattr(exc, "status", None)
                ):
                    time.sleep(self.retry_backoff_s * (2.0 ** (attempts - 1)))
                    continue
                exc.attempts = attempts
                raise
            try:
                parsed = _parse_generate_content_response(response, self.model)
            except GenerationError as exc:
                exc.attempts = attempts
                raise
            parsed["attempts"] = attempts
            return parsed
