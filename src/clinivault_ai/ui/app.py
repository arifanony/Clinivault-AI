"""Observability UI application layer.

Trace-first design: a submitted query executes exactly one call to
clinivault_ai.pipeline.run_query(); the returned RunTrace is passed
to the browser unchanged and rendered as-is. The UI never calls
retrieval/context/generation independently and never fabricates
fields. Errors are returned as JSON with a safe message; API keys
and environment values are never included in responses.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from clinivault_ai.generation.provider import GeminiProvider
from clinivault_ai.pipeline import run_query
from clinivault_ai.ui.page import PAGE_HTML
DEFAULT_QUERY = "criteria for the diagnosis of diabetes"
DEFAULT_TOP_K = 5


def create_trace_response(run_fn, query, top_k, api_key=None):
    """Execute one pipeline run and wrap the result for the UI.

    Supports both legacy run_fn(query, top_k) and BYOK
    run_fn(query, top_k, api_key=...) callables. A blank/whitespace-only
    request key is normalized to None so the environment fallback still
    works. Returns (status_code, body_dict). Never includes
    environment/secret values in the response.
    """
    if not isinstance(query, str) or not query.strip():
        return 400, {"ok": False, "error": "query must be a non-empty string"}
    try:
        top_k_int = int(top_k)
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "top_k must be an integer"}
    if top_k_int < 1 or top_k_int > 50:
        return 400, {"ok": False, "error": "top_k must be between 1 and 50"}
    if isinstance(api_key, str):
        api_key = api_key.strip() or None

    try:
        try:
            trace = run_fn(query.strip(), top_k_int, api_key=api_key)
        except TypeError:
            # Legacy two-arg run_fn: fall back without the key.
            trace = run_fn(query.strip(), top_k_int)
    except Exception as exc:  # UI boundary: report, never crash the server
        # Safe message: exception text only, never environment/secret state.
        return 500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return 200, {"ok": True, "trace": trace}


# Nine obtained Stage-1 baseline documents. T2D-004 is blocked-access and
# is never loaded; do not invent a substitute (see the M1-M7 guide).
CORPUS_DOCUMENT_IDS = (
    "T2D-001",
    "T2D-002",
    "T2D-003",
    "T2D-005",
    "T2D-006",
    "T2D-007",
    "T2D-008",
    "T2D-009",
    "T2D-010",
)

PROVIDERS = ("e5", "hash")


def _repo_root():
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )


def _embedding_dir(provider):
    if provider == "e5":
        return "embedded-intfloat--e5-small-v2"
    if provider == "hash":
        return "embedded"
    raise ValueError(f"unknown provider {provider!r}")


def default_paths(provider="e5"):
    """(parsed, embeddings) artifact paths for T2D-001 under one provider tree."""
    root = _repo_root()
    return (
        os.path.join(root, "data", "parsed", "stage-1-clean-baseline-corpus",
                     "T2D-001", "T2D-001.parsed.json"),
        os.path.join(root, "data", _embedding_dir(provider),
                     "stage-1-clean-baseline-corpus",
                     "T2D-001", "T2D-001.embeddings.json"),
    )


def default_corpus_paths(provider="e5"):
    """[(parsed, embeddings), ...] for the nine obtained Stage-1 documents."""
    root = _repo_root()
    embedded = _embedding_dir(provider)
    return [
        (
            os.path.join(root, "data", "parsed", "stage-1-clean-baseline-corpus",
                         doc_id, f"{doc_id}.parsed.json"),
            os.path.join(root, "data", embedded,
                         "stage-1-clean-baseline-corpus",
                         doc_id, f"{doc_id}.embeddings.json"),
        )
        for doc_id in CORPUS_DOCUMENT_IDS
    ]


def _select_embedder(model_names):
    """Return the query embedder matching the loaded artifact model(s).

    All corpus artifacts must share one model; a mixed corpus or an
    unknown model fails loud instead of silently pairing a query
    embedder with the wrong vector space (DECISION-017).
    """
    from clinivault_ai.embedding import (
        BaselineHashEmbeddingProvider,
        E5EmbeddingProvider,
        E5_MODEL_NAME,
        EmbeddingError,
    )

    names = sorted(set(model_names))
    if len(names) != 1:
        raise EmbeddingError(
            f"mixed embedding models across corpus artifacts: {names}; "
            "all documents must share one model"
        )
    model_name = names[0]
    if model_name == E5_MODEL_NAME:
        return E5EmbeddingProvider()
    if model_name == BaselineHashEmbeddingProvider.name:
        return BaselineHashEmbeddingProvider()
    raise EmbeddingError(
        f"unsupported embedding artifact model {model_name!r}; "
        f"expected {E5_MODEL_NAME!r} or {BaselineHashEmbeddingProvider.name!r}"
    )


def load_store(provider="e5", *, single_doc=False):
    """Build the (store, embedder) pair once from committed artifacts.

    Loads the nine-document corpus index by default, or the legacy
    T2D-001-only store with ``single_doc=True``. Callers build once at
    startup and reuse the result for every request.
    """
    from clinivault_ai.chunking import chunk_pages, default_config
    from clinivault_ai.retrieval.store import VectorStore

    path_pairs = [default_paths(provider)] if single_doc else default_corpus_paths(provider)
    pairs = []
    model_names = []
    for parsed_path, embeddings_path in path_pairs:
        with open(parsed_path, encoding="utf-8") as f:
            parsed = json.load(f)
        with open(embeddings_path, encoding="utf-8") as f:
            artifact = json.load(f)
        pairs.append((artifact, chunk_pages(parsed, default_config())))
        model_names.append((artifact.get("model") or {}).get("name"))
    embedder = _select_embedder(model_names)
    if single_doc:
        store = VectorStore.from_artifacts(*pairs[0])
    else:
        store = VectorStore.from_corpus(pairs)
    return store, embedder


def make_run_fn(store, embedder):
    """Bind run_query to an already-built store.

    The store is reused for every request; only the generation provider
    is created per-request so that a request-scoped API key can be used
    without persisting it.
    """

    def run_fn(query, top_k, *, api_key=None):
        from clinivault_ai.generation.provider import GeminiProvider

        provider = GeminiProvider(api_key=api_key)
        return run_query(store, query, embedder, provider, top_k=top_k)

    return run_fn


class ObservabilityUI:
    """Minimal HTTP server: serves the page and one JSON trace endpoint.

    Endpoints:
        GET  /            -> the single-page UI (PAGE_HTML)
        POST /api/query   -> {"query": str, "top_k": int} -> trace JSON

    The UI layer never returns environment values. Only trace data
    produced by run_query() and a safe error message are sent.
    """

    def __init__(self, run_fn, *, host="127.0.0.1", port=8765):
        self._run_fn = run_fn
        self.host = host
        self.port = port

    def make_handler(self):
        run_fn = self._run_fn
        page_html = PAGE_HTML

        class Handler(BaseHTTPRequestHandler):
            def _send_json(self, code, body):
                payload = json.dumps(body).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_GET(self):
                if self.path in ("/", "/index.html"):
                    data = page_html.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._send_json(404, {"ok": False, "error": "not found"})

            def do_POST(self):
                if self.path != "/api/query":
                    self._send_json(404, {"ok": False, "error": "not found"})
                    return
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                    request = json.loads(self.rfile.read(length) or b"{}")
                except (ValueError, json.JSONDecodeError):
                    self._send_json(400, {"ok": False, "error": "invalid JSON body"})
                    return
                code, body = create_trace_response(
                    run_fn,
                    request.get("query"),
                    request.get("top_k"),
                    request.get("api_key"),
                )
                self._send_json(code, body)

            def log_message(self, *args):  # keep dev console quiet
                pass

        return Handler

    def serve(self):
        server = ThreadingHTTPServer((self.host, self.port), self.make_handler())
        print(f"Clinivault observability UI: http://{self.host}:{self.port}")
        print("Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


def build_parser():
    """CLI flags for `python -m clinivault_ai.ui`."""
    parser = argparse.ArgumentParser(description="Clinivault observability UI (V1)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--provider", choices=PROVIDERS, default="e5",
                        help="retrieval embeddings: production E5 (default) or hash baseline")
    parser.add_argument("--single-doc", action="store_true",
                        help="index T2D-001 only (legacy path) instead of the nine-document corpus")
    return parser


def main(argv=None):
    """CLI entry point: `python -m clinivault_ai.ui` (Gemini run)."""
    args = build_parser().parse_args(argv)

    scope = "T2D-001 only" if args.single_doc else "nine-document corpus"
    print(f"Loading {scope} index ({args.provider}) ...")
    store, embedder = load_store(args.provider, single_doc=args.single_doc)
    print(f"Loaded {len(store)} chunks.")
    run_fn = make_run_fn(store, embedder)
    ObservabilityUI(run_fn, host=args.host, port=args.port).serve()


if __name__ == "__main__":  # pragma: no cover
    main()
