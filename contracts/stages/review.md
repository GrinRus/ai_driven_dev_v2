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
- `../implement/output/stage-result.md`
- `../implement/output/validator-report.md`
- `context/diff-summary.md`
- `context/acceptance-criteria.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/review-baseline.md`

Optional context documents may improve review depth, but they must not replace implementation artifacts, diff context, and acceptance criteria.

## Upstream dependency rule

- `review` depends on artifacts from the latest completed `implement` attempt.
- `review` must not declare `succeeded` when `implement` validator verdict is `fail` or stage status is unresolved.
- `review` must not declare `succeeded` when diff context or acceptance criteria are missing.

## Review output expectations

- `review-report.md` must include:
  - findings with stable ids, explicit severity, and disposition per finding,
  - rationale tied to implementation evidence and acceptance criteria,
  - an explicit approval status suitable for go/no-go decision (`approved`, `approved-with-conditions`, `rejected`),
  - summary of required changes when approval status is not `approved`.
- severity labels must remain explicit and consistent across findings and summary sections.
- `stage-result.md` and `validator-report.md` must remain consistent with findings and approval status.

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
