# Stage Contract: `idea`

## Purpose

Turn the incoming request into a clearer problem statement, desired outcome, constraints, and open questions.

## Primary output

Required outputs for every `idea` attempt:

- `idea-brief.md`
- `stage-result.md`
- `validator-report.md`

Conditional outputs:

- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `context/intake.md`
- `context/user-request.md`

## Optional context inputs

- `context/business-context.md`
- `context/constraints.md`
- `context/repository-state.md`
- `context/previous-decisions.md`

Optional context documents may enrich the stage output, but their absence must not block an `idea` run.

## Validation focus

Validators for `idea` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

required when the problem statement, success criteria, or constraints are ambiguous

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Exit states

- `succeeded` — all required outputs exist, validation passes, and no blocking questions remain.
- `repair-needed` — validation failed and the repair budget still allows another attempt.
- `blocked` — one or more blocking questions remain unresolved.
- `failed` — repair budget is exhausted or a non-recoverable stage failure occurred.

## Prompt pack

- `prompt-packs/stages/idea/system.md`
- `prompt-packs/stages/idea/run.md`
- `prompt-packs/stages/idea/repair.md`
- `prompt-packs/stages/idea/interview.md`

## Exit evidence

A `idea` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
