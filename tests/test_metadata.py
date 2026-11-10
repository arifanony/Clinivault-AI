"""M3: catalog metadata passthrough and ingestion reports.

Covers exactly what M3 promised:
- catalog holds the nine obtained documents (no T2D-004), with the six
  brief-level fields transcribed from docs/corpus/corpus-manifest.md
- retrieval records/results carry document_name only for catalogued
  documents; synthetic/legacy IDs keep their exact historical contract
- context bundles preserve document_name verbatim when present
- build_ingestion_report returns the brief shape, fails on chunk/embedding
  mismatch, and reports failed pages; writer lands under the canonical path
"""

from __future__ import annotations

import json
import unittest

from clinivault_ai.context import build_context
from clinivault_ai.context.errors import ContextError
from clinivault_ai.corpus.catalog import (
    DOCUMENT_CATALOG,
    get_document_metadata,
    get_document_name,
)
from clinivault_ai.ingestion.errors import IngestionError
from clinivault_ai.ingestion.report import (
    build_ingestion_report,
    report_path,
    write_ingestion_report,
)


EXPECTED_IDS = (
    "T2D-001",
    "T2D-002",
    "T2D-003",
    "T2D-005",
    "T2D-006",
    "T2D-007",
    "T2D-008",
    "T2D-009",
    "T2D-010",
)


def _parsed(document_id="T2D-001", pages=None):
    if pages is None:
        pages = [
            {"page_number": 1, "extraction_status": "ok", "text": "alpha"},
            {"page_number": 2, "extraction_status": "ok", "text": "beta"},
        ]
    return {"provenance": {"document_id": document_id}, "pages": pages}


def _chunk_output(document_id="T2D-001", n=2):
    return {
        "document_id": document_id,
        "chunks": [
            {
                "chunk_id": f"{document_id}-p001-c{i:03d}",
                "document_id": document_id,
                "page_number": 1,
                "chunk_index": i,
                "text": f"text {i}",
            }
            for i in range(1, n + 1)
        ],
    }


def _embedding_artifact(document_id="T2D-001", n=2):
    return {
        "document_id": document_id,
        "model": {"name": "m", "dimension": 2},
        "embeddings": [
            {
                "chunk_id": f"{document_id}-p001-c{i:03d}",
                "document_id": document_id,
                "page_number": 1,
                "vector": [1.0, 0.0],
            }
            for i in range(1, n + 1)
        ],
    }


class CatalogTests(unittest.TestCase):
    def test_nine_obtained_documents_no_blocked_substitute(self):
        self.assertEqual(tuple(sorted(DOCUMENT_CATALOG)), tuple(sorted(EXPECTED_IDS)))
        self.assertNotIn("T2D-004", DOCUMENT_CATALOG)

    def test_required_fields_present(self):
        for document_id in EXPECTED_IDS:
            entry = DOCUMENT_CATALOG[document_id]
            for field in (
                "document_id",
                "document_name",
                "source",
                "publication_date",
                "version",
                "ingestion_date",
            ):
                self.assertIn(field, entry, f"{document_id} missing {field}")
                self.assertIsInstance(entry[field], str)
            self.assertTrue(entry["document_name"])
            self.assertTrue(entry["source"])

    def test_unknown_document_returns_none(self):
        self.assertIsNone(get_document_metadata("T-200"))
        self.assertIsNone(get_document_name("T-200"))
        self.assertIsNone(get_document_name("T2D-004"))

    def test_metadata_returns_a_copy(self):
        first = get_document_metadata("T2D-001")
        assert first is not None
        first["document_name"] = "mutated"
        self.assertNotEqual(
            get_document_metadata("T2D-001")["document_name"], "mutated"
        )


class RetrievalPassthroughTests(unittest.TestCase):
    def test_store_attaches_document_name_for_catalogued_doc(self):
        from clinivault_ai.chunking import chunk_pages, default_config
        from clinivault_ai.embedding import (
            BaselineHashEmbeddingProvider,
            generate_embeddings,
        )
        from clinivault_ai.retrieval import VectorStore

        pages = [
            {"page_number": 1, "extraction_status": "ok", "text": "Alpha beta."},
        ]
        chunk_output = chunk_pages(
            {"provenance": {"document_id": "T2D-001"}, "pages": pages},
            default_config(),
        )
        artifact = generate_embeddings(
            chunk_output, BaselineHashEmbeddingProvider(dimension=8)
        )
        store = VectorStore.from_artifacts(artifact, chunk_output)
        self.assertTrue(store.records)
        for record in store.records:
            self.assertEqual(
                record["document_name"], get_document_name("T2D-001")
            )

    def test_synthetic_store_keeps_exact_historical_record_shape(self):
        from clinivault_ai.chunking import chunk_pages, default_config
        from clinivault_ai.embedding import (
            BaselineHashEmbeddingProvider,
            generate_embeddings,
        )
        from clinivault_ai.retrieval import VectorStore, search

        pages = [
            {"page_number": 1, "extraction_status": "ok", "text": "Alpha beta."},
        ]
        chunk_output = chunk_pages(
            {"provenance": {"document_id": "T-200"}, "pages": pages},
            default_config(),
        )
        artifact = generate_embeddings(
            chunk_output, BaselineHashEmbeddingProvider(dimension=8)
        )
        store = VectorStore.from_artifacts(artifact, chunk_output)
        for record in store.records:
            self.assertNotIn("document_name", record)

        class Fixed:
            name = "fixed"
            dimension = 8

            def embed_texts(self, texts):
                return [[1.0] + [0.0] * 7 for _ in texts]

        results = search(store, "q", Fixed(), 1)
        self.assertEqual(
            set(results[0].keys()),
            {"chunk_id", "document_id", "page_number", "score", "text"},
        )


class ContextPassthroughTests(unittest.TestCase):
    def test_document_name_preserved_verbatim(self):
        results = [
            {
                "chunk_id": "T2D-001-p001-c001",
                "document_id": "T2D-001",
                "document_name": get_document_name("T2D-001"),
                "page_number": 1,
                "score": 0.9,
                "text": "evidence",
            }
        ]
        bundle = build_context(results)
        self.assertEqual(
            bundle["evidence"][0]["document_name"], get_document_name("T2D-001")
        )
        self.assertEqual(
            bundle["documents"][0]["document_name"], get_document_name("T2D-001")
        )

    def test_absent_document_name_stays_absent(self):
        bundle = build_context(
            [
                {
                    "chunk_id": "D-1-p001-c001",
                    "document_id": "D-1",
                    "page_number": 1,
                    "score": 0.5,
                    "text": "t",
                }
            ]
        )
        self.assertNotIn("document_name", bundle["evidence"][0])
        self.assertNotIn("document_name", bundle["documents"][0])

    def test_invalid_document_name_rejected(self):
        bad = {
            "chunk_id": "D-1-p001-c001",
            "document_id": "D-1",
            "document_name": "",
            "page_number": 1,
            "score": 0.5,
            "text": "t",
        }
        with self.assertRaises(ContextError):
            build_context([bad])


class IngestionReportTests(unittest.TestCase):
    def test_brief_shape_and_counts(self):
        report = build_ingestion_report(
            "T2D-001", _parsed(), _chunk_output(), _embedding_artifact()
        )
        self.assertEqual(
            set(report),
            {
                "document_id",
                "total_pages",
                "parsed_pages",
                "failed_pages",
                "total_chunks",
                "embedded_chunks",
                "indexed_chunks",
                "ingestion_status",
            },
        )
        self.assertEqual(report["document_id"], "T2D-001")
        self.assertEqual(report["total_pages"], 2)
        self.assertEqual(report["parsed_pages"], 2)
        self.assertEqual(report["failed_pages"], [])
        self.assertEqual(report["total_chunks"], 2)
        self.assertEqual(report["embedded_chunks"], 2)
        self.assertEqual(report["indexed_chunks"], 2)
        self.assertEqual(report["ingestion_status"], "success")

    def test_failed_pages_marked_partial(self):
        pages = [
            {"page_number": 1, "extraction_status": "ok", "text": "a"},
            {"page_number": 2, "extraction_status": "failed", "text": ""},
        ]
        report = build_ingestion_report(
            "T2D-001",
            _parsed(pages=pages),
            _chunk_output(n=1),
            _embedding_artifact(n=1),
        )
        self.assertEqual(report["failed_pages"], [2])
        self.assertEqual(report["parsed_pages"], 1)
        self.assertEqual(report["ingestion_status"], "partial")

    def test_chunk_embedding_mismatch_fails_loud(self):
        with self.assertRaises(IngestionError):
            build_ingestion_report(
                "T2D-001", _parsed(), _chunk_output(n=2), _embedding_artifact(n=1)
            )

    def test_document_identity_mismatch_fails_loud(self):
        with self.assertRaises(IngestionError):
            build_ingestion_report(
                "T2D-001", _parsed("T2D-002"), _chunk_output(), _embedding_artifact()
            )

    def test_writer_uses_canonical_path_and_roundtrips(self):
        import tempfile
        from pathlib import Path

        report = build_ingestion_report(
            "T2D-001", _parsed(), _chunk_output(), _embedding_artifact()
        )
        with tempfile.TemporaryDirectory() as tmp:
            expected = Path(tmp) / "data" / "ingestion-report" / "stage-1-clean-baseline-corpus" / "T2D-001" / "T2D-001.ingestion-report.json"
            self.assertEqual(
                report_path(tmp, "stage-1-clean-baseline-corpus", "T2D-001"),
                expected,
            )
            out = write_ingestion_report(report, expected)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), report)


if __name__ == "__main__":
    unittest.main()
