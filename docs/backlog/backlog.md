# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W49-E2-S2-T1` — Extract UI job registry/lifecycle from `cli/ui.py`.

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

- `2026-09-08` Planning truth and traceability work W49-E3-S1/T1–T4 and W49-E3-S2/T1–T3 remain
  merged on `origin/main`; their detailed evidence is retained in `roadmap.md` and the [Git
  archive index](reconciliation-history-index.md). The neighboring UI refactor is integrated by
  PR #574 at `45a1a8f7`; its checkout remains read-only reference state.
  `W49-E2-S1-T1` completed in PR #595 at `0011426f`, and the planned T2 `_legacy_*` removal was
  reconciled to preexisting cleanup commit `4d99b3fd` without a duplicate production edit.
  `W49-E2-S1-T3` completed in PR #597 at `25b58943`, and T4 in PR #599 at `b5b3fa47`; their
  focused stage and frontend modules preserve the characterized facade and all required
  CI/security lanes passed. `W49-E2-S1-T5` completed in PR #601 at `71659ca0`; its focused bundle
  coordinator owns canonical result materialization/sealing and run-transcript projection while
  success, blocked, awaiting-quality-review, and manual-stop schemas remain unchanged. The 99-test
  harness group, focused bundle tests, characterization, Ruff, strict mypy, and all required
  CI/security lanes passed. No frontend, runtime, or UI-owned files changed. The next
  dependency-ready task is `W49-E2-S2-T1` for server-side UI job lifecycle extraction.
