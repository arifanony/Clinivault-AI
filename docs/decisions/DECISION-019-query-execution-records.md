# Engineering Decision: Persisted structured query execution records

## Status

Chosen

## Date

2026-11-10

## Problem

`run_query` returns its traces in memory only (M1–M7 guide: no `run_id`
file). Each UI query therefore leaves nothing on disk that Errata — the
separate evaluation product — could later read: no stable run identity,
no timestamp, and no small per-query record of what was retrieved, what
reached context, and what the model answered. Reconstructing a run means
re-running it.

## What This Part of the System Does

- What goes in: the outputs of one `run_query` call — the ranked
  retrieval results, the context bundle, and the generation result —
  plus the query and `top_k`.
- What happens inside: `clinivault_ai.pipeline.records`
  builds one small JSON-serializable record and, only when a log path is
  configured, appends it as a single JSON line.
- What comes out: `run_id`, `timestamp`, and `execution_record` on the
  `run_query` return (existing keys unchanged), and optionally one JSONL
  line per run under gitignored `runs/`.
- Where the output goes next: the JSONL file and the in-memory
  `execution_record` are the contract Errata reads later; no Errata
  logic lives here.

## Requirements

- Keep every existing `run_query` key byte-for-byte; add `run_id`,
  `timestamp`, and `execution_record` only.
- Record schema (exactly):
  `run_id, timestamp, query`,
  `retrieval.top_k`, `retrieval.chunks[{chunk_id, document_id,
  page_number, score}]`,
  `context.chunk_ids_used`,
  `generation.{model, answer, abstained, status}`,
  `sources[{document_id, page_number, chunk_id}]`.
- `abstained` is true exactly when generation `status` is
  `"no_evidence"` (M4; M5 may extend it).
- Default writes nothing. An explicit `run_log_path` wins; otherwise
  `$CLINIVAULT_RUN_LOG` is honoured when set and non-blank.
- Never persist API keys, `.env` contents, prompts, or vectors — the
  record carries provenance and outcomes only.
- Log-write errors propagate instead of silently dropping records.

## Options We Considered

- Option A: small record builder + opt-in JSONL append in the pipeline
  package (chosen).
- Option B: persist the full trace (retrieval/context/generation traces
  with prompt text and timings). Rejected: larger, duplicates the
  in-memory trace, and pulls prompt text into a log Errata does not
  need.
- Option C: always-on logging to a default `runs/` file. Rejected: every
  test and benchmark run would spray files into the working tree; the
  guide requires opt-in.

## Comparison

Option A is the smallest change that closes the gap: no stage behavior
changes, existing callers keep working (new `run_query` parameter is
optional), the default run writes nothing so the existing suite stays
clean, and the persisted artifact is exactly the Errata contract —
nothing more.

## Decision

M4 implements `clinivault_ai.pipeline.records` (`build_execution_record`
/ `resolve_run_log_path` / `append_execution_record`), wires it into
`run_query` with an optional `run_log_path` parameter plus
`$CLINIVAULT_RUN_LOG` fallback, git-ignores `runs/`, and documents the
record as the Errata contract in `docs/pipelines/execution-recording.md`.

## Why We Chose It

OBSERVED: `run_query` already produces everything the record needs
(results, bundle, result); the record is a projection, not a new data
source. The generation result already carries `model`/`answer`/`status`,
so `abstained` is a pure function of `status` with no new signals to
measure.

## Trade-offs

Log-write failures fail the query instead of being swallowed; callers
that configure logging accept that a full disk surfaces as an error.
The record omits evidence text and prompt text by design, so a consumer
that wants verbatim evidence still reads the in-memory trace.

## What We Did Not Choose

Full-trace persistence. Always-on logging. Any key, secret, or
environment capture. A vector database, hybrid retrieval, or reranking —
M6 remains deferred until a measured weakness appears after M1–M5.

## Assumptions

`runs/` stays gitignored and local; anything that needs to survive
across machines moves through an explicit channel, never through git.
The manifest remains the source of truth for catalog fields; M4 adds no
metadata.

## How We Will Validate This

- `python -m unittest tests.test_execution_records` (6 tests: schema,
  abstention, default-no-write, explicit-path append, env-var path,
  no-keys).
- Full gate `python -m unittest discover -s tests` with no new failures
  beyond the known sandbox-proxy loopback error.
- Record file check: two runs append two JSON lines; file text contains
  no `GOOGLE_API_KEY` or key material.

## When We Should Revisit It

When M5 extends abstention beyond `"no_evidence"`, when Errata needs
fields beyond the M4 schema (new decision, additive fields only), or
when a production API needs request-scoped logging instead of a local
JSONL file.
