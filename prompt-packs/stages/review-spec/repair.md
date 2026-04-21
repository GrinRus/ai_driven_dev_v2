# Repair prompt for `review-spec`

You are rerunning the `review-spec` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose root causes before editing (issue quality gaps, weak recommendations, inconsistent readiness/sign-off).
3. Correct only missing or incorrect parts while preserving valid review findings.
4. Rework decision and readiness state together when severity profile changes.
5. Keep issue severity and recommendation priorities stable unless evidence justifies changes.
6. Update `stage-result.md` and `validator-report.md` so attempt outcome is truthful.

## Repair exit checks

- issue list quality and recommendation actionability meet contract intent,
- decision sign-off is coherent with readiness state and required changes,
- no blocking inconsistency remains between report, validator result, and stage status.
