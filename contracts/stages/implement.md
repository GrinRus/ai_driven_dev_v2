# Stage Contract: `implement`

## Purpose

Apply the selected task to the repository, explain the change, and record verification evidence.

## Primary output

- `implementation-report.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../tasklist/output/tasklist.md`
- `context/repository-state.md`

## Validation focus

Validators for `implement` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

optional when a destructive or policy-sensitive choice must be confirmed

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/implement/system.md`
- `prompt-packs/stages/implement/run.md`
- `prompt-packs/stages/implement/repair.md`
- `prompt-packs/stages/implement/interview.md`

## Exit evidence

A `implement` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
