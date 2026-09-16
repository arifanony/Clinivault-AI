"""Unit tests for the retrieval benchmark metric functions (synthetic inputs)."""

import unittest

from clinivault_ai.evaluation import metrics


class HitTests(unittest.TestCase):
    def test_hit1_when_first(self):
        self.assertEqual(metrics.hit_at_k(["a", "b"], ["a"], 1), 1)

    def test_hit1_when_not_first(self):
        self.assertEqual(metrics.hit_at_k(["a", "b"], ["b"], 1), 0)

    def test_hit5_within_five(self):
        self.assertEqual(metrics.hit_at_k(["x", "y", "z", "q", "a"], ["a"], 5), 1)

    def test_hit5_outside_five(self):
        self.assertEqual(
            metrics.hit_at_k(["x1", "x2", "x3", "x4", "x5", "a"], ["a"], 5), 0
        )

    def test_hit_at_k_rejects_bad_k(self):
        with self.assertRaises(ValueError):
            metrics.hit_at_k(["a"], ["a"], 0)


class ReciprocalRankTests(unittest.TestCase):
    def test_rr_first(self):
        self.assertEqual(metrics.reciprocal_rank(["a"], ["a"]), 1.0)

    def test_rr_third(self):
        self.assertEqual(metrics.reciprocal_rank(["x", "y", "a"], ["a"]), 1 / 3)

    def test_rr_absent(self):
        self.assertEqual(metrics.reciprocal_rank(["x", "y"], ["a"]), 0.0)


class FirstRelevantRankTests(unittest.TestCase):
    def test_none_when_absent(self):
        self.assertIsNone(metrics.first_relevant_rank(["x"], ["a"]))

    def test_returns_one_based_rank(self):
        self.assertEqual(metrics.first_relevant_rank(["x", "a", "a2"], ["a"]), 2)


class MultipleRelevantTests(unittest.TestCase):
    def test_uses_highest_ranked_relevant(self):
        self.assertEqual(metrics.reciprocal_rank(["a", "x", "b"], ["b", "a"]), 1.0)

    def test_all_relevant_ranks_sorted(self):
        self.assertEqual(metrics.all_relevant_ranks(["b", "x", "a"], ["a", "b"]),
                         [1, 3])

    def test_all_relevant_ranks_partial_presence(self):
        self.assertEqual(metrics.all_relevant_ranks(["x", "a"], ["a", "b"]), [2])


class ValidationTests(unittest.TestCase):
    def test_empty_relevant_rejected(self):
        with self.assertRaises(ValueError):
            metrics.reciprocal_rank(["a"], [])

    def test_duplicate_relevant_rejected(self):
        with self.assertRaises(ValueError):
            metrics.hit_at_k(["a"], ["a", "a"], 5)

    def test_duplicate_ranked_rejected(self):
        with self.assertRaises(ValueError):
            metrics.reciprocal_rank(["a", "a"], ["a"])


class MrrTests(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(metrics.mrr([1.0, 0.5, 0.0]), 0.5)

    def test_mean_is_order_insensitive(self):
        rrs = [0.5, 1.0, 0.25]
        self.assertEqual(metrics.mrr(rrs), metrics.mrr(list(reversed(rrs))))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            metrics.mrr([])


class DeterminismTests(unittest.TestCase):
    """The same inputs must always produce the same metrics."""

    def test_repeated_runs_identical(self):
        ranked = ["x", "b", "a", "c"]
        relevant = ["a", "c"]
        first = (metrics.hit_at_k(ranked, relevant, 1),
                 metrics.hit_at_k(ranked, relevant, 5),
                 metrics.reciprocal_rank(ranked, relevant),
                 metrics.first_relevant_rank(ranked, relevant),
                 metrics.all_relevant_ranks(ranked, relevant))
        second = (metrics.hit_at_k(ranked, relevant, 1),
                  metrics.hit_at_k(ranked, relevant, 5),
                  metrics.reciprocal_rank(ranked, relevant),
                  metrics.first_relevant_rank(ranked, relevant),
                  metrics.all_relevant_ranks(ranked, relevant))
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
