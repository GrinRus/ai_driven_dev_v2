# Stage Contract: `qa`

## Purpose

Summarize verification outcomes, remaining risks, and readiness status.

## Primary output

- `qa-report.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../review/output/review-report.md`
- `context/verification-output.md`

## Validation focus

Validators for `qa` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

optional when release or acceptance policy is unclear

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/qa/system.md`
- `prompt-packs/stages/qa/run.md`
- `prompt-packs/stages/qa/repair.md`
- `prompt-packs/stages/qa/interview.md`

## Exit evidence

A `qa` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
