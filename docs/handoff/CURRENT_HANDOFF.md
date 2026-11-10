# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git as canonical when resuming. Prefer this file plus
> [M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and
> `git log -1`.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Last completed milestone:** **M5** — deterministic answer
  reliability (DECISION-020), committed and pushed as `51d89c2`.
- **Last pushed commit:** `51d89c2` (`feat: check citations,
  abstention sentinel, and context budget`).
  `master` matches `origin/master`.
- **M6-scope check:** complete — deferred with no code change (see
  `docs/engineering-log/2026-11-10-m6-deferred.md`); no specific
  measured retrieval weakness after M1–M5.
- **Working-tree expectation:** this handoff plus the M1–M7 guide
  refreshed for the M6 deferral; `runs/` stays gitignored and
  unwritten by default.
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

- **Unit/task:** M6-scope check (no code change — deferred per §M6)
- **What was decided:** no specific measured retrieval weakness after
  M1–M5, so no hybrid/rerank/BM25/Top-K experiment was run. Past
  weaknesses on record (T2D-006 near miss, T2D-009 statins lexical gap)
  were hash-era and already answered by M1's production move to raw E5
  (frozen 20/46 · 36/46 · 0.5583); M2–M5 changed no retrieval math
  (hash benchmark re-verified exactly in this unit: 12/46 · 26/46 ·
  0.3601). The missing prerequisite for any future M6 experiment is a
  failure-class breakdown of E5's residual misses.
- **Important files:**
  - `src/clinivault_ai/generation/citations.py` (new)
  - `src/clinivault_ai/generation/generator.py`
  - `src/clinivault_ai/generation/prompt.py`
  - `src/clinivault_ai/generation/provider.py`
  - `src/clinivault_ai/generation/__init__.py`
  - `src/clinivault_ai/context/builder.py`
  - `src/clinivault_ai/context/__init__.py`
  - `src/clinivault_ai/pipeline/__init__.py`
  - `src/clinivault_ai/pipeline/records.py`
  - `tests/test_answer_reliability.py` (new, 31 tests)
  - `docs/decisions/DECISION-020-answer-reliability.md` (new)
  - `docs/pipelines/answer-reliability.md` (new)
  - `docs/engineering-log/2026-11-10-m5-answer-reliability.md` (new)
  - `docs/decisions/README.md`, `docs/architecture/README.md`, `README.md`
  - `docs/engineering-log/2026-11-10-m6-deferred.md` (new, M6 deferral)
- **Tests/gates:**
  - `python -m unittest tests.test_answer_reliability` — 31 tests OK
    (written first; failed honestly before the source change)
  - `python -m unittest discover -s tests` — full gate per the loop
    below (E5 tests skip without the HF cache; the sandbox-proxy
    `test_ui` note from M4 still applies)
  - `benchmark --provider e5` numbers unchanged by M5 (no retrieval-math
    change): Hit@1 **20/46**, Hit@5 **36/46**, MRR **0.5583**
- **Relevant Decision / Pipeline:**
  - `docs/decisions/DECISION-020-answer-reliability.md`
  - `docs/pipelines/answer-reliability.md`

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

### INFERENCE

- M5 is done; retrieval math is unchanged by M5, so M6 stays a
  measurement question (deferred unless a concrete retrieval weakness
  appears after M1–M5).

### NOT YET VALIDATED

- End-to-end Gemini answers on the UI with E5 evidence over the corpus.
- `section` detection — deliberately absent until a deterministic detector
  is measured (DECISION-018).
- Hybrid / rerank (M6) — defer unless a measured weakness appears after M1–M5.

## Next Authorized Action

**M7 only with a fresh authorization — do not start it unasked.** The
M6-scope check is complete (deferred, docs-only; see
`docs/engineering-log/2026-11-10-m6-deferred.md`). M7 is the
productionization slice (query API, container, CI) per
[M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and is
not approved in this session.

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

Then open the M1–M7 guide; the M6-scope check is done (deferred),
so the only next step is **M7 with a fresh authorization**.

## Important Rules

- One milestone per session; stop after commit.
- Do not expand into M6+ without a new authorization.
- Protect `.env`; never commit secrets or put Gemini keys in URLs (`?key=`).
  Use `x-goog-api-key` header only.
- Distinguish OBSERVED / INFERENCE / NOT YET VALIDATED in engineering logs.
- Test gate is **unittest**, not pytest. Default Python via `uv` (3.14+).
- Never overwrite hash embedding JSON when touching E5 paths.
- T2D-004 is blocked-access — do not invent a substitute PDF.
