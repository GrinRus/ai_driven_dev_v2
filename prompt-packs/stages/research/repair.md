# Repair prompt for `research`

You are rerunning the `research` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose root causes before editing (missing evidence, broken citations, stale claims, or unresolved ambiguity).
3. Correct only missing or incorrect parts while preserving valid sections.
4. Re-ground unsupported findings with citations or downgrade them to explicit assumptions.
5. Keep citation ids and question ids stable across repair attempts.
6. Update `stage-result.md` and `validator-report.md` so attempt history and status reflect the repaired outcome truthfully.

## Repair exit checks

- every blocking validator finding is resolved or explicitly remains blocking,
- all material findings are evidence-linked or clearly marked as assumptions,
- unresolved `[blocking]` questions remain visible and prevent `succeeded` status.
