# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W50-E1-S1-T2` — Project freshness consistently into reports and the operator read model.

## Soon

## Parking lot

- `W42-E7-S2-T3` — Record one genuine uncoached first-time operator observation when a participant
  and eligible environment are available; this is deferred human-usability evidence, not a pass.
- `W43-E5-S2-T3` — Run a future cross-runtime lower-capability comparison after Codex-only alpha.
- `W36-E7-S4-T4` — Claude acceptance is not launched under the current Codex-only scope.
- `W36-E7-S3-T2` — Record five first-time-operator sessions after initial live hardening.
- `W36-E7-S3-T3` — Reconcile observed session findings before beta readiness.
- `W36-E7-S4-T5` — Record final same-revision Codex and Claude acceptance evidence.
- `W46-E2-S2-T4`

## Update rules

- Keep `roadmap.md` as the canonical plan and `backlog.md` as the short queue.
- Only local task IDs belong in the queue sections.
- If a task is too large, split it in `roadmap.md` before coding.
- Add new work to `roadmap.md` first, then promote it here only if it becomes immediate.
- `Soon` is reserved for direct successors of tasks currently in `Next`; consciously
  deferred ready work belongs in `Parking lot`.
- Remove completed tasks rather than leaving stale queue entries behind.
- Keep one bounded current reconciliation note; Git and roadmap evidence retain history.
- If roadmap is fully `done` and this queue is empty, reopen work using the
  queue-restoration policy in `docs/backlog/roadmap.md` (`Completed work and queue restoration`).

## Current reconciliation

- `2026-09-08` W49-E3-S1/T1–T4 and W49-E3-S2/T1–T3 remain merged on `origin/main`; detailed
  evidence is retained in `roadmap.md` and the [Git archive index](reconciliation-history-index.md).
  The neighboring UI refactor is integrated by PR #574 at `45a1a8f7`; its checkout remains
  read-only. W49-E2-S1/T1–T5 are merged in PRs #595/#597/#599/#601, W49-E2-S2/T1–T3 in
  #603/#605/#606, and W49-E2-S3-T1 in #608; all preserve the no-UI boundary and required checks.
  W49-E2-S3-T2 completed in PR #610 at `cfcfe33c` (checkpoint fixtures and 479-test harness green).
  W49-E2-S3-T3 completed in PR #612 at `91b088d9` (50-test invalid-manifest matrix and 479-test
  harness green). T4 completed in PR #613 at `d9d17bfa` (1106 core tests and required lanes green);
  T5 completed in PR #615 at `037a35ef` (25 Codex live and 318 adapter tests plus required lanes
  green); T6 completed in PR #617 at `18a71f2e` (18 focused Qwen live tests, 318 adapter tests,
  complexity ratchet, and all required lanes green). T1 of W49-E4-S1 completed in PR #619 at
  `d8b0f379`: 268 tracked Python files were formatted in the reviewed non-UI scope,
  `browser_tests` remained excluded for the neighboring UI boundary, AST equivalence and focused
  checks passed, and required CI/security/browser/build lanes were green. T2 completed in PR #622
  at `765f051a`: CI now enforces `ruff format --check .` in the lint/type/test matrix, with 74
  focused planning/docs/CI tests and all required CI/security/browser/build lanes green. W49-E4-S2-T1
  completed in PR #624 at `a144fbae`: the reviewed baseline covers 23 lifecycle/evidence/adapter/
  scenario-gate modules with exact line/branch counts, source SHA `951e3f8c`, tool versions, and
  a reproducible 369-test command; checker tests and all required CI/security/browser/build lanes
  passed. All remain outside runtime/UI-owned paths; the neighboring UI checkout is read-only.
  W49-E4-S2-T2 completed in PR #626 at `63fa1d7e`: the Linux-native 23-module line/branch
  baseline is enforced by one required CI job, with an explicit Python 3.13.7 interpreter pin and
  a checker regression fixture; all Python, adapter, deterministic, packaged-browser, build, and
  security lanes passed after correcting the OS-specific process-group metric. W49-E4-S3-T1
  completed in PR #627 at `c165eb5d`: pinned CodeQL now analyzes both Python and packaged
  JavaScript/TypeScript, and the complete CI/security/browser/build set passed. W50-E1-S1-T1
  completed in PR #629 at `71c3779a`: the core freshness contract distinguishes current, stale,
  incompatible, and unavailable evidence from candidate SHA, schema, target pin, and locator;
  focused tests and all required CI/security/browser/build lanes passed. The adjacent UI checkout
  remains read-only at `4c1356bc`; queue promotion now selects `W50-E1-S1-T2`.
