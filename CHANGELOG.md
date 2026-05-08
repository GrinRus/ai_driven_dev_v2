# Changelog

All notable user-visible changes to AIDD are tracked here.

This project is prerelease alpha; entries may describe release-candidate changes before a
stable compatibility window exists.

## Unreleased

- Move `main` to `0.1.0a3.dev0` after the published `0.1.0a2` prerelease.
- Remove Docker/GHCR from the supported alpha distribution contract.
- Add baseline OSS security and support documents.
- Add Dependabot, CodeQL, Dependency Review, and OpenSSF Scorecard workflow coverage.
- Track `uv.lock` so `uv` installs and Dependabot updates are reproducible.
- Use locked `uv` sync in CI, release, support, and source-checkout instructions.

## 0.1.0a2 - 2026-05-06

- Published `ai-driven-dev-v2` to PyPI.
- Verified installation through `pipx`.
- Verified installation through `uv tool`.
- Recorded accepted release/install evidence in `docs/release-checklist.md`.
