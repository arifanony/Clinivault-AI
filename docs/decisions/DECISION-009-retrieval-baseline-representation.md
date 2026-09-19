# Engineering Decision: Baseline Retrieval Representation and Configuration

## Status

Chosen (retroactively documented — the choices were made while building the
stage; the record was written after the controlled comparison froze the baseline)

## Date

2026-09-13 to 2026-09-18 (implementation commits `06cb7e3`, `ace908d`,
`b61a2b4`; frozen as the benchmark protocol in `1984724`)

## Decision Question

What representation, index, metric, and Top-K window is the project's **baseline**
retrieval configuration — the thing every future "improvement" must be measured
against?

## Problem

By 2026-09-13 the pipeline ran end-to-end, but the retrieval representation had
never been written down as a decision: the hash provider, the in-memory index,
the cosine metric, and the Top-K=5 window were only visible in code and in
pipeline documents. DECISION-003 forbids recurring API cost during MVP
development, DECISION-001 allows exactly one embedding seam, and the project's
own rule is *baseline first, measure, then improve*. Without an explicit baseline
record, a later representation change could not be evaluated honestly.

## What This Part of the System Does

- Chunks → embedding provider (the seam) → embedding records keyed by `chunk_id`;
  chunk text is never duplicated into the embedding artifact.
- Retrieval: an **in-memory** cosine index built per document by joining
  validated chunk text and validated embedding records on `chunk_id`, re-validating
  document identity, dimensions, vector sanity, duplicate IDs, and exact
  chunk↔embedding agreement in **both** directions.
- Query text is embedded through the same seam; ranking is brute-force cosine,
  best first, with deterministic ties.
- Every result carries `{chunk_id, document_id, page_number, score, text}`.

## The Baseline, As Frozen

1. **Representation** — `clinivault-baseline-hash-v1`: deterministic in-repo
   hashed bag-of-words (`blake2b(digest_size=8) mod 256` per token; lowercase
   whitespace tokenizer; punctuation kept attached; **no** stopword removal, IDF,
   or stemming), L2-normalized, 256 dimensions. Explicitly **not semantic**.
2. **Index** — in-memory, rebuilt from the committed artifacts. **No vector
   database** and no persistence seam.
3. **Metric** — cosine similarity, ranked by `(-score, chunk_id)`; brute force,
   deliberately, at this scale.
4. **Top-K = 5** as the baseline retrieval window (see "On Top-K = 5" below).
5. **Fail-loud** — malformed artifacts, mismatched counts, wrong dimensions, and
   bad `top_k` values raise `RetrievalError`; records are never silently dropped
   or clamped.
6. **Semantic embedding remains undecided** — the seam exists so that it can be
   swapped in, but no semantic model is the production default.

## Options We Considered

- **Option A — deterministic local hash representation + in-memory cosine index
  (chosen).**
- **Option B — a real semantic embedding model via API from the start**: recurring
  cost during MVP (DECISION-003), credential/environment dependency, and no
  measured baseline to compare against; deferred, then tested as arm C of the
  controlled comparison (`d0dc40c`).
- **Option C — term-weighted lexical representation** (stopword removal / IDF):
  considered at design time, later implemented as arm B of the controlled
  comparison.
- **Option D — vector database / approximate index**: no scale requirement
  demonstrated at 9 documents and ~600 chunks.
- **Option E — hybrid/reranked retrieval or metadata filtering**: premature;
  requires a measured baseline first.

## Decision

Option A. The baseline retrieval representation is the deterministic local
hashed bag-of-words provider, a re-validated in-memory cosine index over the
committed embedding artifact, brute-force ranking with deterministic ties, and an
explicit Top-K window (5 in every recorded evaluation). The semantic model stays
a deferred, undecided choice behind the existing `EmbeddingProvider` seam.

## Why We Chose It

- **No recurring cost, no network, fully deterministic** — verified bit-for-bit:
  re-embedding T2D-001 from its committed parsed artifact reproduced the committed
  embedding artifact exactly (`artifact-persistence.md` §F), and two consecutive
  benchmark runs hash to the same SHA-256 (`retrieval-baseline-benchmark.md`).
- **It establishes and tests the contract** (fail-loud boundaries, provenance,
  JSON-serializable records) rather than assuming a model.
- **The seam makes the choice reversible**: replacing the representation is a
  provider swap, which is exactly what the controlled comparison later exploited
  without touching production code.

## On Top-K = 5 (rationale partly UNCERTAIN — recorded, not invented)

Top-K=5 is the baseline window in every recorded run: the retrieval baseline,
the generation baseline, the representative evaluation, the corpus
generalization validation, the 21-case benchmark, and all three arms of the
controlled comparison (`docs/pipelines/representative-evaluation.md`,
`retrieval-baseline-benchmark.md`, `retrieval-controlled-comparison.md`).

- **OBSERVED:** it is the configured default everywhere; the controlled
  comparison deliberately held it at 5 for every arm so that only one variable
  changed at a time; the benchmark protocol is defined at Top-K=5.
- **INFERENCE:** a five-item window is small enough to keep the generation prompt
  inspectable and the evidence bundle reviewable by a human, which matches the
  project's inspection-first style.
- **NOT ESTABLISHED / UNCERTAIN:** the repository contains **no contemporaneous
  rationale for the value 5 itself**, and **no measurement compares other K
  values**. This record therefore documents Top-K=5 as *the frozen baseline
  constant*, not as a demonstrated optimum. Changing K requires evidence
  (a K-sweep under the same labeled benchmark), which has not been run.

## Trade-offs Accepted

- Retrieval quality is **lexical, not semantic**. Documented weaknesses:
  function-word mass dominates scores, hash collisions can inflate scores,
  citation/boilerplate chunks can outrank short body chunks, and long
  number-dense recommendation blocks are normalized downward
  (`retrieval-ranking-investigation.md`).
- Brute force over the whole document index — fine at this scale, not a
  production-scale strategy.
- No vector-store abstraction or persistence seam exists, so replacing the store
  would touch the retrieval package directly.

## What We Did Not Choose (yet)

- A semantic embedding model as the production representation — tested, not
  adopted: see [DECISION-010](./DECISION-010-retain-baseline-retrieval.md).
- IDF/term weighting inside the baseline — tested, worse: same decision.
- Stopword removal as a standalone fix — never evaluated separately; the
  controlled comparison deliberately changed one variable at a time.
- A vector database, hybrid retrieval, reranking, metadata filtering,
  structure-aware reference-page filtering — each requires its own evidence and,
  if adopted, its own decision record.

## Evidence

- `docs/pipelines/embedding-baseline.md` — provider boundary and T2D-001
  verification (107 in / 107 out, deterministic).
- `docs/pipelines/retrieval-baseline.md` — storage, metric, `top_k` validation,
  trace observability, and the "honest quality note".
- `docs/pipelines/artifact-persistence.md` §F — bit-for-bit determinism.
- `docs/pipelines/retrieval-baseline-benchmark.md` /
  `retrieval-baseline-benchmark-results.md` — the frozen 21-case protocol and
  measured baseline (Hit@1 8/21, Hit@5 16/21, MRR 0.5095).
- `docs/pipelines/retrieval-controlled-comparison.md` — the three-arm comparison
  that froze and then tested this baseline (`d0dc40c`).

## How We Will Validate This

- Functional invariants: `tests/test_retrieval.py` (index join in both
  directions, rejects duplicates/orphans/malformed vectors/dimension mismatch,
  exact Top-K, deterministic order, trace contents).
- Determinism: repeated benchmark runs must be byte-identical.
- Quality: the labeled benchmark and any future controlled comparison.

## When We Should Revisit It

- If a controlled comparison on a trustworthy corpus and a larger labeled case
  set shows a materially better representation on Hit@1/MRR.
- If a measured K-sweep shows a different window is better.
- If corpus scale makes brute-force scanning impractical.

## Related Documents

- [DECISION-001: repository architecture](./DECISION-001-repository-architecture.md) — the seam principle this uses.
- [DECISION-003: product direction](./DECISION-003-product-direction.md) — the no-recurring-API-cost constraint.
- [DECISION-010: retain the baseline retrieval representation](./DECISION-010-retain-baseline-retrieval.md) — what the evidence said when tested.
- [DECISION-008: artifact storage](./DECISION-008-artifact-storage-contract.md) — where the embedding artifact lives.
- [retrieval-ranking-investigation.md](../pipelines/retrieval-ranking-investigation.md), [retrieval-baseline-benchmark.md](../pipelines/retrieval-baseline-benchmark.md), [retrieval-controlled-comparison.md](../pipelines/retrieval-controlled-comparison.md).

## Related Commits

`06cb7e3`, `ace908d`, `b61a2b4` (baseline built); `d2155a4`, `1984724`,
`d0dc40c` (investigation, benchmark, comparison).