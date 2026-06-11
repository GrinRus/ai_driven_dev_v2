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

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

## Planning discipline

1. `Milestones` must be dependency-ordered execution increments, not unordered wishes.
2. Each milestone heading or bullet must start with a stable id such as `M1`, `M2`, or `M3`.
3. Each milestone must state the expected outcome and an approval/readiness signal.
4. `Dependencies` must make sequencing constraints explicit (`depends on`, `before`, `after`).
5. Major `Risks` must include mitigation intent and a linked verification expectation.
6. `Verification notes` must reference the milestone ids (`M1`, `M2`, ...) that each check covers,
   map checks to risks where relevant, and cover the highest-risk
   milestone explicitly.
7. `Out of scope` and trade-offs must be explicit enough for operator approval review.

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

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- required outputs exist and are Markdown,
- milestone order and dependencies are explicit and executable,
- every milestone has a stable `M<N>` id and verification notes reference those ids,
- risks include mitigation intent with linked verification expectations,
- verification notes map to milestones/risks and cover highest-risk work,
- stage status and validator verdict are consistent with blocker/question state.
