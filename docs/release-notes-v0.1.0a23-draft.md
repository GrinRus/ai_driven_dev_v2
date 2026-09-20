# Release Notes: v0.1.0a23

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a23`.
Latest accepted published prerelease before this candidate: `v0.1.0a22`.

## Summary

This alpha prerelease consolidates the latest Operator UI recovery improvements, evidence
validation hardening, and deterministic release-quality checks.

## User-visible changes

- Recover stale Operator UI context without leaving the selected task scope, and expose every
  pending implementation question with explicit prompts and durable recovery actions.
- Improve implementation and task-list evidence handling for nested command results, repository-
  prefixed commands, compound shell checks, checksums, listings, concrete CLI evidence, and
  bounded task-list placeholders.
- Keep implementation claims itemized and prevent verification-only evidence from being mistaken
  for implementation completion.
- Align the Operator UI's shared controls, responsive terminal handoff, and visual documentation
  with the shipped cobalt semantic palette.

## Quality and evidence

- The candidate must pass deterministic CI quality, coverage, adapter, browser, build, and security
  lanes before publication.
- Manual external E2E remains local operator-audit evidence and is not a release gate.
- Package publication is accepted only after PyPI, `pipx`, and `uv tool` verification jobs pass.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a23`.
- Publish only through the GitHub Release `published` event after deterministic release-branch
  checks pass.
- Accept the release only after PyPI, `pipx`, and `uv tool` verification jobs pass.
- Replace this draft status with observed publication and install-verification results after the
  release workflow reaches a terminal state.
