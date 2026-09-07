# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W49-E2-S1-T5` — Extract bundle/report coordination behind the facade.

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

- `2026-09-07` `W49-E3-S1-T1` completed in PR #581 and is present on `origin/main` at
  `2a80f526`. The parent-status algebra, parked-child rule, and merged-history archive
  authority passed the full required CI lanes, including packaged UI browser acceptance; the
  neighboring UI refactor remains integrated by PR #574 at `45a1a8f7` and its checkout is
  read-only reference state. `W49-E3-S1-T2` completed in PR #583 and is present on `origin/main`
  at `8c2f6bfe`; the 509 historical reconciliation bullets are indexed in [the Git archive
  index](reconciliation-history-index.md). `W49-E3-S1-T3` completed in PR #585 and is present
  on `origin/main` at `638d9aa`; its 68-test planning/docs suite validates duplicate current notes,
  recursive parent roll-ups, stale completed parents, and parked/blocked child semantics. No
  runtime or UI-owned files changed. `W49-E3-S1-T4` completed in PR #587 and is present on
  `origin/main` at `83db1f5c`; the roll-up and generic planning-integrity checks returned no
  errors, with the focused planning/docs suite passing 68 tests. No runtime or UI-owned files
  changed. `W49-E3-S2-T1` completed in PR #589 and is present on `origin/main` at `9780f1c2`;
  its architecture/analysis wording and documentation consistency guard agree on optional
  frontmatter and the current US-13 scope. The neighboring UI refactor remains read-only
  reference state. No runtime or UI-owned files changed. `W49-E3-S2-T2` completed in PR #591 and
  is present on `origin/main` at `dc0cca33`; its
  schema-versioned registry covers all 13 stories with contract, code, test, scenario, and
  evidence references, and the consistency guard verifies unique IDs plus repository-relative
  artifact existence. Local validation passed 181 focused docs/planning/quality tests; no runtime
  or UI-owned files changed. `W49-E3-S2-T3` completed in PR #593 and is present on `origin/main`
  at `ebba859d`; its deterministic generator produces the checked-in Markdown view, rejects
  missing or duplicate required references, and passed 77 focused traceability/docs/planning
  tests plus all required CI/security lanes. No runtime or UI-owned files changed. `W49-E2-S1-T1`
  completed in PR #595 and is present on `origin/main` at `0011426f`; its provider-free
  characterization compares stable live-facade artifacts, normalized flow steps, operator event
  order, and completed-stage state across two public runs. The neighboring UI refactor remains a
  read-only reference state and no UI-owned files changed. The planned T2 `_legacy_*` removal was
  audited as already present in preexisting cleanup commit `4d99b3fd`, so it is recorded as
  reconciled without a duplicate production edit. `W49-E2-S1-T3` completed in PR #597 and is
  present on `origin/main` at `25b58943`; its focused stage module owns stage classification,
  public inspection-question detection, and callback-driven stage-loop coordination. Terminal,
  blocked, quality-gate, boundary, characterization, Ruff, strict mypy, and all required CI
  lanes passed on the exact candidate. No frontend, report, runtime, or UI-owned files changed.
  `W49-E2-S1-T4` completed in PR #599 and is present on `origin/main` at `b5b3fa47`; its focused
  frontend module owns HTTP probes, target selection, semantic classification, timeout handling,
  and operator-surface checks. The 96-test harness group, deterministic probe matrix,
  characterization, Ruff, strict mypy, and all required CI/security lanes passed. No UI-owned
  files changed. The next dependency-ready task is `W49-E2-S1-T5` for bundle/report coordination;
  the neighboring UI refactor remains a read-only reference state.
