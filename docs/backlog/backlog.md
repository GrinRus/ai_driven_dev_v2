# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

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

- `2026-09-09` Prior W49 evidence remains merged; detailed history is retained in `roadmap.md`
  and the [Git archive index](reconciliation-history-index.md). The adjacent UI refactor remains
  outside this worktree and read-only. Promoted `W36-E7-S4-T6` as the next dependency-ready task
  after the isolated Claude probe showed that explicit Kimi configuration was dropped from the
  provider-private environment; T6 is now done in PR #644 at `3df6a34e`. No UI-owned paths are
  in scope.
- W50-E1-S1-T1/T2 completed in PRs #629/#631 (`71c3779a`/`6cac4a82`): freshness is typed and
  projected through reports, graders, harness metadata, operator summaries, dashboard views, and
  terminal handoffs; required lanes passed.
- W50-E1-S2-T1/T2 completed in PRs #633/#634 (`dd557a75`/`7dab7e0d`): schema-1 retention metadata
  and deterministic sanitized archive export/read/extract fail closed on missing provenance,
  tampering, or mutable `.aidd` deletion; focused/full, security, packaged-browser, and build lanes
  passed. No UI-owned paths changed; neighbor remains at `4c1356bc`.
- `W50-E2-S1-T1` completed in PR #636 at `88ac8a1d`: the candidate manifest freezes clean-worktree
  Git SHA/tree, package version, wheel digest/size, CI scenario inventory, and reproducible
  verification commands; fail-closed validation rejects drift and non-wheel artifacts. Focused
  candidate/release tests, full `make check`, Python matrix, critical coverage, adapter,
  deterministic, packaged-browser, build, and security lanes passed. No UI-owned paths changed;
  neighbor remains at `4c1356bc`.
- `W50-E2-S1-T2` completed in PR #638 at `1abd1291`: the hashed readiness contract binds all
  required Python, coverage, conformance, deterministic, packaged-browser, build, CodeQL,
  dependency-review, and Scorecard results to the exact candidate manifest identity, rejecting
  incomplete or mismatched evidence. Focused/full local checks and all required lanes passed; no
  UI-owned paths changed and neighbor remains at `4c1356bc`.
- `W50-E2-S1-T3` completed in PR #640 at `add04c05`: the exact manifest-bound wheel installs in
  an isolated environment, every CI-marked deterministic scenario runs through installed `aidd`,
  and a hashed fail-closed matrix preserves bundle paths plus stdout/stderr digests. Focused
  tests and all required CI/security/browser/build lanes passed. A review regression fixed
  manifest-relative scenario paths before merge. No UI-owned paths changed; neighbor remains at
  `4c1356bc`.
- `W50-E2-S1-T4` completed in PR #642 at `c9127799`: the exact candidate wheel is clean-installed
  and replaced through both `pipx` and `uv tool`, with installed version, doctor, and PEP 610
  wheel-hash checks captured in a canonical fail-closed report. Focused release/docs/planning
  tests (98) and all required CI/security/browser/build lanes passed; one unrelated UI-baseline
  browser HTTP-400 flake was cleared by rerun. No UI-owned paths changed; neighbor remains at
  `4c1356bc`.
- W50-E2/S1 remains complete. Provider/human acceptance continues to reuse the parked IDs after
  this isolation fix, once the required credentials and eligible participants/environments are
  available.
