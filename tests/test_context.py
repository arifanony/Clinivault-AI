"""Focused tests for baseline context construction (evidence bundling).

Covers exactly what this milestone promised:
- retrieval order preserved; explicit 1-based rank
- all provenance fields preserved verbatim (ids, page, score, text)
- chunk text never discarded or altered
- multiple documents represented without provenance collisions
- empty retrieval results produce an explicit empty bundle
- malformed retrieval input fails clearly (no misleading context)
- end-to-end: retrieval search results package into a valid bundle

Deterministic synthetic retrieval results; the end-to-end test uses the
real retrieval layer with the in-repo baseline provider. No network.
"""

from __future__ import annotations

import unittest

from clinivault_ai.context import ContextError, build_context


def result(n: int, document_id: str = "D-1", page: int | None = None,
           score: float | None = None) -> dict:
    return {
        "chunk_id": f"{document_id}-p{page or n:03d}-c{n:03d}",
        "document_id": document_id,
        "page_number": page if page is not None else n,
        "score": score if score is not None else 1.0 / (n + 1),
        "text": f"evidence text {n}",
    }


class BuildContextTests(unittest.TestCase):
    def test_order_preserved_and_rank_explicit(self):
        bundle = build_context([result(3), result(1), result(2)])
        self.assertEqual([e["rank"] for e in bundle["evidence"]], [1, 2, 3])
        self.assertEqual(
            [e["text"] for e in bundle["evidence"]],
            ["evidence text 3", "evidence text 1", "evidence text 2"],
        )
        self.assertEqual(bundle["evidence_count"], 3)

    def test_provenance_preserved_verbatim(self):
        item = result(1, page=7, score=0.42)
        bundle = build_context([item])
        entry = bundle["evidence"][0]
        self.assertEqual(entry["chunk_id"], item["chunk_id"])
        self.assertEqual(entry["document_id"], "D-1")
        self.assertEqual(entry["page_number"], 7)
        self.assertEqual(entry["score"], 0.42)
        self.assertEqual(entry["text"], item["text"])

    def test_chunk_text_not_discarded_or_altered(self):
        texts = ["Alpha diagnostic criteria text.", "Beta glucose rules.\n\nMore."]
        results = [
            {"chunk_id": f"D-1-p001-c{i}", "document_id": "D-1",
             "page_number": 1, "score": 0.5, "text": text}
            for i, text in enumerate(texts, 1)
        ]
        bundle = build_context(results)
        self.assertEqual([e["text"] for e in bundle["evidence"]], texts)

    def test_multiple_documents_no_provenance_collisions(self):
        results = [
            result(1, document_id="D-1", page=2, score=0.9),
            result(2, document_id="D-2", page=5, score=0.8),
            result(3, document_id="D-1", page=3, score=0.7),
        ]
        bundle = build_context(results)
        docs = {d["document_id"]: d for d in bundle["documents"]}
        self.assertEqual(docs["D-1"]["chunk_count"], 2)
        self.assertEqual(docs["D-1"]["pages"], [2, 3])
        self.assertEqual(docs["D-2"]["chunk_count"], 1)
        self.assertEqual(docs["D-2"]["pages"], [5])
        # evidence items keep their own document identity
        self.assertEqual(
            [(e["document_id"], e["page_number"]) for e in bundle["evidence"]],
            [("D-1", 2), ("D-2", 5), ("D-1", 3)],
        )

    def test_query_recorded_and_optional(self):
        self.assertEqual(build_context([], query="why?")["query"], "why?")
        self.assertIsNone(build_context([])["query"])

    def test_empty_results_explicit_empty_bundle(self):
        bundle = build_context([])
        self.assertEqual(bundle["evidence_count"], 0)
        self.assertEqual(bundle["evidence"], [])
        self.assertEqual(bundle["documents"], [])


class MalformedInputTests(unittest.TestCase):
    def test_non_list_results_rejected(self):
        with self.assertRaises(ContextError):
            build_context("not-a-list")

    def test_non_dict_item_rejected(self):
        with self.assertRaises(ContextError):
            build_context([result(1), "junk"])

    def test_missing_field_rejected(self):
        broken = result(1)
        del broken["score"]
        with self.assertRaises(ContextError):
            build_context([broken])

    def test_invalid_types_rejected(self):
        for mutate in (
            lambda r: r.update(chunk_id=""),
            lambda r: r.update(page_number="2"),
            lambda r: r.update(score="high"),
            lambda r: r.update(text=None),
        ):
            with self.assertRaises(ContextError):
                build_context([result(1, score=0.5), mutate(dict(result(2), score=0.4))])

    def test_duplicate_chunk_ids_rejected(self):
        with self.assertRaises(ContextError):
            build_context([result(1), result(1)])


class EndToEndTests(unittest.TestCase):
    """Real retrieval results -> context bundle, via the real pipeline."""

    def test_search_results_build_into_bundle(self):
        from clinivault_ai.chunking import chunk_pages, default_config
        from clinivault_ai.embedding import BaselineHashEmbeddingProvider
        from clinivault_ai.embedding import generate_embeddings
        from clinivault_ai.retrieval import VectorStore, search

        pages = [
            {"page_number": 1, "extraction_status": "ok",
             "text": "Alpha diagnostic criteria for diabetes.\n\nBeta glucose testing."},
            {"page_number": 2, "extraction_status": "ok",
             "text": "Gamma gestational diabetes screening rules."},
        ]
        chunk_output = chunk_pages(
            {"provenance": {"document_id": "T-300"}, "pages": pages}, default_config()
        )
        artifact = generate_embeddings(
            chunk_output, BaselineHashEmbeddingProvider(dimension=8)
        )
        store = VectorStore.from_artifacts(artifact, chunk_output)
        provider = BaselineHashEmbeddingProvider(dimension=8)
        results = search(store, "diabetes", provider, 2)
        self.assertTrue(results)

        bundle = build_context(results, query="diabetes")
        self.assertEqual(bundle["query"], "diabetes")
        self.assertEqual(bundle["evidence_count"], len(results))
        chunk_map = {c["chunk_id"]: c for c in chunk_output["chunks"]}
        self.assertEqual(
            [e["chunk_id"] for e in bundle["evidence"]],
            [r["chunk_id"] for r in results],
        )
        for rank, entry in enumerate(bundle["evidence"], 1):
            self.assertEqual(entry["rank"], rank)
            chunk = chunk_map[entry["chunk_id"]]
            self.assertEqual(entry["text"], chunk["text"])
            self.assertEqual(entry["page_number"], chunk["page_number"])
            self.assertEqual(entry["document_id"], "T-300")


if __name__ == "__main__":
    unittest.main()
