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

- required output existence and heading coverage for `plan.md`, `stage-result.md`, and `validator-report.md`,
- plan completeness:
  - required sections are populated with non-placeholder content,
  - milestones, risks, dependencies, and verification notes are present and specific,
- sequencing clarity:
  - milestone order is coherent and executable,
  - dependencies and sequencing constraints are explicit rather than implied,
- user-approval readiness:
  - scope boundaries and trade-offs are explicit enough for operator review,
  - major risks have mitigation intent and verification linkage,
- cross-document consistency between plan claims, validator findings, and declared terminal status in `stage-result.md`.

## Interview policy

`plan` may ask user questions when available artifacts are insufficient to produce a reviewable and approvable execution plan.

Mandatory question triggers:

- unresolved scope boundaries (what is in/out of scope remains ambiguous or contradictory),
- sequencing disputes (competing milestone orders have materially different risk profiles),
- missing acceptance signals (success criteria or approval expectations are undefined for key milestones).

Blocking-question rules:

- mark as `[blocking]` when unresolved ambiguity prevents trustworthy milestone sequencing or approval readiness,
- unresolved `[blocking]` questions must force the stage to exit as `blocked` (never `succeeded`).

Non-blocking-question rules:

- mark as `[non-blocking]` when planning can proceed with explicit bounded assumptions,
- record non-blocking assumptions in `plan.md` under `Out of scope`, `Risks`, or `Verification notes`.

Question/answer document rules:

- write each question to `questions.md` with a stable id and marker (`[blocking]` or `[non-blocking]`),
- treat blocking questions as resolved only when `answers.md` includes matching `[resolved]` entries.

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
