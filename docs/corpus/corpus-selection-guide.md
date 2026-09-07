# Corpus Selection Guide

The goal is not collecting the maximum number of PDFs. The goal is a
deliberately curated corpus where every document earns its place.

## The Domain: Type 2 Diabetes

Every document in the corpus must be relevant to **Type 2 Diabetes**. That's
the MVP domain (see [DECISION-003](../decisions/DECISION-003-product-direction.md)).
A beautiful, clean, trustworthy PDF on an unrelated condition is still corpus
noise for now.

Useful clinical questions to keep in mind while selecting (examples that guide
selection — not questions we hard-code into the system):

- What do current guidelines recommend for managing Type 2 Diabetes?
- What are treatment considerations for patients with Type 2 Diabetes and
  cardiovascular risk?
- What changed between an older and a newer guideline?
- What evidence supports a particular treatment approach?
- How do recommendations differ between trusted clinical sources?

## The Selection Rule: Ten Questions

Before a document joins the corpus, we can answer all of these:

1. What clinical topic does this document cover?
2. What type of clinical questions could it help answer?
3. Who published it?
4. Why is the source considered relevant or trustworthy?
5. Publication date?
6. Last updated date, if available?
7. Document version, if available?
8. Document type (clinical guideline, systematic review, research paper,
   healthcare organization guidance)?
9. Technical characteristics (text-based or scanned PDF, multi-column,
   contains tables, long document, references-heavy)?
10. **Why are we adding this document to the corpus?**

Question 10 is the one that matters most. Every document earns its place.

## Relevance and Credibility

- **Domain relevance** — Does it actually cover Type 2 Diabetes or a topic our
  clinical questions need (e.g., cardiovascular risk management in T2D)?
- **Source credibility** — Published guideline, peer-reviewed journal, or
  reputable health organization? Be more careful with preprints, vendor
  whitepapers, and anonymous web content.
- **Publication date** — Is it current enough to be useful? (Older documents
  are still valuable — deliberately — for testing how the system handles
  outdated vs. current guidance in Stage 3.)

## Document Quality and Structure

- **PDF quality** — Is the text layer real text, or a scan? Scanned PDFs need
  OCR, which is a different problem we're not solving in Stage 1. Reject
  unclear scans unless testing OCR is the explicit point.
- **Structure complexity** — Does it stress a capability we haven't validated?
  Multi-column, tables, figures with captions, many sections, long documents.
  Stage 1 wants clean and trusted; Stage 3 deliberately wants the hard ones.
- **Tables** — Does it contain clinically meaningful tables? Tables are where
  parsers usually fail, so note it in the manifest.
- **Length** — Mix short and long documents. Very short docs don't stress
  chunking; 500-page docs stress page tracking.

## Practical and Legal

- **License / reuse** — Do we have the right to keep and process this PDF?
  Prefer open-access. Note the license in the manifest; if unclear, don't add it.
- **Metadata availability** — Is there a PMID, PMCID, or DOI we can record?
  These make the corpus verifiable and the manifests meaningful.

## The Deciding Question

**What does this document add that the corpus doesn't already have?**

If the honest answer is "nothing, we already have three like it" — skip it.
Duplicates are deliberately introduced only in Stage 3, as test cases, and
they get flagged in the manifest.

