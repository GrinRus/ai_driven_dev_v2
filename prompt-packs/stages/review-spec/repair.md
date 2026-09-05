# Repair prompt for `review-spec`

You are rerunning the `review-spec` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving issue traceability,
recommendation actionability, and sign-off consistency.

## Runtime write authority

Write only `review-spec-report.md` as the substantive repair output. Do not write `stage-result.md` or
`validator-report.md`; AIDD owns their canonical status, validation, history, and publication.
Read existing workflow records as evidence. Use the controlled interview path for questions
and operator answers; do not invent answers.

## Read order (do not skip)

1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/review-spec.md`
4. `contracts/documents/review-spec-report.md`, `contracts/documents/validator-report.md`,
   `contracts/documents/stage-result.md`
5. `contracts/documents/questions.md` and `contracts/documents/answers.md`
6. current outputs:
   - `review-spec-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`review-spec-report.md` must contain the exact top-level heading `## Decision`. Put the
sign-off status under that heading. Do not keep or introduce aliases such as
`## Decision/sign-off`, `## Sign-off`, or `## Recommendation decision`; these aliases do not
satisfy the document contract even if they contain an approval status.

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `review-spec-report.md` and reference `repair-brief.md` by path for traceability.

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

Interview document format is strict. `questions.md` bullets use `- Q1 [blocking|non-blocking] ...`;
`answers.md` bullets must reuse the same question id with `[resolved|partial|deferred]`, for example
`- Q1 [resolved] ...`. Do not put a colon after the marker; `- Q1 [resolved]: ...` is invalid.
Do not use `- Q1: [resolved] ...`; it is invalid. Do not invent `A1`/`A2` answer ids.
If no operator answer is present, write `# Answers\n\n- none\n`; do not create `[resolved]`
answers yourself. Render assumptions or metadata as non-bullet continuation prose.

## Finding-to-fix mapping

For each finding:

1. identify root cause in source sections (issues, recommendations, readiness, required changes,
   decision/sign-off);
2. patch the smallest section that resolves the issue code;
3. re-check issue-to-recommendation linkage and recommendation priority order;
4. re-check stage status and blockers against validator verdict and unresolved `[blocking]`
   questions.

Use concrete repair actions:

- `SEM-PLACEHOLDER-CONTENT`: inspect the exact token and line named by the finding, replace
  it with concrete stage-relevant content, and preserve every unaffected section. Do not
  regenerate the whole report from the skeleton.
- `SEM-INCOMPLETE-SECTION` in an AIDD-generated record: expose the actual blockers or their
  absence in substantive runtime content; AIDD reconciles its own record. Never erase a
  concrete blocker or an unresolved blocking question.
- weak issue quality: rewrite issues with explicit scope, severity, evidence, and rationale linked to plan
  risks/gaps; `Issue list` may use top-level bullets or `### I<N> - ...` subsections, but each
  issue item/subsection must include explicit `Severity`, `Evidence`, and `Rationale` text; if no material issue
  exists, use a `Severity: none` no-defect item with explicit evidence and rationale instead of inventing
  artificial advisory issues; do not use bare prose such as `No material issues identified.`;
  for every `### I<N>` subsection, put `- Severity: ...`, `- Evidence: ...`, and
  `- Rationale: because ...` as immediate metadata bullets under that heading before any
  description or recommendation text;
- missing evidence reference: add an `Evidence:` field that names a concrete upstream artifact,
  research/source id, target file path, milestone id, acceptance id, or command/check result;
- unsupported high-severity claim: either cite direct durable evidence or downgrade the item to a
  bounded low/info observation; do not expand implementation scope from speculation;
- contradiction with upstream research or plan: add `Reconciliation:` with the stronger evidence,
  or replace the contradiction with a question or non-blocking observation;
- weak recommendation actionability: rewrite recommendation summary with prioritized, concrete
  Markdown list items tied to issues;
- sign-off inconsistency: align readiness state, decision, and required changes so go/no-go status
  is unambiguous;
  use the exact allowed readiness/sign-off mapping: `ready` -> `approved`,
  `ready-with-conditions` -> `approved-with-conditions`, and `not-ready` -> `rejected`.
  If the decision is `approved-with-conditions`, the readiness state must be
  `ready-with-conditions`; do not replace it with prose such as `conditionally ready`;
- contradiction in plan, operator request, repository state, or optional context: keep/add a
  blocking question instead of forcing approval;
- cross-document drift: repair conflicting readiness, decision, and blocker claims in
  `review-spec-report.md`. AIDD reconciles workflow status after validation; a previous failed
  workflow record must not force stale failure wording into the repaired substantive output.
- downstream-order drift: keep report recommendations flow-aware: `tasklist` is the immediate
  canonical downstream stage, before implementation, review, or QA. AIDD writes workflow next actions.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy only the `review-spec-report.md` skeleton headings from `stage-brief.md` or its document contract
  when substantive output is malformed. AIDD repairs generated workflow records.

## Repair rules

1. Preserve valid findings and recommendations; do not rewrite unaffected sections.
2. Keep issue ids and question ids stable where possible.
3. Do not claim unresolved findings are fixed; AIDD determines `succeeded` after validation.
4. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
5. Keep `review-spec-report.md` evidence truthful for this repair attempt; AIDD owns attempt history and terminal status.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before reporting the repair outcome.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed substantive findings; AIDD derives terminal status from post-runtime validation; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, AIDD sets terminal status to `failed`.
10. Do not claim the repair is complete unless required headings and sign-off decision are mutually consistent.
11. If all listed findings are resolved and no blockers remain, record the repaired evidence in `review-spec-report.md`; AIDD determines `succeeded` after validation. Do not treat the previous failed validator report as a new result.
12. Under `## Readiness state`, preserve exactly one top-level bullet containing exactly one allowed
    token: `ready`, `ready-with-conditions`, or `not-ready`.
13. AIDD writes the first successful downstream action to name `tasklist`,
    not a later canonical stage.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- issue list accepts either bullet or `### I<N>` subsection issue blocks and every issue/no-defect
  block includes severity, evidence, and rationale; every subsection issue has immediate
  `Severity:`, `Evidence:`, and `Rationale:` bullets; bare no-issue prose is not allowed,
- recommendation summary uses prioritized Markdown list items that are concrete and traceable,
- readiness state, required changes, and sign-off decision are coherent,
- `approved-with-conditions` is paired with `ready-with-conditions`,
- successful `stage-result.md` next actions name `tasklist` as the immediate downstream stage,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no blocking inconsistency remains between report, validator result, and stage status.
