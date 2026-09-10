"""Focused tests for the baseline structural chunker (chunker.py).

Covers exactly what this milestone promised:
- deterministic chunk creation (same input, same output)
- chunk provenance: every chunk carries document_id + page_number + chunk_index
- chunk_id matches the repository ID convention
- no empty chunks
- no silent text loss (words and word order are preserved)
- natural boundaries are preferred; oversized text never splits inside a word
- failed/empty pages are recorded rather than dropped
- end-to-end validation report passes on chunker output

Uses synthetic parsed documents (plain dicts), so no corpus file, no PDF,
and nothing in data/ is touched.
"""

from __future__ import annotations

import unittest

from clinivault_ai.chunking import (
    chunk_pages,
    default_config,
    validate_chunks,
)
from clinivault_ai.chunking.chunker import make_chunk_id


def page(page_number: int, text: str, status: str = "ok") -> dict:
    return {
        "document_id": "T-777",
        "page_number": page_number,
        "text": text,
        "extraction_status": status,
    }


def document(pages: list[dict]) -> dict:
    return {"provenance": {"document_id": "T-777"}, "pages": pages}


def tokens(text: str) -> list[str]:
    return text.split()


class BaselineChunkerTests(unittest.TestCase):
    cfg = default_config()

    def test_deterministic_output(self):
        doc = document(
            [
                page(1, "Alpha paragraph one.\n\nAlpha paragraph two."),
                page(2, "Beta text."),
            ]
        )
        first = chunk_pages(doc, self.cfg)
        second = chunk_pages(doc, self.cfg)
        self.assertEqual(first, second)

    def test_provenance_and_id_format(self):
        doc = document([page(1, "Alpha paragraph one.\n\nAlpha paragraph two.")])
        out = chunk_pages(doc, self.cfg)
        self.assertEqual(out["document_id"], "T-777")
        for chunk in out["chunks"]:
            self.assertEqual(chunk["document_id"], "T-777")
            self.assertEqual(chunk["page_number"], 1)
            self.assertEqual(
                chunk["chunk_id"],
                make_chunk_id("T-777", chunk["page_number"], chunk["chunk_index"]),
            )
        # chunk_index is 1..n in order on the page
        indexes = [c["chunk_index"] for c in out["chunks"]]
        self.assertEqual(indexes, list(range(1, len(indexes) + 1)))

    def test_no_text_lost_and_no_empty_chunks(self):
        page1 = "Alpha paragraph one.\n\nAlpha paragraph two."
        page2 = "Beta text continues here."
        doc = document([page(1, page1), page(2, page2)])
        out = chunk_pages(doc, self.cfg)
        chunks = out["chunks"]
        self.assertTrue(chunks)
        for chunk in chunks:
            self.assertTrue(chunk["text"].strip(), "no empty/whitespace-only chunk")
        # Word order preserved across the whole document (no silent loss).
        expected = tokens(page1) + tokens(page2)
        produced = [t for c in chunks for t in tokens(c["text"])]
        self.assertEqual(produced, expected)

    def test_chunks_never_span_pages(self):
        doc = document(
            [
                page(1, "Alpha text on page one."),
                page(2, "Beta text on page two."),
            ]
        )
        out = chunk_pages(doc, self.cfg)
        # Two short single-paragraph pages: each yields exactly one chunk,
        # and no chunk mixes words from both pages.
        self.assertEqual(len(out["chunks"]), 2)
        self.assertEqual(
            tokens(out["chunks"][0]["text"]), tokens("Alpha text on page one.")
        )
        self.assertEqual(
            tokens(out["chunks"][1]["text"]), tokens("Beta text on page two.")
        )
        self.assertEqual(out["statistics"]["pages_with_chunks"], [1, 2])

    def test_pages_sorted_by_page_number(self):
        doc = document(
            [page(3, "Gamma later."), page(1, "Alpha first."), page(2, "Beta middle.")]
        )
        out = chunk_pages(doc, self.cfg)
        self.assertEqual([c["page_number"] for c in out["chunks"]], [1, 2, 3])
        self.assertEqual(tokens(out["chunks"][0]["text"]), tokens("Alpha first."))

    def test_natural_boundaries_preferred(self):
        # Two small blank-line-separated paragraphs fit under target_chars:
        # they belong to one chunk, and the blank-line boundary is kept as
        # a paragraph break inside the chunk.
        text = "Alpha small paragraph.\n\nBeta small paragraph."
        doc = document([page(1, text)])
        out = chunk_pages(doc, self.cfg)
        self.assertEqual(len(out["chunks"]), 1)
        self.assertEqual(out["chunks"][0]["text"], text)

    def test_oversized_paragraph_never_splits_inside_word(self):
        # One long paragraph over max_chars: sentences are kept whole, and
        # every chunk stays within max_chars for normal words.
        sentence = "The quick brown fox jumps over the lazy dog near the river bank."
        text = " ".join([sentence] * 60)  # ~3.5k chars > max_chars 1800
        doc = document([page(1, text)])
        out = chunk_pages(doc, self.cfg)
        self.assertGreater(len(out["chunks"]), 1)
        for chunk in out["chunks"]:
            self.assertLessEqual(len(chunk["text"]), self.cfg.max_chars)
            for word in chunk["text"].split():
                self.assertIn(word, sentence.split(), "no mid-word split")
        produced = [t for c in out["chunks"] for t in tokens(c["text"])]
        self.assertEqual(produced, tokens(text))

    def test_failed_and_empty_pages_recorded_not_dropped(self):
        doc = document(
            [
                page(1, "", status="empty"),
                page(2, "Alpha real text."),
                page(3, "", status="failed"),
            ]
        )
        out = chunk_pages(doc, self.cfg)
        self.assertEqual(len(out["chunks"]), 1)
        self.assertEqual(out["chunks"][0]["page_number"], 2)
        self.assertEqual(
            out["statistics"]["pages_without_chunks"],
            [
                {"page_number": 1, "reason": "empty"},
                {"page_number": 3, "reason": "failed"},
            ],
        )

    def test_short_document_single_chunk(self):
        doc = document([page(1, "One sentence only.")])
        out = chunk_pages(doc, self.cfg)
        self.assertEqual(out["chunks"][0]["chunk_id"], "T-777-p001-c001")
        self.assertEqual(out["chunks"][0]["text"], "One sentence only.")

    def test_single_word_longer_than_max_survives_intact(self):
        # Pathological edge: a single word longer than max_chars must be
        # emitted alone and intact -- never split, never dropped.
        long_word = "w" * (self.cfg.max_chars + 50)
        doc = document([page(1, f"Alpha starts {long_word} beta ends.")])
        out = chunk_pages(doc, self.cfg)
        produced = [t for c in out["chunks"] for t in tokens(c["text"])]
        expected = tokens(f"Alpha starts {long_word} beta ends.")
        self.assertEqual(produced, expected)
        self.assertIn(long_word, [c["text"] for c in out["chunks"]])

    def test_validation_report_passes_on_chunker_output(self):
        text = ("Para one with some clinical content about diagnosis.\n\n" * 40).strip()
        doc = document([page(1, text), page(2, "Alpha second page content.")])
        out = chunk_pages(doc, self.cfg)
        report = validate_chunks(out, max_chars=self.cfg.max_chars)
        self.assertEqual(report["overall_status"], "pass", report["checks"])


if __name__ == "__main__":
    unittest.main()

