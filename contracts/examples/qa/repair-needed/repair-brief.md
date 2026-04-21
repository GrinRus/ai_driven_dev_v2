# Repair Brief

## Trigger

Validator flagged unsupported `ready/proceed` conclusions and evidence-free QA claims.

## Root cause

QA report declared success without tying verdict/recommendation to verification artifacts and ignored unresolved critical-check ambiguity.

## Minimal fix plan

1. Rebuild `qa-report.md` from concrete verification outputs and artifact references.
2. Recompute quality verdict and release recommendation from actual risk profile.
3. Add explicit residual-risk entries for unresolved checks with mitigation ownership.
4. Update `stage-result.md` and `validator-report.md` to reflect repaired outcome.

## Rerun budget

- Remaining repair attempts: 2
