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
| [DECISION-001](./DECISION-001-repository-architecture.md) | Repository architecture: layered stages, plain-dict contracts, fail-loud errors, seams only where replaceability is justified | Chosen (retroactively documented) | 2026-09-13 |
| [DECISION-002](./DECISION-002-python-version.md) | Python version: 3.14 (project runtime contract) | Chosen | 2026-09-08 |
| [DECISION-003](./DECISION-003-product-direction.md) | Product direction: Type 2 Diabetes as the initial domain | Chosen | 2026-09-07 |
| [DECISION-004](./DECISION-004-corpus-strategy.md) | Corpus strategy: question-driven T2D evidence (replacing the original general-corpus plan) | Chosen | 2026-09-07 |
| [DECISION-005](./DECISION-005-initial-clinical-scope.md) | Initial MVP clinical scope: frozen T2D boundary (five question families, explicit out-of-scope list) | Chosen | 2026-09-08 |
| [DECISION-006](./DECISION-006-pdf-parser.md) | PDF parser: pdfplumber for ingestion text extraction (pypdf for validation only; PyMuPDF rejected on licensing) | Chosen | 2026-09-08 |
| [DECISION-007](./DECISION-007-generation-provider.md) | Baseline generation provider: Google Gemini `gemini-2.5-flash` (controlled provider bake-off; OpenRouter 429s, Groq unreachable) | Chosen | 2026-09-13 |
| [DECISION-008](./DECISION-008-artifact-storage-contract.md) | Artifact storage: canonical `data/<stage>/<corpus-version>/<document-id>/` paths, durability = committed, regenerate (never patch) downstream artifacts when upstream changes | Chosen (retroactively documented; refined 2026-09-19) | 2026-09-16 |
| [DECISION-009](./DECISION-009-retrieval-baseline-representation.md) | Baseline retrieval representation and configuration: hash bag-of-words embeddings, in-memory cosine index, explicit Top-K=5, fail-loud invariants | Chosen (retroactively documented) | 2026-09-13 → 2026-09-18 |
| [DECISION-010](./DECISION-010-retain-baseline-retrieval.md) | Historical retention of the baseline retrieval representation after the 21-case controlled comparison | Replaced by DECISION-016 | 2026-09-18 |
| [DECISION-011](./DECISION-011-grounded-generation-contract.md) | Grounded generation contract: evidence-only answers, explicit `no_evidence` abstention (no provider call), fail-loud errors, inspectable prompt/evidence | Chosen (retroactively documented) | 2026-09-13 |
| [DECISION-012](./DECISION-012-rotated-text-exclusion.md) | Exclude rotated (non-upright) text from reading-order extraction: rotated spine banners/watermarks interleaved into body lines; word-level orientation filter before layout reasoning | Chosen | 2026-09-19 |
| [DECISION-013](./DECISION-013-genesis-adoption.md) | Adopt Genesis as the repository-native workflow/control layer (control state, gates, receipts, approvals, recovery); `docs/` remains the sole authoritative engineering knowledge layer | Chosen | 2026-09-19 |
| [DECISION-014](./DECISION-014-benchmark-expansion.md) | Expand retrieval evaluation benchmark from 21 to 46 evidence-backed cases across all 9 corpus documents | Chosen | 2026-09-21 |
| [DECISION-015](./DECISION-015-evaluate-multiple-embedding-models.md) | Evaluate Multiple Local Embedding Models before representation switch | Chosen | 2026-09-21 |
| [DECISION-016](./DECISION-016-retrieval-representation.md) | Retrieval representation for the next integration phase: select local semantic retrieval, with raw `intfloat/e5-small-v2` as the leading candidate; no production change in this decision | Chosen | 2026-09-23 |



## Decisions in Progress

| # | Decision | Status | Milestone |
|---|---|---|---|
| — | — | — | — |

## Not Decided Yet

Still undecided (each gets a decision document when the milestone that needs it
arrives, not before):

- vector storage/database at production scale
- chunking strategy (the current chunker is explicitly a baseline)
- metadata schema beyond the current provenance fields
- abstention thresholds beyond "no evidence", truncation/context-limit policy,
  retries/streaming, and any automatic grounding/citation measurement
- persistence beyond committed artifacts, deployment/infrastructure

Retrieval strategy is recorded as DECISION-009 (baseline configuration),
DECISION-010 (historical 21-case retention outcome), and DECISION-016 (the
46-case-supported local semantic direction for a future integration unit).
Parser, embedding approach, generation provider, generation contract, and
artifact storage are decided. We deliberately keep this list short and honest
rather than pre-writing decisions we can't make yet.
