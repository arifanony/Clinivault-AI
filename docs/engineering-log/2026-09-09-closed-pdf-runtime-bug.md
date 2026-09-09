# Closed PDF file runtime bug: extract_page_text_column_aware crashes with "seek of closed file"

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-09

## Where It Happened

Chunking phase, Step 1 verification of
`src/clinivault_ai/chunking/reader.py` against the real corpus document
T2D-001 (`data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf`),
checkpoint `7a5fc40`.

## What We Expected

`extract_page_text_column_aware(pdf_path, page_number)` to open the PDF, return
reading-order-corrected text for pages 2, 13, and 23, so column detection and
reading order could be validated on real pages.

## What Actually Happened

Every call to `extract_page_text_column_aware()` failed at runtime with:

```
PdfminerException: seek of closed file
```

**Observation (directly verified by execution):** the function never returned a
result on any tested page; the exception was raised as soon as word extraction
was attempted.

**Inferred root cause (code reading, consistent with the exception):** the
function opens the PDF with a context manager and binds `page` *inside* the
`with` block:

```python
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[page_number - 1]

words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
```

`page.extract_words(...)` is called *after* the `with` block has closed the
underlying file. pdfplumber pages are lazy views over the open file object;
once pdfminer closes the file, any deferred extraction on the page raises
"seek of closed file". The exception text matches this mechanism exactly, but
the fix has deliberately not been applied, so the causal chain is stated as
strongly supported inference, not as verified-by-patch.

## Evidence

- Real execution on T2D-001 (pdfplumber, venv Python): opening the PDF and
  calling `page.extract_words(...)` *inside* the open context works (word
  counts 916 / 974 / 1283 on pages 2 / 13 / 23); the identical extraction
  through `extract_page_text_column_aware()` raises `seek of closed file`.
- The only structural difference between the working and failing paths is
  whether extraction happens inside the open-file context.
- Notably, this bug was invisible until now because `reader.py` was
  syntactically invalid at the previous checkpoint (`e82a4fd`): the `def`
  prefix of `_words_to_lines` had been lost, so the module could not even be
  imported, let alone executed. The corruption was repaired in `7a5fc40`
  ("fix: restore column split detection"), which is what first made a runtime
  exercise of this function possible.

## What We Investigated / What Failed

- Direct `detect_column_split()` calls on word lists extracted manually (these
  are pure functions and work fine) — isolating the failure to the file
  lifecycle in `extract_page_text_column_aware()`, not the column logic.
- Replicating the extraction logic inline against an explicitly open
  `pdfplumber.open(...)` context — works, confirming the context-lifetime
  explanation.

## The Fix

**Not fixed in this unit (deliberate).** The repair is expected to be a
one-line restructuring: perform word extraction inside the `with` block (or
re-open the file around the page work). It is scheduled as a separate
implementation unit with its own commit, so that this documentation unit stays
code-free.

## Why This Fix (when applied)

pdfplumber objects are not independent of the file handle that produced them.
Resource lifetime and data extraction must live in the same scope; binding a
lazy object out of its context manager converts a scoping detail into a
runtime crash on first real use.

## Impact

- `extract_page_text_column_aware()` is currently unusable end-to-end: no page
  of any corpus document can be extracted through it. The function has
  therefore never been exercised against real data in its current form.
- Chunking-phase verification had to proceed by calling `detect_column_split()`
  and the internal helpers directly, replicating the extraction logic in the
  verification script. Column-split findings for the real corpus are recorded
  separately (see the column-detection entry, same date).
- No other module is affected; nothing downstream depends on this function yet.

## Prevention / Lesson Learned

1. A module that only existed as untested code carried a crash-on-first-use
   bug plus a syntax corruption — both invisible until the checkpoint was
   actually exercised. **Verify that a checkpoint is importable and runnable,
   not just that it commits.**
2. Syntax corruption can survive a commit: `e82a4fd` contained a mangled
   function definition (`(words: list[dict]) -> list[dict]:` with the `def`
   prefix lost). An AST-parse check before committing would have caught it
   immediately; a quick parse/import smoke test is now considered part of
   checkpoint hygiene.
3. Lazy I/O-backed objects must not outlive their context manager. When a
   function opens a resource, do all dependent work inside the open scope.
