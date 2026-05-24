# Draft Release Notes: v0.1.0a4

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a4`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a3`.

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

The `0.1.0a4` package must not be described as the latest accepted published prerelease
until the GitHub Release is published and the release workflow quality, build, PyPI publish,
`pipx`, and `uv tool` verification jobs pass. Until then, `0.1.0a3` remains the latest
accepted published prerelease evidence.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains local manual audit evidence and is not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Runtime binaries and authentication are external operator prerequisites.
- UI v1 persists only `[resolved]` answers; `[partial]` and `[deferred]` remain CLI/file-mode
  behavior.

## Release checklist

- Confirm `pyproject.toml` version is set to `0.1.0a4` before creating the release branch.
- Run deterministic local gates.
- Run `ci.yml` and `release.yml` dry-runs on `release/v0.1.0a4`.
- Publish the GitHub Release only after explicit maintainer approval.
- Confirm the release workflow quality, build, publish, `pipx`, and `uv tool` verification
  jobs pass for GitHub Release `v0.1.0a4`.
