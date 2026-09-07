# Engineering Decision: Corpus Strategy — Question-Driven Type 2 Diabetes Evidence

## Status

Chosen

## Date

2026-09-07

## Problem

How do we build the document corpus that Clinivault's RAG runs on?

The original working plan was broader: collect a general healthcare PDF corpus
and use it as the RAG knowledge base. The corpus plan at that time described
growing by stages toward a large collection, with the first stage focused on
gathering deliberately varied document structures to validate ingestion.

That original approach never had its own decision document. It was the default
we drifted into — "we need PDFs, so let's collect PDFs." Writing it down now,
as an honest record: it was the plan, it seemed fine at the time, and we
changed it. This document captures why.

## Why the Original Approach Seemed Reasonable Initially

- A varied corpus genuinely does stress-test parsing early — multi-column
  papers, long documents, tables. That felt like the practical first step.
- Collecting documents is concrete and visible progress, while deciding *which*
  documents feels like it can wait.
- A general healthcare corpus felt future-proof: whatever users ask, the
  knowledge base would already have something.

## What Caused Us to Reconsider

Three things, once we looked at the actual product goal instead of the
pipeline:

1. **The product goal changed the requirements.** Clinivault is an
   evidence-grounded clinical knowledge system focused on one domain (see
   DECISION-003). A general-purpose corpus doesn't serve that — most of its
   content would never be retrieved, and the parts that matter would be thin.
2. **RAG evaluation needs a coherent question set.** You can only measure
   retrieval quality, grounding, and citation correctness against questions
   you actually care about. A randomly collected corpus makes "did we retrieve
   the right evidence?" unmeasurable — there's no defined right answer.
3. **Errata will need meaningful test cases.** Old vs. new guidelines,
   conflicting evidence, evolving recommendations — these exist naturally in a
   question-driven domain corpus and barely exist in a random one.

## Alternatives We Considered

- **Keep the general healthcare corpus** — rejected: serves neither the
  product goal nor evaluation.
- **Question-driven corpus, but domain-agnostic** — considered; rejected
  because without a domain, "the questions we care about" has no boundary.
- **Two-track: a small varied parsing-test corpus AND a question-driven
  domain corpus** — considered; partially kept. Layout variety now comes in
  Stage 3 (stress and evaluation corpus) instead of Stage 1, rather than
  running in parallel from day one.

## The New Approach

- Clinivault starts with **Type 2 Diabetes** only.
- The corpus is **question-driven**: we start from the clinical questions the
  product should answer, work backwards to the required evidence, and only
  then select documents.
- Evidence sources: **authoritative clinical guidelines + curated PubMed
  research literature**.
- Start small and deliberate (Stage 1: clean baseline), expand progressively
  (Stage 2: domain evidence), and only later introduce hard cases on purpose
  (Stage 3: layout variety, old/new documents, conflicting evidence).
- Every document earns its place and gets a manifest record explaining why.

## Why the New Approach Is Better

**For Clinivault:** answers get built on genuinely relevant, trusted evidence.
Curation effort goes into documents that will actually be retrieved instead of
spread thin across everything.

**For future Errata evaluation:** a question-driven corpus makes the pipeline
measurable — retrieval quality, grounding, and citation correctness can be
judged against known questions and known evidence. Guideline versioning and
conflicting recommendations inside T2D give Errata realistic reliability test
cases (e.g., "grounded in evidence, but the evidence is outdated") that a
random corpus could never provide on purpose.

## Trade-offs We're Accepting

- **Ingestion robustness is tested later.** The original plan validated
  parsing against messy layouts first; now clean documents come first and
  layout variety waits for Stage 3. If parsing problems surface late, that's
  the cost.
- **More upfront effort per document.** Every document needs a stated reason
  and manifest record. Collecting 100 PDFs is faster than curating 10.
- **Slower initial corpus growth** by design.
- **Possible question-set bias.** If our initial clinical questions are too
  narrow, the corpus inherits that blindness.

## What Evidence Would Make Us Revisit

- If question-driven curation stalls — we can't find trustworthy, legally
  usable documents for the clinical questions that matter.
- If Stage 1's clean baseline hides parsing problems that then bite hard in
  Stage 2/3, we may pull layout-variety testing forward.
- If Errata's evaluation design needs corpus characteristics we didn't plan
  for, we add them deliberately — with a new decision document, not silently.

## Related Documents

- [DECISION-003: Product direction](./DECISION-003-product-direction.md) — why Type 2 Diabetes
- [Corpus README](../corpus/README.md) — the staged strategy in practice
- [Corpus selection guide](../corpus/corpus-selection-guide.md) — the ten questions
