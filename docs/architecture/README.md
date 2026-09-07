# Architecture

Status: planned next (nothing implemented yet — this will be written as the
system actually takes shape, starting with the M1 vertical slice).

Planned contents, written only as things actually exist:

- How the system fits together: contracts, ingestion, embedding, vector
  storage, retrieval, context construction, generation, recording
- Which layers may depend on which, and why
- **The two-products rule:** Clinivault is a standalone clinical evidence
  product; Errata is a separate, reusable AI evaluation product that lives in
  its own repository. Clinivault preserves the structured evidence,
  provenance, and execution records that would let Errata evaluate this
  pipeline later through a shared contract — but integration is not a
  current MVP goal, and no Errata logic lives here
- Which components are deliberately replaceable (parser, embedding model,
  vector database, LLM) and where we chose NOT to add seams

