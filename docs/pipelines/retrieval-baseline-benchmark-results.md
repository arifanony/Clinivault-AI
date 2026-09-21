# Controlled Baseline Retrieval Benchmark — Measured Results

Status: **expanded baseline measurement complete** (offline, deterministic, reads-only).

This document records the exact measured results of the controlled retrieval benchmark defined in `docs/pipelines/retrieval-baseline-benchmark.md`. It reflects the **expanded 46-case benchmark set** (21 original cases + 25 new evidence-backed cases) evaluated via `python -m clinivault_ai.evaluation.benchmark` against canonical corpus artifacts under `data/parsed/` and `data/embedded/`.

## How to reproduce

```
.venv/Scripts/python -m clinivault_ai.evaluation.benchmark
```

Environment: no network, no generation, no API keys. Uses persisted `BaselineHashEmbeddingProvider` (`clinivault-baseline-hash-v1`, 256-dim vectors) and cosine similarity at Top-K=5.

## Aggregate Results Comparison

| Benchmark Version | Total Cases | Hit@1 | Hit@5 | MRR |
|---|---|---|---|---|
| **Original Baseline (21 Cases)** | 21 | 8 / 21 (38.10%) | 16 / 21 (76.19%) | 0.5095 |
| **Expanded Baseline (46 Cases)** | **46** | **12 / 46 (26.09%)** | **26 / 46 (56.52%)** | **0.3601** |

- Absolute Hit@1 increased from 8 to 12.
- Absolute Hit@5 increased from 16 to 26.
- Hit@5 percentage dropped from 76.19% to 56.52%, reflecting a broader, more rigorous set of complex clinical queries (numerical cut-offs, classification tables, multi-drug comparative recommendations).

---

## Per-Case Results (Expanded 46-Case Suite)

### T2D-001 (107 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-001-diagnosis` | criteria for the diagnosis of diabetes | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-001-classification` | classification of diabetes types | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-001-gdm` | gestational diabetes screening in pregnancy | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-001-hba1c` (AMB) | HbA1c test to diagnose diabetes | 0 | 0 | 0.0000 | None (48, 32) | Original |
| `T2D-001-type1-autoantibody` | presymptomatic type 1 autoantibody screening | **1** | **1** | **1.0000** | **1** | **NEW** (Rec 2.6) |
| `T2D-001-diagnosis-criteria-table` | A1C and glucose criteria for diagnosing diabetes | **0** | **0** | **0.0000** | **8** | **NEW** (Table 2.1) |
| `T2D-001-prediabetes-screening` | prediabetes/T2DM screening population & interval | **0** | **1** | **0.3333** | **3** | **NEW** (Rec 2.1) |

### T2D-002 (34 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-002-screening` | screening recommendations for prediabetes and type 2 diabetes | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-002-lifestyle-outcomes` | lifestyle intervention weight/incidence outcomes | **0** | **0** | **0.0000** | **9 (26)** | **NEW** (Meta-analysis) |
| `T2D-002-metformin-prediabetes` | metformin weight & diabetes prevention | **0** | **1** | **0.2500** | **4** | **NEW** (DPP data) |

### T2D-003 (44 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-003-hba1c-accuracy` | pooled sensitivity/specificity HbA1c at 6.5% | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-003-quadas` (AMB) | optimal FPG & quality assessment tool | 0 | 1 | 0.3333 | 3 | Original |
| `T2D-003-fpg-optimal-cutoff` | optimal fasting plasma glucose cut-off point | **0** | **0** | **0.0000** | **29** | **NEW** (104 mg/dL cut-off) |
| `T2D-003-hba1c-optimal-threshold` | optimal HbA1c cut-off & certainty level | **0** | **0** | **0.0000** | **8** | **NEW** (6.03% threshold) |

### T2D-005 (84 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-005-a1c-goal` | recommended A1C goal for most adults | 0 | 1 | 0.2000 | 5 | Original |
| `T2D-005-hypoglycemia` | treatment & glucose threshold for hypoglycemia | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-005-cgm-targets` | continuous glucose monitoring time-in-range targets | **0** | **0** | **0.0000** | **28** | **NEW** (Table 6.2) |
| `T2D-005-glycemic-deintensification` | relax glycemic goals / deintensify medications | **0** | **0** | **0.0000** | **6 (25)** | **NEW** (Rec 6.7) |
| `T2D-005-dka-prevention` | recognize and prevent diabetic ketoacidosis | **0** | **0** | **0.0000** | **19 (74)** | **NEW** (Rec 6.22) |

### T2D-006 (142 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-006-glp1-sglt2` | when to use GLP-1 or SGLT2 in type 2 diabetes | 0 | 1 | 0.2500 | 4 | Original |
| `T2D-006-second-line` | factors guiding second-line medication choice | 0 | 0 | 0.0000 | 6 | Original |
| `T2D-006-insulin-initiation` | when to initiate insulin therapy | **0** | **0** | **0.0000** | **82 (98)** | **NEW** (BG >= 300 / A1C > 10%) |
| `T2D-006-metformin-first-line` | advantages of metformin vs sulfonylureas | **0** | **0** | **0.0000** | **15** | **NEW** (No excess CV risk) |
| `T2D-006-initial-combination` | initial combination therapy criteria | **0** | **0** | **0.0000** | **90** | **NEW** (A1C 1.5-2.0% above goal) |

### T2D-007 (54 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-007-first-line` | ACP recommendation for first-line treatment | 0 | 1 | 0.3333 | 3 | Original |
| `T2D-007-add-on` | when to add SGLT2 or GLP-1 to metformin | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-007-dpp4-against` | ACP recommendation regarding DPP-4 inhibitors | **1** | **1** | **1.0000** | **1** | **NEW** (Against DPP-4 rec) |
| `T2D-007-sglt2-cv-ckd-outcomes` | SGLT2 mortality, HF, and CKD evidence | **1** | **1** | **1.0000** | **1** | **NEW** (High certainty evidence) |
| `T2D-007-hypoglycemia-risk` | SGLT2 vs sulfonylurea hypoglycemia risk | **0** | **0** | **0.0000** | **14** | **NEW** (Lower risk rec) |

### T2D-008 (64 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-008-weight` (AMB) | medications reducing A1C and body weight | 0 | 1 | 0.2500 | 4 | Original |
| `T2D-008-harms` | main harms of SGLT2 and GLP-1 | 0 | 1 | 0.3333 | 3 | Original |
| `T2D-008-harms-variant` | SGLT2 genital infections OR 3.29 | 0 | 1 | 0.5000 | 2 | Original |
| `T2D-008-tirzepatide-weight` | NMA body weight & A1C reduction rankings | **0** | **1** | **0.2000** | **5** | **NEW** (NMA Table 1) |
| `T2D-008-finerenone-mortality` | finerenone effect on all-cause mortality | **0** | **0** | **0.0000** | **17** | **NEW** (OR 0.89 mortality) |
| `T2D-008-sglt2-kidney-nma` | SGLT2 kidney disease progression superiority | **0** | **0** | **0.0000** | **8** | **NEW** (NMA kidney outcome) |

### T2D-009 (142 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-009-bp` | blood pressure goal & hypertension treatment | 1 | 1 | 1.0000 | 1 | Original |
| `T2D-009-statins` | statin recommendations for CV risk | 0 | 0 | 0.0000 | 21 (42, 98) | Original |
| `T2D-009-statin-variant` | high-intensity statin recommendation | 0 | 1 | 0.5000 | 2 | Original |
| `T2D-009-aspirin-primary` | aspirin primary prevention in diabetes | **0** | **0** | **0.0000** | **16 (48)** | **NEW** (ASCEND trial) |
| `T2D-009-sglt2-heart-failure` | SGLT2 inhibitors in heart failure | **1** | **1** | **1.0000** | **1** | **NEW** (Rec 10.41a/10.44c) |
| `T2D-009-icosapent-ethyl` | icosapent ethyl addition criteria | **0** | **0** | **0.0000** | **14** | **NEW** (Rec 10.31) |

### T2D-010 (70 candidate chunks)

| Case ID | Query | Hit@1 | Hit@5 | RR | First Rank | Notes |
|---|---|---|---|---|---|---|
| `T2D-010-ckd-screening` | CKD screening and monitoring | 0 | 0 | 0.0000 | 19 | Original |
| `T2D-010-kidney-protection` | ACEi/ARB/SGLT2/finerenone kidney recs | 0 | 0 | 0.0000 | 11 (12) | Original |
| `T2D-010-albuminuria-classification` | CKD albuminuria & eGFR classification | **0** | **1** | **0.5000** | **2** | **NEW** (Table 11.1 / A1-A3) |
| `T2D-010-finerenone-ckd` | finerenone in DKD (FIDELIO-DKD) | **0** | **1** | **0.3333** | **3** | **NEW** (Rec 11.8) |
| `T2D-010-protein-restriction` | dietary protein intake in CKD | **0** | **1** | **0.2500** | **4** | **NEW** (>1.3 g/kg/day rec) |

---

## Conclusion & Baseline Significance

1. The expanded 46-case benchmark provides a comprehensive baseline for evaluating retrieval quality across all 9 documents in the Clinivault AI baseline corpus.
2. The benchmark is completely deterministic and reproducible in ~0.5 seconds offline.
3. The frozen baseline retrieval system achieves **Hit@1 = 26.09% (12/46)**, **Hit@5 = 56.52% (26/46)**, and **MRR = 0.3601**.
4. Future retrieval improvements (semantic dense retrieval, BM25 hybrid indexing, reranking) will be evaluated against this exact 46-case benchmark set.
