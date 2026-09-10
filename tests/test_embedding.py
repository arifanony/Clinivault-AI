"""Focused tests for baseline embedding generation (embedding package).

Covers exactly what this milestone promised:
- one embedding per input chunk; chunk identity preserved exactly
- record order is deterministic and matches chunk order
- model identity (name, dimension, params) is recorded
- vector dimensionality is validated consistently
- malformed / non-finite / all-zero / wrong-count responses fail clearly
- empty input text fails instead of producing a zero-signal vector
- provider failures raise without silently dropping records
- the baseline hash provider is deterministic and L2-normalized

No network access and no paid API calls: a local fake provider plus the
in-repo BaselineHashEmbeddingProvider cover every invariant.
"""

from __future__ import annotations

import math
import unittest

from clinivault_ai.chunking import chunk_pages, default_config
from clinivault_ai.embedding import (
    BaselineHashEmbeddingProvider,
    EmbeddingError,
    generate_embeddings,
)


def make_chunks(n_pages: int = 2):
    pages = [
        {
            "page_number": number,
            "extraction_status": "ok",
            "text": f"Page {number} alpha text about diabetes.\n\nPage {number} beta text.",
        }
        for number in range(1, n_pages + 1)
    ]
    return chunk_pages(
        {"provenance": {"document_id": "T-100"}, "pages": pages}, default_config()
    )


class FakeProvider:
    """Deterministic fake: vector encodes text length and index position."""

    name = "fake-provider-v1"
    dimension = 8

    def __init__(self, fail=False, vectors=None):
        self.fail = fail
        self.vectors = vectors

    def embed_texts(self, texts):
        if self.fail:
            raise RuntimeError("provider unavailable")
        if self.vectors is not None:
            return self.vectors
        return [[float(len(text) % 7 + 1)] + [0.0] * (self.dimension - 1)
                for text in texts]


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.chunk_output = make_chunks()

    def test_one_embedding_per_chunk_identity_preserved_in_order(self):
        artifact = generate_embeddings(self.chunk_output, FakeProvider())
        chunks = self.chunk_output["chunks"]
        self.assertEqual(artifact["statistics"]["embedding_count"], len(chunks))
        self.assertEqual(len(artifact["embeddings"]), len(chunks))
        for record, chunk in zip(artifact["embeddings"], chunks):
            self.assertEqual(record["chunk_id"], chunk["chunk_id"])
            self.assertEqual(record["document_id"], chunk["document_id"])
            self.assertEqual(record["page_number"], chunk["page_number"])
        ids = [r["chunk_id"] for r in artifact["embeddings"]]
        self.assertEqual(len(ids), len(set(ids)), "chunk ids must be unique")

    def test_deterministic_ordering_and_repeat_calls(self):
        first = generate_embeddings(self.chunk_output, FakeProvider())
        second = generate_embeddings(self.chunk_output, FakeProvider())
        self.assertEqual(first, second)

    def test_model_identity_is_recorded(self):
        artifact = generate_embeddings(self.chunk_output, FakeProvider())
        self.assertEqual(artifact["model"]["name"], "fake-provider-v1")
        self.assertEqual(artifact["model"]["dimension"], 8)
        self.assertEqual(artifact["document_id"], "T-100")
        self.assertEqual(artifact["statistics"]["dimension"], 8)

    def test_baseline_provider_params_are_recorded(self):
        artifact = generate_embeddings(self.chunk_output)
        self.assertEqual(artifact["model"]["name"], "clinivault-baseline-hash-v1")
        self.assertEqual(artifact["model"]["dimension"], 256)
        self.assertEqual(artifact["model"]["method"], "hashed-bag-of-words")
        self.assertEqual(artifact["model"]["norm"], "l2")

    def test_no_chunk_text_in_embedding_records(self):
        artifact = generate_embeddings(self.chunk_output, FakeProvider())
        for record in artifact["embeddings"]:
            self.assertEqual(
                set(record.keys()), {"chunk_id", "document_id", "page_number", "vector"}
            )


class MalformedResponseTests(unittest.TestCase):
    """Every malformed response must fail clearly with no partial artifact."""

    def setUp(self):
        self.chunk_output = make_chunks()
        self.ok_vector = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    def assert_embedding_error(self, vectors, message_part=None):
        with self.assertRaises(EmbeddingError) as ctx:
            generate_embeddings(
                self.chunk_output, FakeProvider(vectors=vectors)
            )
        if message_part:
            self.assertIn(message_part, str(ctx.exception))

    def test_wrong_dimension_fails(self):
        self.assert_embedding_error(
            [self.ok_vector[:7]] * 2, "expected dimension 8"
        )

    def test_non_numeric_value_fails(self):
        bad = list(self.ok_vector)
        bad[3] = "x"
        self.assert_embedding_error([bad] * 2, "non-numeric")

    def test_non_finite_value_fails(self):
        bad = list(self.ok_vector)
        bad[3] = float("nan")
        self.assert_embedding_error([bad] * 2, "non-finite")

    def test_all_zero_vector_fails(self):
        zeros = [0.0] * 8
        self.assert_embedding_error([zeros] * 2, "all-zero")

    def test_count_mismatch_fails(self):
        self.assert_embedding_error(
            [self.ok_vector] * 3, "refusing to drop or pad"
        )

    def test_non_list_response_fails(self):
        provider = FakeProvider()
        provider.embed_texts = lambda texts: "not-a-list"
        with self.assertRaises(EmbeddingError):
            generate_embeddings(self.chunk_output, provider)

    def test_provider_failure_raises_without_partial_output(self):
        with self.assertRaises(RuntimeError):
            generate_embeddings(self.chunk_output, FakeProvider(fail=True))

    def test_empty_text_fails_in_baseline_provider(self):
        provider = BaselineHashEmbeddingProvider()
        with self.assertRaises(EmbeddingError):
            provider.embed_texts(["   "])

    def test_document_id_mismatch_fails(self):
        tampered = make_chunks()
        tampered["chunks"][0]["document_id"] = "OTHER"
        with self.assertRaises(EmbeddingError):
            generate_embeddings(tampered, FakeProvider())

    def test_no_chunks_fails(self):
        with self.assertRaises(EmbeddingError):
            generate_embeddings({"document_id": "T-100", "chunks": []}, FakeProvider())


class BaselineHashProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = BaselineHashEmbeddingProvider(dimension=64)

    def test_deterministic_across_calls(self):
        texts = ["alpha beta gamma about diabetes", "delta epsilon zeta"]
        self.assertEqual(
            self.provider.embed_texts(texts), self.provider.embed_texts(texts)
        )

    def test_vectors_are_l2_normalized_and_right_dimension(self):
        vectors = self.provider.embed_texts(["alpha beta gamma", "alpha"])
        for vector in vectors:
            self.assertEqual(len(vector), 64)
            norm = math.sqrt(sum(v * v for v in vector))
            self.assertAlmostEqual(norm, 1.0, places=9)

    def test_same_text_same_vector_different_text_different(self):
        vectors = self.provider.embed_texts(
            ["identical text", "identical text", "different content"]
        )
        self.assertEqual(vectors[0], vectors[1])
        self.assertNotEqual(vectors[0], vectors[2])


class EndToEndWithRealChunkerTests(unittest.TestCase):
    def test_chunk_output_to_embedding_artifact(self):
        chunk_output = make_chunks()
        artifact = generate_embeddings(chunk_output)
        chunk_ids = [c["chunk_id"] for c in chunk_output["chunks"]]
        embedding_ids = [r["chunk_id"] for r in artifact["embeddings"]]
        self.assertEqual(embedding_ids, chunk_ids)
        self.assertEqual(set(embedding_ids), set(chunk_ids))
        dimensions = {len(r["vector"]) for r in artifact["embeddings"]}
        self.assertEqual(dimensions, {artifact["model"]["dimension"]})


if __name__ == "__main__":
    unittest.main()
