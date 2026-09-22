# Release Notes: v0.1.0a24

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a24`.
Latest accepted published prerelease before this candidate: `v0.1.0a23`.

## Summary

This alpha prerelease consolidates the latest Operator UI recovery fixes, task-list and evidence
validation hardening, and deterministic release-quality coverage.

## User-visible changes

- Keep unresolved-question recovery, resume actions, runtime readiness, active-workspace context,
  long identities, and terminal recovery visible and scoped to the selected work item.
- Preserve explicit prerequisite chains from Plan into Tasklist and keep verification inputs out of
  implementation edit scope.
- Reject unresolved command placeholders and retain exact upstream QA evidence paths so validation
  failures surface as actionable repair work instead of silently progressing.
- Improve evidence parsing for chained dependencies, bound commands, no-op markers, repository-
  prefixed paths, and retained implementation/QA artifacts.

## Quality and evidence

- The candidate must pass deterministic CI quality, coverage, adapter, browser, build, and security
  lanes before publication.
- Local packaged UI and browser journeys are covered by the release preflight and remain provider-
  free.
- Manual external E2E remains local operator-audit evidence and is not a release gate.
- Package publication is accepted only after PyPI, `pipx`, and `uv tool` verification jobs pass.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release does
  not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a24`.
- Publish only through the GitHub Release `published` event after deterministic release-branch
  checks pass.
- Accept the release only after PyPI, `pipx`, and `uv tool` verification jobs pass.
- Replace this draft status with observed publication and install-verification results after the
  release workflow reaches a terminal state.
