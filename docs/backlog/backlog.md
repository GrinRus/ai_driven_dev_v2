# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W34-E5-S2-T1` — Apply one lifecycle budget and owned process groups to setup, run,
  verify, and teardown.

## Soon

- `W34-E5-S2-T2` — Materialize result bundles by copy, hash, and atomic replace instead
  of hard links.

## Parking lot

- `W34-E3-S4-T1` — Add characterization fixtures for corrected routes, jobs, approvals,
  and dashboard states.
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

- `2026-07-16` `W34-E5-S1` is complete: the standalone deterministic lane discovers
  five CI manifests, executes all five through `aidd eval execute`, and verifies exact
  discovered/executed ID parity. `W34-E5-S2-T1` is promoted to `Next`; `S2-T2` is in
  `Soon`.
- `2026-07-16` `W34-E5-S1-T2` is complete: `aidd eval execute` now runs one
  fixture-backed deterministic scenario through preparation, execution, verification,
  teardown, and durable bundle persistence while rejecting live/provider-only inputs.
  `W34-E5-S1-T3` is promoted to `Next`.
- `2026-07-16` `W34-E5-S1-T1` is complete: every CI-labelled manifest now uses a
  provider-free fixture configuration and passes from a fresh materialized working copy.
  `W34-E5-S1-T2` is promoted to `Next`; `T3` is its direct successor in `Soon`.
- `2026-07-16` `W34-E3-S2` and `W34-E3-S3` are complete: approval decisions are
  terminal-safe and the local UI now bounds live-log memory, response size, and terminal
  job retention. `W34-E3-S4-T1` remains parked until executable frontend tests from
  `W34-E5-S3` satisfy its slice dependency.
- `2026-07-16` `W34-E4-S2-T1` is complete: adapters now publish one atomic runtime
  evidence envelope with a canonical outcome while retaining provider-specific exit
  classifications. Codex early-stop truthfulness is the next bounded slice.
- `2026-07-16` `W34-E4-S2-T2` is complete: Codex live now distinguishes protocol
  completion from supervisor termination and commits truthful timeout, cancellation,
  denial, blocked, and protocol-failure evidence.
- `2026-07-16` `W34-E4-S2-T3` is complete: pending Qwen approvals now retain a captured
  blocked result, while denied, cancelled, timeout, and success paths publish one
  consistent evidence envelope without fabricated confirmations.
- `2026-07-16` `W34-E4-S2-T4` is complete: missing, non-executable, and OS-level launch
  failures across all registered runtimes now fail before validation with a safe
  diagnostic, `exit_code: null`, and canonical launch-failure evidence.
- `2026-07-16` `W34-E4-S2` is complete: runtime capture is disk-backed, keeps bounded
  UTF-8 tails with exact counters, preserves the full combined log, and incrementally
  materializes structured events. `W34-E4-S3-T1`/`T2` are now the bounded next queue.
- `2026-07-16` `W34-E4-S3-T1` is complete: Qwen now preserves intervention mode and
  operator-request metadata in native prompts and both execution environments.
  `W34-E4-S3-T2` is promoted to `Next`; `T3` is the direct successor in `Soon`.
- `2026-07-16` `W34-E4-S3-T2` is complete: Claude capability reports now advertise
  only the registered subprocess transport, while non-full permission policies continue
  to block before launch. `W34-E4-S3-T3` is promoted to `Next`.
- `2026-07-16` `W34-E4-S3` and Epic `W34-E4` are complete: Codex live preserves
  supported model selection and rejects unsupported command options before launch.
  `W34-E5-S1-T1` is promoted to `Next`; its direct successor `T2` is in `Soon`.
