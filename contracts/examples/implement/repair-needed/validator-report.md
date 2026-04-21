# Validator Report

## Summary

- Total issues: 4
- Blocking issues: yes
- Affected documents: `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`
- Dominant failure categories: missing diffs and unverifiable claims

## Structural checks

- none

## Semantic checks

- `SEM-MISSING-DIFF-EVIDENCE` (`high`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: change summary claims completed implementation but touched-files list is empty.
- `SEM-UNVERIFIABLE-CHECK-CLAIM` (`high`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: verification note says "Full test suite passed" without executable command/result evidence.
- `SEM-INCOMPLETE-EXECUTION-SUMMARY` (`medium`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/implementation-report.md`: follow-up section does not capture residual risk despite unsupported completion claims.

## Cross-document checks

- `CROSS-STATUS-VALIDATOR-MISMATCH` (`critical`) in `workitems/WI-IMPLEMENT-EXAMPLE/stages/implement/output/stage-result.md`: stage status conflicts with blocking validator findings.

## Result

- Verdict: `fail`
- Repair required for progression: yes
