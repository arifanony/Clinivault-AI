# Engineering Decision Index

One document per meaningful decision. Naming: `DECISION-001-short-name.md`.

We don't write decisions for the whole project up front. At the start of each
milestone we identify the decisions that milestone actually requires, make
those, and document them. Future decisions stay undecided until their
milestone arrives.

Use the template in [`docs/templates/decision-template.md`](../templates/decision-template.md).
Status values: Proposed / Chosen / Replaced / Rejected. A Chosen decision is
never rewritten — if it changes, mark it Replaced and write a new document.

## Decisions Made

| # | Decision | Status | Date |
|---|---|---|---|
| [DECISION-003](./DECISION-003-product-direction.md) | Product direction: Type 2 Diabetes as the initial domain | Chosen | 2026-09-07 |
| [DECISION-004](./DECISION-004-corpus-strategy.md) | Corpus strategy: question-driven T2D evidence (replacing the original general-corpus plan) | Chosen | 2026-09-07 |

## Decisions in Progress

| # | Decision | Status | Milestone |
|---|---|---|---|
| DECISION-001 | Project architecture (repo layout, layer boundaries) | Proposed | M1 |
| DECISION-002 | Python version | Proposed | M1 |

## Not Decided Yet

Everything else — parser, chunking, embedding, vector database, metadata,
LLM provider, retrieval, context construction, abstention, persistence,
deployment. Each gets its decision document when we reach the milestone
that needs it. We deliberately keep this list short and honest rather than
pre-writing decisions we can't make yet.

