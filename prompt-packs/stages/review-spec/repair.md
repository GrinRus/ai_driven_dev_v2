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
5. current outputs:
   - `review-spec-report.md`
   - `stage-result.md`
   - `questions.md` / `answers.md` when present

`repair-brief.md` is AIDD-owned read-only repair control evidence. Do not rewrite it; put
any repair summary in `stage-result.md`.

## Finding-to-fix mapping

For each finding:

1. identify root cause in source sections (issues, recommendations, readiness, required changes,
   decision/sign-off);
2. patch the smallest section that resolves the issue code;
3. re-check issue-to-recommendation linkage and recommendation priority order;
4. re-check stage status and blockers against validator verdict and unresolved `[blocking]`
   questions.

Use concrete repair actions:

- weak issue quality: rewrite issues with explicit scope, severity, and rationale linked to plan
  risks/gaps;
- weak recommendation actionability: rewrite recommendation summary with prioritized, concrete
  remediation steps tied to issues;
- sign-off inconsistency: align readiness state, decision, and required changes so go/no-go status
  is unambiguous;
- contradiction in review context: keep/add a blocking question instead of forcing approval;
- cross-document drift: align `stage-result.md` blockers/next actions with validator/report outcome.

## Repair rules

1. Preserve valid findings and recommendations; do not rewrite unaffected sections.
2. Keep issue ids and question ids stable where possible.
3. Do not mark `succeeded` while validator verdict is `fail`.
4. Keep unresolved `[blocking]` questions explicit under blockers and next actions.
5. Keep `stage-result.md` attempt history and terminal status truthful for this repair attempt.
6. Use exact required headings from document contracts; do not rename or qualify headings.
7. Read the repair budget section in `repair-brief.md` before declaring terminal status.
8. If `repair-brief.md` says `repair-budget-exhausted` or `Rerun allowed after this attempt: no`, `stage-result.md` status must be `failed`; do not claim `succeeded`.
9. Do not claim success unless required headings, validator verdict, stage-result status, and sign-off decision are mutually consistent.

## Repair exit checks

- every blocking finding is resolved or explicitly retained as active blocker,
- issue list and recommendation summary are concrete, prioritized, and traceable,
- readiness state, required changes, and sign-off decision are coherent,
- repair-budget exhaustion cannot coexist with `stage-result.md` status `succeeded`,
- no blocking inconsistency remains between report, validator result, and stage status.
