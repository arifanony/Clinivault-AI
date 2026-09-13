# Document-Generalization Validation

Status: **in progress** (baseline verified on two documents)

This document records evidence that the Clinivault pipeline generalizes
beyond the first baseline document (T2D-001).

It is **not** a decision record and **not** an engineering-problem log.
It is validation evidence: each entry records what was tested, what
happened, and what can/cannot be concluded.

---

## Why We Moved From T2D-001 to T2D-002

T2D-001 (ADA Standards of Care 2026, Section 2: Diagnosis and
Classification) was the first document fully validated end-to-end.

After the single-document baseline was functionally verified, T2D-002
was selected because testing only one document was insufficient to
demonstrate that the pipeline generalized.

T2D-002 was deliberately selected because it differs from T2D-001 in:

| Characteristic | T2D-001 | T2D-002 |
|----------------|---------|---------|
| Authoritative source | ADA | USPSTF |
| Clinical question family | Diagnosis/classification | Screening |
| Document length | 23 pages | 8 pages |
| Document type | Clinical guideline | Recommendation statement |
| Text layer | Yes | Yes |
| Layout | Two-column academic | Two-column clinical |

This was a validation-sequence decision, **not** an architectural
decision. No new decision record was required. No engineering-log
entry was required because no failure occurred.

---

## T2D-002 Validation Evidence

### 1. Document Identity

| Field | Value |
|-------|-------|
| Document ID | T2D-002 |
| Title | Prediabetes and Type 2 Diabetes: Screening |
| Authors / Organization | U.S. Preventive Services Task Force (USPSTF) |
| Source | USPSTF Recommendation Statement |
| Clinical topic | Screening for prediabetes and type 2 diabetes |
| Document type | Clinical guideline / preventive recommendation |

### 2. Source

USPSTF official recommendation statement (2021). Different
authoritative body from T2D-001 (ADA), providing evidence that the
pipeline handles documents from multiple trusted sources.

### 3. Page Count

**8 pages**

### 4. File Characteristics

| Metric | Value |
|--------|-------|
| Filename | T2D-002-uspstf-2021-prediabetes-t2d-screening.pdf |
| Size | 172,732 bytes |
| Text layer | Yes (text-based PDF) |
| Layout | Two-column |
| Tables | Yes |

### 5. Ingestion Result

| Metric | Value |
|--------|-------|
| Pages extracted | 8 / 8 |
| Failed pages | 0 |
| Total characters | 50,445 |
| Status | SUCCESS |

### 6. Parsing/Reading-Order Result

The column-aware parser produced coherent text on all 8 pages. No

### 10. Retrieval Query

**Query:** `"screening recommendations for prediabetes and type 2 diabetes"`

### 11. Top-5 Retrieval Results

| Rank | Chunk ID | Page | Score | Content Summary |
|------|----------|------|-------|-----------------|
| 1 | T2D-002-p007-c003 | 7 | 0.6092 | Metformin prevention subgroups |
| 2 | T2D-002-p002-c001 | 2 | 0.5493 | USPSTF Recommendation summary |
| 3 | T2D-002-p004-c002 | 4 | 0.4790 | Benefits/harms of screening |
| 4 | T2D-002-p001-c001 | 1 | 0.4657 | Recommendation statement header |
| 5 | T2D-002-p008-c001 | 8 | 0.4603 | DESMOND education program |

### 12. Retrieval Classification

**FUNCTIONALLY RELEVANT** — all top-5 results are about USPSTF
screening recommendations, prediabetes, or diabetes prevention.

### 13. Context Provenance

| Metric | Value |
|--------|-------|
| Evidence count | 5 |
| Documents | ['T2D-002'] |
| Latency | 0.08 ms |
| Provenance preserved | Yes (rank, chunk_id, document_id, page_number, score, text) |

### 14. Generated Answer

The US Preventive Services Task Force (USPSTF) recommends screening
for prediabetes and type 2 diabetes (EVIDENCE_ITEM_RANK: 2, T2D-002-
p002-c001). This recommendation applies to nonpregnant adults aged
35 to 70 years who have overweight or obesity (BMI >= 25 or >= 30)
and have no symptoms of diabetes (EVIDENCE_ITEM_RANK: 4, T2D-002-
p001-c001).

The USPSTF concludes with moderate certainty that screening and
offering preventive interventions has a moderate net benefit
(EVIDENCE_ITEM_RANK: 2). The rationale includes: convincing evidence
that lifestyle interventions reduce progression to diabetes
(EVIDENCE_ITEM_RANK: 2); adequate evidence that interventions for
newly diagnosed diabetes reduce mortality (EVIDENCE_ITEM_RANK: 2);
adequate evidence that harms are no greater than small
(EVIDENCE_ITEM_RANK: 2).

### 15. Grounding Inspection Result

**8/8 substantive claims supported** by supplied evidence.

| Claim | Evidence | Verdict |
|-------|----------|---------|
| USPSTF recommends screening | Rank 2 | SUPPORTED |
| Adults aged 35-70 | Rank 4 | SUPPORTED |
| BMI >=25 or >=30 | Rank 4 | SUPPORTED |
| No symptoms required | Rank 4 | SUPPORTED |
| Moderate net benefit | Rank 2 | SUPPORTED |
| Lifestyle interventions reduce progression | Rank 2 | SUPPORTED |
| Interventions reduce mortality | Rank 2 | SUPPORTED |
| Harms no greater than small | Rank 2 | SUPPORTED |

### 16. Per-Stage Latency

| Stage | Latency |
|-------|---------|
| Retrieval | 1.05 ms |
| Context construction | 0.08 ms |
| Prompt construction | 0.08 ms |
| LLM generation | 7,504.00 ms |

### 17. Generation-Stage Total

**7,504.07 ms** — covers prompt construction + LLM generation +
result assembly overhead. Does NOT include query embedding, retrieval,
or context construction.

### 18. Approximate Full-Pipeline Latency

**~7,505.47 ms** — sum of all stages. NOT a performance benchmark;
single-run observation on one query against one document.

### 19. Token Usage

| Metric | Value |
|--------|-------|
| Prompt tokens | 2,873 |
| Candidate tokens | 416 |
| Thinking tokens | 1,008 |
| Total tokens | 4,297 |
| Service tier | standard |

### 20. Provider/Model

| Field | Value |
|-------|-------|
| Provider | google_gemini |
| Model | gemini-2.5-flash |
| Status | ok |

### 21. OBSERVED

- T2D-002 ingested successfully, 0 page failures
- Column-aware parsing produced coherent text on all 8 pages
- 34 chunks and 34 embeddings produced with correct document identity
- Retrieval returned 5 on-topic results for a screening query
- Context preserved full provenance
- Generation produced a structured, evidence-cited answer
- All 8 substantive claims are supported by supplied evidence
- No source-code changes required
- No architecture changes required

### 22. INFERENCE

The existing pipeline generalizes from T2D-001 (ADA) to T2D-002
(USPSTF) without architectural change. The column-aware parser
handles a different two-column guideline document correctly. Retrieval
and generation behavior are consistent across documents from
different authoritative sources.

### 23. NOT YET VALIDATED

- Multi-document indexing and retrieval
- Systematic grounding quality (only manual inspection of two runs)
- Corpus-wide reliability (only 2 of 10 documents tested)
- Image/scanned PDF behavior (no scanned PDFs in corpus)
- Persistence across process restarts
- Long-document behavior (T2D-006 is 33 pages)
- Table-heavy document behavior with complex reading order

---

## Explicit Claim Boundaries

**Two-document validation provides additional evidence of baseline
generalization but does not establish corpus-wide reliability.**

8/8 supported on this run does NOT equal a systematic grounding
evaluation. The grounding assessment is a manual inspection of one
representative run, not a metric.

---

## Why We Moved Forward

T2D-002 passed the controlled functional generalization check without
requiring architectural changes. Therefore the baseline is now
supported across two documents for the tested characteristics.

**Remaining limitation:** Only 2 documents have been validated
end-to-end; broader corpus generalization remains unvalidated.

---

## Comparison with T2D-001 Baseline

| Aspect | T2D-001 | T2D-002 | Consistent? |
|--------|---------|---------|-------------|
| Ingestion success | Yes | Yes | YES |
| Pages | 23 | 8 | Different, both OK |
| Reading order | Coherent | Coherent | YES |
| Chunk count | 107 | 34 | Proportional |
| Embedding dim | 256 | 256 | YES |
| Retrieval on-topic | Yes | Yes | YES |
| Provenance preserved | Yes | Yes | YES |
| Generation status | ok | ok | YES |
| Grounding | 10/12 supported | 8/8 supported | Both mostly supported |
| Pre-LLM stages | <4 ms | <2 ms | YES |
| Architecture changes | None | None | YES |

reading-order corruption or interleaving was observed. Sample from
page 1: "Clinical Review & Education JAMA | US Preventive Services
Task Force | RECOMMENDATION STATEMENT Screening for Prediabetes
and Type 2 Diabetes" — coherent, correctly ordered text from a
two-column layout.

### 7-9. Chunking and Embedding Result

| Metric | Value |
|--------|-------|
| Chunks produced | 34 |
| Document ID | T2D-002 |
| Embeddings produced | 34 |
| Model | clinivault-baseline-hash-v1 |
| Dimension | 256 |
| Chunks-Embedding agreement | True |
