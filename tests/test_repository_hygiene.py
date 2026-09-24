"""Repository hygiene checks that keep duplicated records from drifting."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class RepositoryHygieneTests(unittest.TestCase):
    def test_initial_corpus_manifest_copies_are_identical(self):
        root_copy = REPO_ROOT / "clinivault_initial_corpus_manifest.md"
        docs_copy = REPO_ROOT / "docs" / "corpus" / "initial-corpus-manifest.md"
        self.assertEqual(root_copy.read_bytes(), docs_copy.read_bytes())

    def test_env_example_exists_without_secrets(self):
        example = REPO_ROOT / ".env.example"
        text = example.read_text(encoding="utf-8")
        self.assertIn("GOOGLE_API_KEY=", text)
        for line in text.splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                self.assertEqual(line.split("=", 1)[1].strip(), "")


if __name__ == "__main__":
    unittest.main()
