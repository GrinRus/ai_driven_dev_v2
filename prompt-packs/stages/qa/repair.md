# Repair prompt for `qa`

You are rerunning the `qa` stage because validation failed.

## Repair rules

1. Read `validator-report.md` and `repair-brief.md` first.
2. Diagnose root causes before editing (`unsupported verdict`, `missing evidence references`, `cross-document mismatch`, or unresolved critical-check ambiguity).
3. Correct only missing or incorrect parts while preserving valid evidence-backed conclusions.
4. Rework quality verdict, release recommendation, and residual-risk summary together when evidence profile changes.
5. Remove or downgrade any claim that cannot be tied to concrete verification artifacts.
6. Update `stage-result.md` and `validator-report.md` so repaired attempt status is truthful.

## Repair exit checks

- quality verdict is explicitly supported by cited verification evidence,
- release recommendation is actionable and coherent with verdict/risk profile,
- no unresolved must-fix or missing-critical-check condition is hidden behind `ready`/`proceed` language,
- validator result and stage terminal status do not conflict.
