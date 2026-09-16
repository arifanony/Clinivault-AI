# 2026-09-16 — T2D-010 multi-column extraction interleaving

## Category

Ingestion/parsing — document-specific quality issue (no code change made).

## Discovery

During the retrieval-ranking forensic investigation
(`docs/pipelines/retrieval-ranking-investigation.md`), the parsed T2D-010
text (ADA Standards 2026 "Chronic Kidney Disease and Risk Management"
chapter, a multi-column layout) was found to contain column-interleaved
text: tokens from two physical columns merged into one reading line.

OBSERVED example — `T2D-010-p004-c003` (parsed page 4):

> "Re- Early changes in kidney function may be mission of albuminuria may
> occur sponta- detected by increases in albuminuria be- neously, and
> cohort studies evaluating fore changes in"

Fragments from the left and right columns alternate mid-sentence
("may be" / "mission of ... may occur" / "sponta-" / "detected by ... be-
neously"). The same interleaving pattern is visible in other T2D-010
chunks (e.g., p005-c004, p008-c001 side-margins "Downloaded from
diabetesjournals.org" mixed into body text).

## Impact (OBSERVED)

- Recommendation passages are fragmented and, in the affected chunks,
  semantically damaged; the 11.4-series finerenone recommendation text
  could not be located by its label in the parsed artifact.
- T2D-010 showed the strongest reference/boilerplate domination in the
  validation unit; degraded text quality of this document is a contributing
  factor (see investigation document, case C.3/C.4), though the primary
  mechanism (hash baseline genericity) is independent of it.

## Classification

Document-specific parsing issue on a multi-column PDF. Consistent with the
existing parsing-history entries (column detection, row merging) but a
previously unobserved manifestation on this document. Not fixed in this
unit — diagnosis only.

## Action

Recorded; a dedicated ingestion-quality unit should review the multi-column
extraction path using T2D-010 as the regression case before any retrieval
change is evaluated.
