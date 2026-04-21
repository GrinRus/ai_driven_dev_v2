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
- `../review-spec/output/review-spec-report.md`

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
