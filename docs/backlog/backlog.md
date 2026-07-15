# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W34-E7-S2-T4` — Adopt identifier containment for run and attempt paths after the
  workspace/work-item rollout.

## Soon


## Parking lot

- `W34-E1-S3-T1` — Define the canonical versioned validator field/code registry.
- `W34-E1-S4-T1` — Reuse the canonical section-aware interview parser in
  cross-validation.
- `W34-E1-S5-T1` — Add one production-equivalent full-stack contract fixture runner.
- `W34-E2-S3-T1` — Move archive decisions to a separate append-only operator
  overlay/index.
- `W34-E3-S2-T1` — Resolve each approval exactly once with compare-and-set semantics.
- `W34-E3-S3-T1` — Store live chunks in a byte-bounded ring, cap responses, and evict
  terminal jobs by TTL/count.
- `W34-E3-S4-T1` — Add characterization fixtures for corrected routes, jobs, approvals,
  and dashboard states.
- `W34-E4-S2-T1` — Define typed stop reasons and one runtime-evidence commit contract.
- `W34-E4-S3-T1` — Propagate Qwen intervention mode and operator-request metadata.
- `W34-E5-S1-T1` — Repair stale CI-labelled smoke manifests and fixtures.
- `W34-E5-S2-T1` — Apply one lifecycle budget and owned process groups to setup, run,
  verify, and teardown.
- `W34-E5-S3-T1` — Replace divergent eval classifiers with one typed earliest-failure
  classifier.
- `W34-E5-S4-T1` — Extract durable flow-state and resume coordination from live
  orchestration.
- `W34-E6-S1-T1` — Remove superseded Claude question/resume code after a public-import
  compatibility review.
- `W34-E6-S2-T1` — Close dependency-update proposals that target packages removed by
  the cleanup slice.
- `W34-E7-S3-T1` — Reject ambiguous, unknown, or malformed safety-sensitive
  configuration.
- `W34-E8-S1-T2` — Normalize inherited local-task statuses and historical disposition
  semantics.
- `W34-E8-S2-T1` — Replace stale planned/completed-wave architecture wording with
  stable implemented ownership boundaries.
- `W35-E2-S9-T1` — Extract task attempt, recovery, and interview-evidence lifecycle from
  the task-execution hotspot.
- `W35-E2-S10-T1` — Reuse one immutable repository snapshot per task checkpoint.
- `W36-E1-S1-T3` — Replace checklist-only navigation wording with the canonical
  Guided Setup / Inbox / Studio / History state-route matrix.
- `W36-E2-S1-T1` — Select and document a maintained provider-free browser driver and
  packaged-UI test policy.
- `W36-E2-S3-T1` — Extract shared dashboard loading, context selection, and mutation
  dispatch from legacy renderer ownership.
- `W36-E3-S1-T1` — Add semantic typography, spacing, radius, elevation, control-size,
  state, focus, and motion tokens.
- `W36-E4-S1-T1` — Add the Project -> Work item -> Runtime -> Review/Launch onboarding
  state machine.
- `W36-E5-S1-T1` — Hide a zero-value Evidence Inspector and keep Filmstrip/log evidence
  collapsed until requested.
- `W36-E5-S2-T1` — Replace the measured `275px` mobile header with a compact
  context/status bar and maintenance overflow.
- `W36-E5-S3-T1` — Implement the typed project-local Inbox projection and deterministic
  priority sections.
- `W36-E5-S4-T1` — Compose the active Studio view from shared mode navigation, compact
  context bar, stage navigation, and Decision Bar slots.
- `W36-E5-S5-T1` — Render blocking questions with durable resolution and draft-recovery
  semantics in Recovery Studio.
- `W36-E5-S6-T1` — Render typed runtime failure and the eligible recovery action without
  conflating validation repair.
- `W36-E5-S7-T1` — Render canonical implement tasks, attempts, recovery, and aggregate
  finalization inside Studio.
- `W36-E5-S8-T1` — Implement the typed Filmstrip frame projection from durable attempts,
  task attempts, and finalization milestones.
- `W36-E5-S0-T1` — Add one core-owned recommended outcome and rationale to the terminal
  handoff read model.
- `W36-E5-S10-T1` — Switch the default renderer to Studio only after all per-surface
  parity entries close.
- `W36-E6-S1-T1` — Add a URL-state codec for Inbox / Studio / History, work item, run,
  stage, attempt/task-attempt detail, and artifact selection.
- `W36-E6-S2-T1` — Define the scoped browser-session draft key, retention, and cleanup
  contract.
- `W36-E6-S3-T1` — Replace terminal-on-error polling with cursor-preserving retry and
  bounded backoff.
- `W36-E6-S4-T1` — Add a keyed client mutation guard with pending lock, duplicate
  suppression, conflict readback, and retryable failure state.
- `W36-E7-S1-T1` — Add the Guided Setup project validation, create/resume, runtime
  review, first-launch, and resulting Inbox browser journey.

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
  queue-restoration policy in `docs/backlog/roadmap.md` (`W8-E3-S1`).

## Current reconciliation

- `2026-07-15` The seven foundation tasks selected from `Next` are complete. Their five
  direct successors now form the bounded `Next` queue in dependency order; `Soon` is
  intentionally empty, and the Wave 36 UI work remains in `Parking lot` behind the
  Wave 34/35 and browser-foundation gates.
