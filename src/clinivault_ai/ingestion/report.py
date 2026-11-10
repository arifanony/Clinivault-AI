"""Ingestion reports for the Stage-1 corpus (M3, DECISION-018).

A report answers the project-brief evidence question for one document:
how many pages were seen, parsed, and failed, and how many chunks were
produced, embedded, and indexed. Reports live under
``data/ingestion-report/<corpus-version>/<DOC-ID>/`` and are never written
inside ``parsed/`` or ``embedded/`` trees.
"""

from __future__ import annotations

import json
from pathlib import Path

from .errors import IngestionError

REPORT_DIR_NAME = "data/ingestion-report"
REPORT_FILENAME_SUFFIX = ".ingestion-report.json"


def build_ingestion_report(
    document_id: str,
    parsed_document: dict,
    chunk_output: dict,
    embedding_artifact: dict,
) -> dict:
    """Build the brief-shaped ingestion report for one document.

    Shape: ``{document_id, total_pages, parsed_pages, failed_pages,
    total_chunks, embedded_chunks, indexed_chunks, ingestion_status}``.
    ``failed_pages`` is a sorted list of page numbers whose
    ``extraction_status`` is ``"failed"``. ``ingestion_status`` is
    ``"success"`` when no page failed, else ``"partial"``.

    Raises IngestionError when the document identities disagree or when
    the chunk count does not equal the embedding count (no silent drops).
    """
    if not isinstance(document_id, str) or not document_id:
        raise IngestionError("document_id must be a non-empty string")
    if not isinstance(parsed_document, dict):
        raise IngestionError("parsed_document must be a dict")
    if not isinstance(chunk_output, dict):
        raise IngestionError("chunk_output must be a dict")
    if not isinstance(embedding_artifact, dict):
        raise IngestionError("embedding_artifact must be a dict")

    parsed_doc_id = (parsed_document.get("provenance") or {}).get("document_id")
    pages = parsed_document.get("pages")
    if not isinstance(pages, list):
        raise IngestionError("parsed_document has no pages list")
    chunk_doc_id = chunk_output.get("document_id")
    emb_doc_id = embedding_artifact.get("document_id")
    for label, value in (
        ("parsed_document", parsed_doc_id),
        ("chunk_output", chunk_doc_id),
        ("embedding_artifact", emb_doc_id),
    ):
        if value != document_id:
            raise IngestionError(
                f"{label} document_id {value!r} != expected {document_id!r}"
            )

    chunks = chunk_output.get("chunks")
    embeddings = embedding_artifact.get("embeddings")
    if not isinstance(chunks, list):
        raise IngestionError("chunk_output has no chunks list")
    if not isinstance(embeddings, list):
        raise IngestionError("embedding_artifact has no embeddings list")

    total_chunks = len(chunks)
    embedded_chunks = len(embeddings)
    if total_chunks != embedded_chunks:
        raise IngestionError(
            f"chunk count {total_chunks} != embedding count {embedded_chunks} "
            f"for {document_id!r} (no silent drops)"
        )

    failed_pages = sorted(
        page["page_number"]
        for page in pages
        if isinstance(page, dict)
        and page.get("extraction_status") == "failed"
        and isinstance(page.get("page_number"), int)
    )
    total_pages = len(pages)
    parsed_pages = total_pages - len(failed_pages)

    return {
        "document_id": document_id,
        "total_pages": total_pages,
        "parsed_pages": parsed_pages,
        "failed_pages": failed_pages,
        "total_chunks": total_chunks,
        "embedded_chunks": embedded_chunks,
        "indexed_chunks": total_chunks,
        "ingestion_status": "success" if not failed_pages else "partial",
    }


def report_path(repo_root: str | Path, corpus_version: str, document_id: str) -> Path:
    """Return the canonical report path (parent dirs not created)."""
    return (
        Path(repo_root)
        / REPORT_DIR_NAME
        / corpus_version
        / document_id
        / f"{document_id}{REPORT_FILENAME_SUFFIX}"
    )


def write_ingestion_report(report: dict, path: str | Path) -> Path:
    """Write one report as indented JSON, creating parent dirs as needed."""
    if not isinstance(report, dict) or not report.get("document_id"):
        raise IngestionError("report must carry a document_id")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return out
