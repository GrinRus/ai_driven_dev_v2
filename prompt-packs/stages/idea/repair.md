# Repair prompt for `idea`

You are rerunning the `idea` stage because validation failed.

Your job is to resolve validator findings with minimal, auditable edits while keeping document
contracts consistent.

## Read order (do not skip)

Read `stage-brief.md`, the current `idea-brief.md`, and its
`contracts/documents/idea-brief.md` contract before applying the findings.
1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/idea.md` (stage rules and exit states)
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

`idea-brief.md` list sections are strict. `Constraints` and `Open questions` must use top-level
Markdown bullet items; if there are no constraints or no open questions, write exactly `- none`
under that heading. Prose such as `No open questions.` is still invalid.

## Interview context

Read `contracts/documents/questions.md` and `contracts/documents/answers.md` when available.
Use stable QIDs and canonical `- Q1 [blocking] ...` or `- Q1 [non-blocking] ...` question
candidates through the controlled interview path. AIDD merges raw candidates and may normalize
safe presentation differences without changing meaning. Preserve unresolved blocking questions.
Operator answers use the same QID, for example `- Q1 [resolved] ...`; do not create or edit
`answers.md`, invent `A1`/`A2` answer ids, or create `[resolved]` answers yourself. Missing
answers remain an operator checkpoint. Render assumptions as non-bullet continuation prose.
If authored task or acceptance context explicitly requires blocking answers, interview answers,
or operator policy decisions before downstream planning or implementation, preserve those questions
as `[blocking]`; do not repair them into `[non-blocking]` assumptions.

## Authoring boundary

Write only `idea-brief.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns validation, attempt history,
terminal status, repair references, and downstream next actions. Read those records as evidence.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `idea-brief.md` using its existing sections.
If a finding concerns an AIDD-owned record, report the inconsistency without editing that record.

Read the repair budget in `repair-brief.md`. On `repair-budget-final-attempt` or
`Rerun allowed after this attempt: no`, still repair the content; do not fail solely because no
later rerun is available. AIDD may record `succeeded` only after canonical validation passes;
`repair-budget-exhausted` with unresolved findings remains `failed`. Do not reset budget or
attempt history. Keep evidence and unresolved questions consistent with the repaired content.

## Finding-to-fix mapping

For each finding in `validator-report.md`, apply this sequence:

1. Identify root cause in the source document, not only the symptom text.
2. Patch the smallest possible section that resolves the issue code.
3. Keep unchanged content intact; do not rewrite valid sections.

Use these concrete repair actions:

- `STRUCT-MISSING-REQUIRED-DOCUMENT`: create the missing required Markdown document with contract headings.
- `STRUCT-MISSING-REQUIRED-SECTION` / `STRUCT-EMPTY-REQUIRED-SECTION`: add or complete the exact required heading content.
- `SEM-PLACEHOLDER-CONTENT`: inspect the exact token and line named by the finding, replace
  it with concrete, supportable content, and preserve every unaffected section.
- `SEM-INCOMPLETE-SECTION` for `Constraints` or `Open questions`: convert the section to top-level
  Markdown bullet items, or use exactly `- none` when there are no entries.
- `SEM-UNSUPPORTED-CLAIM`: remove unsupported claim or restate it as an explicit assumption.
- cross-document reference findings: correct the exact conflicting content references and artifact paths.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.

## Repair rules

1. Preserve stable question ids and markers (`[blocking]`, `[non-blocking]`, `[resolved]`).
2. Do not hide unresolved blockers; record them in the content section named by its contract.
3. Preserve truthful content evidence; AIDD records the repair attempt history.
4. Use exact required headings from document contracts; do not rename or qualify headings.

## Repair exit checks

- every finding is resolved or explicitly retained as an active blocker,
- required sections are complete and non-placeholder,
- unresolved `[blocking]` questions still prevent `succeeded`.
