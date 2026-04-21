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
4. Write or update required output documents in Markdown.
5. If required inputs are missing or review baseline is contradictory, raise a question instead of inventing assumptions.
6. Keep the output useful for the next stage rather than merely well-formatted.
