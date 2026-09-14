"""Tests for baseline end-to-end pipeline execution with trace collection."""

from __future__ import annotations

import json
import unittest

from clinivault_ai.chunking import chunk_pages, default_config
from clinivault_ai.embedding import BaselineHashEmbeddingProvider, generate_embeddings
from clinivault_ai.generation import generate_answer
from clinivault_ai.pipeline import run_query
from clinivault_ai.retrieval import search
from clinivault_ai.retrieval.store import VectorStore


class FakeGenerationProvider:
    name = "fake"
    model = "fake-model-v1"

    def __init__(self):
        self.last_prompt = None
        self.calls = 0

    def generate(self, prompt, timeout=60.0):
        self.calls += 1
        self.last_prompt = prompt
        return {
            "text": "Paris.",
            "usage": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 2,
                "totalTokenCount": 12,
            },
        }


def build_store():
    pages = [
        {
            "page_number": 1,
            "extraction_status": "ok",
            "text": "Alpha the capital city of France is Paris.\n\nBeta more text.",
        },
        {
            "page_number": 2,
            "extraction_status": "ok",
            "text": "Gamma Paris has been the capital since 508 AD.\n\nDelta other.",
        },
    ]
    chunk_output = chunk_pages(
        {"provenance": {"document_id": "T-200"}, "pages": pages}, default_config()
    )
    embedder = BaselineHashEmbeddingProvider(dimension=8)
    artifact = generate_embeddings(chunk_output, embedder)
    store = VectorStore.from_artifacts(artifact, chunk_output)
    return store, embedder


class RunQueryTests(unittest.TestCase):
    def test_end_to_end_trace_collected_and_serializable(self):
        store, embedder = build_store()
        gen = FakeGenerationProvider()
        trace = run_query(store, "capital city of France", embedder, gen, top_k=2)

        # Structure
        self.assertEqual(trace["query"], "capital city of France")
        for key in ("retrieval_trace", "context_trace", "generation_trace", "result"):
            self.assertIn(key, trace)

        # Retrieval trace content
        rt = trace["retrieval_trace"]
        self.assertEqual(rt["top_k"], 2)
        selected = [c["chunk_id"] for c in rt["candidates"] if c["selected"]]
        self.assertEqual(len(selected), 2)

        # Context trace content
        ct = trace["context_trace"]
        self.assertEqual(ct["evidence_count"], 2)
        self.assertEqual([e["rank"] for e in ct["evidence"]], [1, 2])
        self.assertEqual(
            [e["chunk_id"] for e in ct["evidence"]], selected
        )
        self.assertEqual(ct["documents"], [{"document_id": "T-200", "chunk_count": 2, "pages": [1, 2]}])

        # Generation trace content
        gt = trace["generation_trace"]
        self.assertEqual(gt["provider"], "fake")
        self.assertEqual(gt["model"], "fake-model-v1")
        self.assertEqual(gt["status"], "ok")
        self.assertEqual(gt["answer"], "Paris.")
        self.assertTrue(gt["provider_called"])
        self.assertEqual(gt["evidence"], ct["evidence"])
        self.assertIn("capital city of France", gt["prompt_text"])
        self.assertEqual(gt["usage"]["totalTokenCount"], 12)

        # JSON-serializable end to end
        json.dumps(trace)  # must not raise

    def test_stage_behavior_unchanged_vs_direct_calls(self):
        from clinivault_ai.context import build_context

        store, embedder = build_store()
        gen = FakeGenerationProvider()
        query = "capital city of France"

        trace = run_query(store, query, embedder, gen, top_k=2)
        direct_results = search(store, query, embedder, 2)
        direct_bundle = build_context(direct_results, query)
        direct_result = generate_answer(direct_bundle, gen)

        self.assertEqual(trace["result"]["answer"], direct_result["answer"])
        self.assertEqual(trace["context_trace"]["evidence"], direct_bundle["evidence"])
        self.assertEqual(
            [c["chunk_id"] for c in trace["retrieval_trace"]["candidates"] if c["selected"]],
            [r["chunk_id"] for r in direct_results],
        )
        self.assertEqual(trace["result"]["evidence"], direct_bundle["evidence"])


if __name__ == "__main__":
    unittest.main()
