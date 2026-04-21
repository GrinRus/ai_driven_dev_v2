# Stage Contract: `tasklist`

## Purpose

Break the approved plan into reviewable implementation tasks with verification notes.

## Primary output

- `tasklist.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../plan/output/plan.md`
- `../plan/output/stage-result.md`
- `../review-spec/output/review-spec-report.md`
- `../review-spec/output/stage-result.md`
- `../review-spec/output/validator-report.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/previous-decisions.md`

Optional context documents may improve task decomposition quality, but they must not replace required plan and review-spec artifacts.

## Upstream dependency rule

- `tasklist` depends on artifacts from the latest completed `review-spec` attempt.
- `tasklist` must not declare `succeeded` when review-spec readiness/sign-off outcome indicates unresolved blocking conditions.

## Validation focus

Validators for `tasklist` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

optional when task prioritization or scope boundaries remain unclear

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/tasklist/system.md`
- `prompt-packs/stages/tasklist/run.md`
- `prompt-packs/stages/tasklist/repair.md`
- `prompt-packs/stages/tasklist/interview.md`

## Exit evidence

A `tasklist` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
