# Clinivault M1–M7 implementation guide

This is the **authoritative next-work guide** for a later session or a
smaller model. **M1 is done.** Resume at the M1 commit tip (`git log -1`)
and implement **M2 only** next.

- **Do not implement M2–M7 in one session.** One milestone, then tests,
  docs, commit, stop.
- **Do not treat uncommitted working-tree code as done.** If the tree is
  dirty with *partial* M2–M7 edits and no matching tests/docs/decision
  records, discard those edits and start from the last good commit. The
  intentional M1 tree (DECISION-017 + E5 provider + tests + docs) was
  committed; do not discard a clean post-M1 `master`.
- **Do not hand-edit** `.genesis/project.json`. Genesis CLI only, or skip
  Genesis if Node is missing (this machine often has no `genesis` CLI).
- **Do not print, commit, or paste** `.env` contents.

## What is already recorded (do not redo)

### M0 (committed as `dbcea0c`)

`dbcea0c` — `chore: align docs with the live pipeline and keep Gemini keys out of URLs`

- Status pages matching reality; corpus dates; Chosen decision wording
- Gemini key via `x-goog-api-key` only; `.env.example` with empty key
- Optional extras `semantic` / `eval` for `sentence-transformers`

### M1 (done — production raw E5)

Start the next session from the commit that landed M1 (message begins
`feat: use raw e5-small-v2…`). Confirm with `git log -1`.

M1 includes:

- `DECISION-017` Chosen: production retrieval is raw `intfloat/e5-small-v2`
- `E5EmbeddingProvider` in `src/clinivault_ai/embedding/provider.py`
- UI T2D-001 defaults → E5 artifacts; still single-doc
- `benchmark --provider hash|e5` (default hash); E5 gate 20/46 · 36/46 · 0.5583
- Docs: `embedding-e5.md`, engineering log 2026-09-25, architecture/README updates
- Handoff: `docs/handoff/CURRENT_HANDOFF.md` refreshed for M2 resume

**Next milestone: M2.** Prefer `CURRENT_HANDOFF.md` plus this file plus
`git log -1` for resume.

## How this project records work (required every milestone)

Copy this loop. Skipping docs is how status went stale before M0.

1. Write the decision the milestone needs (template:
   `docs/templates/decision-template.md`). Status values: Proposed /
   Chosen / Replaced / Rejected. Never rewrite a Chosen file.
2. Implement the smallest code change.
3. Tests: `.venv/Scripts/python -m unittest discover -s tests`
4. Milestone-specific gate (below).
5. Pipeline doc and/or engineering log. Logs use
   `docs/templates/engineering-problem-log-template.md` and must label
   **OBSERVED** / **INFERENCE** / **NOT YET VALIDATED**.
6. Refresh `README.md` Current Status and `docs/architecture/README.md`
   if behavior changed.
7. Add the decision to `docs/decisions/README.md` in numeric order.
8. Commit that milestone only. Suggested prefixes: `feat:`, `docs:`,
   `fix:`, `chore:`.

Default Python: 3.14 via `uv`. Test gate is **unittest**, not pytest.

```text
uv sync
uv sync --extra semantic   # only when the local E5 model is required
.venv/Scripts/python -m unittest discover -s tests
```

---

## Facts the implementer must not forget

### Retrieval query embedding

`src/clinivault_ai/retrieval/search.py` does:

```python
query_vector = provider.embed_texts([query])[0]
```

It does **not** call `embed_query`. Raw E5 means **no prefixes** on
corpus **and** query. Prefixes only on `embed_query` would not run.

### Artifact paths (DECISION-008)

| Role | Path | Dimension |
|---|---|---|
| Hash baseline (keep forever) | `data/embedded/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json` | 256 |
| E5 EVAL-HF durable (read in M1) | `data/embedded-intfloat--e5-small-v2/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json` | 384 |
| Parsed | `data/parsed/stage-1-clean-baseline-corpus/<DOC>/<DOC>.parsed.json` | — |

Nine obtained documents: T2D-001, 002, 003, 005, 006, 007, 008, 009, 010.
**T2D-004 is blocked-access. Do not invent a substitute PDF.**

**Never overwrite hash JSON** when adding E5.

A 384-d query against a 256-d store must fail loud. Pair provider with
matching artifacts.

### Eval-only vs production

`src/clinivault_ai/evaluation/hf_semantic.py` (`HFEmbeddingProvider`) is
evaluation-only. Production must get its own class in
`src/clinivault_ai/embedding/provider.py`. Do not import the eval module
from UI/pipeline.

`HFEmbeddingProvider` uses `local_files_only=True`. The model is expected
in the Hugging Face cache from EVAL-HF-002. If missing: clear
`EmbeddingError`, no silent download in tests.

### Frozen E5 numbers (must reproduce in M1)

Top-K = 5, 46 cases, same labels:

- Hit@1 **20/46**
- Hit@5 **36/46**
- MRR **0.5583**

Hash comparison (do not lose the ability to run this):

- Hit@1 12/46, Hit@5 26/46, MRR 0.3601

Command after M1:

```text
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5
```

Default benchmark must remain **hash** so historical numbers stay
runnable.

### UI today (`dbcea0c`)

`src/clinivault_ai/ui/app.py`:

- `default_paths()` → T2D-001 **hash** embeddings
- `make_run_fn` rebuilds the store **on every request**
- `VectorStore` is one `document_id`; `search()` stamps
  `store.document_id` on every hit

### Generation today

- Abstain only if evidence list is empty (`status: no_evidence`, no
  provider call)
- Citations are prompt text only; not parsed
- No context char budget
- Gemini retries: none
- `run_query` returns traces in memory only (no `run_id` file)

### Tests

About 218 tests at M0. Network-free. Do not add a required live Gemini or
required E5 encode to the default suite. E5 tests: `unittest.skipUnless`.

---

## M1 — Production raw E5 (**DONE** — do not redo)

Keep this section as the historical checklist. Implementation and the
frozen E5 scores are already landed. Jump to **M2**.

### Decision

New file `docs/decisions/DECISION-017-production-e5-retrieval.md`

- **Chosen:** production retrieval representation is raw
  `intfloat/e5-small-v2`. Hash stays as `clinivault-baseline-hash-v1`.
- Read existing E5 tree; do not regenerate unless vectors fail to match.
- DECISION-009 still owns Top-K=5, cosine, fail-loud, deterministic ties.
- DECISION-016 stays the *direction* record. DECISION-017 is
  *implementation authorization*.
- Cite EVAL-HF-003: `query:`/`passage:` did not beat raw.

### Code

1. `E5EmbeddingProvider` in `src/clinivault_ai/embedding/provider.py`
   - `name = "intfloat/e5-small-v2"`
   - dimension from model, expect **384**
   - `provider_params`: method hf-sentence-transformers, raw formatting,
     empty prefixes
   - `embed_texts`: encode as-is; empty text → `EmbeddingError`
   - lazy import sentence_transformers; missing extra → tell user
     `uv sync --extra semantic`
   - `local_files_only=True`
2. Export from `src/clinivault_ai/embedding/__init__.py`
3. **Do not** change `generate_embeddings()` default (keep hash)
4. UI `default_paths()` → E5 T2D-001 JSON; use `E5EmbeddingProvider()`
   when that artifact’s `model.name` is e5. **Still T2D-001 only.**
5. `benchmark.py`: `--provider hash|e5` selecting embedding directory +
   provider. Default hash.

### Tests

- Offline: empty text, params `input_formatting == "raw"` (construct
  params without loading the model if needed, or skip load)
- SkipUnless extra + cache: encode one string, len 384, finite, not
  all-zero
- SkipUnless: re-encode T2D-001 first chunk text; prefer byte-for-byte
  match to committed E5 vector (EVAL-HF-003 already showed this for
  T2D-001)

### Docs after the 20/46 numbers exist

- README Current Status: production retrieval is raw E5; hash retained
- architecture README replaceable-embedding bullet
- `docs/architecture/artifact-storage.md` §J: E5 is production-read
- `docs/engineering-log/YYYY-MM-DD-e5-production-integration.md` + index
- `docs/pipelines/embedding-e5.md` (production vs hash paths)

### Commit

`feat: use raw e5-small-v2 as production retrieval embeddings`

**Stop. Do not start M2 in the same session.**

---

## M2 — Nine-document index, load once

Only after M1 commit and reproduced E5 scores.

### Code

- Add `document_id` (and later metadata) onto each `VectorStore` record
  in `from_artifacts`
- `VectorStore.from_corpus(list[(embedding_artifact, chunk_output)])`
  - fail on empty, dimension mismatch, duplicate `chunk_id`
- `search()` result `document_id` from **record**, not
  `store.document_id`
- Load docs 001–003, 005–010. Skip 004
- UI: build index **once at startup**; `--provider e5|hash` default e5;
  optional `--single-doc` for the old T2D-001 path

### Tests

Duplicates, dimension mismatch, mixed document_ids in one result list,
store object not rebuilt per request.

### Docs

observability-ui.md, architecture README, retrieval-baseline.md

### Commit

`feat: retrieve across the nine-document Stage-1 corpus`

**Stop.**

---

## M3 — Metadata + ingestion report

### Decision DECISION-018

Document fields from `docs/corpus/corpus-manifest.md` only (do not guess
from PDF text): `document_id`, `document_name` (Title), `source`,
`publication_date`, `version`, `ingestion_date`.

Chunk: `parser_status` from page `extraction_status`.

**Section:** leave absent unless you have a measured deterministic
detector. Do not invent headings.

### Code

- Catalog module or JSON keyed by document_id
- Attach `document_name` onto chunks/results/context (optional fields;
  do not break old tests that omit them)
- `build_ingestion_report(...)` with brief shape:
  `document_id, total_pages, parsed_pages, failed_pages, total_chunks,
  embedded_chunks, indexed_chunks, ingestion_status`
- Fail if chunk count ≠ embedding count
- Write under
  `data/ingestion-report/stage-1-clean-baseline-corpus/<DOC>/`
  never inside parsed/embedded

### Docs

`docs/pipelines/ingestion-report.md`, corpus README, architecture
contracts table

### Commit

`feat: add document metadata passthrough and ingestion reports`

**Stop.**

---

## M4 — Execution record (Errata interface)

### Decision DECISION-019

JSONL under gitignored `runs/`. Env `CLINIVAULT_RUN_LOG`. Default: do
not write unless path set. Never persist API keys or `.env`.

### Schema (keep existing `run_query` keys; add)

```text
run_id, timestamp, query
retrieval.top_k
retrieval.chunks[{chunk_id, document_id, page_number, score}]
context.chunk_ids_used
generation.{model, answer, abstained, status}
sources[{document_id, page_number, chunk_id}]
```

`abstained` is true when status is `no_evidence` (M4). M5 may extend it.

### Docs

`docs/pipelines/execution-recording.md` — this is a **contract for
Errata**, not Errata logic.

### Commit

`feat: persist structured query execution records`

**Stop.**

---

## M5 — Answer reliability (no AI judges)

- Parse `EVIDENCE_ITEM_RANK` / chunk ids from the answer; put
  `invalid_citations` on the result
- Keep empty-evidence abstention (no provider call)
- Add sentinel e.g. answers starting `ABSTAIN:` when evidence exists but
  the model refuses; update prompt via successor to DECISION-011 if the
  contract changes
- **No retrieval-score threshold** without a measured decision
- Context `max_chars`: drop lowest-rank tail; record
  `truncated_chunk_ids`
- Gemini retry on 429/5xx only; record `attempts`; no retry on 401/403
- Tiny labeled set: in-scope supported, DECISION-005 out-of-scope, empty
  evidence. Metrics: citation validity, abstention correctness. Fake
  provider in unit tests.

### Commit

`feat: check citations, abstention sentinel, and context budget`

**Stop.**

---

## M6 — Only if measured

If M1–M5 do not show a specific retrieval weakness, write
`docs/engineering-log/YYYY-MM-DD-m6-deferred.md` and skip hybrid,
rerank, BM25, Top-K changes.

If you do run an experiment: **one variable**, frozen 46 cases, new
decision.

---

## M7 — Productionization

- FastAPI wrapping `run_query`; keep stdlib UI as inspector
- Decision: in-memory index is enough until corpus/concurrency require
  Qdrant (do not add Qdrant “for completeness”)
- Dockerfile, stdlib JSON logging (no keys), GitHub Actions: `uv sync` +
  unittest (E5 tests skip without cache)
- Stage 2 corpus: T2D-004 only via legitimate access; never bypass 403

### Commit

`feat: add query API, container, and CI for the unittest gate`

**Stop. That is the MVP deploy slice, not a rewrite.**

---

## Session checklist for the other system

```text
git status --short
git log -1 --oneline          # expect dbcea0c or a later *complete* milestone commit
git rev-parse HEAD
uv sync
.venv/Scripts/python -m unittest discover -s tests
# then implement ONE milestone from this file
# then tests + docs + commit + stop
```

If `sentence-transformers` or local E5 files are missing during M1:
fail with an install/cache message. After DECISION-017 is Chosen, **do
not** silently fall the UI back to hash.

## What this guide is not

- Not a Genesis task receipt
- Not permission to implement M2–M7 while M1 is open
- Not Errata
- Not a claim that E5 is already production (it is not, until M1 lands)
