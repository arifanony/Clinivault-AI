# Engineering Decision: Grounded Generation Contract — Evidence-Only Answers, Explicit No-Evidence Abstention, Fail-Loud Errors

## Status

Chosen (retroactively documented)

## Date

2026-09-13 (implemented in `7fba7c1`; error contract hardened in `1f6c1fc`)

## Decision Question

What exactly does the generation stage return, what does it do when retrieval
supplies **no** evidence, and how do provider/input failures surface — given that
DECISION-007 chose the provider but explicitly left the output contract, prompt
format, and abstention behavior undecided?

## Problem

DECISION-007 fixed `gemini-2.5-flash` behind a provider seam and listed the
generation output contract, prompt format, abstention logic, and truncation policy
as still undecided. The generation stage then had to define its contract before
any answer could be trusted or measured: does an empty evidence bundle produce a
call to the model at all, is a failed provider call silent, and what is returned
alongside the answer so a human can check grounding?

## What This Part of the System Does

```
context/evidence bundle
  -> input contract validation (malformed -> GenerationError)
  -> empty evidence -> status "no_evidence", answer null, NO provider call
  -> prompt construction (query + every evidence item with rank/chunk_id/
     document_id/page_number + instruction to answer ONLY from the supplied
     evidence and cite identifiers when possible)
  -> one provider call through the GenerationProvider seam
  -> result: answer + exact evidence used + provider/model + status + timings
     + provider usage metadata
```

Output contract: `{query, answer, status, provider, model, prompt_text,
evidence, timings{prompt_construction_ms, llm_generation_ms, total_ms}, usage}`.

- `status` ∈ `ok` / `no_evidence` / `failed`; `answer` is null unless `ok`.
- `evidence` is the verbatim input evidence list; `prompt_text` is the exact
  prompt sent; `usage` is passed through without arithmetic.
- Provider failure, empty response, or malformed response → `GenerationError`.
  Errors may include the provider's message but never credentials.

## Options We Considered

- **Option A — evidence-constrained prompt + explicit `no_evidence` abstention +
  fail-loud errors + fully inspectable prompt/evidence (chosen).**
- **Option B — always call the provider** and let it answer from parametric
  knowledge when evidence is missing: rejected; contradicts the evidence-grounded
  product promise (DECISION-003).
- **Option C — silent fallback / empty answer on provider failure**: rejected;
  hides failures and makes runs unreconstructable.
- **Option D — post-generation claim verification, grounding scores, structured
  evidence-span attribution**: deferred, not rejected — no labeled grounding
  dataset exists, and the UI's Grounding Analysis panel is an explicitly labeled
  placeholder rather than a fake score.
- **Option E — treat the prompt constraint as a *sufficient* grounding
  guarantee**: rejected by observation — the first real run added two claims that
  (as recorded at the time) were not in the supplied evidence (2026-09-13
  engineering log). The general lesson stands: prompt text constrains but does
  not prove grounding.

## Decision

Option A. The generation stage answers only from supplied evidence, returns an
explicit `no_evidence` result with `answer: null` and no provider call when the
evidence bundle is empty, raises `GenerationError` on any input/provider failure,
and returns the exact prompt and evidence used so that grounding can be inspected
after the fact.

## Why We Chose It

- A clinical evidence product must never present ungrounded text as
  evidence-backed; refusing is the safe failure direction, and the repository has
  now measured that direction in practice: in the corpus generalization
  validation, every case where retrieval missed returned "no answer" rather than a
  wrong answer (`retrieval-ranking-investigation.md` §F).
- Returning the exact prompt and evidence items is what later made the
  retrieval-trace forensic re-check possible (which overturned a grounding
  misclassification — see the 2026-09-14 engineering log).
- Fail-loud errors keep the pipeline's failure semantics consistent with every
  other stage (DECISION-001: one error type per stage, no silent drops).

## Trade-offs Accepted

- Abstention means retrieval weakness surfaces to the user as "no answer"; there
  is no fallback summarization. This is intentional and documented.
- Prompt constraints reduce, but do not eliminate, parametric additions, and
  there is **no automatic claim-to-evidence verification** yet.
- No context-limit/truncation policy, no retries, no streaming (a 5-item,
  ~8.5k-character prompt is the largest case actually exercised).
- Grounding quality is not measured systematically (single-run observations,
  manual claim classification).

## What We Did Not Choose (yet)

- Post-generation claim verification; hallucination-rate measurement;
  chain-of-verification prompts; mandatory structured evidence-span attribution;
  truncation/summarization policy; abstention thresholds beyond "no evidence".
  All are listed as undecided in the 2026-09-13 engineering log.

## Evidence

- `docs/pipelines/generation-baseline.md` — contract, provider, error behavior,
  real T2D-001 run (prompt/tokens/latency, claim classification).
- `docs/pipelines/observability-ui.md` — `no_evidence` rendering
  (`provider_called: false`, no fabricated answer) and the labeled grounding
  placeholder.
- `docs/engineering-log/2026-09-13-generation-parametric-additions.md` — the
  observation that motivated the "prompt text is not proof" caveat.
- `docs/engineering-log/2026-09-14-grounding-claims-were-in-supplied-evidence.md`
  — the re-check that revised two of those claims.
- Commits `7fba7c1` (baseline grounded generation), `1f6c1fc` (input error
  contract), `cfea9e1` (generation trace).

## How We Will Validate This

- Unit tests: input contract failures, empty-evidence path without a provider
  call, provider failure/empty/malformed responses, exact prompt/evidence
  preservation (`tests/`).
- Real run: one T2D-001 query against `gemini-2.5-flash` with tokens, latency, and
  claim classification recorded.

## When We Should Revisit It

- If a boundedly-scoped grounding measurement becomes available (labeled
  claim-evidence pairs or an automatic checker), revisit the "prompt + abstention"
  sufficiency question.
- If prompts approach context limits, or if retries/streaming become
  requirements.
- If the product needs answers to partial evidence (e.g. explicit
  "insufficient evidence in corpus" responses distinct from `no_evidence`).

## Related Documents

- [DECISION-007: generation provider](./DECISION-007-generation-provider.md) — provider selection and the explicitly deferred contract.
- [DECISION-001: repository architecture](./DECISION-001-repository-architecture.md) — stage contracts and fail-loud error rule.
- [generation-baseline.md](../pipelines/generation-baseline.md), [observability-ui.md](../pipelines/observability-ui.md).
- [Engineering logs](../engineering-log/README.md): 2026-09-13 and 2026-09-14 entries.

## Related Commits

`7fba7c1`, `1f6c1fc`, `cfea9e1`, `ee47ec9`, `4ab0652`.