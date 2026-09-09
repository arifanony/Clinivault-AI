"""Focused tests for the coverage-based region detector in reader.py.

reader.py is loaded directly from its file path because the full
clinivault_ai.chunking package does not import yet (chunker.py and
validate.py do not exist — that is a separate unit of work).
"""

import importlib.util
import pathlib
import unittest

_SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
_SPEC = importlib.util.spec_from_file_location(
    "clinivault_reader_under_test",
    _SRC / "clinivault_ai" / "chunking" / "reader.py",
)
reader = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(reader)


def word(x0, x1, top, text="w"):
    return {"x0": x0, "x1": x1, "top": top, "text": text}


def grid_words(widths, pw):
    """Build synthetic words for `widths` regions evenly usable across pw.

    In-region word gaps are kept below the 6pt min-gutter-width so only the
    true inter-region gaps can be detected as gutters.
    """
    words = []
    usable = pw * 0.9
    region_w = usable / len(widths)
    for i, n_lines in enumerate(widths):
        base = pw * 0.05 + i * region_w
        inner = region_w * 0.8
        step = inner / 5.0
        for line in range(n_lines):
            top = 50.0 + line * 12.0
            for k in range(5):
                x0 = base + k * step
                words.append(word(x0, x0 + step * 0.92, top))
    return words


class DetectRegionGuttersTests(unittest.TestCase):
    def test_two_regions_single_gutter(self):
        pw = 600.0
        words = grid_words([40, 40], pw)
        gutters = reader.detect_region_gutters(words, pw)
        self.assertEqual(len(gutters), 1)
        # gutter must sit between the two regions (left ends ~246, right
        # starts ~300 on this synthetic layout)
        self.assertGreater(gutters[0]["mid"], 246)
        self.assertLess(gutters[0]["mid"], 300)
        self.assertAlmostEqual(
            reader.detect_column_split(words, pw), gutters[0]["mid"]
        )

    def test_three_regions_two_gutters(self):
        pw = 800.0
        words = grid_words([40, 40, 40], pw)
        gutters = reader.detect_region_gutters(words, pw)
        self.assertEqual(len(gutters), 2)
        self.assertLess(gutters[0]["mid"], gutters[1]["mid"])

    def test_single_region_no_gutter(self):
        pw = 600.0
        words = grid_words([40], pw)
        self.assertEqual(reader.detect_region_gutters(words, pw), [])
        self.assertIsNone(reader.detect_column_split(words, pw))

    def test_narrow_gap_rejected(self):
        pw = 600.0
        # Two regions separated by only a 4pt gap (below min_gutter_width=6):
        # left region ends at x1=148, right starts at x0=152. In-region word
        # gaps are 2pt (between words) so rows are not split internally.
        words = []
        for line in range(40):
            top = 50.0 + line * 12.0
            for k in range(5):
                words.append(word(50 + k * 20, 68 + k * 20, top))   # ends 148
            for k in range(5):
                words.append(word(152 + k * 20, 170 + k * 20, top)) # starts 152
        self.assertEqual(reader.detect_region_gutters(words, pw), [])

    def test_too_few_lines_on_a_side_rejected(self):
        pw = 600.0
        words = grid_words([3, 40], pw)  # left side has only 3 lines
        self.assertEqual(reader.detect_region_gutters(words, pw), [])

    def test_empty_words(self):
        self.assertEqual(reader.detect_region_gutters([], 600.0), [])


class CrossRegionLeakageTests(unittest.TestCase):
    """Regression tests for the row-merge cross-region leakage fix.

    Reproduces the T2D-001 failure pattern (engineering log
    2026-09-10-row-merge-cross-region-leakage): words from two regions share
    a baseline and the gap between them is within DEFAULT_ROW_SPLIT_GAP, so
    the row-segmenter merges them into one segment. The fix splits such
    segments into per-region runs before row construction.
    """

    def _two_region_same_baseline_words(self):
        # pw=600. Left region x 50-286, 12pt gutter (segments split at gaps
        # > 8pt, so detection works exactly as on T2D-001 pages 6/16 where
        # gutters measure 9-11pt), right region 298-548. Words from both
        # sides share every rounded top — reproducing the row-merge leak
        # precondition: naive rounded-top row grouping merges L and R words
        # into one row, which the old extraction then assigned by row center.
        words = []
        for line in range(30):
            top = 50.0 + line * 12.0
            for k in range(5):
                x0 = 50 + k * 48
                words.append(word(x0, x0 + 44, top, text=f"L{line}_{k}"))
            for k in range(5):
                x0 = 298 + k * 50
                words.append(word(x0, x0 + 46, top, text=f"R{line}_{k}"))
        return words

    def test_same_baseline_row_is_split_per_region(self):
        pw = 600.0
        words = self._two_region_same_baseline_words()
        gutters = reader.detect_region_gutters(words, pw)
        self.assertEqual(len(gutters), 1)
        bounds = [g["mid"] for g in gutters]

        # Leak precondition (as on T2D-001): naive rounded-top row grouping
        # merges left- and right-region words sharing a baseline.
        rows: dict[int, list[dict]] = {}
        for w in words:
            rows.setdefault(round(w["top"]), []).append(w)
        merged = [
            " ".join(x["text"] for x in sorted(r, key=lambda w: w["x0"]))
            for r in rows.values()
        ]
        self.assertTrue(any("L" in m and "R" in m for m in merged))

        # The fix: segment-based assignment splits them per region.
        regions = reader._assign_regions(words, bounds)
        self.assertEqual(len(regions), 2)
        self.assertTrue(all(w["text"].startswith("L") for w in regions[0]))
        self.assertTrue(all(w["text"].startswith("R") for w in regions[1]))
        # No extracted row in either region mixes L and R words.
        for region in regions:
            for line in reader._words_to_lines(region):
                labels = {t[0] for t in line["text"].split()}
                self.assertEqual(len(labels), 1, line["text"])

    def test_region_major_order_preserved(self):
        pw = 600.0
        words = self._two_region_same_baseline_words()
        gutters = reader.detect_region_gutters(words, pw)
        regions = reader._assign_regions(
            words, [g["mid"] for g in gutters]
        )
        # Each region reads top-to-bottom, left-to-right within a row.
        for region in regions:
            tops = [round(w["top"]) for w in region]
            self.assertEqual(tops, sorted(tops))
        # Left region holds all 30 L lines, right all 30 R lines.
        self.assertEqual(len({round(w["top"]) for w in regions[0]}), 30)
        self.assertEqual(len({round(w["top"]) for w in regions[1]}), 30)

    def test_single_region_extraction_unchanged(self):
        pw = 600.0
        words = grid_words([40], pw)
        # No gutter: extraction must fall back to plain top-then-x0 ordering,
        # which is exactly _words_to_text over that sort.
        fallback = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))
        self.assertEqual(reader.detect_region_gutters(words, pw), [])
        self.assertEqual(
            reader._words_to_text(fallback),
            reader._words_to_text(fallback),
        )
        # And a single-region assignment with no bounds returns one region
        # containing every word, in the same order as the fallback.
        regions = reader._assign_regions(words, [])
        self.assertEqual(len(regions), 1)
        self.assertEqual(
            [id(w) for w in regions[0]], [id(w) for w in fallback]
        )


class TableGuardTests(unittest.TestCase):
    """Semantic guard: table-internal separators must not become doc regions.

    Synthetic stand-ins mimic pdfplumber Table objects; only `.cells`
    ((x0, top, x1, bottom) tuples) is read — bbox is deliberately absent to
    prove it plays no role in the guard.
    """

    @staticmethod
    def table(cells):
        class _T:
            pass

        t = _T()
        t.cells = cells
        return t

    def gutter(self, mid, pw=600.0):
        return {
            "start": mid - 5.0,
            "end": mid + 5.0,
            "width": 10.0,
            "mid": mid,
            "max_coverage": 0.0,
            "left_lines": 30,
            "right_lines": 30,
        }

    def test_candidate_near_cell_boundary_rejected(self):
        # p16 pattern: candidate mid 0.358*pw sits ~5 pt from a cell boundary.
        pw = 600.0
        candidate = self.gutter(pw * 0.358)
        cells = [
            (pw * 0.25, 50, pw * 0.367, 90),   # interior column boundary 0.367
            (pw * 0.367, 50, pw * 0.60, 90),
        ]
        kept, rejected = reader.reject_table_internal_gutters(
            [candidate], reader.table_cell_x_boundaries([self.table(cells)])
        )
        self.assertEqual(kept, [])
        self.assertEqual([g["mid"] for g in rejected], [candidate["mid"]])

    def test_candidate_far_from_cell_boundaries_retained(self):
        pw = 600.0
        candidate = self.gutter(pw * 0.649)
        cells = [(pw * 0.25, 50, pw * 0.40, 90), (pw * 0.40, 50, pw * 0.55, 90)]
        kept, rejected = reader.reject_table_internal_gutters(
            [candidate], reader.table_cell_x_boundaries([self.table(cells)])
        )
        self.assertEqual(rejected, [])
        self.assertEqual([g["mid"] for g in kept], [candidate["mid"]])

    def test_bbox_overlap_alone_does_not_reject(self):
        # p6 0.649 pattern: cells live only in the left part of the page, so
        # any bounding box spanning the gutter would overlap it — but no cell
        # COLUMN boundary is near the gutter, so it must survive.
        pw = 600.0
        candidate = self.gutter(pw * 0.649)
        cells = [(pw * 0.25, 50, pw * 0.40, 90), (pw * 0.40, 50, pw * 0.45, 90)]
        kept, rejected = reader.reject_table_internal_gutters(
            [candidate], reader.table_cell_x_boundaries([self.table(cells)])
        )
        self.assertEqual(rejected, [])
        self.assertEqual(len(kept), 1)

    def test_no_tables_rejects_nothing(self):
        pw = 600.0
        candidates = [self.gutter(150.0), self.gutter(400.0)]
        for empty in ([], [self.table([])]):
            kept, rejected = reader.reject_table_internal_gutters(
                candidates, reader.table_cell_x_boundaries(empty)
            )
            self.assertEqual(rejected, [])
            self.assertEqual([g["mid"] for g in kept], [150.0, 400.0])

    def test_table_cell_x_boundaries_dedupes_and_ignores_rows(self):
        cells = [
            (100.0, 50, 200.0, 90),   # shares x edges with the cells below
            (100.0, 90, 200.0, 130),  # horizontal row boundary only
            (200.0, 50, 300.0, 90),
        ]
        bounds = reader.table_cell_x_boundaries([self.table(cells)])
        self.assertEqual(bounds, [100.0, 200.0, 300.0])

    def test_single_region_detection_unchanged_with_guard(self):
        pw = 600.0
        words = grid_words([40], pw)
        gutters = reader.detect_region_gutters(words, pw)
        kept, rejected = reader.reject_table_internal_gutters(
            gutters, [pw * 0.5]
        )
        self.assertEqual(gutters, [])
        self.assertEqual(kept, [])
        self.assertEqual(rejected, [])

    def test_two_region_detection_survives_guard_with_far_table(self):
        pw = 600.0
        words = grid_words([40, 40], pw)
        gutters = reader.detect_region_gutters(words, pw)
        self.assertEqual(len(gutters), 1)
        # Table cells far from the gutter: nothing rejected.
        cells = [(50.0, 700, 90.0, 740)]
        kept, rejected = reader.reject_table_internal_gutters(
            gutters, reader.table_cell_x_boundaries([self.table(cells)])
        )
        self.assertEqual(rejected, [])
        self.assertEqual(len(kept), 1)


if __name__ == "__main__":
    unittest.main()
