# M5 answer-reliability implementation

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-11-10

## Where It Happened

Generation stage (`generator.py`, `citations.py`, `prompt.py`,
`provider.py`), context budget (`context/builder.py`), execution
record (`pipeline/records.py`), `tests/test_answer_reliability.py`.

## What We Expected

Implement the M5 guide bullets directly: parse citation refs, add an
abstention sentinel, budget context chars, retry 429/5xx, and pin it
with a tiny labeled set — all offline, no AI judges.

## What Actually Happened

**OBSERVED:** The M4 execution-record test asserts exact top-level key
sets (`set(record) == {...}`), so the M5 record extension had to fit
inside existing sections: `abstained` widened to the new status and
`context.truncated_chunk_ids` added, with no new top-level keys. The
bundle/trace/result dicts only ever get key-based (not exact-shape)
assertions, so the new fields there were safe.

**OBSERVED:** `_post_json` already converts every `HTTPError` into a
message-only `GenerationError`, which would have forced the retry loop
to parse status codes out of message text. The fix was a purely
additive `.status` attribute on the raised error — message text and
raise sites unchanged — so the loop tests 429/5xx vs 401/403 exactly.

**OBSERVED:** A `max_chars` budget can legally be smaller than the top
item, which would turn a budget into an empty bundle and flip the run
to `no_evidence` — a packaging concern leaking into abstention
semantics. Rank 1 is therefore always kept: an empty bundle still
means empty retrieval, never a budget.

**INFERENCE:** The new M5 tests were written first and failed honestly
(31 tests: 4 failures + 23 errors for the missing behavior) before any
source was touched; after implementation the focused set (97 tests
with the neighboring stage suites) passes.

## NOT YET VALIDATED

- Live Gemini compliance: refusals carrying the `ABSTAIN:` prefix and
  citations using only printed identifiers (needs a real run).
- Whether `max_chars` in characters is an adequate stand-in for token
  budgeting at real prompt sizes.
