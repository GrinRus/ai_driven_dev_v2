# Validator Report

## Summary

- Total issues: 3
- Blocking issues: yes
- Affected documents: `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`, `workitems/WI-PLAN-EXAMPLE/stages/plan/output/questions.md`
- Dominant failure categories: incomplete risk and verification coverage

## Structural checks

- none

## Semantic checks

- `SEM-INCOMPLETE-SECTION` (`medium`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`: each `Risks` item must include mitigation direction.
- `SEM-INCOMPLETE-SECTION` (`medium`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`: `Verification notes` cannot be `none` and must map checks to milestone ids.

## Cross-document checks

- `CROSS-BLOCKING-UNANSWERED` (`critical`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/questions.md`: Q1 is blocking and has no matching resolved answer.

## Result

- Verdict: `fail`
- Repair required for progression: yes
