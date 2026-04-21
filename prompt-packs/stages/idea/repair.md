# Repair prompt for `idea`

You are rerunning the `idea` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Identify the root cause of each finding before editing documents.
3. Correct only missing or incorrect parts, but keep cross-document consistency across `idea-brief.md`, `validator-report.md`, and `stage-result.md`.
4. Preserve valid content; do not rewrite sections that already satisfy the contract.
5. Remove placeholder or unsupported statements from required sections instead of masking them.
6. Keep question ids stable; unresolved `[blocking]` questions must remain visible.
7. Update `stage-result.md` so attempt history, validation summary, blockers, and next actions reflect the repaired attempt truthfully.

## Repair exit checks

- every repaired finding is either resolved or explicitly documented as still blocking,
- no required section regresses to placeholder content,
- `stage-result.md` does not declare `succeeded` when validator verdict is `fail`.
