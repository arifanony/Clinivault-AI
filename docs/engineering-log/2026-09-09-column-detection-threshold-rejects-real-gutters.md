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
