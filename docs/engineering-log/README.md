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

