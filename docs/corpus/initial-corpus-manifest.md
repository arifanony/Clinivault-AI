# Clinivault AI - Initial Type 2 Diabetes Corpus

Purpose: a small, deliberate MVP corpus for testing ingestion, metadata, provenance, retrieval, and answer grounding.

Do NOT treat this as a complete medical library. Start with these documents, verify access/licensing, and expand later.

## 1. Diagnosis and classification - primary guideline
**American Diabetes Association (ADA), Standards of Care in Diabetes - 2026, Section 2: Diagnosis and Classification of Diabetes**

Official article:
https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes

Official PDF:
https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S27/848854/dc26s002.pdf

Why included:
- Current 2026 ADA diagnostic/classification guidance.
- Covers A1C, fasting plasma glucose, 2-hour OGTT, confirmatory testing, and classification.
- Primary guideline source for diagnosis questions.

## 2. Screening - primary preventive guideline
**U.S. Preventive Services Task Force (USPSTF), Prediabetes and Type 2 Diabetes: Screening - 2021**

Official page:
https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/screening-for-prediabetes-and-type-2-diabetes

PDF:
https://www.uspreventiveservicestaskforce.org/home/getfilebytoken/g2bEcQW6ae_NTFZ9KUxT_t

Why included:
- Independent guideline/recommendation source for screening.
- Useful for evidence comparison against ADA.
- Covers population selection, screening tests, and screening intervals.

## 3. Diagnostic accuracy - foundational systematic review
**Kaur et al., 2020, Diagnostic accuracy of tests for type 2 diabetes and prediabetes: A systematic review and meta-analysis**

PubMed:
https://pubmed.ncbi.nlm.nih.gov/33216783/

Full text (PMC):
https://pmc.ncbi.nlm.nih.gov/articles/PMC7678987/

PDF:
https://pmc.ncbi.nlm.nih.gov/articles/PMC7678987/pdf/pone.0242415.pdf

PMID: 33216783
PMCID: PMC7678987
DOI: 10.1371/journal.pone.0242415

Why included:
- Directly evaluates diagnostic accuracy of screening tests in previously undiagnosed adults.
- Useful for retrieval questions comparing sensitivity/specificity of HbA1c and fasting plasma glucose.

## 4. Diagnostic accuracy - newer evidence
**Baechle et al., 2026, Reassessment of the Diagnostic Accuracy of HbA1c and Glucose for Type 2 Diabetes: A Systematic Review and Meta-Analysis of Observational Studies**

PubMed:
https://pubmed.ncbi.nlm.nih.gov/41889232/

DOI:
https://doi.org/10.1002/dmrr.70160

Why included:
- Newer evidence than the 2020 review.
- Direct comparison of HbA1c, fasting plasma glucose, and 1-hour plasma glucose against the 2-hour plasma glucose standard.
- Important for testing current-vs-older evidence retrieval.

Note: use the legitimate full-text route provided by PubMed/publisher rather than third-party copies.

## 5. Glycemic management
**ADA, Standards of Care in Diabetes - 2026, Section 6: Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises**

Official article:
https://diabetesjournals.org/care/article/49/Supplement_1/S132/163927/6-Glycemic-Goals-Hypoglycemia-and-Hyperglycemic

Official PDF:
https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S132/848848/dc26s006.pdf

Why included:
- Current guideline source for glycemic targets and monitoring questions.

## 6. Pharmacological treatment
**ADA, Standards of Care in Diabetes - 2026, Section 9: Pharmacologic Approaches to Glycemic Treatment**

Official article:
https://diabetesjournals.org/care/article/49/Supplement_1/S183/163934/9-Pharmacologic-Approaches-to-Glycemic-Treatment

Official PDF:
https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S183/848878/dc26s009.pdf

Why included:
- Current guideline source for medication selection and treatment strategy.

## 7. Pharmacological treatment - independent guideline
**American College of Physicians (ACP), 2024, Newer Pharmacologic Treatments in Adults With Type 2 Diabetes: A Clinical Guideline**

PubMed:
https://pubmed.ncbi.nlm.nih.gov/38639546/

PMID: 38639546
PMCID: PMC11614146
DOI: 10.7328/M23-2788

Why included:
- Independent guideline perspective for comparison with ADA.
- Useful for evidence-conflict/consensus questions.

## 8. Pharmacological treatment - broad evidence synthesis
**Nong et al., 2025, Medications for adults with type 2 diabetes: a living systematic review and network meta-analysis**

PubMed:
https://pubmed.ncbi.nlm.nih.gov/40813122/

PMID: 40813122
DOI: 10.1136/bmj-2024-083039

Why included:
- Large, current evidence synthesis covering multiple drug classes and outcomes.
- Useful for comparison and evidence-synthesis retrieval tests.

## 9. Cardiovascular considerations
**ADA, Standards of Care in Diabetes - 2026, Section 10: Cardiovascular Disease and Risk Management**

Official article:
https://diabetesjournals.org/care/article/49/Supplement_1/S216/163933/10-Cardiovascular-Disease-and-Risk-Management

Official PDF:
https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S216/848870/dc26s010.pdf

Why included:
- Current guideline source for cardiovascular-risk questions in type 2 diabetes.

## 10. Kidney considerations
**ADA, Standards of Care in Diabetes - 2026, Section 11: Chronic Kidney Disease and Risk Management**

Official article:
https://diabetesjournals.org/care/article/49/Supplement_1/S246/163935/11-Chronic-Kidney-Disease-and-Risk-Management

Official PDF:
https://diabetesjournals.org/care/article-pdf/49/Supplement_1/S246/848818/dc26s011.pdf

Why included:
- Current guideline source for kidney-risk and CKD questions.

---

# MVP collection rule

Keep this first corpus deliberately small. Do not download dozens of random papers.

The initial corpus is intended to cover:
1. Diagnosis and classification
2. Screening
3. Glycemic management
4. Pharmacological treatment
5. Cardiovascular considerations
6. Kidney considerations
7. Evidence comparison and synthesis

Use official publisher/organization sources or legitimate PubMed/PMC full-text routes. Do not use Scribd, StudyLib, random mirrors, or other unauthorized copies.

For each acquired document, record:
- document_id
- title
- authors/organization
- source
- source_url
- full_text_url or pdf_url
- PMID / PMCID / DOI where applicable
- document_type
- publication_date
- last_updated (when applicable)
- topic
- file_name
- license/reuse notes
- acquisition_date
- checksum/content hash after download
- page count after download
- notes on tables, figures, columns, scans, or unusual PDF structure
