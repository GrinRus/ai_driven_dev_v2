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
4. Write `tasklist.md` as an ordered implementation decomposition with stable task ids and imperative titles.
5. Keep each task bounded to one dominant output artifact so it stays reviewable as a standalone unit.
6. Record explicit dependencies for every task (`none` when independent) and keep ordering executable in dependency order.
7. Add verification notes for every task that name the primary check, test, or scenario proving completion.
8. Write or update `stage-result.md` and `validator-report.md` so readiness and validation outcomes are consistent.
9. If required inputs are missing or a critical decision is unclear, raise a question instead of inventing an answer.
10. Keep the output useful for the next stage rather than merely well-formatted.

## Completion checklist

- task entries are ordered, uniquely identified, and imperative,
- each task has one dominant output artifact,
- each task has explicit dependencies (`none` or concrete upstream ids),
- dependencies are resolvable and do not imply hidden prerequisites,
- each task has at least one concrete verification note,
- each task stays small enough for single-pass implementation and review,
- `stage-result.md` and `validator-report.md` agree with tasklist readiness.
