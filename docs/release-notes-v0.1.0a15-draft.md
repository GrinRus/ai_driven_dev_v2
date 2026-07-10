# Release Notes: v0.1.0a15

Status: published on 2026-07-10 and accepted.

Accepted package version: `0.1.0a15`.
Previous accepted published prerelease evidence: `0.1.0a14`.

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
- Package verification passed for `v0.1.0a15` through the GitHub Release workflow and
  independent local `uv tool` smoke.

## Release checklist

- GitHub Release target: `release/v0.1.0a15`.
- Release branch: `release/v0.1.0a15`.
- Release workflow: run by GitHub Release `published` event only.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed
  in `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/29069296628`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a15/`.
- `pipx` and `uv tool` verification: accepted package-channel evidence.
