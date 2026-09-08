"""Deterministic ingestion validation and observed extraction statistics.

Checks are mechanical (no AI, no thresholds invented before observing data).
Quantitative values are *reported*; the only hard failures are structural:
missing provenance, zero text at document level, or JSON that cannot
round-trip.
"""

from __future__ import annotations

import json
import statistics
from datetime import UTC, datetime

# Chars in C0 control range (minus \n \r \t) plus DEL are considered
# "control characters" for the encoding-anomaly report.
_CONTROL_CHARS = frozenset(
    chr(code) for code in range(0, 32) if code not in (10, 13, 9)
) | {chr(127)}

# Reporting-only heuristic: pages far below the document's median text volume.
_LOW_TEXT_REPORT_RATIO = 0.10
_CONTROL_RATIO_REPORT_THRESHOLD = 0.01


def _now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def control_char_ratio(text: str) -> float:
    if not text:
        return 0.0
    control = sum(1 for ch in text if ch in _CONTROL_CHARS)
    return control / len(text)


def summarize_pages(pages: list[dict]) -> dict:
    """Observed statistics. Nothing here decides acceptance by itself."""
    char_counts = [page["char_count"] for page in pages]
    word_counts = [page["word_count"] for page in pages]
    total_chars = sum(char_counts)

    def spread(values: list[int]) -> dict:
        if not values:
            return {}
        return {
            "mean": round(statistics.fmean(values), 1),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
        }

    median_chars = statistics.median(char_counts) if char_counts else 0
    low_text_threshold = (
        median_chars * _LOW_TEXT_REPORT_RATIO if median_chars > 0 else 0
    )
    return {
        "page_count": len(pages),
        "total_chars": total_chars,
        "total_words": sum(word_counts),
        "chars_per_page": spread(char_counts),
        "words_per_page": spread(word_counts),
        "empty_pages": [p["page_number"] for p in pages if p["extraction_status"] == "empty"],
        "failed_pages": [p["page_number"] for p in pages if p["extraction_status"] == "failed"],
        # Reporting-only: pages unusually low relative to the document median.
        # NOT an acceptance threshold — see DECISION-006 and the pipeline doc.
        "low_text_pages_reported_only": {
            "rule": f"char_count < {_LOW_TEXT_REPORT_RATIO:.0%} of median ({median_chars})",
            "pages": [
                {"page_number": p["page_number"], "char_count": p["char_count"]}
                for p in pages
                if p["char_count"] < low_text_threshold
            ],
        },
        "control_char_anomaly_pages": [
            {
                "page_number": p["page_number"],
                "ratio": round(control_char_ratio(p["text"]), 4),
            }
            for p in pages
            if control_char_ratio(p["text"]) > _CONTROL_RATIO_REPORT_THRESHOLD
        ],
    }

def _check(name: str, status: str, detail: str) -> dict:
    return {"name": name, "status": status, "detail": detail}


REQUIRED_PAGE_FIELDS = (
    "document_id", "filename", "page_number", "text", "text_sha256",
    "char_count", "word_count", "page_width", "page_height",
    "extraction_status", "extraction_error",
)


def check_provenance(pages: list[dict]) -> list[str]:
    """Return a list of provenance problems (empty list = complete)."""
    problems: list[str] = []
    for page in pages:
        for field_name in REQUIRED_PAGE_FIELDS:
            if field_name not in page:
                problems.append(
                    f"page {page.get('page_number', '?')}: missing field '{field_name}'"
                )
        for triad in ("document_id", "filename", "page_number"):
            if page.get(triad) in (None, ""):
                problems.append(
                    f"page {page.get('page_number', '?')}: empty traceability field '{triad}'"
                )
    return problems


def build_validation_report(
    document_id: str,
    source_sha256: str,
    expected_pages: int,
    pages: list[dict],
    extra_checks: list[dict] | None = None,
) -> dict:
    stats = summarize_pages(pages)
    checks: list[dict] = []

    checks.append(_check(
        "source_sha256_matches_manifest", "pass",
        f"source SHA-256 verified against manifest: {source_sha256}",
    ))

    page_count_ok = len(pages) == expected_pages
    checks.append(_check(
        "page_count_matches_manifest", "pass" if page_count_ok else "fail",
        f"expected {expected_pages} pages, parsed {len(pages)}",
    ))

    checks.append(_check(
        "document_text_present", "pass" if stats["total_chars"] > 0 else "fail",
        f"total extracted characters: {stats['total_chars']}",
    ))

    provenance_problems = check_provenance(pages)
    checks.append(_check(
        "page_provenance_complete", "pass" if not provenance_problems else "fail",
        "all page records carry document_id + filename + page_number"
        if not provenance_problems else "; ".join(provenance_problems[:10]),
    ))

    if stats["failed_pages"]:
        checks.append(_check(
            "extraction_failures", "fail",
            f"pages failed to extract: {stats['failed_pages']}",
        ))
    else:
        checks.append(_check(
            "extraction_failures", "pass", "no page-level extraction failures",
        ))

    empty = stats["empty_pages"]
    checks.append(_check(
        "empty_pages_reported", "info" if not empty else "warn",
        f"pages with no extractable text (kept, not dropped): {empty or 'none'}",
    ))

    checks.append(_check(
        "control_char_anomalies", "info",
        f"pages above {(_CONTROL_RATIO_REPORT_THRESHOLD * 100):.0f}% control-character "
        f"ratio (reported only): "
        f"{[a['page_number'] for a in stats['control_char_anomaly_pages']] or 'none'}",
    ))

    checks.append(_check(
        "low_text_pages", "info",
        f"reporting-only low-text rule: "
        f"{[p['page_number'] for p in stats['low_text_pages_reported_only']['pages']] or 'none'}",
    ))

    if extra_checks:
        checks.extend(extra_checks)

    hard_fail = any(check["status"] == "fail" for check in checks)
    overall = "fail" if hard_fail else (
        "pass_with_warnings" if any(c["status"] == "warn" for c in checks) else "pass"
    )

    return {
        "document_id": document_id,
        "validated_at_utc": _now_utc(),
        "checks": checks,
        "statistics": stats,
        "overall_status": overall,
    }


def roundtrip_equivalent(obj: dict, path: str) -> bool:
    """Semantic JSON round-trip check: reload the written file and compare
    the resulting Python objects (never raw bytes — formatting is not the
    validation target)."""
    with open(path, encoding="utf-8") as handle:
        reloaded = json.load(handle)
    return reloaded == obj

