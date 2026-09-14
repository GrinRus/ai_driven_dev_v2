# Release Notes: v0.1.0a22

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a22`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a21`.

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

- The candidate must pass the deterministic CI quality, coverage, adapter, browser, build, and
  security lanes before publication.
- Manual external E2E remains local operator-audit evidence and is not a release gate.
- Package publication is accepted only after PyPI, `pipx`, and `uv tool` verification jobs pass.

## Compatibility and limitations

- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Runtime binaries, authentication, and provider access remain external operator prerequisites.
- Docker/GHCR is not a supported alpha distribution channel.

## Publication checklist

- Release branch: `release/v0.1.0a22`.
- Publish only through the GitHub Release `published` event after deterministic release-branch
  checks pass.
- Accept the release only after PyPI, `pipx`, and `uv tool` verification jobs pass.
- Replace this draft status with observed publication and install-verification results after the
  release workflow reaches a terminal state.
