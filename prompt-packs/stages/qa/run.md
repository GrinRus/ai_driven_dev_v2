# Run prompt for `qa`

## Stage objective

Produce a defensible `qa` package that states:

- quality verdict (`ready`, `ready-with-risks`, or `not-ready`),
- residual risk profile with mitigation and ownership notes,
- release recommendation (`proceed`, `proceed-with-conditions`, or `hold`),
- evidence links that justify material claims.

The stage is complete only when verdict, recommendation, and evidence are coherent across
`qa-report.md`, `stage-result.md`, and `validator-report.md`.

## Inputs to read first

- required:
  - `../implement/output/implementation-report.md`
  - `../implement/output/stage-result.md`
  - `../implement/output/validator-report.md`
  - `../review/output/review-report.md`
  - `../review/output/stage-result.md`
  - `../review/output/validator-report.md`
  - `context/verification-output.md`
  - `context/verification-artifacts.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/release-policy.md`
- contract of record:
  - `contracts/stages/qa.md`

## Required outputs (always write)

- `qa-report.md`
- `stage-result.md`
- `validator-report.md`

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed
- `repair-brief.md` only when validation fails and repair is required

## QA discipline

1. Do not declare `succeeded`, `ready`, or `proceed` when upstream `review` is unresolved or
   explicitly `rejected`.
2. Do not pass QA when required verification output/artifacts are missing for material claims.
3. Every material verdict/recommendation claim must point to concrete verification evidence.
4. Residual risks must include severity and explicit mitigation/ownership notes.
5. Blocking uncertainty must become a `[blocking]` question with release recommendation `hold`.

## Execution instructions

1. Read all required upstream artifacts and `contracts/stages/qa.md` before drafting outputs.
2. Verify upstream `review` outcome is not `rejected` and is consistent with implementation status.
3. Build `qa-report.md` with explicit quality verdict, residual risks, and release recommendation.
4. Tie verdict and recommendation claims to `verification-output.md` and/or
   `verification-artifacts.md` references.
5. Use only supported recommendation values (`proceed`, `proceed-with-conditions`, `hold`).
6. If critical checks are missing, contradictory, or inconclusive, ask a `[blocking]` question
   instead of inventing assumptions.
7. Keep `stage-result.md` and `validator-report.md` aligned with the final QA conclusion.

## Completion checklist

- quality verdict is explicit and evidence-backed,
- residual risks include severity plus mitigation/ownership,
- release recommendation is actionable and consistent with verdict,
- material claims reference concrete verification evidence,
- unresolved critical uncertainty is surfaced as blocking question with `hold`,
- `qa-report.md`, `stage-result.md`, and `validator-report.md` are outcome-consistent.
