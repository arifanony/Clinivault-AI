# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git as canonical when resuming. Prefer this file plus
> [M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and
> `git log -1`.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Last completed milestone:** **M1** — production raw `intfloat/e5-small-v2`
  retrieval (DECISION-017).
- **Verified commit:** the tip of `master` after the M1 handoff commit
  (`feat: use raw e5-small-v2 as production retrieval embeddings`). After
  `git pull`, confirm with `git log -1 --oneline`.
- **Working-tree expectation after pull:** clean (no uncommitted M1 leftovers).
- **Intentionally ignored/protected local files:** `.env` is ignored and must
  never be staged or committed. Copy `.env.example` locally and set
  `GOOGLE_API_KEY` only on the machine. Never print or paste keys.

## Last Completed Unit

- **Unit/task:** M1 / `DECISION-017-PRODUCTION-E5-RETRIEVAL`
- **What was completed:** production retrieval switched to raw
  `intfloat/e5-small-v2` via `E5EmbeddingProvider`. UI T2D-001 defaults read
  E5 artifacts. `benchmark --provider e5` reproduces the frozen scores. Hash
  baseline remains available (`data/embedded/`, default benchmark = hash).
- **Important files:**
  - `docs/decisions/DECISION-017-production-e5-retrieval.md`
  - `docs/engineering-log/2026-09-25-e5-production-integration.md`
  - `docs/pipelines/embedding-e5.md`
  - `docs/handoff/M1-M7-IMPLEMENTATION-GUIDE.md`
  - `src/clinivault_ai/embedding/provider.py`
  - `src/clinivault_ai/evaluation/benchmark.py`
  - `src/clinivault_ai/ui/app.py`
  - `tests/test_e5_provider.py`
- **Tests/gates:**
  - `.venv/Scripts/python -m unittest discover -s tests` — 224 tests OK
    (skips allowed when semantic extra or HF cache missing)
  - `.venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5`
    — Hit@1 **20/46**, Hit@5 **36/46**, MRR **0.5583**
- **Relevant Decision / Log / Pipeline:**
  - `docs/decisions/DECISION-017-production-e5-retrieval.md`
  - `docs/engineering-log/2026-09-25-e5-production-integration.md`
  - `docs/pipelines/embedding-e5.md`

## Current Technical Understanding

### OBSERVED

- Production query embedding uses `embed_texts` with **no** `query:` /
  `passage:` prefixes (same path as frozen EVAL-HF-003 raw winner).
- E5 artifacts live under `data/embedded-intfloat--e5-small-v2/` (384-d).
  Hash artifacts under `data/embedded/` (256-d) are untouched.
- `E5EmbeddingProvider` uses `local_files_only=True`. Empty HF cache fails
  loud; no silent hash fallback in the UI.
- UI still indexes **T2D-001 only** and rebuilds the store per request.

### INFERENCE

- M2 (nine-doc index, load once at startup) is the next measured product gap.

### NOT YET VALIDATED

- End-to-end Gemini answers on the UI with E5 evidence (retrieval-only gate for M1).
- Corpus-wide search across all nine Stage-1 docs.
- Hybrid / rerank (M6) — defer unless a measured weakness appears after M1–M5.

## Next Authorized Action

**M2 only** — nine-document Stage-1 corpus index, load once at UI startup,
`--provider e5|hash` (default e5). See
[M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) §M2.

**Do not start M3–M7 in the same session.** One milestone, tests, docs,
commit, stop.

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

Then open the M1–M7 guide and implement **M2 only**.

## Important Rules

- One milestone per session; stop after commit.
- Do not expand into M3+ without a new authorization.
- Protect `.env`; never commit secrets or put Gemini keys in URLs (`?key=`).
  Use `x-goog-api-key` header only.
- Distinguish OBSERVED / INFERENCE / NOT YET VALIDATED in engineering logs.
- Test gate is **unittest**, not pytest. Default Python via `uv` (3.14+).
- Never overwrite hash embedding JSON when touching E5 paths.
- T2D-004 is blocked-access — do not invent a substitute PDF.
