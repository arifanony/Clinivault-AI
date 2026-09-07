# Engineering Decision: Product Direction — Type 2 Diabetes as the Initial Domain

## Status

Chosen

## Date

2026-09-07

## Problem

Clinivault could be built as a generic healthcare chatbot — "ask anything about
medicine." A generic scope sounds bigger, but it makes everything harder and
worse: corpus curation becomes shallow (random PDFs), retrieval quality becomes
impossible to measure meaningfully, citations point at an unfocused evidence
pool, and evaluation criteria stay vague. We need to decide what the product
actually is before curating any corpus.

## What This Part of the System Does

This decision doesn't add a component — it constrains the whole product. It
defines what Clinivault is:

> An evidence-grounded clinical knowledge system that helps users explore
> clinical questions using curated clinical guidelines and research evidence,
> while showing where the answer came from.

Basic flow:

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

It also fixes the MVP domain: **Type 2 Diabetes**. Everything downstream
(corpus curation, metadata, retrieval evaluation, citations) works backwards
from real T2D clinical questions rather than from generic healthcare coverage.

## Requirements

- Answers grounded in retrieved evidence, with visible sources
- A deliberately curated corpus where every document earns its place
- Provenance and execution information preserved so the future Errata product
  could evaluate this pipeline through a shared contract
- No unnecessary AI/LLM calls or recurring API costs during MVP development

## Options We Considered

- **Option A — Generic healthcare chatbot:** cover all of medicine from day one.
- **Option B — Focused domain: Type 2 Diabetes:** one clinical domain, deeply
  curated.
- **Option C — Focused domain: something else** (hypertension, oncology,
  cardiology generally): same approach, different domain.

## Comparison

| Criterion | A: Generic | B: Type 2 Diabetes | C: Other domain |
|---|---|---|---|
| Curation effort | Very high, shallow result | Focused, deep | Focused, deep |
| Publicly available evidence | Overwhelming, unfocused | Large and well-organized | Varies by domain |
| Guideline versioning to test old-vs-new | Hard to curate | Strong (guidelines update regularly) | Varies |
| Conflicting-evidence test cases | Hard to find deliberately | Natural (evolving recommendations, e.g., cardiovascular risk) | Varies |
| Real-world clinical relevance | Broad but shallow | Strong | Strong |
| Meaningful evaluation possible early | No | Yes | Yes |

## Decision

Focus the MVP on **Type 2 Diabetes**, with the product positioned as an
evidence-grounded clinical knowledge system — not a generic chatbot.

## Why We Chose It

Type 2 Diabetes gives us everything the product needs in one place: strong
real-world clinical relevance; a large amount of publicly available evidence;
clinical guidelines with updates and versions over time; systematic reviews and
research papers; nuanced or conflicting evidence; and structured clinical
recommendations. That combination lets us test the things that matter —
grounding, citation, current-vs-outdated evidence — with a corpus we can
actually curate well. It also produces useful evaluation material for Errata
later, without merging the two products.

## Trade-offs

- A narrower demo surface: questions outside T2D are out of scope for now, even
  if the system could technically answer them.
- Discipline required: the temptation to add "just one more domain" must wait
  until the pattern works in this one.
- Some generic capabilities (e.g., broad medical terminology coverage) get
  delayed.

## What We Did Not Choose

- **Generic coverage (Option A)** — it guarantees shallow curation and vague
  evaluation. Nothing about this decision prevents expanding later; starting
  generic prevents focusing later.
- **Another domain (Option C)** — several would work, but T2D has the best
  combination of public evidence volume, guideline versioning, and
  recommendation evolution to test old-vs-new evidence deliberately.

## Assumptions

- Enough legally usable, good-quality T2D evidence exists publicly to build all
  three corpus stages (we believe this; the corpus manifest will prove it).
- The domain choice does not change the core architecture: ingestion,
  retrieval, context construction, and generation stay domain-agnostic so
  another domain could be added later as new corpus + metadata, not new code.

## How We Will Validate This

- The Stage 1 corpus (5–10 documents) establishes reliable ingestion,
  retrieval, grounding, and citation on real T2D material.
- The Stage 2 corpus answers the example clinical questions with traceable
  sources — verified during retrieval evaluation.
- Guideline-version documents in the corpus make old-vs-new comparison
  demonstrable.

## When We Should Revisit It

- If we cannot assemble a legally usable, quality T2D corpus (unlikely, but
  would force a domain change).
- After the T2D pattern proves out (Stage 2 working end-to-end), extending to
  another domain is an *addition* — new corpus + metadata — and should be
  treated as a new decision, not a scope expansion by accident.

## Related Documents

- [DECISION-004: Corpus strategy](./DECISION-004-corpus-strategy.md) — how the evidence corpus is built and grown
- [Corpus README](../corpus/README.md) — staged corpus strategy
- [Corpus selection guide](../corpus/corpus-selection-guide.md) — how documents are chosen
- [DECISION-001](./DECISION-001-project-architecture.md) (in progress) — project architecture
