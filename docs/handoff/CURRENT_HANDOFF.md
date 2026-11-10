# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git as canonical when resuming. Prefer this file plus
> [M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) and
> `git log -1`.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Last completed milestone:** **M3** — document metadata passthrough and
  ingestion reports (DECISION-018).
- **Last pushed commit:** `a569b04` (`feat: retrieve across the
  nine-document Stage-1 corpus`). M2 is committed and pushed. M3 is
  implemented, tested, and documented in the working tree but **not yet
  committed** — review, commit as
  `feat: add document metadata passthrough and ingestion reports`, then push.
  After that, confirm with `git rev-parse HEAD` / `git log -1 --oneline`.
- **Working-tree expectation:** M3 files modified (see below), plus nine new
  reports under `data/ingestion-report/`; untracked scratch removed before
  commit.
- **Intentionally ignored/protected local files:** `.env` is ignored and must
  never be staged or committed. Copy `.env.example` locally and set
  `GOOGLE_API_KEY` only on the machine. Never print or paste keys.

## Last Completed Unit

- **Unit/task:** M3 / document metadata passthrough and ingestion reports
  (DECISION-018)
- **What was completed:** `src/clinivault_ai/corpus/catalog.py` holds the
  nine catalog entries transcribed from `docs/corpus/corpus-manifest.md`
  (T2D-004 excluded by design). The retrieval store attaches
  `document_name` to in-memory records for catalogued documents;
  `search()` propagates it to results and trace candidates;
  `context.build_context()` preserves it in evidence entries and the
  documents summary (optional everywhere; synthetic/legacy IDs keep their
  exact contract). `build_ingestion_report()` / `write_ingestion_report()`
  produce the brief-shaped report per document; all nine reports under
  `data/ingestion-report/stage-1-clean-baseline-corpus/<DOC>/` are
  `success` (181 pages, 727 chunks). `section` stays absent by decision.
- **Important files:**
  - `src/clinivault_ai/corpus/catalog.py` (new), `src/clinivault_ai/corpus/__init__.py` (new)
  - `src/clinivault_ai/ingestion/report.py` (new)
  - `src/clinivault_ai/retrieval/store.py`
  - `src/clinivault_ai/retrieval/search.py`
  - `src/clinivault_ai/context/builder.py`
  - `tests/test_metadata.py` (new, 14 tests)
  - `data/ingestion-report/stage-1-clean-baseline-corpus/<DOC>/` (nine reports)
  - `docs/decisions/DECISION-018-document-metadata-and-ingestion-reports.md` (new)
  - `docs/pipelines/ingestion-report.md` (new)
  - `docs/decisions/README.md`, `docs/architecture/README.md`,
    `docs/corpus/README.md`, `README.md`
- **Tests/gates:**
  - `python -m unittest tests.test_metadata` — 14 tests OK
  - `python -m unittest discover -s tests` — 256 tests; only known failure
    is `test_ui.HandlerRequestTests` under the sandbox proxy (passes with
    loopback excluded from proxy); 4 E5 tests skip without the HF cache
  - `benchmark --provider e5` numbers unchanged by M3 (no retrieval-math
    change): Hit@1 **20/46**, Hit@5 **36/46**, MRR **0.5583**
- **Relevant Decision / Pipeline:**
  - `docs/decisions/DECISION-018-document-metadata-and-ingestion-reports.md`
  - `docs/pipelines/ingestion-report.md`

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

### INFERENCE

- M4 (persisted execution records, DECISION-019) is the next measured
  product gap; retrieval math is unchanged by M3, so M6 stays deferred.

### NOT YET VALIDATED

- End-to-end Gemini answers on the UI with E5 evidence over the corpus.
- `section` detection — deliberately absent until a deterministic detector
  is measured (DECISION-018).
- Hybrid / rerank (M6) — defer unless a measured weakness appears after M1–M5.

## Next Authorized Action

**M4 only** — persisted execution records (DECISION-019): JSONL under
gitignored `runs/`, never persisting keys. See
[M1-M7-IMPLEMENTATION-GUIDE.md](./M1-M7-IMPLEMENTATION-GUIDE.md) §M4.

**Do not start M5–M7 in the same session.** One milestone, tests, docs,
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
