# Repair prompt for `review`

You are rerunning the `review` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose root causes before editing (`unsupported findings`, `missing severity`, `absent disposition`, or approval-status mismatch).
3. Correct only missing or incorrect parts while preserving valid evidence-backed findings.
4. Rework severity/disposition labels and approval decision together when finding profile changes.
5. Remove or reclassify any finding that cannot be tied to implementation evidence or acceptance criteria.
6. Update `stage-result.md` and `validator-report.md` so repaired attempt status is truthful.

## Repair exit checks

- every remaining finding has stable id, severity, disposition, and rationale,
- no unsupported or evidence-free finding remains,
- approval status is coherent with unresolved `must-fix` findings,
- validator result and stage status do not conflict.
