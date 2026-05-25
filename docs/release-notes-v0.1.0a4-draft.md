# Release Notes: v0.1.0a4

Status: published on 2026-05-23.

## Summary

This release candidate focuses on the local operator UI runtime flow. It keeps AIDD in
prerelease alpha while making stage execution, question handling, live logs, and artifact
inspection more consistent between the UI and CLI.

## User-visible changes

- Added separate UI actions for full workflow execution and selected-stage execution.
- Selected-stage UI runs now use the same stage-run semantics as `aidd stage run <stage>`.
- UI run actions return async job ids and expose polling live runtime logs while a job runs.
- Persisted `runtime.log` remains available after job completion through the existing log
  view and CLI read surfaces.
- Added a read-only artifact document viewer in the UI with safe Markdown Preview and Source
  modes.
- Primary stage outputs such as `idea-brief.md`, `research-notes.md`, and `plan.md` are
  included in artifact indexes and can be rendered directly in the UI.
- Clarified question-answer handling: the UI writes `[resolved]` answer entries, and CLI
  operators edit `answers.md` after inspecting `aidd stage questions`.
- Fresh UI work items now load without `/api/run` errors before the first run exists.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains local manual audit evidence and is not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Runtime binaries and authentication are external operator prerequisites.
- UI v1 persists only `[resolved]` answers; `[partial]` and `[deferred]` remain CLI/file-mode
  behavior.

## Release checklist

- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed
  for GitHub Release `v0.1.0a4`.
- Refresh manual live evidence locally, separately from release automation, when maintainers
  need an operator-quality audit.
