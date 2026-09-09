# Column-split detection rejects the real gutters: 5%-of-page-width threshold is too strict for T2D-001

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-09

## Where It Happened

Chunking phase, Step 1 verification — `detect_column_split()` in
`src/clinivault_ai/chunking/reader.py` tested against real pages of T2D-001
(`data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf`),
checkpoint `7a5fc40` (after the `return best_mid` restoration).

## What We Expected

The module's own docstring claims the heuristic was "Tuned on T2D-001: the
gutter between content columns is ~210 pt on a 594 pt-wide page; the small
gaps within a column are <10 pt", with `DEFAULT_COLUMN_GAP_THRESHOLD = 15.0`
and a rejection rule `best_gap < page_width * 0.05`. We expected pages that
visually contain two-column content (13, 23) to yield a detected split.

## What Actually Happened

`detect_column_split()` returned `None` on all three representative pages.
The `return best_mid` path is live and reachable — `None` here is a
*legitimate* algorithm outcome, not the missing-return bug. The diagnostic
gaps between consecutive distinct `x0` positions:

| Page | Words | Largest interior x0-gap | Gap midpoint | ≥ 15 pt threshold | Passes `page_width * 0.05` (≈ 29.7 pt)? |
|---|---|---|---|---|---|
| 2 | 916 | 29.2 pt | 555.1 | yes | **no** |
| 13 | 974 | 23.5 pt | 558.0 | yes | **no** |
| 23 | 1283 | 23.5 pt | 558.0 | yes | **no** |

Every candidate gap passes the 15 pt minimum but is rejected by the
`page_width * 0.05` rule, so the function correctly returns `None` and
extraction falls back to top-then-x0 sorting.

## Why the original assumption did not hold

The documented tuning story assumed the dominant gutter shows up as a large
gap between consecutive *distinct x0 start positions*. On the real geometry it
does not, for a structural reason: the gap list is built from **word start (x0)
positions only**, not from the space between the left column's right edges
(x1) and the right column's left edges (x0). Left-column words with indented
or mid-column x0 values fill the x-range between the columns, so the widest
actual inter-column gutter never appears as a consecutive-x0 gap at all. What
remains are modest gaps from ragged line endings and indents (23–29 pt), and
the 5%-of-page-width rule (≈ 29.7 pt) — introduced to reject narrow
false-positive gaps — is tuned just above them, so it rejects every real
candidate. The ~210 pt figure in the docstring does not correspond to any
observable x0-gap on these pages.

## Evidence

- Gap diagnostics computed by replicating `detect_column_split()` internals
  (same x0 set, same edge margins) over pdfplumber word data from the open
  file: table above; page width 593.972 pt.
- Reading-order impact observed on the fallback output (pages 13 and 23):
  clearly interleaved text across columns. Page 13 head:
  `"regarding ICIs, PD-1 (e.g., nivolumab) and A1C may not capture the early peak of trauma or pancreatectomy, neoplasia,"` —
  mid-sentence fragments from left and right columns alternate.
- `return best_mid` restored in `7a5fc40` was verified live (module imports;
  the function returns real midpoints when the thresholds are satisfied) —
  the failures above are threshold behavior, not the return-path bug.

## What We Investigated / What Failed

- Confirming the missing-return fix took effect (it did; failures are not the
  old bug).
- Measuring the actual gap distribution to determine whether `None` was a
  legitimate result or a regression — it is legitimate under the current rule,
  which is precisely the problem.

## The Fix

**Not fixed in this unit (deliberate).** No threshold was changed and no
algorithm redesigned. The diagnosis points at a design flaw to be decided
separately: gap detection likely needs to measure the gutter between column
*x1* right edges and *x0* left edges (or use per-row column attribution), and
the 5% rule's purpose (rejecting narrow false positives) needs to be
reconciled with real gutters of ~20–30 pt between *x0* values. That is a
decision and an implementation unit of its own.

## Why This Fix (when applied)

The current detector cannot see the feature it claims to detect on the very
document it was "tuned" on. Any threshold adjustment made before fixing the
gap metric itself would be fitting to a proxy signal.

## Impact

- Two-column detection is effectively dead on the real corpus: every tested
  T2D-001 page falls back to interleaved top-then-x0 reading order.
- The fallback output is usable as raw text but is not reading-order-correct;
  any chunking built on it today would inherit cross-column sentence
  fragments.
- Downstream chunking design must not assume column-aware extraction works
  until this is resolved.

## Prevention / Lesson Learned

1. "Tuned on T2D-001" claims must be re-verified against the actual document
   once a real corpus exists — the tuning story and the geometry disagreed.
2. A heuristic documented with specific numbers (~210 pt gutter, <10 pt inner
   gaps) that cannot be reproduced from the code's own measurement (distinct
   x0 gaps) is a red flag: the measurement and the claim were never made in
   the same terms.
3. Always distinguish "the bug is fixed" from "the feature now works": the
   return-path fix was verified correct, and the feature still fails for an
   independent reason.

## Follow-up Investigation — Variable-column grid and a coverage-based candidate signal

> Added 2026-09-09 after a read-only diagnostic pass across all 23 T2D-001
> pages (checkpoint `163b8ea`, after the closed-PDF fix). This section records
> what was measured, what the measurements suggest, and a candidate direction
> for the next implementation unit. **No production code was changed in this
> unit and the candidate below is not implemented.**

### Method

- Word/line geometry read with pdfplumber; approximate text lines reconstructed
  by grouping words on rounded `top` (3 pt tolerance) — the same grouping
  `_words_to_lines()` already uses.
- All geometry expressed **page-relative** (ratios of page width; width is
  593.97 pt) to avoid hard-coding T2D-001 coordinates.
- Two read-only metrics computed per page:
  1. **Word-interval band inventory** — union of all word `[x0, x1]` intervals
     merged with 6 pt linkage, keeping bands with ≥ 30 words.
  2. **Per-line coverage profile** — `coverage(x)` = the fraction of
     reconstructed lines that have a word interval covering x, scanned at
     1 pt steps over the interior 15 %–85 % of page width.

### OBSERVED

1. **Band inventory across all 23 pages** (band x-ranges as page-width ratios):

   | Layout | Pages | Content bands (ratios) |
   |---|---|---|
   | One full-width band | 2, 3, 5, 6, 10, 16 | ~0.10–0.92 |
   | Two bands, narrow+wide (~154 pt + ~320 pt) | 4, 8, 12, 14, 18, 20, 22 | ~0.10–0.36 + ~0.38–0.92 |
   | Two bands, wide+narrow (~320 pt + ~154 pt) | 1, 9, 17 | ~0.08–0.62 + ~0.64–0.90 |
   | Three equal bands (~154 pt each) | 7, 11, 13, 15, 19, 21, 23 | ~0.08–0.34, 0.36–0.62, 0.64–0.90 |

   - Real inter-band gutters measured between band edges (left band's `x1` →
     right band's `x0`): **10.8–11.9 pt** (e.g., 202.1 → 213.8 on page 13).
   - A **persistent narrow right-edge band** at x ≈ 569.7–575.7 (≈ 6 pt wide,
     31–80 words) appears on nearly every page, separated from main content by
     a 23–37 pt gap — a sidebar/margin element, not a content column. Page 5
     lacks it entirely.
   - Full-width elements exist: a running header line at top ≈ 30.8 spanning
     35.9–546.0, table captions, and on page 2 table rows spanning ~65.8–497.9.

2. **Coverage profile on the representative pages** (runs where coverage ≤ 5 %
   of lines, interior scan):

   | Page | Gutter runs ≤ 5 % coverage | Run width | Max coverage inside run |
   |---|---|---|---|
   | 2 | 0.640–0.658 | 11.0 pt | 3 % (table rows cross the left gutter, which only dips at isolated points) |
   | 13 | 0.340–0.359 and 0.620–0.638 | 11.0 pt each | 1 % / 0 % |
   | 23 | 0.340–0.359 and 0.620–0.638 | 11.0 pt each | 0 % / 0 % |

   Direct checks: page 13 at x = 207.9 (inside the first gutter) — **0 of 119
   lines** cover it; word-span crossings at both gutter positions — **0 of 119**
   (page 23: 0 of 123). Page 2's line-length distribution (p25 = 154.1,
   median = 154.1, p75 = 320.0) confirms band-shaped lines rather than
   full-width paragraphs, despite its table content merging the interval union
   into one band.

### INFERENCE (suggested by the measurements, not separately proven)

- The "single-column vs two-column" hypothesis is **refuted** for this
  document: T2D-001 is a **variable-column grid** — pages use 1, 2, or 3
  content bands on a consistent grid (bands ≈ 154 pt wide, boundaries at
  stable ratios ~0.34/0.36 and ~0.62/0.64), with some pages mixing band widths.
- The real gutters are **~11 pt wide — below both the 15 pt `gap_threshold`
  and the ≈ 29.7 pt `page_width * 0.05` rejection**. Even a corrected x1-to-x0
  gap metric would need a much smaller minimum plus interior filtering. The
  reliable signal is a **sustained low line-coverage region**, not a large gap
  between distinct x0 positions.
- A page-level single-split model (the current `detect_column_split` contract)
  cannot represent 3-band pages; reading order needs **N regions**, not one
  split point.
- The right-edge sidebar creates a spurious low-coverage gap at ratios
  ~0.92–0.96; an interior scan window (~15 %–85 %) excludes it without
  special-casing.
- On page 2 the left gutter is crossed by table rows, so coverage there never
  sustains ≤ 5 % — a coverage-based detector would find **one** gutter and
  split page 2 into (table + left text) | (right text). That matches the
  layout's major visual regions, but it is a **fallback-quality result for
  table pages**, not a verified reading order.

### CANDIDATE ALGORITHM (defined for the next unit, not implemented)

1. Reconstruct lines by top-grouping (existing `_words_to_lines` grouping).
2. Scan `coverage(x)` at 1 pt steps over an interior window (e.g., 15 %–85 %
   of page width) — page-relative, no absolute coordinates.
3. Gutter candidates = contiguous runs where coverage ≤ a small tolerance
   (observed real gutters sustain ≤ 1 % on pure-text pages and ≤ 3 % on mixed
   pages; e.g., 5 %).
4. Keep runs with width ≥ a minimum gutter width (observed 11.0 pt on pages
   2/13/23; **page 7 has an irregular 7.2 pt gutter**, so the threshold must
   sit below ~11 pt — e.g., 6–10 pt — accepting page-7 irregularity).
5. Require sustained text on both sides of each surviving gutter (minimum
   word/line volume per side) — filters margins and the sidebar band.
6. Surviving gutters → N−1 region boundaries → N regions; column-major
   reading order per region (a generalization of the current single
   `split_x`); zero surviving gutters → current single-column fallback.

### NOT YET VALIDATED

- All thresholds (coverage tolerance, minimum gutter width, interior window):
  only observed ranges, not tuned.
- Reading-order correctness for N-region column-major output, especially on
  table-heavy pages (2) and mixed-band pages (4, 8, 12, 14, 18, 20, 22).
- Behavior beyond T2D-001 — no other corpus document has been tested.
- Page 7's irregular 7.2 pt gutter (its band 2 is ~158.8 pt wide, suggesting
  an embedded table); not investigated at line level.
- Whether the sidebar band (31–80 words/page) should ever appear in the output
  text at all (today it does, as right-margin text in fallback order).
- No explicit check for rotated text or non-grid layouts.

### Conflicting layout evidence (honest notes)

- The layout hypothesis "single-column pages vs two-column pages" does not
  hold: page-level band counts vary 1/2/3, and page 2 mixes a table with
  columnar text. Any next implementation must be evaluated per page, not per
  document.
- Page 7's second gutter is 7.2 pt — narrower than every other measured
  gutter; a single minimum-width rule will classify page 7 as 2-band rather
  than 3-band.
- Page 5 lacks the right-edge sidebar band entirely; sidebar presence is not a
  reliable per-page constant.
