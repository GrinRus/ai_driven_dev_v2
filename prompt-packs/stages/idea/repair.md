# Repair prompt for `idea`

You are rerunning the `idea` stage because validation failed.

Your job is to resolve validator findings with minimal, auditable edits while keeping document
contracts consistent.

## Read order (do not skip)

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/idea.md` (stage rules and exit states)
4. `contracts/documents/validator-report.md` and `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. current output documents:
   - `idea-brief.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

`idea-brief.md` list sections are strict. `Constraints` and `Open questions` must use top-level
Markdown bullet items; if there are no constraints or no open questions, write exactly `- none`
under that heading. Prose such as `No open questions.` is still invalid.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not invent `A1`/`A2` answer ids. Render assumptions or metadata as non-bullet continuation prose.

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
- `SEM-INCOMPLETE-SECTION` for `Constraints` or `Open questions`: convert the section to top-level
  Markdown bullet items, or use exactly `- none` when there are no entries.
- `SEM-UNSUPPORTED-CLAIM`: remove unsupported claim or restate it as an explicit assumption.
- `CROSS-REFERENCE-MISMATCH`: align conflicting references and artifact paths.
- `CROSS-BLOCKING-UNANSWERED`: keep stage terminal status blocked until matching resolved answers exist.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve stable question ids and markers (`[blocking]`, `[non-blocking]`, `[resolved]`).
2. Keep workspace-relative artifact paths wrapped in backticks in `stage-result.md`.
3. Never mark stage status `succeeded` when validator verdict is `fail`.
4. Do not hide unresolved blockers; record them explicitly under `Blockers`.
5. Ensure attempt history reflects this repair attempt truthfully.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, and blockers are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.

## Repair exit checks

- every finding is resolved or explicitly retained as an active blocker,
- required sections are complete and non-placeholder,
- `validator-report.md` verdict and `stage-result.md` status are consistent,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- unresolved `[blocking]` questions still prevent `succeeded`.
