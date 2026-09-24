"""Offline baseline tests for Clinivault AI generation.

No network, no API keys, no .env loading.
Uses fake providers and synthetic context bundles only.
"""

from __future__ import annotations

import time
import unittest
from typing import Any

from clinivault_ai.generation.errors import GenerationError
from clinivault_ai.generation.generator import generate_answer
from clinivault_ai.generation.prompt import build_prompt


class FakeProvider:
    name = "fake"
    model = "fake-model-v1"

    def __init__(self, *, answer="fake answer", usage=None, fail=False):
        self._answer = answer
        self._usage = usage
        self._fail = fail
        self.last_prompt = None

    def generate(self, prompt, timeout=60.0):
        self.last_prompt = prompt
        if self._fail:
            raise GenerationError("fake provider failure")
        result = {"text": self._answer}
        if self._usage is not None:
            result["usage"] = self._usage
        return result


class FakeEmptyProvider:
    name = "fake_empty"
    model = "fake-empty-v1"

    def generate(self, prompt, timeout=60.0):
        return {"text": "   "}


def make_bundle(*, query="What is the capital of France?", evidence=None):
    if evidence is None:
        evidence = [
            {"rank": 1, "chunk_id": "T2D-001-c014", "document_id": "T2D-001",
             "page_number": 14, "score": 0.6, "text": "France capital city is Paris."},
            {"rank": 2, "chunk_id": "T2D-001-c002", "document_id": "T2D-001",
             "page_number": 2, "score": 0.5, "text": "Paris has been the capital since 508 AD."},
        ]
    return {
        "query": query,
        "evidence_count": len(evidence),
        "documents": [{"document_id": "T2D-001", "chunk_count": len(evidence), "pages": [14, 2]}],
        "evidence": evidence,
    }


class PromptTests(unittest.TestCase):
    def test_prompt_includes_query(self):
        bundle = make_bundle(query="What is the capital of France?")
        prompt = build_prompt(bundle)
        self.assertIn("What is the capital of France?", prompt)

    def test_prompt_includes_each_evidence_text(self):
        bundle = make_bundle()
        prompt = build_prompt(bundle)
        for item in bundle["evidence"]:
            self.assertIn(item["text"], prompt)

    def test_prompt_preserves_provenance_fields(self):
        bundle = make_bundle()
        prompt = build_prompt(bundle)
        for item in bundle["evidence"]:
            self.assertIn(str(item["rank"]), prompt)
            self.assertIn(item["chunk_id"], prompt)
            self.assertIn(item["document_id"], prompt)
            self.assertIn(str(item["page_number"]), prompt)

    def test_prompt_constrains_to_evidence(self):
        bundle = make_bundle()
        prompt = build_prompt(bundle)
        self.assertIn("ONLY the evidence", prompt)
        self.assertIn("Do not invent", prompt)

    def test_prompt_rank_order_preserved(self):
        bundle = make_bundle()
        prompt = build_prompt(bundle)
        first_pos = prompt.find("EVIDENCE_ITEM_RANK: 1")
        second_pos = prompt.find("EVIDENCE_ITEM_RANK: 2")
        self.assertGreater(second_pos, first_pos)

    def test_prompt_rejects_missing_key(self):
        bundle = make_bundle()
        del bundle["query"]
        with self.assertRaises(ValueError):
            build_prompt(bundle)

    def test_prompt_rejects_non_dict(self):
        with self.assertRaises(ValueError):
            build_prompt(["not", "a", "dict"])

    def test_prompt_rejects_evidence_missing_field(self):
        bundle = make_bundle()
        bundle["evidence"][0].pop("rank")
        with self.assertRaises(ValueError):
            build_prompt(bundle)

    def test_prompt_no_retrieval(self):
        bundle = make_bundle()
        start = time.perf_counter()
        build_prompt(bundle)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.assertLess(elapsed_ms, 10.0)
class GeneratorSuccessTests(unittest.TestCase):
    def test_valid_bundle_reaches_generation(self):
        provider = FakeProvider(answer="Paris.")
        result = generate_answer(make_bundle(), provider)
        self.assertEqual(result["answer"], "Paris.")

    def test_status_ok(self):
        provider = FakeProvider(answer="Paris.")
        result = generate_answer(make_bundle(), provider)
        self.assertEqual(result["status"], "ok")

    def test_provider_identity_preserved(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        self.assertEqual(result["provider"], "fake")
        self.assertEqual(result["model"], "fake-model-v1")

    def test_evidence_preserved_in_output(self):
        bundle = make_bundle()
        provider = FakeProvider(answer="x")
        result = generate_answer(bundle, provider)
        self.assertEqual(result["evidence"], bundle["evidence"])

    def test_prompt_text_in_result(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        self.assertIn("EVALUATED_QUESTION", result["prompt_text"])

    def test_provider_receives_prompt(self):
        provider = FakeProvider(answer="x")
        generate_answer(make_bundle(), provider)
        self.assertIsNotNone(provider.last_prompt)
        self.assertIn("EVALUATED_QUESTION", provider.last_prompt)

    def test_usage_preserved_when_returned(self):
        provider = FakeProvider(answer="x", usage={"input": 9, "output": 3})
        result = generate_answer(make_bundle(), provider)
        self.assertEqual(result["usage"], {"input": 9, "output": 3})

    def test_usage_absent_when_not_returned(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        self.assertIsNone(result["usage"])


class TimingTests(unittest.TestCase):
    def test_timing_fields_exist(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        for key in ("prompt_construction_ms", "llm_generation_ms", "total_ms"):
            self.assertIn(key, result["timings"])

    def test_timings_are_numeric(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        for key, value in result["timings"].items():
            self.assertIsInstance(value, float, f"{key} must be float")

    def test_timings_non_negative(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        for key, value in result["timings"].items():
            self.assertGreaterEqual(value, 0.0, f"{key} must be >= 0")

    def test_total_at_least_component(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(), provider)
        t = result["timings"]
        self.assertGreaterEqual(
            t["total_ms"], t["prompt_construction_ms"] + t["llm_generation_ms"])


class InputValidationTests(unittest.TestCase):
    def test_rejects_non_dict(self):
        with self.assertRaises(GenerationError):
            generate_answer(["not", "a", "dict"], FakeProvider())

    def test_rejects_missing_query(self):
        bundle = make_bundle()
        del bundle["query"]
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())

    def test_rejects_empty_query(self):
        bundle = make_bundle(query="   ")
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())

    def test_rejects_missing_evidence(self):
        bundle = make_bundle()
        del bundle["evidence"]
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())

    def test_rejects_non_list_evidence(self):
        bundle = make_bundle()
        bundle["evidence"] = "not a list"
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())


class MalformedEvidenceTests(unittest.TestCase):
    """Valid top-level bundle, but evidence item missing a required field.

    The generation module's public error contract is GenerationError.
    ValueError from prompt.py must not leak across the boundary.
    """

    def test_evidence_missing_text_raises_generation_error(self):
        bundle = make_bundle()
        del bundle["evidence"][0]["text"]
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())

    def test_evidence_missing_chunk_id_raises_generation_error(self):
        bundle = make_bundle()
        del bundle["evidence"][0]["chunk_id"]
        with self.assertRaises(GenerationError):
            generate_answer(bundle, FakeProvider())

    def test_evidence_missing_field_message_identifies_field(self):
        bundle = make_bundle()
        del bundle["evidence"][0]["text"]
        with self.assertRaises(GenerationError) as ctx:
            generate_answer(bundle, FakeProvider())
        self.assertIn("text", str(ctx.exception))

    def test_evidence_missing_field_does_not_call_provider(self):
        bundle = make_bundle()
        del bundle["evidence"][0]["text"]
        provider = FakeProvider()
        with self.assertRaises(GenerationError):
            generate_answer(bundle, provider)
        self.assertIsNone(provider.last_prompt)


class EmptyEvidenceTests(unittest.TestCase):
    def test_empty_evidence_no_answer(self):
        provider = FakeProvider(answer="should not be called")
        result = generate_answer(make_bundle(evidence=[]), provider)
        self.assertIsNone(result["answer"])
        self.assertEqual(result["status"], "no_evidence")

    def test_empty_evidence_does_not_call_provider(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(evidence=[]), provider)
        self.assertIsNone(provider.last_prompt)

    def test_empty_evidence_timings_present(self):
        provider = FakeProvider(answer="x")
        result = generate_answer(make_bundle(evidence=[]), provider)
        self.assertIn("prompt_construction_ms", result["timings"])
        self.assertEqual(result["timings"]["llm_generation_ms"], 0.0)


class ProviderFailureTests(unittest.TestCase):
    def test_provider_failure_raises(self):
        provider = FakeProvider(fail=True)
        with self.assertRaises(GenerationError):
            generate_answer(make_bundle(), provider)

    def test_empty_llm_response_raises(self):
        provider = FakeEmptyProvider()
        with self.assertRaises(GenerationError):
            generate_answer(make_bundle(), provider)

    def test_no_silent_fallback_answer(self):
        provider = FakeProvider(fail=True)
        try:
            generate_answer(make_bundle(), provider)
        except GenerationError:
            pass
        else:
            self.fail("expected GenerationError, no fallback answer expected")


class GenerationTraceTests(unittest.TestCase):
    """Observability trace tests (additive; result contract unchanged)."""

    def _usage(self):
        return {
            "promptTokenCount": 10,
            "candidatesTokenCount": 5,
            "totalTokenCount": 15,
        }

    def test_trace_ok_populated_and_json_serializable(self):
        import json

        provider = FakeProvider(usage=self._usage())
        trace: dict = {}
        result = generate_answer(make_bundle(), provider, trace=trace)
        self.assertEqual(trace["provider"], "fake")
        self.assertEqual(trace["model"], "fake-model-v1")
        self.assertEqual(trace["query"], result["query"])
        self.assertEqual(trace["answer"], result["answer"])
        self.assertEqual(trace["status"], "ok")
        self.assertTrue(trace["provider_called"])
        self.assertEqual(trace["prompt_text"], result["prompt_text"])
        self.assertEqual(trace["evidence"], result["evidence"])
        self.assertEqual(trace["timings"], result["timings"])
        self.assertEqual(trace["usage"], self._usage())
        json.dumps(trace)  # must not raise

    def test_trace_timings_present(self):
        provider = FakeProvider()
        trace: dict = {}
        generate_answer(make_bundle(), provider, trace=trace)
        timings = trace["timings"]
        for key in ("prompt_construction_ms", "llm_generation_ms", "total_ms"):
            self.assertIn(key, timings)
            self.assertIsInstance(timings[key], float)
            self.assertGreaterEqual(timings[key], 0.0)

    def test_trace_no_evidence_provider_not_called(self):
        provider = FakeProvider()
        trace: dict = {}
        result = generate_answer(
            make_bundle(evidence=[]), provider, trace=trace
        )
        self.assertEqual(trace["status"], "no_evidence")
        self.assertFalse(trace["provider_called"])
        self.assertIsNone(trace["answer"])
        self.assertIsNone(trace["usage"])
        self.assertEqual(trace["evidence"], [])
        self.assertEqual(result["status"], "no_evidence")
        # Provider was genuinely never invoked.
        self.assertIsNone(provider.last_prompt)

    def test_trace_evidence_preserved_verbatim(self):
        provider = FakeProvider()
        trace: dict = {}
        generate_answer(make_bundle(), provider, trace=trace)
        self.assertEqual(trace["evidence"], make_bundle()["evidence"])
        self.assertIn(
            "France capital city is Paris.", trace["prompt_text"]
        )

    def test_no_trace_backward_compatible(self):
        provider = FakeProvider(usage=self._usage())
        result = generate_answer(make_bundle(), provider)
        self.assertEqual(result["status"], "ok")
        self.assertNotIn("provider_called", result)


class GeminiRequestShapeTests(unittest.TestCase):
    """The API key must travel in a header, never in the request URL."""

    def test_api_key_sent_in_header_not_url(self):
        import io
        import json
        from unittest.mock import patch

        from clinivault_ai.generation.provider import GeminiProvider

        captured = {}

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            captured["headers"] = {k.lower(): v for k, v in req.header_items()}
            body = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
            return FakeResponse(json.dumps(body).encode("utf-8"))

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            out = GeminiProvider(api_key="SECRET-KEY").generate("hi")

        self.assertEqual(out["text"], "ok")
        self.assertNotIn("SECRET-KEY", captured["url"])
        self.assertNotIn("key=", captured["url"])
        self.assertEqual(captured["headers"]["x-goog-api-key"], "SECRET-KEY")


if __name__ == "__main__":
    unittest.main()