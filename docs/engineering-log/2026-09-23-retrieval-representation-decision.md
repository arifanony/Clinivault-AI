# Engineering Log: Retrieval Representation Decision After 46-Case Evaluation

- **Date:** 2026-09-23
- **Task:** DECISION-016-RETRIEVAL-REPRESENTATION
- **Author:** Coding Agent

## Changed Understanding

DECISION-010's baseline-retention conclusion was correct for the earlier frozen
21-case comparison but could not be carried forward unchanged after
DECISION-014 made the 46-case benchmark authoritative. On the expanded set,
Gemini semantic retrieval measured 21/46 Hit@1, 42/46 Hit@5, and MRR 0.6109,
against the hash baseline's 12/46, 26/46, and 0.3601. Local semantic screening
then showed raw `intfloat/e5-small-v2` at 20/46, 36/46, and 0.5583.

EVAL-HF-003 closed the only identified E5 protocol limitation: intended
`query:`/`passage:` formatting did not improve the frozen benchmark (19/46,
35/46, 0.5486), while raw reproduced EVAL-HF-002 exactly and T2D-001 raw
vectors matched the persisted artifact byte-for-byte.

## Decision Impact

[DECISION-016](../decisions/DECISION-016-retrieval-representation.md) replaces
DECISION-010 as the forward-looking representation decision. It selects local
dense semantic retrieval, with raw E5-small as the leading candidate for a
separately authorized future integration unit. It does not alter production
retrieval, corpus artifacts, benchmark definitions, labels, metrics, or Top-K.

## Limits Preserved

- The 46-case benchmark does not establish a universal model winner or
  statistical significance between close local-model results.
- Raw E5 is not characterized as statistically better than intended E5
  formatting; normalization simply did not help on this benchmark.
- Gemini remains the higher measured aggregate-quality reference, but its cloud
  dependency does not meet the current MVP offline/cost constraint.