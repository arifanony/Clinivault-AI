# DECISION-013: Adopt Genesis as the Repository-Native Workflow/Control Layer

- **Date:** 2026-09-19
- **Status:** Accepted
- **Decided by:** Human approval in the active engineering conversation (this unit's approval is the human's explicit approval of the read-only discovery report; no earlier approval exists).

## Decision

Adopt the official Genesis harness (genesis-kit) as the **repository-native workflow/control layer** for Clinivault AI. Genesis owns *control state* only: project objective, current phase, active/next bounded unit, task scope, executable gates, evidence receipts, approvals, checkpoints, and recovery. It does **not** replace or duplicate the authoritative engineering knowledge layer.

## Context

Clinivault AI is developed as a sequence of bounded engineering units executed by an AI agent across multiple sessions. Every unit has so far relied on the unit brief supplied in the conversation (the chat message) as the de facto control state: what the unit is, which files are in scope, what gates must pass, and when to stop.

## Problem

Repeated continuity problems were observed during long-running units:

- Active work became difficult to reconstruct after cold-session interruptions (the T2D-010 remediation session required repeated re-establish-state steps after context compaction).

## Alternatives considered

1. **Status quo (no harness).** Rejected: control state remains conversation-dependent; cold-session recovery cost was repeatedly demonstrated (T2D-010 session interruptions).
2. **Extend `.clinerules/` with a hand-maintained state file.** Rejected: purely human-enforced; no mechanical gate receipts, no tamper-evident evidence freshness, no recovery commands — recreating Genesis poorly.
3. **Full Genesis adoption including knowledge records.** Rejected: would create a second authoritative source for decisions/findings, violating the one-owner-per-information-type rule.
4. **Adopt as control layer only (chosen).** Genesis owns workflow/control state; `docs/` remains the sole owner of engineering knowledge; cross-references only.

## Rationale

Genesis is the smallest existing mechanism that mechanically closes the control-state gap: machine-enforced active unit/task, executable gates bound to runtime receipts that reject stale evidence, human-only approval commands, explicit checkpoints/recovery, and a cold-session brief. The knowledge layer (decisions, findings, results) is already comprehensive and must not be duplicated — Genesis references it rather than restating it.

## Ownership model

| Information type | Authoritative owner | Genesis role |
|---|---|---|
| Decision Records | `docs/decisions/` | None (cross-reference only; may record approval *events*, never decision content) |
| Engineering Logs | `docs/engineering-log/` | None (cross-reference only) |
| Pipeline/evaluation results | `docs/pipelines/` + `data/` artifacts (DECISION-008 contract) | None (cross-reference only) |
| Architecture | `docs/architecture/` | None |
| Project objective, phase, active/next bounded unit, task/file scope | Genesis (`project.json`/KICKOFF/PLAN) | **Owner** |
| Executable gates, evidence receipts, approvals, checkpoints, recovery | Genesis | **Owner** |
| Binding invariants / requirements | Both — binding text in Genesis brief; durable rationale in `docs/` | Reference each other |
| Assumptions | Genesis `record` (with supersession); durable outcomes promoted into `docs/` | Owner of transient assumptions |

## Consequences

- A fresh session can determine project identity, last completed milestone, current control state, next authorized unit, authoritative document locations, and required proof from the repository alone (`genesis brief`, `KICKOFF.md`).
- `.genesis/` is added to the repository; `.genesis/local/` (raw traces) is git-ignored; no secrets may ever enter Genesis state (aligns with the DECISION-008 security rule).
- The trusted executable test gate is `python -m unittest discover -s tests` (corrected from the auto-detected pytest command; pytest is NOT added as a dependency).
- Node.js (>=18) becomes a toolchain prerequisite for the workflow harness only; it is not a runtime dependency of the Python pipeline.
- Future unit briefs are grounded in `genesis brief` rather than reconstructed from chat.

## Risks / limitations

- Genesis does not guarantee working-directory sandboxing ("candidate work directories are not sandboxes"); host permissions remain the trust boundary.
- The static index is advisory, JS/TS/Python-only, and "absence from the index is not evidence of absence."
- Genesis coordinates and records execution; the coding host executes — it performs no autonomous execution.
- Recovery never auto-replays side effects; resume is explicit and human-initiated.
- Risk of agents treating `.genesis/` state as decision authority — mitigated strictly by the ownership model above.

## Related documents

- `docs/decisions/DECISION-001-repository-architecture.md` (layered design Genesis wraps)
- `docs/decisions/DECISION-008-artifact-storage-contract.md` (security/artifact rules Genesis must honor)
- `docs/templates/decision-template.md`
- Genesis official skills: `skills/genesis/SKILL.md`, `skills/ponytail/SKILL.md` (genesis-kit v2.4.0)

## Related commits

- `b3e1487` — fix: remediate t2d-010 parser extraction (last completed technical unit at decision time)
- `449efe7` — docs: complete decision and engineering log audit (knowledge-layer baseline)
- (this commit) — feat: adopt genesis workflow harness
- Decisions and findings are durable in `docs/`, but the *active* control state (current phase, next bounded action, gate status) lives only in conversation history.
- A new session, IDE, or contributor cannot mechanically determine "what was the last completed unit" and "what is authorized next" from the repository alone.

## Evidence

- Read-only Genesis discovery run (2026-09-19), actual output: 158 files detected, Python-only project, 51 Python files, 55 Markdown files, 9 PDFs, 6 PNGs, revision commit `b3e1487`, dirty=true (the preserved `.env`/`.env.example`/`TESTIMG/` untracked items), `legacy_genesis=false`. No `.genesis/` existed.
- Genesis v2.4.0, Node v24.19.0, kit from the official repository `https://github.com/ayush488-glitch/genesis-kit` (origin verified at install time).
- 11 Decision Records and 10 Engineering Logs already exist and cover the knowledge layer comprehensively (audit commit `449efe7`).
- Discovery found an executable-command mismatch: Genesis auto-detected `python -m pytest`, but the actual project test suite is `python -m unittest discover -s tests`. The pytest command must not become a trusted gate.
- Genesis `--write` was NOT executed during discovery; no project file was modified by the read-only run (verified via `git status --short` / `git diff --check`).