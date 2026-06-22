# Release Notes: v0.1.0a11

Status: published on 2026-06-22.

Published package version: `0.1.0a11`.
Latest accepted published prerelease evidence: `0.1.0a11`.

## Summary

This prerelease publishes the post-`v0.1.0a10` live E2E hardening work. It keeps AIDD in
alpha and does not make a beta-readiness or unattended production claim.

## User-visible changes

- Live E2E reports are execution-only: runner outputs describe run integrity and evidence
  bundles, while deliverable quality is recorded manually in `quality-report.md`.
- Live evidence now includes per-stage timeout policy, target workspace classifications,
  verification-residue cleanup, and non-gating stage-result consistency warnings.
- Manual post-run quality reporting now explicitly covers artifact quality, code/test
  quality, workspace hygiene, and AIDD operator UI/UX.
- Maintained live prompts, contracts, scenario manifests, and runtime setup now emphasize
  installed `aidd` self-checks, shared public-surface checks, and tracked/untracked diff
  accounting.
- Operator UI stage navigation and maintained runtime evidence were hardened through the
  current supported Codex and Claude Code live matrix.

## Compatibility

- Existing CLI behavior remains compatible for `aidd`, `aidd --help`, `aidd doctor`,
  `aidd init`, `aidd run`, `aidd stage ...`, and `aidd ui --work-item ...`.
- Runtime launches still require an explicit runtime id; no hidden fallback is added.
- Runtime binaries and authentication remain external operator prerequisites.
- `0.1.0a11` is the latest accepted published prerelease after GitHub Release, PyPI,
  `pipx`, and `uv tool` verification succeeded.

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
- Provider smoke reproducibility depends on the operator shell environment; provider
  binaries outside the Codex app's default non-interactive PATH should be run through a
  login shell or explicit PATH prefix.
- Package verification is accepted for `0.1.0a11`; the GitHub Release workflow and
  independent local `pipx` plus `uv tool` checks passed.

## Release checklist

- GitHub Release target: `release/v0.1.0a11`.
- Release branch: `release/v0.1.0a11`.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- Release workflow:
  `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/27942016411`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a11/`.
- `pipx` and `uv tool` verification: passed.
