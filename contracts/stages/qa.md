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

- `../implement/output/implementation-report.md`
- `../implement/output/stage-result.md`
- `../implement/output/validator-report.md`
- `../review/output/review-report.md`
- `../review/output/stage-result.md`
- `../review/output/validator-report.md`
- `context/verification-output.md`
- `context/verification-artifacts.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/release-policy.md`

Optional context documents may improve QA depth, but they must not replace implementation artifacts, review findings, and verification evidence.

## Upstream dependency rule

- `qa` depends on artifacts from the latest completed `review` attempt.
- `qa` must not declare `succeeded` when review status is unresolved or review decision is `rejected`.
- `qa` must not declare `succeeded` when verification output or verification artifacts are missing.

## QA output expectations

- `qa-report.md` must include:
  - an explicit quality verdict (`ready`, `ready-with-risks`, `not-ready`),
  - residual risk summary with severity and mitigation/ownership notes,
  - release recommendation aligned to verdict and risk profile,
  - evidence references linking verdict claims to verification artifacts.
- release recommendation must be actionable (for example: `proceed`, `proceed-with-conditions`, `hold`).
- `stage-result.md` and `validator-report.md` must remain consistent with verdict and release recommendation.

## Validation focus

Validators for `qa` should check:

- required output existence and heading coverage for `qa-report.md`, `stage-result.md`, and `validator-report.md`,
- consistency with upstream review decision and verification evidence artifacts,
- unsupported verdicts:
  - quality verdict and release recommendation must follow from cited evidence and risk profile,
  - verdicts that contradict material unresolved findings or missing checks are rejected,
- missing evidence references:
  - material QA claims must reference concrete verification artifacts or execution outputs,
  - evidence-free pass/ready claims are rejected,
- cross-document consistency between QA verdict, residual risk summary, validator findings, and terminal status in `stage-result.md`.

## Interview policy

`qa` may ask user questions when it cannot produce a defensible quality verdict from available execution evidence.

Mandatory question triggers:

- blocked verification where required checks could not run to completion or produced inconclusive outputs,
- missing execution artifacts needed to support material verdict or release recommendation claims,
- contradictory critical-check evidence across verification outputs and review findings.

Blocking-question rules:

- mark as `[blocking]` when unresolved ambiguity prevents a reliable `ready`/`not-ready` verdict or actionable release recommendation,
- unresolved `[blocking]` questions must force stage status `blocked` (never `succeeded`) and release recommendation `hold`.

Non-blocking-question rules:

- mark as `[non-blocking]` when QA can proceed with bounded assumptions and explicit mitigations,
- record each non-blocking assumption in `qa-report.md` so downstream release decisions can revisit it.

Question/answer document rules:

- write each question to `questions.md` with a stable id and marker (`[blocking]` or `[non-blocking]`),
- treat blocking questions as resolved only when `answers.md` includes matching `[resolved]` entries.

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
