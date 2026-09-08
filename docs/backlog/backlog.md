# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W49-E2-S3-T2` — Decompose `build_task_flow_checkpoint`.

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
  CI/security lanes passed. No frontend, runtime, or UI-owned files changed. `W49-E2-S2-T1`
  completed in PR #603 and is present on `origin/main` at `058331b3`; the UI job registry/lifecycle
  now has one canonical server-side owner, with two-project lifecycle isolation and the full 341
  test CLI suite green. No static UI, frontend tests, or neighboring UI checkout files changed.
  `W49-E2-S2-T2` completed in PR #605 and is present on `origin/main` at `0c5af159`; existing
  `ui_http` codecs and `ui_routing` dispatch are composed by `aidd.cli.ui_transport`, with success,
  validation, not-found, explicit-failure, and two-project endpoint contracts covered. Focused and
  full CLI suites (10 and 345 tests), planning/traceability/CI tests (52), Ruff, strict mypy, and
  required CI/security lanes passed after one transient packaged-browser rerun. No static UI,
  frontend tests, or neighboring UI checkout files changed. The next dependency-ready task is
  `W49-E2-S2-T3` for ordered dashboard next-action rules. `W49-E2-S2-T3` completed in PR #606
  and is present on `origin/main` at `2e4c42b3`; typed priority rules and the dashboard state
  matrix preserve the `OperatorNextAction` contract, with 1106 core tests, Ruff, strict mypy,
  and required CI/security lanes green after two transient packaged-browser reruns. No static UI,
  frontend tests, or neighboring UI checkout files changed. The next dependency-ready task is
  `W49-E2-S3-T1` for the complexity baseline and no-new-E/F ratchet. `W49-E2-S3-T1` completed in
  PR #608 and is present on `origin/main` at `cb37d4eb`; the Radon baseline and CI ratchet cover
  new E/F blocks, complexity increases, malformed baseline data, and stale entries. The full
  3212-test Python suite, 141 Node DOM tests, Ruff, strict mypy, deterministic/conformance/
  browser/build lanes, and security checks passed. No runtime or UI-owned files changed. The
  next dependency-ready task is `W49-E2-S3-T2` for `build_task_flow_checkpoint` decomposition.
