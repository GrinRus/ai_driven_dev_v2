# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- None; T10 and its dependent live acceptance T4 are complete.

## Soon

- None; the next accepted work is intentionally parked pending operator/product evidence.

## Parking lot

- `W42-E7-S2-T3` — Record one genuine uncoached first-time operator observation when a participant
  and eligible environment are available; this is deferred human-usability evidence, not a pass.
- `W43-E5-S2-T3` — Run a future cross-runtime lower-capability comparison after Codex-only alpha.
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

- `2026-09-14` T10 is complete in `68f7a9fe`: QA upstream verdicts now use parsed review
  dispositions, and focused/full checks pass. T4 is complete in live run
  `eval-live-007-claude-code-20260914T112909Z` on `deepseek-flash` from an independent root;
  all stages, validator reports, Seatbelt/session integrity, and final manual quality reports
  pass. The adjacent UI refactor remains outside this worktree and read-only.
- Earlier W50 release and acceptance evidence remains recorded in roadmap/Git history; this
  bounded note tracks the completed T10 → T4 sequence and parked follow-ups.
