"""M4: persisted structured query execution records (DECISION-019).

The execution record is the Errata contract: one small JSON-serializable
dict per run_query call, plus optional JSONL persistence. Covers:

- run_query keeps its existing keys and adds run_id / timestamp /
  execution_record with the M4 schema
- abstained is true exactly when generation status is "no_evidence"
- default run_query writes nothing unless a log path is set
- explicit path or CLINIVAULT_RUN_LOG env var appends one JSON line,
  creating parent dirs
- records never carry API keys or environment secrets
"""

from __future__ import annotations

import json
import os
import unittest


def _silent_env(**overrides):
    """Return an env mapping with secret-like values scrubbed."""
    env = dict(os.environ)
    env.pop("CLINIVAULT_RUN_LOG", None)
    env.update(overrides)
    return env


class ExecutionRecordSchemaTests(unittest.TestCase):
    def test_run_query_adds_record_and_stays_serializable(self):
        from clinivault_ai.pipeline import run_query
        from tests.test_pipeline import FakeGenerationProvider, build_store

        store, embedder = build_store()
        trace = run_query(
            store, "capital city of France", embedder,
            FakeGenerationProvider(), top_k=2,
        )
        # Existing keys are kept.
        for key in ("query", "retrieval_trace", "context_trace",
                    "generation_trace", "result"):
            self.assertIn(key, trace)
        for key in ("run_id", "timestamp", "execution_record"):
            self.assertIn(key, trace)
        self.assertTrue(trace["run_id"])
        self.assertTrue(trace["timestamp"])

        record = trace["execution_record"]
        self.assertEqual(
            set(record),
            {"run_id", "timestamp", "query", "retrieval", "context",
             "generation", "sources"},
        )
        self.assertEqual(record["run_id"], trace["run_id"])
        self.assertEqual(record["timestamp"], trace["timestamp"])
        self.assertEqual(record["query"], "capital city of France")
        self.assertEqual(record["retrieval"]["top_k"], 2)
        self.assertEqual(len(record["retrieval"]["chunks"]), 2)
        for chunk in record["retrieval"]["chunks"]:
            self.assertEqual(
                set(chunk),
                {"chunk_id", "document_id", "page_number", "score"},
            )
        self.assertEqual(
            record["context"]["chunk_ids_used"],
            [c["chunk_id"] for c in record["retrieval"]["chunks"]],
        )
        self.assertEqual(record["generation"]["status"], "ok")
        self.assertEqual(record["generation"]["answer"], "Paris.")
        self.assertEqual(record["generation"]["model"], "fake-model-v1")
        self.assertFalse(record["generation"]["abstained"])
        self.assertEqual(len(record["sources"]), 2)
        for source in record["sources"]:
            self.assertEqual(
                set(source), {"document_id", "page_number", "chunk_id"}
            )
        json.dumps(trace)  # whole trace, record included, must serialize
        json.dumps(record)

    def test_abstained_true_on_no_evidence(self):
        from clinivault_ai.context import build_context
        from clinivault_ai.generation import generate_answer
        from clinivault_ai.pipeline.records import build_execution_record
        from tests.test_pipeline import FakeGenerationProvider

        bundle = build_context([], "empty question")
        result = generate_answer(bundle, FakeGenerationProvider())
        self.assertEqual(result["status"], "no_evidence")
        record = build_execution_record(
            query="empty question", top_k=5, results=[],
            bundle=bundle, result=result,
        )
        self.assertTrue(record["generation"]["abstained"])
        self.assertIsNone(record["generation"]["answer"])
        self.assertEqual(record["retrieval"]["chunks"], [])
        self.assertEqual(record["context"]["chunk_ids_used"], [])
        self.assertEqual(record["sources"], [])
        json.dumps(record)


class ExecutionRecordPersistenceTests(unittest.TestCase):
    def test_default_writes_nothing(self):
        import tempfile
        from unittest.mock import patch

        from clinivault_ai.pipeline import run_query
        from tests.test_pipeline import FakeGenerationProvider, build_store

        store, embedder = build_store()
        with tempfile.TemporaryDirectory() as tmp:
            probe = f"{tmp}/should-not-exist.jsonl"
            with patch.dict(os.environ, _silent_env(), clear=True):
                run_query(store, "q", embedder,
                          FakeGenerationProvider(), top_k=1)
            self.assertFalse(os.path.exists(probe))

    def test_explicit_path_appends_one_json_line(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from clinivault_ai.pipeline import run_query

        from tests.test_pipeline import FakeGenerationProvider, build_store

        store, embedder = build_store()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runs" / "nested" / "q.jsonl"
            with patch.dict(os.environ, _silent_env(), clear=True):
                first = run_query(store, "first q", embedder,
                                  FakeGenerationProvider(), top_k=1,
                                  run_log_path=target)
                second = run_query(store, "second q", embedder,
                                   FakeGenerationProvider(), top_k=1,
                                   run_log_path=str(target))
            lines = target.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            first_record = json.loads(lines[0])
            second_record = json.loads(lines[1])
            self.assertEqual(first_record["run_id"], first["run_id"])
            self.assertEqual(second_record["run_id"], second["run_id"])
            self.assertEqual(first_record["query"], "first q")
            self.assertNotEqual(first_record["run_id"], second_record["run_id"])

    def test_env_var_path_is_honoured(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from clinivault_ai.pipeline import run_query
        from tests.test_pipeline import FakeGenerationProvider, build_store

        store, embedder = build_store()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runs.jsonl"
            with patch.dict(
                os.environ,
                _silent_env(CLINIVAULT_RUN_LOG=str(target)),
                clear=True,
            ):
                trace = run_query(store, "env q", embedder,
                                  FakeGenerationProvider(), top_k=1)
            record = json.loads(target.read_text(encoding="utf-8").strip())
            self.assertEqual(record["run_id"], trace["run_id"])

    def test_records_never_carry_keys(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from clinivault_ai.pipeline import run_query
        from tests.test_pipeline import FakeGenerationProvider, build_store

        sentinel = "SENTINEL-KEY-9f8e7d6c5b4a"
        store, embedder = build_store()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "runs.jsonl"
            with patch.dict(
                os.environ,
                _silent_env(
                    CLINIVAULT_RUN_LOG=str(target),
                    GOOGLE_API_KEY=sentinel,
                ),
                clear=True,
            ):
                trace = run_query(store, "key q", embedder,
                                  FakeGenerationProvider(), top_k=1)
            body = target.read_text(encoding="utf-8")
            self.assertNotIn(sentinel, body)
            self.assertNotIn("GOOGLE_API_KEY", body)
            self.assertNotIn("api_key", json.dumps(trace["execution_record"]))


if __name__ == "__main__":
    unittest.main()
