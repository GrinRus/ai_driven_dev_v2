# Release Notes: v0.1.0a24

Status: published and verified on 2026-09-22.

Published package version: `0.1.0a24`.
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

## Publication evidence

- Release branch: `release/v0.1.0a24`.
- Tag: `v0.1.0a24` at commit `95e457e6f30c8f03c163e00174849ce88ce44ffe`.
- GitHub Release: https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a24
- Release workflow: https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/35671164113
- Result: published prerelease and package-channel evidence accepted.
- Job results: `quality` passed on Python 3.12, 3.13, and 3.14; `build` passed;
  `publish-pypi` passed; `verify-pypi-install` passed; `verify-uv-tool-install` passed.
- PyPI: https://pypi.org/project/ai-driven-dev-v2/0.1.0a24/
- Independent isolated `pipx` install returned `aidd 0.1.0a24`; `aidd doctor` completed
  successfully.
- Independent isolated `uv tool` install returned `aidd 0.1.0a24`; `aidd doctor` completed
  successfully.
- No Docker/GHCR artifact was published.
