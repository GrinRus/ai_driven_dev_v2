# Run prompt for `plan`

## Stage objective

Produce an execution-ready `plan` package that a reviewer can approve without guessing milestone
order, dependency constraints, or verification expectations.

The stage is complete only when sequencing is explicit, risk handling is concrete, and verification
signals are mapped to planned increments.

## Inputs to read first

- required:
  - `../idea/output/idea-brief.md`
  - `../idea/output/stage-result.md`
  - `../research/output/research-notes.md`
  - `../research/output/stage-result.md`
  - `../research/output/validator-report.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/plan.md`

## Required outputs (always write)

- `plan.md`
  - include complete sections:
    - `Goals`
    - `Out of scope`
    - `Milestones`
    - `Implementation strategy`
    - `Risks`
    - `Dependencies`
    - `Verification approach`
    - `Verification notes`
- `stage-result.md`
- `validator-report.md`

## Planning discipline

1. `Milestones` must be dependency-ordered execution increments, not unordered wishes.
2. Each milestone must state the expected outcome and an approval/readiness signal.
3. `Dependencies` must make sequencing constraints explicit (`depends on`, `before`, `after`).
4. Major `Risks` must include mitigation intent and a linked verification expectation.
5. `Verification notes` must map checks to milestones, risks, or both, and cover the highest-risk
   milestone explicitly.
6. `Out of scope` and trade-offs must be explicit enough for operator approval review.

## Execution instructions

1. Read required inputs and `contracts/stages/plan.md` before drafting outputs.
2. If upstream `research` status is unresolved or its validator verdict is `fail`, do not mark the
   `plan` stage as `succeeded`.
3. Draft `plan.md` with concrete, non-placeholder content aligned to the required sections.
4. Prefer the narrowest safe sequencing that preserves dependency constraints and verification
   coverage.
5. If scope boundaries, ordering, or acceptance signals are ambiguous, raise a question instead of
   inventing assumptions.
6. Update `validator-report.md` so findings and verdict match plan completeness and sequencing
   clarity.
7. Update `stage-result.md` so status, blockers, and next actions remain consistent with validator
   and question artifacts.

## Completion checklist

- required outputs exist and are Markdown,
- milestone order and dependencies are explicit and executable,
- risks include mitigation intent with linked verification expectations,
- verification notes map to milestones/risks and cover highest-risk work,
- stage status and validator verdict are consistent with blocker/question state.
