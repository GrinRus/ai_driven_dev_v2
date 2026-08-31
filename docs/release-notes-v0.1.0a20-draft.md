# Release Notes: v0.1.0a20

Status: published on 2026-08-31; accepted package-channel evidence.

Published package version: `0.1.0a20`.
Latest accepted published prerelease evidence: `0.1.0a20`.

## Summary

This alpha prerelease carries forward the task-centered operator workflow and document-first
validation, recovery, and live-evaluation evidence paths prepared for `v0.1.0a19`, with a
compatible package build metadata pin.

## User-visible changes

- Add the task-centered operator workspace with launch readiness, dependency-aware task views,
  selected-task actions, active-attempt visibility, Markdown evidence, decision recovery,
  implementation review, run history, and immutable Flow Complete handoff.
- Preserve canonical work-item identifiers, routes, CLI behavior, Markdown contracts, and
  historical evidence while keeping technical lineage and runtime controls contextual.
- Add durable interview resume and QID-ledger behavior, tolerant tasklist presentation and
  located findings, one-time repair-extension recovery, and provider-free resilience scenarios.
- Harden implementation verification evidence, dependency parsing, bounded target diffs, and
  task-aware live checkpoints for large external evaluations.
- Pin Hatchling to Core Metadata 2.4 so PyPI publication remains compatible with the release
  publisher.

## Quality and evidence

- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
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

- Release branch: `release/v0.1.0a20`.
- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a20`.
- Published workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/33385397818`.
- Tag and release branch resolve to `0803711c1e6f24c931803b13c852e8d727286d54`.
- Quality (Python 3.12/3.13/3.14), build, PyPI publish, `pipx`, and `uv tool` verification
  jobs passed.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a20/`.
- The current source development version is `0.1.0a21.dev0`; no candidate from it is accepted.
- Docker/GHCR is not a supported alpha distribution channel.
