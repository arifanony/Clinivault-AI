"""Offline tests for the observability UI application layer.

No network, no API keys, no real server binding (except a loopback
test server on port 0). run_fn is faked so the HTTP handler /
response-contract logic is tested in isolation.
"""

from __future__ import annotations

import json
import unittest

from clinivault_ai.ui.app import ObservabilityUI, create_trace_response
from clinivault_ai.ui.page import PAGE_HTML


def make_trace():
    return {
        "query": "q",
        "retrieval_trace": {
            "query": "q",
            "provider": {"name": "baseline", "dimension": 256},
            "embedding_ms": 0.2,
            "top_k": 5,
            "total_candidates": 2,
            "store": {"document_id": "T2D-001", "dimension": 256},
            "candidates": [
                {"rank": 1, "selected": True, "chunk_id": "C1",
                 "document_id": "T2D-001", "page_number": 1, "score": 0.9},
                {"rank": 2, "selected": False, "chunk_id": "C2",
                 "document_id": "T2D-001", "page_number": 2, "score": 0.5},
            ],
        },
        "context_trace": {
            "query": "q",
            "input_retrieval_count": 2,
            "evidence_count": 1,
            "context_ms": 0.05,
            "evidence": [{"rank": 1, "chunk_id": "C1", "document_id": "T2D-001",
                          "page_number": 1, "score": 0.9, "text": "evidence text"}],
        },
        "generation_trace": {
            "provider": "google_gemini", "model": "gemini-2.5-flash",
            "query": "q", "status": "ok", "answer": "an answer",
            "provider_called": True, "prompt_text": "PROMPT contains evidence text",
            "timings": {"prompt_construction_ms": 0.1,
                        "llm_generation_ms": 1.0, "total_ms": 1.1},
            "usage": {"totalTokenCount": 10},
        },
        "result": {"status": "ok", "answer": "an answer"},
    }


class GoodRunFn:
    def __call__(self, query, top_k):
        self.last_query, self.last_top_k = query, top_k
        return make_trace()


class FailRunFn:
    def __call__(self, query, top_k):
        raise RuntimeError("boom: simulated failure")


class CreateTraceResponseTests(unittest.TestCase):
    def test_successful_query_passes_through_trace(self):
        run_fn = GoodRunFn()
        code, body = create_trace_response(run_fn, "criteria", 5)
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["trace"], make_trace())
        self.assertEqual(run_fn.last_query, "criteria")
        self.assertEqual(run_fn.last_top_k, 5)

    def test_top_k_string_is_coerced(self):
        run_fn = GoodRunFn()
        code, body = create_trace_response(run_fn, "q", "7")
        self.assertEqual(code, 200)
        self.assertEqual(run_fn.last_top_k, 7)

    def test_blank_query_rejected(self):
        code, body = create_trace_response(GoodRunFn(), "   ", 5)
        self.assertEqual(code, 400)
        self.assertFalse(body["ok"])
        self.assertIn("query", body["error"])

    def test_bad_top_k_rejected(self):
        for bad in ("abc", "0", "-1", "51", None):
            code, body = create_trace_response(GoodRunFn(), "q", bad)
            self.assertEqual(code, 400, f"top_k={bad!r}")
            self.assertFalse(body["ok"])

    def test_run_failure_returns_safe_error_no_trace(self):
        code, body = create_trace_response(FailRunFn(), "q", 5)
        self.assertEqual(code, 500)
        self.assertFalse(body["ok"])
        self.assertIn("RuntimeError", body["error"])
        self.assertIn("boom", body["error"])
        self.assertNotIn("trace", body)


class PageHtmlTests(unittest.TestCase):
    def test_page_is_investigation_console(self):
        self.assertIn("RAG Observability / Investigation Console", PAGE_HTML)
        self.assertIn("<h1>Clinivault AI</h1>", PAGE_HTML)

    def test_page_contains_grounding_disclaimer(self):
        self.assertIn(
            "Automatic claim-to-evidence evaluation is not available yet.",
            PAGE_HTML,
        )

    def test_page_renders_selected_flag_from_trace_not_rank(self):
        # Selection is read from the trace's actual selected value (c.selected),
        # never inferred from rank position.
        self.assertIn("!!c.selected", PAGE_HTML)

    def test_page_distinguishes_selected_unselected_chips(self):
        self.assertIn("Selected: ' + (sel ? 'YES' : 'NO')", PAGE_HTML)

    def test_page_renders_retrieval_to_context_relationship(self):
        # A candidate is marked TO CONTEXT only by matching context_trace
        # evidence chunk ids (ctxIds), never fabricated.
        self.assertIn("ctxIds[c.chunk_id]", PAGE_HTML)
        self.assertIn("'NOT to context'", PAGE_HTML)
        self.assertIn("'TO CONTEXT'", PAGE_HTML)

    def test_page_expands_exact_retrieved_chunk_text(self):
        self.assertIn('<details class="chunk"', PAGE_HTML)
        self.assertIn("c.text", PAGE_HTML)  # exact retrieved text rendered

    def test_page_links_retrieval_row_to_context_card(self):
        self.assertIn('href="#ctx-', PAGE_HTML)

    def test_page_renders_exact_prompt_from_trace(self):
        self.assertIn("gt.prompt_text", PAGE_HTML)

    def test_page_renders_exact_answer_from_trace(self):
        self.assertIn("gt.answer", PAGE_HTML)

    def test_page_renders_usage_and_track_raw_trace(self):
        self.assertIn("JSON.stringify(gt.usage)", PAGE_HTML)
        self.assertIn("JSON.stringify(t, null, 2)", PAGE_HTML)

    def test_page_handles_no_evidence_state(self):
        self.assertIn("'no_evidence'", PAGE_HTML)
        self.assertIn("generation was not called", PAGE_HTML)

    def test_page_uses_trace_fields_defensively(self):
        self.assertIn("function dash(v)", PAGE_HTML)

    def test_page_does_not_embed_default_secret(self):
        # BYOK intentionally includes a password input; it must not carry
        # a default value and must not persist the key anywhere.
        self.assertNotIn("GOOGLE_API_KEY=", PAGE_HTML)
        self.assertNotIn("localStorage", PAGE_HTML)
        self.assertNotIn("sessionStorage", PAGE_HTML)

    def test_page_byok_input_and_payload(self):
        self.assertIn('id="api_key"', PAGE_HTML)
        self.assertIn('type="password"', PAGE_HTML)
        self.assertIn("api_key: a", PAGE_HTML)

    def test_page_well_formed_document(self):
        self.assertTrue(PAGE_HTML.lstrip().startswith("<!DOCTYPE html>"))
        self.assertTrue(PAGE_HTML.rstrip().endswith("</html>"))


class ByokRequestTests(unittest.TestCase):
    """BYOK request handling: fake providers only, no real keys."""

    def test_request_key_reaches_provider(self):
        seen = {}

        class FakeByokRunFn:
            def __call__(self, query, top_k, *, api_key=None):
                seen["api_key"] = api_key
                return make_trace()

        code, body = create_trace_response(FakeByokRunFn(), "q", 5, api_key="REQ-KEY")
        self.assertEqual(code, 200)
        self.assertEqual(seen["api_key"], "REQ-KEY")
        self.assertNotIn("REQ-KEY", json.dumps(body))

    def test_blank_request_key_normalized_to_none(self):
        seen = {}

        class FakeByokRunFn:
            def __call__(self, query, top_k, *, api_key=None):
                seen["api_key"] = api_key
                return make_trace()

        code, _ = create_trace_response(FakeByokRunFn(), "q", 5, api_key="   ")
        self.assertEqual(code, 200)
        self.assertIsNone(seen["api_key"])

    def test_key_never_included_in_error_output(self):
        class FailByokRunFn:
            def __call__(self, query, top_k, *, api_key=None):
                raise RuntimeError("boom: simulated failure")

        code, body = create_trace_response(FailByokRunFn(), "q", 5, api_key="REQ-KEY")
        self.assertEqual(code, 500)
        self.assertNotIn("REQ-KEY", json.dumps(body))

    def test_provider_prefers_request_key_over_env(self):
        import os
        from unittest.mock import patch

        from clinivault_ai.generation.provider import GeminiProvider

        captured = {}

        def fake_post(url, payload, timeout):
            captured["url"] = url
            return {"text": "hello", "usage": {}}

        os.environ["GOOGLE_API_KEY"] = "ENV-KEY"
        try:
            with patch("clinivault_ai.generation.provider._post_json", side_effect=fake_post):
                out = GeminiProvider(api_key="REQ-KEY").generate("hi")
            self.assertEqual(out["text"], "hello")
            self.assertIn("REQ-KEY", captured["url"])
            self.assertNotIn("ENV-KEY", captured["url"])
        finally:
            del os.environ["GOOGLE_API_KEY"]

    def test_provider_env_fallback_still_works(self):
        import os
        from unittest.mock import patch

        from clinivault_ai.generation.provider import GeminiProvider

        captured = {}

        def fake_post(url, payload, timeout):
            captured["url"] = url
            return {"text": "hello", "usage": {}}

        os.environ["GOOGLE_API_KEY"] = "ENV-KEY"
        try:
            with patch("clinivault_ai.generation.provider._post_json", side_effect=fake_post):
                out = GeminiProvider().generate("hi")
            self.assertEqual(out["text"], "hello")
            self.assertIn("ENV-KEY", captured["url"])
        finally:
            del os.environ["GOOGLE_API_KEY"]

    def test_missing_request_and_env_key_is_safe_error(self):
        import os
        from unittest.mock import patch

        from clinivault_ai.generation.errors import GenerationError
        from clinivault_ai.generation.provider import GeminiProvider

        os.environ.pop("GOOGLE_API_KEY", None)
        with patch("clinivault_ai.generation.provider._post_json") as post:
            with self.assertRaises(GenerationError):
                GeminiProvider().generate("hi")
            post.assert_not_called()

    def test_provider_never_logs_or_stores_key(self):
        import json as _json
        import logging

        from clinivault_ai.generation.provider import GeminiProvider

        provider = GeminiProvider(api_key="REQ-KEY")
        # No key in any JSON-serializable/exported provider state.
        exported = {
            "name": provider.name,
            "model": provider.model,
            "timeout": provider.timeout,
        }
        self.assertNotIn("REQ-KEY", _json.dumps(exported))
        records = []
        handler = logging.Handler()
        handler.emit = lambda record: records.append(record.getMessage())
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            root.warning("trace %s", {"ok": True})
        finally:
            root.removeHandler(handler)
        self.assertNotIn("REQ-KEY", _json.dumps(records))


class HandlerRequestTests(unittest.TestCase):
    """End-to-end over a real loopback HTTP server (no pipeline calls)."""

    def test_get_page_and_post_query_and_validation(self):
        import threading
        from http.server import ThreadingHTTPServer
        from urllib.request import urlopen, Request
        from urllib.error import HTTPError

        ui = ObservabilityUI(GoodRunFn(), port=0)
        server = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler())
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/") as r:
                page = r.read().decode()
            self.assertIn("RAG Investigation Console", page)

            req = Request(
                base + "/api/query",
                data=json.dumps({"query": "q", "top_k": 5}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(req) as r:
                body = json.loads(r.read().decode())
            self.assertEqual(r.status, 200)
            self.assertTrue(body["ok"])
            self.assertEqual(body["trace"]["result"]["status"], "ok")

            req_bad = Request(
                base + "/api/query",
                data=json.dumps({"query": "", "top_k": 5}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(HTTPError) as cm:
                urlopen(req_bad)
            self.assertEqual(cm.exception.code, 400)
            body = json.loads(cm.exception.read().decode())
            cm.exception.close()
            self.assertFalse(body["ok"])

            with self.assertRaises(HTTPError) as cm2:
                urlopen(base + "/nope")
            self.assertEqual(cm2.exception.code, 404)
            cm2.exception.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()