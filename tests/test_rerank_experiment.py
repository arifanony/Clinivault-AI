"""Tests for the rerank experiment's pure logic and frozen protocol.

The experiment itself needs the E5 and cross-encoder model caches and
runs through the module CLI, the same split the benchmark uses. What is
unit-tested here: the per-case movement classification and that the
experiment's protocol constants still match DECISION-022 (pool of 20,
production top-5, E5 baseline unchanged).
"""

import unittest

from clinivault_ai.evaluation.rerank_experiment import (
    POOL,
    RERANK_MODEL,
    TOP_K,
    _movement,
)


class MovementTests(unittest.TestCase):
    def test_improved(self):
        self.assertEqual(_movement(0.2, 0.5), "improved")
        self.assertEqual(_movement(0.0, 1.0), "improved")

    def test_regressed(self):
        self.assertEqual(_movement(1.0, 0.0), "regressed")
        self.assertEqual(_movement(0.5, 0.3333), "regressed")

    def test_unchanged(self):
        self.assertEqual(_movement(0.5, 0.5), "unchanged")
        self.assertEqual(_movement(0.0, 0.0), "unchanged")


class ProtocolTests(unittest.TestCase):
    def test_pool_and_top_k_match_decision_022(self):
        self.assertEqual(POOL, 20)
        self.assertEqual(TOP_K, 5)

    def test_rerank_model_is_the_recorded_candidate(self):
        self.assertEqual(RERANK_MODEL,
                         "cross-encoder/ms-marco-MiniLM-L-6-v2")


if __name__ == "__main__":
    unittest.main()
