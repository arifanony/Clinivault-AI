"""Offline tests for the evaluation-only controlled-comparison modules.

No network access, no API keys, no real provider calls. The semantic
provider is tested only for its offline validation/configuration surface.
"""

from __future__ import annotations

import unittest

from clinivault_ai.embedding.errors import EmbeddingError
from clinivault_ai.evaluation.termweighted import TermWeightedProvider
from clinivault_ai.evaluation import comparison
from clinivault_ai.evaluation.cases import CASES


class _FakeProvider:
    """Minimal offline EmbeddingProvider for runner tests."""

    name = "fake-provider"
    dimension = 4

    def __init__(self, corpus_texts=None):
        self.corpus_texts = list(corpus_texts or [])

    def embed_texts(self, texts):
        return [[1.0, 0.0, 0.0, 0.0] for _ in texts]

    def provider_params(self):
        return {"method": "fake"}


class TermWeightedProviderTests(unittest.TestCase):
    CORPUS = [
        "glucose thresholds diagnose diabetes",
        "screening recommendations for adults",
        "diabetes diagnosis criteria in adults",
    ]

    def setUp(self):
        self.provider = TermWeightedProvider(self.CORPUS)

    def test_rejects_empty_corpus(self):
        with self.assertRaises(EmbeddingError):
            TermWeightedProvider([])

    def test_rejects_invalid_dimension(self):
        with self.assertRaises(ValueError):
            TermWeightedProvider(self.CORPUS, dimension=0)

    def test_provider_params(self):
        params = self.provider.provider_params()
        self.assertEqual(params["idf"], "1+ln(N/df)")
        self.assertEqual(params["corpus_chunks"], 3)

    def test_rejects_empty_text(self):
        with self.assertRaises(EmbeddingError):
            self.provider.embed_texts([""])

    def test_output_shape_and_norm(self):
        vectors = self.provider.embed_texts(["diabetes diagnosis", "the of the"])
        self.assertEqual(len(vectors), 2)
        for v in vectors:
            self.assertEqual(len(v), 256)
            self.assertAlmostEqual(sum(c * c for c in v), 1.0, places=6)

    def test_deterministic(self):
        a = self.provider.embed_texts(["diabetes diagnosis criteria"])
        b = self.provider.embed_texts(["diabetes diagnosis criteria"])
        self.assertEqual(a, b)

    def test_implements_provider_seam(self):
        from clinivault_ai.embedding.provider import EmbeddingProvider

        # EmbeddingProvider is a structural protocol (not runtime_checkable).
        # Assert the surface actually consumed by generate_embeddings()/the
        # comparison runner: name, dimension, batch embed_texts, params.
        for attr in ("name", "dimension", "embed_texts", "provider_params"):
            self.assertTrue(hasattr(self.provider, attr), attr)

    def test_weighting_reduces_common_tokens(self):
        # Purpose-built corpus: "the" in every chunk, "glucose" in two of
        # three. weight = 1+ln(N/df), so the informative token must win.
        p = TermWeightedProvider(
            ["the patient the", "the glucose level", "glucose the test"]
        )
        self.assertGreaterEqual(p._weight("the"), 1.0)
        self.assertGreater(p._weight("glucose"), p._weight("the"))


class ComparisonRunnerTests(unittest.TestCase):
    """Runner behavior with a fake provider over the frozen cases."""

    def test_run_with_fake_provider_shape(self):
        result = comparison.run_with_provider(
            cases=tuple(list(CASES)[:2]),
            provider_factory=lambda doc, texts: _FakeProvider(texts),
            top_k=5,
        )
        self.assertEqual(result["n_cases"], 2)
        for record in result["per_case"]:
            self.assertIn("case_id", record)
            self.assertIn("first_relevant_rank", record)
            self.assertEqual(len(record["top5"]), 5)
            self.assertEqual(len(record["top5_scores"]), 5)

    def test_missing_rank_triggers_full_rank_recalc(self):
        result = comparison.run_with_provider(
            cases=tuple(c for c in CASES if c.case_id == "T2D-009-statins"),
            provider_factory=lambda doc, texts: _FakeProvider(texts),
            top_k=5,
        )
        record = result["per_case"][0]
        # The fake provider produces identical vectors, so relevant evidence
        # cannot be in the top-5; the runner must record full-corpus ranks.
        self.assertIn("full_rank_of_expected", record)

    def test_ambiguity_flag_preserved(self):
        result = comparison.run_with_provider(
            cases=tuple(c for c in CASES if c.ambiguous)[:1],
            provider_factory=lambda doc, texts: _FakeProvider(texts),
            top_k=5,
        )
        self.assertTrue(result["per_case"][0]["ambiguous"])


class SemanticProviderOfflineTests(unittest.TestCase):
    """Only the offline surface of the semantic provider is tested."""

    def test_missing_key_rejected_without_network(self):
        import os
        from unittest.mock import patch

        from clinivault_ai.evaluation.semantic import GeminiEmbeddingProvider

        with patch.dict(os.environ, {}, clear=True), \
                patch("clinivault_ai.evaluation.semantic.Path") as p:
            p.return_value.is_file.return_value = False
            with self.assertRaises(EmbeddingError):
                GeminiEmbeddingProvider(api_key=None)

    def test_invalid_batch_size_rejected(self):
        from clinivault_ai.evaluation.semantic import GeminiEmbeddingProvider

        with self.assertRaises(EmbeddingError):
            GeminiEmbeddingProvider(api_key="dummy", batch_size=0)

    def test_params_record_model_identity(self):
        from clinivault_ai.evaluation.semantic import GeminiEmbeddingProvider

        provider = GeminiEmbeddingProvider(api_key="dummy")
        params = provider.provider_params()
        self.assertEqual(params["model"], "models/gemini-embedding-001")
        self.assertEqual(params["task_types"]["queries"], "RETRIEVAL_QUERY")
        self.assertEqual(provider.dimension, 3072)

    def test_rejects_empty_text(self):
        from clinivault_ai.evaluation.semantic import GeminiEmbeddingProvider

        provider = GeminiEmbeddingProvider(api_key="dummy")
        with self.assertRaises(EmbeddingError):
            provider.embed_query("")


if __name__ == "__main__":
    unittest.main()
