"""Structured query execution records for the Errata contract (M4, M5).

One record per :func:`clinivault_ai.pipeline.run_query` call: a small
JSON-serializable dict with the M4 schema plus the M5 extensions
(``"abstained"`` status abstention, ``truncated_chunk_ids``). Records
carry provenance and outcomes only — never prompts, vectors, API keys,
or environment values.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

RUN_LOG_ENV_VAR = "CLINIVAULT_RUN_LOG"


def new_run_id() -> str:
    """Return a fresh unique run identifier."""
    return uuid.uuid4().hex


def new_timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def build_execution_record(
    *,
    query: str,
    top_k: int,
    results: list[dict],
    bundle: dict,
    result: dict,
    run_id: str | None = None,
    timestamp: str | None = None,
) -> dict:
    """Build the M4 execution record from one pipeline run's outputs.

    Only the contracted fields are kept: chunk provenance, the ordered
    chunk ids used as context, and the generation outcome. ``abstained``
    is true when generation status is ``"no_evidence"`` (M4) or the M5
    ``"abstained"`` sentinel refusal. ``context`` also carries the M5
    ``truncated_chunk_ids`` (``[]`` when the budget kept everything).
    """
    evidence = bundle.get("evidence") if isinstance(bundle, dict) else []
    if not isinstance(evidence, list):
        evidence = []
    truncated = bundle.get("truncated_chunk_ids") if isinstance(bundle, dict) else []
    if not isinstance(truncated, list):
        truncated = []
    status = result.get("status") if isinstance(result, dict) else None
    chunks = [
        {
            "chunk_id": item["chunk_id"],
            "document_id": item["document_id"],
            "page_number": item["page_number"],
            "score": float(item["score"]),
        }
        for item in results
    ]
    return {
        "run_id": run_id or new_run_id(),
        "timestamp": timestamp or new_timestamp(),
        "query": query,
        "retrieval": {"top_k": top_k, "chunks": chunks},
        "context": {
            "chunk_ids_used": [item["chunk_id"] for item in evidence],
            "truncated_chunk_ids": list(truncated),
        },
        "generation": {
            "model": result.get("model"),
            "answer": result.get("answer"),
            "abstained": status in ("no_evidence", "abstained"),
            "status": status,
        },
        "sources": [
            {
                "document_id": item["document_id"],
                "page_number": item["page_number"],
                "chunk_id": item["chunk_id"],
            }
            for item in evidence
        ],
    }


def resolve_run_log_path(explicit: str | Path | None = None) -> Path | None:
    """Return where the next record should be appended, if anywhere.

    An explicit path wins; otherwise ``CLINIVAULT_RUN_LOG`` is honoured.
    Unset or blank means: do not write. The default never writes.
    """
    if explicit is not None:
        return Path(explicit)
    configured = (os.environ.get(RUN_LOG_ENV_VAR) or "").strip()
    return Path(configured) if configured else None


def append_execution_record(record: dict, path: str | Path) -> Path:
    """Append one record as a single JSON line, creating parents as needed."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return out
