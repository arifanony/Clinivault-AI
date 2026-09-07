# Architecture

Status: planned next (nothing implemented yet — this will be written as the
system actually takes shape, starting with the M1 vertical slice).

Planned contents, written only as things actually exist:

- How the system fits together: contracts, ingestion, embedding, vector
  storage, retrieval, context construction, generation, recording
- Which layers may depend on which, and why
- The structured evidence this system produces (execution records, ingestion
  records) and how the external Errata product consumes it — Errata itself
  is a separate product and lives in its own repository
- Which components are deliberately replaceable (parser, embedding model,
  vector database, LLM) and where we chose NOT to add seams

