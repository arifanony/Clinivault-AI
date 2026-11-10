"""Document catalog for the Stage-1 clean baseline corpus (M3).

Single source of truth for brief-level metadata joined onto retrieval
results and context bundles at index time. Values are transcribed from
``docs/corpus/corpus-manifest.md`` only; nothing is guessed from PDF text.
T2D-004 is blocked-access and has no entry here by design.
"""

from __future__ import annotations

DOCUMENT_CATALOG: dict[str, dict[str, str]] = {
    "T2D-001": {
        "document_id": "T2D-001",
        "document_name": "Standards of Care in Diabetes \u2014 2026, Section 2: Diagnosis and Classification of Diabetes",
        "source": "Diabetes Care 49(Supplement 1), ADA (official publisher)",
        "publication_date": "2026 (January)",
        "version": "2026 Standards of Care",
        "ingestion_date": "2026-09-10",
    },
    "T2D-002": {
        "document_id": "T2D-002",
        "document_name": "Prediabetes and Type 2 Diabetes: Screening",
        "source": "USPSTF (recommendation statement)",
        "publication_date": "2021",
        "version": "2021 final recommendation statement",
        "ingestion_date": "2026-09-16",
    },
    "T2D-003": {
        "document_id": "T2D-003",
        "document_name": "Diagnostic accuracy of tests for type 2 diabetes and prediabetes: A systematic review and meta-analysis",
        "source": "PLOS ONE (publisher of record)",
        "publication_date": "2020 (December)",
        "version": "",
        "ingestion_date": "2026-09-15",
    },
    "T2D-005": {
        "document_id": "T2D-005",
        "document_name": "Standards of Care in Diabetes \u2014 2026, Section 6: Glycemic Goals, Hypoglycemia, and Hyperglycemic Crises",
        "source": "Diabetes Care 49(Supplement 1), ADA (official publisher)",
        "publication_date": "2026",
        "version": "2026 Standards of Care",
        "ingestion_date": "2026-09-15",
    },
    "T2D-006": {
        "document_id": "T2D-006",
        "document_name": "Standards of Care in Diabetes \u2014 2026, Section 9: Pharmacologic Approaches to Glycemic Treatment",
        "source": "Diabetes Care 49(Supplement 1), ADA (official publisher)",
        "publication_date": "2026",
        "version": "2026 Standards of Care",
        "ingestion_date": "2026-09-15",
    },
    "T2D-007": {
        "document_id": "T2D-007",
        "document_name": "Newer Pharmacologic Treatments in Adults With Type 2 Diabetes: A Clinical Guideline",
        "source": "ACP clinical guideline (full text deposited in PMC)",
        "publication_date": "2024",
        "version": "",
        "ingestion_date": "2026-09-15",
    },
    "T2D-008": {
        "document_id": "T2D-008",
        "document_name": "Medications for adults with type 2 diabetes: a living systematic review and network meta-analysis",
        "source": "The BMJ (official publisher)",
        "publication_date": "2025",
        "version": "",
        "ingestion_date": "2026-09-15",
    },
    "T2D-009": {
        "document_id": "T2D-009",
        "document_name": "Standards of Care in Diabetes \u2014 2026, Section 10: Cardiovascular Disease and Risk Management",
        "source": "Diabetes Care 49(Supplement 1), ADA (official publisher)",
        "publication_date": "2026",
        "version": "2026 Standards of Care",
        "ingestion_date": "2026-09-15",
    },
    "T2D-010": {
        "document_id": "T2D-010",
        "document_name": "Standards of Care in Diabetes \u2014 2026, Section 11: Chronic Kidney Disease and Risk Management",
        "source": "Diabetes Care 49(Supplement 1), ADA (official publisher)",
        "publication_date": "2026",
        "version": "2026 Standards of Care",
        "ingestion_date": "2026-09-18",
    },
}


def get_document_metadata(document_id: str) -> dict[str, str] | None:
    """Return a copy of the catalog entry, or None when unknown."""
    entry = DOCUMENT_CATALOG.get(document_id)
    return dict(entry) if entry is not None else None


def get_document_name(document_id: str) -> str | None:
    """Return the catalog title for a known document, else None."""
    entry = DOCUMENT_CATALOG.get(document_id)
    if entry is None:
        return None
    return entry["document_name"]
