# Broader Corpus Generalization Validation — Remaining Documents

Unit: validation only. No RAG architecture changes were made.

## A. Objective

Determine whether the existing baseline pipeline (hash embeddings, Top-K=5,
in-memory VectorStore, existing context construction, Gemini 2.5 Flash,
existing prompt, RunTrace) generalizes beyond T2D-001/T2D-002 to the remaining
validated corpus documents before deciding whether any retrieval, embedding,
chunking, generation, or infrastructure improvement is justified.

This is qualitative generalization evidence, not a statistical evaluation.

## B. Documents included / excluded

Included: T2D-003, T2D-005, T2D-006, T2D-007, T2D-008, T2D-009, T2D-010.

Excluded: T2D-004 (remains blocked; not forced into validation).

T2D-001 and T2D-002 were validated previously (see
`document-generalization-validation.md` and `representative-evaluation.md`).

## C. Validation methodology

- Documents validated one at a time for failure localization.
- For each document: confirm identity → ingest (parse) → chunk → embed →
  build index → select 1–2 representative queries from actual document
  content → retrieve → inspect retrieval qualitatively → build context →
  generate with baseline Gemini → inspect answer claims against the exact
  supplied chunk text (using the RunTrace evidence, not memory) → record.
- Claim classifications: SUPPORTED / PARTIALLY SUPPORTED / UNSUPPORTED only.
  Manual inspection against the supplied chunk text. No automatic grounding
  evaluation was performed.
- Temporary probe scripts and trace JSONs were used during the unit and
  removed afterwards; all durable results are recorded here.

## D. Baseline configuration (unchanged throughout)

- Baseline hash embedding provider, 256-dimensional embeddings

## E. Per-document results

### E.1 Ingestion / chunking / embedding (measured offline)

Raw PDFs live in `data/raw/stage-1-clean-baseline-corpus/`; parsed artifacts
in `data/parsed/stage-1-clean-baseline-corpus/<DOC>/<DOC>.parsed.json`.

| Doc | Raw size | Pages | Extracted text | Chunks | Embeddings | Dim | Chunk/emb agreement |
|---|---|---|---|---|---|---|---|
| T2D-003 | 1,498,978 B | 19 | 54,452 chars | 44 | 44 | 256 | OK (1:1) |
| T2D-005 | 948,730 B | 18 | 123,344 chars | 84 | 84 | 256 | OK (1:1) |
| T2D-006 | 1,547,487 B | 33 | 212,167 chars | 142 | 142 | 256 | OK (1:1) |
| T2D-007 | 1,004,874 B | 19 | 52,600 chars | 38 | 38 | 256 | OK (1:1) |
| T2D-008 | 795,139 B | 16 | 94,726 chars | 66 | 66 | 256 | OK (1:1) |
| T2D-009 | 1,535,506 B | 30 | 212,482 chars | 142 | 142 | 256 | OK (1:1) |
| T2D-010 | 1,258,833 B | 15 | 106,597 chars | 71 | 71 | 256 | OK (1:1) |

OBSERVED: ingestion (PDF parse) succeeded for every document via the existing
`clinivault_ai.ingestion` CLI; page-failure counts are not exposed in the
parsed artifact (`statistics` has no per-page ok/fail fields), so page
success/failure split is recorded as "no failures surfaced by the parser"
rather than an explicit zero. Text-based PDFs throughout (no OCR needed).
Every chunk obtained exactly one 256-dim embedding; chunk IDs and embedding
keys agreed for all seven documents.

RECONCILIATION (artifact-storage audit, 2026-09-16): the chunk/embedding
figures above were measured from in-memory generation during this unit
(`chunk_pages` + `generate_embeddings` feeding `VectorStore` directly); the
embedding artifacts were **not persisted** — no `T2D-003/005/006/007/008/
009/010.embeddings.json` exists under `data/embedded/stage-1-clean-baseline-corpus/`,
and none was committed (commit e190b22 added only the parsed artifacts).
The only durable embedding artifact in the repository is T2D-001's. The
results recorded here remain valid for the runs performed (deterministic
baseline; replayed and confirmed by the retrieval-ranking investigation),
but the embedding stage for these documents must be re-run and persisted to
the canonical locations defined in `docs/architecture/artifact-storage.md`
by a dedicated unit. T2D-002 additionally has no persisted parsed artifact.

### E.2 T2D-003 — Kaur et al., "Diagnostic accuracy of tests for type 2 diabetes and prediabetes" (PLOS ONE, systematic review/meta-analysis)

Query 1: "What were the pooled sensitivity and specificity of HbA1c at 6.5%
for diagnosing diabetes?" (primary clinical topic; numeric table evidence)

- Retrieval: rank 1 = T2D-003-p008-c002 (0.2942) — meta-analysis Table 2;
  rank 4 = p008-c001 (0.1759) — threshold/study-count table. Relevant chunks
  present; no irrelevant domination.
- Context: 5/5 evidence items passed through, IDs/pages preserved. CONTEXT OK.
- Generation: `gemini-2.5-flash`, status ok, prompt 4,151 tokens,
  candidates 211 (thoughts 665).
- Claims: pooled sensitivity 0.654 (95% CI 0.574–0.727) and specificity
  0.945 (95% CI 0.902–0.970) — verified verbatim in p008-c002 → SUPPORTED.
  "17 studies" at the 6.5% threshold — verified in p008-c001 Table 2 →
  SUPPORTED.

Query 2: "What was the optimal cut-off for fasting plasma glucose and what

### E.3 T2D-005 — ADA Standards of Care 2026, "Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises" chapter

Query 1: "What is the recommended A1C goal for most adults with diabetes?"
(primary recommendation; table/figure content)

- Retrieval: rank 5 = T2D-005-p005-c001 (0.3481) — Figure 6.1 (individualized
  A1C/CGM goals); ranks 1–4 are chapter intro. Relevant chunk present.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,685, candidates 101.
- Claims: A1C goal <7.0% for most nonpregnant adults with good health, low
  treatment risks/burdens — verified against the Figure 6.1 chunk →
  SUPPORTED (the model conditioned the goal on health/function, matching the
  figure). Person-centered individualization — SUPPORTED.

Query 2: "How should hypoglycemia be treated and what glucose threshold
defines clinically significant hypoglycemia?" (multi-chunk; numeric thresholds)

- Retrieval: rank 1 = p010-c002 (0.3705) — treatment text; rank 2 = p010-c004
  (glucagon); rank 5 = p008-c001 (0.3213) — hypoglycemia definitions. All
  relevant; no boilerplate domination.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,373, candidates 452 (thoughts 1,566).
- Claims (all verified against supplied chunk text): 15 g carbohydrates
  (5–10 g for automated insulin delivery users), recheck at 15 min, EMS for
  unalert individuals, pure glucose preferred, acarbose → pure glucose only,
  dietary protein should not be used, first-aid kits include oral glucose —
  all in p010-c002 → SUPPORTED. Intranasal/ready-to-inject glucagon widely
  available and preferred — p010-c004 → SUPPORTED. <70 mg/dL clinically
  important regardless of symptoms; Level 2 <54 mg/dL (neuroglycopenic
  threshold); 70 mg/dL recognized adrenergic threshold — p008-c001 →
  SUPPORTED.

T2D-005 totals: 5 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED.
Failure classification: E for both queries. Note (OBSERVED): Figure 6.1 text
survives extraction in visually garbled form ("<5 7.0%", "0 — 1% %"), yet the
answer still stated the correct <7.0% goal — the model tolerated the
artifact; a known fragility of table-heavy pages, not a failure of this query.

### E.4 T2D-006 — ADA Standards of Care 2026, pharmacologic approaches chapter (33 pages, 142 chunks)

Query 1: "When should GLP-1 receptor agonists or SGLT2 inhibitors be used in
type 2 diabetes treatment?" (recommendation/criteria; rec-numbered text)

- Retrieval: ranks 1–3 (0.4310/0.4303/0.4288) are reference-list chunks
  (p029/p030); ranks 4–5 = p010-c002 (recs 9.21/9.22) and p008-c003 (recs
  9.9b/9.10/9.12 + ASCVD text). Relevant recommendation chunks present at
  ranks 4–5; reference chunks occupy ranks 1–3 (boilerplate pressure).
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 3,088, candidates 651.
- Claims (all verified in supplied chunks): GLP-1 RA and/or SGLT2i included
  for established/high ASCVD risk irrespective of A1C; GLP-1–based therapy
  preferred to insulin absent severe hyperglycemia (9.21); insulin+GLP-1 RA
  combination (9.22); HFpEF GLP-1 RA (9.9b); CKD eGFR 20–60 GLP-1–based
  therapy (9.10); MASLD/obesity GLP-1 RA (9.12) → all SUPPORTED.

Query 2: "What factors guide the choice of second-line medication after
metformin?" (terminology variation; general algorithm question)

- Retrieval: ranks 1–5 landed on the special-populations section
  (p024-c005/c004, p023-c003/c004, p025-c005). The document contains the

### E.5 T2D-007 — ACP clinical guideline (2024 update), Annals of Internal Medicine

Query 1: "What does the ACP guideline recommend for first-line treatment of
type 2 diabetes?" (primary recommendation)

- Retrieval: rank 3 = T2D-007-p003-c002 (0.3801) — background/2017-guideline
  text; ranks 1–2 are other content pages. Relevant chunk present.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok. Claim: the 2017 ACP version recommended metformin
  plus lifestyle when pharmacologic therapy is needed — verified verbatim in
  p003-c002, with the model correctly attributing it to the 2017 version
  that this guideline updates → SUPPORTED. No overreach beyond evidence.

Query 2: "When should an SGLT2 inhibitor or GLP-1 receptor agonist be added
to metformin?" (recommendation + class-specific prioritization)

- Retrieval: rank 1 = p009-c001 (0.4384) — clinical considerations; rank 3 =
  p008-c002 (0.3474) (prioritize SGLT2 in CHF/CKD); rank 4 = p002-c002
  (0.3380) (Recommendation 1). Strong relevant set.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok. Claims (all verified): add SGLT2i or GLP-1 agonist
  to metformin + lifestyle in inadequate glycemic control (strong rec, high
  certainty) — p002-c002 → SUPPORTED; metformin+lifestyle first steps,
  benefits/harms/cost/preferences assessment, prioritize SGLT2i in CHF/CKD —
  p008-c002 → SUPPORTED; prioritize GLP-1 in increased stroke risk or weight
  loss goal — p009-c001 → SUPPORTED; SGLT2i reduces all-cause mortality,
  MACE, CKD progression, CHF hospitalization; GLP-1 reduces all-cause
  mortality, MACE, stroke — p002-c002 → SUPPORTED.

T2D-007 totals: 5 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED.
Failure classification: E for both queries.

### E.6 T2D-008 — BMJ living systematic review / network meta-analysis of antihyperglycemic agents

Query 1: "Which medication classes most effectively reduce A1C and body
weight in adults with type 2 diabetes?" (comparative-effectiveness question)

- Retrieval: rank 4 = T2D-008-p001-c002 (0.3513) — abstract/RESULTS chunk
  naming SGLT-2 inhibitors, GLP-1RAs, finerenone, tirzepatide as providing
  differential benefits including body weight. Glycemia (A1C) comparative
  ranking evidence exists in the article but was not in Top-5.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,852, candidates 92.
- Claims: named drug classes provide weight benefits / differential benefits
  — verified in p001-c002 → SUPPORTED. The model explicitly stated the
  supplied evidence does not identify which classes most effectively reduce
  A1C → accurate for supplied evidence; honest refusal, no unsupported claim.
- Classification: generation = E; retrieval = OBSERVED weakness (A1C
  comparative results not surfaced for this phrasing).

Query 2 (original): "What are the main harms of SGLT2 inhibitors and GLP-1
receptor agonists reported in the review?"

- Retrieval: rank 3 = p013-c004 (0.4859) — discussion chunk stating a
  "recent NMA ... demonstrated molecule-specific and dose-dependent benefits
  and harms for weight loss and gastrointestinal side effects". The SGLT2
  medication-specific harms chunk (p001-c004) was not in this Top-5.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok. Claims: GLP-1 RA molecule-specific, dose-dependent
  GI harms — verified p013-c004 → SUPPORTED. Model explicitly stated the
  evidence does not report main SGLT2 harms → accurate for the supplied

### E.7 T2D-009 — ADA Standards of Care 2026, "Cardiovascular Disease and Risk Management" chapter (30 pages, 142 chunks)

Query 1: "What blood pressure goal is recommended for adults with diabetes
and how should hypertension be treated?" (multi-chunk recommendation set)

- Retrieval: rank 1 = p003-c002 (0.4829) — BP goals; rank 2 = p006-c001
  (0.4707) — lifestyle; rank 4 = p006-c003 (0.4550) — pharmacologic recs;
  ranks 3/5 = p002 monitoring chunks. Highly relevant set.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,584, candidates 1,000.
- Claims (all verified in supplied chunks): individualized <130/80
  on-treatment goal via shared decision-making (p003-c002) → SUPPORTED; SBP
  <120 for elevated CVD risk with benefit/trade-off caveat (p003-c002,
  p006-c001) → SUPPORTED; lifestyle for BP >120/80 incl. DASH, sodium,
  alcohol, activity, smoking (p006-c001) → SUPPORTED; initiate/titrate
  pharmacotherapy ≥130/80 (p006-c003) → SUPPORTED; ≥150/90 prompt two drugs
  or single-pill combination (p006-c003) → SUPPORTED; ACEi/ARB first-line in
  albuminuria or CAD, UACR 30–299 / ≥300 and eGFR <60 detail, avoid
  ACEi+ARB (incl. ARB+neprilysin, direct renin inhibitors) combination
  (p006-c003) → SUPPORTED; home BP monitoring counseling (p002-c004) and
  measurement every routine visit or ≥6 months (p002-c003) → SUPPORTED.

Query 2 (original): "When are statins recommended for cardiovascular risk
reduction in type 2 diabetes?"

- Retrieval: ranks 1–5 (p001-c002 0.5343, p016-c001, p029-c004, p030-c005,
  p018-c003) — intro and reference-heavy chunks; the statin recommendation
  chunks (10.20–10.23, p008) were NOT retrieved although they exist in the
  document (proven by the variant below) → RETRIEVAL FAILURE (B) for this
  query phrasing: supporting evidence exists but was not supplied in Top-K.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok. Model explicitly stated the supplied evidence does
  not answer the statin question and described what the evidence does cover
  → accurate, safe refusal; no unsupported claims. Generation grounding held
  even though retrieval failed.

Query 2b (variant): "For which patients is high-intensity statin therapy
recommended, including age and primary versus secondary prevention?"

- Retrieval: rank 5 = p008-c003 (0.3265) — recs 10.20–10.23; rank 2 =
  p009-c002 (0.3491) — primary-prevention text. Relevant evidence retrieved.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,719, candidates 304.
- Claims: high-intensity statin for diabetes aged 40–75 at higher
  cardiovascular risk, LDL reduction ≥50% and goal <70 mg/dL (10.20) —
  verified p008-c003 → SUPPORTED; primary prevention aged ≥40, high-
  intensity in context of additional ASCVD risk — verified p009-c002 →
  SUPPORTED. Model correctly noted the supplied evidence does not explicitly
  give secondary-prevention high-intensity recommendations — accurate for
  the supplied Top-5.


## F. Cross-document findings

### OBSERVED

1. Pipeline generalizes mechanically across all seven documents: ingestion,
   chunking, embedding (1:1 chunk/embedding agreement, 256-dim), index
   construction, context passing (5/5 in every query, IDs/pages preserved),
   and generation (12 generated answers returned status ok; one document's
   generation was blocked by quota, not by implementation).
2. Claim grounding across the 12 generated answers: 34 substantive claims
   inspected, 34 SUPPORTED, 0 PARTIALLY SUPPORTED, 0 UNSUPPORTED. No
   generation-grounding failure was observed anywhere in this unit.
3. The model repeatedly gave evidence-accurate refusals when the answer was
   not in the supplied Top-5 (T2D-003 FPG cut-off, T2D-008 A1C ranking and
   SGLT2 harms, T2D-009 statins, T2D-006 general second-line). No
   hallucinated specifics appeared in any inspected answer.
4. Retrieval weakness pattern (cross-document): on chapters with long
   reference lists (T2D-006 q2, T2D-009 q2, T2D-010 q1/q2),
   reference/boilerplate chunks and off-topic special-population chunks can
   occupy the entire Top-5 for natural-language questions, while the same
   document answers keyword-style or differently-phrased queries well
   (T2D-008 q2b, T2D-009 q2b). Relevant evidence existed in each document;
   the hash embedding sometimes failed to rank it into Top-K. In every such
   case the model refused rather than fabricate.
5. Table/figure pages survive extraction in partially garbled form
   (e.g., T2D-005 Figure 6.1) yet did not cause wrong answers in this unit.

### INFERENCE

1. Generation grounding is not the current bottleneck; retrieval ranking on
   reference-heavy guideline chapters is the first observed weakness class.
   If a future unit justifies a change, the evidence points at ranking
   (e.g., document-structure-aware filtering or reranking) rather than
   chunking, prompting, or generation.
2. Safe-refusal behavior means retrieval gaps currently degrade to "no
   answer" rather than wrong answers — acceptable for a clinical tool, but
   it converts retrieval weakness into coverage loss.
3. No component added during this unit was needed; no implementation defect
   was found.

### NOT YET VALIDATED

1. T2D-010 generation (Gemini quota exhausted before its queries; retrieval
   and context validated offline).
2. Multi-document combined indexing and cross-document retrieval (all runs
   were single-document, consistent with prior units).
3. Any statistical retrieval metric or labeled relevance dataset (none
   exists; this unit is qualitative).

## G. Limitations

- Qualitative validation only; 1–2 queries per document (13 total, 12 with
  generation).
- Small document set; T2D-004 remains blocked and unvalidated.
- No formal labeled relevance dataset; no recall/precision/MRR metrics; no
  automated grounding evaluation; classifications are manual judgments
  against supplied chunk text.
- Gemini free-tier quota constraints limited real runs; 429 QUOTA_EXCEEDED
  was encountered previously for EVAL-4/EVAL-5 and during this unit's
  T2D-010 attempt. Per the quota rule, no failed provider call was retried.
- Multi-document indexing not yet validated.
- Page-level ok/fail counts are not exposed by the parsed artifact; absence
  of surfaced failures was used instead of an explicit zero.

## H. Next-step recommendation

No RAG architecture change is justified yet by this evidence. The baseline
continues to generalize: every generated claim across six documents was
supported by supplied evidence, and retrieval gaps degraded to safe refusals
rather than grounding failures. The single recurring weakness — hash-embedding
ranking allowing reference-list chunks to dominate Top-5 on reference-heavy
guideline chapters (OBSERVED in T2D-006 q2, T2D-009 q2, T2D-010) — should be
re-confirmed with a small set of additional queries (after quota recovery,
including T2D-010 generation) before any ranking/retrieval component is
proposed. Do not implement reranking, hybrid retrieval, or query rewriting
on the basis of this unit alone.

T2D-009 totals: 10 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED (plus one
evidence-accurate refusal after a retrieval failure).

### E.8 T2D-010 — ADA Standards of Care 2026, "Chronic Kidney Disease and Risk Management" chapter

- Ingestion/chunking/embedding: OK (15 pages, 106,597 chars, 71 chunks,
  71×256-dim embeddings, agreement OK).
- Query 1: "How should chronic kidney disease be screened and monitored in
  adults with diabetes?" — retrieval validated OFFLINE: Top-5 dominated by
  reference-list chunks (p012-c003 0.4905, p015-c004, p015-c003, p008-c001,
  p010-c001); the screening recommendation chunks were not in Top-5.
- Query 2: "When are ACE inhibitors, ARBs, SGLT2 inhibitors, or finerenone
  recommended for kidney protection in diabetes?" — retrieval validated
  OFFLINE: Top-5 dominated by reference/pregnancy-contraindication chunks
  (p011-c003, p004-c003, p014-c006, p015-c006, p012-c005); the
  kidney-protection recommendation chunks were not in Top-5.
- Context: both queries passed 5/5 evidence items with IDs/pages preserved
  (validated offline).
- Generation: NOT YET VALIDATED. The generation probe encountered Gemini
  free-tier 429 QUOTA_EXCEEDED after the earlier documents' calls; no
  further provider requests were attempted per the quota rule.
- Classification: NOT YET VALIDATED for generation; retrieval weakness
  OBSERVED offline (reference-heavy pages dominating Top-5 for both
  natural-language queries). A keyword-style variant probe
  ("annual screening urinary albumin creatinine ratio eGFR monitoring CKD
  diabetes recommendations") improved candidate diversity but still showed
  reference chunks among top ranks.

  Top-5, safe refusal.

Query 2b (variant, keyword-style): "SGLT2 inhibitors increase genital
infections odds ratio medication-specific harms"

- Retrieval: rank 2 = T2D-008-p001-c004 (0.2399) — the medication-specific
  harms paragraph. Relevant chunk retrieved with keyword-style phrasing.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 2,264, candidates 123.
- Claims: SGLT-2 inhibitors increase genital infections, OR 3.29 (95% CI
  2.88–3.77), high certainty — verified verbatim in p001-c004 → SUPPORTED.

T2D-008 totals: 3 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED (plus two
evidence-accurate refusals).

  general second-line/combination guidance (Figure 9.4 / recommendation
  section), but it was not in Top-5. A generic phrasing matched the
  "switching medications" subsection instead of the general algorithm.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok. The model correctly identified that the supplied
  evidence only covers second-line choice in the mTOR-inhibitor
  hyperglycemia context (pioglitazone consideration; no direct evidence for
  GLP-1 RA/SGLT2i — verified in p024-c004) and explicitly declined the
  general question → both statements SUPPORTED; no unsupported claims.
- Classification: generation = E (safe refusal); retrieval = OBSERVED
  weakness (relevant general guidance exists in the document but was not
  retrieved for the generic phrasing). Not a context or generation failure.

T2D-006 totals: 8 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED.

quality assessment tool was used?" (concept across methods sections)

- Retrieval: rank 3 = p001-c002 (0.1412), rank 4 = p004-c003 (0.1348) —
  methods chunks; relevant evidence present but not at rank 1.
- Context: 5/5, preserved. CONTEXT OK.
- Generation: status ok, prompt 3,072 tokens, candidates 164.
- Claims: QUADAS-2 was the quality-assessment tool — verified verbatim in
  p001-c002 ("quality assessment of studies using QUADAS-2 tool") and
  p004-c003 → SUPPORTED. The model explicitly stated the evidence does not
  give the optimal FPG cut-off — accurate for the supplied Top-5; honest
  refusal, no unsupported claim.

T2D-003 totals: 3 SUPPORTED, 0 PARTIALLY, 0 UNSUPPORTED.
Failure classification: E (no significant failure) for both queries.

- Top-K = 5
- Existing VectorStore (in-memory, from artifacts)
- Existing context construction
- Existing Gemini generation provider (`google_gemini`, `gemini-2.5-flash`)
- Existing prompt and RunTrace
- No Top-K experiments, no embedding comparison, no reranking, no hybrid
  retrieval, no query rewriting, no chunk-size or prompt changes.
