# Release Notes: v0.1.0a6

Status: published on 2026-06-01.

Latest accepted published prerelease evidence: `0.1.0a6`.

## Summary

This prerelease packages the Operator Mission Control UI rollout and completed-flow
next-action behavior after the accepted `0.1.0a5` prerelease. It keeps
AIDD in prerelease alpha and preserves the manual-only live E2E release boundary.

## User-visible changes

- Added the Mission Control operator UI for completed runs, with Flow Complete handoff
  status, compact final QA metrics, Start Next Flow actions, and responsive desktop,
  tablet, and mobile layouts.
- Added Start Follow-up Flow source finding selection with primary QA report context,
  collapsed supporting evidence, selected-source summaries, and recommendation controls.
- Added archive confirmation so Archive Run requires an explicit confirmation before
  recording local navigation metadata.
- Added follow-up, clone, eval-batch, preflight, lineage, run-history, and final
  checkpoint refinements used by local UI and manual live E2E evidence.

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

## Release checklist

- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a6`.
- Release branch: `release/v0.1.0a6`.
- Release commit: `1cab7c90f3588624d842657d580e4f42483678ca`.
- Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26756539146`.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a6/`.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- Release tag `v0.1.0a6` matched `project.version` `0.1.0a6` and the remote
  `release/v0.1.0a6` branch HEAD before publishing.
