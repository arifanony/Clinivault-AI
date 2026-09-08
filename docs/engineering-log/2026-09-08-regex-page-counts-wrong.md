# Ad-hoc regex page counting recorded wrong page counts in the corpus manifest

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-08

## Where It Happened

Corpus validation (pre-ingestion) → `docs/corpus/corpus-manifest.md` page
counts; surfaced by the new ingestion pipeline's page-count check on T2D-001.

## What We Expected

The manifest's recorded page counts to match the actual PDFs.

## What Actually Happened

Before a PDF library was available, page counts were derived from an ad-hoc
regex scan counting `/Type /Page` objects in raw and zlib-decompressed bytes.
For several ADA PDFs this **over-counted** (the PDFs contain stale/duplicate
page objects inside compressed object streams). The ingestion pipeline's
fail-fast page-count check then rejected T2D-001: expected 37, found 23.

## Evidence

pypdf and pdfplumber independently agree on the true page tree counts:
T2D-001: 23 (not 37) · T2D-005: 18 (not 23) · T2D-006: 33 (not 46) ·
T2D-009: 30 (not 46) · T2D-010: 15 (not 23). T2D-002/003/007/008 were
unaffected. The new ingestion run failed with "page count mismatch …
expected 37, found 23" — the check did exactly its job.

## What We Investigated / What Failed

- The regex approach cannot know which page objects are live in the page
  tree; object streams and incremental updates make raw byte scanning
  unreliable for structure.

## The Fix

- Page counts now come from real parsers (pypdf/pdfplumber page tree).
- All five wrong manifest rows were corrected to parser-based counts.
- The ingestion pipeline verifies every document against the manifest's
  recorded count before parsing, so wrong metadata fails loudly instead of
  propagating.

## Why This Fix

Parser page-tree traversal is the PDF-standard definition of "how many pages
this document has". Byte-pattern counting guesses.

## Impact

- Manifest corrections (5 rows); no raw PDF touched.
- T2D-001 ingested successfully after correction; other documents will be
  verified against manifest facts when their ingestion phase starts.

## Prevention / Lesson Learned

Ad-hoc byte-level scans are fine for quick sanity checks but must never be
recorded as authoritative metadata. Once a real parser exists, re-derive
structural facts from it — and design ingestion to verify inputs against
recorded facts so errors surface instead of propagating.
