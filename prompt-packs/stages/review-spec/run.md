# Run prompt for `review-spec`

## Stage objective

Produce a review-ready `review-spec` package that makes go/no-go decomposition decisions explicit,
defensible, and consistent across report, validator output, and stage status.

The stage is complete only when issue severity is concrete, recommendations are actionable, and
sign-off state is coherent with required changes.

## Inputs to read first

- required:
  - `../plan/output/plan.md`
  - `../plan/output/stage-result.md`
  - `../plan/output/validator-report.md`
  - `context/review-context.md`
- optional context when available:
  - `context/repository-state.md`
  - `context/constraints.md`
  - `context/previous-decisions.md`
- contract of record:
  - `contracts/stages/review-spec.md`

## Required outputs (always write)

- `review-spec-report.md`
- `stage-result.md`
- `validator-report.md`

## Review discipline

1. Every issue must be concrete, scoped, severity-tagged, and rationale-backed.
2. Recommendation summary must map remediation steps to identified issues where applicable.
3. Recommendations must be prioritized and explicit enough for downstream execution.
4. Sign-off decision must be explicit (`approved`, `approved-with-conditions`, or `rejected`) and
   consistent with readiness state and required changes.
5. Blocking uncertainty must be turned into questions instead of implied assumptions.

## Execution instructions

1. Read required plan artifacts, review context, and `contracts/stages/review-spec.md` before
   drafting outputs.
2. If required plan artifacts are missing or inconsistent, do not mark stage as `succeeded`.
3. Draft `review-spec-report.md` with explicit sections for issue list, recommendation summary,
   readiness state, required changes, and decision/sign-off.
4. Keep issue wording tied to observable plan gaps or risks, not generic quality statements.
5. Map recommended actions to issue ids/severity where possible so remediation order is clear.
6. If contradictory constraints or missing decision authority block sign-off, raise a `[blocking]`
   question instead of forcing approval status.
7. Update `validator-report.md` and `stage-result.md` so verdict, blockers, and next actions remain
   consistent with report conclusions.

## Completion checklist

- issue list is concrete, severity-tagged, and rationale-backed,
- recommendations are prioritized and mapped to identified issues,
- readiness state, required changes, and sign-off decision are coherent,
- unresolved blocking ambiguity is captured as explicit questions,
- stage status and validator verdict agree with report outcome.
