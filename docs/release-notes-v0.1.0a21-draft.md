# Release Notes: v0.1.0a21

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a21`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a20`.

## Summary

This alpha prerelease carries the release and documentation hardening merged after `v0.1.0a20`.

## User-visible changes

- Make CI aggregate checks fail closed when any required lane is skipped or fails.
- Harden release verification for `pipx` and `uv tool` installs, package metadata, and release
  publication evidence.
- Align the Operator Handbook configuration inventory with supported runtime selectors and
  permission controls.
- Document that stopping the local UI server does not cancel active runtime jobs.

## Quality and evidence

- Deterministic Python, frontend, browser, adapter-conformance, scenario, security, and package
  build checks are required by the release workflow.
- Package publication is accepted only after PyPI, `pipx`, and `uv tool` verification jobs pass.
- Manual external E2E remains local operator-audit evidence and is not a release gate.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a21`.
- Publish only through the GitHub Release `published` event after deterministic release-branch
  checks pass.
- Accept the release only after PyPI, `pipx`, and `uv tool` verification jobs pass.
- The `0.1.0a21` package must not be described as the latest accepted published prerelease until
  all publication and install-verification evidence is complete.
