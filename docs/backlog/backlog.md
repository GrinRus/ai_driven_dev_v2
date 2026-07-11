# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic, slice, and local task.

## Next

- `W34-E1-S1-T1` — Add canonical `stage-result.md` semantic rules and a final
  post-normalization publication invariant.

## Soon

- `W34-E1-S2-T1` — Add a typed evidence context and bind implementation output to
  selected task, changed paths, allowed scope, and authored checks.
- `W34-E2-S1-T1` — Publish stage outputs through staged-directory verification and
  atomic replace.
- `W34-E3-S1-T1` — Add a filesystem-backed run-mutation lease and atomic run/attempt
  allocation.
- `W34-E4-S1-T1` — Add provider-free adapter lifecycle characterization fixtures.
- `W34-E7-S1-T1` — Define typed capability rules for runtime operator requests.
- `W34-E7-S2-T1` — Add shared typed identifier validation and resolve-and-contain
  primitives.
- `W35-E1-S1-T1` — Define the accepted operator state hierarchy, progressive
  disclosure, and one-primary-action contract.

## Parking lot

- `W34-E1-S3-T1` — Create a canonical validator field/code registry and synchronize
  renderer, contract, repair prompts, and dual-read consumers.
- `W34-E1-S4-T1` — Reuse the canonical section-aware interview parser in
  cross-validation.
- `W34-E1-S5-T1` — Add one production-equivalent full-stack contract fixture runner.
- `W34-E2-S2-T1` — Validate immutable runtime, target, and configuration fields when
  an existing run manifest is reused.
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
- `W34-E7-S3-T1` — Reject ambiguous, unknown, or malformed safety-sensitive
  configuration.
- `W35-E2-S1-T1` — Select and document a maintained provider-free browser driver and
  packaged-UI test policy.
- `W35-E3-S1-T1` — Add semantic typography, spacing, radius, elevation, control-size,
  state, focus, and motion tokens.
- `W35-E4-S1-T1` — Add the Project -> Work item -> Runtime -> Review/Launch onboarding
  state machine.
- `W35-E5-S1-T1` — Add a visibility policy for zero-value sidebar and bottom-dock
  sections.
- `W35-E5-S2-T1` — Replace the measured `275px` mobile header with a compact
  context/status bar and maintenance overflow.
- `W35-E6-S1-T1` — Add a URL-state codec for work item, run, stage, mode, detail, and
  artifact selection.
- `W35-E6-S2-T1` — Define and implement a scoped noncanonical browser-session draft
  store.
- `W35-E6-S3-T1` — Replace terminal-on-error polling with cursor-preserving retry and
  bounded backoff.
- `W35-E6-S4-T1` — Add a keyed client mutation guard with pending lock, duplicate
  suppression, conflict readback, and retryable failure state.
- `W35-E7-S1-T1` — Add the project validation, create/resume, runtime review, and
  first-launch browser journey.

## Update rules

- Keep `roadmap.md` as the canonical plan and `backlog.md` as the short queue.
- Only local task ids belong in this file.
- If a task is too large, split it in `roadmap.md` before coding.
- Add new work to `roadmap.md` first, then promote it here only if it becomes immediate.
- Remove completed tasks rather than leaving stale queue entries behind.
- If roadmap is fully `done` and this queue is empty, reopen work using the queue-restoration policy in `docs/backlog/roadmap.md` (`W8-E3-S1`).

## Queue sync notes

- `2026-07-11` Wave 35 was added from the operator UX/UI audit while Wave 34 remains
  active. `W34-E1-S1-T1` remains the sole `Next`; the accepted UX-contract task
  `W35-E1-S1-T1` was appended to `Soon`. Entry tasks `W35-E2-S1-T1`,
  `W35-E3-S1-T1`, `W35-E4-S1-T1`, `W35-E5-S1-T1`, `W35-E5-S2-T1`,
  `W35-E6-S1-T1`, `W35-E6-S2-T1`, `W35-E6-S3-T1`, `W35-E6-S4-T1`, and
  `W35-E7-S1-T1` were appended to `Parking lot`; their dependent tasks remain in the
  canonical roadmap. Server-side mutation, approval, retention, runtime-evidence,
  run-identity, archive, DOM-test, and next-flow-split foundations remain Wave 34
  responsibilities and are not duplicated.
- `2026-07-10` Wave 34 opened from
  `docs/analysis/codebase-audit-2026-07-10.md`. `W34-E1-S1-T1` is promoted to
  `Next`; cross-document evidence, atomic publication, local mutation serialization,
  provider-free adapter characterization, runtime policy, and identifier containment
  foundations are in `Soon`. One entry task for each dependent slice is visible in
  `Parking lot`; remaining dependent local tasks stay in the canonical roadmap until
  their predecessor is complete. Frontend session/origin hardening is intentionally not
  queued while `aidd ui` remains a private, single-operator local frontend.
- `2026-06-22` Wave 32 was opened for the `AIDD-LIVE-011` exact-PyPI raw-log
  rendering defect. `W32-E1-S1-T1` is promoted to `Next`; the task is scoped to
  CLI log rendering plus focused regression coverage and a source-checkout live rerun.
- `2026-06-22` Completed `W32-E1-S1-T1`; `aidd run logs` now prints persisted raw
  runtime logs literally, focused CLI checks passed, and source/local-wheel
  `AIDD-LIVE-011` rerun `eval-live-011-opencode-20260622T133433Z` passed through
  terminal QA. Exact PyPI proof remains a release follow-up because `0.1.0a11` is
  immutable.
- `2026-06-29` Wave 33 opened for live E2E product-evaluation follow-up after PR #93
  proved the stage-run/remediation protocol on fresh `AIDD-LIVE-008` and
  `AIDD-LIVE-011` runs. `W33-E1-S1-T1` is promoted to `Next`,
  `W33-E1-S1-T2` to `Soon`, and bundle-summary plus new-repository expansion tasks stay
  parked until the maintained matrix evidence table exists.
- `2026-06-30` Completed `W33-E1-S1-T1`: local report
  `.aidd/reports/evals/maintained-matrix-20260630.md` shows all six canonical
  maintained lanes are counted-clean with terminal `pass`, final reports, complete
  stage-quality audits, and no unresolved unexpected product residue.
- `2026-06-30` Completed `W33-E1-S1-T2` as `no rerun needed`; no canonical maintained
  lane is missing or stale, so no new live run was launched.
- `2026-06-30` Completed `W33-E2-S1-T1` and `W33-E2-S1-T2`; terminal
  product-evaluation bundles now include read-only `product-evaluation-bundle-summary.*`
  navigation artifacts, and docs/skill guidance keep final counted-clean decisions in
  manual `quality-report.md`. `W33-E3-S1-T1` is promoted to `Next` and
  `W33-E3-S1-T2` to `Soon`.
- `2026-07-02` Completed `W33-E3-S1-T1` and `W33-E3-S1-T2`; setup audits for
  Pydantic, FastAPI, Rich, and Ruff are recorded in
  `docs/e2e/live-e2e-candidate-setup-audits.md`, and `AIDD-LIVE-013` is drafted
  as a Rich candidate-only product-evaluation manifest. No unblocked Wave 33
  local tasks remain queued.
- `2026-07-02` Closed `W30-E3-S1-T1` by reconciliation: accepted `v0.1.0a9`
  release/install evidence already exists, origin has tag `v0.1.0a9`, and latest accepted
  package evidence is `0.1.0a13`, so no `v0.1.0a9` release-prep action remains valid. The
  active backlog queue is empty.
- `2026-04-23` Backlog queue was restored after readiness cleanup and synchronized with Wave 7/Wave 8 roadmap tasks.
- `2026-04-23` Queue-restoration policy was documented under `W8-E3-S1` to govern future wave opening when backlog is empty.
- `2026-04-23` Wave 9 queue bootstrap promoted `W9-E1-S1-T1` to `Next`, `W9-E1-S1-T2` and `W9-E1-S1-T3` to `Soon`, and `W9-E1-S1-T4` to `Parking lot`.
- `2026-04-23` After completing `W9-E1-S1-T1`, backlog queue advanced with `W9-E1-S1-T2` promoted to `Next`.
- `2026-04-23` After completing `W9-E1-S1-T2`, backlog queue advanced with `W9-E1-S1-T3` promoted to `Next`.
- `2026-04-23` After completing `W9-E1-S1-T3`, backlog queue advanced with `W9-E1-S1-T4` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W9-E1-S1-T4`, Wave 9 queue is empty; open a new wave via `W8-E3-S1` queue-restoration policy before further implementation.
- `2026-04-23` Wave 10 was opened via `W8-E3-S1` queue-restoration policy; promoted `W10-E0-S1-T1` to `Next`, `W10-E0-S1-T2`, `W10-E1-S1-T1`, and `W10-E1-S1-T2` to `Soon`, and `W10-E1-S1-T3`, `W10-E1-S1-T4`, `W10-E2-S1-T1`, `W10-E2-S1-T2`, and `W10-E3-S1-T1` to `Parking lot`.
- `2026-04-23` After completing `W10-E0-S1-T1`, backlog queue advanced with `W10-E0-S1-T2` promoted to `Next`.
- `2026-04-23` After completing `W10-E0-S1-T2`, backlog queue advanced with `W10-E1-S1-T1` promoted to `Next`.
- `2026-04-23` After completing `W10-E1-S1-T1`, backlog queue advanced with `W10-E1-S1-T2` promoted to `Next`.
- `2026-04-23` After completing `W10-E1-S1-T2`, backlog queue advanced with `W10-E1-S1-T3` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W10-E1-S1-T3`, backlog queue advanced with `W10-E1-S1-T4` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W10-E1-S1-T4`, backlog queue advanced with `W10-E2-S1-T1` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W10-E2-S1-T1`, backlog queue advanced with `W10-E2-S1-T2` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W10-E2-S1-T2`, backlog queue advanced with `W10-E3-S1-T1` promoted from `Parking lot` to `Next`.
- `2026-04-23` After completing `W10-E3-S1-T1`, Wave 10 queue is empty; reopen work via `W8-E3-S1` queue-restoration policy when the next wave is defined.
- `2026-04-23` Wave 11 was opened via `W8-E3-S1` queue-restoration policy; promoted `W11-E1-S1-T1` to `Next`, `W11-E1-S1-T2` and `W11-E1-S2-T1` to `Soon`, and `W11-E1-S2-T2`, `W11-E1-S2-T3`, `W11-E1-S3-T1`, `W11-E1-S3-T2`, `W11-E1-S3-T3`, `W11-E1-S3-T4`, `W11-E2-S1-T1`, and `W11-E2-S1-T2` to `Parking lot`.
- `2026-04-23` After completing `W11-E1-S1-T1`, `W11-E1-S1-T2`, `W11-E1-S2-T1`, `W11-E1-S2-T2`, `W11-E1-S2-T3`, `W11-E1-S3-T1`, `W11-E1-S3-T2`, `W11-E1-S3-T3`, and `W11-E1-S3-T4`, backlog queue advanced with `W11-E2-S1-T1` promoted to `Next` and `W11-E2-S1-T2` promoted to `Soon`.
- `2026-04-23` After completing `W11-E2-S1-T1` and `W11-E2-S1-T2`, Wave 11 queue is empty; reopen work via `W8-E3-S1` queue-restoration policy when the next wave is defined.
- `2026-04-24` Wave 12 was opened via `W8-E3-S1` queue-restoration policy; promoted `W12-E1-S1-T1` to `Next`, `W12-E1-S1-T2` and `W12-E1-S2-T1` to `Soon`, and `W12-E1-S2-T2`, `W12-E1-S3-T1`, `W12-E1-S3-T2`, `W12-E2-S1-T1`, `W12-E2-S1-T2`, `W12-E2-S2-T1`, and `W12-E2-S2-T2` to `Parking lot`.
- `2026-04-24` After completing Wave 12, backlog queue is empty again; reopen work via `W8-E3-S1` queue-restoration policy before the next implementation wave.
- `2026-04-24` Wave 13 was opened via `W8-E3-S1` queue-restoration policy; promoted `W13-E1-S1-T1` to `Next`, `W13-E1-S1-T2` and `W13-E1-S2-T1` to `Soon`, and `W13-E1-S2-T2`, `W13-E2-S1-T1`, `W13-E2-S1-T2`, `W13-E2-S2-T1`, `W13-E2-S2-T2`, `W13-E3-S1-T1`, `W13-E3-S1-T2`, `W13-E3-S2-T1`, and `W13-E3-S2-T2` to `Parking lot`.
- `2026-04-24` After completing Wave 13, backlog queue is empty again; reopen work via `W8-E3-S1` queue-restoration policy before the next implementation wave.
- `2026-04-24` Wave 14 was opened via `W8-E3-S1` queue-restoration policy; promoted `W14-E1-S1-T1` to `Next`, `W14-E1-S1-T2` to `Soon`, and `W14-E1-S2-T1` to `Parking lot`.
- `2026-04-24` After completing Wave 14, backlog queue is empty again; reopen work via `W8-E3-S1` queue-restoration policy before the next implementation wave.
- `2026-04-25` Wave 15 was opened via `W8-E3-S1` queue-restoration policy after the readiness audit found an all-done roadmap and empty queue; completed `W15-E0-S1-T1`, promoted `W15-E1-S1-T1` to `Next`, `W15-E2-S1-T1` to `Soon`, and `W15-E3-S1-T1` plus `W15-E3-S2-T1` to `Parking lot`.
- `2026-04-25` After completing `W15-E1-S1-T1`, backlog queue advanced with `W15-E2-S1-T1` promoted to `Next`; `W15-E3-S1-T1` and `W15-E3-S2-T1` remain in `Parking lot`.
- `2026-04-25` After completing `W15-E2-S1-T1`, backlog queue advanced with `W15-E3-S1-T1` promoted from `Parking lot` to `Next`; `W15-E3-S2-T1` remains in `Parking lot`.
- `2026-04-25` `W15-E3-S1-T1` is blocked because local preflight found no configured AIDD-compatible live runtime wrapper env var; backlog advanced with `W15-E3-S2-T1` promoted to `Next`.
- `2026-04-25` `W15-E3-S2-T1` is blocked because local preflight found no release candidate tag or local publishing credentials; active backlog queue is empty.
- `2026-05-03` Wave 16 complexity-reduction work completed shared Markdown parsing, semantic facade/plumbing extraction, stage-specific semantic rule modules, adapter probe/streaming/path-resolution dedupe, adapter surface registry, CLI command module split, runtime config map, eval phase/render extraction, and documented compatibility shim retention; backlog queue is empty again.
- `2026-05-03` Wave 17 opened as a second complexity-reduction pass; promoted `W17-E0-S1-T1` to `Next`, `W17-E1-S1-T1` and `W17-E2-S1-T1` to `Soon`, and the remaining Wave 17 local tasks to `Parking lot`.
- `2026-05-03` Wave 17 completed; backlog queue is empty again and the next implementation wave should be opened via the queue-restoration policy before further changes.
- `2026-05-03` Wave 17 corrective audit closed the remaining decomposition gaps in roadmap tasks `W17-E1-S3-T1`, `W17-E2-S2-T1`, `W17-E3-S2-T1`, and `W17-E4-S3-T1`; backlog queue remains empty.
- `2026-05-04` Wave 18 was opened via `W8-E3-S1` queue-restoration policy for architecture/documentation conformance closure; promoted `W18-E1-S1-T1` to `Next`, `W18-E1-S1-T2` and `W18-E2-S1-T1` to `Soon`, and `W18-E2-S1-T2` plus `W18-E3-S1-T1` to `Parking lot`.
- `2026-05-04` Wave 18 completed; architecture/current-state docs, artifact ownership wording, archival snapshot markers, and docs consistency regressions are in place, and the backlog queue is empty again.
- `2026-05-04` Wave 19 was opened via `W8-E3-S1` queue-restoration policy for user-story implementation closure; promoted `W19-E1-S1-T1` to `Next`, `W19-E1-S1-T2`, `W19-E1-S1-T3`, `W19-E2-S1-T1`, and `W19-E3-S1-T1` to `Soon`, and parked compatibility/live evidence tasks until the event, repair, and eval closures landed.
- `2026-05-04` Wave 19 completed; native structured question/event routing, optional JSONL attempt and eval artifacts, repair-history finalization, and Python 3.12-3.14 CI alignment are in place, and the backlog queue is empty again.
- `2026-05-04` Wave 20 was opened via `W8-E3-S1` queue-restoration policy for gap intake and product-scope expansion; promoted `W20-E1-S1-T1` to `Next`, `W20-E1-S1-T2`, `W20-E1-S2-T1`, `W20-E2-S1-T1`, and `W20-E3-S1-T1` to `Soon`, and parked release evidence capture plus frontend/project-set implementation tasks.
- `2026-05-04` W20 evidence-and-contract pass completed `W20-E1-S1-T1`, `W20-E1-S1-T2`, `W20-E1-S2-T1`, `W20-E2-S1-T1`, and `W20-E3-S1-T1`; `W20-E1-S2-T2` remains parked as blocked by missing release candidate tag and publishing credentials, and frontend/project-set implementation tasks remain parked for explicit promotion.
- `2026-05-04` W20 foundation pass completed live failure triage plus the OpenCode native command regression, frontend read/write service foundation, and project-set config/resolver foundation; release evidence, fresh clean live rerun, frontend UI, and project-set stage/harness integration remain parked follow-ups.
- `2026-05-04` W20 implementation pass completed project-set stage/harness integration and the first local frontend UI surface; OpenCode rerun `W20-E1-S3-T3` found an AIDD-owned interview parser boundary, `W20-E1-S3-T4` fixed it with regression coverage, and `W20-E1-S3-T5` is next for the post-parser-fix live rerun.
- `2026-05-04` W20 closure-and-hardening pass completed frontend smoke hardening and project-set artifact evidence tightening; post-parser-fix OpenCode live rerun `W20-E1-S3-T5` is blocked by runtime/provider timeout evidence, and `W20-E1-S2-T2` remains parked until a release candidate tag and registry credentials exist.
- `2026-05-04` W20 live timeout-profile pass completed `W20-E1-S4-T1`; backlog advanced `W20-E1-S4-T2` to `Next`, parked Codex fallback `W20-E1-S4-T3`, and kept release/install evidence `W20-E1-S2-T2` parked until a release candidate tag and registry credentials exist.
- `2026-05-04` `W20-E1-S4-T2` is blocked by live model-output validation evidence, not provider/runtime timeout; `W20-E1-S4-T3` remains parked and unpromoted because Codex fallback is reserved for provider/runtime timeout blockers.
- `2026-05-04` W20 comparative live-flow diagnosis opened `W20-E1-S5`; promoted `W20-E1-S5-T1` to `Next`, `W20-E1-S5-T2` and `W20-E1-S5-T3` to `Soon`, and left Codex fallback plus release/install evidence parked.
- `2026-05-04` `W20-E1-S5-T1` completed the forensic matrix baseline; backlog advanced `W20-E1-S5-T2` to `Next` and kept `W20-E1-S5-T3` in `Soon`.
- `2026-05-04` `W20-E1-S5-T2` ran Claude control rerun `eval-live-005-claude-code-20260504T152414Z`; status `fail`, quality gate `fail`, first boundary `adapter`, and first signal `Adapter outcome: timeout`.
- `2026-05-04` `W20-E1-S5-T3` completed the comparison decision: fresh Claude timeout does not match latest OpenCode validation formatting failure, so no AIDD-owned core regression is proven; active W20 queue is empty except parked Codex fallback and release/install evidence.
- `2026-05-04` Remaining W20 gap tasks were added for OpenCode contract-compliance hardening, Claude timeout/profile diagnosis, local-project operator UI evidence, frontend provider readiness, and local operator adoption; `W20-E1-S6-T1` is promoted to `Next`, near-term hardening/evidence/adoption tasks are in `Soon`, and rerun/manual-smoke/release tasks remain parked.
- `2026-05-06` `W20-E1-S6` completed idea-stage OpenCode contract-compliance hardening and post-hardening rerun evidence; old `Open questions` list-format blocker is closed, new review-stage evidence-reference blocker was added as `W20-E1-S8`, `W20-E1-S7-T1` is promoted to `Next`, and `W20-E1-S8-T4` is parked until local review hardening lands.
- `2026-05-06` `W20-E1-S7` completed Claude timeout/profile diagnosis; post-evidence Claude rerun `eval-live-005-claude-code-20260506T074233Z` passed with quality gate `warn`, first failure boundary `none`, and no stage timeouts. `W20-E1-S8-T1` is promoted to `Next`; `W20-E1-S8-T4` remains parked until review-stage hardening lands.
- `2026-05-06` `W20-E1-S8` completed OpenCode review evidence-reference hardening and rerun evidence. `eval-live-005-opencode-20260506T094747Z` passed with first failure boundary `none`; generated quality gate was `fail` due to an AIDD-owned quality parser mismatch, now fixed and covered locally as `warn`/`ready-with-risks`. `W20-E2-S5-T1` is promoted to `Next`.
- `2026-05-06` `W20-E2-S5` completed the separate operator-UI local-project E2E lane, deterministic service/CLI coverage, manual installed UI smoke against a disposable local fixture project, and project-set root visibility evidence. `W20-E2-S6-T1` is promoted to `Next`.
- `2026-05-06` `W20-E2-S6` completed runtime readiness read model, private UI endpoint/panel, and escaping/source-of-truth tests. `W20-E4-S1-T1` is promoted to `Next`; `W20-E4-S1-T2` remains in `Soon`.
- `2026-05-06` `W20-E4-S1` completed local operator path docs and the GitHub issue-intake scope guard. `W20-E4-S2-T1` is promoted to `Next`; `W20-E4-S2-T2` is promoted to `Soon`.
- `2026-05-06` `W20-E4-S2` completed the source-installed local fixture smoke path. No unblocked Wave 20 local tasks remain; `W20-E1-S2-T2` and `W20-E1-S4-T3` stay parked behind their documented external conditions.
- `2026-05-06` Release candidate tag `v0.1.0a0` was pushed to merged `main` commit `aa3655998227e6da2a979b06d2c87543adbf4734`; release run `25437182363` failed at PyPI Trusted Publishing `invalid-publisher`, so `W20-E1-S2-T2` remains parked. The discovered prerelease GHCR `latest` tagging defect was fixed as completed roadmap task `W20-E1-S2-T3`.
- `2026-05-06` Fresh OpenCode fallback gate `eval-live-005-opencode-20260506T131037Z` failed at validation (`qa` attempt 3 `SEM-RISK-UNDERREPORT`) with no timeout signals, so Codex fallback was not run and `W20-E1-S4-T3` was removed from `Parking lot` as not applicable.
- `2026-05-06` Release/install evidence closed with accepted tag `v0.1.0a2` on commit `92c893dbd830292ecab5b684a0a4044ef61a67d6`; release run `25448551936` passed build, PyPI publish, `pipx`, `uv tool`, container publish, and GHCR verification. Later alpha distribution policy demoted Docker/GHCR to historical evidence only. `W20-E1-S2-T2` is done and removed from the parking lot; the active backlog queue is empty.
- `2026-05-07` Wave 21 was opened via `W8-E3-S1` queue-restoration policy for full audit closure; promoted `W21-E1-S1-T1` to `Next`, UI safety and project-set evidence tasks to `Soon`, and adapter/provenance/runtime-log/maintainability closure tasks to `Parking lot`.
- `2026-05-07` Wave 21 completed explicit UI runtime selection, warn-only UI request safety, conditional project-set stage-result evidence, adapter callable registration, manifest provenance completion, runtime-log event ownership, and scoped module decomposition. Active backlog queue is empty again.
- `2026-05-07` Wave 22 was opened via `W8-E3-S1` queue-restoration policy to reconcile the empty active backlog with stale historical blocked local tasks; `W22-E0-S1-T1` was promoted to `Next` for the reconciliation pass.
- `2026-05-07` Wave 22 completed `W22-E0-S1-T1`: stale blockers `W15-E3-S1-T1`, `W15-E3-S2-T1`, `W20-E1-S3-T5`, and `W20-E1-S4-T2` were closed or superseded by accepted later evidence. Active backlog queue remains empty.
- `2026-05-18` Wave 23 completed `W23-E1-S1-T1`: the legacy eval-run
  product command and its monolithic live execution path were removed, manual live
  E2E now uses the stepwise black-box evaluator module, and the active backlog queue
  remains empty.
- `2026-05-21` Wave 24 opened for beta-readiness release preparation. Completed
  `W24-E1-S1-T1` through `W24-E1-S1-T4` for source-of-truth audit, deterministic
  release guardrails, source-installed local smoke path verification, and draft
  release notes. Promoted `W24-E1-S2-T1` to `Next` and `W24-E1-S2-T2` to `Soon`
  for manual live evidence refresh outside CI/CD.
- `2026-05-26` Wave 25 opened from the audit's non-security local-alpha findings.
  Operator UI/runtime hardening moved ahead of W24 manual live evidence; `W24-E1-S2-T1`
  and `W24-E1-S2-T2` remain parked, not removed.
- `2026-05-26` Completed `W25-E1-S1-T1`; backlog advanced with `W25-E1-S1-T2`
  promoted to `Next`.
- `2026-05-26` Completed `W25-E1-S1-T2`; backlog advanced with `W25-E1-S1-T3`
  promoted to `Next`.
- `2026-05-26` Completed `W25-E1-S1-T3`; backlog advanced with `W25-E1-S2-T1`
  promoted to `Next`.
- `2026-05-26` Completed `W25-E1-S2-T1`; backlog advanced with `W25-E2-S1-T1`
  promoted to `Next`; `W25-E1-S2-T2` and `W25-E1-S2-T3` remain parked.
- `2026-05-26` Completed `W25-E2-S1-T1`; backlog advanced with `W25-E1-S2-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E1-S2-T2`; backlog advanced with `W25-E1-S2-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E1-S2-T3`; backlog advanced with `W25-E2-S1-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E2-S1-T2`; backlog advanced with `W25-E2-S1-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E2-S1-T3`; backlog advanced with `W25-E2-S2-T1`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E2-S2-T1`; backlog advanced with `W25-E2-S2-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E2-S2-T2`; backlog advanced with `W25-E2-S2-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E2-S2-T3`; backlog advanced with `W25-E3-S1-T1`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E3-S1-T1`; backlog advanced with `W25-E3-S1-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E3-S1-T2`; backlog advanced with `W25-E3-S1-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E3-S1-T3`; backlog advanced with `W25-E4-S1-T1`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S1-T1`; backlog advanced with `W25-E4-S1-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S1-T2`; backlog advanced with `W25-E4-S1-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S1-T3`; backlog advanced with `W25-E4-S2-T1`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S2-T1`; backlog advanced with `W25-E4-S2-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S2-T2`; backlog advanced with `W25-E4-S2-T3`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S2-T3`; backlog advanced with `W25-E4-S3-T1`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S3-T1`; backlog advanced with `W25-E4-S3-T2`
  promoted from `Parking lot` to `Next`.
- `2026-05-26` Completed `W25-E4-S3-T2` and closed Wave 25. No non-security W25
  local operator workflow hardening tasks remain queued; W24 manual live evidence
  tasks remain parked.
- `2026-05-26` Completed `W24-E1-S2-T1` manual live refresh with one supplementary
  Codex smoke pass and three medium-plus/large terminal evidence bundles:
  `eval-live-007-codex-20260526T163850Z` exposed harness/stage timeout cleanup work,
  `eval-live-007-claude-code-20260526T172838Z` recorded an external provider quota
  blocker with visible raw logs, and `eval-live-006-opencode-20260526T173043Z`
  exposed provider-error payload classification work. `W24-E1-S2-T2` is promoted to
  `Next`.
- `2026-05-26` Split broad `W24-E1-S2-T2` evidence-backed fix work: `W24-E1-S2-T2`
  now owns `opencode` provider error-payload classification and remains in `Next`;
  `W24-E1-S2-T3` owns live harness timeout lifecycle/evidence cleanup and is promoted
  to `Soon`.
- `2026-05-26` Completed `W24-E1-S2-T2`; native OpenCode provider API error payloads
  with zero process exit now stop as `provider_error` before repair retries, with raw
  logs and runtime exit metadata preserved. `W24-E1-S2-T3` is promoted to `Next`.
- `2026-05-26` Completed `W24-E1-S2-T3`; black-box live stage command timeouts now
  reconcile non-terminal inspected stage metadata to `failed`, write timeout
  reconciliation evidence, and keep the evidence local. Wave 24 is closed and the active
  backlog queue is empty.
- `2026-05-27` Wave 26 was opened for the accepted Mission Control operator UI and
  completed-flow lineage behavior; promoted `W26-E1-S1-T1` to `Next`, core lineage
  follow-up plus static UI refactoring foundation tasks to `Soon`, and kept the
  remaining core read-model, UI, API, deterministic coverage, local-project E2E, and
  public live E2E next-flow checkpoint tasks plus operator documentation follow-up in
  `Parking lot`.
- `2026-05-27` After rebasing on remote `origin/main`, latest-main UI analysis found no
  new remote commits beyond the branch base, but confirmed current main already split
  packaged static assets and core operator frontend read models while leaving
  `operator.js`, `operator.css`, and script-string UI tests large. `W26-E2-S0` was added
  so static UI module/CSS/test refactoring happens before Mission Control screen rollout.
- `2026-05-28` Completed `W26-E1-S1-T1`; terminal-run handoff now exposes final QA
  status, final artifacts, blockers, repair counts, approval counts, answered
  questions, and recommended next-flow actions. `W26-E1-S1-T2` is promoted to `Next`.
- `2026-05-28` Completed `W26-E1-S1-T2`; lineage references for source run, source work
  item, baseline, and child work item candidates now flow through core run/work-item read
  models. `W26-E1-S2-T1` is promoted to `Next`.
- `2026-05-28` Completed `W26-E1-S2-T1`; follow-up draft creation now writes durable
  work-item context with source-run lineage and referenced source artifacts. `W26-E1-S2-T2`
  is promoted to `Next`, and `W26-E1-S2-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E1-S2-T2`; clone-flow draft creation now records editable
  runtime, prompt-pack, resource, commit, and baseline configuration before launch.
  `W26-E1-S2-T3` is promoted to `Next`.
- `2026-05-28` Completed `W26-E1-S2-T3`; next-flow launch preflight now checks writable
  workspace state, runtime selection, contract availability, source-run existence, and
  baseline availability before runtime execution. `W26-E2-S0-T1` is promoted to `Next`.
- `2026-05-28` Completed `W26-E2-S0-T1`; the local UI now serves packaged static assets
  through a manifest-backed loader while preserving `/operator.js` and `/operator.css`
  compatibility routes. `W26-E2-S0-T2` is promoted to `Next`, and `W26-E2-S0-T3` is
  promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S0-T2`; `operator.js` is now a compatibility bootstrap
  that loads smaller packaged browser modules for API/state, shell rendering, cockpit,
  artifacts, logs/jobs, questions, approvals/interventions, and next-flow actions.
  `W26-E2-S0-T3` is promoted to `Next`, and `W26-E2-S0-T4` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S0-T3`; `operator.css` is now a compatibility loader
  for packaged token, base, layout, component, and responsive CSS layers. `W26-E2-S0-T4`
  is promoted to `Next`, and `W26-E1-S3-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S0-T4`; monolithic UI script-string assertions were
  split into surface-specific packaged asset contract tests. `W26-E1-S3-T1` is promoted
  to `Next`, and `W26-E1-S3-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E1-S3-T1`; core now exposes a read-only stage document
  workbench read model for Markdown preview/source state, contract requirements,
  validation summaries, references, diff candidates, and version history. `W26-E1-S3-T2`
  is promoted to `Next`, and `W26-E1-S3-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E1-S3-T2`; core stage views now expose read-only
  recovery diagnostics for blocking questions, validation repair attempts, raw-log
  truncation, pending runtime approvals, stopped runs, and request-change context.
  `W26-E1-S3-T3` is promoted to `Next`, and `W26-E2-S1-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E1-S3-T3`; core now exposes an evidence graph read model
  that links existing artifact indexes, stage documents, validator reports, runtime
  events, approval queues, and logs, with a flat artifact table fallback when graph
  inputs are incomplete. `W26-E2-S1-T1` is promoted to `Next`, and `W26-E2-S1-T2`
  is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S1-T1`; Project Setup now renders New Work Item,
  Follow-up Flow, Clone Previous Flow, and Eval / Scenario Batch modes with inherited
  previous-run context from work-item lineage. `W26-E2-S1-T2` is promoted to `Next`,
  and `W26-E2-S1-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S1-T2`; terminal QA handoffs now render Flow Complete,
  Start Next Flow actions, final artifacts, blockers, evidence, approval counts, and
  safety/runtime summaries without a generic runtime fallback. `W26-E2-S1-T3` is
  promoted to `Next`, and `W26-E2-S2-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S1-T3`; Run history now renders parent/source run
  lineage, child work item candidates, next-action badges, linked artifacts, and
  follow-up/clone/eval/archive actions with escaped dynamic labels. `W26-E2-S2-T1`
  is promoted to `Next`, and `W26-E2-S2-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S2-T1`; Start Next Flow now renders a read-only
  source findings selection step grouped by QA findings, review notes, failed
  evidence, and manual request, backed by `/api/next-flow/source-findings`.
  `W26-E2-S2-T2` is promoted to `Next`, and `W26-E2-S2-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S2-T2`; the wizard now renders an editable follow-up
  work item definition with generated acceptance criteria, required evidence,
  inherited context toggles, and first-stage input preview. `W26-E2-S2-T3` is
  promoted to `Next`, and `W26-E2-S3-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S2-T3`; the next-flow wizard now renders launch
  confirmation with preflight results, audit preview, source artifact links, and an
  honest queued launch action. `W26-E2-S3-T1` is promoted to `Next`, and
  `W26-E2-S3-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S3-T1`; the Artifacts tab now renders the Stage
  Document Workbench with artifact tree, Preview/Source/Diff controls, contract
  requirements, validation results, missing evidence, references, and version history.
  `W26-E2-S3-T2` is promoted to `Next`, and `W26-E2-S3-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S3-T2`; Questions and Validation now render first-class
  recovery screens for required answers, partial/deferred interview states, repair
  availability, repair timelines, explicit stop context, and Run Repair / Stop Run /
  Request Change actions. `W26-E2-S3-T3` is promoted to `Next`, and `W26-E2-S3-T4`
  is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S3-T3`; Runtime Logs / Live Console and Approvals /
  Request Change now render raw log filters, bounded-log notices, approval queues,
  diff previews, intervention composer controls, and audit logs. `W26-E2-S3-T4` is
  promoted to `Next`, and `W26-E3-S1-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E2-S3-T4`; Artifacts / Evidence Graph now renders
  provenance nodes, selectable edges, selected-artifact inspector actions, flat table
  fallback, and open/download/copy-path controls. `W26-E3-S1-T1` is promoted to
  `Next`, and `W26-E3-S1-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E3-S1-T1`; private UI endpoints now create durable
  follow-up and clone drafts through core next-flow services with deterministic bad
  request responses and no runtime execution. `W26-E3-S1-T2` is promoted to `Next`,
  and `W26-E3-S1-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E3-S1-T2`; private next-flow launch now runs preflight,
  starts a normal workflow job for the new work item only after explicit runtime
  selection, and passes source-run lineage to the run manifest without mutating the
  source run. `W26-E3-S1-T3` is promoted to `Next`, and `W26-E3-S2-T1` is promoted
  to `Soon`.
- `2026-05-28` Completed `W26-E3-S1-T3`; private archive decisions now persist
  operator archive metadata for terminal QA runs while keeping source artifacts
  readable through dashboard, history, and artifact endpoints. `W26-E3-S2-T1` is
  promoted to `Next`, and `W26-E3-S2-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E3-S2-T1`; static UI asset contracts now cover accepted
  Mission Control landmarks, Flow Complete handoff, next-flow wizard controls, run
  lineage labels, and focus-visible affordances. `W26-E3-S2-T2` is promoted to
  `Next`, and `W26-E3-S2-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E3-S2-T2`; service-level UI regressions now cover
  completed-run next actions, follow-up draft creation, clone draft creation, launch
  preflight, and archive decisions while preserving source artifacts. `W26-E3-S2-T3`
  is promoted to `Next`, and `W26-E4-S1-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E3-S2-T3`; the manual browser checklist now covers Flow
  Complete, Start Next Flow wizard controls, run-history lineage, desktop/tablet/mobile
  completed-flow layouts, and keyboard traversal. `W26-E4-S1-T1` is promoted to
  `Next`, and `W26-E4-S1-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S1-T1`; the local-project UI E2E lane now requires
  completed-run evidence for Flow Complete, Start Next Flow, follow-up draft, launch
  preflight, run-history lineage, archive decision, and artifact preservation.
  `W26-E4-S1-T2` is promoted to `Next`, and `W26-E4-S1-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S1-T2`; deterministic local fixture coverage now seeds
  a terminal QA run and proves the UI can create a follow-up draft with source-run
  lineage and source artifact references without invoking a provider runtime.
  `W26-E4-S1-T3` is promoted to `Next`, and `W26-E4-S2-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S1-T3`; the local-project manual smoke path now records
  required completed-run evidence fields, browser/viewport/runtime metadata, blocker
  capture, archive decision, and cleanup rules for generated `.aidd/` state.
  `W26-E4-S2-T1` is promoted to `Next`, and `W26-E4-S2-T2` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S2-T1`; manual live E2E policy now requires a
  terminal next-flow checkpoint after `qa`, records the operator decision, and keeps
  second public-repository flow launch optional, manual-only, and outside CI/CD.
  `W26-E4-S2-T2` is promoted to `Next`, and `W26-E4-S2-T3` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S2-T2`; the black-box live evaluator now writes
  `next-flow-checkpoint.json` and `next-flow-checkpoint.md` with completed-run
  next-action evidence, source-run summary fields, blocker/repair/approval/question
  counts, and optional lineage metadata. `W26-E4-S2-T3` is promoted to `Next`, and
  `W26-E5-S1-T1` is promoted to `Soon`.
- `2026-05-28` Completed `W26-E4-S2-T3`; the optional manual-only live follow-up proof
  flag now creates a follow-up draft from terminal QA findings and records
  `next-flow-lineage.json` without launching a child public-repository flow. Wave 26
  live E2E integration is done, and `W26-E5-S1-T1` is promoted to `Next`.
- `2026-05-28` Completed `W26-E5-S1-T1`; operator-facing docs now describe
  completed-run Flow Complete handoff, next-flow actions, source-run lineage,
  launch-preflight troubleshooting, archive behavior, and the boundary between
  local-project UI proof and public-repository live E2E checkpoint evidence. Wave 26 is
  done and the active backlog queue is empty.
- `2026-06-02` Wave 27 opened for UI-first onboarding while preserving existing CLI
  behavior. Promoted `W27-E1-S1-T1` to `Next`, `W27-E1-S1-T2` and `W27-E2-S1-T1` to
  `Soon`, and kept the explicit launcher, project setup, runner selection,
  project-set/recent-project, and onboarding evidence tasks in `Parking lot` until the
  contract is accepted.
- `2026-06-04` Wave 27 was reconciled as shipped/superseded after accepted
  `v0.1.0a8` evidence. Wave 28 opened for post-a8 operator hardening and release
  ergonomics; `W28-E1-S1-T2` is promoted to `Next`, `W28-E2-S1-T1`,
  `W28-E2-S1-T2`, and `W28-E3-S1-T1` are promoted to `Soon`, and
  `W28-E3-S1-T2` plus `W28-E4-S1-T1` remain in `Parking lot`.
- `2026-06-04` Completed `W28-E1-S1-T1` and `W28-E1-S1-T2`: release evidence PR #65 is
  merged into `main`, `0.1.0a9.dev0` source development is current, and the release
  checklist documents PATH-safe `gh` usage. `W28-E2-S1-T1` is promoted to `Next`.
- `2026-06-04` Completed `W28-E2-S1-T1` and `W28-E2-S1-T2`: published
  `ai-driven-dev-v2==0.1.0a8` clean UI onboarding smoke passed from isolated install
  through `idea` and `research`, and no immutable-release UI defect was found.
  `W28-E3-S1-T1` is promoted to `Next`, and `W28-E4-S1-T1` is promoted to `Soon`.
- `2026-06-04` Completed `W28-E3-S1-T1`; `W28-E3-S1-T2` is superseded because no
  source-only operator-control-center defect was found. `W28-E4-S1-T1` is promoted to
  `Next`.
- `2026-06-04` Completed `W28-E4-S1-T1`; next-prerelease readiness evidence and remaining
  operator risks are recorded in the release checklist. Wave 28 is closed and the active
  backlog queue is empty again.
- `2026-06-04` Wave 29 was opened via `W8-E3-S1` queue-restoration policy as one large
  product scope for real-provider UI E2E, browser-verified operator UX, project-set UX,
  prompt/workflow accountability, runtime safety, release ergonomics, and beta readiness.
  Promoted `W29-E1-S1-T1` to `Next`; `W29-E1-S1-T2`, `W29-E2-S1-T1`, and
  `W29-E7-S1-T1` to `Soon`; and parked the remaining Wave 29 implementation/evidence
  tasks until the acceptance contract is written.
- `2026-06-04` Wave 29 contract/tooling pass completed `W29-E1-S1`,
  `W29-E2-S1-T1`, `W29-E3-S1`, `W29-E4-S1-T1` through `T3`, `W29-E5-S1`,
  `W29-E6-S1`, and `W29-E7-S1-T1` through `T2`. Active queue advances to
  `W29-E1-S2-T1`; Claude Code, OpenCode, and Qwen smokes were initially parked as
  `auth/env` blockers because those binaries were not present in the non-interactive
  Codex app shell `PATH`.
- `2026-06-04` Completed `W29-E1-S2-T1` and `W29-E1-S2-T5`: disposable Codex UI smoke
  at `/tmp/aidd-w29-codex-ui-smoke-20260604T101201Z` passed clean onboarding,
  explicit `codex` runner selection, missing-runtime API rejection, selected-stage
  `idea` and `research`, terminal cleanup, logs, timeline, and artifacts. The provider
  triage matrix is recorded in the roadmap; OpenCode/Qwen binary readiness and Claude
  Code login-shell readiness still required separate authenticated smoke lanes. Active
  queue advances to `W29-E2-S1-T2`; `W29-E2-S1-T3` and `W29-E4-S1-T4` move to `Soon`.
- `2026-06-04` Completed `W29-E2-S1-T2` and `W29-E2-S1-T3`: Manual+Browser evidence
  in `/tmp/aidd-w29-browser-ui-smoke-pass-20260604T103044Z` covered clean onboarding,
  runner cards, create-form enablement, explicit `generic-cli`, selected-stage
  `idea` and `research`, terminal cleanup, logs, timeline, and artifacts. Seeded
  evidence in `/tmp/aidd-w29-browser-seeded-20260604T103356Z` covered Implement Review,
  Review Findings, QA Verdict, remediation requests/status, stale downstream badges,
  blockers, and runtime readiness. No repeatable AIDD-owned browser UX defect was found,
  so `W29-E2-S1-T4` is superseded for this pass. Active queue advances to
  `W29-E4-S1-T4`; `W29-E7-S1-T3` moves to `Soon` after comparison work.
- `2026-06-04` Completed `W29-E4-S1-T4`: added a read-only core/UI run comparison
  surface for two run ids in the active work item, covering prompt hash, stage status,
  bounded artifact hash, and validator outcome deltas with legacy/unsafe-path warnings.
  Active queue advances to beta-oriented release note criteria `W29-E7-S1-T3`.
- `2026-06-04` Completed `W29-E7-S1-T3`: release checklist now defines beta-oriented
  release note criteria that require fresh provider, Browser, install, remediation,
  project-set, provenance/comparison, approval audit, security, and package-channel
  evidence, and it keeps `0.1.0a9.dev0` separate from accepted releases. Wave 29 is
  closed with the provider lanes still pending login-shell verification. The queue is
  empty again.
- `2026-06-04` Completed the W29 provider-auth rerun from a login shell: disposable
  evidence root `/tmp/aidd-w29-provider-auth-rerun-20260604T113402Z` proves
  `claude-code`, `opencode`, and optional `qwen` clean UI onboarding plus selected-stage
  `idea -> research` all pass with explicit runtime selection, missing-runtime rejection,
  completed jobs, succeeded stage rail statuses, logs, timelines, and artifacts. W29
  provider lanes are no longer blocked; future provider smokes should use a login shell
  or explicit PATH prefix when provider binaries are outside the Codex app's default
  non-interactive PATH.
- `2026-06-04` Wave 30 opened for security posture and `v0.1.0a9` release readiness:
  `W30-E1-S1-T1` is promoted to `Next`, `W30-E2-S1-T1` and `W30-E2-S1-T2` are in
  `Soon`, and `W30-E3-S1-T1` was parked until a separate explicit release-prep
  approval exists.
- `2026-06-04` Completed `W30-E1-S1-T1`, `W30-E2-S1-T1`, and `W30-E2-S1-T2`: Dependabot
  alerts were triaged and patched through `uv.lock`, fresh source clean-UI smoke evidence
  passed in `/tmp/aidd-w30-release-readiness-smoke-20260604T121108Z`, and release
  readiness notes now keep `0.1.0a9.dev0` as development source. `W30-E3-S1-T1` stayed
  parked until the later accepted release evidence made the original prep action obsolete.
- `2026-06-09` Wave 31 opened for the integrated operator workbench redesign:
  `W31-E1-S1-T1` is promoted to `Next`; `W31-E1-S1-T2`, `W31-E2-S1-T1`, and
  `W31-E3-S1-T1` are in `Soon`; the broader project/work-item, document workbench,
  diagnostics, recovery, contextual navigation, and browser evidence rollout remains
  parked until the UX contract lands.
- `2026-06-09` Wave 31 completed and was removed from the active queue. At that point the
  only parked item was `W30-E3-S1-T1`; it was later closed by accepted release evidence
  reconciliation.
