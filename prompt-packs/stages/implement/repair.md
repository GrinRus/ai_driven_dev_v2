# Repair prompt for `implement`

You are rerunning the `implement` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose root causes before editing (`missing diffs`, `unverifiable claims`, `incomplete summary`, or invalid no-op rationale).
3. Correct only missing or incorrect parts while preserving valid, evidence-backed sections.
4. Rework touched-files list and verification notes together when any implementation claim changes.
5. If result is a no-op, include explicit justification, evidence, and actionable next step; otherwise treat no-op as invalid.
6. Update `stage-result.md` and `validator-report.md` so repaired attempt status is truthful.

## Repair exit checks

- no claim about edits or checks remains without observable evidence,
- touched-files list, change summary, and verification notes are mutually consistent,
- no-op outcomes (if any) include justification, evidence, and next action,
- validator result and stage status do not conflict.
