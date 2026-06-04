# Release Notes: v0.1.0a9

Status: draft, not tagged or published.

Current release-candidate package version: `0.1.0a9`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a8`.

`0.1.0a9` package must not be described as the latest accepted published prerelease until
GitHub Release publication, PyPI publishing, `pipx`, and `uv tool` verification all pass.

## Summary

This prerelease candidate rolls up the post-`v0.1.0a8` operator beta-hardening and release
readiness work. It keeps the alpha support stance while adding stronger real-provider UI
evidence, browser/manual operator evidence, run comparison, release tooling, and security
posture closure.

## User-visible changes

- Recorded clean UI onboarding and selected-stage `idea -> research` evidence for Codex,
  Claude Code, OpenCode, and optional Qwen through explicit runtime selection.
- Added Manual+Browser operator evidence for onboarding, runner cards, active run
  visibility, timeline, artifacts, Implement Review, Review Findings, QA Verdict,
  remediation status, stale downstream badges, and Run History comparison.
- Added a read-only run comparison surface for prompt hashes, stage statuses, artifact
  hashes, and validator outcome deltas.
- Improved release ergonomics with PATH-safe GitHub CLI guidance, non-mutating release
  preflight/evidence helpers, and candidate-specific release note criteria.
- Closed Wave 30 security posture by updating locked docs-extra transitive dependencies
  reported by Dependabot: `idna`, `pymdown-extensions`, and `urllib3`.

## Compatibility

- Existing CLI behavior remains compatible for `aidd`, `aidd --help`, `aidd doctor`,
  `aidd init`, `aidd run`, `aidd stage ...`, and `aidd ui --work-item ...`.
- `aidd ui` without `--work-item` continues to open setup/onboarding mode.
- Runtime launches still require an explicit runtime id; no hidden fallback is added.
- Runtime binaries and authentication remain external operator prerequisites.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported alpha release contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator trials.
- Live E2E evidence remains local manual audit evidence and is not CI/CD, not a release
  workflow, not GitHub Actions, and not a release gate.
- Provider smoke reproducibility depends on the operator shell environment; provider
  binaries outside the Codex app's default non-interactive PATH should be run through a
  login shell or explicit PATH prefix.
- Browser screenshots and API snapshots referenced by Wave 29 evidence are local audit
  evidence, not curated release artifacts.

## Release checklist

- GitHub Release: pending draft `v0.1.0a9`, target `release/v0.1.0a9`.
- Release branch: `release/v0.1.0a9`.
- Remote dry-runs: pending.
- PyPI: must become `https://pypi.org/project/ai-driven-dev-v2/0.1.0a9/` only after
  publication.
- Publish remains blocked until separate explicit approval.
