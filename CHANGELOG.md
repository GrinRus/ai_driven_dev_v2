# Changelog

All notable user-visible changes to AIDD are tracked here.

This project is prerelease alpha; entries may describe release-candidate changes before a
stable compatibility window exists.

## Unreleased

- No unreleased changes yet.

## 0.1.0a4 - 2026-05-22

- Prepare the `0.1.0a4` prerelease package for controlled operator trials.
- Publish `0.1.0a4` to PyPI and verify `pipx` plus `uv tool` install evidence on
  2026-05-23.
- Add local operator UI async jobs for workflow and single-stage runs, with polling-based
  live runtime log chunks and persisted `runtime.log` replay.
- Align UI selected-stage execution with `aidd stage run <stage>` semantics instead of
  workflow range execution.
- Add read-only UI artifact document rendering with safe Markdown Preview/Source modes,
  including primary stage outputs such as `plan.md`.
- Clarify UI and CLI question-answer flows: UI writes `[resolved]` answers, while CLI users
  inspect `aidd stage questions`, edit `answers.md`, and rerun the selected stage.
- Keep fresh UI work items in a clean empty state before the first run.

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
