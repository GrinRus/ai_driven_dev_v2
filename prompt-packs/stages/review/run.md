# Run prompt for `review`

## Goal

Review the implementation result, identify risks, and confirm whether the change is ready for QA or merge.

## Inputs to read first

- `../implement/output/implementation-report.md`
- `../implement/output/stage-result.md`
- `../implement/output/validator-report.md`
- `context/diff-summary.md`
- `context/acceptance-criteria.md`
- optional context when available: repository state, constraints, review baseline
- stage contract: `contracts/stages/review.md`

## Required outputs

- `review-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Instructions

1. Read all required upstream artifacts before writing outputs.
2. Confirm `implement` stage result is resolved and validator verdict is not `fail`.
3. Use `context/diff-summary.md` and `context/acceptance-criteria.md` as mandatory review baseline inputs.
4. Write `review-report.md` with stable finding ids, explicit severity, disposition, and evidence-backed rationale.
5. Declare explicit approval status as `approved`, `approved-with-conditions`, or `rejected`.
6. When status is not `approved`, include required changes tied to specific findings.
7. Do not include findings that cannot be tied to observable evidence or explicit acceptance-criteria mismatches.
8. Write or update `stage-result.md` and `validator-report.md` so review status and findings are consistent.
9. If required inputs are missing or review baseline is contradictory, raise a question instead of inventing assumptions.
10. Keep the output useful for the next stage rather than merely well-formatted.

## Completion checklist

- findings are uniquely identified and severity-labeled,
- each finding has explicit disposition and rationale,
- each finding is supported by implementation evidence or acceptance-criteria mismatch,
- approval status is explicit and consistent with findings,
- unresolved `must-fix` findings prevent `approved` status,
- required changes are listed when approval is conditional or rejected,
- stage result and validator report agree with review outcome.
