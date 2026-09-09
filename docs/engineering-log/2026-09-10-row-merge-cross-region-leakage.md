# Rows spanning multiple regions leak cross-gutter text: row construction happens before region assignment in `extract_page_text_column_aware()`

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-10

## Where It Happened

Visual verification of the coverage-based region detector (commit `18028cf`,
`feat: add coverage based region detection`) in
`src/clinivault_ai/chunking/reader.py`, tested against real pages of T2D-001
(`data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf`):
pages 2, 6, 13, 16, and 23.

## What We Expected

After `18028cf`, we expected region-major extraction to be reading-order-correct
on any page where `detect_region_gutters()` finds valid gutters: each detected
region read top-to-bottom, regions concatenated left to right, with no
cross-region sentence fragments — the failure mode that motivated the whole
column-detection effort.

## What Actually Happened

Gutter *detection* performed well (see below), but extracted text still shows
**cross-gutter text leakage**: words belonging to different horizontal regions
appear concatenated on single output lines.

The cause is in the extraction path of `extract_page_text_column_aware()`.
Words are grouped into rows by `round(w["top"])` **before** region assignment,
and each whole row is then assigned to a single region by the row's horizontal
center:

```python
rows.setdefault(round(w["top"]), []).append(w)   # row construction first
...
center = (min(x0) + max(x1)) / 2.0               # whole-row center
idx = ...                                        # one region per row
```

When two different document regions share a baseline (the same rounded `top`),
their words land in the **same row**, the merged row's center falls in one
region, and the row — including both regions' words — is assigned wholesale to
that region. The detector finds the gutter; the extraction step then walks
straight across it.

Terminology that matters here:

- **Visual whitespace detection** — what `detect_region_gutters()` does:
  finding low line-coverage vertical bands. This works.
- **Semantic document-column detection** — deciding that a whitespace band
  separates *text-flow columns* (rather than a table's columns or an indent).
  This is a different, unsolved problem (see related observations below).
- **Row construction** — grouping words into visual lines by rounded `top`.
  Happens before region assignment and merges across gutters.
- **Region assignment** — mapping lines (or row fragments) to regions. Currently
  row-granular, which is what leaks.

## Evidence

Pixel-ink projection over rendered page images (independent of word geometry)
confirmed every *real* gutter the detector found and exposed the failures:

| Page | Detector output | Pixel-ink check | Verdict |
|---|---|---|---|
| 2 | gutter at ratio 0.649 | visible whitespace (13.0 pt) | correct |
| 6 | gutters at 0.370 and 0.649 | 0.654 visible (7 pt); **0.370 not visible** | one real, one false positive |
| 13 | gutters at 0.350 / 0.629 | both visible (12.5 / 13.0 pt) | correct |
| 16 | gutter at 0.358 | visible whitespace (10.5 pt) | whitespace real, semantics wrong (table) |
| 23 | gutters at 0.350 / 0.629 | both visible (12.5 pt) | correct |

Leakage examples observed in extracted output (rows sharing a baseline across a
gutter keep both sides' words together):

- Page 6, region 2 start line: `"...type 1 from type 2 diabetes: Age (e.g., practice, it may be appropriate to cat..."` — left-column lead-in and right-column text on one output line.
- Page 16, region 2: `"MODY HNF1A AD HNF1A-MODY: progressive insulin secretory defect with presentation i..."` — table's left cells and the "Clinical features" column concatenated.

## Related verified observations (NOT solved)

1. **Page 6 false-positive gutter at ratio ≈ 0.370.** A whitespace band that
   exists at the *word-gap* level (hanging-indent / lead-in structure inside a
   definition list) but not at the *pixel* level. The segment-based coverage
   metric accepts it, splitting one visual text column into two consecutive
   regions. Order survives coarsely (both regions belong to the same column and
   are read consecutively) but list lead-ins are separated from their bodies.
2. **Page 16 table separator interpreted as a document region at ≈ 0.358.**
   The 10.5 pt whitespace is visually real but separates the columns of
   Table 2.7 ("Gene/Inheritance" vs "Clinical features"), not text-flow
   columns. Region-major extraction fragments table rows across two output
   blocks. The detector currently has no notion of tables, figures, or
   "whitespace that is not a column boundary".

Both remain open; no guard, threshold, or logic change was made.

## Why this matters

- Reading order is the entire point of the region detector. Leakage means the
  exact defect it was built to remove (cross-column sentence fragments)
  persists on any page where region baselines coincide — which is common in
  tables and tightly-set columns.
- It separates two concerns that must be fixed independently: detection
  (works, verified) and assignment (row-granular, leaks). Fixing one will not
  fix the other.
- Semantic misclassification (tables, indents) means region count alone is not
  a safe input for structural chunking: a correct-looking "3 regions" may
  include a table fragment.

## Current impact

- Pages 2, 13, 23: verified clean — region-major output is correct and clearly
  better than fallback ordering.
- Pages 6 and 16: gutter found is partly or wholly wrong *semantically*, and
  extracted text shows cross-gutter concatenation. Output is degraded relative
  to intent, though often still closer to correct than the interleaved
  fallback.
- Structural chunking must not treat `region_count` / detected gutters as
  ground-truth layout until assignment and table/figure handling are resolved.

## What remains undecided / future implementation work

Not decided in this unit (documentation only; no code changed):

1. **Fix region assignment granularity** — assign at segment level (the
   detector already splits rows at >8 pt word gaps for coverage) instead of
   whole-row level, so a baseline shared across a gutter splits into separate
   region fragments. Smallest candidate fix; directly addresses leakage.
2. **Table/figure guard** — e.g., pdfplumber `find_tables()` / ruling-line
   evidence to exclude table-interior whitespace from gutter candidates
   (page 16). Needs its own investigation.
3. **Persistence requirement for gutters** — require a low-coverage band to
   persist across a large fraction of page height to reject indent artifacts
   (page 6). Threshold design TBD; deliberately not tuned here.
4. **Cross-corpus validation** — all evidence is T2D-001; the pixel-ink
   cross-check should become part of verification on other documents.

## Prevention / Lesson Learned

1. Detection success is not extraction success: verifying the detector's
   geometry (gutters, ratios) says nothing about the assignment step that
   consumes it. Both need separate verification.
2. Grouping order is semantics: constructing rows before assigning regions
   silently decides that "a visual line" is atomic across the whole page
   width — an assumption multi-column layouts routinely violate.
3. Independent evidence channels (pixel-ink projection vs word geometry)
   caught both the false positive and the leakage that word-geometry-only
   checks would have rationalized.


