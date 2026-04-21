# Stage Contract: `plan`

## Purpose

Describe the intended solution, boundaries, risks, rollout, and verification approach.

## Primary output

- `plan.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../idea/output/idea-brief.md`
- `../idea/output/stage-result.md`
- `../research/output/research-notes.md`
- `../research/output/stage-result.md`
- `../research/output/validator-report.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/previous-decisions.md`

Optional context documents may improve planning quality, but they must not replace required upstream stage artifacts.

## Upstream dependency rule

- `plan` depends on `research` artifacts from the latest completed `research` attempt.
- `plan` must not declare `succeeded` when `research` stage status is unresolved or its validator verdict is `fail`.

## Plan output expectations

- `plan.md` must include explicit milestones, risk coverage, dependencies, and verification notes.
- milestones should be ordered and map to clear execution increments.
- risk entries should include impact and mitigation intent.
- verification notes should tie checks to milestones or risk-heavy areas.
- `stage-result.md` and `validator-report.md` must stay consistent with the declared plan readiness.

## Validation focus

Validators for `plan` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

required when solution boundaries, trade-offs, or priorities are unclear

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/plan/system.md`
- `prompt-packs/stages/plan/run.md`
- `prompt-packs/stages/plan/repair.md`
- `prompt-packs/stages/plan/interview.md`

## Exit evidence

A `plan` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
