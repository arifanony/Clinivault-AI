"""Evaluation-only semantic embedding provider (controlled comparison unit).

This module exists ONLY for the retrieval controlled-comparison experiment
(docs/pipelines/retrieval-controlled-comparison.md). It is NOT the
production embedding provider and is not wired into any pipeline stage.

Provider: Google ``models/gemini-embedding-001`` via the Gemini API
(verified reachable and batch-capable in the provider-feasibility work;
catalog-verified current stable embedding model after ``text-embedding-004``
was retired). Dimension 3072. Chunks are embedded with
``RETRIEVAL_DOCUMENT`` task type; queries with ``RETRIEVAL_QUERY`` (the
API's documented retrieval pairing).

Credentials: read ONLY from the environment / local git-ignored ``.env``
(``GOOGLE_API_KEY``). The key is never printed, logged, written to any
file, or included in error messages, artifacts, or trace output.

Reproducibility limitation (recorded, not hidden): results depend on an
external network service. The API is deterministic for identical input in
practice, but reproducibility requires network access and API quota; this
is an experiment-only limitation and is documented in the comparison
report.

Implements the existing EmbeddingProvider seam (batch-in, batch-out,
order-preserving) so it works with ``generate_embeddings()`` and
``VectorStore`` unchanged.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from clinivault_ai.embedding.errors import EmbeddingError

MODEL_ID = "models/gemini-embedding-001"
MODEL_NAME = "gemini-embedding-001"
EMBED_URL = f"https://generativelanguage.googleapis.com/v1beta/{MODEL_ID}:embedContent"
BATCH_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:batchEmbedContents"
DEFAULT_BATCH_SIZE = 32


def _load_env_key() -> str | None:
    """Read GOOGLE_API_KEY from the process env, falling back to .env.

    The value is returned in-process only; it is never printed or stored.
    """
    key = os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    env_path = Path(".env")
    if not env_path.is_file():
        return None
    try:
        text = env_path.read_text(encoding="utf-8", errors="strict")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("GOOGLE_API_KEY="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            return value or None
    return None


def _error(message: str) -> EmbeddingError:
    # Never include request bodies or the API key in error messages.
    return EmbeddingError(f"Gemini embedding API: {message}")


def _request_batch(api_key: str, requests_payload: list[dict],
                   max_retries: int = 5, backoff_seconds: float = 65.0,
                   batch_gap_seconds: float = 2.0) -> list[list[float]]:
    """POST one batchEmbedContents request.

    Experiment-only bounded retry: the free tier enforces a per-minute
    request limit, so HTTP 429 is retried with a fixed backoff, at most
    ``max_retries`` times. This retry exists ONLY in this evaluation
    provider; production embedding has no retry. Each call also sleeps
    ``batch_gap_seconds`` afterwards to space consecutive batches.
    """
    import time as _time

    body = json.dumps({"requests": requests_payload}).encode("utf-8")
    attempts = 0
    while True:
        req = urllib.request.Request(
            BATCH_URL,
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempts < max_retries:
                attempts += 1
                _time.sleep(backoff_seconds)
                continue
            raise _error(f"HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise _error(f"request failed: {type(exc).__name__}") from exc
    _time.sleep(batch_gap_seconds)
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(requests_payload):
        raise _error("response embeddings count does not match request count")
    vectors = []
    for item in embeddings:
        vector = item.get("values")
        if not isinstance(vector, list) or not vector:
            raise _error("response embedding is missing values")
        vectors.append([float(v) for v in vector])
    return vectors


class GeminiEmbeddingProvider:
    """Semantic embeddings via the Gemini API (evaluation-only provider)."""

    name = "gemini-embedding-001"

    def __init__(self, api_key: str | None = None, batch_size: int = DEFAULT_BATCH_SIZE):
        self._api_key = api_key or _load_env_key()
        if not self._api_key:
            raise EmbeddingError(
                "GeminiEmbeddingProvider: GOOGLE_API_KEY is absent or empty"
            )
        if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size < 1:
            raise EmbeddingError("batch_size must be a positive integer")
        self.batch_size = batch_size
        self.dimension = 3072

    def provider_params(self) -> dict:
        return {
            "method": "gemini-api-embedding",
            "model": MODEL_ID,
            "task_types": {"texts": "RETRIEVAL_DOCUMENT", "queries": "RETRIEVAL_QUERY"},
            "batch_size": self.batch_size,
            "external": True,
        }

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed chunk/body texts (RETRIEVAL_DOCUMENT) in order."""
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> list[float]:
        """Embed one query (RETRIEVAL_QUERY)."""
        return self._embed([query], "RETRIEVAL_QUERY")[0]

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise EmbeddingError("cannot embed empty or whitespace-only text")
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]
            requests_payload = [
                {
                    "model": MODEL_ID,
                    "content": {"parts": [{"text": text}]},
                    "taskType": task_type,
                }
                for text in batch
            ]
            vectors.extend(_request_batch(self._api_key, requests_payload))
        return vectors
