# Production raw E5 retrieval integration

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-25

## Where It Happened

Production embedding seam (`E5EmbeddingProvider`), observability UI
T2D-001 defaults, `evaluation.benchmark --provider e5`.

## What We Expected

Authorize DECISION-017, encode queries with the same raw
`intfloat/e5-small-v2` used for the committed EVAL-HF vectors, and
reproduce Hit@1 20/46, Hit@5 36/46, MRR 0.5583 without overwriting hash
artifacts.

## What Actually Happened

**OBSERVED:** `local_files_only=True` failed on first load because
`%USERPROFILE%\.cache\huggingface` had no model snapshots (only an
unrelated harness file). Production code did not download and did not
fall back to hash.

**OBSERVED:** After one explicit `SentenceTransformer('intfloat/e5-small-v2')`
download into the local cache, `E5EmbeddingProvider` loaded (384-d).
Re-encoding T2D-001 chunk 0 matched the committed E5 vector exactly.

**OBSERVED:** `.venv/Scripts/python -m unittest discover -s tests` —
224 tests, OK (1 skip: missing-extra message while sentence-transformers
is installed).

**OBSERVED:** `.venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5`
printed `Hit@1=20/46  Hit@5=36/46  MRR=0.5583`. Wall time **39.21s**
(model load + 46 queries + store loads for 9 documents on CPU).

**INFERENCE:** Query encoding through `embed_texts` (no prefixes) is the
same path EVAL-HF-003 measured as better than `query:`/`passage:`.

**NOT YET VALIDATED:** End-to-end Gemini answers on the UI with E5
evidence (this unit gated retrieval only). Corpus-wide search is not
implemented.

## Evidence

```text
uv sync --extra semantic
.venv/Scripts/python -m unittest discover -s tests
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark --provider e5
```

Default `benchmark` (no flag) remains hash for historical 12/46 · 26/46
· 0.3601.

## What We Investigated

Hugging Face hub cache location vs EVAL-HF-era assumption that the model
was still on disk.

## What We Tried

Load with `local_files_only=True` first (required by DECISION-017). Only
then populate the cache with an explicit download outside the production
constructor.

## What Failed

Silent offline load when the cache is empty — by design. The UI must
surface `EmbeddingError`, not hash.

## The Fix

Keep `local_files_only=True` in `E5EmbeddingProvider`. Operators install
`uv sync --extra semantic` and ensure `intfloat/e5-small-v2` is in the
Hugging Face cache.

## Why This Fix

Matches EVAL-HF: no unauthenticated hub traffic on every UI request.

## Impact

- Production T2D-001 UI defaults to the E5 artifact tree.
- Benchmark `--provider hash|e5` (default hash).
- Hash JSON under `data/embedded/` untouched.

## Prevention / Lesson Learned

`local_files_only` is only as good as the cache. Document a one-time
download; never treat "model used to be here" as durable.
