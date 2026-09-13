# Engineering Decision: Repository Architecture — Stage Boundaries, Contracts, and Seams

## Status

Chosen (retroactively documented)

## Date

2026-09-13 (choices made incrementally during M1, 2026-09-08 to 2026-09-10,
commits `ad2923c` through `ace908d`; recorded here once the architecture had
actually been built and tested, rather than pre-written)

## Problem

The project needed to decide, before generation and evaluation work, how the
pipeline stages are organized in code: how components relate to each other,
what contracts connect them, and where abstraction seams are placed. This was
carried in the decision index from project initialization as
"Project architecture (repo layout, layer boundaries) | Proposed | M1" and
was made concretely, stage by stage, while implementing the first vertical
slice. Without writing it down, the shape of the system — and the reason it
looks the way it does — would live only in the code.

This is NOT a "final architecture" document. Clinivault is still evolving;
this records the foundational choices made so far and what they deliberately
do not yet include.

## What This Part of the System Does

Not a runtime component. It fixes the repository's architectural rules:

1. **Layered stage packages in strict data-flow order.** One package per
   pipeline stage under `src/clinivault_ai/`: `ingestion` -> `chunking` ->
   `embedding` -> `retrieval` -> `context`. Each stage consumes only the
   previous stage's output; no stage imports a later one (verified: no
   downstream-to-upstream imports exist).
2. **Plain-dict stage contracts.** Every stage exchanges JSON-serializable
   dicts with documented required fields (page records, chunk records,
   embedding records, retrieval results, evidence bundles). Where artifacts
   are persisted, a reload-equivalence check (semantic compare, never byte
   compare) validates them.
3. **Fail-loud stage errors.** Each stage defines one error type
   (`IngestionError`, `EmbeddingError`, `RetrievalError`, `ContextError`);
   inconsistency raises instead of dropping, padding, or silently
   reinterpreting records.
4. **One explicit seam.** `EmbeddingProvider` is the only provider
   abstraction, required by the project brief's replaceability rule.

## The seam principle

**Use explicit boundaries between pipeline stages and introduce abstraction
seams only where current requirements justify replaceability. Avoid
speculative abstractions.**

Currently:
- `EmbeddingProvider` is an explicit provider seam (the project brief
  requires the embedding model to be replaceable, and DECISION-003's
  no-recurring-API-cost rule needs a deterministic local baseline).
- Other components (parser wrapper, vector store, future generation
  provider) remain concrete until a demonstrated requirement justifies
  abstraction. This is a current-state statement, not a permanent refusal:
  the moment a stage shows a real second implementation need, a seam can be
  introduced and this decision is revisited under the repository's
  decision-change process.

## Requirements

- Every pipeline stage must be independently testable from its input
  contract (proven: all five stages are tested with synthetic inputs, no
  network).
- Stage contracts must survive JSON round-trips unchanged (proven: the
  ingestion reload-equivalence check and the deterministic embedding and
  retrieval artifacts).
- Provenance must survive every stage boundary: document -> page -> chunk
  -> embedding -> retrieval result -> evidence bundle (proven end-to-end
  on T2D-001).
- Inconsistent inputs must fail loudly at stage boundaries, never silently
  produce partial or padded output.
- Adding a stage must not require modifying earlier stages.

## Options We Considered

- **Option A — layered packages, plain-dict contracts, one seam (chosen).**
- **Option B — fewer, larger modules:** simpler at first, but merges
  responsibilities (parsing vs chunking vs validation) that evolved
  separately and would have made the reader fixes of 2026-09-09/10 harder
  to isolate.
- **Option C — abstraction seams for every stage (parser, store, LLM) from
  day one:** speculative abstractions with no demonstrated second
  implementation; would have added indirection before any requirement
  justified it.
- **Option D — typed dataclass/dataclass-heavy contracts everywhere:**
  stronger static guarantees, but the pipeline's artifacts are
  JSON-oriented evidence records; plain dicts with validated required
  fields kept serialization trivial and the contracts inspectable.

## Comparison

| Criterion | A | B | C | D |
|---|---|---|---|---|
| Stage isolation and testability | Good | Weak | Good | Good |
| Serialization/evidence-friendliness | Good | Good | Good | Weaker (mapping overhead) |
| Fits observed change patterns | Yes (reader fixes stayed local) | No | Indirection without need | No |
| Alignment with "avoid speculative abstractions" | Yes | Neutral | No | Neutral |

## Decision

Option A. Layered stage packages in strict data-flow order; plain-dict,
JSON-serializable stage contracts; one error type per stage with
fail-loud semantics; a single `EmbeddingProvider` seam under the
principle that seams are introduced only where current requirements
justify replaceability.

## Why We Chose It

The pattern was proven by the work itself: the reading-order defects
(2026-09-09/10 engineering-log entries) were fixed entirely inside
`chunking/reader.py` with its tests green throughout; the embedding
provider seam made the deterministic baseline provider and any future
semantic model interchangeable without touching the pipeline; and every
stage was developed and verified against synthetic inputs before touching
real data. No alternative was observed to serve these outcomes better,
and the rejected options describe costs that were not paid.

## Trade-offs Accepted

- Retrieval is an in-memory brute-force index over a JSON artifact — no
  vector-store abstraction or persistence seam exists (a production
  vector database would be its own future decision).
- Stage contracts are plain dicts: fewer static guarantees, in exchange
  for trivially serializable, inspectable evidence records.
- `context` currently validates the retrieval result contract strictly
  and ignores unknown extra fields rather than passing them through.

## Related Decisions

- [DECISION-006: PDF parser](./DECISION-006-pdf-parser.md) — the parser
  choice this architecture wraps.
- Future decisions this one deliberately leaves open: embedding model,
  vector storage, generation provider, abstention. Each is decided when
  its milestone arrives.
