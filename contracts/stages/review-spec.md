# Stage Contract: `review-spec`

## Purpose

Review whether the plan is coherent, safe, and ready to decompose into tasks.

## Primary output

- `review-spec-report.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../plan/output/plan.md`
- `../plan/output/stage-result.md`
- `../plan/output/validator-report.md`
- `context/review-context.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/previous-decisions.md`

Optional context documents may refine review quality, but they must not replace required plan and review-context artifacts.

## Upstream dependency rule

- `review-spec` depends on artifacts from the latest completed `plan` attempt.
- `review-spec` must not declare `succeeded` if required plan artifacts are missing or inconsistent.

## Validation focus

Validators for `review-spec` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

required when plan approval depends on unresolved product decisions

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/review-spec/system.md`
- `prompt-packs/stages/review-spec/run.md`
- `prompt-packs/stages/review-spec/repair.md`
- `prompt-packs/stages/review-spec/interview.md`

## Exit evidence

A `review-spec` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
