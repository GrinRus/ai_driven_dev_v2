# Run prompt for `qa`

## Goal

Summarize verification outcomes, remaining risks, and readiness status.

## Inputs to read first

- `../implement/output/implementation-report.md`
- `../implement/output/stage-result.md`
- `../implement/output/validator-report.md`
- `../review/output/review-report.md`
- `../review/output/stage-result.md`
- `../review/output/validator-report.md`
- `context/verification-output.md`
- `context/verification-artifacts.md`
- optional context when available: repository state, constraints, release policy
- stage contract: `contracts/stages/qa.md`

## Required outputs

- `qa-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Instructions

1. Read all required upstream artifacts before writing outputs.
2. Confirm review status is resolved and review decision is not `rejected`.
3. Use verification outputs and verification artifacts as mandatory evidence baseline for QA conclusions.
4. Write `qa-report.md` with explicit quality verdict, residual risk summary, and release recommendation.
5. Tie verdict and recommendation claims to concrete verification evidence references.
6. Keep release recommendation actionable (`proceed`, `proceed-with-conditions`, or `hold`).
7. Do not issue `ready` or `proceed` conclusions when unresolved must-fix findings or missing critical checks remain.
8. Write or update `stage-result.md` and `validator-report.md` so QA outcome is consistent.
9. If required inputs are missing or evidence baseline is contradictory, raise a question instead of inventing assumptions.
10. Keep the output useful for the next stage rather than merely well-formatted.

## Completion checklist

- quality verdict is explicit and evidence-backed,
- residual risks include severity plus mitigation/ownership notes,
- release recommendation is actionable and coherent with verdict,
- evidence references are present for material claims,
- verdict does not conflict with unresolved must-fix findings or missing critical evidence,
- stage result and validator report agree with QA outcome.
