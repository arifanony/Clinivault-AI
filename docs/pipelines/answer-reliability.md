# Answer reliability (M5)

Status: **implemented**. Deterministic post-generation checks over the
existing pipeline — no AI judges, no retrieval-score threshold. This
document is the contract; it is not Errata logic and not a grounding
score.

## 1. What problem does this pipeline solve?

The prompt constrains the model but does not prove grounding (2026-09-13
log): cited refs were never checked, refusals on non-empty evidence
were invisible, prompts had no budget, and one transient 429/5xx failed
the whole run. M5 makes each of those observable with deterministic
rules.

## 2. What goes in?

The outputs of one `run_query(store, query, embedding_provider,
generation_provider, top_k=5, max_chars=None)` call: ranked retrieval
results, the context bundle, and the generation result — plus the
provider's attempt count.

## 3. What happens, step by step?

```
run_query inputs (max_chars=None keeps everything)
  ↓
retrieval → context → generation (unchanged order; traces as before)
  ↓
build_context(..., max_chars): best-first prefix that fits is kept;
  lowest-rank tail dropped whole items at a time → truncated_chunk_ids
  (rank 1 always kept; None = pre-M5 behavior exactly)
  ↓
build_prompt: same grounded prompt + ABSTAIN sentinel instruction +
  cite-only-printed-identifiers instruction (DECISION-020 successors
  the DECISION-011 prompt contract)
  ↓
GeminiProvider.generate: try; on 429/5xx retry with doubling backoff
  (max_attempts=3, retry_backoff_s=1.0s); 401/403, malformed, non-HTTP
  raise at once; attempts reported on success and on failure
  ↓
generate_answer: answer starting ABSTAIN: → status "abstained";
  EVIDENCE_ITEM_RANK / EVIDENCE_ITEM_CHUNK_ID refs parsed and checked
  → invalid_citations [{kind, value}]; attempts recorded
  ↓
build_execution_record: abstained true for no_evidence AND abstained;
  context gains truncated_chunk_ids (existing keys byte-for-byte)
```

Empty evidence still short-circuits: status `no_evidence`, answer
null, no provider call, `attempts: 0`, `invalid_citations: []`.

## 4. What comes out?

Result: `{..., status ∈ ok/no_evidence/abstained, attempts,
invalid_citations}`. Bundle/trace: `truncated_chunk_ids` (+ trace
`max_chars`). Record: `generation.abstained` widened,
`context.truncated_chunk_ids` added. `run_id`, `timestamp`, and all
M4 keys unchanged.

## 5. Which components are involved?

- `src/clinivault_ai/generation/citations.py` (new: parse + validate)
- `generation/generator.py` (sentinel, attempts, invalid_citations)
- `generation/prompt.py` (sentinel + cite-exact-identifiers instructions)
- `generation/provider.py` (429/5xx retry, attempts reporting)
- `context/builder.py` (`max_chars` budget, truncation reporting)
- `pipeline/__init__.py` (`max_chars` passthrough), `pipeline/records.py`
- `tests/test_answer_reliability.py` (31 tests incl. the labeled 3-case set)

## 6. Which metadata is created or preserved?

New: per-answer `invalid_citations`, per-run `attempts`, per-bundle
`truncated_chunk_ids`. Preserved: every existing key, prompt/evidence
verbatim passthrough, no keys/prompts/vectors in any new field.

## 7. What can fail?

- Provider 429/5xx persistently → `GenerationError` after `max_attempts`
  (with `.attempts`); 401/403 → immediate `GenerationError`.
- Malformed `max_chars` (non-positive, non-integer) → `ContextError`.
- Model refusal without the sentinel → reads as `ok` (known limitation).
- Well-formed but semantically wrong citation → passes (syntactic check).

## 8. How do we detect failure?

`status: abstained` with an `ABSTAIN:` answer; non-empty
`invalid_citations`; `attempts > 1`; non-empty `truncated_chunk_ids`;
raised `GenerationError`/`ContextError`. The labeled set pins the
expected outcome of each case; metrics are citation validity and
abstention correctness (both 1.0 on the set).

## 9. What evidence or logs does it produce?

Generation/context traces carry the new fields; the execution record
carries them under the Errata contract; no new files are written by
default (JSONL opt-in unchanged from M4).

## 10. What consumes the output next?

The observability UI renders status/answer/evidence as before; Errata
reads the execution record later. M6 (only if a measured retrieval
weakness appears) and M7 are untouched.

## Related decisions

- [DECISION-020](./../decisions/DECISION-020-answer-reliability.md) —
  this milestone (successor to the DECISION-011 prompt/status contract,
  which stays Chosen and unrewritten).
- [DECISION-011](./../decisions/DECISION-011-grounded-generation-contract.md) —
  the base contract this extends.
- [DECISION-005](./../decisions/DECISION-005-initial-clinical-scope.md) —
  the out-of-scope boundary the labeled refusal case exercises.
- [DECISION-019](./../decisions/DECISION-019-query-execution-records.md) —
  the record contract M5 extends additively.

## Known limitations

Syntactic citation checks only; sentinel depends on model compliance;
`max_chars` counts characters, not tokens; retry covers 429/5xx only.
Live-Gemini compliance is NOT YET VALIDATED.
