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
  - `context/acceptance-criteria.md`
  - `context/verification-output.md`
  - `context/verification-artifacts.md`
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

## Interview document syntax

- `questions.md` bullets must be exactly `- Q1 [blocking] text` or
  `- Q1 [non-blocking] text`.
- `answers.md` bullets must be exactly `- Q1 [resolved] text`,
  `- Q1 [partial] text`, or `- Q1 [deferred] text`.
- Do not put punctuation immediately after the marker: `- Q1 [resolved]: text` and
  `- Q1: [resolved] text` are invalid.
- Do not invent `A1`/`A2` answer ids; answer bullets always reuse question ids.
- Planning may ask downstream clarification questions, but it must not invent
  `[resolved]` answers for missing operator decisions. If no operator answer is present,
  write `# Answers\n\n- none\n`.

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
8. When `context/verification-output.md` names authored verification commands, copy those commands
   exactly and preserve those commands exactly when citing them in the plan. Preserve flags, path
   lists, environment variables, and coverage/cache-disabling options such as
   `--coverage.enabled=false`; do not rewrite them as `npx`, package-manager aliases, or broader
   suite commands.
9. Optional broad checks outside the authored verification boundary may be documented only as
   optional/non-blocking exploratory checks. Do not turn them into required pass criteria or a
   milestone exit condition unless the authored task or review-spec explicitly requires them.

## Execution instructions

1. Read required inputs and `contracts/stages/plan.md` before drafting outputs.
2. If upstream `research` status is unresolved or its validator verdict is `fail`, do not mark the
   `plan` stage as `succeeded`.
3. Draft `plan.md` with concrete, non-placeholder content aligned to the required sections.
4. Prefer the narrowest safe sequencing that preserves dependency constraints and verification
   coverage.
5. If scope boundaries, ordering, or acceptance signals are ambiguous, raise a question instead of
   inventing assumptions.
6. Use `context/verification-output.md` as the verification boundary when present; if you need to
   mention an authored command, quote it exactly rather than paraphrasing executable details.
7. Update `validator-report.md` so findings and verdict match plan completeness and sequencing
   clarity.
8. Update `stage-result.md` so status, blockers, and next actions remain consistent with validator
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
- authored verification commands from `context/verification-output.md` are preserved exactly, or
  referenced generically without changing command flags or broadening scope,
- optional broader checks are not promoted to required pass criteria outside the authored boundary,
- stage status and validator verdict are consistent with blocker/question state.
