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

Early-stage MVP development (status as of 2026-09-24):

- **Done:** the Stage 1 clean baseline corpus (nine obtained documents;
  T2D-004 is blocked-access) is acquired, validated, parsed, chunked, and
  embedded, with durable artifacts under `data/` (DECISION-008). The full
  baseline pipeline runs end to end: ingestion with column-aware reading
  order, structural chunking, embedding through a provider seam, in-memory
  cosine top-k retrieval, context construction into inspectable evidence
  bundles, grounded generation with Gemini `gemini-2.5-flash`
  (DECISION-007, DECISION-011), end-to-end traces, and a local
  observability UI. A frozen 46-case retrieval benchmark (DECISION-014)
  and a local embedding-model screen (DECISION-015) led to
  DECISION-016: local semantic retrieval with raw `intfloat/e5-small-v2`.
- **In progress:** integrating DECISION-016 into production retrieval,
  then corpus-wide retrieval, richer metadata, persisted execution
  records, and answer-reliability checks (see the roadmap in
  [docs/architecture/README.md](./docs/architecture/README.md)).
- **Not yet built:** citation validation, abstention beyond "no evidence",
  a production API, containerization, CI, and deployment infrastructure.
- Architecture documentation is written as components actually take shape,
  not before — see [docs/architecture/](./docs/architecture/README.md).

## Local setup

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```text
uv sync
copy .env.example .env
```

Then put a Gemini Developer API key in `.env` as `GOOGLE_API_KEY`. The
file is git-ignored. The observability UI can also take a per-request key;
the provider sends it in the `x-goog-api-key` header, never in the URL.

Optional local-model extra (evaluation today; production integration is
the next unit):

```text
uv sync --extra semantic
```

`--extra eval` is an alias for the same dependency.

The test gate is `python -m unittest discover -s tests` (from the
uv-managed environment). Genesis (`genesis brief .`) is the workflow
control layer. It is not a Python dependency: install Node.js >= 18, then
the official [genesis-kit](https://github.com/ayush488-glitch/genesis-kit)
CLI. Do not edit `.genesis/project.json` by hand.

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
