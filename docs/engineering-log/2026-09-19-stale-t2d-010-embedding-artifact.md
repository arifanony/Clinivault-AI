# 2026-09-19 — Regenerating a downstream artifact from an uncommitted upstream parse: the committed T2D-010 chunk/embedding pair is inconsistent

## Category

Artifact/durability integrity (no source-code change made in this log). Discovered
while auditing documentation coverage; re-verified against the filesystem and Git.

## Discovery

`b705d60` ("record controlled retrieval benchmark measured results + regenerate
stale T2D-010 embeddings") rewrote
`data/embedded/stage-1-clean-baseline-corpus/T2D-010/T2D-010.embeddings.json`
from 71 to 70 records and recorded the results in
`docs/pipelines/retrieval-baseline-benchmark-results.md`. The recorded rationale
was that the committed embedding artifact was stale relative to the current
reader because commit `896c7af` ("guard table internal gutter candidates")
eliminated a spurious fragmented table-cell chunk `T2D-010-p011-c005`.

Re-verification of the committed state (`b705d60` = HEAD) does **not** support
that rationale, and shows the committed parsed/embedded pair is inconsistent.

### OBSERVED — the committed parsed artifact is current and yields 71 chunks

- `data/parsed/stage-1-clean-baseline-corpus/T2D-010/T2D-010.parsed.json` at
  `HEAD` is byte-identical to re-extraction with the committed reader (`HEAD`
  version of `src/clinivault_ai/chunking/reader.py`) on **15 of 15 pages**.
- Chunking it yields **71 chunks**, including `T2D-010-p011-c005` (116 chars).
- The pre-guard reader (`ce168df`) produces byte-identical page-11 text, so
  `896c7af` did not change T2D-010 page 11 at all. The fragment is present under
  every committed reader version tested.

### OBSERVED — `p011-c005` is a chunker size-boundary fragment, not a table artifact

- The committed page-11 text is 6932 chars. The chunker's pieces for that page are
  `[1770, 1627, 1663, 1752, 116]`.
- The 116-char tail is the end of page 11's body text:
  `"(156), in a prospective 12-week open-label trial of 13 individuals on dialysis
  who had been denied transplant due to"` — it continues the sentence ending
  `"...Vanek et al."` in `p011-c004` (page 12 continues the sentence).
- It is shorter than the chunker's `min_chars` (200), but the merge rule cannot
  absorb it: `1752 + 2 + 116 = 1870 > max_chars (1800)`. So the baseline chunker
  legitimately emits it as a separate chunk.
- Therefore the working description "a spurious fragmented table-cell chunk
  removed by the table-internal gutter guard" is **not** what the repository
  shows. (INFERENCE: the fragment appears/disappears with page-text length because
  the chunker's max-char boundary lands differently.)

### OBSERVED — the committed embedding artifact matches the *working tree* parse, not the committed one

- The committed `T2D-010.embeddings.json` has **70 records** (no `p011-c005`).
- Re-embedding the committed parsed artifact's chunk texts (hash provider) matches
  the committed vectors for only **37 / 70** records.
- Re-embedding the **working-tree** parsed artifact's chunk texts matches the
  committed vectors for **70 / 70** records, exactly.
- The working-tree parsed artifact is *modified and uncommitted*; it equals the
  output of the uncommitted reader change (`_upright_words`, which drops rotated
  text) — page 11: 6798 chars, pieces `[1770, 1627, 1652, 1746]`, 4 chunks, with
  the 116-char tail living inside `T2D-010-p011-c004`.
- The rotated text being dropped is real and page-wide: **all 15 committed
  T2D-010 pages** contain the rotated access footer
  ("Downloaded … from diabetesjournals.org/… by guest on 08 September 2026"),
  and page 1 also contains reversed spine-banner fragments (`NEMEGANAM`,
  `KSIR`, `YENDIK`, `CINORHC`).

### OBSERVED — the committed pair fails the fail-loud invariant

- `VectorStore.from_artifacts(<committed embeddings>, chunk_pages(<committed
  parsed artifact>))` raises
  `RetrievalError: chunk T2D-010-p011-c005 has no embedding record`.
- `python -m clinivault_ai.evaluation.benchmark` reads exactly these canonical
  files (`src/clinivault_ai/evaluation/benchmark.py`: `data/parsed/…` +
  `data/embedded/…`), so the recorded 21-case results depend on the uncommitted
  working-tree parsed artifact.
- Control: at `b705d60^` (`6bb2754`) the pair **was** consistent — the committed
  71-record embedding artifact reproduced 71/71 from the committed parsed
  artifact.
- Control: the other eight documents are unaffected — committed embeddings
  reproduce from their parsed artifacts (107/107, 34/34, 44/44, 84/84, 142/142,
  38/38, 66/66, 142/142) and all nine documents build a `VectorStore` in the
  current working tree.

## What was ruled out (OBSERVED)

- **Not corruption or truncation:** every file is valid JSON with correct
  `document_id`, dimensions (256), and model metadata; no records were dropped
  silently — the mismatch raised loudly.
- **Not a reader regression on T2D-010:** the committed parsed artifact is
  reproducible from the committed reader, page for page.
- **Not a benchmark-definition change:** `cases.py`, `metrics.py`, and the frozen
  labels are untouched; the recorded aggregates (8/21, 16/21, 0.5095) are the same
  in both records.

## Root cause / mechanism

A downstream artifact was regenerated against an **uncommitted** upstream state
(the in-progress rotated-text reader change), and only the downstream artifact was
committed. The embedding artifact stores model metadata and statistics but **no
fingerprint of the upstream parsed/chunk artifact** (no reader version, no chunk
hash), so the committed tree contains two individually valid artifacts that do not
belong together — a state that passes an "artifact exists at the canonical path"
check and fails only under recomputation or a vector-store build.

## Classification

- **OBSERVED:** every count/vector/page comparison above; the `RetrievalError`;
  the dependency of the recorded benchmark on the working-tree parsed artifact.
- **INFERENCE:** the fragment's appearance/disappearance is driven by the
  chunker's `max_chars` boundary interacting with page-text length; the reader's
  rotated-text handling (uncommitted) is what changes that length.
- **NOT YET VALIDATED:** whether the remediation accepts the rotated-text filter
  as-is; what the benchmark aggregate will be from the resulting committed state;
  whether other documents contain rotated text whose chunk sets will change when
  the filter is committed.

## Impact

- `docs/pipelines/retrieval-baseline-benchmark-results.md` §"Artifact changes made
  in this run" attributed the fragment removal to `896c7af`; that attribution is
  not supported by the repository and is corrected by a cross-reference to this
  log. The measured numbers themselves are unchanged.
- At `b705d60`, the committed T2D-010 corpus state is internally inconsistent
  until the upstream parsed artifact (and reader change) are committed together.
- Documentation elsewhere that quoted "71 records" for T2D-010
  (`t2d-010-ingestion-quality-investigation.md` §2) is stale as of `b705d60`.

## Action

- Recorded; **no artifact, parser, or retrieval change was made in this unit.**
- The uncommitted remediation work (reader change, regenerated T2D-010 parsed and
  validation artifacts, reader tests) was left exactly as found.
- Follow-up owned by that remediation unit: commit the upstream parsed artifact
  together with the reader change, then re-run
  `python -m clinivault_ai.evaluation.benchmark` and re-record the results if any
  aggregate moves.
- Candidate future unit (NOT IMPLEMENTED): store an upstream fingerprint in
  downstream artifacts and add a staleness check — see
  [DECISION-008](../decisions/DECISION-008-artifact-storage-contract.md).

## Evidence (exact paths used)

- `data/parsed/stage-1-clean-baseline-corpus/T2D-010/T2D-010.parsed.json`
  (`HEAD` + working tree)
- `data/parsed/stage-1-clean-baseline-corpus/T2D-010/T2D-010.validation.json`
- `data/embedded/stage-1-clean-baseline-corpus/T2D-010/T2D-010.embeddings.json`
  (`HEAD`, `b705d60^`, working tree)
- `data/raw/stage-1-clean-baseline-corpus/T2D-010-ada-2026-soc-11-ckd.pdf`
- `src/clinivault_ai/chunking/reader.py` (`HEAD` and working tree),
  `src/clinivault_ai/chunking/chunker.py`,
  `src/clinivault_ai/evaluation/benchmark.py`
- Temporary probe scripts (`_audit_probe*.py`, repo root) were used for the
  comparisons and **deleted**; they were never committed.

## Related documents / commits

- [DECISION-008: artifact storage contract](../decisions/DECISION-008-artifact-storage-contract.md)
- [DECISION-010: retain the baseline retrieval representation](../decisions/DECISION-010-retain-baseline-retrieval.md)
- `docs/pipelines/retrieval-baseline-benchmark-results.md`,
  `docs/pipelines/artifact-persistence.md`, `docs/architecture/artifact-storage.md`
- [2026-09-16 — T2D-010 multi-column extraction interleaving](./2026-09-16-t2d-010-column-interleaving.md)
- Commits `6bb2754`, `8ce9420`, `896c7af`, `ce168df`, `6307999`, `b705d60`.