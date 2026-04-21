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
- `../tasklist/output/stage-result.md`
- `../tasklist/output/validator-report.md`
- `context/repository-state.md`
- `context/task-selection.md`
- `context/allowed-write-scope.md`

## Optional context inputs

- `context/constraints.md`
- `context/previous-decisions.md`
- `context/runtime-capabilities.md`

Optional context documents may improve implementation quality, but they must not replace task selection, repository state, and write-scope controls.

## Upstream dependency rule

- `implement` depends on artifacts from the latest completed `tasklist` attempt.
- `implement` must not declare `succeeded` when selected task id is missing from `tasklist.md`.
- `implement` must not declare `succeeded` when edits exceed `context/allowed-write-scope.md` or the scope definition is missing.

## Implementation output expectations

- `implementation-report.md` must include:
  - an explicit change summary mapped to the selected task id,
  - a touched-files list with file path and short change intent per entry,
  - verification notes naming the primary checks executed and their outcomes,
  - follow-up notes for known residual risks or deferred non-blocking items.
- touched-files entries must stay within `context/allowed-write-scope.md`.
- `stage-result.md` and `validator-report.md` must remain consistent with declared verification outcomes.

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
