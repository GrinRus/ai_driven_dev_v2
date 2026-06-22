# Release Notes: v0.1.0a11

Status: published on 2026-06-22, then superseded by the `v0.1.0a12` hotfix
candidate for raw-log CLI rendering.

Published package version: `0.1.0a11`.
Superseding hotfix candidate: `0.1.0a12`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a10`.

## Summary

This prerelease prepares the post-`v0.1.0a10` live E2E hardening work for package
publication. It keeps AIDD in alpha and does not make a beta-readiness or unattended
production claim.

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
- The published `0.1.0a11` package is superseded by `0.1.0a12` because
  exact-PyPI live audit found a raw runtime log rendering crash in
  `aidd run logs`.

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
- Exact-PyPI `AIDD-LIVE-011` is not counted for `0.1.0a11` because it found the
  raw-log CLI rendering defect fixed in the `0.1.0a12` hotfix candidate.

## Release checklist

- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a11`,
  target `release/v0.1.0a11`.
- Release branch: `release/v0.1.0a11`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a11/`.
- Superseded by: `v0.1.0a12` hotfix candidate.
