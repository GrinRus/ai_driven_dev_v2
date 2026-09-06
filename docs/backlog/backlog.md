# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W48-E3-S3-T4` — Atomically seal and validate inventory, digests, sizes, and identities before
  PASS.

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

- `2026-09-07` `W48-E3-S3-T3` completed in PR #558 and is present on `origin/main` at `432ca93e`.
  Required CI lanes passed; evaluation bundles now materialize raw attempt logs/exits/events,
  stage validators, task ledgers, and finalization evidence under bundle-relative
  `canonical-evidence` with digest/size records. Focused result-bundle/eval coverage passed
  (32 tests), and the adjacent `codex/ui-completion` checkout remains untouched with its own
  unpushed UI work. `W48-E3-S3-T4` is now the promoted dependency-ready successor, while
  `W46-E2-S2-T4` and human/provider acceptance tasks stay parked.
