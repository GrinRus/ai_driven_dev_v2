# Repair prompt for `review-spec`

You are rerunning the `review-spec` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving issue traceability,
recommendation actionability, and sign-off consistency.

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
any repair summary in `stage-result.md` and reference `repair-brief.md` by path for traceability.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

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
- cross-document drift: align `stage-result.md` blockers/next actions with validator/report outcome.
  If canonical validation passed but draft `stage-result.md` still says `failed`, `blocked`, or
  `Validator verdict: fail`, remove stale failure wording and make status/verdict match the
  repaired output.

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.
- Re-copy the `stage-result.md` and `validator-report.md` skeleton headings from `stage-brief.md` or the document contracts when a common output is malformed.

## Repair rules

1. Preserve valid findings and recommendations; do not rewrite unaffected sections.
2. Keep issue ids and question ids stable where possible.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-final-attempt` or `Rerun allowed after this attempt: no`, still repair the listed findings and set `stage-result.md` status from the actual repaired output state; do not fail solely because no later rerun is available.
9. If AIDD later records `repair-budget-exhausted` after validation, terminal status must be `failed`.
10. Do not claim success unless required headings, validator verdict, stage-result status, and sign-off decision are mutually consistent.
11. If all listed findings are resolved and no blockers remain, set `stage-result.md` `Status` to `succeeded`; remove stale notes that say canonical AIDD validation still has open findings.
12. Under `## Readiness state`, preserve exactly one top-level bullet containing exactly one allowed
    token: `ready`, `ready-with-conditions`, or `not-ready`.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- issue list accepts either bullet or `### I<N>` subsection issue blocks and every issue/no-defect
  block includes severity, evidence, and rationale; every subsection issue has immediate
  `Severity:`, `Evidence:`, and `Rationale:` bullets; bare no-issue prose is not allowed,
- recommendation summary uses prioritized Markdown list items that are concrete and traceable,
- readiness state, required changes, and sign-off decision are coherent,
- `approved-with-conditions` is paired with `ready-with-conditions`,
- `repair-budget-final-attempt` can coexist with `stage-result.md` status `succeeded` only when all listed findings are resolved,
- `repair-budget-exhausted` cannot coexist with `stage-result.md` status `succeeded`,
- no blocking inconsistency remains between report, validator result, and stage status.
