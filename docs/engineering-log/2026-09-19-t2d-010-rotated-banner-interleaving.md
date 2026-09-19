# T2D-010 Rotated-Banner Interleaving — Root Cause and Remediation

- **Date:** 2026-09-19
- **Type:** Parser defect investigation + remediation (reader/layout layer only)
- **Follows:** `2026-09-16-t2d-010-column-interleaving.md` (investigation, no fix),
  `t2d-010-ingestion-quality-investigation.md` (isolation)
- **Decision record:** [DECISION-012](../decisions/DECISION-012-rotated-text-exclusion.md)

## Problem

T2D-010's parsed text contained interleaved garbage in body paragraphs: page
1 mixed reversed fragments ("NEMEGANAM", "KSIR", "CINORHC", "YENDIK",
"AESID", "DNA") into the cover/abstract text, and every page interleaved
watermark fragments ("Downloaded", "from", "diabetesjournals.org…", "by",
"guest", "on", "08", "September", "2026") mid-line. The 2026-09-16
investigation had classified this as multi-column interleaving but had not
isolated the mechanical cause.

## Symptoms

- Page-1 body text visually and mechanically interleaved with unrelated
  short tokens at line boundaries.
- Rotated-fragment tokens appeared inside the same line groups as upright
  body words (shared y-bands).

## Investigation (OBSERVED)

- Raw-PDF probes (pdfplumber word dicts, `extract_words(use_text_flow=False)`):
  the interleaved tokens are **rotated 90°** glyphs — the journal spine
  banner ("Chronic Kidney Disease and Risk Management…") and the per-page
  access watermark are drawn rotated, so pdfplumber reports them with
  `upright=False` while their `top` coordinates fall inside body-line bands.
- Line assembly groups words by `top` position; rotated words therefore
  interleave into body lines **and appear reversed** (glyph order is left in
  banner-space).
- Mechanism confirmed generically: 9/9 T2D-010 pages and 5 other corpus
  documents (T2D-005–T2D-009) carry the same rotated watermark
  ("utm_source=chatgpt.com" variant) and show identical interleaving in
  their committed parsed artifacts.

## Root cause / mechanism

Rotated (non-upright) text was treated as body text by the layout layer.
Structural rule violated: decorative rotated text must never enter
reading-order assembly.

## Remediation

`reader._upright_words(words)` — a word-level orientation filter applied
immediately after pdfplumber word extraction and **before any layout
reasoning** (gutter detection, line assembly, region splitting). Words
without an `upright` attribute pass through untouched (synthetic dicts in
tests/other callers unaffected). No content matching, no page-specific
cases.

## Before / after (T2D-010, committed artifact comparison)

- Parsed text: 106,583 → 104,472 chars; 2,111 characters of banner/watermark
  removed across all 15 pages; upright body text verbatim-preserved
  ("interprofessional expert committee" count 1 → 1; "Downloaded" 1 → 0).
- Chunks: 70 → 70, IDs identical in order; the spurious `p011-c005` remains
  eliminated (table-internal-gutter guard unchanged).
- Embeddings: **unchanged by value** — fresh re-embedding from the
  remediated parsed artifact reproduces the committed 70-record
  `T2D-010.embeddings.json` byte-identically (the rotated text lived in
  regions that never produced chunk text). Per DECISION-008 the consistency
  check passes; no regeneration was required.

## Regression checks

- Full test suite: **210/210 OK** (5 new `UprightWordFilterTests`).
- Corpus-wide chunk/embedding cardinality re-check (all 9 docs): ALL-OK
  (T2D-001: 107/107 … T2D-010: 70/70).
- Full corpus re-parse from raw PDFs with the new reader:
  T2D-001/002/003/T2D-010 re-parse **identical**; T2D-005–009 differ **only**
  by rotated banner/watermark removal (verified by diff inspection: all
  changed spans are reversed banner fragments or the watermark string; no
  body text inserted or removed). Their committed artifacts were NOT
  regenerated in this unit (out of scope) and remain internally consistent
  as parsed-with-embeddings pairs; a future re-ingestion of those documents
  will require regeneration under DECISION-008.
- Frozen 21-case benchmark: reproduces exactly (Hit@1 8/21, Hit@5 16/21,
  MRR 0.5095; T2D-010 full-ranks 19 and 11/12) — expected, since chunk
  texts/vectors are unchanged.

## Retrieval diagnostic

Diagnostic only, no retrieval change (per DECISION-010). Full benchmark
re-run after remediation: **Hit@1 8/21, Hit@5 16/21, MRR 0.5095 — identical
to the frozen records**, including T2D-010 full-ranks (ckd-screening
`p001-c002` = 19; kidney-protection `p006-c004`/`p006-c003` = 11/12). This
is the expected outcome: chunk texts and vectors are byte-identical, so the
retrieval diagnostic shows no movement by construction. The observed T2D-010
retrieval weakness remains a ranking-mechanism issue (per
`retrieval-ranking-investigation.md`), not an ingestion issue.

## Label-attribution correction (OBSERVED, changes a prior finding)

The earlier investigation recorded: "the finerenone recommendation label
series (**11.4a**) could not be located anywhere in the parsed corpus." A
direct raw-PDF check in this unit establishes:

- The raw T2D-010 PDF contains **no "11.4a" label anywhere** (15 pages,
  plain pdfplumber extraction). The label series is 11.1a, 11.1b, 11.2,
  11.3, 11.4, 11.5, 11.6a–c, 11.7a, 11.7b, 11.8, 11.9, 11.10, 11.11a,
  11.11b, 11.12a, 11.12b.
- "11.4" is "Optimize glucose management" — not finerenone.
- The finerenone/nsMRA recommendation is **11.8** ("To reduce CKD
  progression… a nonsteroidal mineralocorticoid receptor antagonist…"),
  and its text plus the finerenone trial evidence **are present** in the
  remediated parsed artifact (pages 7 and 10).

Therefore the "11.4a not locatable" finding was an **incorrect expected
label, not an extraction gap**. The genuine extraction defect on T2D-010
was the rotated-banner/watermark interleaving (fixed here); q2's target
content (page-6 kidney-protection discussion) is extracted and its ranks
(11/12) reflect the ranking mechanism, not ingestion. This supersedes the
corresponding paragraph of `t2d-010-ingestion-quality-investigation.md`
(a correction note has been added there).

## Remaining limitations

- Retrieval ranking weaknesses (function-word mass, hash collisions) are
  unaffected by definition — ingestion remediation only.

## Related

- [DECISION-012](../decisions/DECISION-012-rotated-text-exclusion.md),
  [DECISION-006](../decisions/DECISION-006-pdf-parser.md),
  [DECISION-008](../decisions/DECISION-008-artifact-storage-contract.md)
- Pipeline: `../pipelines/ingestion-parsing.md`,
  `../pipelines/t2d-010-ingestion-quality-investigation.md`
- Prior logs: `2026-09-16-t2d-010-column-interleaving.md`,
  `2026-09-19-stale-t2d-010-embedding-artifact.md`
- Commit: (this unit) `fix: remediate t2d-010 parser extraction`
