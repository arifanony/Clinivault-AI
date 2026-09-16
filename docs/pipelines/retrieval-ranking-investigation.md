# Baseline Retrieval Ranking Weakness — Forensic Investigation

Investigation unit: diagnosis only. No retrieval, embedding, chunking, or
generation code was changed.

## A. Objective

The corpus generalization validation
(`corpus-generalization-validation.md`) found relevant evidence inside Top-K=5
for only 9/13 queries. Affected cases: T2D-006 q2, T2D-009 q2, and T2D-010
q1/q2 (validated offline). This unit answers two questions with evidence:

1. Why did the baseline miss or under-rank relevant evidence in these
   specific cases?
2. Is there enough evidence to justify changing the retrieval architecture?

## B. Baseline configuration (unchanged)

- Embedding provider: `clinivault-baseline-hash-v1` (hashed bag-of-words,
  blake2b, whitespace-lowercase tokenizer, **no stopword removal, no IDF,
  punctuation kept attached to tokens**, L2-normalized), 256 dimensions.
- Top-K = 5, cosine similarity, deterministic tie-break by chunk_id,
  brute-force ranking (existing `search`/`VectorStore`).
- Single-document in-memory indexes rebuilt from the committed parsed
  artifacts; queries replayed offline (no API calls).

Method: for each affected query the baseline Top-5 was replayed via the
existing `search` seam (it reproduced the recorded validation results
exactly, confirming the recorded evidence is trustworthy). One controlled
full-ranking inspection per query was then performed — justified because
locating the true rank of the known relevant chunks cannot be established
from Top-5 alone; retrieval behavior/configuration was not changed. Score
decompositions were computed at hash-bucket level from the exact baseline
token/hash math.

## C. Affected cases

### C.1 T2D-006 q2 — "What factors guide the choice of second-line medication after metformin?" (142 chunks)

Baseline Top-5 (reconstructed, identical to recorded validation run):

| Rank | Chunk | Page | Score | Content |
|---|---|---|---|---|
| 1 | T2D-006-p024-c005 | 24 | 0.4438 | mTOR-inhibitor hyperglycemia timing/agents (special populations) |
| 2 | T2D-006-p023-c003 | 23 | 0.4017 | Medication-unavailability strategies (252 tokens) |
| 3 | T2D-006-p025-c005 | 25 | 0.3978 | Kidney-transplant UTI risk (49 tokens) |
| 4 | T2D-006-p023-c004 | 23 | 0.3938 | Switching FDA-approved medications; childbearing (225 tokens) |
| 5 | T2D-006-p024-c004 | 24 | 0.3860 | mTOR → pioglitazone "second-line treatment" (239 tokens) |

Relevant evidence (general intensification guidance after metformin):
**T2D-006-p015-c004** — "Initial combination therapy should be considered in
people presenting with A1C levels 1.5–2.0% above their individualized goal..."
ranks **6** with 0.3842 — one rank below the cutoff (margin 0.0018).

Score decomposition of rank-1 chunk (bucket level): literal-token buckets
0.3826, collision-only buckets 0.0612. Two function words alone — "the"
(0.2296) and "of" (0.1071) — contribute **76%** of the rank-1 score; the
content tokens ("second-line", "choice", "medication", "metformin")
contribute ≈0.01–0.03 each.

Classification: **B — ranking quality issue** (relevant evidence one rank
below cutoff), with **C — query/terminology mismatch** contributing (the
document's general guidance uses "initial combination therapy" vocabulary,
while the literal string "second-line" appears in the mTOR special-
population chunk, which the lexical model then rewards).

### C.2 T2D-009 q2 — "When are statins recommended for cardiovascular risk reduction in type 2 diabetes?" (142 chunks)

Baseline Top-5:

| Rank | Chunk | Page | Score | Content |
|---|---|---|---|---|
| 1 | T2D-009-p001-c002 | 1 | 0.5343 | Chapter intro: ASCVD risk in diabetes |
| 2 | T2D-009-p016-c001 | 16 | 0.4311 | Rec 10.38b (natriuretic peptides) |
| 3 | T2D-009-p029-c004 | 29 | 0.4214 | Reference: albiglutide CV-outcomes citation |
| 4 | T2D-009-p030-c005 | 30 | 0.4206 | Reference: semaglutide HF citation |
| 5 | T2D-009-p018-c003 | 18 | 0.4096 | FDA CVOT guidance discussion |

Relevant evidence and its true rank (controlled full-ranking inspection):

- T2D-009-p008-c003 (recs 10.20–10.23, high-intensity statin therapy):
  rank **42**, score 0.3157
- T2D-009-p008-c004 (rec 10.26 secondary prevention): rank **98**, 0.2423
- Closest relevant supporting chunk: T2D-009-p009-c001 ("beneficial effects
  of statin therapy on ASCVD outcomes"): rank **21**, 0.3577

The gap between rank 5 (0.4096) and the best relevant chunk (0.3577) is far
beyond tie range — this is not a near miss.

Score decomposition of rank-1 chunk: literal buckets 0.5168, collision-only
0.0175. Six tokens — "risk" (0.1139), "in" (0.0788), "type" (0.0701),
"2" (0.0613), "are" (0.0613), "cardiovascular" (0.0526) — contribute **82%**
of the score; the only discriminative query token ("statins") appears in
none of the Top-5 chunks.

Classification: **A — true coverage failure at Top-K=5**, caused by
**B — ranking quality** (generic-token domination) and **C — terminology**
(the query is almost entirely chapter-ubiquitous vocabulary; the
recommendation chunks are long (40–45 rec lines, many numbers/abbreviations
such as LDL/ASCVD/PCSK9/ezetimibe) whose length dilutes their normalized
similarity). Reference chunks additionally share "cardiovascular … type 2
diabetes" literally through citation titles.


### C.3 T2D-010 q1 — "How should chronic kidney disease be screened and monitored in adults with diabetes?" (71 chunks)

Baseline Top-5:

| Rank | Chunk | Page | Score | Content |
|---|---|---|---|---|
| 1 | T2D-010-p012-c003 | 12 | 0.4905 | Reference: DCCT/EDIC citation |
| 2 | T2D-010-p015-c004 | 15 | 0.4826 | Reference: FIGARO-DKD citation |
| 3 | T2D-010-p015-c003 | 15 | 0.4561 | Reference: EMPEROR-Preserved citation |
| 4 | T2D-010-p008-c001 | 8 | 0.4521 | Kidney-benefit body text |
| 5 | T2D-010-p010-c001 | 10 | 0.4358 | MRA-outcomes reference/rec header |

Relevant evidence: the screening recommendations 11.1a/11.1b ("Assess kidney
function with random urine albumin-to-creatinine ratio…", "…monitor urinary
albumin…") live in parsed-page-1 text and are chunked into
**T2D-010-p001-c002**, which ranks **28** (0.3487). Supporting monitoring
content: p006-c001 (rec 11.6c) rank 54, albuminuria-categories table
p002-c001 rank 63.

Score decomposition of rank-1 chunk: literal buckets 0.4770, collision-only
buckets 0.0134. OBSERVED collision mechanism: the query tokens "chronic",
"be", and "screened" hash to the **same 256-dim bucket** (their per-token
attributions are identical, 0.1411 each). A reference chunk that merely
contains the stopword "be" is therefore credited for the query's content
words "screened"/"chronic" without containing them. This is the clearest
hash-collision inflation in the affected set.

Classification: **A — true coverage failure**, driven by
**E — collision/boilerplate inflation** (a stopword bucket shared with
content words lifts citation chunks), with **D — chunking/parsing
interaction** contributing (see C.5).

### C.4 T2D-010 q2 — "When are ACE inhibitors, ARBs, SGLT2 inhibitors, or finerenone recommended for kidney protection in diabetes?" (71 chunks)

Baseline Top-5:

| Rank | Chunk | Page | Score | Content |
|---|---|---|---|---|
| 1 | T2D-010-p011-c003 | 11 | 0.3447 | Pregnancy contraindication for ACEi/ARB/SGLT2i/MRA |
| 2 | T2D-010-p004-c003 | 4 | 0.3385 | Body text, column-interleaved |
| 3 | T2D-010-p014-c006 | 14 | 0.3298 | Reference: FDA drug-safety citation |
| 4 | T2D-010-p015-c006 | 15 | 0.3293 | Reference: semaglutide-dialysis citation |
| 5 | T2D-010-p012-c005 | 12 | 0.3207 | Reference: cystatin-C citation |

Relevant evidence and true ranks: T2D-010-p006-c004 (SGLT2 inhibitor with
ACEi/ARB) rank **12** (0.2926); p006-c003 (ACEi/ARB similar benefits,
albuminuria 30–299 mg/g) rank **13** (0.2924); p006-c001 (rec 11.6c) rank
**20**; p006-c005 rank **23** (0.2647). Finerenone trial/discussion chunks
(p010-c001/c004, p011-c002) rank 25–66. The literal finerenone
recommendation text (11.4-series) could not be located by its label in the
parsed artifact (see C.5).

Score decomposition of rank-1 chunk: literal 0.3447, collision 0.0000 —
pure lexical overlap, including punctuation-attached tokens ("inhibitors,"
matching the query's comma-carrying token).

Classification: **A — true coverage failure** via **B — ranking quality**
(all Top-5 scores 0.32–0.34 compress the relevant chunks at 0.26–0.29 out)
and **E** (citation domination), with **D — parsing interaction**
contributing.

### C.5 Cross-cutting OBSERVED parsing artifact (T2D-010)

The parsed T2D-010 text shows multi-column extraction interleaving, e.g.
T2D-010-p004-c003: "Re- Early changes in kidney function may be mission of

## D. Root-cause analysis

### OBSERVED (measured, reproduced)

1. Replaying the baseline reproduced the recorded validation Top-5 exactly
   for all affected queries — the recorded evidence is trustworthy and the
   pipeline is deterministic.
2. Function-word mass decides ranking in natural-language queries: 76%
   (T2D-006 rank-1: "the"+"of") and 82% (T2D-009 rank-1: "risk/in/type/
   2/are/cardiovascular") of the top score comes from generic tokens.
   The provider applies no stopword removal and no IDF weighting.
3. Reference/citation chunks (228–264 tokens) accumulate shared chapter
   vocabulary in citation titles; 8 of the 20 top-ranked slots across the
   four affected queries are unambiguous reference-list/citation chunks
   (9 counting a citation-header chunk).
4. Hash-bucket collisions merge query content words with stopwords:
   "chronic"+"be"+"screened" share one bucket (identical 0.1411
   contributions), so a citation chunk containing only "be" is credited
   for "screened"/"chronic". Bucket-collision share of top scores:
   0.06/0.44 (T2D-006), 0.02/0.53 (T2D-009), 0.01/0.49 (T2D-010 q1),
   0.00/0.34 (T2D-010 q2) — secondary except when collision merges content
   words with ubiquitous stopwords (T2D-010 q1).
5. Relevant chunks exist in every affected document and are not lost:
   true ranks are 6 (T2D-006, Δscore 0.0018 to rank 5), 21/42/98 (T2D-009),
   28 (T2D-010 q1), 12/13/20 (T2D-010 q2).
6. T2D-010's parsed text contains multi-column interleaving corruption
   (e.g., p004-c003), fragmenting recommendation passages; the 11.4-series
   finerenone recommendation could not be located by label.

### INFERENCE (what the baseline's documented properties explain)

1. All of the above are consistent with the documented design intent of
   `clinivault-baseline-hash-v1` ("NOT semantic", zero dependencies,
   hashed bag-of-words). The behavior is a **representational limitation of
   the baseline, not an implementation bug**: the math behaves exactly as
   specified, and the provider module explicitly defers semantic-model
   choice to a future decision.
2. Length dilution: L2 normalization means long recommendation blocks (full
   of numbers, dosages, abbreviations) carry small per-token weights, while
   shorter or citation-dense chunks with generic terms compete effectively.
3. Query style matters: content-dense keyword queries (T2D-008 q2b,
   T2D-009 q2b) retrieved the relevant chunks in the validation unit;
   generic natural-language phrasings did not. This is the expected
   behavior of an IDF-free lexical model.

### NOT YET VALIDATED

1. Whether the mechanism generalizes beyond 4 forensic cases / 8 documents
   (requires a controlled benchmark; see G).
2. Whether stopword/IDF weighting alone would materially fix the ranking
   (counterfactual not run — out of scope for a diagnosis unit).
3. T2D-010 generation remains blocked by Gemini 429 quota (recorded in the
   validation unit; no provider call was made in this unit, and with Top-5
   known to lack the answer a generation run would not inform the retrieval
   diagnosis).
4. Exact location of the finerenone recommendation text in T2D-010's parsed
   artifact (requires an ingestion-quality review of the multi-column
   parser on this document).

## E. Cross-case pattern

The four affected queries share one mechanism chain:

1. The query's discriminative power is diluted by function words and
   chapter-ubiquitous clinical vocabulary (no stopword/IDF weighting).
2. Citation/reference chunks and thematically-adjacent intro chunks share
   that generic vocabulary literally and win the cosine comparison.
3. The genuinely relevant chunks — often long, number-dense recommendation
   blocks — are normalized downward and land anywhere from rank 6 to rank
   98.
4. Hash collisions add a secondary inflation that becomes decisive only
   when a query's content words collide with stopwords (T2D-010 q1).

The three documents did NOT fail for identical reasons: T2D-006 q2 is a
one-rank near miss amplified by terminology mismatch; T2D-009 q2 and
T2D-010 are full coverage failures with different dominant mechanisms
(genericity vs collision/boilerplate), and T2D-010 additionally suffers a
document-specific extraction artifact.

## F. Impact

- In the 13-query validation, 4 queries (~31%) had relevant evidence
  outside Top-5. In all four the generation layer refused rather than
  hallucinate — so the operational effect of this weakness is **coverage
  loss (no answer)**, not wrong answers. For a clinical tool this failure
  direction is the safe one, but it caps usefulness on reference-heavy
  guideline chapters.
- The weakness is query-style dependent: keyword-style or
  content-detailed phrasings retrieved the relevant evidence even in the
  same documents (T2D-008 q2b, T2D-009 q2b).
- Only four cases were investigated; the fraction should not be
  extrapolated to the whole corpus without a benchmark.

## G. Recommendation

**No retrieval implementation change is justified by this unit alone.**

The evidence justifies exactly one next step: build a small **controlled
retrieval benchmark** — per-document query → relevant-chunk labels for the
8 ingested documents, measured offline (Top-5 hit rate and MRR through the
existing `search` seam, no API cost) — and use it to adjudicate between the
candidate mitigations the mechanisms point to:

1. lexical weighting (stopword removal / IDF) inside or beside the hash
   baseline,
2. a semantic embedding provider via the existing provider seam,
3. structure-aware filtering of reference-list pages.

The provider seam makes option 2 cheap to test; the benchmark makes the
choice evidence-driven rather than anecdotal. Separately, the T2D-010
multi-column extraction interleaving should be reviewed in a dedicated
ingestion-quality unit (it affects parsed-text quality generally, not only
retrieval), and T2D-010 generation should be completed once Gemini quota
allows.

albuminuria may occur sponta- detected by increases in albuminuria…" — two
columns merged mid-sentence. This fragments recommendation passages and
damages chunk coherence in the most-affected document. It is a
document-specific ingestion artifact (multi-column ADA chapter layout),
recorded in the engineering log; it is not a retrieval-layer defect.
