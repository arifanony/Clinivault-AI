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

from clinivault_ai.pipeline import run_query
from clinivault_ai.ui.page import PAGE_HTML

DEFAULT_QUERY = "criteria for the diagnosis of diabetes"
DEFAULT_TOP_K = 5


def create_trace_response(run_fn, query, top_k):
    """Execute one pipeline run and wrap the result for the UI.

    run_fn(query, top_k) -> RunTrace dict (normally a partial of
    pipeline.run_query). Returns (status_code, body_dict). Never
    includes environment/secret values in the response.
    """
    if not isinstance(query, str) or not query.strip():
        return 400, {"ok": False, "error": "query must be a non-empty string"}
    try:
        top_k_int = int(top_k)
    except (TypeError, ValueError):
        return 400, {"ok": False, "error": "top_k must be an integer"}
    if top_k_int < 1 or top_k_int > 50:
        return 400, {"ok": False, "error": "top_k must be between 1 and 50"}

    try:
        trace = run_fn(query.strip(), top_k_int)
    except Exception as exc:  # UI boundary: report, never crash the server
        # Safe message: exception text only, never environment/secret state.
        return 500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    return 200, {"ok": True, "trace": trace}


def _load_t2d001_store(parsed_path, embeddings_path):
    """Build the single-document store from existing baseline artifacts."""
    from clinivault_ai.chunking import chunk_pages, default_config
    from clinivault_ai.embedding import BaselineHashEmbeddingProvider
    from clinivault_ai.retrieval.store import VectorStore

    with open(parsed_path, encoding="utf-8") as f:
        parsed = json.load(f)
    with open(embeddings_path, encoding="utf-8") as f:
        artifact = json.load(f)
    chunk_output = chunk_pages(parsed, default_config())
    embedder = BaselineHashEmbeddingProvider()
    store = VectorStore.from_artifacts(artifact, chunk_output)
    return store, embedder


def make_run_fn(parsed_path, embeddings_path, generation_provider):
    """Bind run_query to one document's store and a generation provider."""

    def run_fn(query, top_k):
        store, embedder = _load_t2d001_store(parsed_path, embeddings_path)
        return run_query(store, query, embedder, generation_provider, top_k=top_k)

    return run_fn


def default_paths():
    """Repository-relative baseline artifact paths (T2D-001)."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return (
        os.path.join(root, "data", "parsed", "stage-1-clean-baseline-corpus",
                     "T2D-001", "T2D-001.parsed.json"),
        os.path.join(root, "data", "embedded", "stage-1-clean-baseline-corpus",
                     "T2D-001", "T2D-001.embeddings.json"),
    )


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
                    run_fn, request.get("query"), request.get("top_k")
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


def main(argv=None):
    """CLI entry point: `python -m clinivault_ai.ui` (Gemini run)."""
    parser = argparse.ArgumentParser(description="Clinivault observability UI (V1)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    from clinivault_ai.generation.provider import GeminiProvider

    parsed_path, embeddings_path = default_paths()
    run_fn = make_run_fn(parsed_path, embeddings_path, GeminiProvider())
    ObservabilityUI(run_fn, host=args.host, port=args.port).serve()


if __name__ == "__main__":  # pragma: no cover
    main()
