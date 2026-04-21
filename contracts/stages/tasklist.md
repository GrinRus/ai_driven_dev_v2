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
- `../plan/output/stage-result.md`
- `../review-spec/output/review-spec-report.md`
- `../review-spec/output/stage-result.md`
- `../review-spec/output/validator-report.md`

## Optional context inputs

- `context/repository-state.md`
- `context/constraints.md`
- `context/previous-decisions.md`

Optional context documents may improve task decomposition quality, but they must not replace required plan and review-spec artifacts.

## Upstream dependency rule

- `tasklist` depends on artifacts from the latest completed `review-spec` attempt.
- `tasklist` must not declare `succeeded` when review-spec readiness/sign-off outcome indicates unresolved blocking conditions.

## Tasklist output expectations

- `tasklist.md` must include:
  - an ordered decomposition of implementation tasks with stable task ids and imperative titles,
  - one dominant output artifact per task so each item remains reviewable as a standalone unit,
  - explicit dependency notes per task (upstream task ids or `none`),
  - verification notes per task naming the primary check, test, or scenario proving completion.
- task ordering should be executable in dependency order rather than by prose grouping alone.
- `stage-result.md` and `validator-report.md` must stay consistent with the declared tasklist readiness.

## Validation focus

Validators for `tasklist` should check:

- required output existence and heading coverage for `tasklist.md`, `stage-result.md`, and `validator-report.md`,
- consistency with approved upstream `plan` and `review-spec` outcomes,
- task independence:
  - each task has one dominant deliverable rather than bundled unrelated outcomes,
  - dependency notes avoid hidden coupling and do not rely on unspecified prerequisites,
- ordering clarity:
  - task order is executable in dependency order and avoids contradictory sequencing,
  - dependency references are explicit and resolvable to listed task ids or upstream stage artifacts,
- reviewability:
  - each task has a bounded completion surface and at least one concrete verification note,
  - task scope remains small enough for single-pass implementation and review,
- cross-document consistency between tasklist readiness claims, validator findings, and terminal status in `stage-result.md`.

## Interview policy

`tasklist` may ask user questions when it cannot produce a safe and executable decomposition from available planning artifacts.

Mandatory question triggers:

- unresolved sequencing constraints where multiple valid orders materially change risk or delivery outcome,
- unresolved staffing or ownership assumptions that affect task decomposition or parallelization,
- conflicting prioritization directives that block a coherent dependency order.

Blocking-question rules:

- mark as `[blocking]` when unresolved ambiguity prevents deterministic critical-path ordering or task ownership assumptions,
- unresolved `[blocking]` questions must force stage status `blocked` (never `succeeded`).

Non-blocking-question rules:

- mark as `[non-blocking]` when decomposition can proceed with explicit bounded assumptions,
- record non-blocking assumptions in `tasklist.md` so downstream stages can validate or revise them.

Question/answer document rules:

- write each question to `questions.md` with a stable id and marker (`[blocking]` or `[non-blocking]`),
- treat blocking questions as resolved only when `answers.md` includes matching `[resolved]` entries.

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
