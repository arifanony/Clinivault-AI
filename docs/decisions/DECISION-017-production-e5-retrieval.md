# Engineering Decision: Production retrieval representation is raw intfloat/e5-small-v2

## Status

Chosen

## Date

2026-09-25

## Problem

[DECISION-016](./DECISION-016-retrieval-representation.md) selected local dense
semantic retrieval with raw `intfloat/e5-small-v2` as the leading candidate,
but it explicitly did not change production code. Production still used
`clinivault-baseline-hash-v1`. This unit authorizes and implements that switch
behind the existing embedding seam.

## What This Part of the System Does

- What goes in: validated chunk text and query text
- What happens inside: `E5EmbeddingProvider.embed_texts` encodes strings as-is
  (no `query:` / `passage:` prefixes). Retrieval already embeds queries via
  `embed_texts([query])[0]`, so both paths stay raw.
- What comes out: 384-dimensional vectors joined to chunks by `chunk_id`
- Where the output goes next: in-memory cosine search (Top-K=5, DECISION-009)

## Requirements

- Reproduce the frozen 46-case E5 numbers: Hit@1 20/46, Hit@5 36/46, MRR 0.5583
- Keep hash artifacts at `data/embedded/` untouched
- Read EVAL-HF durable E5 artifacts at `data/embedded-intfloat--e5-small-v2/`
- Fail loud if the optional extra or local model files are missing
- Do not silently fall back to hash in the production UI

## Options We Considered

- Option A: implement raw `intfloat/e5-small-v2` as the production provider,
  reading existing E5 artifacts (chosen).
- Option B: keep hash as production until a larger labeled set exists.
- Option C: switch production to Gemini embeddings (best measured aggregate,
  rejected in DECISION-016 for MVP cost/offline constraints).
- Option D: use E5 `query:`/`passage:` prefixes (EVAL-HF-003: did not improve
  the frozen benchmark).

## Comparison

Raw E5 beat hash on Hit@1, Hit@5, and MRR under the frozen protocol. Prefixing
did not help. Cloud Gemini scored higher but is not the MVP default.

## Decision

Production retrieval representation is raw `intfloat/e5-small-v2` via
`E5EmbeddingProvider`. Hash remains available as `clinivault-baseline-hash-v1`
and as the default of `generate_embeddings()` / `benchmark --provider hash`.

DECISION-009 still owns Top-K=5, cosine, fail-loud validation, and
deterministic tie-breaking. DECISION-016 remains the direction record; this
document is the implementation authorization.

## Why We Chose It

OBSERVED: EVAL-HF-002/003 measured raw E5 at 20/46, 36/46, MRR 0.5583 versus
hash 12/46, 26/46, 0.3601 on the same 46 cases. Intended E5 prefixes did not
improve those aggregates. The durable E5 artifact tree already exists.

## Trade-offs

Local semantic encoding needs `sentence-transformers`/`torch` (optional extra)
and is slower than hashing. The 46 cases are a project benchmark, not a
universal quality proof.

## What We Did Not Choose

Cloud embeddings as the MVP default. Regenerating or overwriting hash JSON.
A multi-document index (M2). Prefix formatting.

## Assumptions

The Hugging Face cache still has `intfloat/e5-small-v2` from EVAL-HF, or the
operator can install it without changing the raw protocol. Chunking, labels,
and Top-K stay frozen for the reproduction gate.

## How We Will Validate This

- Unit tests (E5 tests skip unless the extra and local model files exist)
- `python -m clinivault_ai.evaluation.benchmark --provider e5` reproduces
  20/46, 36/46, 0.5583
- T2D-001 re-encode matches the committed E5 vector when the model is present
- Hash benchmark remains runnable and unchanged

## When We Should Revisit It

A larger labeled set, a better local model under the same protocol, or a
change to the offline/cost constraint (DECISION-016 revisit criteria).
