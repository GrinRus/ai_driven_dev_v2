# Changelog

All notable user-visible changes to AIDD are tracked here.

This project is prerelease alpha; entries may describe release-candidate changes before a
stable compatibility window exists.

## Unreleased

- Move `main` to `0.1.0a4.dev0` after accepted `v0.1.0a3` package release
  evidence.

## 0.1.0a3 - 2026-05-22

- Prepare the `0.1.0a3` prerelease package for controlled operator trials.
- Remove Docker/GHCR from the supported alpha distribution contract.
- Add baseline OSS security and support documents.
- Add Dependabot, CodeQL, Dependency Review, and OpenSSF Scorecard workflow coverage.
- Track `uv.lock` so `uv` installs and Dependabot updates are reproducible.
- Use locked `uv` sync in CI, release, support, and source-checkout instructions.
- Prepare beta-readiness release guardrails without changing the alpha safety claim.
- Add deterministic release quality checks before package publish.
- Keep live E2E as local manual operator audit evidence only, with workflow-shape
  checks preventing live scenarios in GitHub Actions, CI/CD, and release automation.
- Harden live quality parsing and evidence accounting for review, QA, untracked
  target-repository changes, and implementation touched-file mismatches.
- Fix interview answer ownership so runtime-authored `answers.md` changes cannot
  create, rewrite, delete, or resolve operator-owned answers.
- Normalize malformed runtime-created `answers.md` content for newly asked questions
  back to canonical empty answers before interview handling resumes.

## 0.1.0a2 - 2026-05-06

- Published `ai-driven-dev-v2` to PyPI.
- Verified installation through `pipx`.
- Verified installation through `uv tool`.
- Recorded accepted release/install evidence in `docs/release-checklist.md`.
