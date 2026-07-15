# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`
- Dominant failure categories: incomplete execution summary, missing diff, and unverifiable claims

## Structural checks

- none

## Semantic checks

- `SEM-INCOMPLETE-EXECUTION-SUMMARY` (`medium`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: no-op output lacks evidence-backed justification.
- `SEM-INCOMPLETE-EXECUTION-SUMMARY` (`medium`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: no-op output lacks an actionable follow-up step.
- `SEM-MISSING-DIFF-EVIDENCE` (`high`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: change summary claims completed implementation but touched-files list is empty.
- `SEM-UNVERIFIABLE-CHECK-CLAIM` (`high`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: verification outcome lacks executable command evidence.

## Cross-document checks

- none

## Result

- Verdict: `fail`
- Repair required for progression: yes
