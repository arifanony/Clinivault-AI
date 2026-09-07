# Document Corpus

The corpus is part of the system design, not just a folder of PDFs. Every
document in it exists for a reason we can state.

## How the Corpus Grows

We deliberately grow it in three stages. Never jump straight to a large corpus.

**Stage 1 — Parsing validation (5–10 documents)**
Deliberately varied structures so we can prove ingestion works:
- a simple, clean layout
- a multi-column research paper
- a long document (100+ pages)
- a table-heavy document
- a document with many sections and subsections
- one with references and figures
- one deliberately awkward/complex layout

Purpose: validate the ingestion pipeline before caring about retrieval quality.

**Stage 2 — Domain corpus (30–50 documents)**
One coherent healthcare domain. Mix of document types: clinical guidelines,
review articles, research papers, treatment information, diagnostic
information, risk factors, complications, medication/intervention studies.
Purpose: meaningful cross-document retrieval.

**Stage 3 — Scale testing (100+ documents)**
Tests ingestion consistency, duplicates and near-duplicates, conflicting
evidence, old vs. new publications, metadata filtering, corpus updates, and
retrieval at larger scale.

## Where Things Live

| File | What it is |
|---|---|
| [`corpus-selection-guide.md`](./corpus-selection-guide.md) | How to evaluate a candidate PDF before adding it |
| [`corpus-manifest.md`](./corpus-manifest.md) | One record per document — why it's in the corpus |

Raw PDFs live in `data/raw/`, in per-stage folders:
`stage-1-parsing-validation/`, `stage-2-domain-corpus/`, `stage-3-scale-test/`.
