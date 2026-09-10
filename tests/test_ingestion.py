"""Minimal ingestion tests for the first parser milestone.

Covers exactly what this milestone promised:
- source SHA mismatch is rejected
- missing source is rejected
- page provenance exists
- empty/failed extraction is represented rather than silently dropped
- output JSON can be loaded successfully

Uses a tiny generated blank PDF as fixture (pypdf), so no corpus file is
needed and nothing in data/ is touched.
"""

from __future__ import annotations

import tempfile
import unittest
from unittest import mock
from pathlib import Path

from pypdf import PdfWriter

from clinivault_ai.ingestion import run_ingestion
from clinivault_ai.ingestion.errors import IngestionError
from clinivault_ai.ingestion.output import load_json
from clinivault_ai.ingestion.source import compute_sha256
from clinivault_ai.ingestion.validation import REQUIRED_PAGE_FIELDS


def _make_blank_pdf(path: Path) -> str:
    """A valid one-page PDF with no text layer."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as handle:
        writer.write(handle)
    return compute_sha256(path)


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.out_dir = self.tmp / "parsed"
        self.blank_pdf = self.tmp / "T2D-999-blank-fixture.pdf"
        self.sha = _make_blank_pdf(self.blank_pdf)

    def _run(self, source=None, sha=None, pages=1):
        return run_ingestion(
            source_path=source or self.blank_pdf,
            output_dir=self.out_dir,
            expected_sha256=sha or self.sha,
            expected_pages=pages,
            document_id="T2D-999",
        )

    def test_missing_source_is_rejected(self):
        with self.assertRaises(IngestionError):
            self._run(source=self.tmp / "does-not-exist.pdf")

    def test_sha_mismatch_is_rejected(self):
        wrong = "0" * 64
        with self.assertRaises(IngestionError):
            self._run(sha=wrong)

    def test_page_count_mismatch_is_rejected(self):
        with self.assertRaises(IngestionError):
            self._run(pages=5)

    def test_page_provenance_exists(self):
        summary = self._run()
        parsed = load_json(Path(summary["parsed_path"]))
        page = parsed["pages"][0]
        self.assertEqual(page["document_id"], "T2D-999")
        self.assertTrue(page["filename"])
        self.assertEqual(page["page_number"], 1)

    def test_empty_extraction_is_represented_not_dropped(self):
        # The fixture is a blank PDF: the page has no text layer, so the
        # record must exist with status "empty" and empty text.
        summary = self._run()
        parsed = load_json(Path(summary["parsed_path"]))
        self.assertEqual(len(parsed["pages"]), 1)
        page = parsed["pages"][0]
        self.assertEqual(page["extraction_status"], "empty")
        self.assertEqual(page["text"], "")
        self.assertEqual(page["char_count"], 0)
        # The document-level text check must fail loudly, not hide it.
        validation = load_json(Path(summary["validation_path"]))
        by_name = {c["name"]: c for c in validation["checks"]}
        self.assertEqual(by_name["document_text_present"]["status"], "fail")
        self.assertEqual(validation["overall_status"], "fail")

    def test_output_json_loads_successfully(self):
        summary = self._run()
        parsed = load_json(Path(summary["parsed_path"]))
        validation = load_json(Path(summary["validation_path"]))
        self.assertIn("provenance", parsed)
        self.assertIn("pages", parsed)
        self.assertIn("checks", validation)
        self.assertTrue(summary["reload_ok"])


class ColumnAwareIngestionTests(unittest.TestCase):
    """Ingestion must extract page text through the column-aware reader.

    Focused on the integration seam only: which extraction path parsing.py
    calls, that the reader's text lands in the page record with provenance
    and status semantics intact, that reader metadata does not leak into
    the parsed page schema, and that a reader failure stays isolated per
    page. Reader behavior itself (gutter detection, fallback ordering) is
    covered by tests/test_reader.py and is deliberately not duplicated here.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.out_dir = self.tmp / "parsed"
        self.blank_pdf = self.tmp / "T2D-998-blank-fixture.pdf"
        self.sha = _make_blank_pdf(self.blank_pdf)

    def _run(self):
        return run_ingestion(
            source_path=self.blank_pdf,
            output_dir=self.out_dir,
            expected_sha256=self.sha,
            expected_pages=1,
            document_id="T2D-998",
        )

    def test_ingestion_uses_column_aware_reader(self):
        extraction = {
            "text": "Region one line.\nRegion two line.",
            "fallback_used": False,
            "region_count": 2,
            "gutters": [{"mid": 297.0}],
        }
        with mock.patch(
            "clinivault_ai.ingestion.parsing.extract_page_text_column_aware",
            return_value=extraction,
        ) as fake:
            summary = self._run()
        fake.assert_called_once_with(str(self.blank_pdf), 1)
        parsed = load_json(Path(summary["parsed_path"]))
        page = parsed["pages"][0]
        self.assertEqual(page["text"], "Region one line.\nRegion two line.")
        self.assertEqual(page["extraction_status"], "ok")
        self.assertEqual(page["word_count"], 6)
        self.assertEqual(page["char_count"], len(page["text"]))

    def test_reader_failure_is_isolated_per_page(self):
        with mock.patch(
            "clinivault_ai.ingestion.parsing.extract_page_text_column_aware",
            side_effect=RuntimeError("reader boom"),
        ):
            summary = self._run()
        parsed = load_json(Path(summary["parsed_path"]))
        page = parsed["pages"][0]
        # The record still exists with full provenance -- never dropped.
        self.assertEqual(page["document_id"], "T2D-998")
        self.assertEqual(page["page_number"], 1)
        self.assertEqual(page["extraction_status"], "failed")
        self.assertIn("RuntimeError: reader boom", page["extraction_error"] or "")
        validation = load_json(Path(summary["validation_path"]))
        by_name = {c["name"]: c for c in validation["checks"]}
        self.assertEqual(by_name["extraction_failures"]["status"], "fail")
        self.assertEqual(validation["overall_status"], "fail")

    def test_reader_metadata_does_not_leak_into_page_schema(self):
        extraction = {
            "text": "Region text.",
            "fallback_used": False,
            "gutters": [{"mid": 297.0}],
            "rejected_gutters": [{"mid": 212.0}],
            "column_boundaries": {"regions": []},
            "lines": [],
            "words": [{"x0": 1.0, "x1": 2.0, "top": 1.0, "text": "Region"}],
        }
        with mock.patch(
            "clinivault_ai.ingestion.parsing.extract_page_text_column_aware",
            return_value=extraction,
        ):
            summary = self._run()
        parsed = load_json(Path(summary["parsed_path"]))
        page = parsed["pages"][0]
        # Parsed page schema is exactly the required provenance set:
        # reader-specific observability must not change the contract.
        self.assertEqual(set(page.keys()), set(REQUIRED_PAGE_FIELDS))


if __name__ == "__main__":
    unittest.main()
