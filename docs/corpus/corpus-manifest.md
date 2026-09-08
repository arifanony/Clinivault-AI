# Corpus Manifest

One record per document. If a document is in `data/raw/`, it must be here.
This is how we remember why each document exists in the corpus.

> **Relationship to the acquisition input:** `clinivault_initial_corpus_manifest.md`
> (repo root) is the curated acquisition/source list — the input that says *what we
> intend to acquire and from where*. **This file is the source of truth for documents
> actually present in the corpus.** A document gets a full record here only after it
> has been downloaded and validated; blocked or unobtainable sources get an honest
> status record instead, and are never substituted with a different paper.

| Field | Description |
|---|---|
| Document ID | Stable ID, also used by the ingestion pipeline |
| Title | Document title |
| Authors / Organization | Named authors, or the issuing organization where authorship is corporate |
| Source | Publisher / journal / organization |
| Source URL / reference | Where the document came from (URL or citation) |
| PDF / full-text URL used | The exact legitimate route the file was actually downloaded from (may differ from the curated input when the input's route was blocked) |
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
| Acquisition date | When the file was actually downloaded and validated |
| Ingestion date | When it was ingested (filled by the pipeline later) |
| License / reuse | License or usage terms where known |
| Filename | Path under `data/raw/` |
| Pages | Page count |
| Technical characteristics | text-based / scanned / multi-column / contains tables / long / references-heavy |
| Expected complexity | simple / moderate / complex |
| Known characteristics | Anything tricky: bad text layer, huge tables, embedded images with text, etc. |
| Reason for inclusion | The honest answer to "why is this here?" — every document earns its place |
| SHA-256 | Content checksum computed at acquisition time |
| Acquisition status | obtained / blocked-access / not-obtained / validation-failed |


## Stage 1 — Clean Baseline Corpus (target: 5–10 documents)

Acquisition date for all records below: **2026-09-08**. Validation method: magic
bytes (`%PDF`), structural open check (`startxref` + `%%EOF`), and page count read
from `/Type /Page` objects (including decompressed streams). A PDF-library
re-verification of structure and page count happens at ingestion time.

### T2D-002 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-002 |
| Title | Prediabetes and Type 2 Diabetes: Screening |
| Authors / Organization | U.S. Preventive Services Task Force (USPSTF) |
| Source | USPSTF (recommendation statement) |
| Source URL / reference | https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/screening-for-prediabetes-and-type-2-diabetes |
| PDF / full-text URL used | https://www.uspreventiveservicestaskforce.org/home/getfilebytoken/g2bEcQW6ae_NTFZ9KUxT_t (tokenized link from the curated input — may expire; official page above is the stable reference) |
| Source identifier | — |
| Clinical topic | Screening for prediabetes and type 2 diabetes |
| Questions it helps answer | Which populations to screen, which screening tests, screening intervals |
| Why the source is trusted | Independent U.S. federal preventive-services task force; recommendation statements are U.S. government works |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline / preventive recommendation |
| Publication date | 2021 |
| Last updated | — |
| Version | 2021 final recommendation statement |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | U.S. government work — public domain (verify statement text on document at ingestion) |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-002-uspstf-2021-prediabetes-t2d-screening.pdf` |
| Pages | 8 |
| Technical characteristics | text-based PDF (`%PDF-1.6`, 172,732 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | simple–moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Independent guideline/recommendation source for screening; enables evidence comparison against ADA |
| SHA-256 | D523E5447FE6592727B1C66A5F7D9F256042011CFB410C93695AF1C08F8F451F |
| Acquisition status | obtained |


### T2D-003 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-003 |
| Title | Diagnostic accuracy of tests for type 2 diabetes and prediabetes: A systematic review and meta-analysis |
| Authors / Organization | Kaur et al. |
| Source | PLOS ONE (publisher of record) |
| Source URL / reference | https://pubmed.ncbi.nlm.nih.gov/33216783/ · https://doi.org/10.1371/journal.pone.0242415 |
| PDF / full-text URL used | https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0242415&type=printable — PLOS publisher route; the curated input's PMC direct-PDF link returned an HTML interstitial instead of a PDF |
| Source identifier | PMID 33216783 · PMCID PMC7678987 · DOI 10.1371/journal.pone.0242415 |
| Clinical topic | Diagnostic accuracy of screening/diagnostic tests for T2D and prediabetes |
| Questions it helps answer | Comparing sensitivity/specificity of HbA1c and fasting plasma glucose in undiagnosed adults |
| Why the source is trusted | Peer-reviewed open-access systematic review and meta-analysis in PLOS ONE |
| Domain | Type 2 Diabetes |
| Document type | Systematic review + meta-analysis |
| Publication date | 2020 (December; exact day to verify against PDF at ingestion) |
| Last updated | — |
| Version | — |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | PLOS ONE — open access, CC BY (verify exact license statement on document at ingestion) |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-003-kaur-2020-diagnostic-accuracy-sr-meta.pdf` |
| Pages | 19 |
| Technical characteristics | text-based PDF (`%PDF-1.6`, 1,498,978 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Directly evaluates diagnostic accuracy of screening tests; foundational (older) evidence for current-vs-older comparison |
| SHA-256 | 84E456E4B8A1C944825FC0CBE996575F683F52ABBC1B95EDD66D3C6493211138 |
| Acquisition status | obtained |


### T2D-007 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-007 |
| Title | Newer Pharmacologic Treatments in Adults With Type 2 Diabetes: A Clinical Guideline |
| Authors / Organization | American College of Physicians (ACP); named authors to verify against PDF at ingestion |
| Source | ACP clinical guideline (full text deposited in PMC) |
| Source URL / reference | https://pubmed.ncbi.nlm.nih.gov/38639546/ |
| PDF / full-text URL used | https://europepmc.org/articles/PMC11614146?pdf=render — Europe PMC legitimate render route; the curated input's PMC direct-PDF route returned an HTML interstitial instead of a PDF |
| Source identifier | PMID 38639546 · PMCID PMC11614146 · DOI 10.7328/M23-2788 |
| Clinical topic | Pharmacological treatment of T2D (newer agents) |
| Questions it helps answer | Treatment selection considerations; independent-of-ADA guideline perspective for evidence-conflict/consensus questions |
| Why the source is trusted | National professional society clinical guideline, peer-reviewed, open access via PMC |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2024 |
| Last updated | — |
| Version | — |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | Open-access full text via PMC (exact license terms to verify on document at ingestion) |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-007-acp-2024-newer-pharmacologic-t2d.pdf` |
| Pages | 19 |
| Technical characteristics | text-based PDF (`%PDF-1.5`, 1,004,874 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Independent guideline perspective for comparison with ADA; evidence-conflict/consensus test material |
| SHA-256 | FE9B91697FABF5C687A27BBFE8E4CC73BB0B7888344177D23A7ACC4991C45592 |
| Acquisition status | obtained |


### T2D-005 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-005 |
| Title | Standards of Care in Diabetes — 2026, Section 6: Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises |
| Authors / Organization | American Diabetes Association (ADA) |
| Source | *Diabetes Care* 49(Supplement 1), ADA (official publisher) |
| Source URL / reference | https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/6-Glycemic-Goals-Hypoglycemia-and-Hyperglycemic |
| PDF / full-text URL used | https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S132/848848/dc26s006.pdf (manual browser download from the official route; automated download was bot-blocked) |
| Source identifier | — (section DOI to record at ingestion from the document) |
| Clinical topic | Glycemic management — targets, monitoring, hypoglycemia/hyperglycemic crises |
| Questions it helps answer | General glycemic targets, monitoring concepts, and management considerations |
| Why the source is trusted | Primary national guideline body for diabetes care; current 2026 standards |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2026 (*Diabetes Care* 49 Suppl 1; exact date to verify against PDF at ingestion) |
| Last updated | — |
| Version | 2026 Standards of Care |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | © American Diabetes Association; free-to-read on the official site; reuse/processing terms to be confirmed at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-005-ada-2026-soc-06-glycemic-goals.pdf` (corrected from a `…goals.pdf.pdf` double extension during validation) |
| Pages | 18 |
| Technical characteristics | text-based PDF (948,730 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Current guideline source for glycemic targets and monitoring questions (curated input, family 2: glycemic management) |
| SHA-256 | 1F289B37628D109A8CE50751409F8C6AF7047B5E5CCE723BF2FFFA576DFF21F1 |
| Acquisition status | obtained |


### T2D-006 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-006 |
| Title | Standards of Care in Diabetes — 2026, Section 9: Pharmacologic Approaches to Glycemic Treatment |
| Authors / Organization | American Diabetes Association (ADA) |
| Source | *Diabetes Care* 49(Supplement 1), ADA (official publisher) |
| Source URL / reference | https://diabetesjournals.org/care/article/49/Supplement_1/S183/163934/9-Pharmacologic-Approaches-to-Glycemic-Treatment |
| PDF / full-text URL used | https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S183/848878/dc26s009.pdf (manual browser download from the official route; automated download was bot-blocked) |
| Source identifier | — (section DOI to record at ingestion from the document) |
| Clinical topic | Pharmacological treatment of T2D |
| Questions it helps answer | Medication classes, treatment selection considerations, treatment strategy |
| Why the source is trusted | Primary national guideline body for diabetes care; current 2026 standards |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2026 (*Diabetes Care* 49 Suppl 1; exact date to verify against PDF at ingestion) |
| Last updated | — |
| Version | 2026 Standards of Care |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | © American Diabetes Association; free-to-read on the official site; reuse/processing terms to be confirmed at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-006-ada-2026-soc-09-pharmacologic.pdf` |
| Pages | 33 |
| Technical characteristics | text-based PDF (1,547,487 bytes); long document; detailed layout inspection deferred to ingestion |
| Expected complexity | moderate–complex |
| Known characteristics | none recorded yet |
| Reason for inclusion | Current guideline source for medication selection and treatment strategy (curated input, family 3: pharmacological treatment) |
| SHA-256 | 80CB995FFA59A092BE7F7B913AA316128E9BC7BA31CC7B3737407009EB6EBD1C |
| Acquisition status | obtained |


### T2D-009 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-009 |
| Title | Standards of Care in Diabetes — 2026, Section 10: Cardiovascular Disease and Risk Management |
| Authors / Organization | American Diabetes Association (ADA) |
| Source | *Diabetes Care* 49(Supplement 1), ADA (official publisher) |
| Source URL / reference | https://diabetesjournals.org/care/article/49/Supplement_1/S216/163933/10-Cardiovascular-Disease-and-Risk-Management |
| PDF / full-text URL used | https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S216/848870/dc26s010.pdf (manual browser download from the official route; automated download was bot-blocked) |
| Source identifier | — (section DOI to record at ingestion from the document) |
| Clinical topic | Cardiovascular considerations in T2D — CVD and risk management |
| Questions it helps answer | T2D together with cardiovascular risk questions |
| Why the source is trusted | Primary national guideline body for diabetes care; current 2026 standards |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2026 (*Diabetes Care* 49 Suppl 1; exact date to verify against PDF at ingestion) |
| Last updated | — |
| Version | 2026 Standards of Care |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | © American Diabetes Association; free-to-read on the official site; reuse/processing terms to be confirmed at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-009-ada-2026-soc-10-cardiovascular.pdf` |
| Pages | 30 |
| Technical characteristics | text-based PDF (1,535,506 bytes); long document; detailed layout inspection deferred to ingestion |
| Expected complexity | moderate–complex |
| Known characteristics | none recorded yet |
| Reason for inclusion | Current guideline source for cardiovascular-risk questions in T2D (curated input, family 4: cardiovascular and kidney considerations) |
| SHA-256 | 5E4DBC63E3DC5E970C1100C1ED3FD8EF8047766E8C8E071247B2550974CF62F1 |
| Acquisition status | obtained |


### T2D-010 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-010 |
| Title | Standards of Care in Diabetes — 2026, Section 11: Chronic Kidney Disease and Risk Management |
| Authors / Organization | American Diabetes Association (ADA) |
| Source | *Diabetes Care* 49(Supplement 1), ADA (official publisher) |
| Source URL / reference | https://diabetesjournals.org/care/article/49/Supplement_1/S246/163935/11-Chronic-Kidney-Disease-and-Risk-Management |
| PDF / full-text URL used | https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S246/848818/dc26s011.pdf (manual browser download from the official route; automated download was bot-blocked) |
| Source identifier | — (section DOI to record at ingestion from the document) |
| Clinical topic | Kidney considerations in T2D — CKD and risk management |
| Questions it helps answer | T2D together with kidney-related clinical questions |
| Why the source is trusted | Primary national guideline body for diabetes care; current 2026 standards |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2026 (*Diabetes Care* 49 Suppl 1; exact date to verify against PDF at ingestion) |
| Last updated | — |
| Version | 2026 Standards of Care |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | © American Diabetes Association; free-to-read on the official site; reuse/processing terms to be confirmed at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-010-ada-2026-soc-11-ckd.pdf` |
| Pages | 15 |
| Technical characteristics | text-based PDF (1,258,833 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Current guideline source for kidney-risk and CKD questions (curated input, family 4: cardiovascular and kidney considerations) |
| SHA-256 | 51BA72330499096A818C00CC2A88D0E7DA067A2487B2C29B77F269F69D8CD536 |
| Acquisition status | obtained |


### T2D-001 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-001 |
| Title | Standards of Care in Diabetes — 2026, Section 2: Diagnosis and Classification of Diabetes |
| Authors / Organization | American Diabetes Association (ADA) |
| Source | *Diabetes Care* 49(Supplement 1), ADA (official publisher) |
| Source URL / reference | https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes |
| PDF / full-text URL used | https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S27/848854/dc26s002.pdf (re-acquired copy downloaded manually from the official route by the curator; automated download is bot-blocked) |
| Source identifier | DOI 10.2337/dc26-S002 (observed in the parsed page-1 text of the acquired PDF) |
| Clinical topic | Diagnosis and classification of diabetes |
| Questions it helps answer | Clinical definitions, diagnostic criteria (A1C, fasting plasma glucose, 2-hour OGTT), confirmatory testing, classification |
| Why the source is trusted | Primary national guideline body for diabetes care; current 2026 standards |
| Domain | Type 2 Diabetes |
| Document type | Clinical guideline |
| Publication date | 2026 (January) — *Diabetes Care* 49(Supplement 1), observed in the parsed page-1 text ("Diabetes Care Volume 49, Supplement 1, January 2026"; pp. S27–S49) |
| Last updated | — |
| Version | 2026 Standards of Care |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 (re-acquisition) |
| Ingestion date | 2026-09-08 (parsed; ingestion pipeline v0.1.0) |
| License / reuse | © American Diabetes Association; free-to-read on the official site; reuse/processing terms to be confirmed at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-001-ada-2026-soc-02-diagnosis-classification.pdf` |
| Pages | 23 |
| Technical characteristics | text-based PDF (`%PDF-1.6`, 1,054,611 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Primary guideline source for diagnosis/classification questions (curated input, family 1: diagnosis and classification) |
| SHA-256 | 97D8CC13CD7356BE84B148A9FFF47C6E115131B9657DD0A746A834F2C70017B8 |
| Acquisition status | obtained (re-acquired canonical copy) |
| Provenance note | The first validated copy of this document was lost in a file-handling incident during the 2026-09-08 correction (duplicate-content mix-up followed by an accidental deletion; see engineering log [`2026-09-08-duplicate-file-content-mismatch.md`](../../engineering-log/2026-09-08-duplicate-file-content-mismatch.md)). This record describes the re-acquired canonical copy, manually downloaded from the official ADA route and verified (real PDF, opens, 37 pages, SHA-256 above) before acceptance. Its byte stream differs from the lost copy despite identical document content and length — the earlier hash is retained only as historical incident information in the engineering log. |




### T2D-004 — blocked-access (manual download required)

| Field | Value |
|---|---|
| Document ID | T2D-004 |
| Title | Reassessment of the Diagnostic Accuracy of HbA1c and Glucose for Type 2 Diabetes: A Systematic Review and Meta-Analysis of Observational Studies |
| Authors / Organization | Baechle et al. |
| Source | *Diabetes/Metabolism Research and Reviews* (Wiley) |
| Source URL / reference | https://pubmed.ncbi.nlm.nih.gov/41889232/ · https://doi.org/10.1002/dmrr.70160 |
| Source identifier | PMID 41889232 · DOI 10.1002/dmrr.70160 |
| Clinical topic | Diagnostic accuracy — newer evidence (HbA1c vs glucose measures) |
| Acquisition status | **blocked-access** |
| Reason | The Wiley `pdfdirect` route returned **HTTP 403** (bot protection/paywall) on 2026-09-08; protection was **not** bypassed. Confirmed via the NCBI ID converter API that this article is **not in PMC** (no PMCID), so no open-access full text is available through legitimate automated routes. The curated input itself directs to the publisher/PubMed legitimate route only. |
| Required manual action | If you have legitimate access (publisher subscription or open-access copy), download the PDF from the DOI route in a browser and place it in `data/raw/stage-1-clean-baseline-corpus/` as `T2D-004-baechle-2026-hba1c-glucose-diagnostic-accuracy.pdf`; validation and full record will follow. Do not substitute a different paper. |

### T2D-008 — obtained

| Field | Value |
|---|---|
| Document ID | T2D-008 |
| Title | Medications for adults with type 2 diabetes: a living systematic review and network meta-analysis |
| Authors / Organization | Nong et al.; full author list to verify against PDF at ingestion |
| Source | *The BMJ* (official publisher) |
| Source URL / reference | https://pubmed.ncbi.nlm.nih.gov/40813122/ · https://doi.org/10.1136/bmj-2024-083039 |
| PDF / full-text URL used | Manual browser download from the official BMJ route (https://www.bmj.com/content/389/bmj-2024-083039) by the curator; automated routes were bot-blocked (HTTP 403) during acquisition, and the article is not in PMC |
| Source identifier | PMID 40813122 · DOI 10.1136/bmj-2024-083039 |
| Clinical topic | Pharmacological treatment — broad evidence synthesis (multiple drug classes and outcomes) |
| Questions it helps answer | Comparison and evidence-synthesis questions across drug classes |
| Why the source is trusted | Large, current living systematic review and network meta-analysis in a top-tier general medical journal |
| Domain | Type 2 Diabetes |
| Document type | Living systematic review + network meta-analysis |
| Publication date | 2025 (BMJ; exact volume/e-locator to verify against PDF at ingestion) |
| Last updated | Living review — update status to check at ingestion |
| Version | — |
| Date added | 2026-09-08 |
| Acquisition date | 2026-09-08 |
| Ingestion date | — (pending) |
| License / reuse | Likely open access (BMJ research); exact license terms to verify on document at ingestion |
| Filename | `data/raw/stage-1-clean-baseline-corpus/T2D-008-nong-2025-t2d-medications-living-nma.pdf` |
| Pages | 16 |
| Technical characteristics | text-based PDF (795,139 bytes); detailed layout inspection deferred to ingestion |
| Expected complexity | moderate |
| Known characteristics | none recorded yet |
| Reason for inclusion | Large, current evidence synthesis covering multiple drug classes and outcomes; comparison and evidence-synthesis retrieval test material (curated input, family 5) |
| SHA-256 | 5B3ADB77392885E2893DFF6A2711FDE1F9107926752AD7953F7480DD1C2FDFEB |
| Acquisition status | obtained (recovered from earlier blocked-access after manual download) |



## Stage 2 — Domain Evidence Corpus (target: 30–50 documents)

(add rows when Stage 2 begins; previous guideline versions go here where
legally available, with version and publication/updated dates recorded)

## Stage 3 — Stress and Evaluation Corpus (100+ documents)

(add rows when Stage 3 begins; duplicates, near-duplicates, and
conflicting-evidence documents go here deliberately, flagged in
Known characteristics — these become future Errata test cases)

