# Stage Contract: `review`

## Purpose

Review the implementation result, identify risks, and confirm whether the change is ready for QA or merge.

## Primary output

- `review-report.md`
- `stage-result.md`
- `validator-report.md`
- `repair-brief.md` when validation fails
- `questions.md` / `answers.md` when clarification is required

## Required inputs

- `../implement/output/implementation-report.md`
- `context/diff-summary.md`

## Validation focus

Validators for `review` should check:

- required document existence,
- required headings and sections,
- consistency with upstream inputs,
- whether the main output actually serves the stage purpose,
- whether the stage result reflects validator and repair outcomes.

## Interview policy

optional when review trade-offs require operator judgment

## Repair policy

- default repair budget: 2 attempts after the initial run
- repair uses the same target documents
- every failed attempt must preserve validator findings and a repair brief

## Prompt pack

- `prompt-packs/stages/review/system.md`
- `prompt-packs/stages/review/run.md`
- `prompt-packs/stages/review/repair.md`
- `prompt-packs/stages/review/interview.md`

## Exit evidence

A `review` run is considered ready to progress when:

- the required output documents exist,
- validators pass,
- any required user questions have answers,
- `stage-result.md` names the next action clearly.
