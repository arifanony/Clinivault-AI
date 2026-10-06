# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git as canonical when resuming. Prefer this file plus
> [M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and
> `git log -1`.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Last completed milestone:** **M2** — nine-document corpus index, load
  once at UI startup (no new decision record; representation still
  DECISION-017).
- **Last pushed commit:** `b018476` (`docs: pin M1 handoff resume SHA for
  cross-device start`). M2 is implemented, tested, and documented in the
  working tree but **not yet committed** — review, commit as
  `feat: retrieve across the nine-document Stage-1 corpus`, then push.
  After that, confirm with `git rev-parse HEAD` / `git log -1 --oneline`.
- **Working-tree expectation:** M2 files modified (see below), untracked
  scratch (`.uv-cache/`, `.uv-python/`) removed before commit.
- **Intentionally ignored/protected local files:** `.env` is ignored and must
  never be staged or committed. Copy `.env.example` locally and set
  `GOOGLE_API_KEY` only on the machine. Never print or paste keys.

## Last Completed Unit

- **Unit/task:** M2 / nine-document Stage-1 corpus index, load once
- **What was completed:** `VectorStore.from_corpus()` merges the nine
  obtained documents into one index (727 chunks; T2D-004 excluded);
  `search()` takes `document_id` per hit from its record. The UI builds
  the corpus index once at startup with `--provider e5|hash` (default e5)
  and `--single-doc` for the legacy T2D-001 path; the bound store is
  reused for every request. Mixed-model corpora fail loud.
- **Important files:**
  - `src/clinivault_ai/retrieval/store.py`
  - `src/clinivault_ai/retrieval/search.py`
  - `src/clinivault_ai/ui/app.py`
  - `tests/test_retrieval.py` (`FromCorpusTests`)
  - `tests/test_ui.py` (corpus paths / parser / load-once / load tests)
  - `docs/pipelines/observability-ui.md` (§M2)
  - `docs/pipelines/retrieval-baseline.md` (§Corpus index)
  - `docs/architecture/README.md`, `README.md`
- **Tests/gates:**
  - `.venv/Scripts/python -m unittest discover -s tests` — 242 tests OK
    (1 expected conditional E5 skip)
  - `benchmark --provider e5` — Hit@1 **20/46**, Hit@5 **36/46**, MRR
    **0.5583** (unchanged); default hash — 12/46, 26/46, 0.3601 (unchanged)
- **Relevant Decision / Pipeline:**
  - `docs/decisions/DECISION-017-production-e5-retrieval.md` (unchanged)
  - `docs/pipelines/retrieval-baseline.md`, `docs/pipelines/observability-ui.md`

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

### INFERENCE

- M3 (document metadata passthrough + ingestion reports, DECISION-018) is
  the next measured product gap.

### NOT YET VALIDATED

- End-to-end Gemini answers on the UI with E5 evidence over the corpus.
- Brief-level metadata (document_name, dates, version) on chunks/results.
- Hybrid / rerank (M6) — defer unless a measured weakness appears after M1–M5.

## Next Authorized Action

**M3 only** — document metadata passthrough and ingestion reports
(DECISION-018). See
[M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) §M3.

**Do not start M4–M7 in the same session.** One milestone, tests, docs,
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

Then open the M1–M7 guide and implement **M3 only**.

## Important Rules

- One milestone per session; stop after commit.
- Do not expand into M4+ without a new authorization.
- Protect `.env`; never commit secrets or put Gemini keys in URLs (`?key=`).
  Use `x-goog-api-key` header only.
- Distinguish OBSERVED / INFERENCE / NOT YET VALIDATED in engineering logs.
- Test gate is **unittest**, not pytest. Default Python via `uv` (3.14+).
- Never overwrite hash embedding JSON when touching E5 paths.
- T2D-004 is blocked-access — do not invent a substitute PDF.
