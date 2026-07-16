# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W34-E6-S1-T3` — Remove unused direct runtime dependencies and regenerate the lock.

## Soon

- `W34-E6-S1-T4` — Remove the obsolete raw repository inventory `manifest.txt`.

## Parking lot

- `W34-E3-S4-T1` — Add characterization fixtures for corrected routes, jobs, approvals,
  and dashboard states.
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

- `2026-07-16` `W34-E6-S1-T2` is complete: the unexported and unreferenced
  `interview_supported()` helper is removed while parsing, persistence, and stage
  routing remain unchanged. `T3` is promoted to `Next`; `T4` is in `Soon`.

- `2026-07-16` `W34-E6-S1-T6` is complete: Claude, Codex, and OpenCode no longer define
  dead prompt-read shims; `aidd.adapters.native_prompt` remains the sole owner.
  `W34-E6-S1-T2` is promoted to `Next`; `T3` is in `Soon`.

- `2026-07-16` `W34-E6-S1-T1` is complete: the Claude-only question detection,
  persistence, fallback routing, and resume surface is removed; registered adapters
  retain the shared `runtime_events` path. New cleanup task `W34-E6-S1-T6` is promoted
  to `Next`; `T2` remains its direct successor in `Soon`.

- `2026-07-16` `W34-E5-S4-T4`, slice `W34-E5-S4`, and Epic `W34-E5` are complete:
  atomic report writes, transcript serialization, flow-report rendering, and paired
  JSON/Markdown bundle publication are reports-owned. `W34-E6-S1-T1` is promoted to
  `Next`; `W34-E6-S1-T2` is in `Soon`.

- `2026-07-16` `W34-E5-S4-T3` is complete: typed stage-audit and finding inputs now
  produce a pure quality decision with verdict, progression, action, and reason; the
  policy module has no filesystem, subprocess, clock, or network dependencies.

- `2026-07-16` `W34-E5-S4-T2` is complete: the steps module now owns the canonical
  command result, interruption, owned process loop, process-group cleanup, and combined
  checkpoint classification; orchestration exposes compatibility bindings only.

- `2026-07-16` `W34-E5-S4-T1` is complete: durable flow-state creation, atomic
  persistence, read accessors, stale-run reconstruction, and explicit resume validation
  now live in `live_e2e_flow_state`; orchestration retains the compatibility facade.

- `2026-07-16` `W34-E5-S3` is complete: local, CI, release, contributor, and configured
  strict typing now all cover `src scripts`, with no release-script suppressions.
  `S4-T1` is promoted to `Next`; `S4-T2` is in `Soon`.
- `2026-07-16` `W34-E5-S3-T6` is complete: the resource smoke builds offline with a
  bounded command, imports directly from the extracted wheel under `UV_OFFLINE=1`, and
  performs no dependency resolution. `S3-T7` is promoted to `Next`; `S4-T1` is in
  `Soon`.
- `2026-07-16` `W34-E5-S3-T5` is complete: provider-free `node:test` fixtures execute
  real packaged modules for load ordering, stale dashboard suppression, poll invalidation
  on cancellation, and escaped error rendering. `S3-T6` is promoted to `Next`; `S3-T7`
  is in `Soon`.
- `2026-07-16` `W34-E5-S3-T4` is complete: the manifest and filesystem JavaScript
  sets must match exactly, every packaged asset passes bounded `node --check`, and CI
  runs the executable syntax gate. `S3-T5` is promoted to `Next`; `S3-T6` is in `Soon`.
- `2026-07-16` `W34-E5-S3-T3` is complete: release evidence requires canonical
  GitHub/PyPI identities, an exact canonical version line, and explicit successful command
  exit statuses; legacy payloads without status fail closed. `S3-T4` is promoted to
  `Next`; `S3-T5` is in `Soon`.
- `2026-07-16` `W34-E5-S3-T2` is complete: release preflight bounds subprocess and
  registry calls, preserves JSON output, and records timeout, DNS, TLS, transport, and
  server blockers without treating uncertainty as version absence. `S3-T3` is promoted
  to `Next`; `S3-T4` is in `Soon`.
- `2026-07-16` `W34-E5-S3-T1` is complete: taxonomy and first-boundary APIs now project
  one ranked typed candidate set and agree for text, structured, validation, exit, and
  verification signals. `S3-T2` is promoted to `Next`; `S3-T3` is in `Soon`.
- `2026-07-16` `W34-E5-S2` is complete: running-stage checkpoints re-read durable
  state after UI startup, record terminal transitions explicitly, and defer successful
  transitions to the normal post-stage checkpoint. `S3-T1` is promoted to `Next`;
  `S3-T2` is in `Soon`.
- `2026-07-16` `W34-E5-S4-T5` is complete: the fake runtime no longer delays every
  successful stage and exposes a bounded ready/release barrier only when checkpoint tests
  opt in. `S2-T3` is promoted to `Next`; classifier task `S3-T1` is in `Soon`.
- `2026-07-16` `W34-E5-S2-T2` is complete: result artifacts are copied into verified
  staging files and published with ordered SHA-256 evidence plus an atomic commit marker;
  hard links are no longer used. Independent fixture task `S4-T5` is promoted to `Next`;
  `S2-T3` is in `Soon`.
- `2026-07-16` `W34-E5-S2-T1` is complete: deterministic setup, run, verification, and
  teardown now share one monotonic lifecycle budget and launch commands in owned process
  groups with bounded descendant cleanup. `S2-T2` is promoted to `Next`; independent
  checkpoint-fixture task `S4-T5` is in `Soon`.
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
