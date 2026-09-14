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
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol, runtime_checkable

from clinivault_ai.generation.errors import GenerationError

API_ROOT = "https://generativelanguage.googleapis.com"
GENERATE_CONTENT_PATH = "/v1beta/models/{model}:generateContent"


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


def _raise_generation_error(exc: urllib.error.HTTPError, body: bytes) -> None:
    try:
        parsed = json.loads(body)
    except Exception:
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
        message = parsed["error"].get("message")
        if message:
            raise GenerationError(
                f"Gemini API error response (status {exc.code}): {message}"
            ) from exc
        raise GenerationError(
            f"Gemini API error response (HTTP {exc.code})" f" from {API_ROOT}"
        ) from exc
    raise GenerationError(
        f"Gemini API error response (HTTP {exc.code})" f" from {API_ROOT}"
    ) from exc


def _coerce_usage(value: Any) -> dict[str, Any]:
    """Return a usage dict, leaving the original intact when it is a dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    return {"raw": value}


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    """POST JSON to *url* and return the parsed JSON body.

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
    """

    name: str = "google_gemini"
    model: str = "gemini-2.5-flash"

    def __init__(
        self,
        *,
        model: str | None = None,
        timeout: float = 60.0,
        api_key: str | None = None,
    ) -> None:
        if model:
            self.model = model
        self.timeout = timeout
        self._api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None

    def generate(self, prompt: str, timeout: float | None = None) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise GenerationError("GeminiProvider.generate requires a non-empty prompt string")

        t = float(timeout) if timeout is not None else self.timeout
        if t <= 0:
            raise GenerationError("GeminiProvider timeout must be positive")

        api_key = self._api_key or _env_api_key()
        url = (
            f"{API_ROOT}{GENERATE_CONTENT_PATH.format(model=urllib.parse.quote(self.model, safe=''))}"
            f"?key={urllib.parse.quote(api_key, safe='')}"
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

        response = _post_json(url, payload, t)
        return _parse_generate_content_response(response, self.model)
