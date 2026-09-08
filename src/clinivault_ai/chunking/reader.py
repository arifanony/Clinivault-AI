"""
Reading-order correction for two-column PDF pages.

Default pdfplumber extraction (extract_words sorted by top, then x0) interleaves
content from two columns when they share vertical bands. This module provides
column-aware extraction that separates left and right columns and outputs them
in correct reading order.

This is a deterministic, geometry-based pass — no ML, no layout model.
It is designed for the specific document type in our MVP corpus: text-based
two-column clinical PDFs where columns are separated by a visible vertical gutter.
"""

from __future__ import annotations

import pdfplumber
from typing import Optional

DEFAULT_COLUMN_GAP_THRESHOLD = 15.0
"""Minimum gap (in points) between consecutive distinct x0 positions that we treat
as a column boundary. Tuned on T2D-001: the gutter between content columns is
~210pt on a 594pt-wide page; the small gaps within a column are <10pt."""

DEFAULT_COLUMN_MARGIN = 10.0
"""Ignore words this close to the page edge when detecting columns — avoids
flash/header/footnote text near edges being treated as a column."""


def detect_column_split(
    words: list[dict],
    page_width: float,
    gap_threshold: float = DEFAULT_COLUMN_GAP_THRESHOLD,
    edge_margin: float = DEFAULT_COLUMN_MARGIN,
) -> Optional[float]:
    """Return the x midpoint of the dominant column gutter, or None if single-column.

    The page x-range has two edges: the left column occupies the left portion,
    the right column the right portion, and there is a wide gap between them.
    We find the largest gap between consecutive x0 positions that is interior
    (not at the page edges) and use its midpoint as the split.
    """
    if not words:
        return None

    xs = sorted(
        {
            round(w["x0"], 1)
            for w in words
            if w["x0"] is not None
            and w["x0"] > edge_margin
            and w["x0"] < page_width - edge_margin
        }
    )

    if len(xs) < 4:
        return None

    best_gap = 0.0
    best_mid = 0.0
    for i in range(len(xs) - 1):
        gap = xs[i + 1] - xs[i]
        if gap >= gap_threshold and gap > best_gap:
            best_gap = gap
            best_mid = (xs[i] + xs[i + 1]) / 2.0

    if best_gap > 0 and best_gap < page_width * 0.05:
        return None

def extract_page_text_column_aware(
    pdf_path: str,
    page_number: int,
    gap_threshold: float = DEFAULT_COLUMN_GAP_THRESHOLD,
    edge_margin: float = DEFAULT_COLUMN_MARGIN,
) -> dict:
    """Extract a single page's text with column-aware reading order.

    Returns a dict with:
      - page_number
      - is_two_column: bool
      - split_x: the column split x midpoint if two-column, else None
      - column_boundaries: dict with left_x1, right_x0
      - text: the reading-order-corrected text (left column then right column)
      - word_count: total words extracted
      - left_word_count, right_word_count
      - lines: list of reconstructed lines (top, x0, x1, text, column)

    The text is built by sorting each column by (top, x0), joining words with
    spaces, and inserting line breaks between distinct top positions. Then the
    left column text is followed by the right column text.
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]

    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)

    split_x = detect_column_split(words, page.width, gap_threshold, edge_margin)
    is_two_column = split_x is not None and split_x > 0

    if not is_two_column:
        left_words = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))
        return {
            "page_number": page_number,
            "is_two_column": False,
            "split_x": None,
            "column_boundaries": None,
            "text": _words_to_text(left_words),
            "word_count": len(words),
            "left_word_count": len(words),
            "right_word_count": 0,
            "lines": _words_to_lines(left_words),
            "words": words,
        }

    left_words = [w for w in words if w["x0"] < split_x]
    right_words = [w for w in words if w["x0"] >= split_x]

    left_sorted = sorted(left_words, key=lambda w: (round(w["top"]), w["x0"]))
    right_sorted = sorted(right_words, key=lambda w: (round(w["top"]), w["x0"]))

    left_text = _words_to_text(left_sorted)
    right_text = _words_to_text(right_sorted)

    combined_text = left_text
    if right_text.strip():
        if not combined_text.endswith("\n"):
            combined_text += "\n"
        combined_text += right_text

    return {
        "page_number": page_number,
        "is_two_column": True,
        "split_x": split_x,
        "column_boundaries": {
            "left_x0": min((w["x0"] for w in left_words), default=0),
            "left_x1": max((w["x1"] for w in left_words), default=0),
            "right_x0": min((w["x0"] for w in right_words), default=0),
            "right_x1": max((w["x1"] for w in right_words), default=0),
            "split_x": split_x,
        },
        "text": combined_text,
        "word_count": len(words),
        "left_word_count": len(left_words),
        "right_word_count": len(right_words),
        "lines": _words_to_lines(left_sorted) + _words_to_lines(right_sorted),
        "words": words,
    }

(words: list[dict]) -> list[dict]:
    """Group words into lines by top position (within 3pt tolerance).

    Each line is a dict with:
      - top: rounded top position
      - x0: min x0 in the line
      - x1: max x1 in the line
      - text: joined words
      - word_count: number of words in the line
      - median_x0: median x0 position (for column attribution)
    """
    if not words:
        return []

    rows: dict[int, list[dict]] = {}
    for w in words:
        key = round(w["top"])
        rows.setdefault(key, []).append(w)

    lines = []
    for top in sorted(rows.keys()):
        row_words = sorted(rows[top], key=lambda w: w["x0"])
        text = " ".join(w.get("text", "") or "" for w in row_words)
        x0 = min(w["x0"] for w in row_words)
        x1 = max(w["x1"] for w in row_words)
        median_x0 = sorted(w["x0"] for w in row_words)[len(row_words) // 2]
        lines.append(
            {
                "top": top,
                "x0": x0,
                "x1": x1,
                "text": text,
                "word_count": len(row_words),
                "median_x0": median_x0,
            }
        )

    return lines


def _words_to_text(words: list[dict]) -> str:
    """Convert sorted words to line-based text.

    Words are grouped by top position (within 3pt tolerance), sorted by x0 within
    each line, and joined with spaces. Lines are joined with newlines.
    """
    lines = _words_to_lines(words)
    return "\n".join(line["text"] for line in lines)
