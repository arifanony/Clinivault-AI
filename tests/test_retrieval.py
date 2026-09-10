"""Focused tests for baseline vector storage and similarity retrieval.

Covers exactly what this milestone promised:
- index build from chunk output + embedding artifact (ID-joined)
- chunk<->embedding agreement enforced in both directions (no silent drops)
- duplicate / malformed / dimension-mismatched vectors rejected
- deterministic ranking and deterministic tie-breaking
- top-k validation and behavior
- empty query and query-dimension mismatch rejected
- provenance preserved: results carry chunk_id, document_id, page_number,
  score, and the exact chunk text for the retrieved chunk_id
- provider failures propagate (no second embedding implementation)

No network, no API keys, no paid services: the in-repo baseline hash
provider plus a controlled fake query provider cover every invariant.
"""

from __future__ import annotations

import unittest

from clinivault_ai.chunking import chunk_pages, default_config
from clinivault_ai.embedding import BaselineHashEmbeddingProvider, generate_embeddings
from clinivault_ai.retrieval import RetrievalError, VectorStore, search


def make_chunk_output():
    pages = [
        {
            "page_number": 1,
            "extraction_status": "ok",
            "text": "Alpha diagnostic criteria for diabetes.\n\nBeta glucose testing rules.",
        },
        {
            "page_number": 2,
            "extraction_status": "ok",
            "text": "Gamma gestational diabetes screening.\n\nDelta treatment options.",
        },
    ]
    return chunk_pages(
        {"provenance": {"document_id": "T-200"}, "pages": pages}, default_config()
    )


def make_artifacts():
    chunk_output = make_chunk_output()
    artifact = generate_embeddings(
        chunk_output, BaselineHashEmbeddingProvider(dimension=8)
    )
    return chunk_output, artifact


class ControlledQueryProvider:
    """Returns a fixed vector for any query (ranking is fully controlled)."""

    name = "controlled-query-provider"
    dimension = 8

    def __init__(self, vector):
        self.vector = vector

    def embed_texts(self, texts):
        return [list(self.vector) for _ in texts]


class IndexBuildTests(unittest.TestCase):
    def setUp(self):
        self.chunk_output, self.artifact = make_artifacts()

    def test_index_builds_with_joined_records(self):
        store = VectorStore.from_artifacts(self.artifact, self.chunk_output)
        self.assertEqual(len(store), len(self.chunk_output["chunks"]))
        self.assertEqual(store.document_id, "T-200")
        self.assertEqual(store.dimension, 8)
        chunk_ids = {c["chunk_id"] for c in self.chunk_output["chunks"]}
        record_ids = {r["chunk_id"] for r in store.records}
        self.assertEqual(chunk_ids, record_ids)

    def test_duplicate_embedding_ids_rejected(self):
        self.artifact["embeddings"].append(dict(self.artifact["embeddings"][0]))
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)

    def test_duplicate_chunk_ids_rejected(self):
        self.chunk_output["chunks"].append(dict(self.chunk_output["chunks"][0]))
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)

    def test_missing_embedding_rejected(self):
        self.artifact["embeddings"] = self.artifact["embeddings"][:-1]
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)

    def test_embedding_without_chunk_rejected(self):
        extra = dict(self.artifact["embeddings"][0])
        extra["chunk_id"] = "T-200-p999-c999"
        self.artifact["embeddings"].append(extra)
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)

    def test_document_id_mismatch_rejected(self):
        self.artifact["document_id"] = "OTHER"
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)

    def test_empty_artifacts_rejected(self):
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts({"document_id": "X", "embeddings": []}, self.chunk_output)
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, {"document_id": "X", "chunks": []})

    def test_malformed_vectors_rejected(self):
        for bad in (
            [0.0] * 8,
            ["x"] + [0.0] * 7,
            [float("nan")] + [0.0] * 7,
            [1.0] * 7,
        ):
            tampered = {
                "document_id": "T-200",
                "model": {"name": "m", "dimension": 8},
                "embeddings": [
                    {
                        "chunk_id": c["chunk_id"],
                        "document_id": "T-200",
                        "page_number": c["page_number"],
                        "vector": list(bad),
                    }
                    for c in self.chunk_output["chunks"]
                ],
            }
            with self.assertRaises(RetrievalError):
                VectorStore.from_artifacts(tampered, self.chunk_output)

    def test_embedding_dimension_mismatch_with_model_rejected(self):
        self.artifact["model"]["dimension"] = 16
        with self.assertRaises(RetrievalError):
            VectorStore.from_artifacts(self.artifact, self.chunk_output)


class SearchTests(unittest.TestCase):
    """Query embedding, cosine ranking, tie-breaking, top-k, provenance."""

    def setUp(self):
        chunk_output, artifact = make_artifacts()
        self.store = VectorStore.from_artifacts(artifact, chunk_output)
        self.chunk_map = {c["chunk_id"]: c for c in chunk_output["chunks"]}

    def test_identical_query_vector_ranks_that_chunk_first_with_score_one(self):
        target = self.store.records[0]
        results = search(self.store, "q", ControlledQueryProvider(target["vector"]), 2)
        self.assertEqual(results[0]["chunk_id"], target["chunk_id"])
        self.assertAlmostEqual(results[0]["score"], 1.0, places=9)

    def test_ranking_is_deterministic(self):
        provider = ControlledQueryProvider([1.0, 0, 0, 0, 0, 0, 0, 0])
        first = search(self.store, "diabetes", provider, 2)
        second = search(self.store, "diabetes", provider, 2)
        self.assertEqual(first, second)

    def test_ties_break_deterministically_by_chunk_id(self):
        # All records share the same vector, so all scores tie; the order
        # must then be chunk_id ascending, deterministically.
        records = [
            {
                "chunk_id": f"T-200-p001-c{i:03d}",
                "page_number": 1,
                "text": f"text {i}",
                "vector": [1.0] + [0.0] * 7,
                "norm": 1.0,
            }
            for i in (3, 1, 2)
        ]
        crafted = VectorStore(document_id="T-200", dimension=8, records=records)
        provider = ControlledQueryProvider([0.0, 1.0] + [0.0] * 6)  # orthogonal
        results = search(crafted, "q", provider, 3)
        ids = [r["chunk_id"] for r in results]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len({r["score"] for r in results}), 1)

    def test_score_ordering_descending(self):
        records = [
            {"chunk_id": "T-200-p001-c001", "page_number": 1, "text": "a",
             "vector": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "norm": 1.0},
            {"chunk_id": "T-200-p001-c002", "page_number": 1, "text": "b",
             "vector": [0.6, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
             "norm": (0.36 + 0.64) ** 0.5},
            {"chunk_id": "T-200-p001-c003", "page_number": 1, "text": "c",
             "vector": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "norm": 1.0},
        ]
        crafted = VectorStore(document_id="T-200", dimension=8, records=records)
        provider = ControlledQueryProvider([1.0, 0.0] + [0.0] * 6)
        results = search(crafted, "q", provider, 3)
        self.assertEqual(
            [r["chunk_id"] for r in results],
            ["T-200-p001-c001", "T-200-p001-c002", "T-200-p001-c003"],
        )
        self.assertAlmostEqual(results[0]["score"], 1.0, places=9)
        self.assertAlmostEqual(results[1]["score"], 0.6, places=9)
        self.assertAlmostEqual(results[2]["score"], 0.0, places=9)

    def test_top_k_returns_exactly_k_best(self):
        provider = ControlledQueryProvider([1.0] + [0.0] * 7)
        results = search(self.store, "q", provider, 2)
        self.assertEqual(len(results), 2)
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        full = search(self.store, "q", provider, len(self.store))
        self.assertEqual(results, full[:2])

    def test_top_k_validation(self):
        provider = ControlledQueryProvider([1.0] + [0.0] * 7)
        for bad in (0, -1, True, 2.5, len(self.store) + 1):
            with self.assertRaises(RetrievalError):
                search(self.store, "q", provider, bad)

    def test_empty_query_rejected(self):
        provider = ControlledQueryProvider([1.0] + [0.0] * 7)
        for bad in ("", "   ", None, 42):
            with self.assertRaises(RetrievalError):
                search(self.store, bad, provider, 1)

    def test_query_dimension_mismatch_rejected(self):
        with self.assertRaises(RetrievalError):
            search(self.store, "q", ControlledQueryProvider([1.0] * 7), 1)

    def test_provider_failure_propagates(self):
        class Failing:
            name = "failing"
            dimension = 8

            def embed_texts(self, texts):
                raise RuntimeError("provider down")

        with self.assertRaises(RuntimeError):
            search(self.store, "query text", Failing(), 1)

    def test_results_carry_exact_contract_and_true_text(self):
        provider = ControlledQueryProvider([1.0] + [0.0] * 7)
        results = search(self.store, "diagnostic criteria diabetes", provider, 2)
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(
                set(result.keys()),
                {"chunk_id", "document_id", "page_number", "score", "text"},
            )
            self.assertEqual(result["document_id"], "T-200")
            chunk = self.chunk_map[result["chunk_id"]]
            self.assertEqual(result["text"], chunk["text"])
            self.assertEqual(result["page_number"], chunk["page_number"])
            self.assertTrue(-1.0000001 <= result["score"] <= 1.0000001)
