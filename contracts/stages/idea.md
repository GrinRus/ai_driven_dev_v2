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

- required output existence for `idea-brief.md`, `stage-result.md`, and `validator-report.md`,
- required heading coverage in `idea-brief.md` (`Problem statement`, `Desired outcome`, `Constraints`, `Open questions`),
- minimum completeness of `idea-brief.md`:
  - `Problem statement` states the core user or business problem and affected scope;
  - `Desired outcome` states a concrete target result or acceptance signal;
  - `Constraints` lists actionable boundaries or explicitly records `- none`;
  - `Open questions` lists unresolved decisions or explicitly records `- none`,
- no unresolved placeholder content in required sections (for example `TBD`, `TODO`, `N/A`, `...`, or equivalent filler),
- consistency between `idea-brief.md` and required inputs (`context/intake.md`, `context/user-request.md`) for goals and constraints,
- `validator-report.md` issue codes and severities follow the shared `validator-report.md` contract vocabulary,
- `stage-result.md` status and validation summary agree with `validator-report.md` and any repair outcomes (for example, no `succeeded` when validator verdict is `fail`).

## Interview policy

`idea` may ask user questions only when required inputs are insufficient to produce a reliable `idea-brief.md`.

Mandatory question triggers:

- the core user or business problem is missing or ambiguous,
- success criteria are missing, contradictory, or non-testable,
- constraints are missing or contradictory where they can change scope, feasibility, or priority,
- a high-impact assumption (for example compliance, security, budget, or deadline) cannot be grounded in the provided inputs.

Blocking-question rules:

- mark a question as `[blocking]` when the answer is required to produce truthful `Problem statement`, `Desired outcome`, or `Constraints` content,
- mark a question as `[blocking]` when unresolved uncertainty can invalidate progression safety for downstream stages,
- unresolved `[blocking]` questions must force the stage to exit as `blocked` (never `succeeded`).

Non-blocking-question rules:

- mark a question as `[non-blocking]` when the stage can proceed with an explicit, low-risk assumption,
- when using `[non-blocking]`, record the assumption in `idea-brief.md` so downstream stages can revisit it.

Question/answer document rules:

- write every question to `questions.md` with a stable question id and marker (`[blocking]` or `[non-blocking]`),
- treat a blocking question as resolved only when `answers.md` provides a matching `[resolved]` answer for the same question id.

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
