# Engineering Decision: PDF Parser — pdfplumber for Ingestion Text Extraction

## Status

Chosen

## Date

2026-09-08

## Problem

The ingestion pipeline needs a PDF parser to convert one validated PDF into
structured parsed page data. The parser choice affects license obligations,
extraction fidelity, dependency risk, and how much of the text layer we can
trust downstream. This is the first real runtime dependency of the project, so
it also had to fit the newly finalized Python 3.14 environment (DECISION-002).

## What This Part of the System Does

The parser takes one verified PDF and produces per-page extracted text plus
page geometry. It does **not** clean, normalize, chunk, embed, or interpret —
it extracts. Extraction output is treated as parser output only.

## Requirements

- Page-by-page extraction with a stable 1-based page number
- Layout-aware text extraction for machine-generated clinical PDFs
- Per-page failure isolation (one bad page must not kill the document)
- A license compatible with a closed commercial product
- Pure-Python (or at least reliably available) on Python 3.14
- Raw PDF bytes are never modified

## Options We Considered

- **Option A — pdfplumber** (MIT, built on pdfminer.six)
- **Option B — pypdf** (BSD)
- **Option C — PyMuPDF (fitz)** (AGPL-3.0 / commercial dual license)
- **Option D — pdfminer.six directly** (MIT)

## Comparison

| Criterion | A: pdfplumber | B: pypdf | C: PyMuPDF | D: pdfminer.six |
|---|---|---|---|---|
| License | MIT | BSD | **AGPL-3.0 / commercial** | MIT |
| Text fidelity / layout awareness | Good (word & char geometry) | Moderate | Excellent | Good but low-level |
| Table extraction | Built-in | Basic | Good | None built-in |
| Per-page API fit | Natural | Natural | Natural | Awkward (low-level) |
| Python 3.14 availability | Pure Python — fine | Pure Python — fine | Binary wheels — riskier | Pure Python — fine |
| Speed | Moderate | Moderate | Fastest | Moderate |

## Decision

Use **pdfplumber** as the ingestion text-extraction parser. Use **pypdf**
only as a lightweight structural-validation utility (open check, page count,
encryption detection) — not for text extraction. PyMuPDF is rejected.

## Why We Chose It

- **MIT license** — no copy-left obligations for a closed product.
- **Per-page extraction** maps directly onto our page-record model, where
  every page must carry `document_id + page_number`.
- **Layout-aware extraction** (word/character geometry from pdfminer.six)
  gives better text for multi-column clinical layouts than plain text pull.
- **Table extraction capability** matters because ADA guideline sections are
  table-heavy; we don't need it in this phase, but it avoids a future parser
  change for tables.
- **Suitable for our current corpus**: Stage-1 documents are machine-generated
  (not scanned) clinical PDFs, which is exactly pdfplumber's sweet spot.

## What This Decision Does NOT Claim

pdfplumber is **not** universally better than the alternatives:

- PyMuPDF is faster and often better on complex layouts; it was rejected
  **specifically because of its AGPL/commercial dual-licensing model**, which
  would impose obligations (or fees) on a closed product — not because of
  technical quality.
- pypdf remains in use for lightweight PDF validation (open check, page
  count, encryption detection) where its simplicity is an advantage; it is
  simply not our primary text extractor.

## Known Limitations We Accept

- **Reading order is not guaranteed.** Multi-column layouts may interleave
  text in extraction order rather than visual reading order. This is a known
  possible issue, to be *observed* on real output before deciding whether to
  mitigate.
- **Complex layouts** (sidebars, figures with embedded text, floating boxes)
  can produce fragmented or out-of-order text.
- **Slower than PyMuPDF** — acceptable at our current scale (one document).
- Hyphenation, ligatures, and spacing artifacts are passed through as-is:
  this phase performs **no semantic cleaning or normalization**.

These limitations are accepted for the first ingestion phase and must be
re-examined against actual T2D-001 extraction output before processing the
remaining Stage-1 documents.

## Trade-offs

- If complex-layout fidelity later proves insufficient, the options are
  layout-aware post-processing inside our pipeline, or revisiting this
  decision (PyMuPDF's licensing makes it a product-level decision, not a
  drop-in swap).

## What We Did Not Choose

- **PyMuPDF (Option C)** — technically strong, rejected on licensing.
- **pypdf as primary extractor (Option B)** — kept for validation only.
- **Raw pdfminer.six (Option D)** — everything we need from it comes through
  pdfplumber's API; direct use would add code without adding capability.

## Assumptions

- Stage-1 corpus documents are machine-generated PDFs with real text layers.
- MIT-licensed dependencies are acceptable for this product.

## How We Will Validate This

- The T2D-001 ingestion run must produce page records for all 37 pages with
  provenance intact, deterministic validation checks passing, and observed
  text statistics recorded — before the parser is used on any other document.

## When We Should Revisit It

- If observed reading-order or layout problems on real documents materially
  damage downstream usability
- If a needed capability (e.g., better table extraction) proves impossible
  on top of pdfplumber
- If licensing constraints change

## Related Documents

- [DECISION-002: Python version](./DECISION-002-python-version.md) — the runtime contract this dependency was added under
- [Ingestion parsing pipeline](../pipelines/ingestion-parsing.md) — the pipeline this parser powers
