# Engineering Decision: Python Version

## Status

Chosen

## Date

2026-09-08

## Problem

The project needs a declared, consistently applied Python version before the
first real dependency is added. Until now the version existed only as a
placeholder in `pyproject.toml` (`requires-python = ">=3.14"`) and
`.python-version` (`3.14`), while the actual virtual environment had been
created with Python 3.13.13 — an inconsistency that surfaced the moment we
tried to add the first parser dependency.

## What This Part of the System Does

Not a component — this fixes the runtime contract for the whole project: which
Python version Clinivault is developed and run against, and what the
environment must satisfy.

## Requirements

- One declared version, applied consistently across `pyproject.toml`,
  `.python-version`, and the actual virtual environment
- Dependency installation must be reproducible (`uv` lockfile)
- The project package must import and run successfully in the declared
  environment

## Options We Considered

- **Option A — keep 3.14 as declared:** recreate the venv on Python 3.14.
- **Option B — relax `requires-python` to 3.13:** match the existing (broken)
  venv instead of fixing it.

## Comparison

| Criterion | A: keep 3.14 | B: relax to 3.13 |
|---|---|---|
| Consistency with declared project files | ✅ | ❌ requires rewriting two files to match an accident |
| Runtime support horizon | Longer | Shorter |
| Signals intent | Project chose 3.14 deliberately | Environment accident becomes policy |

## Decision

Standardize on **Python 3.14** (currently CPython 3.14.7 in the project
venv). `pyproject.toml` keeps `requires-python = ">=3.14"` and
`.python-version` keeps `3.14`. The virtual environment was recreated on
3.14.7 via `uv venv --python 3.14 --clear`, and dependencies are locked with
`uv`.

## Why We Chose It

3.14 was already the declared version in both project files; the only thing
wrong was the environment, not the declaration. Relaxing the requirement to
match an accidentally-created 3.13 venv would have promoted an accident into
policy and shortened the support horizon for no benefit. The venv was recreated
on 3.14.7, after which the project imports and runs cleanly.

## Why the Previous Environment Was Inconsistent

The `.venv` had been created (by an earlier `uv` run) with Python 3.13.13
while `pyproject.toml` already declared `>=3.14`. Nothing failed visibly
because no dependencies were installed yet — the mismatch only surfaced when
the first real dependency had to be resolved against the declared Python
requirement.

## Scope of This Decision

This is a **project-environment decision**: it states which Python version
*this project* standardizes on and develops against. It is not a claim that
other Python versions cannot run this code, and it imposes nothing on other
projects or products (including Errata).

## Trade-offs

- 3.14 is newer than many prebuilt-binary packages historically support on
  day one; pure-Python dependencies (our parser choice) avoid most of that
  risk, but binary wheels must be checked when adding compiled dependencies.
- Development machines must have Python 3.14 available via `uv` (uv can fetch
  it automatically).

## How We Will Validate This

- `.venv\Scripts\python.exe --version` reports 3.14.x
- `uv sync` / `uv add` resolve and install without version conflicts
- The project package imports and its entry point runs in the venv

## When We Should Revisit It

- If a needed dependency cannot support 3.14 and no alternative exists
- If a platform we must target (e.g., future deployment environment) cannot
  provide 3.14
- When a new Python major version is declared and the project chooses to move
  deliberately — with a new decision, not by environment drift

## Related Documents

- [DECISION-006: PDF parser](./DECISION-006-pdf-parser.md) — the first dependency chosen under this runtime contract
