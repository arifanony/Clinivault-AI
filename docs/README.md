# Clinivault AI — How This Project Is Run

## What Clinivault Is

Clinivault AI is an **evidence-grounded clinical knowledge system**. It helps
users explore clinical questions using curated clinical guidelines and research
evidence, while showing where the answer came from.

For the MVP we deliberately focus on **one clinical domain: Type 2 Diabetes** —
not because other domains don't matter, but because a focused domain lets us
build a serious, curated evidence system instead of a generic "ask anything
about medicine" chatbot. (See [DECISION-003](./decisions/DECISION-003-product-direction.md).)

Basic product flow:

```
User clinical question
        ↓
Retrieve relevant evidence
        ↓
Generate a grounded answer
        ↓
Show supporting sources / evidence
        ↓
User can see where the answer came from
```

**Errata is a separate product.** It will eventually evaluate stages of an
AI/RAG system (ingestion quality, extraction quality, metadata completeness,
retrieval quality, grounding, citation quality, answer reliability). Clinivault
does not implement Errata — it only preserves the evidence, provenance, and
execution information that would let Errata evaluate this pipeline later
through a shared contract. Future integration is possible; integration is
**not** a current MVP goal.

---

This project builds the above system, and the build process itself is documented
so every important decision can be explained and defended later.

Two rules drive everything else:

1. **We decide things when we need them, not before.** At the start of each
   milestone we ask: which decisions does *this* milestone actually require?
   We make those, document them, implement, test, and move on.
2. **We measure before adding complexity.** No hybrid retrieval, reranking,
   semantic chunking, or agents until a baseline exists, a weakness is measured,
   and an improvement is tested against that baseline.

## Documentation Map

| Directory | What lives here |
|---|---|
| `docs/decisions/` | One document per meaningful engineering decision |
| `docs/architecture/` | How the system fits together (kept in sync with reality) |
| `docs/pipelines/` | How each pipeline works, block by block |
| `docs/corpus/` | Why each document is in the corpus, and how we choose documents |
| `docs/engineering-log/` | Problems we hit that taught us something |
| `docs/templates/` | The three templates used above |

## What Counts as a "Meaningful Decision"

A decision gets its own document when it affects architecture, reliability,
quality, cost, scalability, maintainability, performance, or future product
direction — parser choice, chunking strategy, embedding model, vector database,
metadata structure, retrieval strategy, LLM provider, execution record format.

Trivial choices (helper functions, naming, minor implementation details) do not
get documents. Engineering judgment applies.

## The Milestone Loop

1. Understand the current milestone
2. Identify the decisions it requires
3. Compare realistic approaches
4. Recommend one
5. Document the decision
6. Implement
7. Test
8. Record meaningful problems or findings
9. Move on

## When a Decision Changes

The old decision document is never rewritten. It gets marked `Replaced`, and a
new document explains what changed, why, and what evidence caused the change.
The project history should show how the system actually evolved.

## Documentation Must Match Reality

Docs distinguish clearly between: **implemented**, **being built**, **planned
next**, **future possibility**, and **rejected**. We don't document features
that don't exist, and diagrams don't include components just to look impressive.

## What "Done" Means

A milestone or feature is done when:

- [ ] The implementation works
- [ ] Relevant tests exist
- [ ] The decisions behind it are documented
- [ ] The pipeline behavior is explained
- [ ] Meaningful problems encountered are recorded
- [ ] Validation evidence exists
- [ ] Known limitations are written down

Documentation evolves alongside the code, not after it.

## Errata Boundary

Errata is a separate product — an external evaluation harness. This repository
produces structured evidence (execution records, ingestion records) that Errata
can consume later. No evaluation logic lives here.
