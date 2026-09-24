# DECISION-012: Exclude Rotated (Non-Upright) Text from Reading-Order Extraction

- **Status:** Chosen (2026-09-19)
- **Scope:** `src/clinivault_ai/chunking/reader.py` (layout/reading-order layer only)
- **Supersedes:** nothing; refines [DECISION-006](DECISION-006-pdf-parser.md)

## Decision

pdfplumber word extraction feeding the column-aware reader is filtered to
**upright text only** (`word["upright"]` truthy; words without the attribute
are kept). Rotated text — journal spine banners and rotated access watermarks
drawn at 90° — is excluded **before any layout reasoning** (gutter detection,
line assembly, region splitting). This is a structural rule about text
orientation, not a document-specific exception.

## Context

[T2D-010 ingestion-quality investigation](../pipelines/t2d-010-ingestion-quality-investigation.md)
and the earlier engineering log
(`2026-09-16-t2d-010-column-interleaving.md`) confirmed genuine multi-column
interleaving on T2D-010. The remediation unit of 2026-09-19 isolated a
distinct, *mechanically identified* contributor that the 2026-09-16
investigation had recorded only as unexplained interleaving:

- Every T2D-010 page carries a rotated 90° access watermark
  ("Downloaded from diabetesjournals.org … by guest on 08 September 2026")
  and page 1 a rotated spine banner ("Chronic Kidney Disease and Risk
  Management…"). Their glyphs share y-coordinates with body lines.
- Because pdfplumber's `extract_words(use_text_flow=False)` returns rotated
  words inline with upright body words, line assembly grouped banner words
  into body lines, interleaving **reversed** fragments ("TNEMEGANAM",
  "KSIR", "CINORHC", "YENDIK", "AESID") into paragraphs and into the page-1
  cover block.

## Problem

Rotated decorative text is not body text. Leaving it in the word stream (a)
corrupts reading order — the exact defect blamed on "multi-column
interleaving" — and (b) pollutes the gutter-coverage histogram with the
banner's page-wide extent.

## Evidence

OBSERVED (2026-09-19, from committed vs remediated `T2D-010.parsed.json`
diffs):

- 15/15 T2D-010 pages contained the rotated watermark; the pre-filter text
  interleaved its fragments mid-line on every page (2,111 characters of
  banner/watermark text removed in total; 106,583 → 104,472 chars).
- Page-1 banner fragments ("NEMEGANAM", "KSIR", "DNA", "CINORHC") sat inside
  the cover/body text flow.
- Upright body text is retained verbatim: "interprofessional expert
  committee" appears exactly once before and after; "Downloaded" count 1 → 0.
- Chunk texts and, therefore, hash-embedding vectors are UNCHANGED
  (70 chunk IDs identical in order, all 256-dim vectors byte-identical) — the
  rotated text lived in page regions that never produced chunks. The frozen
  21-case benchmark reproduces exactly (Hit@1 8/21, Hit@5 16/21,
  MRR 0.5095; T2D-010 full-ranks 19 and 11/12 unchanged).

## Alternatives considered

1. **Post-hoc text cleaning (regex out watermark strings).** Rejected:
   content-based, document/provider-specific, violates the no-cleaning
   design rule in DECISION-006/ingestion pipeline.
2. **Region-level rotation filtering (drop non-upright *lines* after
   assembly).** Rejected: too late — the damage to line assembly has already
   happened.
3. **Per-page special-casing of T2D-010 page 1.** Rejected: explicitly
   forbidden (document-specific hack).
4. **Word-level orientation filter before layout reasoning.** Chosen:
   smallest, structural, applies to any PDF with rotated banners/watermarks.

## Rationale

Text orientation is a PDF structural property reported directly by
pdfplumber (`upright`). Filtering on it requires no content knowledge,
cannot touch clinical text, and fixes the mechanism (shared y-bands) rather
than symptoms.

## Consequences

- Rotated text (spine banners, access watermarks) is permanently absent from
  parsed page text for all documents. This is intentional: it is publisher
  infrastructure, not corpus content.
- Corpus-wide regression check: all 9 documents re-parsed/re-chunked from raw
  with the new reader — chunk counts, IDs, and provenance unchanged; T2D-001/
  002/003 re-parse identical; T2D-005–009 carry the same rotated access
  watermark and their re-parse differs **only** by banner/watermark removal
  (verified by diff inspection; no body text affected). Their committed
  artifacts were not regenerated in this unit and remain internally consistent
  as parsed-with-embeddings pairs; any future re-ingestion regenerates per
  [DECISION-008](DECISION-008-artifact-storage-contract.md).
- Downstream artifacts: T2D-010 embedding artifact verified still consistent
  (70 records, IDs and vectors identical) — no regeneration required, per
  [DECISION-008](DECISION-008-artifact-storage-contract.md) the consistency
  check is what matters, and it passes.
- The honest limitation recorded in the T2D-010 ingestion investigation is
  now **corrected**, not unresolved (OBSERVED 2026-09-19 against the raw
  source): the label "11.4a" does not exist anywhere in the raw T2D-010 PDF.
  The recommendation-label series runs 11.1a–11.12b, and the finerenone/nsMRA
  recommendation is **11.8** ("To reduce CKD progression… a nonsteroidal
  mineralocorticoid receptor antagonist…"), whose text — and the finerenone
  trial evidence — **is present** in the remediated parsed artifact (pages 7
  and 10). The earlier "11.4a not locatable" finding was a mislabeled
  expectation, not an extraction gap (see engineering log).

## Regression considerations

`tests/test_reader.py::UprightWordFilterTests` (5 tests) pins: upright kept,
rotated dropped, missing attribute preserved (synthetic dicts pass through),
order-preserving/non-mutating, and the shared-y-band interleaving scenario.
Full suite: 210/210 pass.

## Related documents / commits

- Engineering log: `../engineering-log/2026-09-19-t2d-010-rotated-banner-interleaving.md`
- Pipeline docs: `../pipelines/ingestion-parsing.md`,
  `../pipelines/t2d-010-ingestion-quality-investigation.md`
- Decisions: [DECISION-006](DECISION-006-pdf-parser.md),
  [DECISION-008](DECISION-008-artifact-storage-contract.md),
  [DECISION-010](DECISION-010-retain-baseline-retrieval.md)
- Commit: (this unit) `fix: remediate t2d-010 parser extraction`
- See also [DECISION-013](DECISION-013-genesis-adoption.md): adopting a repository-native control layer was justified in part by the continuity gap this remediation surfaced at session boundaries