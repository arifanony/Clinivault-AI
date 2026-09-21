# DECISION-014: Expand Retrieval Evaluation Benchmark from 21 to 46 Evidence-Backed Cases

- **Date:** 2026-09-21
- **Status:** Accepted
- **Decided by:** TASK EVAL-EXPAND-001 authorized under Genesis control state and local agent operating contract.

## Decision

Expand the static retrieval evaluation benchmark in `src/clinivault_ai/evaluation/cases.py` from 21 to 46 evidence-backed cases across all 9 documents in the baseline corpus (`stage-1-clean-baseline-corpus`). 

The baseline retrieval pipeline architecture (TF-IDF vector store with un-tuned chunking, preprocessed text, cosine similarity) remains **frozen** and unchanged.

## Context

The original 21-case retrieval benchmark was established during representative and corpus generalization validation (`docs/pipelines/retrieval-baseline-benchmark.md`). While it effectively demonstrated baseline behavior and identified key failure modes (reference section boilerplate in T2D-010, vocabulary mismatch in dense guidelines), its document coverage was uneven:
- T2D-002 had only 1 case.
- T2D-003, T2D-005, T2D-006, T2D-007, and T2D-010 had only 2 cases each.
- Several major clinical topics covered in the corpus (e.g., presymptomatic type 1 autoantibody screening, CGM time-in-range metrics, DPP-4 guidelines, finerenone mortality evidence, aspirin primary prevention, albuminuria classification tables) lacked dedicated benchmark queries.

## Expanded Benchmark Composition

The expanded benchmark adds 25 new cases (bringing the total to 46 cases across 9 corpus documents):

| Document | Baseline 21-Case Count | Expanded 46-Case Count | New Topics Added |
|---|---|---|---|
| **T2D-001** | 4 | 7 | Type 1 autoantibody screening, criteria table direct lookup, adult prediabetes screening interval |
| **T2D-002** | 1 | 3 | Lifestyle intervention weight/incidence outcomes, metformin for prediabetes weight effect |
| **T2D-003** | 2 | 4 | Optimal FPG numeric cut-off (104 mg/dL), optimal HbA1c threshold (6.03% moderate quality) |
| **T2D-005** | 2 | 5 | CGM time-in-range goals (Table 6.2), glycemic goal deintensification, DKA prevention education |
| **T2D-006** | 2 | 5 | High glucose/A1C insulin initiation criteria, metformin vs SU first-line CV risk, initial combination therapy criteria |
| **T2D-007** | 2 | 5 | ACP recommendation against DPP-4 inhibitors, SGLT2 mortality/CHF/CKD high-certainty evidence, hypoglycemia risk vs SU |
| **T2D-008** | 3 | 6 | Tirzepatide/semaglutide weight NMA rankings, finerenone all-cause mortality reduction (OR 0.89), SGLT2 kidney progression superiority |
| **T2D-009** | 3 | 6 | Aspirin primary prevention ASCEND evidence, SGLT2 in HFpEF/HFrEF (Rec 10.41a/10.44c), icosapent ethyl addition criteria (Rec 10.31) |
| **T2D-010** | 2 | 5 | Albuminuria/eGFR classification table (A1/A2/A3), finerenone in DKD (Rec 11.8 / FIDELIO-DKD), dietary protein intake restriction (>1.3 g/kg/day) |
| **TOTAL** | **21** | **46** | **25 new cases spanning all 9 corpus documents** |

All 21 original benchmark cases are preserved **verbatim** in code and ID, maintaining backward traceability.

## Verification of Labels and Expected Chunks

Every new case label was constructed following strict evidence-preservation discipline:
1. Expected chunk IDs were identified by auditing parsed text (`data/parsed/`) and embedding artifacts (`data/embedded/`) for explicit claim support.
2. Chunk IDs were verified against the canonical embedding JSON artifacts (`<doc>.embeddings.json`) for exact ID existence.
3. Substring texts of expected chunks were verified against the extracted corpus text via automated probe scripts (`tmp_chunks_all.txt`).
4. Labels cite the exact evidence location and recommendation number (e.g., ADA Recommendation 2.6, 6.7, 6.22, 10.31, 10.41a, 10.44c, 11.8; ACP Recommendation 1/2; NMA Table 1).

## Baseline Benchmark Results (Frozen Baseline Pipeline)

Running the expanded 46-case benchmark against the frozen baseline retrieval architecture yields:

| Metric | Original Benchmark (21 Cases) | Expanded Benchmark (46 Cases) | Absolute Count |
|---|---|---|---|
| **Total Cases** | 21 | 46 | +25 cases |
| **Hit@1** | 38.10% (8 / 21) | **26.09%** (12 / 46) | 12 hits |
| **Hit@5** | 76.19% (16 / 21) | **56.52%** (26 / 46) | 26 hits |
| **MRR** | 0.5095 | **0.3601** | — |

### Key Findings & Observations

1. **Increased Statistical Power:** Absolute Hit@1 increased from 8 to 12; absolute Hit@5 increased from 16 to 26.
2. **Realistic Measurement of Weaknesses:** The percentage drop in Hit@5 (76.19% -> 56.52%) reflects the inclusion of hard, realistic clinical queries (e.g., numerical cut-offs, dense classification tables, multi-drug comparative recommendations) where un-tuned TF-IDF keyword matching fails to rank the target chunk in the top 5 (ranking target chunks at ranks 6–98).
3. **Reproducibility:** The expanded benchmark suite runs in ~0.5s offline using canonical artifacts with zero network or non-deterministic dependencies.

## Consequences

- The expanded 46-case benchmark is now the authoritative evaluation baseline for all future Clinivault AI retrieval experiments (dense embeddings, hybrid retrieval, reranking).
- Any future retrieval architecture modification must be evaluated against this 46-case baseline set.
- All 210 existing repository tests continue to pass (`python -m unittest discover -s tests`).

## Related Documents

- `docs/decisions/DECISION-009-retrieval-baseline-representation.md`
- `docs/decisions/DECISION-010-retain-baseline-retrieval.md`
- `docs/pipelines/retrieval-baseline-benchmark.md`
- `docs/pipelines/retrieval-baseline-benchmark-results.md`
- `src/clinivault_ai/evaluation/cases.py`
- `src/clinivault_ai/evaluation/benchmark.py`
