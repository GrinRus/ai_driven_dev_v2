# Release Notes: v0.1.0a19

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a19`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a18`.

## Summary

This alpha prerelease consolidates the task-centered operator workflow and hardens the
document-first validation, recovery, and live-evaluation evidence paths used by maintained
Codex and Claude Code runs.

## User-visible changes

- Add a task-centered operator workspace with launch readiness, dependency-aware task views,
  selected-task actions, active-attempt visibility, Markdown evidence, decision recovery,
  implementation review, run history, and immutable Flow Complete handoff.
- Preserve canonical work-item identifiers, routes, CLI behavior, Markdown contracts, and
  historical evidence while moving technical lineage and runtime controls into contextual
  surfaces.
- Add durable interview resume and QID-ledger behavior, tolerant tasklist presentation and
  located findings, one-time repair-extension recovery, and provider-free resilience scenarios.
- Harden implementation verification evidence, dependency parsing, bounded target diffs, and
  task-aware live checkpoints for large external evaluations.
- Expand responsive browser and accessibility coverage for the supported operator surfaces.

## Quality and evidence

- Deterministic Python, frontend, browser, adapter-conformance, scenario, security, and package
  build checks are required by the release workflow.
- Fresh local Large `AIDD-LIVE-012` runs for Codex and Claude Code completed `idea → qa` with
  terminal `pass`, target verification, manual stage-quality reports, and schema-v1 task-aware
  checkpoints. See `docs/e2e/live-large-codex-claude-run-report-2026-08-31.md`.
- The selected Starlette target is backend-only; no target product UI/design surface exists for
  a pixel-level comparison. Manual live E2E remains outside CI/CD and release automation.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Human usability observation, cross-runtime lower-capability comparison, Claude/beta acceptance,
  and Wave 36 sessions remain deferred.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a19`.
- Publish only through the GitHub Release `published` event after deterministic release-branch
  checks pass.
- Accept the release only after PyPI, `pipx`, and `uv tool` verification jobs pass.

`0.1.0a19` package must not be described as the latest accepted published prerelease until
the package-channel verification jobs complete successfully.
