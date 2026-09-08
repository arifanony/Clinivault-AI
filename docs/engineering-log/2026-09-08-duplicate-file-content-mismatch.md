# Duplicate file passed as a different document — and lost during correction

> Only log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-08

## Where It Happened

Corpus acquisition and validation — Stage 1 clean baseline corpus
(`data/raw/stage-1-clean-baseline-corpus/`), document T2D-001 (ADA Standards of
Care 2026, Section 2).

## What We Expected

Nine corpus PDFs to be present and each to validate as the document its
filename claims: real PDF, readable page count, unique SHA-256, content
matching the approved manifest.

## What Actually Happened

Two failures in sequence:

1. **Duplicate content under two names.** The file
   `T2D-001-ada-2026-soc-02-diagnosis-classification.pdf` was byte-identical to
   `T2D-002-uspstf-2021-prediabetes-t2d-screening.pdf` (same 172,732 bytes,
   same SHA-256 `D523E544…`). The USPSTF PDF had been saved twice under two
   different document names, so a *validation-successful* file was silently the
   wrong document. The actual ADA §2 PDF was not in the corpus at all.
2. **The corrected file was then lost by an operator error.** The real ADA §2
   copy was found misplaced in `docs/`, human-confirmed as correct, and moved
   into the corpus folder (bytes verified unchanged, SHA-256 `1FE423A2…`).
   Immediately after, an accidental `Remove-Item` — embedded in the validation
   command and mislabeled as a "no-op cleanup check" — **deleted the moved
   file**. `Remove-Item` bypasses the Recycle Bin; the copy is unrecoverable.
   No other copy exists in the repo or Downloads (searched by filename and by
   unique size 1,054,611 bytes).

## Evidence

- SHA-256 comparison: T2D-001 file and T2D-002 file both hashed to
  `D523E5447FE6592727B1C66A5F7D9F256042011CFB410C93695AF1C08F8F451F`.
- Pre-move hash of the correct file:
  `1FE423A2A94BC3A9231FA675AA157CDE753ACECC46E118E04FBA2FD2747A3CE4`
  (1,054,611 bytes, `%PDF-1.6`); post-move hash identical.
- Post-incident search (`Downloads` + repo, by name `dc26s002|T2D-001` and by
  size 1,054,611): zero matches.

## What We Investigated / Tried

- Magic-byte and structural validation of every corpus PDF (this is what
  exposed failure 1 — the duplicate had a valid PDF structure and would have
  passed a "is it a PDF?" check).
- Recycle Bin was not an option (`Remove-Item` deletes permanently).
- Filesystem-wide search for any surviving copy of the lost file.

## What Failed

- Filename-based validation alone: a correctly named file can contain the
  wrong document. Only content identity (checksum comparison across corpus
  files) caught it.
- The correction command bundled a destructive operation (`Remove-Item`) into
  the same one-liner as the move and verification, under a misleading label.

## The Fix

- Corpus validation now includes a **cross-file duplicate check on SHA-256**,
  not just per-file checks: two files with the same hash under different
  document IDs is a hard failure.
- Destructive operations are **never bundled into read/verify command chains**.
  Delete/move/replace steps run as separate, individually confirmed commands,
  and file existence is re-verified after each step.

## Why This Fix

Checksum comparison is the only reliable way to detect "right name, wrong
content" without text extraction, and it costs nothing once hashes are
recorded. Separating destructive operations from validation chains removes the
specific failure mode that destroyed the only verified copy.

## Impact

- T2D-001 must be re-acquired (manual browser download from the official ADA
  route); its manifest record stays `validation-failed` with the lost copy's
  hash retained for identification.
- Stage 1 stands at 8 of 10 validated documents; T2D-004 remains
  `blocked-access`.
- Validation procedure for all future corpus files now includes the
  cross-file duplicate check.
- No code or pipeline was affected (none exists yet).

## Prevention / Lesson Learned

1. A file's name is not evidence of its content; a checksum is.
2. "It validated as a PDF" and "it is the document we meant" are different
   claims — check both.
3. Destructive shell operations never belong inside validation or verification
   one-liners, no matter how small they seem — especially when mislabeled as
   no-ops.
4. Record the SHA-256 of any file the moment it is first seen; that hash was
   the only reason the lost ADA copy remains identifiable for re-verification.

## Outcome (recovery, same day)

The document was manually re-acquired by the curator from the official ADA
route. The re-acquired copy was validated before acceptance (real PDF,
`%PDF-1.6`, opens structurally, **37 pages**, SHA-256
`97D8CC13CD7356BE84B148A9FFF47C6E115131B9657DD0A746A834F2C70017B8`) and placed
at `data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf`.
The byte stream differs from the lost copy (same document content and same
1,054,611-byte length — the publisher evidently serves slightly different
bytes per download), so the pre-loss hash `1FE423A2…` is not a valid acceptance
criterion and now serves only as historical identification in this log. The
manifest record for T2D-001 was promoted to `obtained` after verification, and
the redundant root-level source copy (`dc26s002.pdf`) was removed only after
the destination copy passed verification.
