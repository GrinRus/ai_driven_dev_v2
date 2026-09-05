# Repair prompt for `idea`

You are rerunning the `idea` stage because validation failed.

Your job is to resolve validator findings with minimal, auditable edits while keeping document
contracts consistent.

## Runtime write authority

Write only `idea-brief.md` as the substantive repair output. Do not write `stage-result.md` or
`validator-report.md`; AIDD owns their canonical status, validation, history, and publication.
Never create, edit, delete, or replace either record; if a finding names one, expose the needed
correction in `idea-brief.md` and let AIDD reconcile the workflow record.
Read existing workflow records as evidence. Use the controlled interview path for questions
and operator answers; do not invent answers.

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
any repair summary in `idea-brief.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Validator-report protocol v1

Read `validator-report.md` as AIDD-owned finding evidence; do not rewrite it:

- interpret the canonical fields `Total issues`, `Blocking issues`, `Affected documents`,
  `Dominant failure categories`, optional `Finding occurrences`, `Verdict`, and
  `Repair required for progression`;
- when citing a finding, copy only finding codes declared by
  `contracts/documents/validator-report.md`; do not invent, rename, or generalize a code;
- recognize `Validator verdict` and `Repair required` as read-only legacy field aliases;
  AIDD writers emit the canonical labels;
- recognize `STRUCT-MISSING-DOCUMENT`, `STRUCT-MISSING-HEADING`,
  `STRUCT-EMPTY-SECTION`, and `CROSS-REFERENCE-MISMATCH` as read-only legacy codes.

Any other field alias or finding code is invalid protocol vocabulary. Report unknown input
vocabulary in substantive runtime content instead of changing the validator report. If it or any
other blocker prevents completion, submit a `[blocking]` question through the controlled
interview path; substantive blocker prose alone does not pause AIDD.

`idea-brief.md` list sections are strict. `Constraints` and `Open questions` must use top-level
Markdown bullet items; if there are no constraints or no open questions, write exactly `- none`
under that heading. Prose such as `No open questions.` is still invalid.

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not use `- Q1: [resolved] ...`; it is invalid. Do not invent `A1`/`A2` answer ids.
If no operator answer is present, write `# Answers\n\n- none\n`; do not create `[resolved]`
answers yourself. Render assumptions or metadata as non-bullet continuation prose.
If authored task or acceptance context explicitly requires blocking answers, interview answers,
or operator policy decisions before downstream planning or implementation, preserve those questions
as `[blocking]`; do not repair them into `[non-blocking]` assumptions.

## Finding-to-fix mapping

For each finding in `validator-report.md`, apply this sequence:

1. Identify root cause in the source document, not only the symptom text.
2. Patch the smallest possible section that resolves the issue code.
3. Re-check cross-document consistency, especially:
   - substantive repair evidence vs the previous validator findings (read-only),
   - blockers vs unresolved `[blocking]` questions,
   - question ids between `questions.md` and `answers.md`.
4. Keep unchanged content intact; do not rewrite valid sections.

Use these concrete repair actions:

- `STRUCT-MISSING-DOCUMENT`: create the missing required Markdown document with contract headings.
- `STRUCT-MISSING-HEADING` / `STRUCT-EMPTY-SECTION`: add or complete the exact required heading content.
- `SEM-PLACEHOLDER-CONTENT`: inspect the exact token and line named by the finding, replace
  it with concrete, supportable content, and preserve every unaffected section.
- `SEM-INCOMPLETE-SECTION` in an AIDD-generated record: expose the actual blockers or their
  absence in substantive runtime content; AIDD reconciles its own record. Never erase a
  concrete blocker or an unresolved blocking question.
- `SEM-INCOMPLETE-SECTION` for `Constraints` or `Open questions`: convert the section to top-level
  Markdown bullet items, or use exactly `- none` when there are no entries.
- `SEM-UNSUPPORTED-CLAIM`: remove unsupported claim or restate it as an explicit assumption.
- `CROSS-REFERENCE-MISMATCH`: align conflicting references and artifact paths.
- `CROSS-BLOCKING-UNANSWERED`: preserve unresolved questions until matching resolved answers exist;
  AIDD keeps the stage blocked.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `idea-brief.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.

## Repair rules

1. Preserve stable question ids and markers (`[blocking]`, `[non-blocking]`, `[resolved]`).
2. Keep workspace-relative artifact paths wrapped in backticks in `idea-brief.md`.
3. Never claim unresolved findings are fixed; AIDD determines `succeeded` after validation.
4. Do not hide unresolved blockers; record them explicitly under `Blockers`.
5. Expose truthful repair evidence in `idea-brief.md`; AIDD preserves attempt history.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before reporting the repair outcome.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed substantive findings; AIDD derives terminal status from post-runtime validation; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, AIDD sets terminal status to `failed`.
10. Do not claim the repair is complete unless required headings and blockers are mutually consistent.
11. If all listed findings are resolved and no blockers remain, record the repaired evidence in `idea-brief.md`; AIDD determines `succeeded` after validation. Do not treat the previous failed validator report as a new result.

## Repair exit checks

- every finding is resolved or explicitly retained as an active blocker,
- required sections are complete and non-placeholder,
- `validator-report.md` verdict and `stage-result.md` status are consistent,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- unresolved `[blocking]` questions still prevent `succeeded`.
