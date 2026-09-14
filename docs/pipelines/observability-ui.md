# Observability UI (V1 — Manual Query Mode)

Status: implemented and verified (development/debug console, not a production application).

## Why This Was Added

The forensic investigation of the T2D-001 grounding findings required manually
reconstructing what retrieval supplied, what context packaged, and what the
prompt contained. The backend trace observability unit (retrieval trace,
context trace, generation trace, end-to-end `run_query()`) made every run
reconstructable in data, but only programmatically. This UI makes the
same RunTrace inspectable by a human without running scripts.

Scope of V1 (deliberately bounded):

- Manual Query Mode ONLY. Test/Evaluation Mode is future work.
- Query input + Top-K control, run status, pipeline overview, retrieval
  candidates table (with the actual `selected` flag), context evidence panel
  (exact text + provenance), exact prompt text panel, generation metadata +
  answer panel, and a Grounding Analysis section that states explicitly that
  automatic claim-to-evidence evaluation is NOT available yet (placeholder —
  no fake grounding scores).
- The UI consumes the existing backend trace contract only. It calls the
  single end-to-end `run_query()` path; it does not call
  `retrieval.search` / `build_context` / `generate_answer` independently.

## Technology Chosen and Why

Python stdlib `http.server` (ThreadingHTTPServer) serving one static
HTML/JS page (`src/clinivault_ai/ui/page.py`) plus one JSON endpoint
(`/api/query`). **No new dependencies** — no Flask/Streamlit/FastAPI, no
frontend framework. The repository had no web framework, and the
"no unnecessary infrastructure" rule applies: this is a debug console,
not a product surface.

Architecture / data flow:

```
browser: query + top_k
  → POST /api/query
  → run_query(store, query, embedder, gemini, top_k=...)   # existing backend
  → RunTrace {query, retrieval_trace, context_trace, generation_trace, result}
  → JSON response → render RunTrace panels
```

Error handling: exceptions are returned as a safe JSON error body
(`{"ok": false, "error": ...}`); no API key or environment secret is ever
sent to the client or rendered. Empty-evidence runs render the
`no_evidence` status with `provider_called: false` and no fabricated answer.

## Tests

Exact command:

```
.venv\Scripts\python -m unittest tests.test_ui
```

Exact result: **Ran 11 tests — OK** (0 failures).

Full suite:

```
.venv\Scripts\python -m unittest discover -s tests
```

Exact result: **Ran 152 tests — OK** (141 pre-existing + 11 new UI tests).

Coverage: query submission validation, trace rendering, retrieval
candidate rendering, selected-flag rendering (uses the trace's `selected`
value, not inferred rank), context evidence rendering with exact text,
exact prompt rendering, generation metadata rendering, answer rendering,
empty-evidence state, error state, and a no-secrets check.

## Real T2D-001 Verification

Configuration: baseline store (107 chunks), baseline hash embedder
(`clinivault-baseline-hash-v1`, dim 256), `gemini-2.5-flash`, Top-K = 5,
query = `"criteria for the diagnosis of diabetes"`, executed through the
UI server's `/api/query` endpoint (the same path the browser uses).

Observed retrieval trace (deterministic, matches the established baseline):

| Rank | Selected | Chunk ID | Page | Score |
|------|----------|----------|------|-------|
| 1 | true | T2D-001-p014-c003 | 14 | 0.6018 |
| 2 | true | T2D-001-p002-c002 | 2 | 0.5851 |
| 3 | true | T2D-001-p023-c006 | 23 | 0.5814 |
| 4 | true | T2D-001-p002-c003 | 2 | 0.5680 |
| 5 | true | T2D-001-p017-c003 | 17 | 0.5641 |

Ranks 6+ were returned as non-selected candidates (`selected: false`) —
the trace distinguishes retrieved candidates from the subset passed
downstream.

Observed context trace: `evidence_count: 5`, `input_retrieval_count: 5`,
exact evidence text for all five chunks preserved with provenance.

Observed generation trace: provider `google_gemini`, model
`gemini-2.5-flash`, status `ok`, `provider_called: true`, timings captured
(prompt 0.03 ms / LLM 15,505.58 ms / total 15,505.61 ms), usage captured
(prompt 2477, candidates 950, thoughts 2108, total 5535), full prompt text
present (contains the p002-c003 "repeat testing" passage and the p017-c003
IADPSG passage), generated answer rendered verbatim. The complete RunTrace
is JSON-serializable.

Two transient provider 503s ("high demand") occurred during verification;
the UI surfaced each as a clean JSON error without secrets — this itself
validated the error path. The final run succeeded.

## Five-Case Representative UI Verification

All five representative evaluation cases (the same cases defined in
`docs/pipelines/representative-evaluation.md`) were submitted through the
real UI server's `POST /api/query` endpoint — the exact path the browser
uses — and the returned RunTrace was checked against the render contract.

Exact test command:

```
.venv\Scripts\python -m unittest discover -s tests
```

Exact result: **Ran 152 tests — OK** (exit code 0).

Cases and results:

| Case | Document | Query | Result | Model | Context items | Candidates | LLM ms | Total tokens |
|------|----------|-------|--------|-------|---------------|------------|--------|--------------|
| EVAL-1 | T2D-001 | criteria for the diagnosis of diabetes | ok | gemini-2.5-flash | 5 | 107 | 15,777 | 5,467 |
| EVAL-2 | T2D-001 | classification of diabetes types | ok | gemini-2.5-flash | 5 | 107 | 14,670 | 5,025 |
| EVAL-3 | T2D-001 | gestational diabetes screening in pregnancy | ok | gemini-2.5-flash | 5 | 107 | 9,616 | 5,540 |
| EVAL-4 | T2D-002 | screening recommendations for prediabetes and type 2 diabetes | blocked (provider 429) | — | — | — | — | — |
| EVAL-5 | T2D-001 | HbA1c test to diagnose diabetes | blocked (provider 429) | — | — | — | — | — |

For every successful case the render-contract checks passed: status `ok`,
provider `google_gemini` + model `gemini-2.5-flash`, `provider_called: true`,
retrieval table present (`total_candidates` candidates each with
rank/chunk_id/document_id/page_number/score/selected), exactly 5 selected
candidates in rank order, context evidence preserved with exact text,
prompt text contains the query verbatim plus the `SUPPLIED_EVIDENCE` block,
timings present, token/usage metadata present, and a non-empty rendered
answer. The JSON RunTrace is fully JSON-serializable.

EVAL-1's deterministic retrieval ranks were re-confirmed against the trace:

| Rank | Selected | Chunk ID | Page | Score |
|------|----------|----------|------|-------|
| 1 | true | T2D-001-p014-c003 | 14 | 0.6018 |
| 2 | true | T2D-001-p002-c002 | 2 | 0.5851 |
| 3 | true | T2D-001-p023-c006 | 23 | 0.5814 |
| 4 | true | T2D-001-p002-c003 | 2 | 0.5680 |
| 5 | true | T2D-001-p017-c003 | 17 | 0.5641 |

### Screenshot capability note

A real browser could not be driven and screenshots could not be captured in
this environment. Verification was performed at the HTTP / render-contract
level: the exact single-page HTML a browser receives was served and its panel
markers (Retrieval, Context, Prompt, Generation, Grounding Analysis) were
confirmed present, and each query was executed through the same
`POST /api/query` endpoint the page calls. The JSON returned by that endpoint
contains every field the page renders. No in-browser pixel/DOM screenshot
artifact is therefore part of this document.

### EVAL-4 / EVAL-5 rate-limit limitation

EVAL-4 (T2D-002) and EVAL-5 (T2D-001, HbA1c) could not be completed as
full UI runs at verification time. The Gemini `gemini-2.5-flash` free tier
returned `429 QUOTA_EXCEEDED` for `generate_content_free_tier_requests`
(limit shown: 20) for every attempt, including across many spaced retries
(30–90 s waits) — an account-level free-tier quota exhaustion, not a
per-minute transient. The UI correctly surfaced this as a safe JSON error
body with no secret exposure (itself a positive error-path check).

Implications recorded honestly, per the project's evidence rule:

- EVAL-1/2/3 demonstrate that the UI renders every stage of a real
  successful run (retrieval, context, prompt, generation, timings, usage).
- EVAL-4/5 generation outputs were **not** obtained and are **not yet
  validated**. Their retrieval/context stages are deterministic and would
  render identically, but no claim about their generated answers is made
  here. They remain outstanding as real UI verification until provider
  quota permits.

## Limitations

- Debug console only: no authentication, no persistence, no run history.
- Grounding Analysis is a labeled placeholder; automatic claim-to-evidence
  evaluation is not implemented.
- Single-user, local development use assumed.
- No Test/Evaluation Mode yet.
- Browser-level screenshots are not captured in this environment;
  verification is at the HTTP / render-contract level (see above).
- Real end-to-end UI verification for all five representative cases is
  blocked pending Gemini free-tier quota; EVAL-4 and EVAL-5 generation
  outputs are not yet validated.