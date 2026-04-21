# Validator Report

## Summary

- Total issues: 3
- Blocking issues: yes
- Affected documents: `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`, `workitems/WI-PLAN-EXAMPLE/stages/plan/output/questions.md`
- Dominant failure categories: sequencing and approval-readiness gaps

## Structural checks

- none

## Semantic checks

- `SEM-UNSUPPORTED-CLAIM` (`high`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`: milestone sequencing lacks dependency-aware rationale.
- `STRUCT-EMPTY-SECTION` (`high`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/plan.md`: `Verification notes` does not provide milestone-risk coverage.

## Cross-document checks

- `CROSS-BLOCKING-UNANSWERED` (`critical`) in `workitems/WI-PLAN-EXAMPLE/stages/plan/output/questions.md`: Q1 is blocking and has no matching resolved answer.

## Result

- Verdict: `fail`
- Repair required for progression: yes
