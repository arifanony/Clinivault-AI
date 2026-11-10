"""M5: answer reliability (DECISION-020).

Covers, with fake providers only (no network, no API keys):

- citation parsing: EVIDENCE_ITEM_RANK / EVIDENCE_ITEM_CHUNK_ID refs in
  the answer are checked against the evidence; misses land on
  result["invalid_citations"]
- abstention sentinel: an answer starting with "ABSTAIN:" (evidence
  present but the model refuses) returns status "abstained"
- context budget: build_context(..., max_chars=...) drops the
  lowest-rank tail and records truncated_chunk_ids; rank 1 is always kept
- Gemini retry: 429/5xx are retried (attempts recorded); 401/403 raise
  immediately; parse errors are not retried
- tiny labeled set: in-scope supported, DECISION-005 out-of-scope
  refusal, and empty evidence; metrics are citation validity and
  abstention correctness
"""

from __future__ import annotations

import unittest
import urllib.error

from clinivault_ai.generation.errors import GenerationError


def _retrieval_results():
    return [
        {"chunk_id": "T-200-c1", "document_id": "T-200", "page_number": 1,
         "score": 0.9, "text": "Alpha the capital city of France is Paris."},
        {"chunk_id": "T-200-c2", "document_id": "T-200", "page_number": 2,
         "score": 0.7, "text": "Beta Paris has been the capital since 508 AD."},
        {"chunk_id": "T-200-c3", "document_id": "T-200", "page_number": 2,
         "score": 0.5, "text": "Gamma other supporting text about Paris."},
    ]


def _bundle(query="What is the capital of France?", n_evidence=3):
    from clinivault_ai.context import build_context

    return build_context(_retrieval_results()[:n_evidence], query)


class ScriptedProvider:
    """Fake generation provider returning a canned answer."""

    name = "fake"
    model = "fake-model-v1"

    def __init__(self, answer):
        self._answer = answer
        self.calls = 0
        self.last_prompt = None

    def generate(self, prompt, timeout=60.0):
        self.calls += 1
        self.last_prompt = prompt
        return {"text": self._answer}


class CitationParsingTests(unittest.TestCase):
    def test_valid_rank_and_chunk_refs_parse_clean(self):
        from clinivault_ai.generation import generate_answer

        bundle = _bundle()
        answer = ("Paris (EVIDENCE_ITEM_RANK: 1, "
                  "EVIDENCE_ITEM_CHUNK_ID: T-200-c1).")
        result = generate_answer(bundle, ScriptedProvider(answer))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["invalid_citations"], [])

    def test_unknown_rank_is_invalid(self):
        from clinivault_ai.generation import generate_answer

        bundle = _bundle()
        result = generate_answer(
            bundle, ScriptedProvider("Paris (EVIDENCE_ITEM_RANK: 9)."))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["invalid_citations"],
            [{"kind": "rank", "value": 9}],
        )

    def test_rank_zero_is_invalid(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            _bundle(), ScriptedProvider("x (EVIDENCE_ITEM_RANK: 0)."))
        self.assertEqual(
            result["invalid_citations"],
            [{"kind": "rank", "value": 0}],
        )

    def test_unknown_chunk_id_is_invalid(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            _bundle(),
            ScriptedProvider("x (EVIDENCE_ITEM_CHUNK_ID: T-200-c999)."),
        )
        self.assertEqual(
            result["invalid_citations"],
            [{"kind": "chunk_id", "value": "T-200-c999"}],
        )

    def test_answer_without_refs_has_no_invalid_citations(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(_bundle(), ScriptedProvider("Paris."))
        self.assertEqual(result["invalid_citations"], [])

    def test_refs_from_all_evidence_positions_validate(self):
        from clinivault_ai.generation import generate_answer

        answer = ("a (EVIDENCE_ITEM_RANK: 1) "
                  "b (EVIDENCE_ITEM_RANK: 2) "
                  "c (EVIDENCE_ITEM_CHUNK_ID: T-200-c3).")
        result = generate_answer(_bundle(), ScriptedProvider(answer))
        self.assertEqual(result["invalid_citations"], [])

    def test_parse_helper_round_trip(self):
        from clinivault_ai.generation.citations import (
            parse_citation_refs,
            validate_citation_refs,
        )

        bundle = _bundle()
        refs = parse_citation_refs(
            "a (EVIDENCE_ITEM_RANK: 2, EVIDENCE_ITEM_CHUNK_ID: T-200-c2).")
        self.assertEqual(refs["ranks"], [2])
        self.assertEqual(refs["chunk_ids"], ["T-200-c2"])
        self.assertEqual(
            validate_citation_refs(refs, bundle["evidence"]), [])


class AbstentionSentinelTests(unittest.TestCase):
    def test_abstain_prefix_yields_abstained_status(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            _bundle(),
            ScriptedProvider("ABSTAIN: the evidence does not cover this."),
        )
        self.assertEqual(result["status"], "abstained")
        self.assertTrue(result["answer"].startswith("ABSTAIN:"))

    def test_abstain_counts_as_abstained_in_execution_record(self):
        from clinivault_ai.generation import generate_answer
        from clinivault_ai.pipeline.records import build_execution_record

        bundle = _bundle()
        result = generate_answer(
            bundle, ScriptedProvider("ABSTAIN: out of scope."))
        record = build_execution_record(
            query="q", top_k=5, results=_retrieval_results(),
            bundle=bundle, result=result,
        )
        self.assertEqual(record["generation"]["status"], "abstained")
        self.assertTrue(record["generation"]["abstained"])

    def test_lowercase_abstain_is_not_a_sentinel(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            _bundle(), ScriptedProvider("abstain: not really."))
        self.assertEqual(result["status"], "ok")

    def test_abstain_mid_answer_is_not_a_sentinel(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            _bundle(), ScriptedProvider("Paris. ABSTAIN: trailing."))
        self.assertEqual(result["status"], "ok")

    def test_empty_evidence_still_no_evidence(self):
        from clinivault_ai.context import build_context
        from clinivault_ai.generation import generate_answer

        provider = ScriptedProvider("ABSTAIN: never called")
        result = generate_answer(
            build_context([], "empty question"), provider)
        self.assertEqual(result["status"], "no_evidence")
        self.assertIsNone(result["answer"])
        self.assertEqual(provider.calls, 0)


class GenerationAttemptsTests(unittest.TestCase):
    def test_fake_provider_without_attempts_defaults_to_one(self):
        from clinivault_ai.generation import generate_answer

        result = generate_answer(_bundle(), ScriptedProvider("Paris."))
        self.assertEqual(result["attempts"], 1)

    def test_no_evidence_records_zero_attempts(self):
        from clinivault_ai.context import build_context
        from clinivault_ai.generation import generate_answer

        result = generate_answer(
            build_context([], "q"), ScriptedProvider("unused"))
        self.assertEqual(result["attempts"], 0)


class ContextBudgetTests(unittest.TestCase):
    def test_default_keeps_everything(self):
        from clinivault_ai.context import build_context

        bundle = build_context(_retrieval_results(), "q")
        self.assertEqual(bundle["evidence_count"], 3)
        self.assertEqual(bundle["truncated_chunk_ids"], [])

    def test_tail_is_dropped_and_recorded(self):
        from clinivault_ai.context import build_context

        results = _retrieval_results()
        budget = len(results[0]["text"]) + len(results[1]["text"])
        trace: dict = {}
        bundle = build_context(results, "q", trace=trace, max_chars=budget)
        self.assertEqual(
            [e["chunk_id"] for e in bundle["evidence"]],
            ["T-200-c1", "T-200-c2"],
        )
        self.assertEqual(bundle["truncated_chunk_ids"], ["T-200-c3"])
        self.assertEqual(trace["truncated_chunk_ids"], ["T-200-c3"])
        self.assertEqual(trace["max_chars"], budget)

    def test_rank_one_survives_a_tiny_budget(self):
        from clinivault_ai.context import build_context

        bundle = build_context(_retrieval_results(), "q", max_chars=1)
        self.assertEqual(
            [e["chunk_id"] for e in bundle["evidence"]], ["T-200-c1"])
        self.assertEqual(
            bundle["truncated_chunk_ids"], ["T-200-c2", "T-200-c3"])

    def test_trace_reports_budget_when_nothing_truncated(self):
        from clinivault_ai.context import build_context

        trace: dict = {}
        build_context(_retrieval_results(), "q", trace=trace, max_chars=10**6)
        self.assertEqual(trace["truncated_chunk_ids"], [])
        self.assertEqual(trace["max_chars"], 10**6)

    def test_rejected_budgets(self):
        from clinivault_ai.context import build_context
        from clinivault_ai.context.errors import ContextError

        for bad in (0, -5, "100", 10.5, True):
            with self.assertRaises(ContextError, msg=f"max_chars={bad!r}"):
                build_context(_retrieval_results(), "q", max_chars=bad)

    def test_truncation_reaches_the_execution_record(self):
        from clinivault_ai.context import build_context
        from clinivault_ai.generation import generate_answer
        from clinivault_ai.pipeline.records import build_execution_record

        results = _retrieval_results()
        budget = len(results[0]["text"])
        bundle = build_context(results, "q", max_chars=budget)
        result = generate_answer(bundle, ScriptedProvider("Paris."))
        record = build_execution_record(
            query="q", top_k=5, results=results,
            bundle=bundle, result=result,
        )
        self.assertEqual(record["context"]["truncated_chunk_ids"],
                         ["T-200-c2", "T-200-c3"])
        self.assertEqual(record["context"]["chunk_ids_used"], ["T-200-c1"])


class GeminiRetryTests(unittest.TestCase):
    def _script_urlopen(self, script):
        import io
        import json
        from unittest.mock import patch

        import clinivault_ai.generation.provider as provider_mod

        calls = []

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout):
            calls.append(req)
            action = script[len(calls) - 1]
            if isinstance(action, Exception):
                raise action
            body = {"candidates": [{"content": {"parts": [{"text": action}]}}]}
            return FakeResponse(json.dumps(body).encode("utf-8"))

        return patch.object(provider_mod.urllib.request, "urlopen",
                            side_effect=fake_urlopen), calls

    @staticmethod
    def _http_error(code):
        return urllib.error.HTTPError("http://gemini.invalid", code,
                                      "error", {}, None)

    def test_first_try_success_records_one_attempt(self):
        from clinivault_ai.generation.provider import GeminiProvider

        patcher, calls = self._script_urlopen(["ok"])
        with patcher:
            out = GeminiProvider(api_key="K", retry_backoff_s=0).generate("hi")
        self.assertEqual(out["text"], "ok")
        self.assertEqual(out["attempts"], 1)
        self.assertEqual(len(calls), 1)

    def test_rate_limit_then_success(self):
        from clinivault_ai.generation.provider import GeminiProvider

        patcher, calls = self._script_urlopen(
            [self._http_error(429), "recovered"])
        with patcher:
            out = GeminiProvider(api_key="K", retry_backoff_s=0).generate("hi")
        self.assertEqual(out["text"], "recovered")
        self.assertEqual(out["attempts"], 2)
        self.assertEqual(len(calls), 2)

    def test_server_errors_exhaust_retries_then_raise(self):
        from clinivault_ai.generation.provider import GeminiProvider

        script = [self._http_error(500), self._http_error(503),
                  self._http_error(500)]
        patcher, calls = self._script_urlopen(script)
        provider = GeminiProvider(api_key="K", retry_backoff_s=0,
                                  max_attempts=3)
        with patcher:
            with self.assertRaises(GenerationError) as ctx:
                provider.generate("hi")
        self.assertEqual(len(calls), 3)
        self.assertEqual(getattr(ctx.exception, "attempts", None), 3)

    def test_forbidden_never_retries(self):
        from clinivault_ai.generation.provider import GeminiProvider

        patcher, calls = self._script_urlopen([self._http_error(403)])
        with patcher:
            with self.assertRaises(GenerationError) as ctx:
                GeminiProvider(api_key="K", retry_backoff_s=0).generate("hi")
        self.assertEqual(len(calls), 1)
        self.assertEqual(getattr(ctx.exception, "attempts", None), 1)

    def test_unauthorized_never_retries(self):
        from clinivault_ai.generation.provider import GeminiProvider

        patcher, calls = self._script_urlopen([self._http_error(401)])
        with patcher:
            with self.assertRaises(GenerationError):
                GeminiProvider(api_key="K", retry_backoff_s=0).generate("hi")
        self.assertEqual(len(calls), 1)

    def test_malformed_response_is_not_retried(self):
        import io
        from unittest.mock import patch

        import clinivault_ai.generation.provider as provider_mod
        from clinivault_ai.generation.provider import GeminiProvider

        calls = []

        class FakeResponse(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def fake_urlopen(req, timeout):
            calls.append(req)
            return FakeResponse(b"not json")

        with patch.object(provider_mod.urllib.request, "urlopen",
                          side_effect=fake_urlopen):
            with self.assertRaises(GenerationError):
                GeminiProvider(api_key="K", retry_backoff_s=0).generate("hi")
        self.assertEqual(len(calls), 1)

    def test_rejected_retry_config(self):
        from clinivault_ai.generation.provider import GeminiProvider

        for kwargs in ({"max_attempts": 0}, {"max_attempts": -2},
                       {"max_attempts": "3"}, {"retry_backoff_s": -1.0}):
            with self.assertRaises(GenerationError, msg=str(kwargs)):
                GeminiProvider(api_key="K", **kwargs)


LABELED_CASES = [
    {
        "name": "in-scope supported answer",
        "query": "What is the capital city of France?",
        "scope": "in_scope",
        "n_evidence": 2,
        "answer": ("Paris (EVIDENCE_ITEM_RANK: 1, "
                   "EVIDENCE_ITEM_CHUNK_ID: T-200-c1)."),
        "expect_status": "ok",
        "expect_abstained": False,
        "expect_citations_valid": True,
    },
    {
        "name": "out-of-scope refusal (DECISION-005: Type 1 Diabetes)",
        "query": "How is Type 1 Diabetes diagnosed in children?",
        "scope": "out_of_scope",
        "n_evidence": 2,
        "answer": ("ABSTAIN: Type 1 Diabetes is outside the Type 2 "
                   "Diabetes MVP scope (DECISION-005)."),
        "expect_status": "abstained",
        "expect_abstained": True,
        "expect_citations_valid": True,
    },
    {
        "name": "empty evidence",
        "query": "What is the capital city of France?",
        "scope": "in_scope",
        "n_evidence": 0,
        "answer": None,
        "expect_status": "no_evidence",
        "expect_abstained": True,
        "expect_citations_valid": True,
    },
]


class LabeledReliabilitySetTests(unittest.TestCase):
    """Tiny labeled reliability set: citation validity + abstention."""

    def _run_case(self, case):
        from clinivault_ai.context import build_context
        from clinivault_ai.generation import generate_answer
        from clinivault_ai.pipeline.records import build_execution_record

        results = _retrieval_results()[:case["n_evidence"]]
        bundle = build_context(results, case["query"])
        provider = ScriptedProvider(case["answer"])
        result = generate_answer(bundle, provider)
        record = build_execution_record(
            query=case["query"], top_k=5, results=results,
            bundle=bundle, result=result,
        )
        return result, record, provider

    def test_every_labeled_case_behaves_as_labeled(self):
        for case in LABELED_CASES:
            with self.subTest(case["name"]):
                result, record, _ = self._run_case(case)
                self.assertEqual(result["status"], case["expect_status"])
                self.assertEqual(record["generation"]["abstained"],
                                 case["expect_abstained"])

    def test_citation_validity_metric_is_perfect(self):
        from clinivault_ai.generation import generate_answer

        scored = 0
        for case in LABELED_CASES:
            if case["n_evidence"] == 0:
                continue
            results = _retrieval_results()[:case["n_evidence"]]
            from clinivault_ai.context import build_context

            bundle = build_context(results, case["query"])
            result = generate_answer(bundle, ScriptedProvider(case["answer"]))
            self.assertEqual(result["invalid_citations"], [])
            scored += 1
        self.assertGreater(scored, 0)

    def test_abstention_correctness_metric_is_perfect(self):
        correct = 0
        for case in LABELED_CASES:
            _, record, _ = self._run_case(case)
            if record["generation"]["abstained"] == case["expect_abstained"]:
                correct += 1
        self.assertEqual(correct, len(LABELED_CASES))

    def test_empty_evidence_never_calls_the_provider(self):
        _, _, provider = self._run_case(
            [c for c in LABELED_CASES if c["n_evidence"] == 0][0])
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
