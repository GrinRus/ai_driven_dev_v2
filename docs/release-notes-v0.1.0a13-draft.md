# Release Notes: v0.1.0a13

Status: published on 2026-06-30 and accepted after package-channel verification.

Published package version: `0.1.0a13`.
Latest accepted published prerelease: `0.1.0a13`.

Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed
for `v0.1.0a13`.

## Summary

This prerelease prepares the Wave 33 live product-evaluation evidence loop for easier
operator review. It adds generated read-only bundle summaries, records maintained-matrix
coverage, and refreshes operator docs while keeping manual `quality-report.md` as the only
counted-clean quality decision. AIDD remains alpha software for local evaluation and
controlled operator trials.

## User-visible changes

- Product-evaluation live bundles now include generated
  `product-evaluation-bundle-summary.json` and `product-evaluation-bundle-summary.md`
  artifacts at the bundle root.
- Bundle summaries list stage-quality audit presence and decisions, remediation source
  ids, repair counts, tracked/untracked product files, known harness files, final report
  presence, and terminal flow-state/verdict consistency.
- Bundle summaries are navigation evidence only. They do not modify `verdict.md`,
  `grader.json`, `quality-report.md`, or compute counted-clean.
- The maintained live matrix records the canonical large/xlarge coverage state and keeps
  planned or experimental runtimes out of missing canonical coverage.
- Live E2E catalog, quality rubric, and skill guidance now state that manual
  `quality-report.md` remains the final counted-clean source.

## Compatibility

- CLI behavior, stage contracts, runtime adapters, and release workflows are unchanged.
- No live E2E automation is added to CI/CD or release workflows.
- Generated product-evaluation summaries are harness reports, not model-authored stage
  contracts and not runner-owned quality scoring.
- Runtime binaries and authentication remain external operator prerequisites.
- The `0.1.0a13` package is accepted package-channel evidence after GitHub Release,
  PyPI, `pipx`, and `uv tool` verification succeeded.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported alpha release contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator trials.
- Live E2E evidence remains local manual audit evidence and is not CI/CD, not a release
  workflow, not GitHub Actions, and not a release gate.
- Local Wave 33 large/xlarge counted-clean evidence is release context only; it is not
  committed under `.aidd/` and does not replace package-channel verification.
- Package verification is accepted: the GitHub Release workflow and independent local
  `pipx` plus `uv tool` checks passed for `0.1.0a13`.

## Release checklist

- GitHub Release target: `release/v0.1.0a13`.
- Release branch: `release/v0.1.0a13`.
- Release workflow: run by GitHub Release `published` event only.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a13/`.
- `pipx` and `uv tool` verification: accepted package-channel evidence.
