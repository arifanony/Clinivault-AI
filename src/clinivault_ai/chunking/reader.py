"""
Reading-order correction for multi-region PDF pages.

Default pdfplumber extraction (extract_words sorted by top, then x0) interleaves
content from side-by-side text regions when they share vertical bands. This
module detects text regions from a page-relative line-coverage profile and
outputs text region by region (each region top-to-bottom, regions left to
right), falling back to plain top-then-x0 ordering when no valid gutter exists.

This is a deterministic, geometry-based pass — no ML, no layout model.
Region detection is the implementation experiment documented in the
engineering-log entry 2026-09-09-column-detection-threshold-rejects-real-gutters
(Follow-up Investigation): real T2D-001 gutters are ~11 pt wide and sustain
0–3 % line coverage, which the retired distinct-x0-gap heuristic could never see.
"""

from __future__ import annotations

import pdfplumber
from typing import Optional

DEFAULT_COLUMN_GAP_THRESHOLD = 15.0
"""Legacy parameter of the retired distinct-x0-gap detector. Kept only for API
compatibility; the active detection path no longer uses it."""

DEFAULT_COLUMN_MARGIN = 10.0
"""Ignore words this close to the page edge when detecting regions — avoids
edge furniture (headers, footnotes, sidebar marks) being treated as content."""

DEFAULT_COVERAGE_TOLERANCE = 0.05
"""A vertical position is 'gutter-like' when at most this fraction of words
straddle it. Real T2D-001 gutters sustain 0–3 % word coverage (documented
follow-up investigation)."""

DEFAULT_MIN_GUTTER_WIDTH = 6.0
"""Minimum width in points of a low-coverage run before it counts as a gutter.
Real T2D-001 gutters measure 10.8–11.9 pt; page 7 has an irregular 7.2 pt one,
so this must stay below ~11 pt."""

DEFAULT_REGION_SCAN_LO = 0.15
"""Left edge of the interior scan window, as a fraction of page width.
Excludes the left page margin without hard-coding document coordinates."""

DEFAULT_REGION_SCAN_HI = 0.85
"""Right edge of the interior scan window, as a fraction of page width.
Excludes the right margin and the right-edge sidebar band (x ≈ 0.96·width)."""

DEFAULT_MIN_SIDE_LINES = 5
"""Minimum number of reconstructed text lines required on each side of a
candidate gutter — rejects accidental whitespace and margin slivers."""

DEFAULT_ROW_SPLIT_GAP = 8.0
"""Horizontal gap (pt) at which consecutive words in the same visual row are
split into separate line segments. Evidence (T2D-001 rows, pages 2/7/13/23):
within-row word spaces have p95 <= 6.2 pt, while inter-region gutters start at
10.8 pt — so 8 pt separates them without hard-coding document coordinates.
Baseline-aligned columns share row tops, so this split is what keeps column
detection (and side-volume validation) from merging columns into full-width
lines."""

DEFAULT_TABLE_CELL_PROXIMITY = 10.0
"""A candidate gutter whose midpoint lies within this distance (pt) of a
detected table cell column boundary is rejected as a document region boundary.
Evidence (T2D-001 semantic-guard investigation): Table 2.7's internal column
separator sits 5 pt from a detected cell boundary, while the nearest
genuine-gutter/cell-boundary distance observed was ~26 pt — 10 pt separates
the two populations without page-specific tuning."""


def _line_segments(words: list[dict], split_gap: float) -> list[dict]:
    """Group words into visual rows, then split rows at large horizontal gaps.

    Words are grouped by rounded top (same grouping as _words_to_lines); within
    a row, consecutive words separated by more than split_gap start a new
    segment. Returns segments as dicts with top, x0, x1, words.
    """
    rows: dict[int, list[dict]] = {}
    for w in words:
        rows.setdefault(round(w["top"]), []).append(w)

    segments = []
    for top in sorted(rows):
        row = sorted(rows[top], key=lambda w: w["x0"])
        current: list[dict] = [row[0]]
        for prev, w in zip(row, row[1:]):
            if w["x0"] - prev["x1"] > split_gap:
                segments.append(
                    {
                        "top": top,
                        "x0": current[0]["x0"],
                        "x1": current[-1]["x1"],
                        "words": current,
                    }
                )
                current = [w]
            else:
                current.append(w)
        segments.append(
            {"top": top, "x0": current[0]["x0"], "x1": current[-1]["x1"], "words": current}
        )
    return segments


def detect_region_gutters(
    words: list[dict],
    page_width: float,
    edge_margin: float = DEFAULT_COLUMN_MARGIN,
    coverage_tolerance: float = DEFAULT_COVERAGE_TOLERANCE,
    min_gutter_width: float = DEFAULT_MIN_GUTTER_WIDTH,
    scan_lo: float = DEFAULT_REGION_SCAN_LO,
    scan_hi: float = DEFAULT_REGION_SCAN_HI,
    min_side_lines: int = DEFAULT_MIN_SIDE_LINES,
    row_split_gap: float = DEFAULT_ROW_SPLIT_GAP,
) -> list[dict]:
    """Detect vertical gutters from the page-relative line-coverage profile.

    Words are first reconstructed into line segments (_line_segments): rows are
    split at horizontal gaps > row_split_gap so baseline-aligned columns are
    not merged into full-width lines. For each candidate x (1 pt steps over the
    interior scan window) we compute coverage(x) = the fraction of segments
    whose [x0, x1] span covers x. Segments do not straddle inter-region
    gutters, so gutters appear as contiguous low-coverage runs; a candidate is
    accepted only if it is wide enough and both sides hold enough segments.
    All geometry is page-relative — no absolute coordinates.

    Returns gutters sorted left to right, each a dict with:
      start, end  — bounds of the low-coverage run
      width, mid  — run width and midpoint
      max_coverage — worst (highest) coverage inside the run
      left_lines, right_lines — segments fully on each side
    An empty list means "no valid regions detected".
    """
    if not words:
        return []

    segments = _line_segments(words, row_split_gap)
    if len(segments) < 2 * min_side_lines:
        return []

    runs: list[dict] = []
    current: Optional[dict] = None
    x = page_width * scan_lo
    scan_end = page_width * scan_hi
    while x <= scan_end:
        covered = sum(1 for s in segments if s["x0"] <= x <= s["x1"])
        frac = covered / len(segments)
        if frac <= coverage_tolerance:
            if current is None:
                current = {"start": x, "end": x, "max_coverage": frac}
            else:
                current["end"] = x
                current["max_coverage"] = max(current["max_coverage"], frac)
        elif current is not None:
            runs.append(current)
            current = None
        x += 1.0
    if current is not None:
        runs.append(current)

    gutters = []
    for run in runs:
        width = run["end"] - run["start"]
        if width < min_gutter_width:
            continue
        left = sum(1 for s in segments if s["x1"] <= run["start"])
        right = sum(1 for s in segments if s["x0"] >= run["end"])
        if left < min_side_lines or right < min_side_lines:
            continue
        gutters.append(
            {
                **run,
                "width": width,
                "mid": (run["start"] + run["end"]) / 2.0,
                "left_lines": left,
                "right_lines": right,
            }
        )
    return gutters


def table_cell_x_boundaries(tables: list) -> list[float]:
    """Collect deduplicated vertical (column) x-boundaries from table cells.

    Uses only the geometry of individual cells — never table.bbox — so the
    table's outer bounding box cannot by itself look like a column boundary.
    A cell is a (x0, top, x1, bottom) tuple; its x0/x1 are vertical rule
    positions shared by the column it belongs to. Horizontal row separators
    contribute nothing here because we only read x coordinates.
    """
    bounds: set[float] = set()
    for table in tables:
        for cell in getattr(table, "cells", None) or []:
            try:
                x0, _top, x1, _bottom = cell
            except (TypeError, ValueError):
                continue
            if x0 is not None:
                bounds.add(round(float(x0), 1))
            if x1 is not None:
                bounds.add(round(float(x1), 1))
    return sorted(bounds)


def reject_table_internal_gutters(
    gutters: list[dict],
    cell_x_bounds: list[float],
    proximity: float = DEFAULT_TABLE_CELL_PROXIMITY,
) -> tuple[list[dict], list[dict]]:
    """Semantic guard: reject candidates that are table-internal separators.

    Invariant: a candidate gutter whose midpoint lies within `proximity` of
    any detected table cell column boundary is a table's internal column
    separator, not a document region boundary, and must not become one.
    Bounding-box overlap alone never rejects a candidate, and the absence of
    detected tables (empty cell_x_bounds) rejects nothing — find_tables() can
    miss visible tables, so "no table detected" is not positive evidence.

    Returns (kept, rejected) gutter lists, both sorted left to right.
    """
    kept, rejected = [], []
    for gutter in gutters:
        near_cell = any(
            abs(gutter["mid"] - b) <= proximity for b in cell_x_bounds
        )
        (rejected if near_cell else kept).append(gutter)
    return kept, rejected


def detect_column_split(
    words: list[dict],
    page_width: float,
    gap_threshold: float = DEFAULT_COLUMN_GAP_THRESHOLD,
    edge_margin: float = DEFAULT_COLUMN_MARGIN,
) -> Optional[float]:
    """Backward-compatible single-split view over detect_region_gutters().

    Returns the midpoint of the first detected gutter, or None when the page
    has no valid gutter. Superseded by detect_region_gutters(); retained so
    earlier diagnostics and callers keep working.
    """
    gutters = detect_region_gutters(words, page_width, edge_margin=edge_margin)
    return gutters[0]["mid"] if gutters else None


def _assign_regions(
    words: list[dict],
    region_bounds: list[float],
    row_split_gap: float = None,
) -> list[list[dict]]:
    """Assign words to text regions, guaranteeing no cross-region rows.

    Segments are the same row-segmentation used by detection (rows split at
    horizontal gaps > row_split_gap). A segment whose words all belong to one
    region is assigned intact. A segment that spans a gutter (possible when
    two regions share a baseline and the gap at the gutter is within the
    row-split threshold) is split into contiguous per-region runs, so no
    extracted row can contain words from two distinct detected regions.

    Returns one word list per region, ordered left to right.
    """
    if row_split_gap is None:
        row_split_gap = DEFAULT_ROW_SPLIT_GAP

    def region_index(x: float) -> int:
        idx = 0
        for mid in region_bounds:
            if x >= mid:
                idx += 1
        return idx

    regions: list[list[dict]] = [[] for _ in range(len(region_bounds) + 1)]
    for seg in _line_segments(words, row_split_gap):
        seg_words = sorted(seg["words"], key=lambda w: w["x0"])
        indices = [region_index((w["x0"] + w["x1"]) / 2.0) for w in seg_words]
        if len(set(indices)) == 1:
            regions[indices[0]].extend(seg_words)
            continue
        # Split into contiguous runs of same-region words (x0-ordered), so
        # opposite sides of a gutter never merge into one extracted row.
        run_start = 0
        for i in range(1, len(seg_words) + 1):
            if i == len(seg_words) or indices[i] != indices[run_start]:
                regions[indices[run_start]].extend(seg_words[run_start:i])
                run_start = i
    return regions


def extract_page_text_column_aware(
    pdf_path: str,
    page_number: int,
    gap_threshold: float = DEFAULT_COLUMN_GAP_THRESHOLD,
    edge_margin: float = DEFAULT_COLUMN_MARGIN,
) -> dict:
    """Extract a single page's text with region-aware reading order.

    Text regions are detected with detect_region_gutters() (page-relative
    line-coverage profile), then filtered by a semantic guard: candidates
    within DEFAULT_TABLE_CELL_PROXIMITY of a detected table cell column
    boundary are rejected as table-internal separators (bbox overlap alone
    and undetected tables never reject anything). Text is assigned to regions
    per word (whole segments when single-region, split into per-region runs
    when a segment spans a gutter), so no extracted row contains words from
    two distinct regions. Each region is read top-to-bottom, regions are
    concatenated left to right. When no valid gutter exists the page falls
    back to the plain top-then-x0 ordering.

    Returns a dict with:
      - page_number
      - is_two_column: True when at least one gutter was detected
      - split_x: first gutter midpoint (compatibility; None in fallback)
      - gutters: list of detected gutter dicts (empty in fallback)
      - rejected_gutters: candidates rejected by the table-cell semantic guard
      - region_count: number of text regions (1 in fallback)
      - fallback_used: True when no gutter was found
      - text: region-major reading-order text
      - word_count
      - left_word_count, right_word_count (first/last region, compatibility)
      - column_boundaries: per-region x extents
      - lines: reconstructed lines in region reading order
      - words: raw pdfplumber word dicts
    """
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number - 1]
        # Extract words while the PDF is still open — page objects become
        # unusable ("seek of closed file") once the context manager exits.
        words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
        # Semantic-guard evidence: table cell geometry must also be read while
        # the page is open. Default find_tables() settings only — the guard
        # treats undetected tables as unknown, never as evidence of absence.
        cell_x_bounds = table_cell_x_boundaries(page.find_tables())

    gutters = detect_region_gutters(words, page.width, edge_margin=edge_margin)
    gutters, rejected_gutters = reject_table_internal_gutters(gutters, cell_x_bounds)
    region_bounds = [g["mid"] for g in gutters]

    if not region_bounds:
        fallback_words = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))
        return {
            "page_number": page_number,
            "is_two_column": False,
            "split_x": None,
            "gutters": [],
            "rejected_gutters": rejected_gutters,
            "region_count": 1,
            "fallback_used": True,
            "column_boundaries": None,
            "text": _words_to_text(fallback_words),
            "word_count": len(words),
            "left_word_count": len(words),
            "right_word_count": 0,
            "lines": _words_to_lines(fallback_words),
            "words": words,
        }

    # Assign text to regions (see _assign_regions: whole segments when they
    # sit in one region, split into per-region runs when they span a gutter,
    # so no extracted row contains words from two distinct regions). Genuinely
    # page-wide lines (running headers) land in whichever region their center
    # falls — a known, accepted limitation.
    regions = _assign_regions(words, region_bounds)

    region_lines = []
    region_texts = []
    for region_words in regions:
        ordered = sorted(region_words, key=lambda w: (round(w["top"]), w["x0"]))
        region_lines.append(_words_to_lines(ordered))
        region_texts.append(_words_to_text(ordered))

    return {
        "page_number": page_number,
        "is_two_column": True,
        "split_x": region_bounds[0],
        "gutters": gutters,
        "rejected_gutters": rejected_gutters,
        "region_count": len(regions),
        "fallback_used": False,
        "column_boundaries": {
            "regions": [
                {
                    "x0": min((w["x0"] for w in rw), default=0),
                    "x1": max((w["x1"] for w in rw), default=0),
                    "word_count": len(rw),
                }
                for rw in regions
            ]
        },
        "text": "\n".join(t for t in region_texts if t.strip()),
        "word_count": len(words),
        "left_word_count": len(regions[0]),
        "right_word_count": len(regions[-1]),
        "lines": [ln for group in region_lines for ln in group],
        "words": words,
    }

def _words_to_lines(words: list[dict]) -> list[dict]:
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
