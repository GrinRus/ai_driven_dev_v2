# Release Notes: v0.1.0a15

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a15`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a14`.

The `0.1.0a15` package must not be described as the latest accepted published prerelease
until the GitHub Release workflow publishes to PyPI and verifies `pipx` plus `uv tool`
installability.

## Summary

This prerelease prepares the operator frontend recovery UX work after accepted
`v0.1.0a14` package-channel evidence. It focuses on making failed QA handoffs,
follow-up launch, clone, eval, archive, and history decisions clearer for a first-time
operator while preserving immutable terminal-run evidence.

## User-visible changes

- Failed terminal QA handoffs now consistently promote `Start Follow-up Flow` as the
  remediation path.
- Follow-up flow screens better explain source findings, definition blockers, preflight
  failures, launch failures, and runtime readiness changes.
- Clone, eval, archive, history, and fresh-work paths are labeled as secondary,
  clone-only, comparison-only, navigation-only, or separate-scope actions instead of
  remediation.
- Recovery actions remain visible earlier on desktop and mobile unhappy paths.
- Browser-verified UX audit evidence records before/after behavior for recovery, clone,
  eval, and archive states.

## Compatibility

- The core workflow remains runtime-agnostic and document-first.
- Runtime-specific behavior stays inside adapters.
- No manual external eval automation is added to CI/CD or release workflows.
- Runtime binaries and authentication remain external operator prerequisites.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported alpha release contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator trials.
- Manual external eval evidence remains local operator audit evidence and is not CI/CD,
  not a release workflow, not GitHub Actions, and not a release gate.
- Package verification has not yet run for `v0.1.0a15`; this draft becomes accepted
  release evidence only after the GitHub Release workflow publishes and verifies the
  package.

## Release checklist

- GitHub Release target: `release/v0.1.0a15`.
- Release branch: `release/v0.1.0a15`.
- Release workflow: run by GitHub Release `published` event only.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs are
  still pending until publication.
- PyPI: pending `https://pypi.org/project/ai-driven-dev-v2/0.1.0a15/`.
- `pipx` and `uv tool` verification: pending package-channel evidence.
