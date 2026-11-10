"""M7: production query API (DECISION-021).

Covers, with fake providers and synthetic stores only (no network, no
API keys, no E5 cache):

- health shape (status, counts, embedding model; no secrets)
- query happy path (answer, status, run_id, sources, record fields)
- validation rejections (empty/blank query, bad top_k/max_chars)
- abstention mapping and invalid-citation passthrough
- per-request API key isolation (factory receives the body key)
- provider failure -> 500 with a safe, secret-free message
- access logs are JSON lines carrying no query, answer, or key
"""

from __future__ import annotations

import json
import os
import unittest

from fastapi.testclient import TestClient

from clinivault_ai.api import create_app
from clinivault_ai.generation.errors import GenerationError


def _silent_env(**overrides):
    env = dict(os.environ)
    env.pop("GOOGLE_API_KEY", None)
    env.update(overrides)
    return env


class ScriptedProvider:
    """Fake generation provider returning a canned answer."""

    name = "fake"
    model = "fake-model-v1"

    def __init__(self, answer="Paris.", calls=None):
        self._answer = answer
        self.calls = calls if calls is not None else []

    def generate(self, prompt, timeout=60.0):
        self.calls.append(prompt)
        return {"text": self._answer, "attempts": len(self.calls)}


def _client(answer="Paris.", provider_calls=None, factory=None):
    from tests.test_pipeline import build_store

    store, embedder = build_store()

    def make_provider(api_key=None):
        if factory is not None:
            return factory(api_key)
        return ScriptedProvider(answer, provider_calls)

    return TestClient(create_app(store, embedder, make_provider))


class HealthTests(unittest.TestCase):
    def test_health_shape(self):
        body = _client().get("/health").json()
        self.assertEqual(body["status"], "ok")
        self.assertIsInstance(body["document_count"], int)
        self.assertIsInstance(body["chunk_count"], int)
        self.assertGreater(body["chunk_count"], 0)
        self.assertTrue(body["embedding_model"])
        dumped = json.dumps(body)
        self.assertNotIn("GOOGLE_API_KEY", dumped)
        self.assertNotIn("api_key", dumped)


class QueryHappyPathTests(unittest.TestCase):
    def test_answer_and_record_fields(self):
        res = _client().post(
            "/query", json={"query": "capital city of France", "top_k": 2})
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["answer"], "Paris.")
        self.assertEqual(body["status"], "ok")
        self.assertFalse(body["abstained"])
        self.assertTrue(body["run_id"])
        self.assertTrue(body["timestamp"])
        self.assertEqual(body["model"], "fake-model-v1")
        self.assertEqual(body["invalid_citations"], [])
        self.assertEqual(len(body["sources"]), 2)
        for source in body["sources"]:
            self.assertEqual(
                set(source), {"document_id", "page_number", "chunk_id"})
        self.assertEqual(len(body["retrieval"]["chunks"]), 2)
        self.assertEqual(
            set(body["context"]),
            {"chunk_ids_used", "truncated_chunk_ids"})
        dumped = json.dumps(body)
        self.assertNotIn("prompt_text", dumped)
        self.assertNotIn("GOOGLE_API_KEY", dumped)
        self.assertNotIn("api_key", dumped)

    def test_max_chars_budget_reaches_response(self):
        res = _client().post(
            "/query",
            json={"query": "capital city of France",
                  "top_k": 2, "max_chars": 1},
        )
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(len(body["sources"]), 1)
        self.assertEqual(len(body["context"]["truncated_chunk_ids"]), 1)


class QueryValidationTests(unittest.TestCase):
    def test_missing_query_rejected(self):
        res = _client().post("/query", json={"top_k": 2})
        self.assertEqual(res.status_code, 422)

    def test_empty_query_rejected(self):
        res = _client().post("/query", json={"query": ""})
        self.assertEqual(res.status_code, 422)

    def test_blank_query_rejected(self):
        res = _client().post("/query", json={"query": "   "})
        self.assertEqual(res.status_code, 422)

    def test_top_k_bounds_rejected(self):
        for top_k in (0, -3, 51):
            with self.subTest(top_k=top_k):
                res = _client().post(
                    "/query", json={"query": "q", "top_k": top_k})
                self.assertEqual(res.status_code, 422)

    def test_bad_max_chars_rejected(self):
        for max_chars in (0, -5, "lots"):
            with self.subTest(max_chars=max_chars):
                res = _client().post(
                    "/query", json={"query": "q", "max_chars": max_chars})
                self.assertEqual(res.status_code, 422)


class AbstentionAndCitationTests(unittest.TestCase):
    def test_abstain_answer_maps_to_abstained(self):
        res = _client("ABSTAIN: out of scope.").post(
            "/query",
            json={"query": "Type 1 diabetes in children?", "top_k": 2})
        self.assertEqual(res.status_code, 200, res.text)
        body = res.json()
        self.assertEqual(body["status"], "abstained")
        self.assertTrue(body["abstained"])

    def test_invalid_citation_passes_through(self):
        res = _client("x (EVIDENCE_ITEM_RANK: 99).").post(
            "/query", json={"query": "q", "top_k": 2})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(
            res.json()["invalid_citations"],
            [{"kind": "rank", "value": 99}],
        )


class ProviderKeyTests(unittest.TestCase):
    def test_request_key_reaches_provider_factory(self):
        seen = []

        def factory(api_key):
            seen.append(api_key)
            return ScriptedProvider("Paris.")

        res = _client(factory=factory).post(
            "/query",
            json={"query": "q", "top_k": 2, "api_key": "  REQUEST-KEY  "})
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(seen, ["  REQUEST-KEY  "])
        self.assertNotIn("REQUEST-KEY", json.dumps(res.json()))

    def test_provider_failure_is_500_without_secrets(self):
        from unittest.mock import patch

        sentinel = "SENTINEL-KEY-9f8e7d6c5b4a"

        def factory(api_key):
            raise GenerationError("fake provider failure")

        with patch.dict(os.environ, _silent_env(GOOGLE_API_KEY=sentinel),
                        clear=True):
            res = _client(factory=factory).post(
                "/query", json={"query": "q"})
        self.assertEqual(res.status_code, 500)
        self.assertIn("GenerationError", res.json()["detail"])
        self.assertNotIn(sentinel, res.text)
        self.assertNotIn("GOOGLE_API_KEY", res.text)


class AccessLogTests(unittest.TestCase):
    def test_request_log_is_json_without_query_answer_or_key(self):
        import io
        import logging

        from clinivault_ai.api.app import JsonFormatter

        sentinel_query = "SENTINEL-QUERY-zzz"
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        api_logger = logging.getLogger("clinivault_ai.api")
        old_level = api_logger.level
        api_logger.setLevel(logging.INFO)
        api_logger.addHandler(handler)
        try:
            res = _client().post(
                "/query",
                json={"query": sentinel_query, "top_k": 2,
                      "api_key": "SENTINEL-KEY-zzz"},
            )
        finally:
            api_logger.removeHandler(handler)
            api_logger.setLevel(old_level)
        self.assertEqual(res.status_code, 200, res.text)
        lines = [ln for ln in stream.getvalue().splitlines() if ln.strip()]
        self.assertTrue(lines)
        for line in lines:
            payload = json.loads(line)
            self.assertEqual(payload["method"], "POST")
            self.assertEqual(payload["path"], "/query")
            self.assertEqual(payload["status_code"], 200)
            self.assertIn("duration_ms", payload)
            self.assertEqual(payload["run_id"], res.json()["run_id"])
            flat = json.dumps(payload)
            self.assertNotIn(sentinel_query, flat)
            self.assertNotIn("SENTINEL-KEY-zzz", flat)
            self.assertNotIn("Paris.", flat)


if __name__ == "__main__":
    unittest.main()
