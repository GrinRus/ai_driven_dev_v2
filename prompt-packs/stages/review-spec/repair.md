# Repair prompt for `review-spec`

You are rerunning the `review-spec` stage because validation failed.

Your job is to resolve validator findings with minimal edits while preserving issue traceability,
recommendation actionability, and sign-off consistency.

## Read order (do not skip)

Read `stage-brief.md`, the current `review-spec-report.md`, and its
`contracts/documents/review-spec-report.md` contract before applying the findings.
1. `validator-report.md` (latest findings and severities)
2. `repair-brief.md` (repair scope and constraints)
3. `contracts/stages/review-spec.md`
4. `contracts/documents/questions.md` and `contracts/documents/answers.md`

`review-spec-report.md` must contain the exact top-level heading `## Decision`. Put the
sign-off status under that heading. Do not keep or introduce aliases such as
`## Decision/sign-off`, `## Sign-off`, or `## Recommendation decision`; these aliases do not
satisfy the document contract even if they contain an approval status.

Do not inspect AIDD validator implementation files, installed package files, or bundled examples
during repair. Use `validator-report.md`, `repair-brief.md`, and the named contracts as the repair
scope. After updating the required documents and checking consistency, stop.

## Interview context

Read `contracts/documents/questions.md` and `contracts/documents/answers.md` when available.
Use stable QIDs and canonical `- Q1 [blocking] ...` or `- Q1 [non-blocking] ...` question
candidates through the controlled interview path. AIDD merges raw candidates and may normalize
safe presentation differences without changing meaning. Preserve unresolved blocking questions.
Operator answers use the same QID, for example `- Q1 [resolved] ...`; do not create or edit
`answers.md`, invent `A1`/`A2` answer ids, or create `[resolved]` answers yourself. Missing
answers remain an operator checkpoint. Render assumptions as non-bullet continuation prose.

## Authoring boundary

Write only `review-spec-report.md` and other runtime-content targets explicitly listed in `stage-brief.md`.
Do not write `stage-result.md` or `validator-report.md`; AIDD owns validation, attempt history,
terminal status, repair references, and downstream next actions. Read those records as evidence.
`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it.
Keep any repair summary and remaining content blockers in `review-spec-report.md` using its existing sections.
If a finding concerns an AIDD-owned record, report the inconsistency without editing that record.

Read the repair budget in `repair-brief.md`. On `repair-budget-final-attempt` or
`Rerun allowed after this attempt: no`, still repair the content; do not fail solely because no
later rerun is available. AIDD may record `succeeded` only after canonical validation passes;
`repair-budget-exhausted` with unresolved findings remains `failed`. Do not reset budget or
attempt history. Keep evidence and unresolved questions consistent with the repaired content.

## Finding-to-fix mapping

For each finding:

1. identify root cause in source sections (issues, recommendations, readiness, required changes,
   decision/sign-off);
2. patch the smallest section that resolves the issue code;
3. re-check issue-to-recommendation linkage and recommendation priority order;

Use concrete repair actions:

- `SEM-PLACEHOLDER-CONTENT`: inspect the exact token and line named by the finding, replace
  it with concrete stage-relevant content, and preserve every unaffected section. Do not
  regenerate the whole report from the skeleton.
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

## Targeted repair discipline

- Fix only the sections named by validator findings unless cross-document consistency requires a narrow companion edit.
- Preserve valid sections and stable ids; do not rewrite complete documents just to satisfy one failed heading.

## Repair rules

1. Preserve valid findings and recommendations; do not rewrite unaffected sections.
2. Keep issue ids and question ids stable where possible.
3. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
4. Use exact required headings from document contracts; do not rename or qualify headings.
5. Under `## Readiness state`, preserve exactly one top-level bullet containing exactly one allowed
    token: `ready`, `ready-with-conditions`, or `not-ready`.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- issue list accepts either bullet or `### I<N>` subsection issue blocks and every issue/no-defect
  block includes severity, evidence, and rationale; every subsection issue has immediate
  `Severity:`, `Evidence:`, and `Rationale:` bullets; bare no-issue prose is not allowed,
- recommendation summary uses prioritized Markdown list items that are concrete and traceable,
- readiness state, required changes, and sign-off decision are coherent,
- `approved-with-conditions` is paired with `ready-with-conditions`,

AIDD owns downstream-order drift correction: the immediate next stage after `review-spec` is
`tasklist`. Preserve content needed for that handoff; do not bypass the planning or
implementation gates by naming a later stage.
