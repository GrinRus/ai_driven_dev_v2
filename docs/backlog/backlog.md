# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W49-E1-S2-T4` — Drive built-in registration/config compatibility from descriptors.

## Soon

- `W49-E1-S2-T5` — Prove clean extension with an allowlisted fake external descriptor.

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

- `2026-09-07` `W49-E1-S2-T3` completed in PR #570 and is present on `origin/main` at `82b7bdb1`.
  Runtime policy now consumes adapter-composed protected/credential/config markers; built-in
  provider roots and credential filenames are absent from `aidd.core`. Core and adapter suites
  passed (1405 tests), Ruff, strict mypy, and all required CI lanes passed. The adjacent
  `codex/ui-completion` checkout remains untouched with its completed-but-unpushed UI work;
  UI-bound `W49-E1-S1-T4` remains blocked until that branch is merged. `W49-E1-S2-T4` is now
  the next non-UI dependency-ready task, with T5 promoted to Soon.
