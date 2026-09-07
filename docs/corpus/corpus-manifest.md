# Corpus Manifest

One record per document. If a document is in `data/raw/`, it must be here.
This is how we remember why each document exists in the corpus.

| Field | Description |
|---|---|
| Document ID | Stable ID, also used by the ingestion pipeline |
| Title | Document title |
| Source | Publisher / journal / organization |
| Source URL / reference | Where the document came from (URL or citation) |
| Source identifier | PMID, PMCID, or DOI where available |
| Clinical topic | The specific T2D topic this document covers |
| Questions it helps answer | What clinical questions this document supports |
| Why the source is trusted | The reason this source is credible for this topic |
| Domain | Healthcare domain (currently: Type 2 Diabetes) |
| Document type | Clinical guideline / systematic review / research paper / organization guidance |
| Publication date | As stated in the document |
| Last updated | Update date, where the source provides one |
| Version | Where the source provides one |
| Date added | When we added it to the corpus |
| Ingestion date | When it was ingested (filled by the pipeline later) |
| License / reuse | License or usage terms where known |
| Filename | Path under `data/raw/` |
| Pages | Page count |
| Technical characteristics | text-based / scanned / multi-column / contains tables / long / references-heavy |
| Expected complexity | simple / moderate / complex |
| Known characteristics | Anything tricky: bad text layer, huge tables, embedded images with text, etc. |
| Reason for inclusion | The honest answer to "why is this here?" — every document earns its place |

## Stage 1 — Clean Baseline Corpus (target: 5–10 documents)

(add one row per document as they are selected; columns as defined above)

## Stage 2 — Domain Evidence Corpus (target: 30–50 documents)

(add rows when Stage 2 begins; previous guideline versions go here where
legally available, with version and publication/updated dates recorded)

## Stage 3 — Stress and Evaluation Corpus (100+ documents)

(add rows when Stage 3 begins; duplicates, near-duplicates, and
conflicting-evidence documents go here deliberately, flagged in
Known characteristics — these become future Errata test cases)

