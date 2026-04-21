# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`
- Dominant failure categories: unsupported findings and missing review labels

## Structural checks

- none

## Semantic checks

- `SEM-UNSUPPORTED-FINDING` (`high`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: RV-1 does not reference implementation evidence or acceptance-criteria mismatch.
- `SEM-MISSING-SEVERITY` (`high`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no explicit severity label.
- `SEM-MISSING-DISPOSITION` (`high`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/review-report.md`: finding RV-1 has no disposition classification.

## Cross-document checks

- `CROSS-APPROVAL-MISMATCH` (`critical`) in `workitems/WI-REVIEW-EXAMPLE/stages/review/output/stage-result.md`: `approved` status conflicts with unresolved must-fix-level review concerns.

## Result

- Verdict: `fail`
- Repair required for progression: yes
