# Run prompt for `review-spec`

## Goal

Review whether the plan is coherent, safe, and ready to decompose into tasks.

## Inputs to read first

- `../plan/output/plan.md`
- `../plan/output/stage-result.md`
- `../plan/output/validator-report.md`
- `context/review-context.md`
- optional context when available: repository state, constraints, previous decisions
- stage contract: `contracts/stages/review-spec.md`

## Required outputs

- `review-spec-report.md`
- `stage-result.md`
- `validator-report.md`

## Instructions

1. Read all required upstream plan artifacts and review context before writing outputs.
2. Write `review-spec-report.md` with explicit readiness state, issue list, recommendation summary, required changes, and decision.
3. Ensure issues include severity and rationale, and recommendations are prioritized for action.
4. Declare decision sign-off explicitly as `approved`, `approved-with-conditions`, or `rejected`, and keep it consistent with readiness state.
5. Write or update `stage-result.md` and `validator-report.md` so status and readiness state are consistent.
6. If plan artifacts or review context are missing or contradictory, raise a question instead of inventing assumptions.
7. Keep the output useful for downstream task decomposition rather than merely well-formatted.
