# 2026-09-14 — The two "parametric addition" claims from the T2D-001 run were actually in the supplied evidence

## Category

Generation/grounding — a recorded finding was **revised** (no source-code change).
Discovered while building the retrieval trace and the representative evaluation
(`cde70a4`, `2292852`).

## Discovery

The 2026-09-13 generation log
(`2026-09-13-generation-parametric-additions.md`) recorded that 2 of 12
substantive claims in the first real T2D-001 Gemini answer were **model parametric
additions not present in any supplied evidence item**:

1. "Repeat testing is required to confirm the diagnosis" → cited to rank 4
   (`T2D-001-p002-c003`).
2. "One-step 75-g OGTT derived from the IADPSG criteria" → cited to rank 5
   (`T2D-001-p017-c003`).

Both claims **are** supported by the supplied chunks. Verified programmatically
against the committed T2D-001 parsed artifact:

| Phrase | Chunk | Found |
|---|---|---|
| `repeat test` | `T2D-001-p002-c003` (1760 chars) | yes, at index 1564 |
| `confirm` | `T2D-001-p002-c003` | yes, at indexes 737 and 1670 |
| `one-step` | `T2D-001-p017-c003` (1617 chars) | yes, at index 1558 |
| `75-g` | `T2D-001-p017-c003` | yes, at index 1568 |
| `IADPSG` | `T2D-001-p017-c003` | yes, at index 1595 |

Both chunks were inside the Top-5 that was actually supplied (rank 4 and rank 5,
scores 0.5680 and 0.5641). The same re-check is recorded in
`docs/pipelines/representative-evaluation.md` ("Forensic re-check result … the
original grounding inspection was wrong") and in
`docs/pipelines/retrieval-baseline.md` §"Retrieval Trace (Observability) → Why It
Was Needed".

## What was ruled out (OBSERVED)

- **Not a retrieval failure:** the supporting evidence was in the prompt at ranks
  4 and 5; the trace contract was added after this discovery precisely because
  runs had to be reconstructable in data.
- **Not an artifact change:** the phrase positions were verified against the
  committed `data/parsed/stage-1-clean-baseline-corpus/T2D-001/T2D-001.parsed.json`
  with the unchanged chunker; T2D-001's chunk set (107 chunks) is the same set the
  2026-09-13 run used.
- **Not a prompt problem:** the prompt contained the evidence verbatim; the
  failure was in the *inspection*, not in what was supplied.

## Root cause / mechanism

- **OBSERVED:** the original inspection was a manual read of long,
  table/footnote-dense chunks; the decisive phrases sit near the **end** of each
  chunk (index 1564 of 1760; indexes 1558–1595 of 1617), i.e. inside material that
  is easy to miss when reading a chunk summary rather than the exact chunk text.
- **UNCERTAIN (not established):** the repository records the misclassification
  but not the exact reading step that produced it. This log does not invent one.

## Impact

- The 2026-09-13 conclusion for these two claims is **superseded**: they are
  supported by the supplied evidence, not parametric additions. That log's general
  lesson still stands — prompt-only grounding control is *unmeasured*, and its
  "10/12 supported, 2/12 unsupported" split should not be quoted as a grounding
  measurement.
- The representative evaluation's EVAL-1 grounding re-check reports **0
  UNSUPPORTED** claims with these two re-verified.
- The discovery is the documented reason the retrieval trace (`cde70a4`) and the
  observability UI's exact-chunk-text inspection (`ee47ec9`, `4ab0652`) exist;
  without them, the same misclassification could recur.
- Grounding evaluation remains **not measured** — no labeled claim/evidence
  dataset exists; the UI grounding panel is a labeled placeholder.

## Classification

- **OBSERVED:** phrase presence, positions, and Top-5 membership; the
  representative-evaluation re-check; the trace/UI changes that followed.
- **INFERENCE:** the manual-inspection miss was caused by reading long
  footnote-dense chunks without the exact text at hand.
- **NOT YET VALIDATED:** whether prompt-only grounding permits *other* parametric
  additions (the original concern is unresolved, not disproved) — no measurement
  exists.

## Action

- Recorded; no code change in this unit.
- Cross-references added: a superseding note on the 2026-09-13 log, and links from
  [DECISION-011](../decisions/DECISION-011-grounded-generation-contract.md).

## Evidence (exact paths used)

- `data/parsed/stage-1-clean-baseline-corpus/T2D-001/T2D-001.parsed.json`
- `src/clinivault_ai/chunking/chunker.py` (unchanged; reproduces the 107-chunk
  T2D-001 chunk set)
- `docs/pipelines/representative-evaluation.md`,
  `docs/pipelines/retrieval-baseline.md`,
  `docs/pipelines/observability-ui.md` (§"T2D-001 forensic acceptance")
- Temporary probe script (`_audit_probe*.py`, repo root) used for the substring
  verification and **deleted**; never committed.

## Related documents / commits

- [2026-09-13 — Baseline generation added claims not present in retrieved evidence](./2026-09-13-generation-parametric-additions.md) (partly superseded)
- [DECISION-011: grounded generation contract](../decisions/DECISION-011-grounded-generation-contract.md)
- [2026-09-16 — EVAL-5 recorded retrieval is not reproducible](./2026-09-16-eval5-retrieval-record-not-reproducible.md) (the same programmatic checks that verify these phrases)
- Commits `cde70a4`, `cfea9e1`, `2292852`, `ee47ec9`, `4ab0652`.