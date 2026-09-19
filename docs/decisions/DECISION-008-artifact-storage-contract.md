# Engineering Decision: Artifact Storage — Canonical Durable Paths and Regeneration

## Status

Chosen (retroactively documented). The path contract was established on
2026-09-16; the regeneration rule was extended after the T2D-010 stale-artifact
finding of 2026-09-19.

## Date

2026-09-16 (contract committed in `8ce9420`, corrected in `6307999`,
artifacts persisted in `6bb2754`). Refined 2026-09-19 (`b705d60` and the audit
re-verification recorded in
[the stale-artifact engineering log](../engineering-log/2026-09-19-stale-t2d-010-embedding-artifact.md)).

## Problem

The corpus validation units computed chunking and embeddings **in memory** and
never wrote them down. The artifact audit of 2026-09-16 (`8ce9420`; see
[artifact-storage.md](../architecture/artifact-storage.md) and
[artifact-persistence.md](../pipelines/artifact-persistence.md)) found that only
`T2D-001.embeddings.json` existed durably, that T2D-002 had never been parsed to
disk at all, and that nothing in the repository fixed **where** a pipeline
artifact must live, **which corpus generation** it belongs to, or **what counts
as persisted**. Without that, measured validation results cannot be reproduced
from the repository, and artifacts from different corpus generations can collide.

A second problem surfaced on 2026-09-19: an artifact can exist at the canonical
path and still be internally inconsistent with the upstream artifact it was
derived from.

## What This Part of the System Does

Not a runtime component. It fixes the repository's storage rules for every
pipeline stage:

```
data/<stage>/<corpus-version>/<document-id>/
   e.g. data/embedded/stage-1-clean-baseline-corpus/T2D-005/T2D-005.embeddings.json
```

- One directory per stage, corpus generation, and document — no mixing.
- Durable = written to the canonical path **and** committed (verified from the
  filesystem and Git, never inferred from tooling output).
- Temporary artifacts (probe scripts, trace dumps, scratch JSON) live outside
  `data/`, are never committed, and are deleted after the unit — and any report
  that relied on them must say so.
- Evaluation/benchmark outputs persist nothing by default and must never be
  written into `data/parsed/` or `data/embedded/`.
- No secrets, API keys, `.env` contents, or credentials in any data artifact.

## Requirements

- Every meaningful report states the exact artifact paths it used and whether
  each was read from the canonical location or generated in memory.
- Provenance (document → page → chunk → embedding) survives persistence.
- A downstream stage may only run after the upstream durable artifact exists at
  its canonical path.
- A downstream artifact whose input changed must be **regenerated** with the
  existing pipeline functions — never patched, hand-edited, or partly committed.
- Corpus-version naming prevents collisions between corpus generations.

## Options We Considered

- **Option A — canonical `data/<stage>/<corpus-version>/<document-id>/` layout
  with explicit durability rules (chosen).**
- **Option B — ad-hoc output locations** (repo-root dumps, temp directories,
  one-off generator scripts writing wherever convenient): the state the audit
  actually found; produced publishing inconsistencies.
- **Option C — treat in-memory results as durable** (report the numbers, keep no
  artifact): also the state the audit found; makes every downstream claim
  unverifiable.
- **Option D — flat `data/<document-id>/<stage>.json`, no corpus version**:
  simpler paths, but different corpus generations would silently overwrite each
  other.

## Comparison

| Criterion | A | B | C | D |
|---|---|---|---|---|
| Claims reproducible from the repo | Yes | No | No | Partly |
| Corpus-generation isolation | Yes | No | n/a | No |
| Filesystem/Git verifiable | Yes | No | No | Yes |
| Risk of silent overwrite | None | High | n/a | High |

## Decision

Option A. Pipeline artifacts live only at
`data/<stage>/<corpus-version>/<document-id>/`; durability means committed;
temporary artifacts are labeled and deleted; evaluation runs write nothing into
the parsed/embedded stages; and a downstream artifact is regenerated with the
existing unchanged pipeline functions when its upstream input changes, then
committed **together with** the upstream artifact it was derived from.

## Why We Chose It

- The baseline provider is deterministic, so regeneration is not a risk: the
  durability unit re-embedded T2D-001 from its committed parsed artifact and
  reproduced the committed `T2D-001.embeddings.json` **bit-for-bit**
  (`artifact-persistence.md` §F).
- The fail-loud retrieval invariant already refuses mismatched pairs
  (`VectorStore.from_artifacts` raises `RetrievalError` instead of silently
  dropping records), so a regenerated artifact cannot quietly diverge — the
  T2D-010 case proved this works (it raised).
- Committing the artifacts makes every recorded benchmark and validation claim
  reproducible offline with no network and no API cost.

## Trade-offs Accepted

- Large JSON artifacts are committed to Git (accepted at the current
  9-document, ~600-chunk scale; would need revisiting as the corpus grows).
- The rules are enforced by review and by the standing repository rules, not by
  tooling: there is **no automated staleness or fingerprint check**.
- Downstream artifacts carry no upstream fingerprint (no reader/parser version,
  no upstream artifact hash), so a stale pair is detectable only by
  recomputation.

## What We Did Not Choose

- **B and C** — they are exactly what produced the 2026-09-16 durability gap.
- **D** — corpus-version collision risk.
- **Storing embeddings in a database instead of Git-committed JSON** — no scale
  requirement exists yet; vector storage is still an open future decision
  (see [DECISION-009](./DECISION-009-retrieval-baseline-representation.md)).

## Evidence

- Commits `8ce9420` (contract), `6bb2754` (artifacts persisted), `6307999`
  (corrections), `b705d60` (T2D-010 regeneration + recorded results).
- `docs/architecture/artifact-storage.md` — the normative contract (§B–§I) and
  the per-document state snapshot (§J).
- `docs/pipelines/artifact-persistence.md` — the durability unit's inventory,
  verification, and bit-for-bit reproducibility evidence.
- Audit re-verification 2026-09-19: all nine documents' committed embedding
  artifacts reproduce from their parsed artifacts (107/107, 34/34, 44/44, 84/84,
  142/142, 38/38, 66/66, 142/142) **except** T2D-010, whose committed pair is
  inconsistent at `b705d60` (71 committed chunks vs 70 committed records) — see
  the engineering log linked above. OBSERVED, reproducible.

## How We Will Validate This

- Build a `VectorStore` from the canonical committed artifacts for every
  document; any mismatch must raise, not drop records.
- Regeneration must reproduce committed vectors exactly for the hash provider.
- Reports must name their artifact paths.

## When We Should Revisit It

- If corpus size makes Git-committed artifacts impractical.
- If a downstream artifact must be regenerated and the regenerated upstream
  artifact cannot be committed in the same change (proof that the process rule
  is insufficient).
- When an automated "artifact matches its upstream" check is introduced.

## Consequences and Open Follow-up (NOT YET IMPLEMENTED)

- The current rules verify that an upstream artifact **exists**; the T2D-010
  audit showed existence is not sufficient — content identity matters. A
  fingerprint/hash of the upstream chunk output stored in the downstream
  artifact (plus a staleness check) is a **candidate future unit**, not a
  current capability.
- Committing a downstream artifact regenerated from an uncommitted upstream
  state leaves the committed tree inconsistent even though every individual file
  is a valid artifact — the process rule above exists to prevent this.

## Related Documents

- [artifact-storage.md](../architecture/artifact-storage.md) — the normative contract.
- [artifact-persistence.md](../pipelines/artifact-persistence.md) — durability unit.
- [DECISION-001: repository architecture](./DECISION-001-repository-architecture.md) — stage boundaries and contracts.
- [DECISION-009: baseline retrieval representation](./DECISION-009-retrieval-baseline-representation.md) — the retrieval stage that consumes the embedding artifact.
- [Engineering log: stale T2D-010 embedding artifact](../engineering-log/2026-09-19-stale-t2d-010-embedding-artifact.md).

## Related Commits

`8ce9420`, `6bb2754`, `6307999`, `b705d60`.