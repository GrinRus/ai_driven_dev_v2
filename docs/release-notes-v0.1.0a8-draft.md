# Release Notes: v0.1.0a8

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a8`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a7`.

The `0.1.0a8` package must not be described as the latest accepted published prerelease
until GitHub Release publication, PyPI publish, `pipx`, and `uv tool` verification all
succeed.

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
- Package acceptance still requires GitHub Release publication, PyPI publish, `pipx`, and
  `uv tool` verification for this exact version.
