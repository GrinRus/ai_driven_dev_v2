# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`
- Dominant failure categories: malformed and unsupported review finding

## Structural checks

- none

## Semantic checks

- `SEM-INCOMPLETE-SECTION` (`medium`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no explicit severity label.
- `SEM-INCOMPLETE-SECTION` (`medium`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no disposition classification.
- `SEM-INCOMPLETE-SECTION` (`medium`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no rationale.
- `SEM-UNSUPPORTED-CLAIM` (`high`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no implementation or acceptance evidence.

## Cross-document checks

- none

## Result

- Verdict: `fail`
- Repair required for progression: yes
