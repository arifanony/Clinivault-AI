# Document Corpus

The corpus is part of the product design, not just a folder of PDFs. Every
document in it exists for a reason we can state. The MVP domain is
**Type 2 Diabetes** — see [DECISION-003](../decisions/DECISION-003-product-direction.md).

> **How this strategy evolved:** the first working plan was a general
> healthcare PDF corpus, grown by collection. After looking at the product
> goal and what RAG evaluation actually requires, we replaced it with the
> question-driven, domain-focused strategy below. The full reasoning —
> including what we gave up — is in
> [DECISION-004: Corpus strategy](../decisions/DECISION-004-corpus-strategy.md).

## The Corpus Design Principle

The goal is NOT "get 100 PDFs." The goal is a deliberately curated clinical
evidence corpus where every document has a known purpose.

We grow the corpus by working backwards:

```
Desired clinical questions
        ↓
Required evidence
        ↓
Required document types
        ↓
Trusted / appropriate sources
        ↓
Document selection
        ↓
Ingestion
        ↓
Evidence retrieval
        ↓
Grounded answer
```

## How the Corpus Grows

Three stages. Never jump straight to a large corpus.

**Stage 1 — Clean baseline corpus (5–10 documents)**
Establish a reliable baseline for ingestion, retrieval, grounding, and
citation. Documents should be trusted, relevant to Type 2 Diabetes, relatively
clean text-based PDFs, reasonably structured, and legally available for
processing. Categories: clinical guidelines, authoritative healthcare guidance,
high-quality review papers.

**Stage 2 — Domain evidence corpus (30–50 documents)**
Expand the Type 2 Diabetes knowledge base with documents that help answer
meaningful clinical questions: current clinical guidelines, previous guideline
versions where legally available, systematic reviews, peer-reviewed research
papers, authoritative clinical evidence documents. The goal is not maximum
quantity — it's useful, diverse evidence.

**Stage 3 — Stress and evaluation corpus (100+ documents)**
Deliberately introduce harder material: long documents, complex layouts,
multi-column PDFs, tables, repeated headers/footers, older vs. newer documents,
multiple versions of similar guidance, and documents covering similar questions
with different conclusions. Purpose: expose realistic ingestion and retrieval
challenges — and eventually provide meaningful test cases for Errata.

## Why Old vs. New Evidence Matters

A retrieved answer can be perfectly grounded in evidence and still rely on
outdated guidance (an older guideline retrieved successfully, while a newer
version changed the recommendation). This separates two questions:

- *Is the answer supported by retrieved evidence?*
- *Is the retrieved evidence current and appropriate?*

The second is a future reliability/evaluation problem — good material for
Errata later. We do **not** over-engineer it now; we only make sure the corpus
and metadata (publication date, updated date, version) keep it possible to
evaluate later.

## Where Things Live

| File | What it is |
|---|---|
| [`corpus-selection-guide.md`](./corpus-selection-guide.md) | How to evaluate a candidate PDF before adding it |
| [`corpus-manifest.md`](./corpus-manifest.md) | One record per document — why it's in the corpus |

Raw PDFs live in `data/raw/`, in per-stage folders:
`stage-1-clean-baseline-corpus/`, `stage-2-domain-evidence-corpus/`,
`stage-3-stress-evaluation-corpus/`.

