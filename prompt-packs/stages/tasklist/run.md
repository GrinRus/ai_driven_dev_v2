# Run prompt for `tasklist`

## Goal

Break the approved plan into reviewable implementation tasks with verification notes.

## Inputs to read first

- `../plan/output/plan.md`
- `../plan/output/stage-result.md`
- `../review-spec/output/review-spec-report.md`
- `../review-spec/output/stage-result.md`
- `../review-spec/output/validator-report.md`
- optional context when available: repository state, constraints, previous decisions
- stage contract: `contracts/stages/tasklist.md`

## Required outputs

- `tasklist.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## Instructions

1. Read all required upstream artifacts before writing outputs.
2. Treat the latest completed `review-spec` attempt as the gating upstream source.
3. Do not declare success when review-spec readiness or sign-off indicates unresolved blocking conditions.
4. Write or update the required output documents in Markdown.
5. If required inputs are missing or a critical decision is unclear, raise a question instead of inventing an answer.
6. Keep the output useful for the next stage rather than merely well-formatted.
