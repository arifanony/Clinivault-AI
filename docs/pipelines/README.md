# Pipelines

Status: ingestion parsing implemented for the first document (T2D-001) —
see [`ingestion-parsing.md`](./ingestion-parsing.md); baseline structural
chunking and baseline embedding generation implemented — see
[`embedding-baseline.md`](./embedding-baseline.md); baseline vector
storage and similarity retrieval implemented — see
[`retrieval-baseline.md`](./retrieval-baseline.md); baseline context
construction implemented — see
[`context-construction.md`](./context-construction.md). Further pipeline
docs are created as pipelines are actually built, using
[`docs/templates/pipeline-doc-template.md`](../templates/pipeline-doc-template.md).

Planned documents (each written when that pipeline exists, not before):

- ingestion (this one gets extra detail — every block explained: why it
  exists, input, output, alternatives, failure modes, validation, evidence)
- parsing
- cleaning and normalization
- metadata creation
- generation
- citations
- execution recording

No pipeline is treated as a black box: every doc shows INPUT → steps → OUTPUT
and answers what can fail, how we notice, and what evidence it produces.
