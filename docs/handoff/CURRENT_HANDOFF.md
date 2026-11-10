# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git as canonical when resuming. Prefer this file plus
> [M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and
> `git log -1`.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Last completed milestone:** **M7** — production deploy slice
  (DECISION-021), implemented and tested in the working tree (commit
  with the M7 message below, then push).
- **Last pushed commit:** `c320d04` (`docs: defer M6 retrieval
  changes, no measured weakness`). M5 (`51d89c2`) and M6 are pushed.
- **M6-scope check:** complete — deferred with no code change (see
  `docs/engineering-log/2026-11-10-m6-deferred.md`); no specific
  measured retrieval weakness after M1–M5.
- **Working-tree expectation:** M7 files (see below); `runs/`
  stays gitignored and unwritten by default; untracked scratch removed
  before commit.
- **Intentionally ignored/protected local files:** `.env` is ignored and must
  never be staged or committed. Copy `.env.example` locally and set
  `GOOGLE_API_KEY` only on the machine. Never print or paste keys.

## Last Completed Unit

- **Unit/task:** M5 / deterministic answer reliability (DECISION-020)
- **What was completed:** citation-ref parsing (`EVIDENCE_ITEM_RANK` /
  `EVIDENCE_ITEM_CHUNK_ID` checked against supplied evidence;
  `invalid_citations[{kind, value}]` on the result), `ABSTAIN:` refusal
  sentinel (status `abstained`, `abstained: true` in the record),
  `max_chars` context budget (lowest-rank tail dropped whole items,
  `truncated_chunk_ids` in bundle/trace/record; rank 1 always kept),
  Gemini retry on 429/5xx only (`max_attempts=3`, doubling backoff;
  `attempts` on success and failure; 401/403 raise at once), and a
  3-case labeled set (in-scope supported, DECISION-005 out-of-scope
  refusal, empty evidence) with citation-validity and
  abstention-correctness metrics. No AI judges, no score threshold.
  (Committed and pushed as `51d89c2`; detail preserved in that commit,
  DECISION-020, and the M5 pipeline/engineering-log docs.)

- **Unit/task:** M6-scope check (no code change — deferred per §M6;
  committed and pushed as `c320d04`)
- **What was decided:** no specific measured retrieval weakness after
  M1–M5, so no hybrid/rerank/BM25/Top-K experiment was run (see
  `docs/engineering-log/2026-11-10-m6-deferred.md`).
- **Unit/task:** M7 / production deploy slice (DECISION-021)
- **What was completed:** FastAPI query API over the unchanged
  pipeline (`POST /query` with `query`/`top_k`/`max_chars`/`api_key`,
  `GET /health`), per-request `GeminiProvider` (body key or env,
  never persisted), secret-free JSON access logs (method/path/status/
  duration/`run_id` only), `Dockerfile`, GitHub Actions CI gate.
  No stage semantics changed; UI untouched; no Qdrant; no T2D-004.
- **Important files:**
  - `src/clinivault_ai/api/app.py` (new), `__init__.py` (new),
    `__main__.py` (new)
  - `tests/test_api.py` (new, 13 tests)
  - `Dockerfile` (new), `.github/workflows/ci.yml` (new)
  - `pyproject.toml`, `uv.lock` (fastapi/uvicorn/httpx)
  - `docs/decisions/DECISION-021-production-api-container-ci.md` (new)
  - `docs/pipelines/production-api.md` (new)
  - `docs/decisions/README.md`, `docs/architecture/README.md`,
    `README.md`, `docs/pipelines/README.md`
  - `docs/handoff/CURRENT_HANDOFF.md`,
    `docs/handoff/M1-M7-IMPLEMENTATION-GUIDE.md`
- **Tests/gates:**
  - `python -m unittest tests.test_api` — 13 tests OK (run in the
    project `.venv` via `uv run`; 3 failed honestly first for store
    top_k bounds and log capture, then fixed)
  - `python -m unittest discover -s tests` — full gate per the loop
    below (E5 tests skip without the HF cache; the sandbox-proxy
    `test_ui` note from M4 still applies)
  - No retrieval-math change (API wraps `run_query` unchanged)
- **Relevant Decision / Pipeline:**
  - `docs/decisions/DECISION-021-production-api-container-ci.md`
  - `docs/pipelines/production-api.md`

## Current Technical Understanding

### OBSERVED

- Production query embedding uses `embed_texts` with **no** `query:` /
  `passage:` prefixes (same path as frozen EVAL-HF-003 raw winner).
- E5 artifacts live under `data/embedded-intfloat--e5-small-v2/` (384-d).
  Hash artifacts under `data/embedded/` (256-d) are untouched.
- `E5EmbeddingProvider` uses `local_files_only=True`. Empty HF cache fails
  loud; no silent hash fallback in the UI.
- UI indexes the merged nine-document corpus (727 chunks) built once at
  startup; `--single-doc` keeps the legacy T2D-001 path.
- Corpus stores carry `document_id=None`; per-hit provenance comes from
  each record. Mixed embedding models across corpus artifacts fail loud.
- Catalogued records/results/bundles carry optional `document_name`
  (M3, DECISION-018); unknown IDs keep their exact historical shape.
- Nine ingestion reports under `data/ingestion-report/` are all `success`
  (181 pages, 727 chunks).
- Every `run_query` return carries `run_id`, `timestamp`, and
  `execution_record` (M4, DECISION-019); JSONL persists only when
  `run_log_path` or `$CLINIVAULT_RUN_LOG` is set, under gitignored
  `runs/`, with no keys, prompts, or vectors.
- Generation results carry `status ∈ ok/no_evidence/abstained`,
  `attempts`, and `invalid_citations` (M5, DECISION-020); the
  `ABSTAIN:` sentinel marks refusals on non-empty evidence.
- `build_context` accepts `max_chars` (M5): lowest-rank tail dropped
  whole items, `truncated_chunk_ids` in bundle/trace/record; rank 1
  always kept; `None` is exact pre-M5 behavior.
- `GeminiProvider` retries 429/5xx up to `max_attempts` (default 3)
  with doubling backoff; 401/403 raise at once (M5, DECISION-020).
- Query API (`src/clinivault_ai/api`, M7, DECISION-021) serves the same
  startup-loaded index over `POST /query` / `GET /health`, with a
  per-request `GeminiProvider` and secret-free JSON access logs; the
  UI is untouched. Tests run in the project `.venv` (`uv run`).

### INFERENCE

- M1–M7 are done (M6 deferred, docs-only). The API wraps `run_query`
  unchanged, so pipeline semantics are inherited from M1–M5, not
  re-proven by M7.

### NOT YET VALIDATED

- End-to-end Gemini answers over the API or UI with E5 evidence over
  the corpus (needs key + model cache; never run from this machine).
- `section` detection — deliberately absent until a deterministic detector
  is measured (DECISION-018).
- A failure-class breakdown of E5's residual benchmark misses — the
  prerequisite that would reopen M6.

## Next Authorized Action

**Nothing is queued — the M1–M7 MVP is complete** (M6 deferred,
docs-only). Any further work (Stage-2 corpus, workers/Qdrant,
auth/rate-limits, claim-level verification) needs its own decision
and an explicit fresh authorization. Do not start anything unasked.

## Resume Procedure (other device)

```text
git pull
git status --short
git log -5 --oneline
uv sync
uv sync --extra semantic
copy .env.example .env
# set GOOGLE_API_KEY in .env locally; never commit .env
.venv\Scripts\python -m unittest discover -s tests
# optional gate:
.venv\Scripts\python -m clinivault_ai.evaluation.benchmark --provider e5
```

If E5 load fails with missing model files, download once outside production
code (explicit `SentenceTransformer('intfloat/e5-small-v2')` into the HF
cache), then retry. Do not change `local_files_only=True`.

Genesis CLI is optional; skip if Node/`genesis` is missing. **Never
hand-edit** `.genesis/project.json`.

Then open the M1–M7 guide; M1–M7 are complete, so there is no
next step until new work is authorized.

## Important Rules

- One milestone per session; stop after commit.
- Do not expand into M6+ without a new authorization.
- Protect `.env`; never commit secrets or put Gemini keys in URLs (`?key=`).
  Use `x-goog-api-key` header only.
- Distinguish OBSERVED / INFERENCE / NOT YET VALIDATED in engineering logs.
- Test gate is **unittest**, not pytest. Default Python via `uv` (3.14+).
- Never overwrite hash embedding JSON when touching E5 paths.
- T2D-004 is blocked-access — do not invent a substitute PDF.
