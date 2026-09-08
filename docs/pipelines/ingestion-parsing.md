# Pipeline: Ingestion — PDF Parsing to Structured Page Data

Status: **implemented** (first document T2D-001 ingested; remaining Stage-1
documents not yet processed).

## 1. What problem does this pipeline solve?

Turn one validated raw PDF into structured, provenance-preserving parsed page
data — the input every later stage (chunking, retrieval, citations) will build
on — while guaranteeing every page stays traceable to
`document_id + filename + page_number`.

Governed by [DECISION-006: PDF parser](../decisions/DECISION-006-pdf-parser.md)
(pdfplumber; pypdf for structural validation only) and run under the Python
3.14 runtime contract ([DECISION-002](../decisions/DECISION-002-python-version.md)).

## 2. What goes in?

- One validated raw PDF from `data/raw/stage-1-clean-baseline-corpus/`
- Its recorded facts from the corpus manifest: expected SHA-256 and page count
  (passed explicitly — the manifest is the source of truth, the pipeline does
  not scrape it)

## 3. What happens, step by step?

```
INPUT (one raw PDF + expected SHA-256 + expected page count)
  ↓
[1. Source verification] (ingestion/source.py)
   file exists → SHA-256 matches manifest → PDF opens (pypdf) →
   not encrypted → page count matches manifest → raw PDF metadata captured
   Hard failure here aborts ingestion; the raw file is never touched.
  ↓
[2. Page-level parsing] (ingestion/parsing.py, pdfplumber per DECISION-006)
   every page → text extraction → per-page record; per-page exceptions are
   captured as extraction_status="failed" (never silently dropped)
  ↓
[3. Page-level structured representation]
   {document_id, filename, page_number, text, text_sha256, char_count,
    word_count, page_width, page_height, extraction_status, extraction_error}
  ↓
[4. Ingestion validation] (ingestion/validation.py)
   mechanical checks only: page count, provenance completeness, document
   text present, extraction failures, empty pages, control-char anomalies,
   low-text report. Statistics are observed and reported — no invented
   acceptance thresholds.
  ↓
[5. JSON serialization] (ingestion/output.py)
   <DOC-ID>.parsed.json + <DOC-ID>.validation.json; semantic reload-
   equivalence check (reload == in-memory object; never byte comparison)
OUTPUT
```

Usage:

```
python -m clinivault_ai.ingestion <pdf> --document-id T2D-001 \
    --expected-sha256 <manifest sha> --expected-pages 23 \
    --output-dir data/parsed/stage-1-clean-baseline-corpus/T2D-001
```

## 4. What comes out?

`data/parsed/stage-1-clean-baseline-corpus/<DOC-ID>/`:

- `<DOC-ID>.parsed.json` — provenance header (document_id, source filename,
  source SHA-256, page count, parser name+version, raw PDF metadata,
  extraction timestamp UTC, pipeline version) + the pages array
- `<DOC-ID>.validation.json` — per-check results, observed statistics,
  overall status (`pass` / `pass_with_warnings` / `fail`)

## 5. Which components are involved?

`src/clinivault_ai/ingestion/`: `source.py` (verification), `parsing.py`
(pdfplumber extraction), `validation.py` (checks + statistics),
`output.py` (serialization), `__init__.py` (orchestration + CLI),
`errors.py`. Deliberately no deeper abstraction.

## 6. Which metadata is created or preserved?

Document level: document_id, source filename, source SHA-256, page count,
parser name+version, raw PDF metadata (title/author/creator/producer/dates —
recorded, never trusted), extraction timestamp (UTC), pipeline version.
Page level: document_id + filename + page_number (the traceability triad),
text, text_sha256, char/word counts, page dimensions, extraction status.

## 7. What can fail?

- Source missing / SHA-256 mismatch / page-count mismatch → hard abort
- Encrypted PDF → hard abort
- Unopenable (corrupt) PDF → hard abort
- Per-page extraction exception → page kept with status `failed` + error text
- Page with no text layer (scan) → status `empty`, page kept
- Encoding garbage → control-character ratio reported per page

## 8. How do we detect failure?

Every check above writes a machine-readable result into
`<DOC-ID>.validation.json` with an explicit status; the CLI exits non-zero on
hard failures. Nothing is dropped silently — the empty-pages and failed-pages
lists exist precisely to make absence visible.

## 9. What evidence or logs does it produce?

The validation JSON is the evidence: check-by-check status plus observed
statistics (total chars/words, per-page distributions, anomaly lists). See
`data/parsed/stage-1-clean-baseline-corpus/T2D-001/T2D-001.validation.json`.

## 10. What consumes the output next?

Chunking (not built yet). Every chunk will be traceable through
`(document_id, page_number)` back to the raw PDF via the corpus manifest.

## Observed behavior — first real run (T2D-001, 2026-09-08)

- 23 pages parsed (all `ok`), 0 empty, 0 failed, 0 control-char anomalies.
- 158,398 chars / 23,224 words total; mean 6,886.9 chars & 1,009.7 words per
  page; min page 4,046 chars (p1, cover page), max 9,669 (p20, references).
- Validation: `pass` on all checks; JSON reload-equivalence confirmed.
- **Reading order is a real, observed limitation** (as predicted in
  DECISION-006): multi-column pages extract with columns interleaved line by
  line (clearly visible on p2, p12, and the three-column references on p23).
  The cover page (p1) interleaves title/credit blocks. Text content itself
  extracts completely and cleanly (no encoding garbage; characters such as
  "≥" and "—" survive correctly in UTF-8 JSON).
- No acceptance thresholds were invented beyond the structural checks; the
  observed distribution (4,046–9,669 chars/page, no outliers) gives us a
  baseline to compare future documents against.

## Related decisions

- [DECISION-006: PDF parser](../decisions/DECISION-006-pdf-parser.md)
- [DECISION-002: Python version](../decisions/DECISION-002-python-version.md)

## Known limitations

- Reading order on multi-column layouts is not corrected (accepted for now;
  revisit if it damages retrieval quality later).
- No cleaning/normalization — parser output is passed through as-is by design.
- Only T2D-001 ingested so far; the other 8 Stage-1 documents follow in the
  next phase, each re-verified against its manifest facts.
- Page counts previously recorded in the corpus manifest from an ad-hoc
  regex counter were wrong for several ADA PDFs (over-counted from stale page
  objects in object streams); corrected to parser-based counts on 2026-09-08
  (see engineering log).


