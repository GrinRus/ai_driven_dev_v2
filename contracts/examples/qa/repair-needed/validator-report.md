# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`, `workitems/WI-QA-EXAMPLE/stages/qa/output/stage-result.md`
- Dominant failure categories: unsupported verdict and missing evidence references

## Structural checks

- none

## Semantic checks

- `SEM-UNSUPPORTED-VERDICT` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: `ready` verdict is not supportable because critical verification artifacts are missing.
- `SEM-MISSING-EVIDENCE-REF` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: material QA claims and release recommendation are not linked to concrete evidence.
- `SEM-RISK-UNDERREPORT` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: residual risk section reports `none` despite unresolved critical-check ambiguity.

## Cross-document checks

- `CROSS-RECOMMENDATION-MISMATCH` (`critical`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/stage-result.md`: stage status and recommendation imply progression while validator findings require repair.

## Result

- Verdict: `fail`
- Repair required for progression: yes
