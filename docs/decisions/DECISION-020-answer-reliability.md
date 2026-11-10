# Engineering Decision: Answer reliability — citation checks, abstention sentinel, context budget, Gemini retry

## Status

Chosen

## Date

2026-11-10

## Problem

DECISION-011 made the prompt evidence-constrained and defined one
abstention path (empty evidence → `no_evidence`, no provider call), but
left everything after that unmeasured: cited ranks/chunk ids are never
checked against the evidence actually supplied, a model that refuses on
non-empty evidence is indistinguishable from a normal answer, there is
no context-char budget, and any transient Gemini 429/5xx fails the
whole run. The M1–M7 guide names this the M5 gap. The 2026-09-13 log
already showed prompt text constrains but does not prove grounding, so
M5 adds cheap deterministic checks — no AI judges, no
retrieval-score threshold without a measured decision.

## What This Part of the System Does

- What goes in: the generation result path (`bundle` + provider
  response), the context packaging path (`build_context`), and the
  Gemini HTTP path (`GeminiProvider.generate`).
- What happens inside:
  `clinivault_ai.generation.citations` parses `EVIDENCE_ITEM_RANK` /
  `EVIDENCE_ITEM_CHUNK_ID` refs from the answer and flags refs that
  match no supplied evidence item; `generate_answer` maps an `ABSTAIN:`-
  prefixed answer to status `"abstained"` and records `attempts` +
  `invalid_citations`; `build_context(..., max_chars=...)` drops the
  lowest-rank tail whole items at a time and reports
  `truncated_chunk_ids`; `GeminiProvider` retries 429/5xx with doubling
  backoff and reports `attempts` on success and on failure.
- What comes out: result keys `status ∈ ok / no_evidence / abstained`,
  `attempts`, `invalid_citations`; bundle/trace keys `max_chars`,
  `truncated_chunk_ids`; execution-record `abstained` true for
  `no_evidence` and `abstained`, plus record `context.truncated_chunk_ids`.
- Where the output goes next: the observability traces and the Errata
  execution-record contract (`docs/pipelines/execution-recording.md`);
  no Errata logic lives here.

## Requirements

- Parse both ref styles the prompt stamps (`EVIDENCE_ITEM_RANK: N`,
  `EVIDENCE_ITEM_CHUNK_ID: <id>`); put misses on the result as
  `invalid_citations: [{kind, value}]`; never raise on weird answer text.
- Keep empty-evidence abstention exactly (no provider call, answer
  null, `attempts: 0`).
- Sentinel is the exact prefix `ABSTAIN:` on the stripped answer when
  evidence exists but the model refuses; prompt teaches the sentinel
  via a successor instruction (this document — DECISION-011 itself is
  never rewritten).
- **No retrieval-score threshold** without a measured decision.
- Context `max_chars`: drop the lowest-rank tail whole items at a
  time; record `truncated_chunk_ids` in bundle, trace, and execution
  record; rank 1 is always kept so a budget alone never empties a
  non-empty bundle; `None` keeps the exact pre-M5 behavior; malformed
  budgets fail loud (`ContextError`).
- Gemini retry on 429/5xx only, up to `max_attempts` (default 3) with
  doubling backoff from `retry_backoff_s` (default 1.0s); record
  `attempts` on success and as an exception attribute on failure; no
  retry on 401/403, malformed responses, or non-HTTP errors.
- Tiny labeled set with a fake provider: in-scope supported,
  DECISION-005 out-of-scope refusal, empty evidence. Metrics: citation
  validity, abstention correctness.
- Never persist keys, prompts, or vectors in any new field.

## Options We Considered

- Option A: deterministic post-generation checks + sentinel + budget +
  narrow retry (chosen).
- Option B: AI-judge grounding scores. Rejected: no labeled grounding
  dataset exists (same reason DECISION-011 deferred claim
  verification), and a judge would add cost, latency, and its own
  unmeasured error.
- Option C: retrieval-score abstention threshold. Rejected without a
  measured decision — the guide explicitly forbids it, and scores are
  not calibrated to answerability.
- Option D: mid-text truncation/summarization to fit the budget.
  Rejected: cutting item text corrupts provenance; whole-item tail
  drop keeps every kept item verbatim.
- Option E: retry every failure including 401/403. Rejected: auth
  errors never heal on retry and hammering them hides credential
  problems; fail loud instead.

## Comparison

| Criterion | A: deterministic checks | B: AI judge | C: score threshold |
|---|---|---|---|
| Needs labeled data | No (3-case set suffices) | Yes (absent) | Yes (absent) |
| Extra latency/cost | ~zero | Per-answer call | Zero but uncalibrated |
| Failure direction | Loud (raise / flag) | Silent judge error | Silent wrong abstention |
| Provenance intact | Yes | Yes | Yes |

Retry and budget variants (D, E) were rejected on robustness, not cost:
mid-text cuts corrupt evidence, and retrying auth errors hides the real
problem.

## Decision

Option A. M5 is deterministic answer-reliability checks only, with the
exact sentinel, budget, retry, and metric semantics in Requirements.

## Why We Chose It

- It closes the M5 gap the guide measured without inventing data we do
  not have: every check runs offline with fake providers, and the
  labeled set pins the three reliability outcomes (supported,
  refused, no evidence) the product actually promises.
- It preserves the fail-loud stage semantics from DECISION-001:
  invalid citations are flagged, not hidden; auth errors still raise
  at once; malformed budgets raise instead of silently reshaping the
  bundle.
- It keeps the Errata contract additive: existing record keys are
  byte-for-byte, `abstained` only widens to the new refusal status,
  and the one new record field (`context.truncated_chunk_ids`) has no
  exact-shape test to break.

## Trade-offs

- Citation parsing is syntactic, not semantic: a correctly formatted
  ref to the wrong item still passes. Claim-level verification stays
  deferred (as in DECISION-011).
- The sentinel depends on model compliance: a refusal without the
  prefix reads as `ok`. The prompt teaches it, but nothing enforces it.
- `max_chars` counts characters, not tokens: it bounds prompts
  crudely, not precisely.
- Retry adds worst-case latency (two backoff sleeps at defaults)
  before a persistent 5xx surfaces.

## What We Did Not Choose

Post-generation claim verification, grounding scores, chain-of-
verification prompts, structured evidence-span attribution,
retrieval-score abstention thresholds, mid-text truncation, retry on
401/403 or non-HTTP errors, streaming — all still undecided, as listed
in DECISION-011 and the 2026-09-13 log.

## Assumptions

- The prompt's `EVIDENCE_ITEM_RANK` / `EVIDENCE_ITEM_CHUNK_ID` stamps
  stay stable; the parser follows them, not the other way round.
- `attempts` from third-party providers is advisory; only
  `GeminiProvider` guarantees it.
- Three labeled cases pin the contract; they do not prove real-model
  compliance (NOT YET VALIDATED until a live Gemini run is measured).

## How We Will Validate This

- Unit tests (`tests/test_answer_reliability.py`, 31 tests): citation
  parsing/validation, sentinel mapping (including near-miss
  non-sentinels), budget tail-drop + record propagation, retry matrix
  (429→ok, 5xx exhaustion, 401/403 no-retry, malformed no-retry, config
  rejection), and the labeled 3-case set with citation-validity and
  abstention-correctness metrics at 1.0.
- Full gate: `python -m unittest discover -s tests` (E5 tests skip
  without the HF cache; the sandbox-proxy `test_ui` note from M4 still
  applies).
- Benchmark unchanged (no retrieval-math change): E5 Hit@1 20/46,
  Hit@5 36/46, MRR 0.5583.

## When We Should Revisit It

- If live Gemini runs show refusals without the sentinel, or citations
  that are well-formed but semantically wrong — that is the signal for
  claim-level verification, not more syntax.
- If prompts approach model context limits, revisit char-vs-token
  budgeting.
- If 429/5xx patterns change (e.g. Retry-After headers matter), extend
  the backoff rather than the retry set.
