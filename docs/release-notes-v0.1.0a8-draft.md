# Release Notes: v0.1.0a8

Status: published on 2026-06-04.

Latest accepted published prerelease: `0.1.0a8`.

## Summary

This prerelease is a focused UI audit hotfix after the accepted `0.1.0a7` prerelease.
It keeps the UI-first onboarding and operator control center features intact while fixing
two operator-flow gaps found during clean install and source smoke audits.

## User-visible changes

- Fixed onboarding form state so `Create work item` becomes enabled immediately after the
  operator enters a work item id and request text, including the path where a runner was
  selected before the form was filled.
- Added a visible `Run selected stage` action in the command center for bounded operator
  smoke flows and stage-by-stage execution through the UI.
- Kept `Run workflow` as the primary full-flow action and preserved the existing CLI
  command contracts.
- Kept runtime launch explicit: UI/API stage launches still require a selected runtime id,
  with no hidden `generic-cli` fallback.
- Updated operator/audit documentation to distinguish successful job status `completed`
  from stage rail status `succeeded`.

## Compatibility

- Existing CLI behavior remains compatible for `aidd`, `aidd --help`, `aidd doctor`,
  `aidd init`, `aidd run`, `aidd stage ...`, and `aidd ui --work-item ...`.
- `aidd ui` without `--work-item` continues to open setup/onboarding mode.
- Runtime binaries and authentication remain external operator prerequisites.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator trials.
- Live E2E evidence remains local manual audit evidence and is not CI/CD, not a release
  workflow, not GitHub Actions, and not a release gate.
- Runtime binaries and authentication remain external operator prerequisites.

## Release checklist

- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a8`,
  target `release/v0.1.0a8`.
- Release branch: `release/v0.1.0a8`.
- Release workflow:
  `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26936369016`.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a8/`.
