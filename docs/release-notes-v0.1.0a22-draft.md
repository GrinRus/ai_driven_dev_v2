# Release Notes: v0.1.0a22

Status: published prerelease; package-channel verification passed.

Published package version: `0.1.0a22`.
Previous accepted published prerelease: `0.1.0a21`.

## Summary

This alpha prerelease consolidates the current-format cleanup, evidence and release
reproducibility work, and the latest Claude Code live-flow hardening.

## User-visible changes

- Preserve task-local repository baselines across implementation repairs and resumes so partial
  edits remain observable without folding in unrelated prerequisite changes.
- Make QA upstream validation honor parsed review dispositions, avoiding false blockers caused by
  explanatory `must-fix` wording in accepted follow-up findings.
- Require current persisted execution formats and remove retired configuration and artifact
  compatibility paths; existing workspaces should be recreated with the current CLI.
- Improve isolated Claude Code execution, retained runtime evidence, and fail-closed workflow
  state handling for controlled live evaluations.
- Add reproducible candidate manifests, readiness records, installed deterministic matrices, and
  exact-wheel verification through the supported `pipx` and `uv tool` paths.

## Quality and evidence

- The candidate passed deterministic CI quality, coverage, adapter, browser, build, and security
  lanes before publication.
- Manual external E2E remains local operator-audit evidence and is not a release gate.
- The release workflow published to PyPI and passed both `pipx` and `uv tool` installation
  verification jobs.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a22`.
- Published through the GitHub Release `published` event after deterministic release-branch
  checks passed.
- Accepted after `publish-pypi`, `verify-pypi-install`, and `verify-uv-tool-install` all passed.
- Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/34874926414`.
- PyPI package: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a22/`.
