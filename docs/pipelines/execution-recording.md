# Execution recording (M4)

Status: **implemented**. Each query produces one small structured
execution record — the contract Errata reads later. This document is
that contract, not Errata logic.

## What problem does this solve?

Runs used to exist only in memory: `run_query` returned traces and kept
nothing on disk. A later evaluator could not tell which run an answer
came from, when it ran, what was retrieved, or what the model decided.
The execution record fixes exactly that with one JSON-serializable dict
per run, optionally appended as one JSON line per run.

## What goes in?

The outputs of one `run_query(store, query, embedding_provider,
generation_provider, top_k=5)` call: ranked retrieval results, the
context bundle, and the generation result.

## What happens, step by step?

```
run_query inputs
  ↓
retrieval → context → generation (unchanged; traces collected as before)
  ↓
build_execution_record(query, top_k, results, bundle, result)
  → {run_id, timestamp, query, retrieval, context, generation, sources}
  ↓
return adds run_id + timestamp + execution_record (existing keys kept)
  ↓
IF run_log_path given → append record there
ELIF $CLINIVAULT_RUN_LOG set → append record there
ELSE → write nothing
```

`run_id` is a fresh hex id per call; `timestamp` is UTC ISO-8601.
`abstained` is true exactly when generation `status` is `"no_evidence"`.

## What comes out?

On the `run_query` return, existing keys are unchanged, plus:

```python
{query, retrieval_trace, context_trace, generation_trace, result,  # kept
 run_id,                    # hex string, unique per call
 timestamp,                 # UTC ISO-8601 string
 execution_record}          # the Errata contract, below
```

The record shape (exactly):

```json
{
  "run_id": "9f8e7d6c5b4a...",
  "timestamp": "2026-11-10T12:00:00+00:00",
  "query": "criteria for the diagnosis of diabetes",
  "retrieval": {
    "top_k": 5,
    "chunks": [
      {"chunk_id": "...", "document_id": "T2D-001",
       "page_number": 3, "score": 0.81}
    ]
  },
  "context": {"chunk_ids_used": ["..."]},
  "generation": {
    "model": "gemini-2.5-flash",
    "answer": "...",
    "abstained": false,
    "status": "ok"
  },
  "sources": [
    {"document_id": "T2D-001", "page_number": 3, "chunk_id": "..."}
  ]
}
```

`sources` follows evidence order (one entry per evidence item).
`answer` is null when `status` is `"no_evidence"`.

## Which components are involved?

- `src/clinivault_ai/pipeline/records.py` — `build_execution_record`,
  `resolve_run_log_path`, `append_execution_record`, `RUN_LOG_ENV_VAR`.
- `src/clinivault_ai/pipeline/__init__.py` — `run_query(..., *,
  run_log_path=None)`: builds the record, resolves the path, appends one
  line when configured.

## Which metadata is created or preserved?

`run_id` and `timestamp` are created per run. Retrieval provenance
(`chunk_id`, `document_id`, `page_number`, `score`), the ordered context
chunk ids, and the generation outcome (`model`, `answer`, `abstained`,
`status`) are preserved. Evidence text, prompt text, vectors, timings,
and usage stay in the in-memory trace only — they are not recorded.

## What can fail?

- Stage errors (retrieval/context/generation) propagate unchanged; no
  record is written when the run itself fails.
- A configured log path that cannot be created or written raises
  instead of silently dropping the record.

## How do we detect failure?

The query raises, so the caller sees it. The log file gains no line for
a failed run; a present line always corresponds to a completed run whose
`run_id` matches the returned trace.

## What evidence or logs does it produce?

One JSON object per line (JSONL) at the configured path, conventionally
under gitignored `runs/` (e.g. `runs/queries.jsonl`). Each line is one
`execution_record`. The default configures nothing and writes nothing,
so tests and benchmarks stay file-clean unless they opt in.

## What consumes the output next?

Errata, in its own repository, reads `execution_record` objects (from
the return value or the JSONL file) to evaluate retrieval, grounding,
and abstention. No Errata code lives here.

## Secrets rule

Records never contain API keys, `.env` contents, prompts, or vectors.
`GOOGLE_API_KEY` (environment or request-scoped) is never read by the
recorder and never appears in the file. `runs/` is gitignored and must
stay that way.

## Related decisions

- [DECISION-019](../decisions/DECISION-019-query-execution-records.md)
  (this milestone)
- [DECISION-011](../decisions/DECISION-011-grounded-generation-contract.md)
  (generation statuses, including `no_evidence`)
- [DECISION-007](../decisions/DECISION-007-generation-provider.md)
  (key handling: header only, never in URLs or logs)

## Known limitations

- `abstained` covers only the `"no_evidence"` path; M5 extends
  abstention (sentinel replies, citation checks) and will extend this
  contract additively.
- No log rotation, no request scoping, no concurrency protocol beyond
  single-line appends; a production API (M7) may need more.
