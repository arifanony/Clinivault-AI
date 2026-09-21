# Engineering Log: Retrieval Evaluation Benchmark Expansion to 46 Cases

- **Date:** 2026-09-21
- **Task:** EVAL-EXPAND-001 (Expand Retrieval Evaluation Benchmark)
- **Author:** Coding Agent

## Objective

Expand the static retrieval evaluation benchmark from 21 cases to 46 cases to achieve comprehensive, multi-document coverage across all 9 validated corpus documents without altering the frozen baseline retrieval architecture.

## Execution & Discovery

1. **Artifact Inspection & Text Mapping:**
   - Evaluated the canonical embedding artifacts in `data/embedded/stage-1-clean-baseline-corpus/` and parsed JSON artifacts in `data/parsed/stage-1-clean-baseline-corpus/`.
   - Verified that embedding JSON artifacts store vectors and chunk metadata (`chunk_id`, `document_id`, `page_number`) but do not contain raw chunk texts.
   - Built a deterministic text extraction probe to map all chunk IDs to their exact raw text content across all 9 documents.

2. **Case Design & Evidence Auditing:**
   - Selected 25 new clinical domain queries spanning every document in the corpus.
   - For every new query, audited parsed chunk text to verify that the expected chunk explicitly contains the clinical evidence required to answer the query (e.g., ADA Recommendations 2.6, 6.7, 6.22, 10.31, 10.41a, 10.44c, 11.8; ACP Recommendations 1 & 2; NMA Table 1).
   - Ensured all 21 original benchmark cases were preserved without modification.

3. **Codebase Updates:**
   - Updated `src/clinivault_ai/evaluation/cases.py` to append the 25 new `BenchmarkCase` definitions, expanding `CASES` from 21 to 46 cases.
   - Preserved all case IDs and ambiguous flags for existing cases.

4. **Measured Baseline Performance (Frozen Pipeline):**
   - Executed `python -m clinivault_ai.evaluation.benchmark` against the expanded 46-case benchmark.
   - Result:
     - Total cases: **46** (across 9 documents)
     - Hit@1: **12 / 46 (26.09%)** (up from 8 hits)
     - Hit@5: **26 / 46 (56.52%)** (up from 16 hits)
     - MRR: **0.3601**

5. **Validation & Clean-Up:**
   - Ran unit test suite (`python -m unittest discover -s tests`). All **210 tests passed cleanly**.
   - Removed all temporary probe files (`tmp_probe_chunks.py`, `tmp_probe_out.txt`, `tmp_chunks_all.txt`, `benchmark_47_results.txt`).
   - Recorded `DECISION-014` in `docs/decisions/DECISION-014-benchmark-expansion.md` and updated decisions index in `docs/decisions/README.md`.
   - Updated `docs/pipelines/retrieval-baseline-benchmark.md` and `docs/pipelines/retrieval-baseline-benchmark-results.md`.

## Summary of Findings

The expanded 46-case benchmark suite significantly improves evaluation coverage and provides a far more challenging, realistic measurement of multi-document retrieval performance over clinical guideline text. Absolute hits increased (Hit@1: 8->12, Hit@5: 16->26), while the percentage metrics reflect the increased difficulty of complex queries targeting dense numerical tables, multi-agent comparative recommendations, and specific clinical thresholds.
