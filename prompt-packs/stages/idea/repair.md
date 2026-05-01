# Repair prompt for `idea`

You are rerunning the `idea` stage because validation failed.

Your job is to resolve validator findings with minimal, auditable edits while keeping document
contracts consistent.

## Read order (do not skip)

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/idea.md` (stage rules and exit states)
4. `contracts/documents/validator-report.md` and `contracts/documents/stage-result.md`
5. current output documents:
   - `idea-brief.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md`.

## Finding-to-fix mapping

For each finding in `validator-report.md`, apply this sequence:

1. Identify root cause in the source document, not only the symptom text.
2. Patch the smallest possible section that resolves the issue code.
3. Re-check cross-document consistency, especially:
   - `stage-result.md` status vs validator verdict,
   - blockers vs unresolved `[blocking]` questions,
   - question ids between `questions.md` and `answers.md`.
4. Keep unchanged content intact; do not rewrite valid sections.

Use these concrete repair actions:

- `STRUCT-MISSING-DOCUMENT`: create the missing required Markdown document with contract headings.
- `STRUCT-MISSING-HEADING` / `STRUCT-EMPTY-SECTION`: add or complete the exact required heading content.
- `SEM-PLACEHOLDER-CONTENT`: replace placeholders with concrete, supportable statements.
- `SEM-UNSUPPORTED-CLAIM`: remove unsupported claim or restate it as an explicit assumption.
- `CROSS-REFERENCE-MISMATCH`: align conflicting references and artifact paths.
- `CROSS-BLOCKING-UNANSWERED`: keep stage terminal status blocked until matching resolved answers exist.

## Repair rules

1. Preserve stable question ids and markers (`[blocking]`, `[non-blocking]`, `[resolved]`).
2. Keep workspace-relative artifact paths wrapped in backticks in `stage-result.md`.
3. Never mark stage status `succeeded` when validator verdict is `fail`.
4. Do not hide unresolved blockers; record them explicitly under `Blockers`.
5. Ensure attempt history reflects this repair attempt truthfully.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-exhausted` or `Rerun allowed after this attempt: no`, `stage-result.md` status must be `failed`; do not claim `succeeded`.
9. Do not claim success unless required headings, validator verdict, stage-result status, and blockers are mutually consistent.

## Repair exit checks

- every finding is resolved or explicitly retained as an active blocker,
- required sections are complete and non-placeholder,
- `validator-report.md` verdict and `stage-result.md` status are consistent,
- repair-budget exhaustion cannot coexist with `stage-result.md` status `succeeded`,
- unresolved `[blocking]` questions still prevent `succeeded`.
