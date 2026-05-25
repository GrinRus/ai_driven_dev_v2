# Draft Release Notes: v0.1.0a5

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a5`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a4`.

## Summary

This release candidate follows the published `0.1.0a4` prerelease with release-readiness
cleanup, strict interview repair-prompt clarification, and refreshed W24 manual live
operator evidence. It keeps AIDD in prerelease alpha and does not expand the product scope.

## User-visible changes

- Clarified repair prompts for strict interview documents so runtime repair attempts call
  out that answer lines such as `- Q1 [resolved]: ...` are invalid.
- Refreshed W24 manual live readiness evidence for the maintained beta scenario/runtime
  matrix:
  `AIDD-LIVE-002/codex`, `AIDD-LIVE-007/codex`, `AIDD-LIVE-007/claude-code`,
  `AIDD-LIVE-006/opencode`, and `AIDD-LIVE-008/opencode`.
- Clarified release-readiness documentation so `0.1.0a5` is the current candidate while
  `0.1.0a4` remains the latest accepted published prerelease evidence.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

The `0.1.0a5` package must not be described as the latest accepted published prerelease
until the GitHub Release is published and the release workflow quality, build, PyPI publish,
`pipx`, and `uv tool` verification jobs pass. Until then, `0.1.0a4` remains the latest
accepted published prerelease evidence.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains local manual audit evidence and is not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Runtime binaries and authentication are external operator prerequisites.
- W24 manual live evidence has been refreshed locally for the maintained beta evidence
  matrix, but that evidence is not publish/install acceptance evidence for `0.1.0a5`.

## Release checklist

- Confirm `pyproject.toml` version is set to `0.1.0a5` before creating the release branch.
- Run deterministic local gates.
- Run `ci.yml` and `release.yml` dry-runs on `release/v0.1.0a5`.
- Publish the GitHub Release only after explicit maintainer approval.
- Confirm the release workflow quality, build, publish, `pipx`, and `uv tool` verification
  jobs pass for GitHub Release `v0.1.0a5`.
