# Engineering Problem Log

Problems we hit while building that taught us something or changed an
implementation decision. Use
[`docs/templates/engineering-problem-log-template.md`](../templates/engineering-problem-log-template.md).

We log: things that broke in non-obvious ways, wrong assumptions, tools that
didn't behave as documented, issues that cost real debugging time, and anything
that changed a decision. We don't log trivial syntax mistakes or routine fixes.

## Problem Log

| Problem | Component | Date | One-line summary |
|---|---|---|---|
| [Duplicate file passed as a different document — and lost during correction](./2026-09-08-duplicate-file-content-mismatch.md) | Corpus acquisition / validation | 2026-09-08 | A USPSTF PDF sat under the T2D-001 (ADA §2) filename; the real file was found and moved, then accidentally deleted by an erroneous `Remove-Item` bundled into the validation command — corpus validation now includes cross-file SHA-256 duplicate checks and destructive ops are never bundled with verification. |
| [Ad-hoc regex page counting recorded wrong page counts](./2026-09-08-regex-page-counts-wrong.md) | Corpus validation / ingestion | 2026-09-08 | Regex-based `/Type /Page` counting over-counted ADA PDFs (stale page objects in object streams); ingestion's page-count check caught it — manifest corrected to parser-based counts. |
| [Closed PDF file runtime bug: "seek of closed file"](./2026-09-09-closed-pdf-runtime-bug.md) | Chunking / `reader.py` | 2026-09-09 | `extract_page_text_column_aware()` binds the pdfplumber page inside the open-file context but extracts words after the file closes — crash on first real use; also documents the committed `_words_to_lines` syntax corruption that had masked it. **Fixed** in `163b8ea` (extraction moved inside the open context). |
| [Column-split detection rejects the real gutters](./2026-09-09-column-detection-threshold-rejects-real-gutters.md) | Chunking / `reader.py` | 2026-09-09 | On real T2D-001 pages the largest x0 gaps (23–29 pt) all fall below the `page_width * 0.05` (≈29.7 pt) rejection rule, so two-column pages return `None` and reading order stays interleaved — the x0-gap metric never sees the actual gutter. **Addressed** by the coverage-based region detector (`18028cf`) plus table-internal gutter guarding (`896c7af`); known semantic limitations remain (e.g., the page-6 false-positive gutter ≈0.370 documented in the 2026-09-10 entry). |
| [Rows spanning multiple regions leak cross-gutter text](./2026-09-10-row-merge-cross-region-leakage.md) | Chunking / `reader.py` | 2026-09-10 | `extract_page_text_column_aware()` builds rows by rounded `top` before region assignment, so rows sharing a baseline across a gutter are assigned wholesale by row center — cross-gutter text persists (pages 6, 16); also records the page-6 false-positive gutter (≈0.370) and page-16 table separator misread as a document region (≈0.358). **Row-merge leakage fixed** in `ce168df` (region assignment at segment granularity); the page-6 false-positive gutter and page-16 table-separator semantics remain open. |

