# Run prompt for `review`

## Stage objective

Produce a defensible `review` package that classifies implementation findings by severity and
disposition, then makes an explicit approval decision (`approved`, `approved-with-conditions`,
or `rejected`).

The stage is complete only when every finding is evidence-backed, severity/disposition labels are
coherent, and approval status matches unresolved `must-fix` items.

## Inputs to read first

- required:
  - `../implement/output/implementation-report.md`
  - `../implement/output/stage-result.md`
  - `../implement/output/validator-report.md`
  - `context/diff-summary.md`
  - `context/acceptance-criteria.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/review-baseline.md`
- contract of record:
  - `contracts/stages/review.md`

## Required outputs (always write)

- `review-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Review discipline

1. Findings must have stable ids, explicit severity, explicit disposition, and rationale tied to
   implementation evidence or acceptance-criteria mismatch.
2. Severity and disposition labels must stay consistent between detailed findings and summary
   sections.
3. `must-fix` findings block `approved` status until resolved.
4. Required changes must map to concrete finding ids when status is conditional or rejected.
5. Missing/contradictory baseline context must become explicit questions, not silent assumptions.

## Execution instructions

1. Read required `implement` artifacts, diff summary, acceptance criteria, and
   `contracts/stages/review.md` before drafting outputs.
2. Do not mark stage `succeeded` when `implement` status is unresolved or validator verdict is
   `fail`.
3. Draft `review-report.md` with sections for findings, approval decision, and required changes.
4. Keep every finding tied to observable evidence from `implementation-report.md` and/or explicit
   acceptance-criteria mismatch.
5. Use allowed dispositions (`must-fix`, `follow-up`, `accepted-risk`, `invalid`) and keep wording
   unambiguous for downstream QA.
6. If contradictions in baseline prevent defensible decision, ask a `[blocking]` question instead
   of forcing approval.
7. Update `validator-report.md` and `stage-result.md` so verdict, blockers, and next actions match
   the final review decision.

## Completion checklist

- findings are uniquely identified with severity and disposition labels,
- each finding is evidence-backed or tied to acceptance-criteria mismatch,
- approval status is explicit and consistent with unresolved `must-fix` findings,
- required changes map to concrete findings for non-approved outcomes,
- blocking ambiguity is surfaced via explicit questions,
- `review-report.md`, `validator-report.md`, and `stage-result.md` are outcome-consistent.
