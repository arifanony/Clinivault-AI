# Engineering Decision: Evaluate Multiple Embedding Representations

## Status

Chosen

## Date

2026-09-21 (Recorded during Genesis TASK EVAL-HF-001)

## Context & Problem

In recent experiments (expanding the evaluation benchmark to 46 cases in DECISION-014), the Gemini Semantic Embedding model substantially outperformed the Baseline Hash (Hit@5 91.30% vs 56.52%; MRR 0.6109 vs 0.3601). 
This demonstrated that semantic representational capability fundamentally overcomes the limitations of purely lexical, term-weighted hashing (as attempted with the IDF-counterfactual), particularly for multi-drug queries covering overlapping disease management contexts.

However, moving to a cloud-based external API (like Gemini) carries operational friction that violates current local-only or offline-capable edge deployments (e.g. `HTTP 429` rate limits, offline incompatibility, API costs). 
We need the semantic ranking prowess of dense embeddings, but we must establish the operational trade-offs (latency, dimension size, model memory footprints) of running these models locally.

## Decision

**Clinivault will evaluate a multi-model cohort of local Hugging Face embedding/retrieval models against the exact same 46-case benchmark before making a formal representation change.** 

This decision strictly authorizes an **Evaluation Strategy** and does **NOT** constitute a decision that Gemini or any newly tested local model is chosen as the production pipeline default yet. 
The production architecture continues utilizing the frozen `BaselineHashEmbeddingProvider`.

## Rationale

- **Retention of Strict Metrics:** Retrieval performance is highly bound to representation logic. Keeping the benchmark frozen (46 cases, same labels, Top-K=5) while substituting models ensures a mathematically sound comparison array.
- **Hardware Profile Diversity:** Local environments have varying restrictions. Evaluating a Small (e.g., MiniLM 384-d), Medium (e.g., BGE-Small 384-d), and Large (e.g., BGE-Base 768-d) tier maps expected Hit/MRR improvements directly against CPU cycles or possible GPU memory costs.
- **Durable Investigation:** Instead of adopting the first model that beats the baseline, methodically testing 3–5 candidate models exposes edge-case behavioral regressions and establishes a defensible benchmark suite standard for future evaluation integrations.

## Implementation Guidelines

- Hugging Face runner dependencies (e.g., `sentence-transformers`, `torch`) will be restricted to the local development environment (`.venv`) and **will not** leak into `pyproject.toml` production dependencies until a specific backend is selected.
- Models tested will be explicit dense embedding retrievers (e.g., MTEB leaderboards), not arbitrary language models.
- Embedding outputs across models will be persisted as durable artifacts following the `DECISION-008` storage contract, using nested model identifiers into proper isolated prefixes (e.g., `data/embedded-<model-name>/`) so they do not collide with the `data/embedded/` baseline directory.
