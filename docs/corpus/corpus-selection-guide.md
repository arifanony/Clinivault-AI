# Corpus Selection Guide

The goal is not collecting the maximum number of PDFs. The goal is a
deliberately curated corpus where every document earns its place.

Before adding a candidate document, walk through this checklist:

## Relevance and Credibility

- **Domain relevance** — Does it actually cover the healthcare domain we're
  building for? A tangentially related paper is corpus noise.
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
  In Stage 1 we *want* variety; in Stage 2 we want coverage of the domain.
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
