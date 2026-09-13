# Baseline generation added claims not present in retrieved evidence

> Log problems that taught us something or changed an implementation
> decision. No trivial syntax mistakes.

## Date

2026-09-13

## Where It Happened

Generation stage — `clinivault_ai/generation/`, first real Gemini +
T2D-001 end-to-end run.

## What We Expected

The evidence-constrained prompt ("Answer using ONLY the evidence above.
Do not invent facts...") would be sufficient to keep all model output
grounded in the supplied evidence items. We expected that retrieval +
context construction + prompt constraints would produce a fully
evidence-grounded answer.

## What Actually Happened

The first real Gemini run on T2D-001 (query: "criteria for the diagnosis
of diabetes") produced a structured, citation-aware answer. Manual
inspection of each substantive claim against the 5 supplied evidence
items found:

- **10 of 12** substantive claims were directly supported by the
  supplied evidence.
- **2 of 12** substantive claims were model parametric additions not
  present in any supplied evidence item:
  1. "Repeat testing is required to confirm the diagnosis" — cited to
     rank 4 (T2D-001-p002-c003), but "repeat testing"/"confirm"
     language does not appear in that evidence text.
  2. "One-step 75-g OGTT derived from the IADPSG criteria" — cited to
     rank 5 (T2D-001-p017-c003), but rank 5 contains only
     Carpenter-Coustan values. IADPSG appears in the evidence only as
     a citation title in rank 3 (T2D-001-p023-c006), with no content
     about "one-step" or "75-g OGTT."

## Evidence

- Full verbatim answer preserved in
  `docs/pipelines/generation-baseline.md` (Verification Performed
  section).
- Claim-to-evidence mapping table in the Final Evidence Consistency
  Check report.
- Token usage: prompt 2,477 / candidates 740 / thinking 1,817 / total
  5,034.
- Generation latency: 13,032.69 ms.

## What We Investigated

Whether the unsupported claims originated from the evidence text or
from the model's parametric knowledge. Read the full text of all 5
supplied evidence items from the T2D-001 parsed/chunked artifact and
searched for the specific language used in the unsupported claims.

## What We Tried

N/A — this is an observation from a single real run, not a debugging
session.

## What Failed

The prompt-only control strategy (instructing the model to answer only
from supplied evidence) was insufficient to prevent parametric
additions. The model followed the instruction for most claims but
still inserted two claims from its training knowledge.

## The Fix

No code fix applied. This is a documentation + awareness finding.

## Why This Fix

N/A — no implementation change made.

## Impact

- Grounding classification changed from SUPPORTED to MOSTLY SUPPORTED
  in `docs/pipelines/generation-baseline.md`.
- The baseline generation stage can no longer claim full grounding.
- Documentation now explicitly records the limitation.
- Future generation-grounding decisions must account for this
  observed behavior.

## Prevention / Lesson Learned

Good retrieval and correct context construction do not guarantee that
the generator will restrict every claim to supplied evidence. Prompt
constraints reduce but do not eliminate parametric additions. Any
future claim of "grounded generation" requires measurement beyond
prompt design — this may include output verification, claim-level
evidence checking, or a formal evaluation framework. These are NOT
DECIDED / TO BE EVALUATED directions, not current work.

## Possible Future Directions (NOT DECIDED)

- Post-generation claim verification against supplied evidence.
- Structured output with mandatory evidence-span attribution.
- Hallucination-rate measurement framework.
- Alternative prompt strategies (e.g., chain-of-verification).
- Retrieval-augmented generation with explicit grounding scores.

None of these are implemented or scheduled. They are listed only as
possible responses to this observed limitation.
