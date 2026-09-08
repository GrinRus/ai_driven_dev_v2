# Complexity baseline

`complexity-baseline.json` is the reviewed Radon 6 baseline for Python production code under
`src/**/*.py`. Radon grades cyclomatic complexity as `E` for 31–40 and `F` for 41 or higher.
The baseline records the existing E/F debt so it is visible and can be reduced by the
W49-E2-S3 decomposition tasks.

`make check-complexity` (also run in the CI lint lane) enforces two rules:

- a new E/F block must be explicitly reviewed and added to the baseline;
- a baselined block may not increase its reviewed complexity.

When a refactor removes or renames a baselined block, update the baseline in the same change and
preserve the behavior characterization tests. Do not lower a baseline number to hide a regression.
