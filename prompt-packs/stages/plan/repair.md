# Repair prompt for `plan`

You are rerunning the `plan` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose the root cause before editing (incomplete sections, weak sequencing, unclear acceptance signals, or risk/verification mismatch).
3. Correct only missing or incorrect parts while preserving valid plan sections.
4. Keep milestone order and dependency logic stable unless validator findings require a change.
5. Rework risk and verification notes together when one side is insufficient.
6. Update `stage-result.md` and `validator-report.md` so attempt history and readiness status are truthful.

## Repair exit checks

- completeness gaps are resolved or explicitly documented as blocking,
- sequencing logic is coherent after edits,
- user-approval signals are explicit enough for review,
- `stage-result.md` does not declare `succeeded` while blocking findings remain.
