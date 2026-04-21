# Stage Result

## Stage

- `review`

## Attempt history

- Attempt 1 (`initial`) -> validation `fail`; review findings were incomplete and unsupported.

## Status

- `blocked`

## Produced outputs

- `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`
- `workitems/WI-REVIEW-EXAMPLE/stages/review/output/validator-report.md`
- `workitems/WI-REVIEW-EXAMPLE/stages/review/output/repair-brief.md`
- `workitems/WI-REVIEW-EXAMPLE/stages/review/output/stage-result.md`

## Validation summary

- Validator verdict: `fail` from `workitems/WI-REVIEW-EXAMPLE/stages/review/output/validator-report.md`.
- Unsupported finding and missing severity/disposition fields require repair before progression.

## Blockers

- blocking validator findings require repair of review artifacts.

## Next actions

- Add evidence-backed findings with explicit severity and disposition labels.
- Reconcile approval status with unresolved must-fix findings.

## Terminal state notes

- Stage stopped pending repair on review quality defects.
- Progression to QA is not allowed until validator pass.
