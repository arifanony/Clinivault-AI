# Clinivault AI — Live End-to-End Validation

**Date:** 2026-11-24
**Codebase:** `master` @ `362d475` (final M7 commit, unmodified)
**Run by:** Independent live run on a fresh machine (clean clone, clean environment)
**Verdict:** ✅ **The M1–M7 MVP works end to end, live, exactly as documented.**

This run closes the one item the project handoff listed as NOT YET VALIDATED:
end-to-end Gemini answers over the API with E5 evidence over the full corpus.

---

## 1. Retrieval benchmark — frozen 46 cases, reproduced exactly

Command: `python -m clinivault_ai.evaluation.benchmark --provider e5`

| Metric | E5 (production) | Hash baseline | Frozen record |
|---|---|---|---|
| Hit@1 | **20/46** (43.5%) | 12/46 (26.1%) | 20/46 |
| Hit@5 | **36/46** (78.3%) | 26/46 (56.5%) | 36/46 |
| MRR | **0.5583** | 0.3601 | 0.5583 |

The live run reproduces the frozen E5 numbers to the fourth decimal.
Retrieval behaviour is identical on a different machine, a different OS,
and a newer library stack.

## 2. Test gate — full unittest suite

Command: `python -m unittest discover -s tests`

| | Count |
|---|---|
| Total | 306 |
| Passed | 304 |
| Skipped | 1 |
| Failed | 1 (see note) |

**Note on the one failure:** `test_t2d001_first_chunk_matches_committed_artifact`
demands exact float-for-float equality between a freshly computed E5 embedding
and the artifact committed in this repo. Measured on this machine: cosine
similarity **0.9999999999997**, maximum absolute difference **1.3e-07** — pure
cross-machine floating-point noise. The embedding is the same embedding; the
test's exact-equality bar is stricter than floating-point arithmetic allows
across machines. Retrieval itself is proven unaffected by §1.

## 3. Live API run — real Gemini answers (the first ever for this system)

Server: `python -m clinivault_ai.api` (FastAPI, production E5 index)
Generation: `gemini-2.5-flash`, free-tier API key, 1 attempt per query, no retries needed

**Health:** `GET /health` → `{"status": "ok", "document_count": 9, "chunk_count": 727, "embedding_model": "intfloat/e5-small-v2"}`

### Q1 — Glycemic targets (in scope)

> *What HbA1c target is recommended for most adults with type 2 diabetes?*

**Status: `ok`** — Answer grounded in the ACP guideline (T2D-007): clinicians
should aim for HbA1c between 7% and 8% for most adults, deintensify
pharmacologic treatment below 6.5%, and individualise goals by hypoglycemia
risk, life expectancy, duration, complications, comorbidities and patient
preference. Citations machine-checked: **0 invalid citations**.

### Q2 — Screening (in scope)

> *At what age should screening for type 2 diabetes begin in asymptomatic adults, and how often?*

**Status: `ok`** — Screening begins at age 35 for adults with overweight or
obesity; the USPSTF lowered the starting age from 40 to 35. Cited to the
USPSTF recommendation (T2D-002) and ADA Standards of Care (T2D-001).
Citations machine-checked: **0 invalid citations**.

### Q3 — Out of scope (abstention check)

> *What is the recommended treatment for malaria?*

**Status: `abstained`** — The system refused, as designed:

> `ABSTAIN: The supplied evidence does not contain any information about malaria or its recommended treatment.`

Retrieval returned nearest-neighbour T2D chunks (as top-k always does), but
grounded generation declined to answer from irrelevant evidence. The
abstention sentinel (M5, DECISION-020) works live, not just in unit tests.

## 4. What this proves

- **The pipeline is real, not just tested in pieces.** Ingestion → chunking →
  E5 embedding → retrieval → context construction → grounded Gemini
  generation → citation checking → abstention → structured execution
  records, all over the production FastAPI surface.
- **The numbers in the README are reproducible** by an independent run on
  different hardware.
- **The safety behaviour holds live:** answers cite only supplied evidence,
  citations are validated, and out-of-scope questions get a refusal instead
  of an improvisation.

## 5. Honest limits of this validation

- One live run, three queries — a smoke validation, not a clinical
  evaluation. No claim about answer quality beyond grounding and citation
  validity is made here.
- The system remains **not deployed**: no public URL, no auth or rate
  limiting on the API, in-memory index (no vector database), Type 2 Diabetes
  scope only (9 documents; T2D-004 blocked-access). These are the recorded
  MVP boundaries, unchanged by this run.
- The exact-equality embedding test (§2) can only pass on the machine class
  that produced the committed artifacts; a tolerance-based comparison would
  make it portable.

---

*Evidence: full JSON responses for the three live queries (answers,
citations, retrieval scores, execution records) were captured during the
run and are retained with this validation's working files.*
