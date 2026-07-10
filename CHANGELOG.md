# Changelog

All notable user-visible changes to AIDD are tracked here.

This project is prerelease alpha; entries may describe release-candidate changes before a
stable compatibility window exists.

## Unreleased

- Open development after accepted `v0.1.0a15` package-channel evidence.

## 0.1.0a15 - 2026-07-09

- Prepare the `0.1.0a15` prerelease after accepted `v0.1.0a14` package-channel
  evidence.
- Harden the operator frontend around recovery-first decision making for rejected
  implementation review, review findings, QA not-ready handoff, and failed terminal QA.
- Add clearer follow-up flow source selection, definition blockers, preflight errors,
  launch failures, and runtime readiness refresh behavior.
- Clarify clone, eval, archive, history, and fresh-work paths so secondary navigation or
  comparison actions cannot be mistaken for QA remediation.
- Extend static UI contract coverage and record browser-verified desktop/mobile UX audit
  evidence for recovery, clone, eval, and archive states.

## 0.1.0a14 - 2026-07-03

- Prepare the `0.1.0a14` prerelease after accepted `v0.1.0a13` package-channel
  evidence.
- Reconcile Wave 30 release-readiness backlog state against accepted release evidence,
  closing obsolete `v0.1.0a9` release-prep work without republishing immutable package
  versions.
- Add the first candidate-only live product-evaluation scenario draft for Rich and record
  setup audit evidence for Pydantic, FastAPI, Rich, and Ruff candidates.
- Refresh the live E2E catalog and backlog roadmap so candidate product-evaluation work is
  explicit and remains outside the maintained scenario matrix.

## 0.1.0a13 - 2026-06-30

- Prepare the `0.1.0a13` prerelease after accepted `v0.1.0a12` package-channel
  evidence.
- Add generated read-only product-evaluation bundle summaries at live bundle
  roots, covering stage-quality audit presence, remediation source ids, repair
  counts, product file residue, final report presence, and terminal
  flow-state/verdict consistency without computing counted-clean.
- Record Wave 33 maintained-matrix evidence and the no-rerun decision for clean
  canonical lanes, keeping manual `quality-report.md` as the only counted-clean
  source.
- Refresh live E2E catalog, rubric, and skill guidance so bundle summaries are
  navigation evidence, not runner-owned quality scoring.

## 0.1.0a12 - 2026-06-22

- Prepare the `0.1.0a12` hotfix prerelease to supersede the published
  `0.1.0a11` package, where exact-PyPI live audit found a raw runtime log
  rendering crash in `aidd run logs`.
- Print persisted raw runtime logs literally in `aidd run logs` with Rich
  markup and highlighting disabled, preserving command shape, path/header
  output, latest-run resolution, tail mode, and missing/ambiguous-run behavior.
- Add CLI regression coverage for Rich-markup-like bracket text such as
  `[/, /a, /a/b, /a/b/c.py]` in saved runtime logs.
- Record the source/local-wheel `AIDD-LIVE-011` pass
  `eval-live-011-opencode-20260622T133433Z` as hotfix live evidence; exact-PyPI
  proof starts only after a fixed package version is published.

## 0.1.0a11 - 2026-06-22

- Prepare the `0.1.0a11` prerelease after accepted `v0.1.0a10` package-channel evidence.
- Convert live E2E to an execution-only runner and move deliverable quality decisions into
  a human-authored `quality-report.md`.
- Add live timeout policy evidence, target workspace evidence, and non-gating
  stage-artifact consistency findings for manual post-run review.
- Strengthen manual operator UI/UX review guidance while keeping frontend checkpoints as
  raw run-integrity evidence rather than automatic UX gates.
- Harden live prompts, contracts, scenario manifests, and runtime setup around workspace
  hygiene, shared public-surface verification, installed `aidd` self-checks, and
  verification-residue cleanup.
- Improve operator UI stage navigation and live runtime support evidence for the maintained
  Codex, Claude Code, OpenCode, and Qwen lanes.

## 0.1.0a10 - 2026-06-11

- Publish the `0.1.0a10` prerelease after accepted `v0.1.0a9` package-channel evidence.
- Add the integrated operator workbench shell and project-home surfaces while preserving
  the existing CLI and `.aidd/` artifact ownership model.
- Fix stage input preflight behavior so missing prerequisites are surfaced before runtime
  execution instead of leaking into later stage attempts.
- Tighten live E2E artifact, content, review, QA, and touched-file quality gates, including
  Claude large coverage and stronger repair signals for incomplete target-project code.
- Neutralize live prompt examples so maintained live E2E scenarios do not leak
  target-specific solutions into reusable AIDD prompts.

## 0.1.0a9 - 2026-06-04

- Open the next development cycle after accepted `v0.1.0a8` release evidence.
- Reconcile UI-first onboarding roadmap state with the shipped `v0.1.0a7`/`v0.1.0a8`
  operator path and add post-a8 audit evidence for clean UI onboarding.
- Document PATH-safe GitHub CLI release operations for maintainer shells where `gh` is
  installed outside the default `PATH`.
- Open Wave 30 release-readiness work for `v0.1.0a9`, including Dependabot alert
  triage, patched locked docs dependencies, and a fresh source UI smoke before any
  release candidate branch is prepared.

## 0.1.0a8 - 2026-06-04

- Publish the `0.1.0a8` prerelease after clean UI audit hotfixes landed on `main`.
- Fix onboarding form state so `Create work item` enables immediately after work item id
  and request text entry, including the runner-first selection path.
- Add a visible `Run selected stage` command center action for bounded operator smoke
  flows while keeping `Run workflow` as the primary full-flow action.
- Keep release-readiness docs explicit about `0.1.0a8` as the latest accepted published
  prerelease evidence.

## 0.1.0a7 - 2026-06-02

- Publish the `0.1.0a7` prerelease after the UI-first onboarding and
  operator control center work landed on `main`.
- Add setup-mode `aidd ui` onboarding for project-root selection, work item
  create/resume, runtime readiness, and mandatory explicit runner selection while
  preserving existing CLI behavior.
- Add long-run visibility in the operator UI with an Active Run panel, timeline
  milestones, silence warnings, and live log access.
- Add implement diff review, structured review/QA evidence views, and remediation
  backflow from review or QA findings to a new explicit implement attempt.
- Keep release-readiness docs explicit about `0.1.0a7` as the latest accepted published
  prerelease evidence.

## 0.1.0a6 - 2026-06-01

- Release the `0.1.0a6` prerelease after the Operator Mission Control UI redesign and
  completed-flow next-action rollout landed on `main`.
- Add completed-run Flow Complete handoff, Start Next Flow source-finding selection,
  archive confirmation, follow-up/clone/eval handoffs, and lineage-aware run history.
- Add release-safe local UI evidence for the Mission Control references, including
  desktop, tablet, and mobile browser smoke coverage without moving live E2E into CI/CD.
- Refresh manual-live next-flow checkpoint behavior and experimental Codex/Qwen evidence
  handling while keeping provider runs outside release automation.

## 0.1.0a5 - 2026-05-25

- Prepare the `0.1.0a5` prerelease candidate after `0.1.0a4` was already published.
- Clarify strict interview repair prompts so runtime repair attempts avoid colon-style
  answer bullets such as `- Q1 [resolved]: ...`.
- Refresh W24 manual live readiness evidence for the maintained beta scenario/runtime
  matrix while keeping live E2E outside CI/CD and release workflows.
- Keep release-readiness docs explicit about `0.1.0a5` as the current candidate during
  release preparation and `0.1.0a4` as the then-latest accepted published prerelease
  evidence.

## 0.1.0a4 - 2026-05-23

- Prepare the `0.1.0a4` prerelease package for controlled operator trials.
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
