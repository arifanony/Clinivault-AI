# Clinivault AI — Current AI Handoff

> **Safe transition artifact.** This document contains no `.env` content, API
> keys, tokens, passwords, credentials, or machine-specific secrets. Treat live
> Git and Genesis commands as canonical when resuming; this handoff records the
> verified state immediately before the handoff-document completion commit.

## Repository State

- **Current project:** Clinivault AI
- **Branch:** `master`
- **Verified pre-handoff commit:**
  `f955e23e66a01b2cbb6ff420a94879bded30186b`
  (`docs: decide retrieval representation direction`)
- **Verified pre-handoff remote synchronization:** `HEAD` equaled
  `origin/master` at `f955e23e66a01b2cbb6ff420a94879bded30186b`.
- **Working-tree state before this handoff task:** clean except for the
  pre-existing untracked `.env.example` protected local file. Genesis task
  activation generated the canonical `.genesis/` control-state changes for this
  bounded documentation task.
- **Intentionally ignored/protected local files:** `.env` is ignored; `.env.example`
  is protected local state, untracked, and must not be staged, committed,
  printed, copied, or deleted without explicit safe authorization. `.clinerules/`
  is local-only and ignored.

## Genesis State

- **Pre-handoff `genesis status .`:** `verify/ready`, no active task, no
  blocker.
- **Pre-handoff `genesis brief .` summary:** the project objective is to build
  a production-oriented, evidence-grounded Type 2 Diabetes healthcare RAG
  system through reproducible, evidence-driven engineering. Genesis includes
  the accepted DECISION-016 retrieval-representation record.
- **DOCS-HANDOFF-001:** completed/terminal through the official Genesis CLI.
  It created the handoff artifact and recorded a passing required test gate.
- **Active task after this handoff's completion lifecycle:** none.
- **Current phase/objective after completion:** `verify/ready`; the repository
  is waiting for explicit human authorization of the next bounded technical
  unit.
- **Blocker:** none.
- **Last completed bounded unit:** `DECISION-016-RETRIEVAL-REPRESENTATION`,
  committed and pushed as `f955e23`.
- **Ready for a new authorization:** yes, after this handoff correction is
  committed and pushed. No new technical unit is authorized by this handoff.

## Last Completed Unit

- **Unit/task:** `DECISION-016-RETRIEVAL-REPRESENTATION`
- **What was completed:** an evidence-based retrieval-representation decision
  after the frozen 46-case evaluations. DECISION-010 was marked Replaced as the
  historical 21-case outcome. DECISION-016 selected local dense semantic
  retrieval as the next separately authorized integration direction, with raw
  `intfloat/e5-small-v2` as the leading local candidate. No production retrieval
  implementation changed.
- **Important files changed:**
  - `docs/decisions/DECISION-016-retrieval-representation.md`
  - `docs/decisions/DECISION-010-retain-baseline-retrieval.md`
  - `docs/decisions/README.md`
  - `docs/engineering-log/2026-09-23-retrieval-representation-decision.md`
  - `docs/engineering-log/README.md`
  - `docs/pipelines/retrieval-controlled-comparison.md`
  - canonical Genesis control state and gate receipt under `.genesis/`
- **Tests/gates run:** `python -m unittest discover -s tests`; 215 tests ran
  and passed. Genesis recorded the task gate as passed. Markdown relative-link
  validation and `git diff --check` also passed.
- **Important measured results:**
  - Baseline hash: Hit@1 12/46, Hit@5 26/46, MRR 0.3601.
  - Raw E5-small: Hit@1 20/46, Hit@5 36/46, MRR 0.5583.
  - E5 `query:`/`passage:` format: Hit@1 19/46, Hit@5 35/46, MRR 0.5486.
  - Gemini semantic: Hit@1 21/46, Hit@5 42/46, MRR 0.6109.
- **Relevant Decision Record:**
  `docs/decisions/DECISION-016-retrieval-representation.md`
- **Relevant Engineering Log:**
  `docs/engineering-log/2026-09-23-retrieval-representation-decision.md`
- **Relevant evaluation/report:**
  `docs/pipelines/retrieval-controlled-comparison.md`,
  `docs/engineering-log/2026-09-21-multi-model-embedding-eval.md`,
  `docs/engineering-log/2026-09-22-eval-hf-002.md`, and
  `docs/engineering-log/2026-09-23-eval-hf-003.md`.

## Current Technical Understanding

### OBSERVED

- On the frozen 46-case benchmark, the measured raw E5-small result exceeds the
  baseline hash result on Hit@1, Hit@5, and MRR.
- Gemini has the highest measured aggregate results listed above, but it is a
  cloud/API-dependent provider.
- E5 intended input prefixes did not improve the frozen benchmark relative to
  the reproduced raw protocol; raw E5 vectors for T2D-001 matched the persisted
  EVAL-HF-002 artifact byte-for-byte.
- Current production retrieval remains the baseline hash representation. No
  semantic integration was implemented by DECISION-016.

### INFERENCE

- Under the current MVP offline/cost constraint, local dense semantic retrieval
  with raw E5-small is the most evidence-supported direction for a future,
  separately authorized integration unit.

### NOT YET VALIDATED

- Statistical significance or universal superiority of raw E5-small over other
  local models or E5 prefix formatting.
- Production integration behavior, packaging/runtime cost, memory profile, and
  retrieval behavior outside the frozen 46-case benchmark.
- Any change to corpus, labels, Top-K, chunking, hybrid retrieval, reranking, or
  vector storage.

## Next Authorized Action

After the handoff completion lifecycle recorded by this document:

**WAITING FOR EXPLICIT HUMAN AUTHORIZATION. DO NOT START A NEW TECHNICAL UNIT.**

## Resume Procedure

Before doing any work, run:

```text
git status --short
git log -5 --oneline
git rev-parse HEAD
git rev-parse origin/master
genesis status .
genesis brief .
```

Treat those command results as canonical. Confirm whether the handoff task has
completed and whether `HEAD == origin/master`. Then read only the project
documentation relevant to the active, explicitly authorized task before doing
work; do not reconstruct unrelated repository history.

## Important Rules

The next agent must:

- obey Genesis and its active task, scope, gates, and blockers;
- work on one bounded task at a time;
- require explicit human authorization and an active Genesis task before a new
  technical unit;
- not silently expand scope or begin the next unit automatically;
- use official Genesis CLI commands for task completion and checkpointing;
- create Engineering Logs for meaningful failures, discoveries, investigations,
  or changed understanding;
- create Decision Records for actual engineering decisions;
- never manually edit `.genesis/project.json`;
- protect `.env` and `.env.example`, and never expose or commit secrets;
- verify evidence before claiming success and distinguish OBSERVED, INFERENCE,
  and NOT YET VALIDATED;
- stop after the bounded task is complete; and
- finish the Git/Genesis lifecycle: required gates, Genesis task completion,
  Genesis checkpoint, Genesis status/brief verification, Git diff/status review,
  staged-diff review and `git diff --check`, commit, push when intended for
  sharing, and verification that `HEAD == origin/master`.