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

CASES: tuple[BenchmarkCase, ...] = (
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
)
