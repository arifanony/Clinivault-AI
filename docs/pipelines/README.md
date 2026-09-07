# Pipelines

Status: none written yet. Pipeline docs are created as pipelines are actually
built, using [`docs/templates/pipeline-doc-template.md`](../templates/pipeline-doc-template.md).

Planned documents (each written when that pipeline exists, not before):

- ingestion (this one gets extra detail — every block explained: why it
  exists, input, output, alternatives, failure modes, validation, evidence)
- parsing
- cleaning and normalization
- metadata creation
- chunking
- embedding
- vector storage
- retrieval
- context construction
- generation
- citations
- execution recording

No pipeline is treated as a black box: every doc shows INPUT → steps → OUTPUT
and answers what can fail, how we notice, and what evidence it produces.

