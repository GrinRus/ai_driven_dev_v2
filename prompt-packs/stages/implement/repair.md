# Repair prompt for `implement`

You are rerunning the `implement` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving task alignment,
scope safety, verification truthfulness, and cross-document status consistency.

## Read order (do not skip)

1. `validator-report.md` (latest findings, severities, and locations)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/implement.md`
4. `contracts/documents/implementation-report.md`,
   `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. current outputs:
   - `implementation-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md`.

## Finding-to-fix mapping

For each finding:

1. identify the root cause class:
   - `missing diffs`,
   - `unverifiable claims`,
   - `incomplete summary`,
   - `invalid no-op rationale`,
   - cross-document status drift;
2. patch only the smallest affected section(s) of `implementation-report.md`;
3. re-check touched-files entries against observable repository changes and allowed write scope;
4. re-check `stage-result.md` and `validator-report.md` for status/blocker consistency.

Use concrete repair actions:

- `missing diffs`: remove unsupported touched-files claims or add missing concrete entries that match
  observed edits;
- `unverifiable claims`: replace vague assertions with concrete command/check outcomes, or mark as
  not-run explicitly;
- `incomplete summary`: rewrite change summary so it maps selected task id -> edits -> outcomes;
- `invalid no-op`: add evidence-backed justification and actionable next step, or convert run from
  no-op to real scoped edits;
- status drift: align validator verdict, stage status, blockers, and next actions.

## Repair rules

1. Preserve valid evidence-backed sections; do not rewrite unaffected parts.
2. Keep selected task id and scope constraints explicit after every edit.
3. Rework touched-files list and verification notes together whenever implementation claims change.
4. Do not claim commands/checks that were not executed in this attempt.
5. If no-op is retained, include justification, evidence, and next action; otherwise no-op is invalid.
6. Keep `stage-result.md` attempt status truthful for the current repair attempt.
7. Use exact required headings from document contracts; do not rename or qualify headings.
8. Read the repair budget section in `repair-brief.md` before declaring terminal status.
9. If `repair-brief.md` says `repair-budget-exhausted` or `Rerun allowed after this attempt: no`, `stage-result.md` status must be `failed`; do not claim `succeeded`.
10. Do not claim success unless required headings, validator verdict, stage-result status, touched files, and verification evidence are mutually consistent.

## Repair exit checks

- no edit or verification claim remains without observable evidence,
- selected task id, change summary, touched-files list, and verification notes are mutually consistent,
- touched-files entries stay within allowed write scope and match observed edits,
- no-op outcomes (if any) include evidence-backed rationale and actionable next step,
- repair-budget exhaustion cannot coexist with `stage-result.md` status `succeeded`,
- no status drift remains between `implementation-report.md`, `validator-report.md`, and `stage-result.md`.
