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


if __name__ == "__main__":
    unittest.main()
