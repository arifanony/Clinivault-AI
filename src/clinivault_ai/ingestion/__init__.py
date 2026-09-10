"""Ingestion pipeline: verified PDF -> structured parsed page data.

Pipeline (one document per run):

    PDF source verification (source.py)
        -> page-level parsing (parsing.py, pdfplumber per DECISION-006)
        -> page-level structured representation
        -> deterministic ingestion validation (validation.py)
        -> JSON serialization + reload-equivalence check (output.py)

Concerns are deliberately separated across small modules; this module only
orchestrates them and exposes the command-line entry point.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from importlib.metadata import version as _package_version
from pathlib import Path

from .errors import IngestionError
from .output import load_json, write_json
from .parsing import parse_pages
from .source import verify_source
from .validation import build_validation_report, roundtrip_equivalent

PIPELINE_VERSION = "0.2.0"
PARSER_NAME = "pdfplumber"


def _parser_version() -> str:
    return _package_version(PARSER_NAME)


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def derive_document_id(source_path: Path) -> str:
    """Corpus files are named ``<DOC-ID>-slug.pdf``; derive the ID from that."""
    stem = source_path.stem
    parts = stem.split("-")
    if len(parts) >= 2:
        return f"{parts[0]}-{parts[1]}".upper()
    return stem


def run_ingestion(
    source_path: str | Path,
    output_dir: str | Path,
    expected_sha256: str,
    expected_pages: int,
    document_id: str | None = None,
) -> dict:
    """Ingest one verified PDF. Returns a summary dict for the caller/CLI."""
    source = Path(source_path)
    out_dir = Path(output_dir)

    # 1. Source verification (existence, checksum, open, page count).
    info = verify_source(source, expected_sha256, expected_pages)
    doc_id = document_id or derive_document_id(source)

    # 2./3. Page-level extraction -> structured page records.
    pages = parse_pages(info.path, doc_id, str(source))

    provenance = {
        "document_id": doc_id,
        "source_filename": str(source),
        "source_sha256": info.sha256,
        "page_count": info.page_count,
        "parser": {"name": PARSER_NAME, "version": _parser_version()},
        "pdf_metadata": info.metadata,
        "extraction_timestamp_utc": _now_utc(),
        "pipeline_version": PIPELINE_VERSION,
    }
    parsed_document = {"provenance": provenance, "pages": pages}

    # 5. Serialization + semantic reload check.
    parsed_path = out_dir / f"{doc_id}.parsed.json"
    write_json(parsed_path, parsed_document)
    reload_ok = roundtrip_equivalent(parsed_document, str(parsed_path))

    # 4. Deterministic validation (includes the reload check result).
    extra = [{
        "name": "json_reload_equivalent",
        "status": "pass" if reload_ok else "fail",
        "detail": "reloaded JSON equals the in-memory document (semantic compare)",
    }]
    report = build_validation_report(
        doc_id, info.sha256, expected_pages, pages, extra_checks=extra,
    )
    validation_path = out_dir / f"{doc_id}.validation.json"
    write_json(validation_path, report)

    return {
        "document_id": doc_id,
        "parsed_path": str(parsed_path),
        "validation_path": str(validation_path),
        "reload_ok": reload_ok,
        "overall_status": report["overall_status"],
        "statistics": report["statistics"],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clinivault-ai ingest",
        description="Ingest one verified PDF into structured parsed page data.",
    )
    parser.add_argument("source", help="path to the raw PDF (never modified)")
    parser.add_argument("--document-id", default=None,
                        help="stable document ID (default: derived from filename)")
    parser.add_argument("--expected-sha256", required=True,
                        help="SHA-256 recorded for this document in the corpus manifest")
    parser.add_argument("--expected-pages", type=int, required=True,
                        help="page count recorded for this document in the corpus manifest")
    parser.add_argument("--output-dir", required=True,
                        help="directory for <DOC-ID>.parsed.json and <DOC-ID>.validation.json")
    return parser


def cli(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        summary = run_ingestion(
            source_path=args.source,
            output_dir=args.output_dir,
            expected_sha256=args.expected_sha256,
            expected_pages=args.expected_pages,
            document_id=args.document_id,
        )
    except IngestionError as exc:
        print(f"ingestion failed: {exc}", file=sys.stderr)
        return 2

    stats = summary["statistics"]
    print(f"document_id      : {summary['document_id']}")
    print(f"overall_status   : {summary['overall_status']}")
    print(f"pages            : {stats['page_count']}")
    print(f"total_chars      : {stats['total_chars']}")
    print(f"empty_pages      : {stats['empty_pages'] or 'none'}")
    print(f"failed_pages     : {stats['failed_pages'] or 'none'}")
    print(f"parsed output    : {summary['parsed_path']}")
    print(f"validation output: {summary['validation_path']}")
    print(f"json reload ok   : {summary['reload_ok']}")
    return 0


def main() -> None:  # pragma: no cover - thin CLI wrapper
    raise SystemExit(cli())


if __name__ == "__main__":
    main()
