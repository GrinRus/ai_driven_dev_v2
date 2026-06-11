# Release Notes: v0.1.0a10

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a10`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a9`.

`0.1.0a10` package must not be described as the latest accepted published prerelease until
GitHub Release publication, PyPI publishing, `pipx`, and `uv tool` verification all pass.

## Summary

This prerelease candidate rolls up the post-`v0.1.0a9` work on the integrated operator
workbench, stage preflight correctness, and live E2E quality gates. It keeps AIDD in alpha
and does not make a beta-readiness or unattended-production claim.

## User-visible changes

- Added the integrated operator workbench shell and project-home surfaces so operators can
  navigate setup, current runs, stage cockpit, artifacts, and next-flow actions with a
  denser command-center layout.
- Fixed stage input preflight behavior so missing prerequisites are reported before runtime
  execution instead of being discovered through later stage failure modes.
- Tightened live E2E artifact completeness gates, review obligation checks, QA scoring,
  repair signals, and touched-file accounting for target-project code quality.
- Added Claude large live E2E coverage for the maintained live catalog and kept live E2E
  as local operator evidence, not a release workflow gate.
- Neutralized maintained live prompt examples so reusable AIDD prompts do not encode
  target-specific live-run solutions.

## Compatibility

- Existing CLI behavior remains compatible for `aidd`, `aidd --help`, `aidd doctor`,
  `aidd init`, `aidd run`, `aidd stage ...`, and `aidd ui --work-item ...`.
- `aidd ui` without `--work-item` continues to open setup/onboarding mode.
- Runtime launches still require an explicit runtime id; no hidden fallback is added.
- Runtime binaries and authentication remain external operator prerequisites.

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
- `0.1.0a10` is not accepted package-channel evidence until the release workflow publishes
  and verifies PyPI, `pipx`, and `uv tool` installability.

## Release checklist

- GitHub Release: pending draft `v0.1.0a10`, target `release/v0.1.0a10`.
- Release branch: `release/v0.1.0a10`.
- Remote dry-runs: pending.
- PyPI: must become `https://pypi.org/project/ai-driven-dev-v2/0.1.0a10/` only after
  publication.
- Publish remains blocked until separate explicit approval.
