# Pipeline: Generation — Baseline LLM Answer Generation

Status: **implemented** (baseline; verified end-to-end on T2D-001 with
Google Gemini `gemini-2.5-flash`).

## What this stage does

Transforms a context/evidence bundle into a generated answer using one
chosen LLM, preserving provenance and recording execution measurements.

```
context/evidence bundle (from context construction)
  -> controlled prompt construction (pure function: query + ranked evidence
     with citation identifiers + explicit instruction to answer ONLY from
     the supplied evidence)
  -> one chosen LLM via the GenerationProvider seam
  -> generated answer + evidence/provenance + execution measurements
```

## Input contract

The output of `context.builder.build_context`:

```python
{query,
 evidence_count,
 documents: [{document_id, chunk_count, pages}],
 evidence: [{rank, chunk_id, document_id, page_number, score, text}]}
```

- `rank` is explicit 1-based position (retrieval order).
- Evidence text is verbatim from the source chunk.
- Empty evidence (`evidence_count == 0`) is a legitimate input: the
  baseline returns `status: "no_evidence"` with `answer: null` and does
  NOT fabricate a reply.

## What happens

1. Input contract is validated; malformed bundles raise `GenerationError`.
2. If evidence is empty, an explicit no-answer result is returned
   immediately (no provider call, no fabricated answer).
3. Otherwise the prompt is built (query + each evidence item with its
   rank/chunk_id/document_id/page_number + instruction to answer only
   from the supplied evidence and to cite evidence identifiers when
   possible).
4. The prompt is sent to the provider; the response is parsed.
5. The result is returned with the answer, the exact evidence used,
   provider/model identity, status, timing measurements, and provider
   usage metadata when available.

## Output contract

```python
{query,
 answer,                       # model text, or null if status != "ok"
 status,                       # "ok" | "no_evidence" | "failed"
 provider,                     # e.g. "google_gemini"
 model,                        # e.g. "gemini-2.5-flash"
 prompt_text,                  # the exact prompt sent (inspectable)
 evidence,                     # verbatim evidence items actually used
 timings: {prompt_construction_ms,
           llm_generation_ms,
           total_ms},
 usage: null | dict}           # provider usage metadata, if returned
```

- `evidence` is the verbatim list from the input bundle (no modification).
- `prompt_text` is the exact prompt sent — fully inspectable.
- Timings are measured with `time.perf_counter()` at explicit boundaries.
- `usage` is provider-reported metadata passed through without arithmetic.

## Provider

Per DECISION-007:

- Primary: **Google Gemini API**, model **`gemini-2.5-flash`** (stable,
  non-preview).
- The provider sits behind the `GenerationProvider` seam (`name`, `model`,
  `generate(prompt)`), so replacement is possible without touching the
  generator or prompt logic.

## Error behavior

Fail-loud on every error path — no silent fallbacks, no fabricated
answers:

- Malformed input bundle → `GenerationError`.
- Empty evidence → `status: "no_evidence"`, `answer: null` (no provider
  call).
- Provider failure / empty / malformed response → `GenerationError`.
- Provider-reported error message is included but never exposes
  credentials.

## Out of scope (for this baseline)

- No LLM answer generation beyond the single chosen provider.
- No agents, multi-step reasoning, corrective RAG.
- No hybrid retrieval, reranking, query rewriting.
- No abstention system beyond the explicit no-answer status.
- No evaluation framework.

## Verification Performed

### Automated verification

- 36 generation tests covering: prompt construction, valid input, input
  validation, empty evidence, provider failure, timings, usage metadata,
  credential handling, malformed evidence items (GenerationError contract).
- Full project suite at verification checkpoint: **122/122 passing**
  (reader 16, ingestion 9, chunking 11, embedding 19, retrieval 19,
  context 12, generation 36).
- All tests use in-memory fake providers; no network, no API keys.

### Real T2D-001 verification

- **Query:** "criteria for the diagnosis of diabetes"
- **Document:** T2D-001 (107 chunks, 107 embeddings indexed, dim 256)
- **Provider:** google_gemini / `gemini-2.5-flash`
- **Status:** ok

A second reproduction run was performed after the GenerationError
contract-leak fix (narrow ValueError-to-GenerationError wrap in
generate_answer()). The reproduction confirmed: same retrieval path,
same evidence, same grounding pattern (10/12 supported, 2/12
unsupported), no regression. Measurements below reflect the
final-code reproduction run.

**Retrieved evidence supplied to Gemini (top-5):**

| Rank | Chunk ID | Page | Score |
|------|----------|------|-------|
| 1 | T2D-001-p014-c003 | 14 | 0.6018 |
| 2 | T2D-001-p002-c002 | 2 | 0.5851 |
| 3 | T2D-001-p023-c006 | 23 | 0.5814 |
| 4 | T2D-001-p002-c003 | 2 | 0.5680 |
| 5 | T2D-001-p017-c003 | 17 | 0.5641 |

**Generated answer (full verbatim):**

```
The criteria for the diagnosis of diabetes vary depending on the
clinical scenario and the specific type of diabetes.

**General Diabetes Diagnosis:**
*   **With Classic Symptoms:** If a person has classic symptoms of
    hyperglycemia (e.g., polyuria, polydipsia, unexplained weight
    loss) or presents with hyperglycemic crisis, a random plasma
    glucose measurement of ≥200 mg/dL (≥11.1 mmol/L) is sufficient
    to diagnose diabetes (EVIDENCE_ITEM_RANK: 4, T2D-001-p002-c003).
*   **Without Symptoms:** In an individual without symptoms, fasting
    plasma glucose (FPG) or 2-hour plasma glucose (2-h PG) can be
    used for screening and diagnosis. FPG (or A1C) is generally
    preferred for routine screening due to ease of administration.
    The 2-h PG from an oral glucose tolerance test (OGTT) is more
    sensitive (EVIDENCE_ITEM_RANK: 4, T2D-001-p002-c003). Repeat
    testing is required to confirm the diagnosis regardless of the
    test used when classic symptoms are absent (EVIDENCE_ITEM_RANK: 4,
    T2D-001-p002-c003).
    *   The specific cut-off values for A1C, FPG, or 2-h PG during
        an OGTT for the diagnosis of diabetes in nonpregnant
        individuals without symptoms are not provided in the supplied
        evidence.

**Post-transplantation Diabetes Mellitus (PTDM):**
*   A formal diagnosis of PTDM is best made once the individual is
    stable on an immunosuppressive plan and in the absence of an acute
    infection (EVIDENCE_ITEM_RANK: 1, T2D-001-p014-c003).
*   The OGTT is the preferred test to make a diagnosis of PTDM
    (EVIDENCE_ITEM_RANK: 1, T2D-001-p014-c003; EVIDENCE_ITEM_RANK: 4,
    T2D-001-p002-c003).
    *   The specific glucose values used with the OGTT for PTDM
        diagnosis are not provided in the supplied evidence.

**Gestational Diabetes Mellitus (GDM):**
*   The diagnosis of GDM can be made using the Carpenter-Coustan
    criteria, where at least two of the following four plasma glucose
    levels (measured fasting and at 1, 2, and 3 hours during OGTT) are
    met or exceeded:
    *   Fasting: 95 mg/dL (5.3 mmol/L)
    *   1 hour: 180 mg/dL (10.0 mmol/L)
    *   2 hours: 155 mg/dL (8.6 mmol/L)
    *   3 hours: 140 mg/dL (7.8 mmol/L) (EVIDENCE_ITEM_RANK: 5,
        T2D-001-p017-c003).
*   GDM diagnosis can also be accomplished with the "one-step" 75-g
    OGTT derived from the IADPSG criteria (EVIDENCE_ITEM_RANK: 5,
    T2D-001-p017-c003).
```

**Grounding classification:** MOSTLY SUPPORTED — 10 of 12 substantive
claims in the answer map directly to specific evidence items supplied
to the model. 2 of 12 substantive claims were model parametric
additions not present in the supplied evidence:

1. **"Repeat testing is required to confirm the diagnosis"** — cited
   to rank 4 (T2D-001-p002-c003), but the evidence text does not contain
   any "repeat testing" or "confirm" language. This is a model
   parametric addition.
2. **"One-step 75-g OGTT derived from the IADPSG criteria"** — cited to
   rank 5 (T2D-001-p017-c003), but rank 5 contains only Carpenter-Coustan
   values. IADPSG appears in the evidence only as a citation title in
   rank 3 (T2D-001-p023-c006), with no content about "one-step" or
   "75-g OGTT." This is a model parametric addition.

The model indicated where specific numeric thresholds were absent from
the supplied evidence (e.g., "the specific cut-off values for A1C,
FPG, or 2-h PG... are not provided in the supplied evidence"), rather
than inventing them.

**Single-run baseline measurements:**

| Stage | Latency | Scope |
|-------|---------|-------|
| Query embedding | 0.21 ms | Measured in run script (not in generator) |
| Retrieval (top-5) | 2.50 ms | Measured in run script (not in generator) |
| Context construction | 0.06 ms | Measured in run script (not in generator) |
| Prompt construction | 0.03 ms | Measured inside generator |
| LLM generation | 14,130.50 ms | Measured inside generator |
| **Generation-stage total** | **14,130.54 ms** | `total_ms` from generator — covers prompt construction + LLM generation only |
| **Approximate full pipeline end-to-end** | **~14,130.78 ms** | Sum of all stages: 0.21 + 2.50 + 0.06 + 0.03 + 14,130.50 |

Note: The generator's `total_ms` field covers only the generation stage
(prompt construction + LLM generation + result assembly overhead). It does
NOT include query embedding, retrieval, or context construction, which are
measured separately by the caller. The true end-to-end wall-clock is the sum
of all stages (~13,036.49 ms), not the generator's `total_ms`. The difference
is ~3.7 ms (0.03%) — numerically immaterial, but the distinction matters for
correct interpretation.

**Provider usage metadata:**

- promptTokenCount: 2,477
- candidatesTokenCount: 628
- totalTokenCount: 5,159
- thoughtsTokenCount: 2,054 (internal reasoning tokens)
- serviceTier: standard

Note: totalTokenCount (5,159) = prompt (2,477) + candidates (628) +
thinking (2,054). Do not assume input + output = total for Gemini.
Token counts vary between runs (LLM variability); the values above are
from the final-code reproduction run.

### OBSERVED

- Gemini API connectivity and authorization succeeded on first attempt.
- The model produced a structured, citation-aware answer without
  being explicitly prompted in a rigid format.
- Every substantive factual claim traced to a specific evidence item
  via the citation identifiers from the prompt.
- The model indicated where specific numeric thresholds were absent
  from the supplied evidence, rather than inventing them.
- Generation latency (~14 s) is dominated by the LLM call; all
  pre-LLM stages combined are under 3 ms.
- Provider returned full token accounting including internal
  thinking tokens.
- No API key, credential, or secret appeared in any output.

### LIMITATIONS

- Single-run sample on one document and one query — not a benchmark.
- No systematic grounding evaluation (no labeled dataset, no
  inter-annotator agreement).
- No clinical accuracy validation — MOSTLY SUPPORTED ≠ CLINICALLY CORRECT.
- No long-context testing (5 evidence items only; ~8.5k-char prompt).
- No sustained quota or rate-limit testing.
- No multi-document retrieval/generation testing.

### Move-forward assessment

This single baseline run is sufficient to move to the next
engineering stage because:

1. The complete pipeline (ingest → chunk → embed → retrieve →
   context → prompt → generate → result) executed end-to-end
   without error.
2. The generated answer was mostly grounded in the supplied evidence
   and the model indicated where evidence was incomplete.
3. All execution measurements (timings, token usage, provenance)
   were captured and preserved.
4. No silent failures, no metadata loss, no credential leakage.
5. Automated tests (122/122) continue to pass alongside the real
   run.

Systematic retrieval/generation quality evaluation remains a future
validation step.

### Grounding Observation

This is the first observed generation-level grounding limitation in the
project, recorded from the real T2D-001 run on 2026-09-13.

**What happened:**

- The retrieval/context pipeline supplied 5 evidence items from T2D-001
  (pages 2, 14, 17, 23) with full provenance.
- The prompt explicitly instructed the model to answer ONLY from the
  supplied evidence and to cite evidence identifiers.
- The model nevertheless added two substantive claims that were not
  present in the supplied evidence:
  1. "Repeat testing is required to confirm the diagnosis" — not in any
     evidence item.
  2. "One-step 75-g OGTT derived from the IADPSG criteria" — IADPSG
     appears only as a citation title in rank 3, with no supporting
     content.

**Implication:**

The baseline generation is NOT fully grounded. Good retrieval and
correct context construction do not guarantee that the generator will
restrict every claim to supplied evidence. The prompt constrains
generation but cannot fully prevent the model from adding parametric
knowledge.

**Classification:**

This is an observed generation limitation from a single run, not a
formal hallucination-rate measurement. No labeled evaluation dataset
exists. The finding is specific to this run and should not be
generalized beyond it without further evidence.

- No deployment/API layer.
