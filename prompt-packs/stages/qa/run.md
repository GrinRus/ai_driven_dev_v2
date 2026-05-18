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

Treat `validator-report.md` as draft evidence: AIDD writes the canonical validator report after
post-runtime validation. Treat `stage-result.md` as a truthful summary draft that AIDD may
normalize if canonical validation proves the terminal status inconsistent.

## Conditional outputs

- `questions.md` and `answers.md` when clarification is needed

## System-owned control artifacts

- Do not create or edit `repair-brief.md`; AIDD generates it after validation fails and provides it
  read-only to repair attempts.

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
3. Build `qa-report.md` with these exact H2 sections:
   `Verification summary`, `Release recommendation`, `Evidence`, `Known issues`, and `Readiness`.
4. In `Release recommendation`, put exactly one supported state on its own bullet:
   `proceed`, `proceed-with-conditions`, or `hold`.
5. In `Evidence`, label material evidence entries as `EV-1`, `EV-2`, ... and include command
   outcomes or artifact paths in backticks.
6. Tie verdict and recommendation claims to `verification-output.md` and/or
   `verification-artifacts.md` references.
7. In `Known issues`, use `- Known issues: none.` only as an empty known-defect marker.
   Put residual risks in separate bullets such as
   `- Residual risk RR-1: Severity: low. ... Mitigation/ownership: ...`.
8. Use only supported recommendation values (`proceed`, `proceed-with-conditions`, `hold`).
9. If critical checks are missing, contradictory, or inconclusive, ask a `[blocking]` question
   instead of inventing assumptions.
10. Keep `stage-result.md` and `validator-report.md` aligned with the final QA conclusion.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- quality verdict is explicit and evidence-backed,
- residual risks include severity plus mitigation/ownership,
- release recommendation is actionable and consistent with verdict,
- material claims reference concrete verification evidence,
- unresolved critical uncertainty is surfaced as blocking question with `hold`,
- `qa-report.md`, `stage-result.md`, and `validator-report.md` are outcome-consistent.
