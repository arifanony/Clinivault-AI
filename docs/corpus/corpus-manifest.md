# Corpus Manifest

One record per document. If a document is in `data/raw/`, it must be here.
This is how we remember why each document exists in the corpus.

| Field | Description |
|---|---|
| Document ID | Stable ID, also used by the ingestion pipeline |
| Title | Document title |
| Source | Publisher / journal / organization |
| Source identifier | PMID, PMCID, or DOI where available |
| Domain | Healthcare domain covered |
| Document type | Guideline / review / research paper / patient info / ... |
| Publication date | As stated in the document |
| Date added | When we added it to the corpus |
| Ingestion date | When it was ingested (filled by the pipeline later) |
| Version | Where the source provides one |
| License / reuse | License or usage terms where known |
| Filename | Path under `data/raw/` |
| Pages | Page count |
| Reason for inclusion | The honest answer to "why is this here?" |
| Expected complexity | simple / multi-column / table-heavy / long / complex |
| Known characteristics | Anything tricky: bad text layer, huge tables, embedded images with text, etc. |

## Stage 1 — Parsing Validation (target: 5–10 documents)

| Document ID | Title | Source | Identifier | Domain | Type | Pub date | Added | License | Filename | Pages | Reason for inclusion | Expected complexity | Known characteristics |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## Stage 2 — Domain Corpus (target: 30–50 documents)

(same columns as Stage 1 — add the table when Stage 2 begins)

## Stage 3 — Scale Testing (100+ documents)

(same columns — add the table when Stage 3 begins; duplicates and
near-duplicates go here deliberately, flagged in Known characteristics)
