# Engineering Decision: Baseline Generation Provider — Google Gemini (`gemini-2.5-flash`)

## Status

Chosen

## Date

2026-09-13

## Decision Question

Which LLM provider and model should power the initial Clinivault baseline
generation stage, given the project's constraints of no unnecessary
recurring cost during MVP development (DECISION-003), reproducible
evidence-driven engineering, and easy later replacement through a small
provider seam (DECISION-001)?

## Context / Problem

Clinivault has verified a full retrieval pipeline through context
construction (query -> embedding -> cosine top-k -> evidence bundle).
The next vertical step is baseline generation: a single chosen LLM that
turns a context bundle into a grounded answer, measured for tokens and
latency. The repository contained no LLM provider, no generation code,
and no SDK dependencies; API credentials were local-only (git-ignored
`.env`). A controlled feasibility bake-off was run to choose the first
baseline provider from real evidence rather than reputation.

## Options Considered

- **Google Gemini API** (`gemini-2.5-flash`).
- **OpenRouter** (free `:free` routes; e.g. `google/gemma-4-31b-it:free`,
  `cohere/north-mini-code:free`).
- **Groq** (fast inference provider).
- **Local model** (e.g. Ollama-class) — rejected at this stage because
  local hardware capability/install feasibility is not established in
  the repository and would add environment setup before connectivity is
  even proven; revisit later if local privacy/offline needs arise.

## Evidence from the Controlled Bake-Off (2026-09-13)

**Google Gemini — `gemini-2.5-flash`**
- API connectivity: verified. `GET /v1beta/models` returned 200 and
  listed `gemini-2.5-flash` (stable, non-preview: `version 001`,
  text generation methods, ~1M-token context per model metadata).
- Neutral test (`"Reply with exactly: PROVIDER_OK"`): **3/3 HTTP 200**,
  exact output `PROVIDER_OK`.
- Synthetic grounded test (France/Paris, "answer only from supplied
  evidence"): **1/1 HTTP 200**, answer `Paris` — consistent with the
  evidence.
- Latency (small controlled feasibility measurement): neutral 1573 /
  1397 / 1538 ms (mean 1503, min 1397, max 1573); grounded 1637 ms.
- Token usage returned: prompt/completion/total 9/3/41–47 for neutral
  (totals include internal thinking tokens, exceeding prompt+output);
  grounded 33/1/81. Latency and token metadata are observable from the
  API.

**OpenRouter**
- Reachable and authorized; 19 `:free` routes.
- `google/gemma-4-31b-it:free`: 2/3 neutral successes then upstream
  **429 (free-route contention)**; grounded request hit 429.
- `cohere/north-mini-code:free`: grounded synthetic test succeeded
  (`Paris.`); not preferred for general RAG use (code-focused model;
  neutral text empty).
- Free route is usable but intermittently rate-limited upstream.

**Groq**
- Repeated **HTTP 403, Cloudflare error 1010** from this development
  environment (edge block, not an auth response).
- No model catalog and no generation request could be completed.

## Why Gemini Was Chosen

Chosen for the initial generation baseline based on: successful
connectivity, repeated successful controlled requests (3/3 neutral),
successful synthetic evidence-flow verification, observable token usage,
measurable latency, an exact stable non-preview model identity
(`gemini-2.5-flash`), a currently documented free-tier path, and the
sole provider that completed both the neutral and grounded flow without
a rate-limit failure during the bake-off. OpenRouter remained reachable
but showed free-route 429 contention; Groq was not routable from this
environment.

This is a baseline choice grounded in the bake-off evidence. It is not
a claim that Gemini is the best model generally, the best model for
healthcare, clinically accurate, provably grounded, or production-ready.

## Exact Model Identity

- Provider: **Google Gemini API**
- Model: **`gemini-2.5-flash`** (stable, non-preview; ~1M-token
  context per underlying model metadata).

## Cost / Free-Tier Position

- Documented (official Gemini Developer API docs): `gemini-2.5-flash`
  has a free tier; free input/output tokens for eligible models; the
  free tier requires no billing account. Paid usage requires linking an
  active billing account.
- **Account-specific status: NOT confirmed in this repository.** A
  manual Google AI Studio check was performed by the user, but its
  specific result is not recorded in the repo/session, and the API does
  not expose tier/billing. Documentation-level free-tier eligibility is
  NOT treated as account-level proof. Until the project's tier and
  billing state are recorded/manually confirmed, development cannot be
  asserted to be zero-cost; request volumes shall be kept small and
  billing state verified before assuming "free".

## Latency Observations (small controlled feasibility measurement)

Neutral (n=3, `gemini-2.5-flash`): 1573, 1397, 1538 ms; mean 1503 ms,
min 1397 ms, max 1573 ms. Synthetic grounded: 1637 ms. This is a tiny,
single-day sample — not a performance benchmark.

## Token-Usage Observations

Provider returns prompt/completion/total token counts. Observed totals
include internal thinking tokens (total well above prompt+completion),
e.g. 9/3/41–47 (neutral) and 33/1/81 (grounded). Token accounting is
available for baseline cost/latency measurement.

## Reliability Observations

In the controlled window, Gemini completed every request without an
observed rate-limit error; OpenRouter free routes returned an upstream
429; Groq was unreachable (HTTP 403 / Cloudflare 1010).

## Known Limitations

- If the account tier is not the (documented) free tier, use may be
  billed; billing outcome of the bake-off requests is unknown.
- Swift thinking-token usage raises total-token counts that must be
  accounted for in cost estimates.
- Small sample; one-day latency data.
- No healthcare/clinical quality or systematic grounding validation.

## What Remains Undecided

- Exact generation output contract and prompt format design (next unit).
- Generation provider seam implementation (`GenerationProvider`) — a
  future source-code unit, not built here.
- Abstention logic, context-limit/truncation policy, retries/streaming.
- Whether paid usage is ever justified (only if later evidence shows need).

## Distributed-Fact Classification (from the bake-off)

- **OBSERVED:** Gemini API worked in this environment; `gemini-2.5-flash`
  completed 3/3 neutral requests with exact expected output; the
  synthetic grounded flow completed; token and latency metadata were
  returned; OpenRouter free routes produced 429s under contention; Groq
  was blocked by a network-level Cloudflare 1010 from this environment.
- **INFERENCE:** Gemini is the strongest current baseline provider
  candidate from this limited experiment.
- **NOT YET VALIDATED:** healthcare answer quality, systematic grounding,
  clinical accuracy, long-context behavior, sustained quota, production
  reliability, large-scale performance, and the project's account-level
  free-tier/billing state.

## Provider Seam Compatibility

This decision is compatible with DECISION-001's seam principle. The
eventual architecture should allow:

```
Clinivault -> GenerationProvider -> Google Gemini
```

leaving replacement possible later (e.g. if a local model becomes
justified or OpenRouter/Groq become routable). The seam is a future
source-code unit and is not implemented in this documentation change.

## How We Will Validate This

- Next unit: implement generation behind a small `GenerationProvider`
  seam; run representative T2D-001 evidence questions; record tokens,
  latency, and evidence-answer consistency; re-verify account billing
  state.
- Revisit if measured cost, latency, or answer behavior proves unsuitable.

## When We Should Revisit It

- If sustained usage shows the free tier is exhausted or usage becomes
  billed without approval -> reconsider cost path or choice.
- If Groq becomes routable from the environment and offers materially
  better latency with comparable availability, re-evaluate.
- If a local model becomes practical and privacy/offline requirements
  emerge.

## Evidence References

- Provider bake-off and Gemini free-tier/quota/billing verification
  (this session, recorded in conversation audit; official pages:
  ai.google.dev Gemini API pricing / billing / rate-limits).
- DECISION-001 (architecture and seam principle), DECISION-003
  (no-recurring-API-cost during MVP).

## Related Documents (added 2026-09-19, for cross-reference only)

- [generation-baseline.md](../pipelines/generation-baseline.md) — the output
  contract, prompt, and error behavior this decision left undecided were
  implemented and are now recorded in
  [DECISION-011](./DECISION-011-grounded-generation-contract.md).
- [observability-ui.md](../pipelines/observability-ui.md) — BYOK credential
  handling (request-scoped key, never persisted) and the debug console built on
  this provider.
- [DECISION-010](./DECISION-010-retain-baseline-retrieval.md) — the semantic
  embedding arm's single-pass limitation was caused by this provider family's
  free-tier 429 limits.
- Engineering logs: [2026-09-13](../engineering-log/2026-09-13-generation-parametric-additions.md)
  and [2026-09-14](../engineering-log/2026-09-14-grounding-claims-were-in-supplied-evidence.md).