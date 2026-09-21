"""Static benchmark case definitions.

Every case's expected-relevant chunk IDs are taken from documented,
previously verified evidence locations (never from generated answers).
Each case records its label source. Cases whose labels cover only part of
the question, or whose evidence location is only partially established,
carry ``ambiguous=True`` with an explanatory note.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    document_id: str
    query: str
    expected_chunk_ids: tuple[str, ...]
    label_source: str
    ambiguous: bool = False
    note: str = ""


REPRESENTATIVE = "docs/pipelines/representative-evaluation.md"
GENERALIZATION = "docs/pipelines/corpus-generalization-validation.md"
INVESTIGATION = "docs/pipelines/retrieval-ranking-investigation.md"
EXPAND = "EVAL-EXPAND-001 chunk audit (tmp_chunks_all.txt, embedding artifacts)"

CASES: tuple[BenchmarkCase, ...] = (
    # ---------------------------------------------------------------
    # ORIGINAL 21 CASES — unchanged from the baseline benchmark.
    # ---------------------------------------------------------------
    BenchmarkCase(
        "T2D-001-diagnosis", "T2D-001",
        "criteria for the diagnosis of diabetes",
        ("T2D-001-p014-c003", "T2D-001-p002-c002", "T2D-001-p002-c003"),
        f"{REPRESENTATIVE} EVAL-1 (ranks 1, 2, 4 judged relevant)"),
    BenchmarkCase(
        "T2D-001-classification", "T2D-001",
        "classification of diabetes types",
        ("T2D-001-p015-c002", "T2D-001-p004-c003", "T2D-001-p013-c003"),
        f"{REPRESENTATIVE} EVAL-2 (ranks 1, 2, 4 carried the supported claims)"),
    BenchmarkCase(
        "T2D-001-gdm", "T2D-001",
        "gestational diabetes screening in pregnancy",
        ("T2D-001-p023-c001", "T2D-001-p023-c004"),
        f"{REPRESENTATIVE} EVAL-3 (ranks 1, 2 carried the supported claims)"),
    BenchmarkCase(
        "T2D-001-hba1c", "T2D-001",
        "HbA1c test to diagnose diabetes",
        ("T2D-001-p002-c002", "T2D-001-p002-c003"),
        f"{REPRESENTATIVE} EVAL-5 claim table (the chunks cited as carrying "
        "the A1C/glucose diagnostic text; both also content-verified in "
        "EVAL-1's programmatic substring checks)",
        ambiguous=True,
        note="EVAL-5's RECORDED Top-5 is NOT reproducible against the persisted "
             "baseline (actual full ranks 48 and 32) and its quoted evidence "
             "phrase 'either A1C or glucose criteria' is absent from the "
             "corpus-wide chunk text, so this label's provenance is only "
             "partially verified. See retrieval-baseline-benchmark.md sections C "
             "and I and the 2026-09-16 engineering log entry.",
    ),
    BenchmarkCase(
        "T2D-002-screening", "T2D-002",
        "screening recommendations for prediabetes and type 2 diabetes",
        ("T2D-002-p007-c003", "T2D-002-p002-c001", "T2D-002-p004-c002"),
        f"{REPRESENTATIVE} EVAL-4 (ranks 1, 2, 3 judged relevant)"),
    BenchmarkCase(
        "T2D-003-hba1c-accuracy", "T2D-003",
        "What were the pooled sensitivity and specificity of HbA1c at 6.5% for diagnosing diabetes?",
        ("T2D-003-p008-c002", "T2D-003-p008-c001"),
        f"{GENERALIZATION} E.2 q1 (ranks 1 and 4, claims verified verbatim)"),
    BenchmarkCase(
        "T2D-003-quadas", "T2D-003",
        "What was the optimal cut-off for fasting plasma glucose and what quality assessment tool was used?",
        ("T2D-003-p001-c002", "T2D-003-p004-c003"),
        f"{GENERALIZATION} E.2 q2 (QUADAS-2 chunks, ranks 3 and 4)",
        ambiguous=True,
        note="label covers the quality-assessment half only; the optimal FPG "
             "cut-off half was documented as not answered from the supplied Top-5"),
    BenchmarkCase(
        "T2D-005-a1c-goal", "T2D-005",
        "What is the recommended A1C goal for most adults with diabetes?",
        ("T2D-005-p005-c001",),
        f"{GENERALIZATION} E.3 q1 (Figure 6.1 chunk, rank 5, claim verified)"),
    BenchmarkCase(
        "T2D-005-hypoglycemia", "T2D-005",
        "How should hypoglycemia be treated and what glucose threshold defines clinically significant hypoglycemia?",
        ("T2D-005-p010-c002", "T2D-005-p008-c001", "T2D-005-p010-c004"),
        f"{GENERALIZATION} E.3 q2 (ranks 1, 5, 2; claims verified verbatim)"),
    BenchmarkCase(
        "T2D-006-glp1-sglt2", "T2D-006",
        "When should GLP-1 receptor agonists or SGLT2 inhibitors be used in type 2 diabetes treatment?",
        ("T2D-006-p010-c002", "T2D-006-p008-c003"),
        f"{GENERALIZATION} E.4 q1 (ranks 4, 5; recs 9.21/9.22/9.9b/9.10/9.12 verified)"),
    BenchmarkCase(
        "T2D-006-second-line", "T2D-006",
        "What factors guide the choice of second-line medication after metformin?",
        ("T2D-006-p015-c004",),
        f"{INVESTIGATION} C.1 (initial-combination-therapy chunk, true rank 6)"),
    BenchmarkCase(
        "T2D-007-first-line", "T2D-007",
        "What does the ACP guideline recommend for first-line treatment of type 2 diabetes?",
        ("T2D-007-p003-c002",),
        f"{GENERALIZATION} E.5 q1 (rank 3, claim verified verbatim)"),
    BenchmarkCase(
        "T2D-007-add-on", "T2D-007",
        "When should an SGLT2 inhibitor or GLP-1 receptor agonist be added to metformin?",
        ("T2D-007-p009-c001", "T2D-007-p008-c002", "T2D-007-p002-c002"),
        f"{GENERALIZATION} E.5 q2 (ranks 1, 3, 4; Recommendation 1 verified)"),
    BenchmarkCase(
        "T2D-008-weight", "T2D-008",
        "Which medication classes most effectively reduce A1C and body weight in adults with type 2 diabetes?",
        ("T2D-008-p001-c002",),
        f"{GENERALIZATION} E.6 q1 (abstract chunk, rank 4; weight claims verified)",
        ambiguous=True,
        note="label covers the body-weight half only; no documented relevant "
             "chunk exists for the A1C-comparative half (model refused)"),
    BenchmarkCase(
        "T2D-008-harms", "T2D-008",
        "What are the main harms of SGLT2 inhibitors and GLP-1 receptor agonists reported in the review?",
        ("T2D-008-p013-c004", "T2D-008-p001-c004"),
        f"{GENERALIZATION} E.6 q2 + q2b (GLP-1 GI chunk rank 3; SGLT2 harms "
        "chunk documented outside Top-5 for this phrasing)"),
    BenchmarkCase(
        "T2D-008-harms-variant", "T2D-008",
        "SGLT2 inhibitors increase genital infections odds ratio medication-specific harms",
        ("T2D-008-p001-c004",),
        f"{GENERALIZATION} E.6 q2b (keyword-style variant, rank 2, OR 3.29 verified)"),
    BenchmarkCase(
        "T2D-009-bp", "T2D-009",
        "What blood pressure goal is recommended for adults with diabetes and how should hypertension be treated?",
        ("T2D-009-p003-c002", "T2D-009-p006-c001", "T2D-009-p006-c003"),
        f"{GENERALIZATION} E.7 q1 (ranks 1, 2, 4; claims verified verbatim)"),
    BenchmarkCase(
        "T2D-009-statins", "T2D-009",
        "When are statins recommended for cardiovascular risk reduction in type 2 diabetes?",
        ("T2D-009-p008-c003", "T2D-009-p008-c004", "T2D-009-p009-c001"),
        f"{INVESTIGATION} C.2 (recs 10.20-10.23 rank 42, 10.26 rank 98, "
        "closest support rank 21)"),
    BenchmarkCase(
        "T2D-009-statin-variant", "T2D-009",
        "For which patients is high-intensity statin therapy recommended, including age and primary versus secondary prevention?",
        ("T2D-009-p008-c003", "T2D-009-p009-c002"),
        f"{GENERALIZATION} E.7 q2b (ranks 5, 2; rec 10.20 verified)"),
    BenchmarkCase(
        "T2D-010-ckd-screening", "T2D-010",
        "How should chronic kidney disease be screened and monitored in adults with diabetes?",
        ("T2D-010-p001-c002",),
        f"{INVESTIGATION} C.3 (recs 11.1a/11.1b chunk, true rank 28)"),
    BenchmarkCase(
        "T2D-010-kidney-protection", "T2D-010",
        "When are ACE inhibitors, ARBs, SGLT2 inhibitors, or finerenone recommended for kidney protection in diabetes?",
        ("T2D-010-p006-c004", "T2D-010-p006-c003"),
        f"{INVESTIGATION} C.4 (ranks 12 and 13)"),

    # ---------------------------------------------------------------
    # NEW CASES — EVAL-EXPAND-001
    # All chunk IDs verified against embedding artifacts:
    #   data/embedded/stage-1-clean-baseline-corpus/<DOC>/<DOC>.embeddings.json
    # Chunk texts verified in tmp_probe_out (tmp_chunks_all.txt).
    # Label source is abbreviated as EXPAND throughout.
    # Original 21 cases above are NOT modified.
    # ---------------------------------------------------------------

    # --- T2D-001 new cases (3 new; doc previously had 4 cases) ---
    BenchmarkCase(
        "T2D-001-type1-autoantibody", "T2D-001",
        "How should presymptomatic type 1 diabetes be screened using autoantibody testing?",
        ("T2D-001-p007-c001",),
        f"{EXPAND}: T2D-001-p007-c001 (p=7) contains Recommendation 2.6 on screening "
        "for presymptomatic type 1 diabetes by testing autoantibodies against insulin "
        "(IA), glutamic acid decarboxylase (GAD), islet antigens — text verified verbatim."),
    BenchmarkCase(
        "T2D-001-diagnosis-criteria-table", "T2D-001",
        "What are the A1C and glucose criteria for diagnosing diabetes in nonpregnant adults?",
        ("T2D-001-p002-c001",),
        f"{EXPAND}: T2D-001-p002-c001 (p=2) contains Table 2.1 with A1C >= 6.5%, "
        "FPG >= 126 mg/dL and OGTT criteria — verified verbatim. Distinct from "
        "T2D-001-diagnosis which targets narrative screening text; this targets the "
        "criteria table directly using explicit terminology."),
    BenchmarkCase(
        "T2D-001-prediabetes-screening", "T2D-001",
        "Who should be screened for prediabetes and type 2 diabetes and how often should testing be repeated?",
        ("T2D-001-p011-c002", "T2D-001-p009-c003"),
        f"{EXPAND}: T2D-001-p011-c002 (p=11) contains the adult screening/testing "
        "for prediabetes and T2DM section header/text; T2D-001-p009-c003 (p=9) contains "
        "the 3-year repeat interval recommendation — both verified.",
        note="Multiple relevant chunks expected; label covers the primary screening "
             "population and repeat-interval text. Other nearby chunks may also be "
             "relevant but are not labeled."),

    # --- T2D-002 new cases (2 new; doc previously had 1 case) ---
    BenchmarkCase(
        "T2D-002-lifestyle-outcomes", "T2D-002",
        "What is the effect of lifestyle interventions on weight and diabetes incidence in people with prediabetes?",
        ("T2D-002-p005-c002", "T2D-002-p005-c003"),
        f"{EXPAND}: T2D-002-p005-c002 (p=5) contains pooled lifestyle intervention "
        "weight/BMI reduction data (WMD -1.2 kg, BMI -0.54); T2D-002-p005-c003 (p=5) "
        "contains effect-modification by BMI and diabetes incidence reduction "
        "percentages — both verified."),
    BenchmarkCase(
        "T2D-002-metformin-prediabetes", "T2D-002",
        "How does metformin affect weight and diabetes prevention in people with prediabetes?",
        ("T2D-002-p003-c004", "T2D-002-p005-c004"),
        f"{EXPAND}: T2D-002-p003-c004 (p=3) states metformin beneficial effect on weight; "
        "T2D-002-p005-c004 (p=5) cites DPP metformin weight reduction vs placebo data "
        "(-2.0 kg) — both verified."),

    # --- T2D-003 new cases (2 new; doc previously had 2 cases) ---
    BenchmarkCase(
        "T2D-003-fpg-optimal-cutoff", "T2D-003",
        "What is the optimal fasting plasma glucose cut-off point identified in this meta-analysis?",
        ("T2D-003-p002-c001",),
        f"{EXPAND}: T2D-003-p002-c001 (p=2) states 'the optimal cut-off for Fasting "
        "Plasma Glucose (FPG) was estimated as 104 milligram/dL with a sensitivity of "
        "82.3%' — text verified verbatim. Distinct from T2D-003-quadas which uses a "
        "combined FPG/QUADAS-2 query; this targets the FPG numeric result only."),
    BenchmarkCase(
        "T2D-003-hba1c-optimal-threshold", "T2D-003",
        "What was the optimal HbA1c cut-off for detecting diabetes identified in this meta-analysis and what was its certainty level?",
        ("T2D-003-p009-c002",),
        f"{EXPAND}: T2D-003-p009-c002 (p=9) contains 'optimal cutoff of HbA1c 6.03% "
        "was of moderate quality' and GRADE certainty assessment — text verified. "
        "Distinct from T2D-003-hba1c-accuracy which targets pooled sensitivity/"
        "specificity at the standard 6.5% threshold.",
        note="Query targets the 6.03% optimal threshold from meta-regression, not the "
             "standard 6.5% diagnostic cut-off; the distinction is clinically meaningful."),

    # --- T2D-005 new cases (3 new; doc previously had 2 cases) ---
    BenchmarkCase(
        "T2D-005-cgm-targets", "T2D-005",
        "What are the recommended continuous glucose monitoring time-in-range targets for adults with diabetes?",
        ("T2D-005-p003-c004",),
        f"{EXPAND}: T2D-005-p003-c004 (p=3) contains Table 6.2 with CGM metrics for "
        "clinical care — time-in-range goal 70-180 mg/dL and other thresholds — verified."),
    BenchmarkCase(
        "T2D-005-glycemic-deintensification", "T2D-005",
        "When should glycemic goals be relaxed or diabetes medications deintensified?",
        ("T2D-005-p007-c002", "T2D-005-p004-c002"),
        f"{EXPAND}: T2D-005-p007-c002 (p=7) contains 'Less stringent goals (A1C up to "
        "8%) may be recommended for individuals with complex health status'; "
        "T2D-005-p004-c002 (p=4) contains Recommendation 6.7 on deintensifying "
        "medications when harms exceed benefits — both verified."),
    BenchmarkCase(
        "T2D-005-dka-prevention", "T2D-005",
        "What education and monitoring are recommended to recognize and prevent diabetic ketoacidosis?",
        ("T2D-005-p012-c002", "T2D-005-p012-c005"),
        f"{EXPAND}: T2D-005-p012-c002 (p=12) contains Recommendation 6.22 on structured "
        "education for recognition/prevention/management of hyperglycemic crisis; "
        "T2D-005-p012-c005 (p=12) states individuals at risk should measure ketones "
        "with symptoms — both verified."),

    # --- T2D-006 new cases (3 new; doc previously had 2 cases) ---
    BenchmarkCase(
        "T2D-006-insulin-initiation", "T2D-006",
        "When should insulin therapy be initiated in people with type 2 diabetes?",
        ("T2D-006-p015-c003", "T2D-006-p016-c004"),
        f"{EXPAND}: T2D-006-p015-c003 (p=15) states 'initiate insulin therapy for people "
        "who present with blood glucose levels >= 300 mg/dL or A1C > 10%'; "
        "T2D-006-p016-c004 (p=16) contains 'Consider insulin as the first injectable if "
        "symptoms of hyperglycemia are present' — both verified."),
    BenchmarkCase(
        "T2D-006-metformin-first-line", "T2D-006",
        "What are the advantages of metformin compared with sulfonylureas as first-line therapy for type 2 diabetes?",
        ("T2D-006-p014-c003",),
        f"{EXPAND}: T2D-006-p014-c003 (p=14) states 'Compared with sulfonylureas, "
        "metformin as first-line therapy has no excess cardiovascular risk' and describes "
        "its availability in immediate- and extended-release forms — verified."),
    BenchmarkCase(
        "T2D-006-initial-combination", "T2D-006",
        "When should initial combination therapy with two agents be considered rather than sequential add-on for type 2 diabetes?",
        ("T2D-006-p015-c004",),
        f"{EXPAND}: T2D-006-p015-c004 (p=15) states 'Initial combination therapy should "
        "be considered in people presenting with A1C levels 1.5-2.0% above their "
        "individualized goal or in those at high risk for cardiovascular disease' — "
        "verified. NOTE: This chunk is also the labeled expected chunk for T2D-006-second-line. "
        "The queries are meaningfully different: second-line targets factors guiding agent "
        "selection after metformin; this targets the decision to use initial combination "
        "vs sequential therapy.",
        note="Expected chunk T2D-006-p015-c004 is shared with T2D-006-second-line. "
             "Retrieval rank for this case may differ from that case due to different "
             "query semantics. This is intentional — the chunk contains two related "
             "but distinct clinical concepts."),

    # --- T2D-007 new cases (3 new; doc previously had 2 cases) ---
    BenchmarkCase(
        "T2D-007-dpp4-against", "T2D-007",
        "What does the ACP guideline recommend regarding DPP-4 inhibitors added to metformin for inadequate glycemic control?",
        ("T2D-007-p008-c001",),
        f"{EXPAND}: T2D-007-p008-c001 (p=8) states 'ACP recommends against adding a "
        "dipeptidyl peptidase-4 (DPP-4) inhibitor to metformin and lifestyle modifications "
        "in adults with type 2 diabetes and inadequate glycemic control' — verified."),
    BenchmarkCase(
        "T2D-007-sglt2-cv-ckd-outcomes", "T2D-007",
        "What is the evidence for SGLT2 inhibitors reducing mortality, heart failure, and kidney disease outcomes?",
        ("T2D-007-p006-c002",),
        f"{EXPAND}: T2D-007-p006-c002 (p=6) states 'High-certainty evidence indicates "
        "that adding an SGLT-2 inhibitor to usual care reduces the risk for all-cause "
        "mortality, hospitalization due to CHF, and progression of CKD' — verified."),
    BenchmarkCase(
        "T2D-007-hypoglycemia-risk", "T2D-007",
        "How does hypoglycemia risk compare between SGLT2 inhibitors and sulfonylureas in type 2 diabetes?",
        ("T2D-007-p007-c002",),
        f"{EXPAND}: T2D-007-p007-c002 (p=7) states 'The risk for severe hypoglycemia "
        "is lower with SGLT-2 inhibitors and GLP-1 agonists than with sulfonylureas and "
        "long-acting insulins' — verified."),

    # --- T2D-008 new cases (3 new; doc previously had 3 cases) ---
    BenchmarkCase(
        "T2D-008-tirzepatide-weight", "T2D-008",
        "Which diabetes medications produce the greatest body weight and HbA1c reductions according to the network meta-analysis?",
        ("T2D-008-p011-c001", "T2D-008-p011-c002"),
        f"{EXPAND}: T2D-008-p011-c001 (p=11) contains the NMA body weight and HbA1c "
        "reduction table with tirzepatide (-8.63 kg, -1.78% A1C), semaglutide rankings; "
        "T2D-008-p011-c002 (p=11) continues the table with basal insulin, "
        "thiazolidinediones — both verified."),
    BenchmarkCase(
        "T2D-008-finerenone-mortality", "T2D-008",
        "What is the effect of finerenone on all-cause mortality according to this network meta-analysis?",
        ("T2D-008-p007-c004",),
        f"{EXPAND}: T2D-008-p007-c004 (p=7) states 'Finerenone reduces the risk of "
        "all-cause death (OR 0.89 (0.79 to 1.00), high certainty)' — verified verbatim."),
    BenchmarkCase(
        "T2D-008-sglt2-kidney-nma", "T2D-008",
        "What does this network meta-analysis show about SGLT2 inhibitors and kidney disease progression compared with other agents?",
        ("T2D-008-p008-c003",),
        f"{EXPAND}: T2D-008-p008-c003 (p=8) states 'SGLT-2 inhibitors are among the "
        "most effective medications and are probably superior to GLP-1RAs and finerenone "
        "in reducing the risk of kidney disease progression (both moderate certainty)' "
        "— verified."),

    # --- T2D-009 new cases (3 new; doc previously had 3 cases) ---
    BenchmarkCase(
        "T2D-009-aspirin-primary", "T2D-009",
        "Is aspirin recommended for primary prevention of cardiovascular events in adults with diabetes?",
        ("T2D-009-p014-c005", "T2D-009-p014-c003"),
        f"{EXPAND}: T2D-009-p014-c005 (p=14) contains 'Aspirin may be considered in "
        "the context of high cardiovascular risk with low bleeding risk but generally "
        "not in older adults'; T2D-009-p014-c003 (p=14) describes the ASCEND trial "
        "(15,480 diabetes patients, aspirin 100 mg vs placebo) — both verified."),
    BenchmarkCase(
        "T2D-009-sglt2-heart-failure", "T2D-009",
        "When are SGLT2 inhibitors recommended for adults with type 2 diabetes and heart failure?",
        ("T2D-009-p016-c002", "T2D-009-p016-c003"),
        f"{EXPAND}: T2D-009-p016-c002 (p=16) contains Recommendation 10.41a — SGLT2 "
        "inhibitor in established HFpEF/HFrEF with proven benefit; T2D-009-p016-c003 "
        "(p=16) contains Recommendation 10.44c on SGLT inhibitor in stage B or "
        "high-risk/established CVD for heart failure prevention — both verified."),
    BenchmarkCase(
        "T2D-009-icosapent-ethyl", "T2D-009",
        "When should icosapent ethyl be added to statin therapy in adults with diabetes?",
        ("T2D-009-p012-c005",),
        f"{EXPAND}: T2D-009-p012-c005 (p=12) contains Recommendation 10.31 — 'In "
        "individuals with ASCVD or other cardiovascular risk factors on a statin with "
        "managed LDL cholesterol but elevated triglycerides (150-499 mg/dL), the "
        "addition of icosapent ethyl should be considered' — verified."),

    # --- T2D-010 new cases (3 new; doc previously had 2 cases) ---
    BenchmarkCase(
        "T2D-010-albuminuria-classification", "T2D-010",
        "How is chronic kidney disease classified using albuminuria and eGFR categories in diabetes?",
        ("T2D-010-p002-c001", "T2D-010-p002-c002"),
        f"{EXPAND}: T2D-010-p002-c001 (p=2) contains albuminuria categories table "
        "(A1/A2/A3) and states CKD is classified based on eGFR and albuminuria; "
        "T2D-010-p002-c002 (p=2) provides UACR thresholds and eGFR ranges — verified. "
        "Distinct from T2D-010-ckd-screening (monitoring recommendations, p001-c002); "
        "this targets the classification framework itself.",
        note="These classification chunks are in reference-dense pages; retrieval "
             "behaviour may be affected by the same boilerplate-domination pattern "
             "documented in other T2D-010 cases."),
    BenchmarkCase(
        "T2D-010-finerenone-ckd", "T2D-010",
        "When is finerenone recommended to reduce CKD progression and cardiovascular events in people with diabetes?",
        ("T2D-010-p010-c001", "T2D-010-p010-c002"),
        f"{EXPAND}: T2D-010-p010-c001 (p=10) contains Recommendation 11.8 on finerenone "
        "to reduce CKD progression and cardiovascular events; T2D-010-p010-c002 (p=10) "
        "contains secondary outcomes and trial details from FIDELIO-DKD/FIGARO-DKD — "
        "both verified. Distinct from T2D-010-kidney-protection which uses a combined "
        "ACE/ARB/SGLT2/finerenone query (labeled on p006-c004/p006-c003)."),
    BenchmarkCase(
        "T2D-010-protein-restriction", "T2D-010",
        "What is recommended regarding dietary protein intake for people with diabetes and chronic kidney disease?",
        ("T2D-010-p005-c002", "T2D-010-p005-c003"),
        f"{EXPAND}: T2D-010-p005-c002 (p=5) states 'Higher levels of protein intake "
        "(>20% of daily calories or >1.3 g/kg/day) have been associated with increased "
        "albuminuria, more rapid kidney function loss, and CVD mortality'; "
        "T2D-010-p005-c003 (p=5) mentions medical nutrition therapy by a registered "
        "dietitian — both verified."),
)
