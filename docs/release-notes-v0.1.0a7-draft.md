# Release Notes: v0.1.0a7

Status: published on 2026-06-02.

Latest accepted published prerelease: `0.1.0a7`.

## Summary

This prerelease packages UI-first onboarding, long-run operator visibility, implement diff
review, structured review/QA evidence, and remediation backflow after the accepted
`0.1.0a6` prerelease. AIDD remains prerelease alpha and keeps live E2E outside CI/CD and
release workflows.

## User-visible changes

- Added setup-mode `aidd ui` onboarding for selecting a local project root, creating or
  resuming a work item, seeding the request, inspecting runtime readiness, and choosing an
  explicit runner before execution.
- Preserved the existing CLI path: bare `aidd`, `aidd --help`, `aidd init`, `aidd run`,
  `aidd stage ...`, and `aidd ui --work-item ...` continue to use their previous command
  contracts.
- Added Active Run and Timeline UI surfaces for long-running jobs, including elapsed time,
  last output age, runner command context, silence warnings, and real milestones instead
  of synthetic progress.
- Added Implement Review with repository diff summaries, untracked-file visibility,
  implementation-report evidence parsing, source/artifact separation, and mismatch
  warnings.
- Added structured Review Findings and QA Verdict views plus remediation requests that can
  send selected review or QA issues back to `implement` with an explicit runtime id.

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
- GitHub Release, PyPI publish, `pipx`, and `uv tool` verification passed before this
  package was accepted as the latest published prerelease.

## Release checklist

- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a7`,
  target `release/v0.1.0a7`.
- Release branch: `release/v0.1.0a7`.
- Release workflow:
  `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26820675806`.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a7/`.
