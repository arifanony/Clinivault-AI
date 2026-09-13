"""Baseline prompt construction for Clinivault AI.

Pure function: context bundle -> prompt text. No provider, no retrieval,
no summarization, no truncation (context limits are a generation-stage
concern, not prompt-construction).

Responsibility: put the query and the supplied evidence into a prompt in a
stable, inspectable form, with explicit instructions to answer only from
the supplied evidence and not to invent unsupported facts.
"""

from __future__ import annotations

from typing import Any


def build_prompt(bundle: dict[str, Any]) -> str:
    """Build a baseline grounded-generation prompt from a context bundle.

    The bundle input contract is the output of ``clinivault_ai.context
    .build_context``:

        {query, evidence_count, documents, evidence:[{rank, chunk_id,
        document_id, page_number, score, text}, ...]}

    The prompt includes:
    - the original query verbatim
    - each evidence item verbatim, with stable citation identifiers
      (rank, chunk_id, document_id, page_number)
    - an explicit instruction to answer using only the supplied evidence
      and not to invent unsupported facts
    """
    if not isinstance(bundle, dict):
        raise ValueError("bundle must be a dict")
    if "query" not in bundle:
        raise ValueError("bundle must include 'query'")
    if "evidence" not in bundle:
        raise ValueError("bundle must include 'evidence'")
    if not isinstance(bundle["evidence"], list):
        raise ValueError("bundle evidence must be a list")

    query = bundle["query"]
    evidence = bundle["evidence"]

    system_footer = (
        "Answer using ONLY the evidence above.\n"
        "Do not invent facts, explanations, or citations that are NOT "
        "supported by the supplied evidence.\n"
        "If the supplied evidence does not contain enough information to "
        "answer, say so explicitly and do NOT fabricate an answer.\n"
        "Do not add external knowledge, outside sources, or assumptions.\n"
        "Where possible, tie your answer to the specific evidence items you "
        "used (cite their rank, chunk_id, document_id, and page).\n"
    )

    lines: list[str] = []
    lines.append("You are answering a question using only the supplied evidence.")
    lines.append("EVALUATED_QUESTION:")
    lines.append(query)
    lines.append("")
    lines.append(
        f"TOTAL_SUPPLIED_EVIDENCE_ITEMS: {len(evidence)}"
        if evidence
        else "TOTAL_SUPPLIED_EVIDENCE_ITEMS: 0"
    )
    lines.append("SUPPLIED_EVIDENCE:")
    lines.append("")

    for item in evidence:
        _append_evidence_item(lines, item)

    lines.append("")
    lines.append(system_footer)
    return "\n".join(lines) + "\n"


def _append_evidence_item(lines: list[str], item: dict[str, Any]) -> None:
    """Append one evidence item verbatim, with citation identifiers."""
    for key in ("rank", "chunk_id", "document_id", "page_number"):
        if key not in item:
            raise ValueError(f"evidence item missing {key!r}")
    if "text" not in item:
        raise ValueError("evidence item missing 'text'")

    lines.append(f"EVIDENCE_ITEM_RANK: {item['rank']}")
    lines.append(f"EVIDENCE_ITEM_CHUNK_ID: {item['chunk_id']}")
    lines.append(f"EVIDENCE_ITEM_DOCUMENT_ID: {item['document_id']}")
    lines.append(f"EVIDENCE_ITEM_PAGE_NUMBER: {item['page_number']}")
    lines.append("EVIDENCE_TEXT:")
    lines.append(item["text"])
    lines.append("---")
