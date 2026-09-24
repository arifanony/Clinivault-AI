# Pipelines

Status: ingestion parsing implemented and applied to all nine obtained
Stage-1 documents — see [`ingestion-parsing.md`](./ingestion-parsing.md);
baseline grounded generation implemented — see
[`generation-baseline.md`](./generation-baseline.md); baseline structural
chunking and baseline embedding generation implemented — see
[`embedding-baseline.md`](./embedding-baseline.md); baseline vector
storage and similarity retrieval implemented — see
[`retrieval-baseline.md`](./retrieval-baseline.md); baseline context
construction implemented — see
[`context-construction.md`](./context-construction.md); end-to-end trace
observability implemented — see [`retrieval-baseline.md`](./retrieval-baseline.md),
[`context-construction.md`](./context-construction.md), and
[`generation-baseline.md`](./generation-baseline.md); observability UI V1
(manual query mode, debug console) implemented — see
[`observability-ui.md`](./observability-ui.md); T2D-002 document
generalization validated — see
[`document-generalization-validation.md`](./document-generalization-validation.md);
broader corpus generalization validated across the 9 available documents — see
[`corpus-generalization-validation.md`](./corpus-generalization-validation.md);
validated artifacts persisted durably — see
[`artifact-persistence.md`](./artifact-persistence.md); baseline retrieval
ranking weakness investigated — see
[`retrieval-ranking-investigation.md`](./retrieval-ranking-investigation.md);
controlled baseline retrieval benchmark established — see
[`retrieval-baseline-benchmark.md`](./retrieval-baseline-benchmark.md); benchmark
measured results recorded — see
[`retrieval-baseline-benchmark-results.md`](./retrieval-baseline-benchmark-results.md);
representative T2D-001 pipeline evaluation recorded — see
[`representative-evaluation.md`](./representative-evaluation.md); controlled
retrieval comparison (baseline vs term-weighted vs semantic) run — see
[`retrieval-controlled-comparison.md`](./retrieval-controlled-comparison.md);
T2D-010 ingestion-quality isolation investigated — see
[`t2d-010-ingestion-quality-investigation.md`](./t2d-010-ingestion-quality-investigation.md).
Further pipeline
docs are created as pipelines are actually built, using
[`docs/templates/pipeline-doc-template.md`](../templates/pipeline-doc-template.md).

Planned documents (each written when that pipeline exists, not before):

- cleaning and normalization
- metadata creation
- citations
- execution recording

No pipeline is treated as a black box: every doc shows INPUT → steps → OUTPUT
and answers what can fail, how we notice, and what evidence it produces.
