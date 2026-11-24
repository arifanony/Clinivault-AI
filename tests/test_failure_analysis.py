"""Tests for the failure-class boundaries in evaluation.failure_analysis.

Only the pure classification logic is unit-tested here; the full analysis
needs the E5 model cache and runs through the module CLI, the same split
the benchmark itself uses.
"""

import unittest

from clinivault_ai.evaluation.failure_analysis import classify_rank


class ClassifyRankTests(unittest.TestCase):
    def test_rank_one_is_hit(self):
        self.assertEqual(classify_rank(1), "HIT1")

    def test_ranks_two_to_five_are_ranking(self):
        for rank in (2, 3, 4, 5):
            self.assertEqual(classify_rank(rank), "RANKING")

    def test_ranks_six_to_twenty_are_near_miss(self):
        for rank in (6, 12, 20):
            self.assertEqual(classify_rank(rank), "NEAR_MISS")

    def test_rank_beyond_pool_is_deep_miss(self):
        self.assertEqual(classify_rank(21), "DEEP_MISS")
        self.assertEqual(classify_rank(120), "DEEP_MISS")

    def test_absent_chunk_is_deep_miss(self):
        self.assertEqual(classify_rank(None), "DEEP_MISS")


if __name__ == "__main__":
    unittest.main()
