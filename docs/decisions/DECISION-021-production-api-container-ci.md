# Engineering Decision: Production query API, container, and CI (M7)

## Status

Chosen

## Date

2026-11-10

## Problem

M1–M6 built a working pipeline (retrieval → context → generation with
reliability checks) that is only reachable through the stdlib
observability UI (`src/clinivault_ai/ui/app.py`) and direct Python
calls. There is no machine-facing query interface, no container image,
no CI gate, and no JSON service logging — so the system cannot be
deployed, integrated (e.g. by Errata over HTTP), or built reproducibly
outside a developer checkout. The M1–M7 guide scopes M7 as exactly this
MVP deploy slice: query API, container, CI — not a rewrite, no Qdrant,
no Stage-2 corpus work.

## What This Part of the System Does

- What goes in: the already-built `run_query(store, query,
  embedding_provider, generation_provider, top_k, max_chars)` seam plus
  the committed artifact trees and the `load_store` startup wiring.
- What happens inside: a FastAPI application exposes one query endpoint
  and one health endpoint; the index is built once at startup and
  reused per request; each request gets a fresh `GeminiProvider`
  (request API key or environment fallback); access is logged as JSON
  lines on stdout with no secrets, prompts, vectors, or answer text.
- What comes out: HTTP JSON — a curated query response
  (`run_id`/`timestamp`/`query`/`answer`/`status`/`abstained`/`model`/
  `attempts`/`invalid_citations`/`sources`/`retrieval`/`context`) and a
  health response (`status`/`document_count`/`chunk_count`/
  `embedding_model`).
- Where the output goes next: deployment (container), external
  integrators over HTTP, and the existing opt-in JSONL execution
  records (unchanged `CLINIVAULT_RUN_LOG` passthrough).

## Requirements

- Wrap `run_query` without changing any stage: identical retrieval,
  context, generation, and record semantics; validation mirrors the UI
  (`top_k` 1–50; `max_chars` positive int or omitted).
- Keep the stdlib UI untouched as the inspector; the API is additive.
- Never return or log API keys, environment values, prompts, or
  vectors. Request logs carry method/path/status/duration/`run_id`
  only — no query text, no answers.
- Fail loud on mixed-embedding-model corpus artifacts (reuse the
  existing `load_store` guard); fail startup when the E5 model cache
  is absent under `--provider e5` (no silent hash fallback, per
  DECISION-017).
- Offline-capable default test path: API tests run with fake
  providers and synthetic stores (no network, no keys, no E5 cache).
- `Dockerfile` builds a runnable image exposing one port; GitHub
  Actions runs `uv sync` + the unittest gate (E5 tests skip without
  cache, as before).
- No Qdrant, no vector database, no T2D-004 acquisition (blocked
  access — never bypass 403), no new corpus in this unit.

## Options We Considered

- Option A: FastAPI app + Dockerfile + GitHub Actions CI, stdlib JSON
  access logs, in-memory index (chosen).
- Option B: extend the stdlib `http.server` UI into the production
  API. Rejected: hand-rolled routing/validation duplicates what
  FastAPI provides, and the UI module's contract is a browser
  inspector, not a machine interface.
- Option C: add Qdrant (or another vector DB) now. Rejected: the
  in-memory index holds 727 chunks with deterministic behavior and no
  measured capacity or concurrency pressure; a database would add an
  unneeded service, driver, and persistence story to the MVP slice.
- Option D: gunicorn/uvicorn workers + structured-logging library
  (structlog). Rejected for now: a single uvicorn process and stdlib
  `logging` with a small JSON formatter meet the slice; workers and
  richer logging are operational tuning for measured load, not
  first-deploy requirements.

## Comparison

| Criterion | A: FastAPI slice | B: stdlib extension | C: +Qdrant |
|---|---|---|---|
| Machine interface | Typed, validated | Hand-rolled | Same as A |
| New moving parts | One process | None, but more code | +DB service |
| Justified by measurements | Yes (nothing needs more) | Yes | No (no pressure) |
| Testability offline | Yes (TestClient+fakes) | Yes | Needs DB fixture |

## Decision

Option A. M7 ships a FastAPI query API over the unchanged pipeline,
a Dockerfile, and a GitHub Actions CI gate, with stdlib JSON access
logging and the in-memory index.

## Why We Chose It

- It is the smallest slice that makes the system deployable and
  integrable: one process, one port, the exact `run_query` semantics
  the benchmarks and reliability checks already pin down.
- It reuses the hardened paths instead of forking them: `load_store`
  startup wiring (with its fail-loud model guard), `run_query`
  traces/records, and the UI's validation ranges.
- It preserves the evidence-first contracts: the response is the
  execution record plus answer metadata — no prompts, vectors, or
  keys cross the boundary, and logging is explicitly secret-free.

## Trade-offs

- Single-process uvicorn: no multi-worker concurrency story yet;
  adequate for the MVP slice, not for load.
- `max_chars` still counts characters, not tokens (inherited from M5).
- The image bakes no E5 model weights and no API key: deployment must
  provide the Hugging Face cache (volume) and `GOOGLE_API_KEY`
  (secret), documented in the Dockerfile comments.

## What We Did Not Choose

Qdrant or any vector database, a second retrieval path,
token-based budgeting, multi-worker serving, structlog, T2D-004
acquisition, or any change to pipeline/benchmark/labels/Top-K.

## Assumptions

- `fastapi`/`uvicorn`/`httpx` enter default dependencies (offline
  tests use TestClient + fakes; no live network in the gate).
- Deployments needing E5 serve the model cache and key from outside
  the image; `--provider hash` remains the keyless smoke path.
- 727 chunks fit comfortably in memory for the foreseeable MVP load.

## How We Will Validate This

- `tests/test_api.py`: health shape, query happy path, validation
  rejections (empty query, bad `top_k`/`max_chars`), abstention
  mapping, invalid-citation passthrough, no-secret response/log scan,
  per-request key isolation.
- Full gate `python -m unittest discover -s tests` green (minus the
  known sandbox-proxy `test_ui` 502 and E5-cache skips).
- Docker build of the committed `Dockerfile` (where a daemon is
  available); CI workflow runs the same gate on push/PR.

## When We Should Revisit It

- Measured concurrency or memory pressure from real traffic (then:
  workers, Qdrant, caching — with numbers).
- An integrator needs auth, rate limits, or streaming (explicit new
  requirements, not completeness).
- A second corpus or Stage-2 documents change the index-size
  assumption.
