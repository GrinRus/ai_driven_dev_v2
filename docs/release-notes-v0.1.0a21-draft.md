# Release Notes: v0.1.0a21

Status: published on 2026-09-01; accepted package-channel evidence.

Published package version: `0.1.0a21`.
Latest accepted published prerelease evidence: `0.1.0a21`.

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
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/33546307202`.
- Manual external E2E remains local operator-audit evidence and is not a release gate.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a21`.
- Published through the GitHub Release `published` event after deterministic release-branch
  checks passed.
- PyPI, `pipx`, and `uv tool` verification jobs passed.
- Tag and release branch resolve to `1d49477ee70145e80de760bf37e41bd2f211ced8`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a21/`.
