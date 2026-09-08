# Quality baselines

## Critical-module coverage baseline

`critical-coverage-baseline.json` records reviewed line and branch coverage for a focused
allowlist of lifecycle, evidence, adapter, and scenario-gate modules. It is intentionally not a
repository-wide percentage and excludes `src/aidd/cli/static/**`, frontend tests, and browser/UI
surfaces owned by the adjacent UI worktree. The `revision`, Python/Coverage versions, test paths,
and exact pytest arguments make the measurement reproducible from a clean checkout.

Run the baseline measurement from the repository root with the command represented by the
`command` and `test_paths` arrays in the JSON file. Write the JSON report to
`coverage-critical.json`, then compare it with the reviewed baseline:

```bash
uv run --extra dev python scripts/check_critical_coverage.py \
  --baseline docs/quality/critical-coverage-baseline.json \
  --report coverage-critical.json
```

The checker reports a missing critical module or a line/branch regression. Threshold enforcement
is intentionally a separate follow-up (`W49-E4-S2-T2`) so this reviewed measurement can land
before a CI ratchet is enabled.

## Complexity baseline

`complexity-baseline.json` is the reviewed Radon 6 baseline for Python production code under
`src/**/*.py`. Radon grades cyclomatic complexity as `E` for 31–40 and `F` for 41 or higher.
The baseline records the existing E/F debt so it is visible and can be reduced by the
W49-E2-S3 decomposition tasks.

`make check-complexity` (also run in the CI lint lane) enforces two rules:

- a new E/F block must be explicitly reviewed and added to the baseline;
- a baselined block may not increase its reviewed complexity.

When a refactor removes or renames a baselined block, update the baseline in the same change and
preserve the behavior characterization tests. Do not lower a baseline number to hide a regression.
