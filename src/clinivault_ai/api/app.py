"""Production query API for Clinivault AI (M7, DECISION-021).

Thin HTTP layer over :func:`clinivault_ai.pipeline.run_query`: the index
is built once at startup and reused for every request; each request gets
a fresh generation provider so a request-scoped API key never persists.

Response and log contracts are secret-free by construction: no API
keys, environment values, prompts, or vectors are returned or logged.
Access logs carry method/path/status/duration/run_id only — never the
query text or the answer.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from clinivault_ai.generation.provider import GeminiProvider
from clinivault_ai.pipeline import run_query

DEFAULT_TOP_K = 5
MAX_TOP_K = 50

logger = logging.getLogger("clinivault_ai.api")


class QueryRequest(BaseModel):
    """POST /query body: what to ask and how much evidence to use."""

    query: str = Field(min_length=1)
    top_k: int = Field(default=DEFAULT_TOP_K, ge=1, le=MAX_TOP_K)
    max_chars: int | None = Field(default=None, gt=0)
    api_key: str | None = Field(default=None)


class QueryResponse(BaseModel):
    """Curated answer payload: the execution record plus answer metadata."""

    run_id: str
    timestamp: str
    query: str
    answer: str | None
    status: str
    abstained: bool
    model: str | None
    attempts: int | None = None
    invalid_citations: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    retrieval: dict[str, Any] = {}
    context: dict[str, Any] = {}


class HealthResponse(BaseModel):
    """GET /health: liveness plus index provenance (no secrets)."""

    status: str
    document_count: int
    chunk_count: int
    embedding_model: str | None


class JsonFormatter(logging.Formatter):
    """One JSON object per log line on stdout (stdlib only)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
        }
        for key in ("method", "path", "status_code", "duration_ms", "run_id"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    """Direct secret-free JSON access logs at stdout (call once in main)."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("clinivault_ai.api")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False


def _summarize_store(store) -> dict[str, Any]:
    records = getattr(store, "records", []) or []
    documents = sorted(
        {r.get("document_id") for r in records if isinstance(r, dict)}
    )
    return {"document_count": len(documents), "chunk_count": len(records)}


def _build_query_response(trace: dict[str, Any]) -> dict[str, Any]:
    record = trace.get("execution_record") or {}
    result = trace.get("result") or {}
    generation = record.get("generation") or {}
    return {
        "run_id": trace.get("run_id"),
        "timestamp": trace.get("timestamp"),
        "query": record.get("query"),
        "answer": result.get("answer"),
        "status": result.get("status"),
        "abstained": bool(generation.get("abstained", False)),
        "model": result.get("model"),
        "attempts": result.get("attempts"),
        "invalid_citations": result.get("invalid_citations") or [],
        "sources": record.get("sources") or [],
        "retrieval": record.get("retrieval") or {},
        "context": record.get("context") or {},
    }


def create_app(
    store,
    embedder,
    make_generation_provider: Callable[[str | None], Any] | None = None,
    *,
    embedding_model: str | None = None,
) -> FastAPI:
    """Build the FastAPI application over one already-loaded index.

    ``make_generation_provider`` receives the request's API key (or
    None) and must return a generation provider; the default builds a
    per-request ``GeminiProvider`` (request key or environment
    fallback), so keys never persist beyond the request.
    """
    if make_generation_provider is None:
        def make_generation_provider(api_key: str | None) -> Any:
            return GeminiProvider(
                api_key=api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
            )

    summary = _summarize_store(store)
    model_name = embedding_model or getattr(embedder, "name", None)

    app = FastAPI(title="Clinivault AI query API")

    @app.middleware("http")
    async def access_log(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        run_id = getattr(request.state, "run_id", None)
        logger.info(
            "request",
            extra={
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
                **({"run_id": run_id} if run_id else {}),
            },
        )
        return response

    @app.get("/health", response_model=HealthResponse)
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            **summary,
            "embedding_model": model_name,
        }

    @app.post("/query", response_model=QueryResponse)
    def ask(body: QueryRequest, request: Request) -> Any:
        query = body.query.strip()
        if not query:
            return JSONResponse(
                status_code=422,
                content={"detail": "query must be a non-empty string"},
            )
        try:
            provider = make_generation_provider(body.api_key)
            trace = run_query(
                store,
                query,
                embedder,
                provider,
                top_k=body.top_k,
                max_chars=body.max_chars,
            )
        except Exception as exc:  # API boundary: safe message only
            return JSONResponse(
                status_code=500,
                content={"detail": f"{type(exc).__name__}: {exc}"},
            )
        request.state.run_id = trace.get("run_id")
        return _build_query_response(trace)

    return app


def build_parser() -> argparse.ArgumentParser:
    """CLI flags for `python -m clinivault_ai.api`."""
    parser = argparse.ArgumentParser(description="Clinivault AI query API (M7)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--provider", choices=("e5", "hash"), default="e5",
        help="retrieval embeddings: production E5 (default) or hash baseline",
    )
    parser.add_argument(
        "--single-doc", action="store_true",
        help="index T2D-001 only (legacy path) instead of the nine-document corpus",
    )
    return parser


def main(argv=None) -> None:
    """CLI entry point: load the index once, then serve with uvicorn."""
    import uvicorn

    from clinivault_ai.ui.app import load_store

    configure_logging()
    args = build_parser().parse_args(argv)

    scope = "T2D-001 only" if args.single_doc else "nine-document corpus"
    logger.info("loading %s index (%s)", scope, args.provider)
    store, embedder = load_store(args.provider, single_doc=args.single_doc)
    logger.info("loaded %d chunks", len(store))

    app = create_app(store, embedder)
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)
