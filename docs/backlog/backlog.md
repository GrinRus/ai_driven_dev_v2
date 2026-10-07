# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W57-E1-S1-T2` — Pin the baseline and predeclare migration acceptance under accepted P01–P07.
- `W57-E1-S2-T1` — Add source-bound criteria and scoped product decisions.

## Soon

- `W57-E1-S2-T2` — Dereference evidence paths, IDs, and criterion coverage.
- `W57-E2-S1-T1` — Register declared check definitions and execution policy.

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

- `2026-10-06` Accepted one direct breaking migration without backward compatibility.
  W57–W59 retain 40 tasks: positioning/UX W57-E1-S1-T3 and architecture W57-E1-S1-T1
  are done; 38 implementation/measurement/acceptance tasks remain. The
  [accepted contract](../architecture/iterative-delivery-contract.md) replaces the original
  coexistence/default-switch sequence. The [decision log](../architecture/iterative-delivery-decisions.md)
  retains ADR 001–ADR 009 and P01–P07; the roadmap links parameters to their protocol,
  controller, native, human and acceptance tasks. A bounded
  [SWE-bench proposal](../analysis/swe-bench-migration-evaluation-2026-10-06.md) is research input
  to baseline W57-E1-S1-T2, not an accepted extra matrix or completed evidence.
  Next is baseline W57-E1-S1-T2 and source/decision
  W57-E1-S2-T1; their direct successors W57-E1-S2-T2 and W57-E2-S1-T1 are Soon.
  Other migration tasks remain planned in the roadmap. Existing parked observation,
  provider, and beta-readiness tasks retain their status; overlapping evidence must be
  reconciled against the same candidate/protocol before it closes another task.

Earlier completion evidence remains in the roadmap and merged Git history. The
[accepted migration plan](../analysis/iterative-delivery-migration-plan-2026-10-01.md)
retains dated design rationale and its supersession note; this queue and the roadmap own
current execution priority/status. Planning closure does not claim runtime implementation.
