"""E5 production provider tests (DECISION-017).

Always-on tests do not load the local model. Encode/reproduction tests
skip unless sentence-transformers and the cached model files are present.
"""

from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from clinivault_ai.embedding import E5_INPUT_FORMATTING, E5_MODEL_NAME, EmbeddingError
from clinivault_ai.embedding.provider import E5_EXPECTED_DIMENSION, E5EmbeddingProvider

REPO = Path(__file__).resolve().parents[1]
E5_T2D001 = (
    REPO / "data" / "embedded-intfloat--e5-small-v2" / "stage-1-clean-baseline-corpus"
    / "T2D-001" / "T2D-001.embeddings.json"
)
PARSED_T2D001 = (
    REPO / "data" / "parsed" / "stage-1-clean-baseline-corpus"
    / "T2D-001" / "T2D-001.parsed.json"
)


def _sentence_transformers_installed() -> bool:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


def _e5_model_loadable() -> bool:
    if not _sentence_transformers_installed():
        return False
    try:
        E5EmbeddingProvider()
    except EmbeddingError:
        return False
    return True


class E5ProviderContractTests(unittest.TestCase):
    def test_raw_input_formatting_constant(self):
        self.assertEqual(E5_INPUT_FORMATTING, "raw")
        self.assertEqual(E5_MODEL_NAME, "intfloat/e5-small-v2")
        self.assertEqual(E5EmbeddingProvider.name, E5_MODEL_NAME)

    def test_missing_extra_message_mentions_uv_sync(self):
        if _sentence_transformers_installed():
            self.skipTest("sentence-transformers is installed")
        with self.assertRaises(EmbeddingError) as ctx:
            E5EmbeddingProvider()
        self.assertIn("uv sync --extra semantic", str(ctx.exception))


@unittest.skipUnless(_e5_model_loadable(), "local intfloat/e5-small-v2 not available")
class E5ProviderLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = E5EmbeddingProvider()

    def test_empty_text_fails(self):
        with self.assertRaises(EmbeddingError):
            self.provider.embed_texts(["   "])

    def test_params_are_raw(self):
        params = self.provider.provider_params()
        self.assertEqual(params["input_formatting"], "raw")
        self.assertEqual(params["query_prefix"], "")
        self.assertEqual(params["passage_prefix"], "")
        self.assertEqual(params["model"], E5_MODEL_NAME)

    def test_encode_one_string_384d_finite_nonzero(self):
        vectors = self.provider.embed_texts(["diagnostic criteria for type 2 diabetes"])
        self.assertEqual(len(vectors), 1)
        self.assertEqual(len(vectors[0]), E5_EXPECTED_DIMENSION)
        self.assertTrue(all(math.isfinite(v) for v in vectors[0]))
        self.assertFalse(all(v == 0.0 for v in vectors[0]))

    def test_t2d001_first_chunk_matches_committed_artifact(self):
        from clinivault_ai.chunking import chunk_pages, default_config

        parsed = json.loads(PARSED_T2D001.read_text(encoding="utf-8"))
        chunks = chunk_pages(parsed, default_config())["chunks"]
        artifact = json.loads(E5_T2D001.read_text(encoding="utf-8"))
        first_chunk = chunks[0]
        first_record = artifact["embeddings"][0]
        self.assertEqual(first_chunk["chunk_id"], first_record["chunk_id"])
        encoded = self.provider.embed_texts([first_chunk["text"]])[0]
        self.assertEqual(encoded, first_record["vector"])


if __name__ == "__main__":
    unittest.main()
