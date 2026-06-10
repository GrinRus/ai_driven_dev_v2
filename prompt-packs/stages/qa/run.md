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
- optional context when available:
  - `context/selected-task.md`
  - `context/diff-summary.md`
  - `context/verification-output.md`
  - `context/verification-artifacts.md`
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
2. Do not pass QA when verification output/artifacts are missing for material claims.
3. Every material verdict/recommendation claim must point to concrete verification evidence.
4. Residual risks must include severity and explicit mitigation/ownership notes.
5. Blocking uncertainty must become a `[blocking]` question with release recommendation `hold`.
6. When present, the selected task and `context/verification-output.md` define the authored
   verification boundary. Do not downgrade to `ready-with-risks` or `proceed-with-conditions` only because
   optional broader checks outside that boundary were not run or were blocked by local sandbox
   policy, unless they reveal a concrete defect or contradict acceptance criteria/review evidence.
7. Intentional design constraints selected by the authored task or resolved interview answers are
   not residual release risks by themselves. For example, trusted local code execution is `ready`
   when explicit confirmation, documentation, tests, and scope boundaries required by the selected
   task are complete. Downgrade only for missing mitigation/evidence, broadened scope, contradictory
   review/verification artifacts, or a concrete defect beyond the selected boundary.
8. When `context/diff-summary.md`, `context/repository-state.md`, or upstream implementation/review
   evidence shows lockfile, dependency manifest, generated resolver output, or project config
   changes outside the selected task scope, set `QA verdict: not-ready` and release recommendation
   `hold`.

## Execution instructions

1. Read all required upstream artifacts, existing optional context, and `contracts/stages/qa.md`
   before drafting outputs.
2. Verify upstream `review` outcome is not `rejected` and is consistent with implementation status.
   When `context/selected-task.md` is provided, use its expected scope, quality bar, and acceptance
   context to separate required scenario evidence from optional exploratory checks.
   When repository change evidence is provided, inspect every changed tracked or untracked
   deliverable file, excluding AIDD workspace/config artifacts, before deciding readiness.
3. Build `qa-report.md` with these exact H2 sections:
   `Quality verdict`, `Verification summary`, `Release recommendation`, `Evidence`,
   `Known issues`, and `Readiness`.
   In `Quality verdict`, put the quality decision on its own machine-readable line near the
   top, for example `- QA verdict: ready` (or `ready-with-risks` / `not-ready`), then add
   rationale separately.
4. In `Release recommendation`, put exactly one supported state on its own bullet:
   `proceed`, `proceed-with-conditions`, or `hold`.
5. In `Evidence`, label material evidence entries as `EV-1`, `EV-2`, ... and include command
   outcomes or artifact paths in backticks.
6. When `context/acceptance-criteria.md` exists, add an acceptance coverage checklist under
   `Evidence` or `Readiness` with one top-level bullet per criterion. Copy this shape:
   ``- AC-1: confirmed. Evidence: EV-1, `context/verification-output.md`. <criterion-specific sentence>.``
   Each bullet must name exactly one `AC-N` id and cite same-bullet evidence using an `EV-N` id
   and/or a backticked artifact path. Do not use range claims such as `AC-1 through AC-4`, and do
   not rely on a generic sentence such as `all acceptance criteria passed`.
7. Tie verdict and recommendation claims to `verification-output.md` and/or
   `verification-artifacts.md` references when those documents are provided, and otherwise cite
   concrete upstream evidence.
8. In `Known issues`, use `- Known issues: none.` only as an empty known-defect marker.
   Put residual risks in separate bullets such as
   `- Residual risk RR-1: Severity: low. ... Mitigation/ownership: ...`.
   Do not pair `QA verdict: ready` with residual risk bullets. If a real residual risk
   remains, use `ready-with-risks` and `proceed-with-conditions`; if the note is an
   intentional selected-boundary tradeoff already covered by evidence, keep it out of
   `Known issues` and summarize it under `Readiness` instead.
9. Use only supported recommendation values (`proceed`, `proceed-with-conditions`, `hold`).
10. If critical checks are missing, contradictory, or inconclusive, ask a `[blocking]` question
   instead of inventing assumptions.
11. Keep optional broader-check limitations as non-blocking notes when authored verification,
   review, and acceptance criteria are clean.
12. Keep `stage-result.md` and `validator-report.md` aligned with the final QA conclusion.

## Common output skeleton discipline

- Before writing `stage-result.md` or `validator-report.md`, use the exact common skeleton shown in `stage-brief.md`.
- Keep the required headings exactly as written; add stage-specific detail under those headings instead of renaming them.
- If a required section has no findings or blockers, write exactly `- none` rather than leaving it empty.
- If no clarification is needed and you create `questions.md` or `answers.md`, write exactly
  `# Questions\n\n- none\n` or `# Answers\n\n- none\n`; do not write prose such as
  `No questions required.` as a bullet.
- Keep `stage-result.md` status, `validator-report.md` verdict, questions, blockers, and next actions mutually consistent.

## Completion checklist

- quality verdict is explicit and evidence-backed,
- residual risks include severity plus mitigation/ownership,
- `QA verdict: ready` has no residual risk bullets; remaining real risks use
  `ready-with-risks` and `proceed-with-conditions`,
- release recommendation is actionable and consistent with verdict,
- material claims reference concrete verification evidence,
- each `AC-N` from acceptance context has its own evidence-backed checklist bullet when acceptance
  criteria are provided,
- unresolved critical uncertainty is surfaced as blocking question with `hold`,
- optional checks outside the authored verification boundary are not treated as release
  conditions unless they expose a concrete defect,
- intentional selected design constraints are not treated as residual risks when their required
  mitigations and evidence are complete,
- `qa-report.md`, `stage-result.md`, and `validator-report.md` are outcome-consistent.
