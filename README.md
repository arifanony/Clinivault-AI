# Clinivault AI

Clinivault AI is an **evidence-grounded clinical knowledge system**. Users ask
clinical questions and get answers grounded in curated clinical guidelines and
research evidence — with the supporting sources shown, so it is always clear
where an answer came from.

## Why It Exists

Answers to clinical questions need to be traceable to the evidence behind
them. Rather than building a generic "ask anything about medicine" chatbot,
this project builds a focused, curated evidence system where provenance is a
core feature, and where the build process itself is documented so every
important decision can be explained and defended later.

## MVP Focus

The MVP deliberately concentrates on **one clinical domain: Type 2 Diabetes**
with a frozen initial clinical scope — a focused domain makes it possible to
build a serious, curated evidence system instead of a shallow general one.
The reasoning is documented in
[DECISION-003](./docs/decisions/DECISION-003-product-direction.md) and
[DECISION-005](./docs/decisions/DECISION-005-initial-clinical-scope.md).

## Current Status

Early-stage MVP development:

- **Done:** the Stage 1 clean baseline corpus (nine documents) is acquired and
  validated, and the ingestion/parsing baseline is implemented and tested for
  the first corpus document (T2D-001).
- **In progress:** the chunking phase — layout- and reading-order-aware text
  extraction for real clinical PDFs.
- **Not yet built:** the structural chunker and validation, embeddings, vector
  storage, retrieval, context construction, and generation. No end-to-end
  pipeline exists yet.
- Architecture documentation is written as components actually take shape,
  not before.

## Documentation

The project's documentation starts here:

| Area | What it covers |
|---|---|
| [How this project is run](./docs/README.md) | **Start here** — project rules, decision criteria, milestone loop |
| [Decisions](./docs/decisions/README.md) | One document per meaningful engineering decision |
| [Corpus](./docs/corpus/README.md) | What is in the document corpus and why |
| [Pipelines](./docs/pipelines/README.md) | How each pipeline works, block by block |
| [Engineering log](./docs/engineering-log/README.md) | Problems we hit that taught us something |
| [Architecture](./docs/architecture/README.md) | How the system fits together (written as it takes shape) |
