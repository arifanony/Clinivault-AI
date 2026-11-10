# Production query API (M7)

Status: **implemented**. Machine-facing HTTP slice over the unchanged
pipeline — no stage semantics change. The stdlib observability UI
stays the inspector; this is the deployable interface. See
[DECISION-021](./../decisions/DECISION-021-production-api-container-ci.md).

## 1. What problem does this pipeline solve?

M1–M6 are reachable only through the browser UI and direct Python
calls. External integrators (e.g. Errata over HTTP), containers, and
CI need a typed, validated query interface with health reporting and
secret-free logging.

## 2. What goes in?

`POST /query` with `{query, top_k = 5 (1–50), max_chars? (positive
int), api_key? (per-request Gemini key)}`, plus one already-loaded
`(store, embedder)` pair built at startup by the reused `load_store`
wiring (nine-document corpus by default, `--single-doc` legacy path,
`--provider e5|hash`).

## 3. What happens, step by step?

```
POST /query {query, top_k, max_chars?, api_key?}
  ↓
pydantic validation (blank query → 422; top_k/max_chars bounds → 422)
  ↓
fresh GeminiProvider per request (body key, else env; never persisted)
  ↓
run_query(store, query, embedder, provider, top_k, max_chars)
  → retrieval → context → generation (unchanged; traces as before)
  ↓
curated response (record + answer metadata; no prompts/vectors/keys)
  ↓
JSON access log: method/path/status/duration_ms/run_id (no query/answer/key)
```

`GET /health` returns liveness plus index provenance
(`document_count`, `chunk_count`, `embedding_model`).

## 4. What comes out?

`{run_id, timestamp, query, answer, status, abstained, model,
attempts, invalid_citations, sources, retrieval, context}` — the M4
execution record plus answer metadata. Pipeline failures become 500s
with a safe `{detail: "ErrorType: message"}` (no environment state).

## 5. Which components are involved?

- `src/clinivault_ai/api/app.py` (`create_app`, models, JSON logging,
  CLI `main` serving via uvicorn)
- `src/clinivault_ai/api/__main__.py` (`python -m clinivault_ai.api`)
- Reused unchanged: `pipeline.run_query`, `ui.app.load_store`,
  `generation.GeminiProvider`
- `tests/test_api.py` (13 tests, fakes only)
- `Dockerfile`, `.github/workflows/ci.yml`

## 6. Which metadata is created or preserved?

Preserved: every `run_query` trace/record field and all M5
reliability fields (`attempts`, `invalid_citations`,
`truncated_chunk_ids`, `abstained`). New: per-request access-log
lines (stdout JSON). Never created: keys, prompts, vectors in any
response or log.

## 7. What can fail?

- Missing E5 model cache at startup under `--provider e5` → loud
  startup failure (no silent hash fallback, per DECISION-017).
- Missing Gemini key at request time → generation 500 (use
  `--provider hash` for the keyless smoke path; generation still
  needs a key or per-request `api_key`).
- `top_k` beyond the index size → 500 via the existing fail-loud
  retrieval guard.

## 8. How do we detect failure?

HTTP status codes (422 validation, 500 pipeline), `status` field
(`ok`/`no_evidence`/`abstained`), non-empty `invalid_citations`,
`/health` counts, and JSON access logs with status/duration.

## 9. What evidence or logs does it produce?

Stdout JSON access logs (one object per request) and the unchanged
opt-in JSONL execution records (`run_log_path` / `CLINIVAULT_RUN_LOG`).

## 10. What consumes the output next?

Deployments (container), HTTP integrators, and the Errata contract
records. The UI is untouched.

## Related decisions

- [DECISION-021](./../decisions/DECISION-021-production-api-container-ci.md) —
  this milestone (FastAPI slice, in-memory index, container, CI).
- [DECISION-017](./../decisions/DECISION-017-production-e5-retrieval.md) —
  production embeddings and the no-silent-fallback rule reused here.
- [DECISION-019](./../decisions/DECISION-019-query-execution-records.md) —
  the record contract the response carries.
- [DECISION-020](./../decisions/DECISION-020-answer-reliability.md) —
  the reliability fields the response carries.

## Known limitations

Single-process uvicorn (no workers); `max_chars` counts characters,
not tokens (inherited from M5); the image ships no E5 weights and no
key — deployment provides the cache volume and `GOOGLE_API_KEY`.
T2D-004 stays blocked-access and out of scope.
