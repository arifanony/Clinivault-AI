# Engineering Decision: Initial MVP Clinical Scope — Frozen Type 2 Diabetes Boundary

## Status

Chosen

## Date

2026-09-08

## Problem

DECISION-003 fixed the MVP domain as Type 2 Diabetes, but a domain alone is
still a wide space. "Type 2 Diabetes" covers pediatric diabetes, pregnancy,
emergencies, individual diagnosis, and dozens of adjacent topics. Without a
frozen clinical scope inside the domain, the corpus curation, the question set,
and the evaluation have no clear evidence boundary — the same drift problem
that killed the original general-corpus plan (see DECISION-004), just one
level down.

Before curation and evaluation work goes further, we need to write down exactly
which clinical questions the initial MVP covers and which it deliberately does
not.

## What This Part of the System Does

This decision doesn't add a component. It freezes the working clinical boundary
for the initial MVP — the scope that corpus selection, retrieval evaluation,
and answer behavior all work backwards from.

### In scope — the initial question families

The initial MVP answers clinical evidence questions in these five families:

1. **Diagnosis and classification** — clinical definitions, diagnostic
   criteria, and classification-related questions.
2. **Glycemic management** — general glycemic targets, monitoring concepts,
   and management considerations.
3. **Pharmacological treatment** — medication classes, treatment selection
   considerations, and supporting clinical evidence.
4. **Cardiovascular and kidney considerations** — questions involving Type 2
   Diabetes together with cardiovascular or kidney-related clinical
   considerations.
5. **Evidence comparison and synthesis** — questions that require comparing or
   synthesizing information from multiple evidence sources.

### Out of scope — explicitly excluded from the initial MVP

- Type 1 Diabetes
- Gestational Diabetes
- Pediatric diabetes
- Individual patient diagnosis
- Personalized treatment prescriptions
- Emergency medical decision-making
- General healthcare questions unrelated to Type 2 Diabetes

### What "in scope" means in practice

A question is in scope when it is a Type 2 Diabetes clinical evidence question
inside one of the five families above, answerable from the curated corpus. The
out-of-scope list is a hard boundary for the initial MVP, not a set of
suggestions: questions on that list are outside the evidence boundary even if
the system could technically produce an answer.

## Requirements

- A single, written clinical boundary that corpus selection, evaluation, and
  future scope discussions can all point at
- Enough clinical complexity inside the boundary to exercise the RAG pipeline
  meaningfully (guidelines, research evidence, evolving recommendations)
- A boundary narrow enough that document curation, retrieval analysis, and
  evaluation stay controllable and understandable
- An explicit out-of-scope list, so "is this in scope?" is answerable by
  reading a document rather than relitigating a discussion

## Options We Considered

- **Option A — Broader healthcare document collection** (the original idea):
  start wide, cover many conditions, narrow later.
- **Option B — Type 2 Diabetes domain with an unfrozen internal scope**:
  keep the domain (per DECISION-003) but decide question-by-question what
  counts as in scope.
- **Option C — Type 2 Diabetes domain with a frozen clinical scope** (the five
  question families and an explicit out-of-scope list, written down now).

## Comparison

| Criterion | A: Broad corpus | B: T2D, scope undecided | C: T2D, frozen scope |
|---|---|---|---|
| Document curation effort | Very high, shallow result | High, drifting | Focused, deep |
| Clear evidence boundary | No | No — decided case by case | Yes, written down |
| Retrieval quality measurable early | Hardly | Partially | Yes |
| Evaluation controllable | No | Hard | Yes |
| Risk of silent scope creep | High | High | Low |

## Decision

Freeze the initial MVP clinical scope to **Type 2 Diabetes clinical evidence
and information**, organized around the five question families listed above,
with the explicit out-of-scope list as a hard boundary. This is the current
working clinical scope decision for the MVP.

## Why We Chose It

The initial idea was a broader healthcare document collection. Before
implementation, we reconsidered: a broad corpus would make document curation,
retrieval analysis, and evaluation difficult to control and understand. We
would be collecting documents we can't justify, retrieving against questions we
haven't defined, and evaluating answers without a clear evidence boundary.

A focused Type 2 Diabetes domain provides enough clinical complexity and
multiple evidence types — clinical guidelines, systematic reviews, research
papers, evolving and sometimes conflicting recommendations — while keeping the
first MVP manageable. The five question families are wide enough to exercise
everything the RAG pipeline needs to prove (definitions, targets, treatment
evidence, comorbidity reasoning, multi-source synthesis) and narrow enough that
every question in scope maps to evidence we can actually curate and verify.

## Trade-offs

- **A deliberately small answer surface.** Many legitimate healthcare questions
  are out of scope for now, even ones the system could technically answer.
- **Some T2D questions are also excluded.** Type 1, gestational, and pediatric
  diabetes are real clinical topics adjacent to the domain, and they are out of
  bounds for the initial MVP.
- **Discipline required.** The out-of-scope list only works if we hold the
  line when a tempting question falls just outside it.

## What We Did Not Choose

- **Option A (broad corpus)** — the original idea. Rejected because a broad
  corpus defeats the point of curation and makes retrieval and evaluation
  unmeasurable. This reasoning is documented in detail in DECISION-004.
- **Option B (unfrozen internal scope)** — keeps the domain but leaves the
  boundary undefined, which recreates the drift problem inside T2D: every new
  document or question becomes its own negotiation, and the evidence boundary
  never stabilizes enough to evaluate against.

## Assumptions

- The five question families cover the T2D clinical ground needed to
  demonstrate the RAG pipeline end to end.
- Enough publicly available, legally usable evidence exists for these families
  to build a curated corpus (the corpus manifest will prove this).
- The frozen scope constrains product behavior and curation, not the
  architecture: ingestion, retrieval, and generation remain domain-agnostic.

## How We Will Validate This

- Corpus selection: every curated document maps to at least one of the five
  question families, and no document is in the corpus for out-of-scope topics.
- Evaluation: the retrieval and answer evaluation question set stays inside the
  five families, so results are interpretable against a clear evidence boundary.
- Behavior: questions on the out-of-scope list are treated as out of scope, not
  answered by drifting outside the curated corpus.

## When We Should Revisit It

This scope is intentionally a starting boundary, **not a permanent product
limitation**. Expansion should be based on evidence from the MVP — measured
weaknesses, demonstrated capability, real demand — rather than assumed upfront.
Concretely, revisit when:

- The MVP pattern works end to end and a specific new question family or domain
  is justified by evidence rather than enthusiasm. Expansion is an *addition*
  (new corpus + metadata + a new decision document), not a silent widening of
  this one.
- MVP evaluation shows the frozen families are too narrow to prove the pipeline
  (e.g., a needed evidence type can't be represented inside them).
- The out-of-scope list starts generating repeated, concrete product demand —
  that is evidence, and it should be handled with a new decision.

## Related Documents

- [DECISION-003: Product direction](./DECISION-003-product-direction.md) — why Type 2 Diabetes is the domain
- [DECISION-004: Corpus strategy](./DECISION-004-corpus-strategy.md) — why the corpus is question-driven
- [Corpus selection guide](../corpus/corpus-selection-guide.md) — how documents are chosen against this scope
- [Corpus README](../corpus/README.md) — staged corpus strategy



