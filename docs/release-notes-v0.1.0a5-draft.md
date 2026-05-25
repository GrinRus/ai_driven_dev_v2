# Release Notes: v0.1.0a5

Status: published on 2026-05-25.

Latest accepted published prerelease evidence: `0.1.0a5`.

## Summary

This prerelease follows the published `0.1.0a4` prerelease with release-readiness cleanup,
strict interview repair-prompt clarification, and refreshed W24 manual live operator
evidence. It keeps AIDD in prerelease alpha and does not expand the product scope.

## User-visible changes

- Clarified repair prompts for strict interview documents so runtime repair attempts call
  out that answer lines such as `- Q1 [resolved]: ...` are invalid.
- Refreshed W24 manual live readiness evidence for the maintained beta scenario/runtime
  matrix:
  `AIDD-LIVE-002/codex`, `AIDD-LIVE-007/codex`, `AIDD-LIVE-007/claude-code`,
  `AIDD-LIVE-006/opencode`, and `AIDD-LIVE-008/opencode`.
- Clarified release-readiness documentation so `0.1.0a5` moved from current candidate to
  latest accepted published prerelease evidence only after GitHub Release, PyPI, `pipx`,
  and `uv tool` verification passed.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed
for GitHub Release `v0.1.0a5`.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains local manual audit evidence and is not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Runtime binaries and authentication are external operator prerequisites.
- W24 manual live evidence has been refreshed locally for the maintained beta evidence
  matrix, but that evidence remains local operator-audit evidence and is separate from
  package-channel acceptance.

## Release checklist

- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a5`.
- Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26385081630`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a5/`.
- Release tag `v0.1.0a5` matched `project.version` `0.1.0a5` and the remote
  `release/v0.1.0a5` branch HEAD before publishing.
