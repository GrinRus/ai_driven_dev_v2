# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`, `workitems/WI-QA-EXAMPLE/stages/qa/output/stage-result.md`
- Dominant failure categories: missing risks, unsupported verdict, and missing evidence

## Structural checks

- none

## Semantic checks

- `SEM-RISK-UNDERREPORT` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: `ready-with-risks` requires explicit residual risk entries.
- `SEM-RISK-UNDERREPORT` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: `proceed-with-conditions` requires explicit residual risk entries.
- `SEM-MISSING-EVIDENCE-REF` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: material QA claims and release recommendation lack concrete evidence.
- `SEM-UNSUPPORTED-VERDICT` (`high`) in `workitems/WI-QA-EXAMPLE/stages/qa/output/qa-report.md`: ready/proceed outcome is unsupported without verification evidence.

## Cross-document checks

- none

## Result

- Verdict: `fail`
- Repair required for progression: yes
