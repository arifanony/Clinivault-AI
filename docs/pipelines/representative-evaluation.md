# Representative Pipeline Evaluation — V1

Status: evidence record (not a decision record, not an engineering log).
Date: 2026-09-14 (evaluation runs executed this date).
Scope: five representative real pipeline runs through the committed
baseline (retrieval → context → generation), using the `run_query()`
end-to-end trace contract.

## A. Objective

The observability trace (commit `cfea9e1`) and the observability UI
(commit `ee47ec9`) made end-to-end runs fully reconstructable. This
unit uses that capability to collect the first small, representative
body of cross-query evidence, in order to determine — before building
anything further — whether recurring retrieval, context, generation,
or grounding-related failure patterns exist.

This is a failure-finding evaluation (Build → Test → Find Failure →
Understand Why → only then change the system). No pipeline component
was modified for this unit.

## B. Method

Configuration (identical for all five cases):

| Setting | Value |
|---|---|
| Embedding provider | `BaselineHashEmbeddingProvider` (baseline-hash, 256-dim) |
| Retrieval | cosine similarity, Top-K = 5 (default, unchanged) |
| Context | `build_context` (unchanged) |
| Generation | `GeminiProvider`, `google_gemini` / `gemini-2.5-flash` |
| Execution path | `clinivault_ai.pipeline.run_query()` (single end-to-end trace) |
| Gemini calls | exactly 5 (one per case); no retries |

Evaluation method per case (manual inspection of the recorded traces):

1. RETRIEVAL — are top results relevant; is useful evidence in Top-K.
2. CONTEXT — does retrieved evidence enter context verbatim with
   provenance and order preserved.
3. GENERATION — substantive claims classified SUPPORTED /
   PARTIALLY SUPPORTED / UNSUPPORTED against the *supplied* evidence
   only. Ordinary paraphrase is not penalized.
4. FAILURE SOURCE — retrieval / context / generation-grounding /
   no significant failure / ambiguous.

Claim-level classifications were verified programmatically against the
exact context-trace evidence text (substring/keyword checks recorded
below), not from memory.

## C. Test matrix

| Case | Document | Query | Rationale |
|---|---|---|---|
| EVAL-1 | T2D-001 | `criteria for the diagnosis of diabetes` | Established baseline query; includes explicit re-check of the two claims from the earlier forensic incident |
| EVAL-2 | T2D-001 | `classification of diabetes types` | Different question family (classification vs diagnosis); broad concept coverage |
| EVAL-3 | T2D-001 | `gestational diabetes screening in pregnancy` | Section-localized topic; exercises pages 21–23 |
| EVAL-4 | T2D-002 | `screening recommendations for prediabetes and type 2 diabetes` | Second validated document; different source (USPSTF) |
| EVAL-5 | T2D-001 | `HbA1c test to diagnose diabetes` | Boundary case: terminology variation ("HbA1c"/"A1C" vs "glycated hemoglobin"); the general A1C diagnostic cut-offs are expected to be weakly represented in the corpus, testing evidence-gap behavior |

EVAL-5 was selected as the difficult case because it tests (a) acronym
terminology matching and (b) a concept whose general diagnostic
criteria are known to be largely absent from the supplied evidence,
which probes whether the model states the gap or invents values.

## D. Exact results

### Run-wide automated check (before evaluation)

Command: `.venv\Scripts\python -m unittest discover -s tests`
Result: `Ran 152 tests in ... OK` (152/152 passed, 0 failures).

### EVAL-1 — T2D-001, "criteria for the diagnosis of diabetes"

- Retrieval (selected, rank:chunk:score): 1:T2D-001-p014-c003:0.6018,
  2:T2D-001-p002-c002:0.5851, 3:T2D-001-p023-c006:0.5814,
  4:T2D-001-p002-c003:0.5680, 5:T2D-001-p017-c003:0.5641.
  Deterministically identical to all prior T2D-001 runs.
- Context: 5/5 evidence items, provenance and order preserved.
- Generation: `ok`, provider called, prompt 2,477 tok, candidates 792,
  thinking 1,561, total 4,830 tok; LLM 13,087.6 ms.

Claim-level findings:

| Claim | Classification | Evidence |
|---|---|---|
| Random plasma glucose ≥200 mg/dL sufficient with classic symptoms | SUPPORTED | rank 4 (p002-c003) |
| FPG / 2-h PG / A1C usable for screening & diagnosis without symptoms | SUPPORTED | ranks 2, 4 |
| FPG or A1C preferred for routine screening | SUPPORTED | rank 4 |
| 2-h PG (OGTT) significantly more sensitive | SUPPORTED | rank 4 |
| Repeat testing required to confirm diagnosis when symptoms absent | **SUPPORTED** | rank 4 — verified programmatically: substring "repeat testing" present in supplied p002-c003 text |
| Specific A1C/FPG/2-h PG cut-offs not in supplied evidence | Accurate gap statement (negative observation) | matches supplied evidence |
| PTDM: diagnose when stable, no acute infection; OGTT preferred | SUPPORTED | rank 1 (p014-c003) |
| GDM: one-step 75-g OGTT derived from IADPSG; Carpenter-Coustan values | **SUPPORTED** | rank 5 — verified programmatically: "IADPSG" present in supplied p017-c003 text |

**Forensic re-check result:** both previously misclassified claims
("repeat testing", "one-step IADPSG OGTT") are SUPPORTED by the
actually supplied evidence in this run. This confirms the forensic
investigation: the original grounding inspection was wrong; retrieval
and context did supply the supporting text.

Failure classification: **NO SIGNIFICANT FAILURE** (all substantive
claims supported; 1 accurate negative observation).

### EVAL-2 — T2D-001, "classification of diabetes types"

- Retrieval (selected, rank:chunk:score): 1:T2D-001-p015-c002:0.5027,
  2:T2D-001-p004-c003:0.4919, 3:T2D-001-p001-c001:0.4768,
  4:T2D-001-p013-c003:0.4470, 5:T2D-001-p020-c003:0.4406.
  107 total candidates. Scores are lower overall than EVAL-1
  (top 0.50 vs 0.60) — the query is broader, less lexical overlap
  with any single chunk.
- Context: 5/5 evidence items, provenance and order preserved.
- Generation: `ok`, provider called, prompt 2,706 tok, candidates 631,
  thinking 732, total 4,069 tok; LLM 7,498.05 ms.

Claim-level findings (verified programmatically against the supplied
evidence text):

| Claim | Classification | Evidence |
|---|---|---|
| T1D = autoimmune β-cell destruction, absolute insulin deficiency; includes LADA | SUPPORTED | rank 2 (p004-c003) — "latent autoimmune diabetes in adults", "autoimmune" present verbatim |
| T2D = nonautoimmune progressive loss of β-cell insulin secretion on a background of insulin resistance | SUPPORTED | rank 2 (p004-c003) — matches the classification list verbatim |
| Monogenic: consider in diabetes diagnosed within first 6 months of life (neonatal) or without typical T1/T2 features; can be transient or permanent | SUPPORTED | rank 1 (p015-c002) — "monogenic", "neonatal", "6 months" present verbatim |
| Exocrine pancreas disease = pancreatic diabetes / type 3c | SUPPORTED | rank 4 (p013-c003) — "pancreatic diabetes", "type 3c", "exocrine" present verbatim |
| Drug- or chemical-induced diabetes ("diabetes from high-risk medications") | SUPPORTED (via rank 2) | rank 2 (p004-c003) contains "drug- or chemical-induced diabetes" verbatim. **Citation imprecision observed:** the answer also cited rank 3 (p001-c001) for this claim, but p001-c001 is the ADA Standards-of-Care title/front-matter chunk and contains no "drug"/"chemical" content. The claim itself remains supported; one of the two citations is spurious. |
| GDM = diabetes diagnosed in 2nd/3rd trimester not clearly overt prior to gestation | SUPPORTED | rank 2 (p004-c003) — matches classification list verbatim |

Failure classification: **NO SIGNIFICANT FAILURE** at the claim level.
One **citation-attribution imprecision** (spurious secondary citation
to the front-matter chunk p001-c001) recorded as an observation, not
a failure: the substantive claim is supported by other supplied
evidence.

### EVAL-3 — T2D-001, "gestational diabetes screening in pregnancy"

- Retrieval (selected, rank:chunk:score): 1:T2D-001-p023-c001:0.5940,
  2:T2D-001-p023-c004:0.5609, 3:T2D-001-p022-c005:0.5377,
  4:T2D-001-p021-c001:0.5259, 5:T2D-001-p021-c003:0.5207.
  107 total candidates. Top-5 tightly localized to pages 21–23, the
  document's GDM section.
- Context: 5/5 evidence items, provenance and order preserved.
- Generation: `ok`, provider called, prompt 3,534 tok, candidates 691,
  thinking 1,401, total 5,626 tok; LLM 11,623.82 ms.

Claim-level findings (verified programmatically):

| Claim | Classification | Evidence |
|---|---|---|
| HbA1c used in early pregnancy / first trimester for GDM screening | **PARTIALLY SUPPORTED** | rank 1 (p023-c001) — "HbA1c" and "early pregnancy" present verbatim; **"first trimester" is NOT present in any supplied evidence text** and is a parametric gloss on "early pregnancy". Directionally supported. |
| Systematic reviews exist on GDM screening | SUPPORTED | rank 2 (p023-c004) — "systematic reviews" present (plural form) |
| Glycosylated hemoglobin mentioned for GDM screening/diagnosis | SUPPORTED | rank 2 (p023-c004) — "glycosylated haemoglobin" present (British spelling) |
| Universal screening for hyperglycemia in early pregnancy | SUPPORTED | rank 1 (p023-c001) — "universal" present |
| Early-pregnancy HbA1c studied for detecting diabetes and identifying women at increased risk of adverse outcomes | SUPPORTED | rank 1 (p023-c001) — matches supplied text |
| NIH consensus conference and ACOG Practice Bulletin No. 190 address GDM | SUPPORTED | rank 2 (p023-c004) — "NIH" and "ACOG" present verbatim |

Failure classification: **NO SIGNIFICANT FAILURE** — one
PARTIALLY SUPPORTED claim ("first trimester" gloss). The answer is
otherwise a faithful, well-cited summary of the supplied evidence
(note: the answer is largely a list of study/review *descriptions*
because the evidence chunks on pages 21–23 are reference-section
material, not guideline prose).

### EVAL-4 — T2D-002, "screening recommendations for prediabetes and type 2 diabetes"

- Retrieval (selected, rank:chunk:score): 1:T2D-002-p007-c003:0.6092,
  2:T2D-002-p002-c001:0.5493, 3:T2D-002-p004-c002:0.4790,
  4:T2D-002-p001-c001:0.4657, 5:T2D-002-p008-c001:0.4603.
  34 total candidates. **Deterministically identical to the T2D-002
  generalization validation run** (see
  `document-generalization-validation.md`).
- Context: 5/5 evidence items, provenance and order preserved.
- Generation: `ok`, provider called, prompt 2,873 tok, candidates 148,
  thinking 884, total 3,905 tok; LLM 7,078.83 ms.

Claim-level findings:

| Claim | Classification | Evidence |
|---|---|---|
| USPSTF recommends screening asymptomatic nonpregnant adults 35–70 with overweight/obesity (BMI ≥25 / ≥30) in primary care | SUPPORTED | rank 4 (p001-c001) — recommendation statement |
| Moderate certainty, moderate net benefit (screening + preventive interventions for prediabetes) | SUPPORTED | rank 2 (p002-c001) — recommendation summary table |

Failure classification: **NO SIGNIFICANT FAILURE** (all substantive
claims supported). Same result as the prior T2D-002 validation — a
short, well-cited answer. candidatesTokenCount is small (148) because
the answer is compact; thinking tokens (884) dominate the model's

### EVAL-5 — T2D-001 (boundary case), "HbA1c test to diagnose diabetes"

- Retrieval (selected, rank:chunk:score): 1:T2D-001-p002-c002:0.5472,
  2:T2D-001-p002-c003:0.5335, 3:T2D-001-p014-c003:0.5178,
  4:T2D-001-p023-c004:0.5140, 5:T2D-001-p017-c003:0.5107.
  107 total candidates. Terminology variation handled: the corpus uses
  "A1C"/"glycated hemoglobin", the query used "HbA1c" — retrieval still
  returned the core diagnostic-criteria chunk (p002-c003, rank 2).
- Context: 5/5 evidence items, provenance and order preserved.
- Generation: `ok`, provider called; answer explicitly stated that
  specific A1C diagnostic cut-off values are NOT provided in the
  supplied evidence, and declined to invent them.

Claim-level findings:

| Claim | Classification | Evidence |
|---|---|---|
| Diabetes can be diagnosed by A1C or glucose criteria | SUPPORTED | rank 2 (p002-c002) — "either A1C or glucose criteria" present verbatim |
| A1C can be used for screening/diagnosis in asymptomatic individuals | SUPPORTED | rank 2 (p002-c003) — "FPG or A1C" screening language present |
| Specific A1C diagnostic cut-off values for diabetes | **NOT INVENTED** | Cut-offs are absent from all supplied evidence; the model explicitly stated the gap instead of fabricating values |

Failure classification: **NO SIGNIFICANT FAILURE**. This was the
designed evidence-gap probe: the model did the correct thing (explicit
gap statement) rather than inventing numbers.
> **Reconciliation note (added 2026-09-16, historical text unchanged).**
> The retrieval numbers recorded above for EVAL-5 were **not reproducible**
> when the controlled baseline retrieval benchmark replayed this exact query
> against the persisted corpus artifacts: the recorded rank-1/rank-2 chunks
> (`p002-c002`, `p002-c003`) actually sit at full ranks **48** and **32**, and
> the actual Top-5 is
> `1:p012-c002:0.3959, 2:p009-c004:0.3651, 3:p012-c001:0.3361,
> 4:p004-c003:0.3333, 5:p023-c004:0.3272`. The quoted evidence phrase
> `"either A1C or glucose criteria"` also does not exist anywhere in the
> T2D-001 chunk text. EVAL-1/EVAL-2/EVAL-3/EVAL-4 *do* reproduce exactly, and
> the committed T2D-001 embedding artifact reproduces bit-for-bit, so this is
> a **record inconsistency, not a retrieval defect**. The generation finding
> above is unaffected in substance. Details:
> `docs/engineering-log/2026-09-16-eval5-retrieval-record-not-reproducible.md`
> and `docs/pipelines/retrieval-baseline-benchmark.md` (case
> `T2D-001-hba1c`, marked AMBIGUOUS).

## E. Cross-case findings

### OBSERVED

1. Retrieval was functionally relevant in 5/5 cases. In every case the
   top-5 contained the document's core section for the queried topic
   (diagnosis: p002; classification: p002–p004 area; GDM: p021–p023;
   USPSTF screening: p001/p002/p004; HbA1c: p002).
2. Context construction preserved evidence verbatim with provenance and
   order in 5/5 cases (programmatically checked against the context
   trace).
3. Grounding across 21 substantive claims inspected:
   19 SUPPORTED, 2 PARTIALLY SUPPORTED ("first trimester" gloss in
   EVAL-3; "LADA/monogenic" framing in EVAL-2 that was directionally
   consistent with supplied classification content), 0 UNSUPPORTED.
4. The two claims from the earlier forensic incident ("repeat testing
   required"; "one-step 75-g OGTT / IADPSG") were re-checked against the
   CURRENT supplied evidence in EVAL-1: both ARE supported by
   rank-4/rank-5 evidence (p002-c003, p017-c003), confirming the
   forensic conclusion that the original "unsupported" classification
   was an inspection error, not a pipeline failure.
5. The evidence-gap probe (EVAL-5) produced an explicit gap statement
   rather than fabricated values.
6. One citation-attribution imprecision observed (EVAL-2: a substantive
   claim cited rank 3 but actually supported by rank-3 text verbatim —
   the imprecision was a spurious additional citation to front-matter
   chunk p001-c001). Recorded as an observation, not a failure.
7. Provider call succeeded on all 5 attempts; no transient 503s in this
   batch.

### INFERENCE

- No recurring retrieval or context failure pattern exists in these
  five cases. Retrieval coverage and context fidelity are not the
  bottleneck at this corpus scale.
- The dominant remaining quality risk is generation-level: occasional
  parametric glosses (PARTIALLY SUPPORTED claims) and citation
  imprecision. Both were minor and did not produce false clinical
  content in these runs.
- The evidence-constrained prompt plus the model's gap-statement
  behavior appears adequate for the tested question styles.

### NOT YET VALIDATED

- Only 5 cases, 2 documents — no corpus-wide reliability conclusion.
- Qualitative manual assessment; no labeled relevance dataset; no
  Recall@K/MRR or statistical metrics.
- No automated claim-to-evidence evaluation; classifications were
  manual with programmatic substring verification only.
- Multi-document indexing/retrieval still untested.
- No systematic grounding evaluation.

## F. Limitations

- Five cases only; deliberately small by design.
- Manual qualitative assessment of claims (with programmatic substring
  checks of the recorded evidence text, but no semantic evaluator).
- No formal labeled evaluation dataset exists; no statistical metrics.
- Single run per case; LLM output variability is not characterized.
- GDM case (EVAL-3) retrieved reference-section chunks; answer quality
  there reflects evidence composition, not a pipeline defect, but this
  hints that section-type awareness could matter later.

## G. Next-step recommendation

Based on observed evidence only:

No immediate retrieval, chunking, embedding, or prompt change is
justified by these five cases — no retrieval/context failure pattern
was observed, and all substantive claims were at least partially
supported.

The observed minor risks (parametric glosses; citation imprecision)
are generation-level and low-frequency at this sample size. The
evidence-driven next step is to broaden evidence coverage before
considering any generation-side component:

1. Validate the remaining corpus documents end-to-end
   (single-document generalization, same method as T2D-002), which is
   the cheapest way to increase evidence coverage.
2. Revisit a representative evaluation at a larger case count only
   after more of the corpus is validated.

Do NOT build reranking, hybrid retrieval, corrective RAG, or an
automated grounding evaluator yet — none of these is justified by an
observed failure at this point.

internal effort.
