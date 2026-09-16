# T2D-010 Ingestion-Quality Isolation Investigation

- **Date:** 2026-09-16
- **Type:** Forensic investigation (no code or behavior changes)
- **Trigger:** The baseline retrieval benchmark (`docs/pipelines/retrieval-baseline-benchmark.md`) and the ranking investigation (`docs/pipelines/retrieval-ranking-investigation.md`) showed T2D-010 with the worst retrieval behavior of the corpus. This unit asks a narrower question: **is the T2D-010 weakness materially caused by ingestion/parsing/chunking quality?**

## 1. Scope and constraints

Investigation only. No changes to retrieval, embeddings, Top-K, chunking, parser, benchmark, or prompt. The standing uncommitted items (`.env`, `.env.example`, `TESTIMG/`) were untouched. No Gemini API calls were needed.

## 2. Artifact audit (OBSERVED)

All three canonical artifact sets exist for T2D-010 at corpus version `stage-1-clean-baseline-corpus`:

| Stage | Path | Contents |
|---|---|---|
| raw | `data/raw/stage-1-clean-baseline-corpus/T2D-010/` | source PDF (committed) |
| parsed | `data/parsed/stage-1-clean-baseline-corpus/T2D-010/` | `T2D-010.parsed.json`, `T2D-010.validation.json` |
| embedded | `data/embedded/stage-1-clean-baseline-corpus/T2D-010/` | `T2D-010.embeddings.json` (71 records, dim 256) |

## 3. Problem queries and expected evidence (from existing records)

- **q1 (CKD screening):** expected support = the 11.1a/11.1b screening recommendations in chunk `T2D-010-p001-c002`; observed rank **28** (offline replay). Top-5 dominated by citation/boilerplate chunks (DCCT/EDIC, FIGARO, EMPEROR, FDA, cystatin-C).
- **q2 (kidney protection / finerenone):** expected support = `T2D-010-p006-c004` (rank 12), `T2D-010-p006-c003` (rank 13), `T2D-010-p006-c001` (rank 20); finerenone-related chunks spread across ranks 25–66.

## 4. Chunk-level inspection (OBSERVED)

The stored text of the expected chunks and their same-page neighbors was read in full:

- The 11.1a/11.1b screening recommendation content **is present** in `p001-c002`, but the page-1 extraction mixes recommendation text with reference/footnote material, so the clinical sentences do not form a clean contiguous passage.
- Page-6 chunks contain the kidney-protection discussion, but the finerenone recommendation label series (**11.4a**) could not be located anywhere in the parsed corpus text — a controlled search of the full parsed artifact did not find the recommendation label text. The 11.4-series recommendation is therefore **not intact in the parsed artifact**.
- Evidence of multi-column interleaving (sentences from two columns merged mid-line) was confirmed on the affected pages by comparing the parsed text against a plain `pdfplumber` extraction of the same pages of the raw PDF.

## 5. Root-cause decomposition (vs the ranking-investigation classes)

| Query | Ingestion contribution | Ranking contribution | Verdict |
|---|---|---|---|
| q1 | Real but secondary: page-1 text is interleaved with reference material, diluting the passage; the recommendation is still present | **Primary:** stopword hash collision ("chronic"/"be"/"screened" in one bucket, identical 0.1411 contributions) plus citation-chunk boilerplate mass | **B + E dominant, D contributory** |
| q2 | **Material:** the 11.4a recommendation label/text is not locatable in the parsed corpus — a genuine extraction/coverage gap (class D) | Secondary: surviving relevant chunks sit at ranks 12/13/20 due to function-word mass | **D significant, B contributory** |

## 6. Answer to the unit question

**Yes, partially.** Ingestion quality is a **material confound for T2D-010**, but it is not the sole cause:

1. **q2 has a true ingestion defect:** the target finerenone recommendation (11.4 series) is absent/unrecoverable from the parsed artifact. No ranking change can retrieve text that was never extracted intact.
2. **q1's weakness is mostly ranking,** not ingestion: the expected chunk exists and ranks 28 primarily because of hash-embedding behavior (collision + function-word mass + citation boilerplate), even though interleaving further dilutes the passage.
3. T2D-010 is the only corpus document where an extraction/coverage gap of this kind was demonstrated; the other weakness cases (T2D-006 q2, T2D-009 q2) are ranking-driven.

## 7. Classification

- **OBSERVED:** artifact existence; stored chunk contents; absence of the 11.4-series recommendation text in the parsed corpus; interleaving on the affected pages vs raw extraction; the recorded ranks and scores.
- **INFERENCE:** the interleaving and label loss stem from the multi-column layout of this specific ADA Standards-of-Care chapter interacting with the column-aware reader (consistent with the earlier engineering-log entry `2026-09-16-t2d-010-column-interleaving.md`); fixing extraction would move q2's ceiling but not q1's rank-28 behavior.
- **NOT YET VALIDATED:** whether a re-parse (or different extraction strategy) recovers the 11.4 series intact; how much q1's rank would improve if interleave-diluted text were cleaned; generalization of this failure mode to other guideline chapters.

## 8. Consequences for the planned next step

The planned bounded scoring comparison (term weighting vs one semantic provider vs unchanged baseline) remains the correct next retrieval experiment, but for T2D-010 its ceiling is limited by extraction quality. Any such comparison should either exclude the ingestion-defective case (q2) or report it separately as ingestion-limited.
