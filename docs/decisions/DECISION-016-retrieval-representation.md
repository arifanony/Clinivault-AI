# Engineering Decision: Retrieval Representation for the Next Integration Phase

## Status

Chosen

## Date

2026-09-23

## Problem

[DECISION-010](./DECISION-010-retain-baseline-retrieval.md) retained the hash
baseline because neither alternative beat it on Hit@1 or MRR in the then-frozen
21-case comparison. That conclusion was appropriately limited to that evidence.

The authoritative benchmark is now the frozen 46-case set across all nine
baseline-corpus documents ([DECISION-014](./DECISION-014-benchmark-expansion.md)).
On that set, dense semantic representations materially outperform the hash
baseline, and EVAL-HF-001 through EVAL-HF-003 completed the local-model screen.
The project needs a truthful representation decision for its next integration
phase without silently changing production retrieval or overstating what 46
cases prove.

## What This Part of the System Does

- Chunk text is represented as an embedding through the existing provider seam.
- The in-memory cosine index joins embedding records to validated chunks by
  `chunk_id` and preserves document, page, and chunk provenance in results.
- Query text is represented through the corresponding provider and ranked with
  the same cosine metric and frozen Top-K=5 evaluation window.

This decision changes the documented direction for a future integration unit;
it does not change any current pipeline code, persisted artifacts, corpus,
labels, chunking, metric, provenance contract, or Top-K value.

## Requirements

- Base the direction on the frozen 46-case benchmark, not the superseded
  21-case-only conclusion.
- Preserve offline/local operation and avoid a recurring cloud-embedding API
  dependency during the current MVP phase ([DECISION-003](./DECISION-003-product-direction.md)).
- Retain evidence provenance and fail-loud retrieval invariants from
  [DECISION-009](./DECISION-009-retrieval-baseline-representation.md).
- Do not present one frozen, single-pass benchmark as proof of a universal best
  model or as a production implementation.

## Evidence Considered

All results below use the same frozen 46 cases, corpus, relevance labels,
metric implementation, and Top-K=5 unless noted otherwise.

| Representation | Hit@1 | Hit@5 | MRR | Decision relevance |
|---|---:|---:|---:|---|
| Baseline hash | 12/46 | 26/46 | 0.3601 | Current production baseline |
| IDF-weighted hash | 8/46 | 20/46 | 0.2815 | Rejected; worse on every aggregate |
| Gemini semantic | 21/46 | 42/46 | 0.6109 | Best measured aggregate, but cloud/API-dependent |
| BGE-small local semantic | 19/46 | 36/46 | 0.5428 | Local semantic alternative |
| E5-small local semantic, raw | 20/46 | 36/46 | 0.5583 | Best measured local MRR and Hit@1 |
| E5-small local semantic, `query:`/`passage:` | 19/46 | 35/46 | 0.5486 | Intended formatting did not improve this benchmark |

The Gemini, baseline, and IDF figures come from the expanded controlled
comparison. The local figures come from EVAL-HF-001 through EVAL-HF-003. The
E5 raw result was reproduced exactly during EVAL-HF-003; a fresh T2D-001 raw
encoding matched its persisted EVAL-HF-002 vectors byte-for-byte.

## Options We Considered

1. **Continue to retain the hash baseline as the next representation direction.**
   Rejected: it is no longer supported by the authoritative 46-case results;
   every measured semantic candidate listed above exceeds its MRR, and the
   leading local candidates also exceed its Hit@1 and Hit@5.
2. **Select Gemini semantic embeddings for the next phase.** Rejected for the
   current MVP direction: it has the best measured aggregate, but depends on a
   networked, credentialed, rate-limited cloud API and conflicts with the
   current no-recurring-API-cost constraint.
3. **Select local semantic retrieval, with raw `intfloat/e5-small-v2` as the
   leading integration candidate.** Chosen.
4. **Select IDF-weighted hashing.** Rejected: it regressed relative to baseline
   on all three expanded-benchmark aggregates.
5. **Implement hybrid retrieval, reranking, a vector database, or change
   chunking/Top-K.** Not chosen: none was evaluated in this decision's evidence,
   and each would change more than one variable.

## Decision

Replace DECISION-010's retention conclusion with this direction: the next
separately authorized retrieval-integration unit should target a **local dense
semantic representation**, using raw `intfloat/e5-small-v2` as the leading
candidate under the existing provider seam.

This is a representation decision, not an implementation authorization. The
current production default remains `clinivault-baseline-hash-v1` until that
future unit implements the change and validates it against the frozen benchmark
and existing retrieval invariants.

## Why We Chose It

- **OBSERVED:** raw E5-small produced 20/46 Hit@1, 36/46 Hit@5, and MRR 0.5583,
  versus the hash baseline's 12/46, 26/46, and 0.3601.
- **OBSERVED:** among the evaluated local models, raw E5-small had the highest
  recorded Hit@1 and MRR. Its Hit@5 did not exceed every local model, so it is
  selected as the leading integration candidate rather than claimed to be a
  universal local winner.
- **OBSERVED:** intended E5 prefix formatting did not improve the frozen
  benchmark (19/46, 35/46, 0.5486); raw is reproducible and is the protocol
  selected for the future integration evaluation.
- **INFERENCE:** local E5-small is the most evidence-supported next direction
  under the project's offline/cost constraint, while Gemini remains the
  measured quality reference rather than the selected MVP dependency.

## Trade-offs and Limitations

- Local semantic encoding has materially higher CPU encoding/query cost and
  adds local model-runtime dependencies compared with deterministic hashing.
- The 46 cases are a frozen project benchmark, not a statistical demonstration
  of general clinical retrieval quality or significance between close models.
- E5 raw and intended-format differences are within the benchmark's resolution;
  the evidence supports "prefixing did not help," not "raw is statistically
  superior."
- This record does not validate model memory use, deployment packaging,
  repeatability beyond the demonstrated E5 raw checks, or behavior on another
  corpus.

## What We Did Not Choose

- A cloud semantic provider as the current MVP representation default.
- A claim that E5-small is best for every corpus, query distribution, hardware
  profile, or semantic model family.
- Any production retrieval change, benchmark/label change, Top-K change, or new
  retrieval component in this decision unit.

## How We Will Validate the Future Integration

A future integration task must, at minimum:

1. preserve `chunk_id`, document ID, page number, and evidence text in results;
2. retain fail-loud index/artifact validation and deterministic ordering where
   scores tie;
3. verify the selected raw E5 input protocol is actually applied to both corpus
   and query embedding paths;
4. rerun the frozen 46-case benchmark without changing its corpus, labels,
   metrics, or Top-K; and
5. run the repository unit-test suite and record operational dependency,
   latency, and artifact-storage consequences.

## When We Should Revisit It

- A larger, independently reviewed labeled evaluation set changes the result.
- A local candidate materially improves the relevant metrics and operational
  profile under the same controlled protocol.
- The MVP cost/offline constraint changes, making Gemini's higher measured
  aggregate quality acceptable.
- A measured chunking, Top-K, hybrid, or reranking experiment identifies a
  better supported direction.

## Related Documents

- [DECISION-009: baseline retrieval representation](./DECISION-009-retrieval-baseline-representation.md)
- [DECISION-010: historical baseline-retention outcome](./DECISION-010-retain-baseline-retrieval.md)
- [DECISION-014: 46-case benchmark expansion](./DECISION-014-benchmark-expansion.md)
- [DECISION-015: local-model evaluation authorization](./DECISION-015-evaluate-multiple-embedding-models.md)
- [Expanded controlled comparison](../pipelines/retrieval-controlled-comparison.md)
- [EVAL-HF-001](../engineering-log/2026-09-21-multi-model-embedding-eval.md),
  [EVAL-HF-002](../engineering-log/2026-09-22-eval-hf-002.md), and
  [EVAL-HF-003](../engineering-log/2026-09-23-eval-hf-003.md)