# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W45-E1-S2-T1` — Require every QA evidence claim to cite a resolvable artifact or executable
  result. Correct the QA authoring guidance and deterministic fixture coverage for
  `CROSS-QA-UPSTREAM-EVIDENCE` without weakening fail-closed traceability; the fresh Codex medium
  rerun `eval-live-007-codex-20260827T145034Z` exposed a prose-only bounded-diff evidence entry
  (`EV-4`) that exhausted QA validation.

## Soon

- None.

## Parking lot

- `W42-E7-S2-T3` — Record one genuine uncoached first-time operator observation when a participant
  and eligible environment are available; this is deferred human-usability evidence, not a pass.
- `W43-E5-S2-T3` — Run a future cross-runtime lower-capability comparison after Codex-only alpha.
- `W36-E7-S4-T4` — Claude acceptance is not launched under the current Codex-only scope.
- `W36-E7-S3-T2` — Record five first-time-operator sessions after initial live hardening.
- `W36-E7-S3-T3` — Reconcile observed session findings before beta readiness.
- `W36-E7-S4-T5` — Record final same-revision Codex and Claude acceptance evidence.

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

- `2026-08-27` fresh Codex medium rerun `eval-live-007-codex-20260827T145034Z` reached QA after
  implementing the bounded Hono non-Error throw fix and passing 235 focused tests plus TypeScript.
  QA failed closed on one `CROSS-QA-UPSTREAM-EVIDENCE` finding: `EV-4` described a bounded product
  path check only as prose and did not include an exact upstream artifact path or executable
  command/result. This is an AIDD QA authoring/traceability defect, not a Hono or UI defect.
  `W45-E1-S2-T1` is promoted as the next task; the run remains diagnostic until the task is merged
  and the medium lane is rerun from clean `main`.

- `2026-08-27` reconciliation after PR #430 (`fa9a9674`) marks `W45-E1-S1-T3` done. The evidence
  parser now recognizes the exact compound command-substitution/pipeline/test shape that blocked
  the prior Codex medium run; focused validator, semantic implement, and semantic QA checks pass
  (`72 passed`), and CI is green. Fresh Codex medium `eval-live-007-codex-20260827T093650Z` passed
  through QA with task-aware checkpoint evidence. Claude must still be rerun before a two-runtime
  pass is claimed; the earlier Claude QA evidence-link failure remains diagnostic until reproduced.

- `2026-08-27` live Codex medium run `eval-live-007-codex-20260827T044743Z` reached aggregate
  implementation finalization after all five implementation tasks succeeded, but publication
  failed because the non-interview flow had no `workitems/WI-LIVE-HONO-SMOKE/stages/implement/answers.md`.
  This is a core publication compatibility defect, not a target-repository failure. `W45-E1-S1-T1`
  was added as a single `Next` task and is now complete in PR #425 (merge `2878a851`); the
  interrupted run remains retained as diagnostic evidence and must be rerun from a clean `main`.
  Human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-27` PR #425 (merge `2878a851`) completed `W45-E1-S1-T1`. Aggregate stage publication now
  skips only absent conditional `questions.md`/`answers.md` records, publishes them when present,
  and continues to fail closed for missing substantive or canonical AIDD records. Focused core and
  full CI checks passed; the Codex medium lane is next for rerun.

- `2026-08-27` Codex medium rerun `eval-live-007-codex-20260827T064545Z` reached Review with all
  target implementation tasks and focused checks passing, but exhausted validation attempts because
  lifecycle `stage-result.md` retained duplicate terminal status markers after repair. The approved
  Review report and target diff show no product defect; `W45-E1-S1-T2` is the next core hardening task
  before the Codex and Claude lanes are rerun.

- `2026-08-27` Reconciliation after PR #428 (`a184fe95`) marks `W45-E1-S1-T2` done. The fresh Codex
  run `eval-live-007-codex-20260827T082029Z` then found a validator false negative for a valid compound
  `git status`/`awk`/`test` evidence command; target implementation and focused tests passed, but the
  AIDD evidence contract exhausted its repair budget. `W45-E1-S1-T3` is the sole Next task for parser
  hardening; the run remains retained as diagnostic evidence.

- `2026-08-26` PR #421 (merge `722e38b0`) completed `W44-E1-S3-T47`: mobile question and recovery
  headers now retain AIDD, the current Work Item identity, a 44px Inbox/back arrow, and a 44px
  overflow/runtime control with no horizontal overflow. Focused mobile/question recovery checks,
  frontend (`136`), full CI, packaged UI browser, security, and build passed. Wave 44 rendered
  acceptance is complete; human usability, Claude/cross-runtime, and Wave 36 evidence remain in
  the parking lot.

- `2026-08-26` planning update: the fresh 13-surface audit found a bounded target gap on mobile
  question/recovery surfaces: the current header shows AIDD and Inbox but not the current Work Item
  identity required by `13-mobile-decision.png`. `W44-E1-S3-T47` is added to the roadmap and promoted
  to `Next`; no overview, Inbox, setup, route, or action semantics are changed by this task.

- `2026-08-26` PR #418 (merge `f533b336`) completed `W44-E1-S3-T46`: mobile Work Item detail now
  exposes the AIDD brand, current Work Item id, accessible Inbox/back path, and overflow/runtime
  control in a compact 64px header. Fresh five-viewport captures (`320x568`, `390x844`, `768x1024`,
  `1280x900`, `1440x900`) confirm the target shell hierarchy, context/tabs/stages, launch inspector,
  clean diagnostics, and no horizontal overflow. Shell (`20`), mobile header (`6`), focused primary
  decision launch (`4`), frontend (`136`), docs/planning (`50`), Ruff, mypy, and full CI including
  packaged UI browser passed. No additional bounded UI gap was found; human, Claude/cross-runtime,
  and Wave 36 evidence remain parked.

- `2026-08-26` PR #416 (merge `efec5a79`) completed `W44-E1-S3-T45`: tablet detail now uses a compact
  64px topbar, hides duplicate breadcrumb/status chrome, and restores context → tabs → stages order
  at `768x1024`; Inbox/setup and mobile navigation remain unchanged. Focused shell (`18`), active
  studio reconnect (`5`), frontend (`136`), UI contracts (`11`), docs/planning (`50`), Ruff, mypy,
  and full CI including packaged UI browser passed. Fresh mobile comparison identified the next
  bounded detail-header identity gap; `W44-E1-S3-T46` is promoted to `Next`.

- `2026-08-26` PR #414 (merge `2534cdef`) completed `W44-E1-S3-T44`: detail context now uses a compact
  target-style title/metadata rhythm with durable Work Item id and current status still discoverable;
  the desktop title, tabs, and stages occupy the intended first viewport while mobile remains unchanged.
  Focused shell (`15`), active-studio (`5`), frontend (`136`), UI contracts (`183`), docs/planning (`50`),
  Ruff, mypy, and full CI including packaged UI browser (`14m53s`) passed. Fresh `768x1024` comparison
  exposes the next bounded gap: the legacy tablet topbar remains tall and tabs precede context; `T45` is
  promoted to `Next`.

- `2026-08-26` PR #412 (merge `831be726`) completed `W44-E1-S3-T43`: detail surfaces now collapse the
  generic desktop breadcrumb/status row to zero-height chrome while retaining the real runtime settings
  control for launch/recovery. Inbox/setup topbars, routes, ids, status/runtime semantics, and mobile
  behavior remain unchanged; the detail identity helper now waits for durable attached state rather than
  requiring an intentionally hidden chip. Focused shell (`12`), frontend (`136`), UI contracts (`183`),
  docs/planning (`50`), targeted Inbox regressions, Ruff, mypy, and full CI including packaged UI browser
  (`23m19s`) passed. Fresh comparison identifies the next bounded gap: the internal detail context header
  still stacks an eyebrow, phase/status line, and duplicate identity rows; `W44-E1-S3-T44` is promoted to
  `Next`.

- `2026-08-26` PR #410 (merge `3ef38644`) completed `W44-E1-S3-T42`: detail surfaces now use an
  84px primary navigation rail plus a 236px Work Items rail, while Inbox keeps a single 244px rail
  and mobile keeps the collapsed composition. Focused shell/legacy/inbox (`35`), provider-free
  matrix (`9`), frontend (`136`), UI contracts/docs/planning (`110`), Ruff, mypy, and full CI passed.
  Fresh target comparison identified the next bounded gap: the generic desktop breadcrumb/status
  topbar still consumes a duplicated 64px layer above the Work Item header; `W44-E1-S3-T43` is
  promoted to `Next`.

- `2026-08-26` PR #408 (merge `d7994130`) completed `W44-E1-S3-T41`: Validation Repair now keeps
  the desktop Runner and primary repair action inline and visible in the initial `1280x900` and
  `1440x900` viewports through compact tokenized spacing; tablet scrolling and the mobile safe-area
  dock remain intentional. Focused viewport (`10`), recovery/legacy (`28`), frontend (`136`), UI
  contracts (`53`), docs/planning (`50`), Ruff, mypy, and full CI passed. Fresh target comparison
  identified the next bounded gap: detail surfaces need the target icon navigation rail plus a
  separate Work Items navigator; `W44-E1-S3-T42` is promoted to `Next`.

- `2026-08-26` PR #406 (merge `40632549`) completed `W44-E1-S3-T40`: desktop Validation Repair
  actions now remain inline with the finding inspector instead of covering consequence, exact repair
  brief, or extension evidence; mobile keeps its initial-viewport dock. Focused viewport (`10`),
  recovery (`11`), target legacy (`17`), five-viewport matrix, frontend (`136`), UI contracts (`63`),
  docs/planning (`50`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and
  build checks passed. Fresh screenshots found no overlap, but the inline desktop action is now below
  the initial `1280x900`/`1440x900` viewport; `T41` is promoted as the next bounded convergence task.

- `2026-08-26` PR #402 (merge `924138cc`) completed `W44-E1-S3-T38`: shared shell breadcrumbs now
  expose a truthful project label, Work Item, and current-stage label without rendering the absolute
  filesystem path. Existing project-path provenance utilities, route/deep-link behavior, DOM ids,
  and setup/launch semantics remain unchanged. Focused breadcrumb browser checks (`2 passed`),
  frontend tests (`36 passed`), Guided Setup/packaged smoke (`2 passed`), UI contracts/docs/planning
  (`105 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build
  checks passed. `T39` was promoted as the next task and is now complete; `T40` is now `Next`; human usability, Claude/cross-runtime, and Wave 36 acceptance
  remain parked.

- `2026-08-26` PR #400 (merge `6d9f8287`) completed `W44-E1-S3-T37`: Runs and Attempts now use a
  compact retained-run list and tighter chronology rhythm while keeping the selected-attempt
  inspector, evidence/lineage, comparison eligibility, read-only actions, routes, selectors, and
  historical semantics unchanged. Focused history browser checks (`12 passed`, plus `2 passed` after
  final CSS refinement), frontend tests (`36 passed`), UI contracts/docs/planning (`108 passed`), Ruff,
  mypy, full CI, deterministic, adapter, packaged-browser, security, and build checks passed. `T38`
  was promoted and completed; `T39` is now `Next`; human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-26` PR #398 (merge `da87abd7`) completed `W44-E1-S3-T36`: Review/QA Remediation now keeps
  findings, source paths, retained evidence, durable request state, downstream impact, Runner readiness,
  and the single remediation action in the target two-region composition with responsive fallback. Exact
  finding ids, selection semantics, draft destinations, conflict/staleness behavior, routes, and mutation
  services remain unchanged. Focused browser review/QA checks (`6 passed`), frontend tests (`28 passed`),
  UI contracts (`58 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security,
  and build checks passed. `T37` was promoted and completed; `T38` is now `Next` and `T39` is its direct
  `Soon` successor; human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-26` PR #396 (merge `66af77e9`) completed `W44-E1-S3-T35`: Implementation Review now uses a
  compact claims/verification overview, retains the canonical task ledger, and presents repository diff
  evidence beside a distinct Review inspector with responsive one-column fallback. Repository-truth
  evidence, launch readiness, read-only stage documents, routes, ids, and one primary Review action remain
  unchanged. Focused browser composition checks (`3 passed`), frontend tests (`36 passed`), UI contracts,
  docs/planning (`108 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security,
  and build checks passed. `T36` is now `Next` and `T37` is its direct `Soon` successor; human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-26` PR #394 (merge `901b6bd0`) completed `W44-E1-S3-T34`: Project Work now uses a compact
  server-owned grouped table with explicit Work Item, Stage, Progress, Runner, Last event, and Status
  columns, truthful progress bars, selected-context inspector bounds, responsive normal flow, and no
  duplicated entry banner in the selected view. Existing membership/order, routes, ids, deep links,
  keyboard selection, action services, and Guided Setup resume entry action remain intact. Focused target
  browser checks (`4 passed`), Inbox selection/routing smoke (`4 passed`), frontend Inbox tests (`8`),
  UI contracts (`58`), docs/planning (`108`), Ruff, mypy, full CI, deterministic, adapter,
  packaged-browser, security, and build checks passed. `T35` is now `Next` and `T36` is its direct `Soon`
  successor; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-26` PR #392 (merge `99ce2bca`) completed `W44-E1-S3-T33`: Decision and Mobile Decision now
  keep context, retained evidence, resolution choices, editor/destination state, and one real primary
  action in the target first viewport across question and approval fixtures at all five supported
  viewports. Read-only evidence opens when source snippets exist; approval queues expose one primary
  Allow once action while preserving secondary decisions. Focused browser/UI checks (`20 passed`), UI
  asset contracts (`53 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed. `T34` is now `Next` and `T35` is its direct `Soon` successor;
  human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #390 (merge `4fc916a7`) completed `W44-E1-S3-T32`: Task Workspace and Active Task
  now keep the selected attempt inspector, factual attempt controls, task groups, and live-output
  tray in the target first viewport. Ready/running/waiting/cancelling/failed/completed fixtures
  passed across desktop/mobile with clean diagnostics and no nested shell scrolling; docs/planning,
  Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build checks passed.
  `T33` is now `Next` and `T34` is its direct `Soon` successor; human usability, Claude/cross-runtime,
  and Wave 36 acceptance remain parked.

- `2026-08-25` PR #388 (merge `f7ab7364`) completed `W44-E1-S3-T31`: Flow Complete keeps its existing
  core-recommended action visible and focusable across the supported bounded tablet/desktop widths,
  including `768x1024`, while immutable handoff/evidence, fresh-QA gating, lineage, recommendation
  truth, routes, ids, and one-primary semantics remain unchanged. The five-viewport completion and
  target legacy/mobile focus checks passed, together with UI contracts, docs/planning, Ruff, mypy,
  full CI, packaged UI browser, deterministic, adapter, security, and build checks. `T32` is now
  `Next`; `T33` is its direct `Soon` successor; human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-25` PR #386 (merge `7c58edda`) completed `W44-E1-S3-T30`: the Work Item Launch action
  remains the existing primary/mutation control and is now visible and focusable at `320x568` in a
  touch-safe bottom dock. The core Runner readiness projection, literal disabled reason, routes,
  ids, fail-closed eligibility, and one contextual Runner are unchanged. Five-viewport launch and
  provider-free create/Runner/launch checks passed, including one-primary-action, focus, diagnostics,
  and overflow assertions. `W44-E1-S3-T31` was promoted as the successor and is now complete;
  `W44-E1-S3-T32` is now `Next`; human usability, Claude/cross-runtime, and Wave 36 acceptance
  remain parked.

- `2026-08-25` PR #384 (merge `b30de404`) completed `W44-E1-S3-T29`: the fresh rendered audit is
  retained in `docs/e2e/w44-e1-s3-t29-rendered-exit-audit.md`. Focused W44 suites passed (`71`),
  while the five-viewport provider-free matrix recorded `6` passes and two first-viewport contract
  failures at launch (`320x568`) and Flow Complete (`768x1024`). Confirmed target-composition gaps
  were decomposed into T30-T39; T30 was the first follow-up and is now complete, with T31 promoted
  to `Next`; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #382 (merge `5828f53b`) completed `W44-E1-S3-T28`: Markdown Workspace now uses
  the target compact navigator, reader, heading map, provenance/context inspector, source/path
  utilities, and one contextual primary action while generated documents remain read-only. Focused
  document/layout browser checks, evidence journeys, frontend/UI contracts, accessibility/readability/
  design-token checks, docs/planning, Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed. `T29` is now the only `Next` task for a fresh 13-surface
  convergence audit; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #380 (merge `737365c5`) completed `W44-E1-S3-T27`: Implementation Review now
  uses repository-truth summary/diff evidence and an explicit Review gate; Review/QA remediation
  uses finding/source-evidence tables, durable Write/Preview requests, downstream impact, contextual
  Runner readiness, and one primary action. Existing routes, selectors, ledger/evidence projections,
  mutation services, and generated-document boundaries remain unchanged. Focused browser journeys,
  frontend/UI contracts, accessibility/readability/design-token checks, docs/planning, Ruff, mypy,
  full CI, deterministic, adapter, packaged-browser, security, and build checks passed. `T28` is
  now the only `Next` task; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #378 (merge `9b97e908`) completed `W44-E1-S3-T26`: Create Work Item now uses the
  target editor/preview shell with durable context and constraints, visible draft status, responsive
  one-action footer, and no duplicate submit action. Existing request persistence, routes, Work Item
  ids, runtime-independent creation, launch-only Runner selection, and operator-authored Markdown
  semantics remain unchanged. Target Create Work Item, guided setup, first-time recovery, frontend,
  UI/design-token contracts, docs/planning, Ruff, mypy, full Python matrix, deterministic, adapter,
  security, packaged UI browser, and build CI passed. `W44-E1-S3-T27` is now the only `Next` task;
  T28 remains planned, while human usability, Claude/cross-runtime, and Wave 36 acceptance stay
  parked.

- `2026-08-25` PR #376 (merge `a8f15319`) completed `W44-E1-S3-T25`: Flow Complete now leads with a
  target-like completion status row, a central immutable handoff/evidence composition, and a bounded
  Completion inspector with fresh-QA checks, retained evidence, run IDs, the core recommendation, one
  primary action, and disclosed secondary outcomes. Existing routes, selectors, lineage, immutable
  source-run semantics, and handoff services remain unchanged. Focused Flow Complete/mobile/terminal/
  desktop browser checks, frontend suites, five-viewport geometry/accessibility/diagnostic checks, UI
  contracts, planning integrity, Ruff, mypy, deterministic, adapter, security, packaged UI browser,
  and build CI passed. `W44-E1-S3-T26` is now the only `Next` task; Wave 44 exit, human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain open or parked as previously scoped.

- `2026-08-25` PR #374 (merge `a85a9d03`) completed `W44-E1-S3-T24`: Runs and Attempts now use the
  target three-region composition with a compact retained-runs list, selected-attempt tabs and
  chronology, read-only Timeline/Raw log/Artifacts views, and an Evidence and lineage inspector
  with retained evidence, lineage, archive, compare, and one primary open action. Existing history
  routes, selectors, auto-follow/read-only semantics, lineage, archive, and comparison services are
  preserved. Focused target/history browser suites (`16`), frontend state/route tests (`41`), five-
  viewport geometry/accessibility/diagnostic checks, CSS contracts, planning integrity, Ruff, mypy,
  deterministic, adapter, packaged UI browser, security, and build CI passed. `W44-E1-S3-T25` is now
  historical; `W44-E1-S3-T26` is the only `Next` task; Wave 44 exit, human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain open or parked as previously scoped.

- `2026-08-25` PR #372 (merge `a733341c`) completed `W44-E1-S3-T23`: Decision recovery now leads with
  rationale, retained evidence, answer/resolution controls, durable destination, and explicit impact;
  Validation Repair now presents a read-only document navigator/reader plus finding inspector before
  the single repair action. The mobile decision and repair compositions keep their first action visible
  without horizontal overflow, while routes, ids, readiness, answer/repair services, and generated
  document immutability remain unchanged. Focused decision/recovery browser checks (`4`), frontend (`28`),
  UI contracts, docs/planning, Ruff, mypy, deterministic, adapter, security, packaged UI browser, and
  build CI passed. `W44-E1-S3-T24` is now the only `Next` task; Wave 44 exit, human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain open or parked as previously scoped.

- `2026-08-25` PR #370 (merge `6e7b5c88`) completed `W44-E1-S3-T22`: Tasks now keep the authoritative
  ledger in a compact grouped table, the selected task/active attempt in a right inspector, and raw
  output in a dedicated lower tray. Factual elapsed/output-age/milestone/cursor data, reconnect and
  cancellation states, one primary action, routes, ids, and mutation services remain unchanged.
  Desktop/mobile target geometry, accessibility/diagnostics, focused browser (`34`), frontend (`136`),
  UI contracts, docs/planning, Ruff, mypy, deterministic, adapter, security, packaged UI browser, and
  build CI passed. `W44-E1-S3-T23` is now Next and `T24` is Soon; Wave 44 exit, human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain open or parked as previously scoped.

- `2026-08-25` PR #368 (merge `2d450192`) completed `W44-E1-S3-T21`: Work Item Overview/Launch now
  presents the truthful request brief and launch scope beside one contextual Runner readiness
  inspector and one primary launch action. The inspector preserves runtime selection and readiness
  revalidation, while compact desktop stage groups keep all labels readable and mobile stacks the
  Runner/action hierarchy without overflow or duplicate primaries. Four-viewport launch composition,
  stage/action/legacy browser suites, frontend (`136`), UI asset contracts, docs/planning, Ruff, mypy,
  deterministic, adapter, build, security, and packaged UI browser CI passed. `W44-E1-S3-T22` is now
  Next and `T23` is Soon; Wave 44 exit evidence, human usability, Claude/cross-runtime, and Wave 36
  acceptance remain open or parked as previously scoped.

- `2026-08-25` PR #366 (merge `82fb1d23`) completed `W44-E1-S3-T20`: selected Project Work now
  keeps the server-owned table/list inside its desktop grid column, places the Work Item inspector
  beside it without overlap, and stacks it normally on mobile. Four-viewport geometry/accessibility,
  deep-link/reload, action-count, diagnostics, focused browser suites, frontend, docs/planning,
  Ruff, mypy, and full CI including packaged UI browser passed. `W44-E1-S3-T21` is now Next and
  `T22` is Soon; T23-T28 remain planned. Wave 44 exit evidence, human usability, Claude/cross-runtime,
  and Wave 36 acceptance stay open or parked as previously scoped.

- `2026-08-25` PR #364 (merge `47a8d903`) completed `W44-E1-S3-T19` from revision `35ff0ace`. The fresh rendered audit is retained
  in `docs/e2e/w44-e1-s3-t19-rendered-exit-audit.md`; provider-free matrix (`9`) and target legacy
  compositions (`5`) are green with clean diagnostics, but target comparison confirmed remaining
  shell, inspector, recovery, history, completion, and editor-density gaps. `W44-E1-S3-T20` was
  Next and `T21` was Soon; T22-T28 remained in the roadmap as planned successors. Human usability,
  Claude/cross-runtime, and Wave 36 acceptance stay parked.

- `2026-08-24` PR #362 (merge `4e36bc6f`) completed `W44-E1-S3-T18`: the compact eight-stage strip now
  keeps all labels, including `Implement`, readable at `1280x900` while preserving canonical order,
  phase grouping, active/current semantics, keyboard access, and mobile disclosure. Five-viewport
  stage/accessibility checks, related active-shell/mobile navigation checks (`12`), frontend (`136`),
  UI/docs/planning (`103`), packaged JavaScript, Ruff, mypy, full CI, deterministic, adapter, security,
  build, and packaged-browser checks passed. `W44-E1-S3-T19` is now Next for the fresh Wave 44 exit and
  default-routing audit; human usability, Claude/cross-runtime, and Wave 36 acceptance stay parked.

- `2026-08-24` PR #360 (merge `a678418a`) completed `W44-E1-S3-T17`: Validation Repair now presents the
  finding, literal repair consequence, readable Runner readiness, and one primary recovery action before
  long extension evidence across all five supported viewports, without changing readiness projections,
  mutation services, routes, API shapes, or selectors. Focused validation/recovery browser checks,
  frontend/UI contracts, docs/planning, Ruff, mypy, packaged JavaScript, full CI, deterministic, adapter,
  security, build, and packaged-browser checks passed. `W44-E1-S3-T18` is now Next for the independent
  stage-strip label-clipping follow-up; Wave 44 exit/default-routing evidence remains open, while human
  usability, Claude/cross-runtime, and Wave 36 acceptance stay parked.

- `2026-08-24` PR #358 (merge `f543ae51`) completed `W44-E1-S3-T16`: Markdown Workspace now presents a
  compact read-only brief, document body, and visible heading map together while preserving navigator
  provenance, freshness, Source/Compare semantics, stable anchors, generated-document immutability,
  existing routes/API shapes, and mobile touch targets. Focused five-viewport document journeys,
  frontend/UI asset/readability contracts, Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed. `W44-E1-S3-T17` is now Next; the stage-strip clipping follow-up,
  Wave 44 exit/default-routing evidence, human usability, Claude/cross-runtime, and Wave 36 acceptance
  remain parked or open as previously scoped.

- `2026-08-24` PR #356 (merge `2e77fac5`) completed `W44-E1-S3-T15`: Active Task now leads with the
  selected task-attempt evidence, factual elapsed/output-age/milestone/connection facts, one `Open
  live output` primary, guarded cancellation, reconnect state, and collapsible raw output. Existing
  task actions, route/API shapes, core-owned eligibility, and mutation services remain unchanged.
  Provider-free active-attempt states, ready-task regression, desktop tray geometry, frontend/UI
  contracts, Ruff, mypy, full CI, deterministic, adapter, packaged-browser, and build checks passed.
  `W44-E1-S3-T16` was the next task and `W44-E1-S3-T17` was Soon; independent stage-strip label clipping at
  1280px remains a separate follow-up, while human usability, Claude/cross-runtime, and Wave 36
  acceptance stay parked.

- `2026-08-24` PR #354 (merge `b3622bde`) completed `W44-E1-S3-T14`: Project Work rows now support
  click/keyboard selection, a reload-safe `inbox_work_item` deep-link, a compact server-owned filter,
  and target-style inspector/table metadata without changing core Inbox grouping/order or mutation
  services. Inbox (`11`), selection/deep-link (`1`), five-viewport matrix (`9`), frontend (`135`),
  UI contracts, Ruff, mypy, packaged JavaScript, deterministic, adapter, packaged-browser, and build
  checks passed. `W44-E1-S3-T15` is now Next; human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-24` PR #352 (merge `e1d77b01`) completed `W44-E1-S3-T8` as a fresh rendered 13-surface
  audit. The provider-free matrix remained clean across five viewports, but the audit confirmed
  four bounded composition gaps: Project Work selected inspector/filter-table, Active Task live
  evidence, Markdown reader first viewport, and Validation Repair hierarchy. `W44-E1-S3-T14` is
  now Next, `W44-E1-S3-T15` is Soon, and T16/T17 remain in the roadmap for subsequent slices;
  Wave 44 is not yet at exit. Human usability, Claude/cross-runtime, and Wave 36 acceptance remain
  parked.

- `2026-08-24` PR #350 (merge `d486e9ae`) completed `W44-E1-S3-T7`: shared Operator tokens now align
  with the target warm canvas/navy rail/cobalt action/mint success/amber warning language and the
  body reading role is 14px. Existing component selectors and routes remain compatible. Focused UI
  contracts (`65`), frontend (`135`), five-viewport matrix (`9`), Ruff, mypy, packaged JavaScript,
  deterministic, adapter, build, and packaged-browser checks passed. `W44-E1-S3-T8` is now Next for
  the fresh 13-surface audit; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #348 (merge `3193e39e`) completed `W44-E1-S3-T13`: Flow Complete now uses the
  existing responsive single-primary action dock, keeping the immutable handoff outcome action
  visible and focusable at `320x568` without changing lineage or mutation semantics. Completion,
  terminal, full five-viewport provider-free, UI contract, frontend, Ruff, mypy, packaged JavaScript,
  deterministic, adapter, build, and packaged-browser checks passed. `W44-E1-S3-T7` is now Next and
  `W44-E1-S3-T8` is Soon; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #346 (merge `f1f51178`) completed `W44-E1-S3-T12`: Review-remediation now lands on
  the authoritative rejected Review quality gate, and its existing durable remediation control is
  visible at all five target viewport sizes. Focused Review/recovery, UI contract, frontend, Ruff,
  mypy, packaged JavaScript, full CI, and build checks passed. The full provider-free matrix then
  exposed a separate Flow Complete first-action gap at `320x568`; `W44-E1-S3-T13` is now Next and
  token alignment `T7` remains Soon behind it.

- `2026-08-24` PR #344 (merge `f693db74`) completed `W44-E1-S3-T11`: the existing Question Decision
  answer action is now a bounded desktop/tablet action dock at all five supported viewport sizes,
  with mobile behavior and answer services unchanged. The five-viewport regression, selected
  durable-answer recovery, frontend/UI contracts, Ruff, mypy, packaged browser, and build checks
  passed. The remaining route audit still shows the Review-remediation registry using the stale
  `remediation-stale` fixture, which renders generic recovery instead of the rejected Review gate;
  `W44-E1-S3-T12` is now Next and token alignment `T7` is Soon behind it.

- `2026-08-24` PR #342 (merge `eeeb1f33`) completed `W44-E1-S3-T10`: Validation Repair now places
  the finding and one eligible recovery action before long evidence, with shrink-safe responsive
  containment at all five target viewports and no horizontal overflow. A fresh matrix audit then
  exposed two independent remaining gaps: the Question Decision action is below the initial
  `768x1024` viewport, and the Review-remediation registry route renders generic recovery instead of
  the authoritative Review quality gate. `W44-E1-S3-T11` is now Next, `T12` is Soon, and token
  alignment `T7` waits on the recovery-surface corrections. Human usability, Claude/cross-runtime,
  and Wave 36 acceptance remain parked.

- `2026-08-24` PR #338 (merge `99da14c9`) completed `W44-E1-S3-T6`: target Create Work Item,
  Runs/Attempts, and Flow Complete compositions are now rendered with existing routes, ids,
  lineage, and immutable handoff semantics preserved. CI passed including packaged UI browser and
  build. The subsequent rendered audit found a stale question-recovery matrix selector and a
  fixed-width Validation Repair preview that clips on mobile and pushes `Run Repair` below the
  first viewport; these are now bounded `T9` and `T10`. `T9` is Next, `T10` is Soon, and token
  alignment/final audit remain planned. Human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-24` PR #340 (merge `c90ede66`) completed `W44-E1-S3-T9`: the provider-free matrix now
  targets the authoritative question, Validation Repair, and Review surfaces instead of the stale
  recovery shell. Existing first-action, focus, diagnostics, and five-viewport assertions were
  preserved; the responsive Validation Repair composition is now the only `Next` task, with token
  alignment in `Soon`. Human usability, Claude/cross-runtime, and Wave 36 acceptance remain
  parked.

- `2026-08-24` PR #336 (merge `e088c50f`) completed `W44-E1-S3-T5`: explicit recovery routes now
  land on authoritative question, validation, and Review finding surfaces; the Decision form and
  durable destination precede generic recovery chrome, mobile hides the dashboard shell, and the
  remediation parity route uses rejected Review evidence. Focused desktop/mobile browser checks,
  Review/QA journey, frontend, provider-free/docs/planning/UI contracts, Ruff, mypy, deterministic,
  adapter, packaged-browser, security, and build checks passed. `W44-E1-S3-T6` is now `Next`, `T7`
  is in `Soon`; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #334 (merge `df6b3f56`) completed `W44-E1-S3-T4`: the Ready-task Task Workspace
  now renders core-owned groups as a dependency-aware table with selected-task route/reload,
  dependency and verification cells, one Run action, one contextual Runner, and factual attempt
  evidence. The deterministic provider-free Ready fixture and task-run route cover desktop/mobile
  geometry, accessibility, diagnostics, and no duplicate launch actions; frontend, docs/planning,
  Ruff, mypy, deterministic, adapter, packaged-browser, security, and build checks passed.
  `W44-E1-S3-T5` is now `Next`, `T6` is in `Soon`; human usability, Claude/cross-runtime, and
  Wave 36 acceptance remain parked.

- `2026-08-24` PR #332 (merge `c7992051`) completed `W44-E1-S3-T3`: the target desktop Project/
  Work Item rail now exposes project identity, deterministic server-owned Work Item selection,
  canonical route intents, and accessible filtering. Shared Work Item id/context and the
  eight-stage strip remain visible on recovery, history, completion, and mobile decision surfaces;
  mobile uses the central Inbox route without a hidden duplicate rail target. Focused browser/UI,
  frontend, docs/planning, Ruff, mypy, deterministic, adapter, packaged-browser, security, and
  build checks passed. `W44-E1-S3-T4` is now `Next`, `T5` is in `Soon`; human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #330 (merge `834b7bfd`) completed `W44-E1-S3-T2`: the fresh 13-surface target
  UX audit is retained in `docs/e2e/w44-e1-s3-t2-target-ux-audit.md`; route/console/request/
  overflow diagnostics are clean, but target shell, task-ready, decision, create/history/
  completion, and token gaps remain open. `W44-E1-S3-T3` is now `Next` and its direct Task
  Workspace successor `T4` is `Soon`. Human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-24` PR #328 (merge `21c71156`) completed `W44-E1-S3-T1`: the provider-free matrix now
  declares which launch, recovery, and completion journeys require an initial-viewport first
  action, while long Task/Markdown surfaces retain controlled scrolling. Focus-order,
  diagnostics, duplicate-primary, geometry, and overflow assertions remain active across all five
  viewports. The mobile recovery fixed action no longer clips at `320px`. Focused browser/UI
  contracts (`9` matrix and `68` UI checks), frontend Node suite (`135 passed`), docs/planning,
  Ruff, mypy, full Python suite (`2430 passed`), deterministic scenarios, adapter conformance,
  packaged UI browser, security checks, and build passed. `W44-E1-S3-T2` is now `Next`; human
  usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #326 (merge `4e50e093`) completed `W44-E1-S2-T3`: the canonical stage strip is
  readable at desktop/tablet density, mobile exposes a keyboard-accessible current-stage summary
  before the expandable eight-stage path, and Task Workspace errors retain Work Item context and
  navigation. Published tasklist evidence is surfaced by the dashboard so missing-prerequisite
  states do not produce false console failures. Focused stage-strip/mobile/route/document checks,
  frontend Node suite (`135 passed`), full Python suite (`2430 passed`), docs/planning, Ruff,
  mypy, deterministic scenarios, adapter conformance, packaged UI browser, security checks, and
  build passed. `W44-E1-S3-T1` is now `Next`; human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-23` PR #324 (merge `69ce00df`) completed `W44-E1-S2-T2`: Documents now retain Work Item
  context and stage navigation while keeping the navigator, reader, and evidence inspector
  co-visible on desktop; selected Task Workspace detail sits beside the authoritative list and
  active-attempt evidence occupies a full-width tray below. Existing routes, DOM ids, read models,
  and mutation services remain unchanged. Focused provider-free geometry and diagnostics at
  `1280x900`/`1440x900`, shell/document/implementation journeys, frontend tests, UI contracts,
  docs/planning, Ruff, mypy, full Python matrix, deterministic scenarios, adapter conformance,
  packaged UI browser, security checks, and build passed. `W44-E1-S2-T3` is now `Next`; human
  usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-23` PR #322 (merge `e3559b97`) completed `W44-E1-S2-T1`: the desktop shell now follows
  the target navy rail, Work Item tabs, stage strip, central canvas, and contextual decision
  column. Empty-inspector read-only/completion surfaces reclaim the reserved column, while rail
  and status-chip colors satisfy the rendered contrast checks and action cards retain usable hit
  targets. Focused desktop shell, Inbox, and terminal Flow Complete browser checks, Ruff, mypy,
  full Python/frontend checks, deterministic scenarios, adapter conformance, packaged UI browser,
  security checks, and build passed. `W44-E1-S2-T2` was the next task and is now complete; `T3`
  is now `Next`. Human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-23` PR #320 (merge `9792d8f5`) completed `W44-E1-S1-T2`: mobile question,
  intervention, approval, and recovery actions stay visible on `320x568` and `390x844` through
  one existing primary control in a safe-area-aware action dock, with no mutation or core
  eligibility changes. Focused mobile browser checks, full frontend tests, docs/planning,
  Ruff, mypy, packaged UI browser, deterministic scenarios, adapter conformance, and build
  passed. `W44-E1-S2-T1` is now `Next`; its direct successor `W44-E1-S2-T2` is `Soon`. Human
  usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-23` PR #318 (merge `0645856b`) completed `W44-E1-S1-T1`: one shared surface policy
  removes global launch/Runner leakage from Inbox, History, generated Documents, and Flow
  Complete, while preserving read-only terminal recommendations and mobile first-viewport
  decision visibility. Focused browser/contract tests, the full frontend suite, docs/planning,
  Ruff, mypy, packaged UI browser, deterministic scenarios, adapter conformance, and build
  passed. Desktop shell composition remained planned; human usability, Claude/cross-runtime, and
  Wave 36 acceptance remain parked.

- `2026-08-23` Wave 44 opened through the queue-restoration policy after a rendered UI audit found
  target-UX gaps despite completed Wave 42–43 functional tasks. `W44-E1-S1-T1` was promoted to
  `Next` and its direct responsive successor `W44-E1-S1-T2` was placed in `Soon`. The first
  bounded fix removes global launch/Runner leakage from non-launch surfaces; shell composition
  and the evidence-led audit loop remain planned in Wave 44. Human usability, Claude/cross-runtime,
  and Wave 36 acceptance remain parked.

- `2026-08-23` PR #315 (merge `29c07782`) completed `W42-E3-S2-T4`: selected Task Workspace
  detail now renders the bounded task contract from server-owned data and keeps exactly one
  Run/Resume/Finalize action beside one contextual Runner, with literal disabled reasons and
  responsive mobile layout. Focused frontend/UI-contract, core/service, planning/docs, Ruff,
  mypy, Task Workspace browser, full CI, and packaged browser checks passed. The Codex-only
  implementation queue is now empty; genuine uncoached human usability, Claude/cross-runtime,
  and Wave 36 acceptance remain explicitly parked.

- `2026-08-23` PR #313 (merge `fa2426a6`) completed `W42-E3-S1-T3`: Task Workspace now publishes
  core-owned Run/Resume/Finalize action states, while the UI service applies current run-lease and
  Runner-readiness guards with literal disabled reasons. The direct selected-task rendering task
  `W42-E3-S2-T4` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-23` PR #311 (merge `d7b13d48`) completed `W42-E7-S2-T4`: mobile recovery now has one
  shrinkable decision column, summary-first primary actions, and honest initial-viewport checks
  for question, validation, and review/remediation journeys. `W42-E3-S1-T3` is now `Next`, with
  its direct Task Workspace UI successor in `Soon`; human usability, Claude, cross-runtime, and
  Wave 36 work remain parked.
- `2026-08-23` UI audit found three Wave 42 mobile browser journeys red despite green packaged
  checks: question recovery, validation repair, and review/remediation clipped or pushed their
  primary action below the initial viewport. `W42-E7-S2-T4` is the bounded responsive remediation;
  human usability, Claude, cross-runtime, and Wave 36 work remain parked.
- `2026-08-22` PR #308 (merge `52943ae2`) completed `W43-E3-S3-T3`: repair briefs now provide one
  deterministic tasklist correction strategy that preserves stable ids and valid cards, names
  the canonical scaffold, patches only affected sections, synchronizes dependencies and
  verification entries, and requires a post-edit re-parse. Focused repair/tasklist,
  resilience/report, docs/planning, Ruff, mypy, deterministic-scenario, adapter-conformance,
  packaged-browser, and build checks passed. The active Codex-only queue is now empty; human
  usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #306 (merge `3825b465`) completed `W43-E3-S3-T2`: tasklist findings now use a
  fail-closed severity matrix, with unreadable grammar and execution-critical card defects at
  `high`, material dependency/verification gaps at `medium`, and safe presentation variants
  accepted without findings. Focused tasklist/task-plan/repair, resilience/report, docs/planning,
  Ruff, mypy, deterministic-scenario, adapter-conformance, packaged-browser, and build checks
  passed. `W43-E3-S3-T3` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work
  remain parked.

- `2026-08-22` PR #304 (merge `59af3079`) completed `W43-E3-S3-T1`: repeated task-card grammar
  failures now collapse into one located root finding while independent dependency findings and
  valid cards remain preserved. Focused semantic/repair, resilience/report, docs/planning,
  Ruff, mypy, deterministic-scenario, adapter-conformance, packaged-browser, and build checks
  passed. `W43-E3-S3-T2` is now `Next`, with `T3` in `Soon`; human usability, Claude,
  cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` The Codex-only audit found that `W43-E3-S3-T1/T2/T3` remain planned in the
  roadmap and are outside the deferred human/Claude scope. `W43-E3-S3-T1` is promoted to
  `Next`, with `T2` in `Soon`; the human observation, Claude/cross-runtime, and Wave 36 lanes
  remain parked.

- `2026-08-22` PR #301 (merge `3f4cf00e`) completed `W43-E5-S2-T2`: three fresh Codex
  AIDD-LIVE-007 repetitions were retained and validated against the pinned profile. All three
  are explicitly `infra-fail` (runaway repository snapshot serialization or no first runtime
  event), so the aggregate report is indeterminate and makes no stability claim. Focused
  repetition/profile tests (11), eval/docs/planning checks (191), Ruff, mypy, full CI, adapter
  conformance, deterministic scenarios, packaged UI browser, and build passed. There is no
  remaining dependency-ready task in the Codex-only queue; human usability, Claude,
  cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #299 (merge `fa75f0e7`) completed `W43-E5-S2-T1`: the Codex-only stability
  lane now has a pinned AIDD-LIVE-007 profile, native runtime/config identity, canonical nine
  metrics, required/conditional evidence inventory, and fail-closed repetition schema checks.
  Focused profile/eval-doctor tests (11), docs/planning/scenario checks (75), Ruff, mypy, and full
  CI passed. `W43-E5-S2-T2` is now `Next`; human usability, Claude, cross-runtime, and Wave 36
  work remain parked.

- `2026-08-22` PR #297 (merge `69e3f214`) completed `W43-E5-S1-T2`: eight provider-free
  repair-extension scenarios now cover successful and repeated-failure grants, manual-fix
  prevalidation, stale evidence, downstream-success and second-grant guards, Request Change
  separation, and immutable history. Reports retain exact grant hashes, attempt modes, budget and
  history accounting, lineage, raw evidence, and explicit no-loop assertions. Focused repair/core/
  eval tests (62), scenario tests (10), docs/scenario/planning tests (113), Ruff, mypy, deterministic
  scenarios, adapter conformance, packaged UI browser, and build passed. `W43-E5-S2-T1` is now
  `Next`; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #295 (merge `17dfbdae`) completed `W43-E5-S1-T1`: ten provider-free
  ownership/interview/tasklist resilience scenarios now assert terminal state, attempt modes,
  repair budget, canonical/workflow records, located findings, raw evidence, and fail-closed
  semantic omissions. The suite includes safe Markdown variants, malformed question resume,
  eleven-card and single-card tasklist failures, root-cause evidence, and non-repair resume
  accounting. Focused eval/failure-corpus/probe/stage-timing/harness tests (71), full Python suite
  (2387), Ruff, mypy, deterministic scenarios, adapter conformance, packaged UI browser, and
  build passed. `W43-E5-S1-T2` is now `Next`; human usability, Claude, cross-runtime, and Wave 36
  work remain parked.

- `2026-08-22` PR #293 (merge `e4eb8a42`) completed `W43-E4-S4-T2`: the operator UI now renders
  one core-eligible `Run one more repair` action, keeps Request Change and Start new run as
  distinct alternatives, validates the exact selected run/stage/runtime before mutation, streams
  the repair-extension attempt, and reads back durable server state. Focused UI/CLI/core/frontend
  tests, docs/planning checks (50), Ruff, mypy, full Python matrix, deterministic scenarios,
  adapter conformance, packaged UI browser, and build passed. `W43-E5-S1-T1` is now `Next` and
  its direct repair-extension successor is `Soon`; human usability, Claude, cross-runtime, and
  Wave 36 work remain parked.

- `2026-08-22` PR #291 (merge `6456124f`) completed `W43-E4-S4-T1`: core/service read models now
  publish repair-extension eligibility and preview evidence with findings, primary cause, automatic
  budget, manual grant usage, exact validator/brief hashes, selected Runner, downstream restriction,
  configuration identity, and literal disabled reasons. Focused repair/frontend/CLI tests (180),
  docs/planning checks (50), Ruff, mypy, full Python matrix, deterministic scenarios, adapter
  conformance, packaged UI browser, and build passed. `W43-E4-S4-T2` is now `Next`; human usability,
  Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #289 (merge `bf556dca`) completed `W43-E4-S3-T2`: the explicit
  `aidd stage repair-extension` command now selects exact work item/run/stage/runtime, previews
  findings and automatic budget, requires confirmation or explicit non-interactive authorization,
  revalidates core configuration/evidence, streams logs, prints durable grant/attempt/evidence
  paths, propagates cancellation, and never schedules an automatic retry. Focused CLI tests (35),
  core repair/stage tests (150), docs/planning checks (50), Ruff, mypy, full Python matrix,
  deterministic scenarios, adapter conformance, packaged UI browser, and build passed.
  `W43-E4-S4-T1` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-22` PR #287 (merge `24d974a2`) completed `W43-E4-S3-T1`: core preflight now fails
  closed on exhausted-stage identity, stale evidence, configuration drift, active jobs, downstream
  success, and duplicate grants. Manual document fixes finalize with a fresh pass report without
  runtime; unresolved findings persist one grant, a bounded `repair-extension` brief, and reopen
  state without altering automatic repair accounting. Focused repair/stage tests (131), docs/planning
  checks (50), Ruff, mypy, full Python matrix, deterministic scenarios, adapter conformance, packaged
  UI browser, and build passed. `W43-E4-S3-T2` is complete; human usability, Claude, cross-runtime,
  and Wave 36 work remain parked.

- `2026-08-22` PR #285 (merge `14147d97`) completed `W43-E4-S2-T2`: repair-extension attempts and
  history are now distinct from automatic repairs, preserving the original budget and exhaustion
  record while counting one durable operator grant; legacy attempt indexes remain readable and
  duplicate grants fail closed. Focused repair-flow tests (70), Ruff, mypy, full Python matrix,
  deterministic scenarios, adapter conformance, packaged UI browser, and build passed. `W43-E4-S3-T1`
  is complete; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #283 (merge `b7485171`) completed `W43-E4-S2-T1`: the durable
  `repair-extension.md` contract now records immutable run/stage identity, validator/brief
  hashes, configuration identity, author, timestamp, and reason. Core eligibility is pure and
  fail-closed for exhaustion-only, stale evidence, configuration drift, intervention, active
  jobs, prior grants, downstream success, identity mismatch, and validation bypass; Request
  Change and new runs remain separate. Focused repair tests (41), harness/package fixture tests
  (48), docs/planning/packaging checks (51), Ruff, mypy, full Python matrix, deterministic
  scenarios, adapter conformance, packaged UI browser, and build passed. `W43-E4-S2-T2` is now
  complete; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #281 (merge `ed3aa1ba`) completed `W43-E4-S1-T2`: repair briefs now group
  primary, related, and advisory evidence, collapse exact duplicates and explicit related
  findings without dropping workspace-relative paths, and keep advisory-only observations
  outside validator verdicts and repair requests. Focused repair/protocol/report tests (88),
  contract/stage/docs/planning checks (161), full Python suite (2344), Ruff, mypy, and full CI
  including deterministic scenarios, adapter conformance, packaged UI browser, and build passed.
  `W43-E4-S2-T1` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-22` PR #279 (merge `893300ce`) completed `W43-E4-S1-T1`: validator contracts and
  core repair planning now separate impact severity from progression impact, require every
  canonical fail finding for progression, and reserve advisory observations for non-verdict
  evidence while retaining protocol-v1 read compatibility. Focused repair/protocol/report tests
  (83), compatibility checks (96), docs/planning checks (50), full Python suite (2339), Ruff,
  mypy, and full CI including deterministic scenarios, adapter conformance, packaged UI browser,
  and build passed. `W43-E4-S1-T2` is now `Next`; human usability, Claude, cross-runtime, and
  Wave 36 work remain parked.

- `2026-08-22` PR #277 (merge `2b9bc9dd`) completed `W43-E3-S2-T2`: task-plan failures now expose
  typed kind, task id, exact source line, field, missing fields, and root/related classification,
  while `TaskPlanParseError` retains compatibility messages. Semantic tasklist findings now use
  the precise issue line. Focused core/validator tests (105), task-plan regression tests (38),
  docs/planning checks (50), full Python suite (2336), Ruff, mypy, full CI, deterministic
  scenarios, packaged UI browser, and build passed; an independent Python 3.12 UI-cancellation
  timing failure passed on rerun. `W43-E4-S1-T1` is now `Next`; human usability, Claude,
  cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` PR #275 (merge `190d1a51`) completed `W43-E3-S2-T1`: the core parser now accepts
  equivalent `-`/`*` list markers, emphasis/backticks around syntactic labels and ids, and
  supported heading separators without inferring missing executable meaning. Canonical and safe
  presentation variants produce equivalent typed task plans; compact/table-like, unsafe,
  duplicate, and incomplete forms remain fail-closed. Focused parser/semantic tests (34),
  docs/planning checks (50), full Python suite (2332), Ruff, mypy, full CI, deterministic
  scenarios, packaged UI browser, and build passed. `W43-E3-S2-T2` is now `Next`; human
  usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #273 (merge `885deee2`) completed `W43-E3-S1-T2`: generated tasklist stage
  briefs now embed one complete canonical H3 card with outcome, deliverable, bounded scope,
  nested acceptance criterion, dependency, and verification examples. The scaffold is available
  without repository-local contract discovery and is explicitly prompt input rather than validated
  output. Focused stage-preparation/stage-runner tests (11), docs/prompt/planning checks (161),
  full Python suite (2331), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser,
  and build passed. `W43-E3-S2-T1` is now `Next`; human usability, Claude, cross-runtime, and Wave
  36 work remain parked.

- `2026-08-21` PR #271 (merge `da566a09`) completed `W43-E3-S1-T1`: tasklist contracts now
  separate required executable semantics from presentation-only Markdown changes, document safe
  emphasis/list-marker equivalence, and keep compact/table-like forms fail-closed. Safe and invalid
  presentation fixtures plus parser/contract tests were added. Focused task-plan/prompt checks
  (30), docs/planning/semantic checks (56), full Python suite (2330), Ruff, mypy, full CI,
  deterministic scenarios, packaged UI browser, and build passed. `W43-E3-S1-T2` is now `Next`;
  human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #269 (merge `11d8e62d`) completed `W43-E2-S2-T3`: the Decision Workbench now
  renders bounded rejected interview candidates with canonical QID state, retained raw evidence,
  source inspection, draft-preserving edit/review focus, resume or Request Change actions, and no
  repair scheduling. Frontend tests (132), UI/docs/planning contracts (102), provider-free mobile and
  desktop browser recovery, full Python suite (2326), Ruff, mypy, full CI, deterministic scenarios,
  packaged UI browser, and build passed. `W43-E3-S1-T1` is now `Next`; its scaffold successor is
  `Soon`; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #267 (merge `13ba2cd9`) completed `W43-E2-S2-T2`: the core operator stage model
  now exposes bounded rejected, accepted, stale, absent, and permission-unavailable interview
  candidate diagnostics, canonical QID context, protected answers, raw candidate evidence, and
  resume-only recovery guidance without frontend Markdown parsing. Focused core/docs/planning tests
  (122), full Python suite (2326), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser,
  and build passed. `W43-E2-S2-T3` is now `Next`; human usability, Claude, cross-runtime, and Wave 36
  work remain parked.

- `2026-08-21` PR #265 (merge `f774b9df`) completed `W43-E2-S2-T1`: `resume` is now a distinct
  non-repair attempt mode in invocation, artifact indexes, stage results, and repair history;
  only explicit validation-triggered `repair` attempts consume the automatic budget, while
  legacy indexes retain their count fallback. Focused core/docs/planning tests, full Python
  suite (2323), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build
  passed. `W43-E2-S2-T2` is now `Next`; `W43-E2-S2-T3` is `Soon`. Human usability, Claude,
  cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #263 (merge `a489b7c7`) completed `W43-E2-S1-T3`: runtime attempts now
  merge questions by stable QID, preserve omitted questions and operator answers, and retain
  rejected question/answer candidates with explicit operator-attention evidence in the attempt
  index without spending repair budget. Focused core/adapter/validator tests (168), Ruff, mypy,
  full CI, deterministic scenarios, packaged UI browser, and build passed. `W43-E2-S2-T1` is now
  `Next`; `W43-E2-S2-T2` is `Soon`. Human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-21` PR #261 (merge `75a14f59`) completed `W43-E2-S1-T2`: runtime question and
  answer candidates now accept only meaning-preserving Markdown normalization, retain raw
  rejected candidates, and fail closed on duplicate or ambiguous QIDs. Focused interview and
  contract tests, Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build
  passed. `W43-E2-S1-T3` is now `Next`; `W43-E2-S2-T1` is `Soon`. Human usability, Claude,
  cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #259 (merge `0dd3e22e`) completed `W43-E2-S1-T1`: interview contracts now
  define exact-QID merge, operator-owned answers, safe presentation normalization, raw rejected
  candidate evidence, omitted-question preservation, and explicit operator attention for
  ambiguous candidates. Worked examples and focused interview/contract tests cover canonical,
  safe, duplicate, ambiguous, and omitted candidates. Full CI, deterministic scenarios, packaged
  UI browser, and build passed. `W43-E2-S1-T2` is now `Next`; `W43-E2-S1-T3` is `Soon`. Human
  usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #257 (merge `6b87d863`) completed `W43-E1-S4-T1`: generic CLI, Qwen, and
  OpenCode completion now settles only on runtime-authored content, excludes AIDD workflow,
  interview, and control records, retains raw stdout/stderr evidence, and leaves canonical
  validation as the progression authority. Adapter tests (270), core stage/registry/preparation
  tests (382), docs/planning/contract tests (51), Ruff, mypy, full CI, deterministic scenarios,
  packaged UI browser, and build passed. `W43-E2-S1-T1` is now `Next`; `W43-E2-S1-T2` is `Soon`.
  Human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #255 (merge `83e3a7ce`) completed `W43-E1-S3-T3`: runtime completion and
  operator intervention now accept only substantive runtime-owned documents; unexpected
  stage-result, validator-report, and repair-brief drafts are retained under attempt evidence,
  indexed with stable keys, and classified as runtime evidence, while canonical records are
  published once. Focused ownership/stage-runner/intervention/frontend tests (209), docs/planning
  tests (50), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.
  `W43-E1-S4-T1` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-21` PR #253 (merge `e2899537`) completed `W43-E1-S3-T2`: stage-result records now
  come from canonical lifecycle state, preserve attempt/repair and project-set evidence, expose
  deterministic validator/blocker/next-action fields, remove runtime `Terminal state notes: TODO`,
  and remain byte-stable across reconciliation. Focused stage-terminal/repair/stage-runner and
  deterministic project-set tests (127), Ruff, mypy, full CI, packaged UI browser, and build
  passed. `W43-E1-S3-T3` is now `Next`; human usability, Claude, cross-runtime, and Wave 36 work
  remain parked.

- `2026-08-21` PR #250 (merge `f198cb8b`) completed `W43-E1-S3-T1`: runtime discovery and
  completion now target substantive content only; canonical validator reports derive from
  current validation findings, and unexpected runtime validator drafts are retained only in
  attempt evidence/artifact index. Focused core/validator/adapter/CLI/docs/planning tests (254),
  Ruff, mypy, full CI, packaged UI browser, and build passed. `W43-E1-S3-T2` is now `Next` and
  `W43-E1-S3-T3` is `Soon`; human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-21` PR #248 (merge `4db5613e`) completed `W43-E1-S2-T2`: stage briefs now separate
  runtime write targets, AIDD-generated records, interview/control documents, and the published
  compatibility view; all eight run prompts prohibit runtime authoring of canonical terminal
  records. Focused ownership/prompt/stage-runner tests (167), docs/planning tests (50), Ruff, mypy,
  full CI, packaged UI browser, and build passed. `W43-E1-S3-T1` is now `Next` and `W43-E1-S3-T2`
  is `Soon`; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` PR #244 (merge `a4d777c4`) completed `W43-E1-S1-T2`: the canonical ownership
  matrix covers all stage-declared documents exactly once, distinguishes runtime-authored content
  from AIDD workflow/control/interview/raw-evidence records, and preserves read-only generated
  Markdown. Focused docs/planning tests (53), Ruff, mypy, and full CI passed. `W43-E1-S2-T1` is
  now `Next`, its direct brief successor is `Soon`; human usability, Claude, cross-runtime, and
  Wave 36 acceptance remain parked.

- `2026-08-21` PR #246 (merge `f9f74bf6`) completed `W43-E1-S2-T1`: typed owner-separated stage
  output projections cover all eight stages, exclude `stage-result.md` and `validator-report.md`
  from runtime targets, and preserve the complete published compatibility reader. Focused registry/
  preparation/runner/workflow tests (116), docs/planning/ownership tests (53), Ruff, mypy, and full
  CI passed. `W43-E1-S2-T2` is now `Next`, with canonical validator generation in `Soon`.

- `2026-08-21` The execution boundary is intentionally Codex-only: the genuine uncoached
  `W42-E7-S2-T3` observation is parked, Claude/dual-provider acceptance is excluded, and the
  fresh Codex `W42-E7-S3-T2` evidence remains retained without claiming the human gate or default-
  renderer cutover. Wave 43 is now opened in dependency order: ownership matrix is `Next` and its
  direct registry successor is `Soon`; cross-runtime and Wave 36 work remain parked.

- `2026-08-21` The fresh clean-main Codex `AIDD-LIVE-007` run
  `eval-live-007-codex-20260821T033606Z` completed all eight stages with execution verdict
  `pass`, matching tasklist/ledger hashes, successful finalization, and Review eligibility.
  `W42-E7-S3-T2` is reconciled as done with retained flow/code/quality reports, checkpoint,
  target verification, and stage audits. `W42-E7-S2-T3` remains explicitly environment-blocked,
  so no Wave 42 exit or Wave 43 promotion is claimed yet.

- `2026-08-21` PR #240 (merge `2db0e886`) completed `W42-E7-S3-T8`; the isolated Codex live
  command enabled the clean task-aware rerun recorded above.

- `2026-08-21` The first clean post-T7 run `eval-live-007-codex-20260821T023047Z` passed `idea`
  with manual audit but stalled before the first `research` runtime event and was interrupted.
  A disposable installed-stage probe with desktop plugins disabled completed `research`; the
  bounded provider-isolation remediation `W42-E7-S3-T8` is promoted to `Next`. Wave 42 remains
  open and no task-aware live pass is claimed.

- `2026-08-21` PR #237 (merge `53208ce7`) completed `W42-E7-S3-T7`: parser punctuation
  normalization and focused tests passed, but fresh run `eval-live-007-codex-20260821T013433Z`
  ended `infra-fail` after Codex made no progress in `idea` for 30 minutes. T7 is removed from
  the queue; `Next`/`Soon` remain empty, the human-observation blocker remains, and Wave 42/43
  are open.

- `2026-08-21` PR #235 (merge `9ff76b3f`) completed `W42-E7-S3-T6`: `/api/tasks` is reachable and
  explanatory prose is no longer parsed as dependency IDs. Fresh Codex run
  `eval-live-007-codex-20260821T003332Z` still failed closed because authored dependency values
  retained terminal punctuation (`T1.`, `none.`); T7 is promoted to `Next`. Wave 42 and Wave 43
  remain open.

- `2026-08-20` PR #233 (merge `fd6922b7`) completed `W42-E7-S3-T5`: the stale readiness error is
  cleared once the installed UI root responds, so the checkpoint now reaches `/api/tasks` and
  retains the successful public projection. Fresh run `eval-live-007-codex-20260820T233552Z`
  instead exposed parser-level `dependency-drift:T1..T4`, so T6 is promoted to `Next`; Wave 42
  and Wave 43 remain open.

- `2026-08-20` The clean Codex rerun `eval-live-007-codex-20260820T222927Z` passed through
  `tasklist` but the installed `/api/tasks` checkpoint again received connection refused on all
  three bounded attempts; direct verification served the same projection. `W42-E7-S3-T5` is added
  and promoted to `Next` as a bounded lifecycle remediation. Wave 42 and Wave 43 remain open.

- `2026-08-20` PR #230 (merge `afc127fc`) completed `W42-E7-S3-T4`. The task checkpoint now
  retries launcher startup, preserves process/attempt diagnostics, and keeps probing `/api/tasks`
  after a launcher exit; focused checkpoint/tasklist tests (11), full live-E2E harness (64),
  docs/planning tests (50), Ruff, mypy, deterministic/adapter checks, security checks, and
  packaged UI browser CI passed. `Next` and `Soon` remain empty pending the fresh Codex live
  rerun and missing eligible human observation; Wave 42 and Wave 43 are not claimed complete.

- `2026-08-20` The clean Codex run `eval-live-007-codex-20260820T210403Z` passed install,
  `idea -> tasklist` stage validation, manual quality audits, target verification, and public UI
  root checkpoints, but the task-aware checkpoint again received connection refused from
  `/api/tasks` immediately after root readiness. T3's bounded retry and diagnostics worked but
  did not solve the UI launcher/server lifetime race, so `W42-E7-S3-T4` is added and promoted to
  `Next` before another live retry. Wave 42 remains open and the human-observation blocker is
  unchanged.

- `2026-08-20` PR #227 (merge `9613b203`) completed `W42-E7-S3-T3`. The installed `/api/tasks`
  probe now has bounded transient retries and fail-closed diagnostics for an unavailable public
  boundary; focused checkpoint/probe tests, the full live-E2E harness suite, Ruff, mypy,
  deterministic/adapter checks, security checks, and packaged UI browser CI passed. `Next` and
  `Soon` remain empty because `W42-E7-S2-T3` still lacks an eligible uncoached human observation;
  the fresh Codex `W42-E7-S3-T2` acceptance is not claimed complete and Wave 43 remains parked.

- `2026-08-20` Two fresh Codex `AIDD-LIVE-007` attempts reached a valid tasklist but both
  fail-closed at the task-aware checkpoint because the installed short-lived `/api/tasks` probe
  returned connection refused. Direct UI verification served the same endpoint, so the bounded
  remediation `W42-E7-S3-T3` is promoted to `Next` to stabilize the public read boundary before
  retrying live evidence. The original human-observation blocker and Wave 42 exit gate remain
  unchanged.

- `2026-08-20` PR #224 (merge `72aee00e`) landed the Wave 42 human-observation contract and
  fail-closed blocker path. No eligible participant was available, so `W42-E7-S2-T3` remains
  `blocked` rather than `done`; its direct successor `W42-E7-S3-T2` is also `blocked`, and both
  are intentionally absent from `Next`/`Soon`. The Wave 42 exit gate and default-renderer
  decision remain gated. Resume with a fresh anonymized participant observation; do not edit the
  blocker record into a pass.

- `2026-08-20` The Codex-only execution plan is now represented in the canonical roadmap. The
  provider-free rehearsal `W42-E7-S2-T2` is explicitly classified as scripted evidence; the new
  `W42-E7-S2-T3` owns the genuine uncoached observation, and `W42-E7-S3-T2` owns the fresh current-
  revision Codex `AIDD-LIVE-007` run with task-aware checkpoints. Wave 43 E5-S2 now measures Codex
  stability through three repetitions; the original cross-runtime comparison is parked as
  `W43-E5-S2-T3`. Claude, dual-provider, and Wave 36 beta tasks remain out of scope.

- `2026-08-20` `W43-E1-S1-T1` is complete in PR #221 (merge `3862b114`). The evidence-only
  failure corpus is sanitized and provider-free: five replayable cases retain runtime, stage,
  attempt mode, first decisive boundary, primary/related findings, and automatic repair-budget
  consumption. Existing interview, placeholder, rich-tasklist, validator-report, and
  repair-budget paths replay the declared signals with fail-closed manifest/path/credential
  checks. Functional Wave 43 remains gated on the unreconciled Wave 42 exit evidence, so
  `W43-E1-S1-T2` is parked and `Next` is intentionally empty; no ownership behavior is changed.

- `2026-08-20` `W42-E7-S3-T1` is complete in PR #219 (merge `754e6d7c`). Rich task-aware live
  flows now publish schema-v1 JSON/Markdown checkpoints after validated tasklist publication and
  aggregate Implement finalization. The runner reconciles the installed `/api/tasks` projection
  with authorized tasklist, ledger, attempt, and finalization artifacts, preserving run/revision
  identity, dependencies, statuses, attempts, evidence links, next-ready selection, finalization,
  and Review eligibility; hash drift, missing evidence, invalid readiness, premature finalization,
  or eligibility disagreement fail closed. Placeholder legacy tasklists remain outside this lane.
  `W43-E1-S1-T1` is promoted to `Next` as the evidence-only follow-on; functional Wave 43 work
  remains gated on Wave 42 exit evidence.

- `2026-08-20` `W42-E7-S2-T2` is complete in PR #217 (merge `b1bf2b23`). The one-session
  provider-free rehearsal now records the ordered create -> Runner -> launch -> answer -> resume
  journey with per-step elapsed time, durable outcomes, wrong-action/assistance/confusion fields,
  explicit routing decision, accessibility/geometry/one-primary-action checks, and a fail-closed
  `wave42-first-time-operator-journey-v1` evidence contract. It is explicitly labelled a scripted
  rehearsal rather than human usability evidence; missing external runtime is environment-blocked.
  `W42-E7-S3-T1` is now the only Next task.

- `2026-08-20` `W42-E7-S2-T1` is complete in PR #215 (merge `101a1f38`). Wave 42 now has a
  declarative `wave42-responsive-browser-matrix-v1` registry covering eight journeys across
  `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`, with provider-free canonical
  routes, first-action bounds, accessibility/geometry checks, diagnostics, screenshots, and
  bounded cleanup evidence. The matrix passed locally and in packaged UI CI; Flow Complete
  evidence no longer creates nested scroll owners. `W42-E7-S2-T2` is now the only Next task.

- `2026-08-20` `W42-E7-S1-T2` is complete in PR #213 (merge `85e72ec9`). Operator UI shared
  primitives now publish a shared-v1 interaction contract for loading, empty, partial, error,
  disabled, selected, pending, conflict, success, offline, reconnecting, permission-denied,
  focus, and keyboard states. State surfaces expose semantic role/live/busy metadata and visible
  status text; primary action slots are explicitly marked and constrained to one action. Frontend,
  CLI contract, browser accessibility/geometry, docs consistency, planning, Ruff, mypy, packaged
  JavaScript, full CI, packaged browser, and build checks passed. `W42-E7-S2-T1` is now the only
  Next task.

- `2026-08-20` `W42-E7-S1-T1` is complete in PR #211 (merge `dfdee03f`). The packaged Operator UI
  now has a separate Wave 42 provider-free route registry for all 13 target references, mapping
  each filename to a deterministic local query and materializable fixture without credentials,
  provider processes, wall-clock state, or random ids. The registry remains separate from the
  historical Wave 36 journey ids. Manifest, fixture, UI asset, docs consistency, planning,
  frontend, Ruff, mypy, packaged-JS, full CI, packaged browser, and build checks passed.
  `W42-E7-S1-T2` is now the only Next task.

- `2026-08-20` `W42-E6-S2-T1` is complete in PR #209 (merge `7398c13f`). Flow Complete now
  exposes delivered scope, verification, repository state, QA result, run ids, retained evidence,
  known limitations, and core-recommended next outcomes while preserving immutable source-run
  lineage and hiding Runner on terminal/read-only surfaces. Frontend/UI contract checks, focused
  five-viewport terminal browser coverage, Ruff, mypy, full CI, packaged browser acceptance, and
  build passed. `W42-E7-S1-T1` is now the only Next task.

- `2026-08-20` `W42-E6-S1-T1` is complete in PR #207 (merge `118c8c23`). Runs and Attempts now
  expose a bounded Work Item run list, retained attempt metadata, durable timeline events,
  artifacts, hashes, copy ids, lineage, filters, and compare gating without a Runner selector
  on read-only History. Core timeline/service tests, frontend tests, UI contracts, Ruff, mypy,
  five-viewport browser History journeys, and full CI passed. `W42-E6-S2-T1` is now the only Next
  task.

- `2026-08-20` `W42-E5-S2-T2` is complete in PR #205 (merge `1b728c2f`). Review and QA now
  expose selectable findings and risks with exact source evidence, durable browser-session
  remediation drafts, Markdown Write/Preview destinations, and guarded return-to-Implement
  launches. Existing stale downstream readback and rerun semantics remain authoritative;
  generated stage documents stay read-only. Frontend fixtures, UI contracts, focused review/QA
  browser journeys, full frontend tests, Ruff, mypy, and CI (including packaged browser
  acceptance) passed. `W42-E6-S1-T1` is now the only Next task.

- `2026-08-20` `W42-E5-S2-T1` is complete in PR #203 (merge `ef12aae9`). Implementation Review
  now exposes repository-truth changed files and unified diffs together with completed ledger
  claims, actual verification commands/results, residual risks, and allowed/project-set scope
  coverage. Generated stage documents remain read-only. Frontend fixtures, UI contracts, focused
  Implementation browser journeys, full frontend tests, Ruff, mypy, and CI (including packaged
  browser acceptance) passed. `W42-E5-S2-T2` is now the only Next task.

- `2026-08-20` `W42-E5-S1-T2` is complete in PR #201 (merge `377b2c6f`). Validation and
  runtime recovery now render as distinct Decision Workbench states: validation exposes exact
  document/rule/location/budget evidence with repair routing, while runtime exposes the first
  decisive failure, logs, retry, and cancel without consuming validation repair budget. Focused
  frontend/UI contract tests, Ruff, mypy, Python matrix, deterministic/adapter checks, packaged
  browser acceptance, and build passed. `W42-E5-S2-T1` is now the only Next task.

- `2026-08-11` Wave 43 is planned as the runtime-neutral validation and repair resilience track.
  It separates runtime content from AIDD-owned workflow records, protects canonical interview
  ledgers, makes rich-tasklist grammar and diagnostics workable for lower-capability runtimes,
  aligns fail findings with required repair corrections, and adds one audited operator-authorized
  repair extension after automatic exhaustion. Ownership, QID merge, attempt accounting,
  progression-required repair, and one-extension invariants are frozen in target architecture;
  the remaining tasks implement and verify them across contracts, core, adapters, validators,
  CLI, frontend, scenarios, and comparative evals. Wave 42 remains the active queue; only evidence
  task `W43-E1-S1-T1` is parked and ready so the new track does not silently displace the active
  Wave 42 Inbox work.

- `2026-08-11` Wave 42 is accepted as the task-centered Operator UI correction. Its normative
  contract defines `Project -> Work Item -> Stage -> Task/Decision -> Run/Attempt ->
  Document/Evidence`, contextual Runner placement, controlled Markdown authoring, read-only
  generated documents, Work Item/Runner/Task state matrices, compatibility/cutover boundaries,
  schema-v1 task-flow live evidence, 13 target screens, and responsive acceptance. Contract and
  visual-authority tasks `W42-E1-S1-T1` and `W42-E1-S2-T1` are complete. The next implementation
  vocabulary correction `W42-E2-S1-T1` and core-owned attention groups `W42-E2-S1-T2` are
  complete with compatibility identifiers preserved; `W42-E2-S1-T4` now renders the canonical
  Inbox groups, all empty group states, and one selected Work Item inspector action; `W42-E2-S1-T3`
  is complete with Work Item tabs, route persistence, and the exact eight-stage strip. `W42-E2-S2-T1`
  is now next.

- `2026-08-13` `W42-E2-S2-T2` is complete and `W42-E3-S1-T1` is now the only Next task. The
  contextual Runner control is reused beside workflow, stage, task, repair, and remediation
  launches; it mirrors core eligibility and literal disabled reasons, keeps read-only/history/
  completion surfaces selector-free, forwards readiness identity, and service-revalidates before
  mutation. PR #178 merged as `f0cf3c8b`; focused UI/service tests, full frontend tests, CI, and
  packaged browser acceptance passed. T1 was reconciled in PR #177 (`eaa694fa`).

- `2026-08-13` `W42-E3-S1-T1` is complete in PR #180 (merge `eb6bd55f`). The core Task
  Workspace projection now publishes deterministic Ready/Running/Blocked/Done groups,
  dependency graph, next-ready and advisory critical-path signals, attempts, durable events,
  evidence links, preserved successes, and explicit finalization/review eligibility while
  retaining fail-closed tasklist hash drift behavior. Focused task/CLI tests, full UI CLI tests,
  Ruff, mypy, CI Python matrix, deterministic/adapter checks, and packaged browser acceptance
  passed. `W42-E3-S1-T2` is now the only Next task.

- `2026-08-13` `W42-E3-S1-T2` is complete in PR #182 (merge `66c306bf`). The UI service now
  exposes bounded `task_list` navigation payloads and selected-task detail over the existing
  ledger/evidence read model, rejects unknown task ids explicitly, and returns server-winner
  task views after task and finalization mutations. Legacy rich `tasks` payloads remain intact.
  Focused and full UI tests, characterization tests, Ruff, source mypy, CI matrix, deterministic/
  adapter checks, and packaged browser acceptance passed. `W42-E3-S2-T1` is now the only Next task.

- `2026-08-13` `W42-E3-S2-T1` is complete in PR #184 (merge `f358e347`). The Work Item Tasks
  surface now renders core-owned Ready/Running/Blocked/Done groups without browser sorting or
  status mutation, supports bounded search, deterministic selection, next-ready and critical
  path markers, and persists selected task identity in canonical `task_id` deep links. 117 Node
  frontend tests, 156 Python UI/asset tests, CI matrix, deterministic/adapter checks, and
  packaged browser acceptance passed. `W42-E3-S2-T2` is now the only Next task.

- `2026-08-13` `W42-E3-S2-T2` is complete in PR #186 (merge `ff0025c8`). Selected task detail
  now shows outcome, dependencies, blocker, and core-owned status, with exactly one eligible
  Run, Resume, or Finalize action routed through the existing guarded mutation services. Running,
  Blocked, and Done tasks do not receive a fabricated launch action. 117 Node frontend tests,
  50 Python UI asset tests, CI matrix, deterministic/adapter checks, and packaged browser
  acceptance passed. `W42-E3-S2-T3` is now the only Next task.

- `2026-08-13` `W42-E3-S2-T3` is complete in PR #188 (merge `dfe764fb`). The Tasks surface
  now exposes active attempt identity, factual elapsed time, last-output age, durable milestone,
  cancellation state, connection/reconnect cursor, and collapsible raw output from the existing
  UI job evidence without percentage estimates. Focused Node/static tests, CI matrix,
  deterministic/adapter checks, and packaged browser acceptance passed. `W42-E4-S1-T1` is now
  the only Next task; `W42-E6-S1-T1` remains a parallel planned direction.

- `2026-08-13` `W42-E4-S1-T1` is complete in PR #190 (merge `6a5fdc3a`). The read-only
  Markdown workspace now groups Output, Questions, Validation, Inputs, and Evidence while
  showing filename, role, stage/attempt, freshness, bounded state, source of truth, heading
  map, rendered content, and copy/open-folder utilities. Missing, malformed, permission-denied,
  empty, and truncated copies expose one truthful safe action without adding generated-document
  editing. Core/frontend focused tests, full UI asset contracts, all Python matrix checks, and
  packaged browser acceptance passed. At that point, `W42-E4-S1-T2` was the only Next task.

- `2026-08-13` `W42-E4-S1-T2` is complete in PR #192 (merge `9566147b`). Source renders exact
  bounded lines, retained comparison is available only for a named earlier attempt, and heading,
  line, finding, and related-evidence anchors preserve browser history without synthetic versions
  or generated-document editing. The full Python/frontend matrix and packaged browser journeys
  passed after correcting the one-attempt fixture to assert disabled Compare. `W42-E4-S2-T1` was
  then completed in PR #193 (merge `5877a0d5`): operator-owned request Markdown now has a durable
  Preview/Write path, exact readback and destination, browser-session draft editing, and a
  core/service fail-closed consumed-input boundary that routes later changes to revision or
  intervention. Focused request-context tests, UI asset contracts, full frontend tests, Python
  matrix, deterministic/adapter checks, and packaged browser acceptance passed. `W42-E4-S2-T2`
  is now the only Next task.

- `2026-08-13` `W42-E4-S2-T2` is complete in PR #195 (merge `b4176882`). Answers now support
  resolved/partial/deferred resolution, question context, evidence links, unblock consequence,
  browser-session drafts, non-mutating `answers.md` Preview, and durable Write/readback through
  the existing answer service. Invalid QIDs and resolution values fail closed; focused core/CLI
  tests, 123 frontend tests, full Python matrix, deterministic/adapter checks, and packaged
  browser acceptance passed. `W42-E4-S2-T3` is now the only Next task.

- `2026-08-13` `W42-E4-S2-T3` is complete in PR #197 (merge `cf32894d`). Intervention,
  remediation, follow-up, and clone drafts now share purpose-aware identity/state helpers while
  preserving their existing forms, routes, destinations, and runtime-generated-document
  read-only boundary. Source-evidence selection, destination metadata, draft isolation, and
  durable-purpose status are retained in the browser-session draft layer. Focused draft/static
  tests, 124 frontend tests, full Python matrix, deterministic/adapter checks, packaged browser
  acceptance, and package build passed. `W42-E5-S1-T1` is now the only Next task.

- `2026-08-13` `W42-E5-S1-T1` is complete in PR #199 (merge `ccb2748c`). Questions and
  approvals now share a Decision Workbench composition that exposes decision type, reason,
  source snippets, consequence, schema-specific inputs, retained evidence, and one primary
  submit action while preserving separate question and approval workflows. Empty optional
  answer fields remain omitted for API compatibility. Focused UI/contract tests, 125 frontend
  tests, full Python matrix, deterministic/adapter checks, packaged browser acceptance, and
  package build passed. `W42-E5-S1-T2` is now the only Next task.

- `2026-08-12` `W42-E2-S1-T3` is complete. Work Item Overview/Tasks/Documents/Runs tabs now
  persist through canonical routes, keyboard focus, and reload; the active shell renders the
  exact eight stages grouped as Understand, Decide, Deliver, and Prove with retained status and
  stale semantics. Tasks and Runs expose bounded honest placeholders until their owning slices;
  existing evidence/history routes remain readable. Frontend `113`, focused browser route/stage
  `15`, UI CLI `153`, Ruff, and mypy passed. `W42-E2-S2-T2` is now Next.

- `2026-08-10` W40-E1-S4 (including T3), W41-E1-S2, and W36-E7-S4-T94 are complete. The packaged UI uses one
  `operatorWorkspace` scroll owner with Intent context, a four-phase stepper, one current
  decision surface, document content, and a technical-details disclosure. Legacy rail/sidebar/
  dock DOM and responsive rules were removed. User-facing copy uses `Intent`; canonical
  `work_item`/run/stage lineage remains technical. Dynamic form/action IDs, routes, API payloads,
  workflow semantics, and artifact ownership are unchanged. Frontend/static contracts pass;
  the browser matrix passes 192/192 cases across 47 modules at the supported viewport sizes;
  Ruff, mypy, and diff checks are clean. The required Codex live lane used `gpt-5.6-luna` with
  `reasoning_effort=high` and completed all eight stages through QA with status `pass` and zero
  findings. QA verification-summary and readiness bullets now carry retained `EV-N` evidence
  references; the rerun closed the prior `CROSS-QA-UPSTREAM-EVIDENCE` gap without changing
  runtime, workflow, API, or canonical work-item semantics. A live-intervention browser race was
  also closed: a new job no longer requests its artifact index before the first durable attempt
  exists. The canonical live bundle is retained outside the source checkout for audit.

- `2026-08-04` Wave 39 UI selector slice is complete. The local operator shell exposes
  capability-gated model and reasoning-effort controls, UI stage/workflow payloads omit
  blank values, and selected values reach the shared runtime request path with immutable
  `ui-selection` provenance. Frontend 13/13, stage-run 30/30, UI 100/100, Ruff, and mypy pass.

- `2026-08-04` Wave 38 is complete. Typed `model` and `reasoning_effort` selectors are
  capability-gated, Codex-specific mapping is covered for subprocess and app-server paths,
  run snapshots record requested values and `runtime-config`/`runtime-default` provenance,
  and resume rejects selection drift. The generated Codex live profile uses
  `gpt-5.6-luna` with `high`; other runtimes retain native defaults. Full pytest passes
  `2188/2188`, Ruff and mypy pass, and no provider-authenticated live scenario ran.
- `2026-08-04` `W41-E1-S1-T1` is complete. The Document & Evidence Studio and Artifact
  Workbench now put a role/freshness/decision-use brief ahead of the document, keep supporting
  evidence in explained disclosures, and give each validation, requirement, and retained-version
  row an item-level **Why**. Historical evidence is visibly stale, retained-copy comparison is
  honest, and reader document links preserve the Studio context and canonical route on reload.
  Frontend `107`, UI CLI `155`, focused browser `14`, Ruff, and mypy passed.

- `2026-08-04` `W40-E1-S1-T1`, `W40-E1-S2-T1`, and `W40-E1-S3-T1` are complete. Existing
  project launches now start in Inbox, explicit Studio links restore their selected work item,
  new work is independent from runtime selection, and the packaged UI presents factual progress
  with a single next action. Focused CLI/frontend and desktop/mobile browser verification passed.

- `2026-08-03` `W36-E7-S4-T93` is complete. The CodeQL-reported shell compound-evidence
  expression now makes command-substitution and plain assignment alternatives disjoint and uses
  a possessive assignment prefix, removing exponential backtracking without changing accepted
  legitimate commands. The 128-part
  scanner-shaped regression terminates under a two-second guard and is rejected as unverifiable;
  focused validator/planning tests pass `42/42`, with Ruff and mypy clean. This is a bounded
  release security correction after the counted-clean T3 candidate; it does not claim a new live
  provider run.

- `2026-08-03` `W36-E7-S4-T3` is complete. Fresh Codex run
  `eval-live-007-codex-20260803T205243Z` used exact candidate `ae3131a`, tree `696633d`,
  byte-fixed wheel digest `2b3e481`, and Hono pin `cf2d2b7`. All eight stages and manual
  stage-quality audits completed; Vitest passed `236/236`, `tsc --noEmit` passed, and terminal
  Chromium inspection found no console error or horizontal overflow. The derived acceptance is
  execution-pass, quality-reviewed, and counted-clean. The sealed 469-file bundle tree digest is
  `a127580` and readback succeeds without the mutable work path. Sanitized evidence is in
  `docs/e2e/live-e2e-codex-acceptance-2026-08-03-post-t91.md`. Claude, human, and dual-provider
  beta gates remain parked and are not part of the Codex-only alpha release claim.

- `2026-08-03` `W36-E7-S4-T92` is complete on exact candidate `ae3131a`, tree `696633d`,
  tracked archive digest `aecf4e4`, and byte-repeatable wheel digest `2b3e481`. Ruff, mypy,
  Python `2179/2179`, focused validator/planning `55/55`, isolated install/doctor/eval-doctor,
  private-auth Seatbelt readiness, fresh Hono setup with Vitest `233/233` and `tsc --noEmit`,
  clean target diff, and source postflight pass. Browser code is unchanged and retains post-T81
  Chromium `188/188`. Evidence is in `docs/e2e/candidate-readiness-2026-08-03-post-t91.md`;
  T3 is `Next`.

- `2026-08-03` `W36-E7-S4-T91` is complete. Dependency objects are scoped to their individual
  relation spans, and the exact terminal plan now yields the authored acyclic graph without the
  invented reverse edges that exhausted tasklist repair. Focused validator/planning tests pass
  `55/55`, Ruff and mypy pass, and full pytest passes `2179/2179`. T92 is `Next`; T3 remains
  parked until the replacement candidate is recorded.

- `2026-08-03` the post-T90 Codex run passed private auth, target readiness, and manual quality
  audits through `review-spec`. Tasklist then exhausted repair because the dependency parser
  treated both milestone references following the first relation in a mixed-relation sentence
  as prerequisites, inventing `M2/M3 -> M4` in addition to the authored `M4 -> M2/M3` edges.
  The terminal root is not resumed; T91 is `Next`, T92 and a fresh T3 follow.

- `2026-08-03` `W36-E7-S4-T90` is complete on exact candidate `5a53614`, tree `b1877a8`,
  tracked archive digest `143e406`, and byte-repeatable wheel digest `e057790`. Ruff, mypy,
  Python `2178/2178`, validator/prompt/scenario/planning `432/432`, exact terminal QA
  revalidation, bundle/manifest/session/isolation/auth `52/52`, isolated install/doctor/
  eval-doctor, fresh Hono readiness with Vitest `233/233` and `tsc --noEmit`, private Codex auth,
  Seatbelt isolation, and source postflight pass. Browser code is unchanged and retains
  post-T81 Chromium `188/188`. Evidence is in
  `docs/e2e/candidate-readiness-2026-08-03-post-t89.md`; T3 is `Next`.

- `2026-08-03` `W36-E7-S4-T89` is complete. QA-local `EV-N` definitions are accepted only when
  they contain a syntactically executable command and explicit terminal outcome; upstream claims
  still require exact ids or existing full workspace-relative artifact paths. The exact terminal
  post-T88 QA report revalidates from eight blocking occurrences to zero, the focused
  validator/prompt/scenario/planning group passes `432/432`, Ruff and mypy pass, and full pytest
  passes `2178/2178`. Historical candidate `7726023` remains invalid; T90 is `Next`, T3 is `Soon`.

- `2026-08-03` the post-T88 Codex run completed quality-audited `idea` through `review`; its
  four-file Hono patch passed focused Vitest `234/234`, `tsc --noEmit`, Implement, and independent
  Review. QA exhausted document repair because `CROSS-QA-UPSTREAM-EVIDENCE` rejects bounded
  QA-local command evidence even though the QA contract requires post-QA residue and artifact
  checks. The terminal root is not resumed. T89 aligns the contract and validator without
  weakening upstream artifact traceability; T90 then replaces historical candidate `7726023`.

- `2026-08-03` `W36-E7-S4-T88` is complete on exact candidate `7726023`, tree `1f89bd2`,
  tracked archive digest `9a9cf26`, and wheel digest `29b43f7`. Ruff, mypy, exact-candidate
  Python `2175/2175`, validator/prompt/packaging/planning `382/382`, saved terminal Implement
  revalidation, bundle/manifest/isolation `29/29`, isolated install/doctor/eval-doctor, fresh
  Hono readiness with Vitest `233/233` and `tsc --noEmit`, private Codex auth, Seatbelt isolation,
  and source postflight pass. Browser code is unchanged and retains post-T81 Chromium `188/188`.
  Evidence is in `docs/e2e/candidate-readiness-2026-08-03-post-t87.md`; T3 is `Next`.

- `2026-08-03` the post-T86 Codex run passed private auth, target readiness, and manual audits
  through `tasklist`. Implement T1 added only the intended `src/compose.test.ts` red regression,
  with Vitest truthfully reporting the expected pre-runtime-change failure and `tsc` passing, but
  validation exhausted repair on a complete command list shaped as
  `found=$(find ...); if ...; fi; test ...`. T87 now recognizes only closed compound lists with
  concrete executables; the saved terminal report revalidates with zero findings and focused tests
  pass `32/32`. The terminal root is not resumed; T88 is `Next` and T3 is `Soon`.

- `2026-08-03` `W36-E7-S4-T86` is complete on exact candidate `4b2856f`, tree `9137bc3`,
  tracked archive digest `c8769e7`, and wheel digest `f9e9f98`. Ruff, mypy, exact-candidate
  Python `2174/2174`, validators `298/298`, saved terminal Implement revalidation,
  bundle/manifest/isolation `29/29`, isolated install/doctor/eval-doctor, fresh Hono readiness
  with Vitest `233/233` and `tsc --noEmit`, private Codex auth, Seatbelt isolation, and source
  postflight pass. Browser code is unchanged and retains the accepted post-T81 Chromium `188/188`
  gate. Evidence is in `docs/e2e/candidate-readiness-2026-08-03-post-t85.md`; T3 is `Next`.

- `2026-08-03` the post-T84 Codex run passed isolated auth, exact-wheel target readiness, and
  manual quality audits through `tasklist`. Implement T1/T2 succeeded and T3 produced a bounded
  three-file patch with focused Vitest `234/234` and `tsc --noEmit` passing, but the Implement
  validator rejected a complete backticked shell `if ...; then ...; else ...; fi` residue check
  as non-executable evidence. T85 now recognizes only syntactically complete compound checks
  containing a concrete executable; the saved terminal report revalidates with zero findings and
  focused tests pass `31/31`. The terminal root is not resumed; T86 is `Next` and T3 is `Soon`.

- `2026-08-03` `W36-E7-S4-T84` is complete on exact candidate `912f444`, tree `5fb8486`,
  tracked archive digest `3260f35`, and wheel digest `4e1fe07`. Ruff, mypy, Python `2172/2172`,
  validators `296/296`, saved terminal QA revalidation, bundle/manifest/isolation `29/29`,
  isolated install/doctor/eval-doctor, fresh Hono readiness with Vitest `233/233` and
  `tsc --noEmit`, private Codex auth, Seatbelt isolation, and source postflight pass. The browser
  code is unchanged and retains the accepted post-T81 Chromium `188/188` gate. Evidence is in
  `docs/e2e/candidate-readiness-2026-08-03-post-t83.md`; T3 is `Next`.

- `2026-08-03` the post-T82 Codex run reached QA with all prior stage quality audits accepted,
  the four-file Hono patch passing focused Vitest `237/237` and `tsc --noEmit`, and Review
  approved. QA then exhausted repair because cross-document validation rejected QA-local
  `EV-N` references even when their definitions contained full existing upstream/context paths,
  contradicting the QA document contract and prompt. The terminal root is not resumed;
  `W36-E7-S4-T83` is `Next`, T3 is `Soon`, and candidate `09b8d6a` is historical.

- `2026-08-03` `W36-E7-S4-T82` is complete for the active Codex-only prerelease scope on exact
  candidate `09b8d6a`, tree `8bba6dd`, tracked archive digest `9f10c8b`, and wheel digest
  `6db06bc`. T81 Ruff, mypy, and Python `2170/2170`, exact-SHA Chromium `188/188`, focused
  bundle/manifest/isolation `29/29`, isolated install/doctor, Codex eval-doctor, fresh Hono
  readiness with Vitest `233/233` and `tsc --noEmit`, private Codex auth, Seatbelt isolation,
  and source postflight pass. Evidence is in
  `docs/e2e/candidate-readiness-2026-08-03-post-t81.md`; T3 is `Next`, and no live evaluator ran
  during T82.

- `2026-08-03` `W36-E7-S4-T37` is complete for the active Codex-only scope on exact candidate
  `4880ea4`, tree `3ec3904`, tracked archive digest `cca520a`, and wheel digest `300bf16`.
  Ruff, mypy, Python `2170/2170`, exact-SHA Chromium `188/188`, isolated install/doctor, Codex
  eval-doctor, fresh Hono readiness with Vitest `233/233` and `tsc --noEmit`, installed bundle
  deletion/readback, private Codex auth, Seatbelt isolation, and source postflight all pass.
  Sanitized evidence is in `docs/e2e/candidate-readiness-2026-08-03-post-t80.md`. T3 is `Next`;
  Claude and large lanes remain parked, and no live evaluator ran during T37.

- `2026-08-03` the post-T80 `W36-E7-S4-T36` rerun is complete on clean source `403129a`
  and tree `fe3bd4c`: historical cases pass `4/4`, intervention/terminal families `24/24`,
  packaged journeys pass `79/79` with exact discovered/executed parity and `failed_ids=[]`, and
  one fresh uninterrupted full Chromium suite passes `188/188`. All five viewports complete
  without console, page, failed-request, overflow, accessibility, or process-cleanup failure;
  process preflight and postflight are empty. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t80.md`. T37 is `Next`,
  Codex T3 remains parked, and no provider or large scenario ran.

- `2026-08-03` `W36-E7-S4-T80` is complete: Stage Result semantic validation reads only
  canonical leading attempt identities and no longer counts `attempt-000N/...` evidence-path
  references as duplicate attempts. The live-shaped positive case and duplicate negative case
  pass; focused validator/core checks pass `393/393`, planning integrity passes `9/9`, Ruff and
  mypy across `228` modules pass, and full pytest passes `2170/2170`. T36 is `Next`, T37 is
  `Soon`, and Codex T3 remains parked until the replacement candidate is accepted.

- `2026-08-03` the post-T79 Codex T3 attempt on candidate `abbc4d6` passed private auth,
  target readiness, exact-wheel identity, and strong manual audits through `tasklist`.
  Implement completed three provider attempts with exit `0`, kept the target diff inside the
  authored scope, and passed focused Vitest `233/233` plus `tsc --noEmit`, but Stage Result
  semantic validation counted each `attempt-000N/...` evidence-path reference as a second
  attempt identity and exhausted repair on a false non-increasing sequence. The terminal root
  will not be resumed; `W36-E7-S4-T80` is `Next`, T36 is `Soon`, and the candidate is historical.

- `2026-08-03` `W36-E7-S4-T37` is complete for the active Codex-only scope on exact
  candidate `abbc4d6`, tree `bc10c57`, tracked archive digest `93a46bc`, and wheel digest
  `78f4d11`. Ruff, mypy, Python `2168/2168`, exact-SHA Chromium `188/188`, isolated
  install/doctor, Codex eval-doctor, fresh Hono readiness with Vitest `233/233` and
  `tsc --noEmit`, bundle seal/readback after mutable-root deletion, private-auth readiness,
  standalone Seatbelt capability canary, and source postflight all pass. Sanitized evidence is
  in `docs/e2e/candidate-readiness-2026-08-03-post-t79.md`. T3 is `Next`; Claude and large lanes
  remain parked, and no live evaluator ran during T37.

- `2026-08-03` the post-T79 `W36-E7-S4-T36` rerun is complete on clean source `c040f0e`
  and tree `75fe019`: historical cases pass `4/4`, intervention/terminal families `24/24`,
  packaged journeys pass `79/79` with exact discovered/executed parity and `failed_ids=[]`, and
  one fresh uninterrupted full Chromium suite passes `188/188`. All five viewports complete
  without console, page, failed-request, overflow, accessibility, or process-cleanup failure;
  the final process postflight is empty. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t79.md`. T37 is `Next`, Codex
  T3 is `Soon`, and no provider or large scenario ran.

- `2026-08-03` `W36-E7-S4-T79` is complete: aggregate Implement finalization now preserves
  task-local executable evidence from canonical `## Verification` and falls back to legacy
  `## Verification notes`. Re-rendering the saved six-task post-T78 ledger produces `62` backed
  evidence lines and `48` outcome claims instead of zero. Focused checks pass `3/3`, the broader
  implementation/harness group passes `120/120`, Ruff and mypy across `228` modules pass,
  planning integrity passes `9/9`, and full pytest passes `2168/2168`. T36 is `Next`, T37 is
  `Soon`, and Codex T3 remains parked until the replacement candidate; no provider ran for T79.

- `2026-08-03` the post-T78 Codex T3 attempt on candidate `ead6dab` passed isolated auth,
  exact-wheel identity, target readiness, and strong manual audits through `tasklist`. Implement
  completed T1-T6, retained exactly the four allowed Hono paths, and passed canonical validation,
  focused Vitest, and `tsc --noEmit`. The live audit then failed closed because aggregate
  finalization copied only legacy `## Verification notes` and dropped task-local executable
  evidence authored under canonical `## Verification`. The terminal root is not resumed; T79 is
  `Next`, T36 is `Soon`, and T37/T3 remain parked until a replacement candidate exists.

- `2026-08-03` `W36-E7-S4-T37` is complete for the active Codex-only scope on exact
  candidate `ead6dab`, tree `cfbc108`, tracked archive digest `9d87bfd`, and wheel digest
  `dc11248`. Ruff, mypy, Python `2168/2168`, exact-SHA Chromium `188/188`, isolated
  install/doctor, Codex eval-doctor, fresh Hono readiness with Vitest `233/233` and
  `tsc --noEmit`, bundle seal/readback after mutable-root deletion, private-auth readiness,
  standalone Seatbelt visibility canary, and source postflight all pass. Sanitized evidence is
  in `docs/e2e/candidate-readiness-2026-08-03-post-t78.md`. T3 is `Next`; Claude and large
  lanes remain parked, and no live evaluator ran during T37.

- `2026-08-03` the post-T78 `W36-E7-S4-T36` rerun is complete on clean source `a05a58e`
  and tree `7b5ce6a`: historical cases pass `4/4`, intervention/terminal families `24/24`,
  packaged journeys pass `79/79` with exact discovered/executed parity and `failed_ids=[]`, and
  one fresh uninterrupted full Chromium suite passes `188/188`. All five viewports complete
  without console, page, failed-request, overflow, accessibility, or process-cleanup failure;
  explicit packaged and full-suite postflights are empty. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t78.md`. T37 is `Next`, Codex
  T3 is `Soon`, and no provider or large scenario ran.

- `2026-08-03` `W36-E7-S4-T78` is complete: the Inbox running-now fixture cancels its
  test-owned job through the public endpoint, waits for durable `cancelled`, and proves the
  recorded runtime PID has exited before harness teardown. The formerly orphaning `1440x900`
  case passes `1/1`, the full Inbox family passes `9/9` across all five viewports with an empty
  external process postflight, Ruff and mypy across `228` modules pass, planning integrity
  passes `9/9`, and full pytest passes `2168/2168`. T36 is `Next`, T37 is `Soon`, and Codex T3
  remains parked until both replacement gates pass; no provider ran.

- `2026-08-03` the post-T77 T36 attempt started from a verified empty process baseline and
  passed historical cases `4/4`, intervention/terminal families `24/24`, and packaged registry
  `79/79` with exact discovered/executed ID parity and `failed_ids=[]`. The fail-closed
  postflight found one new orphaned Inbox fixture runtime from the final `1440x900` case, so the
  full Chromium layer and all provider work were not launched. `W36-E7-S4-T78` is `Next`, T36
  is `Soon`, and T37/T3 are parked until the cleanup regression and replacement gates pass.

- `2026-08-03` `W36-E7-S4-T77` is complete: aggregate finalization now derives its typed
  execution mode from the whole plan, retains real repository paths, and drops the synthetic
  verification-only `- none` entry without weakening task-local fail-closed validation. The
  saved post-T76 live ledger renders the exact four Hono paths and the saved aggregate report
  revalidates with zero findings. Focused checks pass `33/33`, the broader implementation group
  passes `130/130`, Ruff and mypy across `228` modules pass, planning integrity passes `9/9`,
  and full pytest passes `2168/2168`. T36 is `Next`, T37 is `Soon`, and Codex T3 remains parked
  until the replacement candidate; no new provider run occurred during the fix.

- `2026-08-03` the post-T76 Codex T3 attempt on candidate `c26820c` passed private auth,
  target readiness, exact-wheel identity, and manual quality audits through `tasklist`.
  Implement completed T1-T5, kept the product diff inside the four allowed files, and passed
  focused Vitest plus `tsc --noEmit`, but aggregate finalization combined the real T1-T4 paths
  with T5's truthful `- none` and then applied the selected verification-only rule to the whole
  mixed report. The root is not clean and will not be resumed. `W36-E7-S4-T77` is `Next`, T36 is
  `Soon`, and candidate `c26820c` is historical.

- `2026-08-02` `W36-E7-S4-T37` is complete for the active Codex-only scope on exact
  candidate `c26820c`, tree `a46ed39`, tracked archive digest `45f6174`, and wheel
  digest `469df0b`. Ruff, mypy across `228` modules, Python `2165/2165`, exact-SHA
  Chromium `188/188`, isolated install/doctor and Codex eval-doctor, fresh pinned Hono
  readiness with Vitest `233/233` and `tsc --noEmit`, self-contained bundle
  deletion/readback, Codex private-auth Seatbelt probe/canary, and source postflight all
  pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-08-02-post-t76.md`. Codex T3 is `Next`; Claude
  readiness and live execution remain parked and unclaimed, and no provider evaluator or
  large scenario ran.

- `2026-08-02` the post-T76 `W36-E7-S4-T36` rerun is complete on clean source
  `acd48ce` and tree `43c1e97`: historical cases pass `4/4`, intervention/terminal families
  `24/24`, packaged journeys pass `79/79` with exact discovered/executed ID parity and
  `failed_ids=[]`, and one fresh uninterrupted full Chromium suite passes `188/188`. All five
  viewports complete without console, page, failed-request, overflow, accessibility, or
  test-owned process-cleanup failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-02-post-t76.md`. T37 is `Next`, Codex
  T3 is `Soon`, and no provider or large scenario ran.

- `2026-08-02` `W36-E7-S4-T76` is complete: rich task cards carry typed
  `repository-change`/`verification-only` mode into system-owned selection and readback.
  Explicit verification-only tasks may truthfully preserve an empty task-local diff, while actual
  edits and unclassified no-op completion claims remain fail-closed. Focused checks pass
  `142/142`, the broader core/validator/task group passes `945/945`, Ruff and mypy across `228`
  modules pass, planning integrity passes `9/9`, and full pytest passes `2165/2165`. T36 is
  `Next`, T37 is `Soon`, T3 remains parked until the replacement candidate, and no provider ran.

- `2026-08-02` the post-T75 Codex T3 attempt on candidate `9b9f504` passed private auth,
  target readiness, exact-wheel identity, and manual quality audits through `tasklist`.
  Implement completed four repository-change tasks and passed focused Vitest `237/237` plus
  `tsc --noEmit`, but its verification-only T5 was rejected solely because the truthful
  task-local diff was empty. The terminal root is not resumed. `W36-E7-S4-T76` is `Next`, T36
  is `Soon`, and the candidate is invalid; Claude remains unlaunched under Codex-only scope.

- `2026-08-02` `W36-E7-S4-T37` is complete for the active Codex-only scope on exact
  candidate `9b9f504`, tree `9051118`, tracked archive digest `75ff5a0`, and wheel
  digest `b74d5fc`. Ruff, mypy across `228` modules, Python `2158/2158`, exact-SHA
  Chromium `188/188`, isolated install/doctor and Codex eval-doctor, fresh pinned Hono
  readiness with Vitest `233/233` and `tsc --noEmit`, self-contained bundle
  deletion/readback, Codex private-auth Seatbelt probe/canary, and source postflight all
  pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-08-02-post-t75.md`. Codex T3 is `Next`; Claude
  readiness and live execution remain parked and unclaimed, and no provider evaluator or
  large scenario ran.

- `2026-08-02` the post-T75 `W36-E7-S4-T36` rerun is complete on clean source
  `5d37cae` and tree `374b94b`: historical cases pass `4/4`, intervention/terminal
  families `24/24`, packaged journeys `79/79` with exact discovered/executed ID parity
  and no failed ID, and a fresh uninterrupted full Chromium suite passes `188/188`.
  All five viewports complete without console, page, failed-request, overflow,
  accessibility, or test-owned process-cleanup failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-02-post-t75.md`. T37 is
  `Next`, Codex T3 is `Soon`; no provider or large scenario ran.

- `2026-08-02` `W36-E7-S4-T75` is complete: Inbox provider-job and running-read-model
  preconditions use the existing bounded 30-second surface budget and fail with phase plus last
  durable payload. The diagnostic unit passes `1/1`, Inbox passes `9/9`, and the exact canonical
  prefix through the formerly failing `1280x900` case passes `79/79`; Ruff, mypy across `228`
  modules, planning integrity `9/9`, and full pytest `2158/2158` pass. T36 is `Next`, T37 is
  `Soon`; no provider ran.

- `2026-08-02` the post-T74 T36 gate on clean source `1882dc4` passed historical cases
  `4/4`, intervention/terminal families `24/24`, and packaged registry `79/79` with exact
  discovered/executed parity. Full Chromium then first failed at Inbox `viewport3` after `78`
  passes; the exact case passed in isolation and again at the same full-order position. T75 is
  `Next` to replace the test-only five-second provider-job/read-model polls with the existing
  bounded 30-second surface budget and phase diagnostics. T36 is `Soon`; no provider ran.

- `2026-08-02` `W36-E7-S4-T74` is complete: the Implement contract and runtime-agnostic
  command recognizer accept concrete ``nl -ba ... | sed ...`` inspection pipelines while
  rejecting bare `nl` prose and `.nl` filenames. Focused validator checks pass `51/51`,
  contract/scenario/planning checks pass `80/80`, the saved T2 live report revalidates with zero
  findings, Ruff and mypy across `228` modules pass, and full pytest passes `2157/2157`. T36 is
  `Next`, T37 is `Soon`, and provider acceptance remains parked until a replacement candidate;
  only Codex will be launched under the current scope.

- `2026-08-02` the post-T73 Codex T3 attempt on candidate `30e5f6a` passed private auth,
  target readiness, and strong manual audits through `tasklist`. Implement T1/T2 provider work
  and its focused checks passed, but the semantic validator rejected a concrete
  ``nl -ba ... | sed ...` -> pass`` inspection command and exhausted two repairs. The terminal
  root is not resumed. `W36-E7-S4-T74` is `Next`, T36 is `Soon`, and T37/T3 are parked until a
  replacement candidate exists; Claude remains unlaunched under the current Codex-only scope.

- `2026-08-02` `W36-E7-S4-T37` is complete on exact candidate `30e5f6a`, tree
  `a4bf5c4`, tracked archive digest `4c63a6e`, and wheel digest `472c771`.
  Ruff, mypy across `228` modules, Python `2153/2153`, exact-SHA Chromium
  `188/188`, isolated install/doctor, both eval-doctors, fresh pinned Hono
  readiness with Vitest `233/233` and `tsc --noEmit`, self-contained bundle
  deletion/readback, dual private-auth Seatbelt probes/canaries, and source
  postflight all pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-08-02-post-t73.md`. T3 is `Next`, T4 is
  `Soon`; no provider evaluator or large scenario ran.

- `2026-08-01` `W36-E7-S4-T37` is complete on exact candidate `44ba6d3`,
  tree `f28f428`, tracked archive digest `bb7c0b0`, and wheel digest
  `1ea5b09`. Ruff, mypy across 228 modules, Python `2150/2150`, exact-SHA
  Chromium `188/188`, isolated install/doctor, both eval-doctors, fresh
  pinned Hono readiness with Vitest `233/233` and `tsc --noEmit`,
  self-contained bundle deletion/readback, dual private-auth Seatbelt
  probes/canaries, and source postflight all pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-08-01-post-t72.md`. T3 is promoted to
  `Next`, T4 to `Soon`; no provider evaluator or large scenario ran.

- `2026-08-01` the post-T72 `W36-E7-S4-T36` rerun is complete on clean
  source `bb465ea` and tree `6d43544`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with
  exact discovered/executed ID parity and no failed ID, and full Chromium
  passes `188/188`. All five viewports complete without console, page,
  failed-request, overflow, accessibility, or test-owned process-cleanup
  failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-01-post-t72.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario
  ran.

- `2026-08-01` `W36-E7-S4-T72` is complete after the post-T71 Codex run exposed a
  runtime-agnostic incremental-stage persistence defect. Candidate `9d0bf59`
  passed private auth, target readiness, and manual quality checkpoints from
  `idea` through `tasklist`; Implement then completed task-scoped T1/T2 provider
  work, but canonical repair persistence removed successful deferred attempt 1
  and rejected its own `2,3` history. Deferred success now persists attempt 1
  before `pending`; core/validator checks pass `150/150` and CLI/incremental
  lifecycle checks pass `58/58`; Ruff, mypy, and the clean complete Python
  rerun pass, with `2150/2150`. The terminal provider root is not resumed.
  T36 is restored to `Next`, T37 to `Soon`, and provider acceptance is parked
  until a new candidate exists; no large scenario ran.

- `2026-08-01` `W36-E7-S4-T37` is complete on exact candidate `9d0bf59`,
  tree `8354d0a`, tracked archive digest `f4ef417`, and wheel digest
  `0964977`. Ruff, mypy across 228 modules, Python `2149/2149`, exact-SHA
  Chromium `188/188`, isolated install/doctor, both eval-doctors, fresh
  pinned Hono readiness with Vitest `233/233` and `tsc --noEmit`,
  self-contained bundle deletion/readback, dual private-auth Seatbelt
  probes/canaries, and source postflight all pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-08-01-post-t71.md`. T3 is promoted to
  `Next`, T4 to `Soon`; no provider evaluator or large scenario ran.

- `2026-08-01` the post-T71 `W36-E7-S4-T36` rerun is complete on clean
  source `ef38a3f` and tree `944906b`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with
  exact discovered/executed ID parity and no failed ID, and full Chromium
  passes `188/188`. All five viewports complete without console, page,
  failed-request, overflow, accessibility, or test-owned process-cleanup
  failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-01-post-t71.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario
  ran.

- `2026-08-01` `W36-E7-S4-T71` is complete: macOS Seatbelt now grants
  package-manager environment discovery only exact `literal` access to provider
  ancestor directory objects, without `subpath` access to external or sibling
  trees. Layouts below operator HOME fail before allocation. A real Bun
  lifecycle fixture and a fresh pinned Hono clone complete through the same
  boundary; source remains read-only and sibling, operator HOME, and credential
  probes remain denied. Isolation tests pass `20/20`, the complete harness
  regression `382/382`, Ruff and mypy across 228 modules, and full pytest
  `2149/2149`. T36 is promoted to `Next` and T37 to `Soon`; no provider or
  large scenario ran.

- `2026-07-29` the first post-T69 Codex T3 attempt stopped before provider
  allocation. Candidate `5cb58f3` passed private auth, target clone, run-owned
  wheel install, and public `aidd init`; isolated `bun install` then installed
  packages but failed lifecycle scripts with `CouldntReadCurrentDirectory`.
  A fresh provider-free Seatbelt root reproduces the same failure. The live root
  is terminal and will not be resumed. `W36-E7-S4-T71` is promoted to `Next`;
  T36 is `Soon`, while T37 and provider acceptance return to the parking lot.
  No provider inference or large scenario ran.

- `2026-07-29` `W36-E7-S4-T37` is complete on exact candidate `5cb58f3`, tree
  `90953e1`, tracked archive digest `349fc3e`, and wheel digest `a7e72c1`.
  Ruff, mypy across 228 modules, Python `2147/2147`, an uninterrupted exact-SHA
  Chromium `188/188`, isolated install/doctor, both eval-doctors, fresh pinned
  Hono readiness with Vitest `233/233` and `tsc --noEmit`, self-contained bundle
  deletion/readback, dual private-auth Seatbelt probes/canaries, and source
  postflight all pass. A rejected transient host-saturation browser attempt is
  retained as diagnostic evidence and did not change source or timeouts.
  Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-07-29-post-t69.md`. T3 is promoted to
  `Next`, T4 to `Soon`; no provider evaluator or large scenario ran.

- `2026-07-29` the post-T69 `W36-E7-S4-T36` rerun is complete on clean
  source `aa02a40` and tree `2905378`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with
  exact discovered/executed ID parity and no failed ID, and full Chromium
  passes `188/188`. All five viewports complete without console, page,
  failed-request, overflow, accessibility, or test-owned process-cleanup
  failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-29-post-t69.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario
  ran.

- `2026-07-29` `W36-E7-S4-T69` is complete: local-wheel installation
  explicitly places both uv tool storage and executable links below the selected
  run's install-home, independent of inherited provider-private XDG roots. The
  focused install/planning matrix passes `16/16`; a real no-provider uv
  build/install smoke returns an existing run-owned `aidd` binary and leaves the
  shared provider-private bin empty. The complete harness regression passes
  `380/380`, Ruff and mypy pass, and full pytest passes `2147/2147`. T36 is
  promoted to `Next`, T37 to `Soon`; provider acceptance remains parked and
  candidate `52bb49d` remains historical.

- `2026-07-29` the first post-T68 Codex T3 attempt stopped before provider
  allocation. Candidate `52bb49d` passed preflight, private auth, target clone,
  and wheel build, but inherited private XDG roots made uv publish the installed
  command under provider-private data/bin while the harness searched
  `<run>/install-home/.local/bin/aidd`. The root is terminal and will not be
  resumed. `W36-E7-S4-T69` is promoted to `Next`; T36 is `Soon`, while T37 and
  provider acceptance return to the parking lot. No provider inference or large
  scenario ran.

- `2026-07-29` `W36-E7-S4-T37` is complete on exact candidate `52bb49d`, tree
  `b699659`, tracked archive digest `75105f0`, and wheel digest `90a4247`.
  Ruff, mypy across 228 modules, Python `2146/2146`, exact-SHA Chromium
  `188/188`, isolated install/doctor, both eval-doctors, fresh pinned Hono
  readiness with Vitest `233/233` and `tsc --noEmit`, self-contained bundle
  deletion/readback, dual private-auth Seatbelt probes/canaries, and source
  postflight all pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-07-29-post-t68.md`. T3 is promoted to
  `Next`, T4 to `Soon`; no provider evaluator or large scenario ran.

- `2026-07-29` the post-T68 `W36-E7-S4-T36` rerun is complete on clean
  source `cb12e5b` and tree `6d26af7`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with
  exact discovered/executed ID parity and no failed ID, and full Chromium
  passes `188/188`. All five viewports complete without console, page,
  failed-request, overflow, accessibility, or test-owned process-cleanup
  failure. Sanitized evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-29-post-t68.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario
  ran.

- `2026-07-29` `W36-E7-S4-T68` is complete: typed terminal job evidence plus
  dashboard active-job readback now releases the volatile browser identity before
  the heavier project-home and inbox projections refresh behind a protected
  asynchronous boundary. Frontend passes `99/99`, static contracts `49/49`,
  three consecutive active-Studio matrices pass `5/5`, the exact Guided Setup
  predecessor followed by active Studio passes `10/10`, Ruff and mypy pass, and
  full pytest passes `2146/2146`. The 15-second browser budget is unchanged and
  no test-owned UI process remains. T36 is promoted to `Next`, T37 to `Soon`;
  provider acceptance remains parked.

- `2026-07-29` the post-T67 T36 rerun passed historical cases `4/4` in
  `121.64s` and intervention/terminal families `24/24` in `518.19s`. Packaged
  Guided Setup passed `5/5`, then active Studio reported `4/5`: desktop
  `1440x900` retained `activeJobId` beyond 15 seconds after recovered-log
  cancellation. The registry was stopped before the next journey and full
  browser did not run. `W36-E7-S4-T68` is promoted to `Next` for the remaining
  delayed-cancellation terminal handoff; T36 returns to `Soon`, while T37 and
  provider acceptance remain parked. No provider or large scenario ran.

- `2026-07-29` `W36-E7-S4-T67` is complete: terminal reconciliation
  records the immutable active job id, stale `cancelling` dashboard payloads
  cannot resurrect that tombstoned job, and a genuinely new launch clears the
  tombstone. Guided Setup passes `5/5`, followed by three strict sequential
  active-Studio runs at `5/5` each; frontend passes `99/99`, Ruff and mypy pass,
  and repeated full pytest passes `2146/2146`. One earlier unrelated 100ms
  process-start assertion passed `5/5` in isolation and in the full rerun; no
  process timeout changed. T36 is promoted to `Next`, T37 to `Soon`; provider
  acceptance remains parked.

- `2026-07-29` the post-T66 T36 rerun passed historical cases `4/4` in
  `116.80s` and intervention/terminal families `24/24` in `365.04s`. The
  packaged registry passed its first journey `5/5`, then active Studio reported
  `4/5`: tablet `768x1024` retained `activeJobId` beyond 15 seconds after
  recovered-log cancellation. The registry was stopped before the next journey;
  full browser did not run. `W36-E7-S4-T67` is promoted to `Next` for bounded,
  generation-safe ownership of the nonterminal cancellation poll. T36 returns
  to `Soon`; T37 and provider acceptance remain parked. No provider or large
  scenario ran on the T66 source.

- `2026-07-28` `W36-E7-S4-T66` is complete: macOS isolation now grants
  the fixed real `/private/etc/ssl` directory read-only so HTTPS Git can load
  LibreSSL configuration and trust data. Real Seatbelt reads `openssl.cnf`,
  local Git cloning remains green, no TLS write rule exists, and the exact
  previously failing provider-free HTTPS Hono clone passes. Focused checks pass
  `2/2`, isolation/auth/session passes `55/55`, Ruff and mypy pass, and full
  pytest passes `2146/2146`. T36 is promoted to `Next`, T37 to `Soon`; providers
  and large scenarios remain unstarted on the replacement candidate.

- `2026-07-28` the first post-T65 Codex T3 root stopped before provider
  allocation: public preflight and private auth passed, but Seatbelt denied
  `/private/etc/ssl/openssl.cnf` while HTTPS Git prepared the pinned target clone.
  This is an AIDD isolation-backend target-setup defect, not auth, provider,
  network, or model failure. `W36-E7-S4-T66` is promoted to `Next` for a trusted
  read-only TLS configuration root and real-Seatbelt regression. Candidate
  `1dbe87a` is invalidated; T36 returns to `Soon`, while T37 and both provider
  acceptances are parked. The failed root will not be resumed, and no large
  scenario ran.

- `2026-07-28` `W36-E7-S4-T37` is complete on exact candidate `1dbe87a`,
  tree `075e9fa`, tracked-index digest `c11d307`, archive digest `0f7135d`,
  and wheel digest `3b38a55`. Ruff, mypy across `228` modules, full pytest
  `2146/2146`, exact-SHA Chromium `188/188`, isolated install/doctor, both
  eval-doctors, pinned Hono setup with Vitest `233/233` and `tsc --noEmit`,
  bundle seal/readback after mutable-root deletion, dual private-auth Seatbelt
  sessions, and source postflight pass. Sanitized evidence is in
  `docs/e2e/candidate-readiness-2026-07-28-post-t65.md`. Codex medium acceptance
  T3 is promoted to `Next`, Claude T4 to `Soon`; no evaluator, Qwen, candidate-only,
  or large scenario ran.

- `2026-07-28` the post-T65 `W36-E7-S4-T36` rerun is complete on clean
  source `b38dd4c` and tree `8facd6e`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with exact
  discovered/executed ID parity and no failed ID, and full Chromium passes
  `188/188`. All five viewports complete without console, page, failed-request,
  overflow, accessibility, or test-owned process-cleanup failure. Sanitized
  evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28-post-t65.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario ran.

- `2026-07-28` `W36-E7-S4-T65` is complete: immediate terminal cancellation
  now retains the immutable job identity through dashboard, project, and inbox
  readback, then clears volatile state; active cancellation continues polling and
  late pre-cancel polling cannot overwrite the result. Frontend passes `99/99`,
  both failed mobile cases pass three repeated `2/2` runs, the full active-Studio
  journey passes `5/5`, Ruff and mypy pass, and full pytest passes `2146/2146`.
  T36 is promoted to `Next`, T37 to `Soon`; provider and large scenarios remain
  unstarted.

- `2026-07-28` post-T64 exact-SHA `W36-E7-S4-T37` passed Ruff, mypy across
  `228` modules, and full pytest `2146/2146`, then the exact Chromium gate
  reported `186/188`. Both failures were the mobile active-Studio cancellation
  cases: after a recovered live connection, an immediate terminal cancel response
  left `activeJobId` volatile because only nonterminal cancellation scheduled the
  polling path that performs durable reconciliation. The isolated pair passed
  `2/2`, confirming a suite-load race. `W36-E7-S4-T65` is promoted to `Next`,
  T36 returns to `Soon`, and T37/provider acceptance are parked. No archive,
  wheel, provider evaluator, or large scenario ran.

- `2026-07-28` the final post-T64 `W36-E7-S4-T36` rerun is complete on clean
  source `143cc1e` and tree `2efec8e`: historical cases pass `4/4`,
  intervention/terminal families `24/24`, packaged journeys `79/79` with exact
  discovered/executed ID parity and no failed ID, and full browser passes
  `188/188`. All five viewports complete without console, page, failed-request,
  overflow, accessibility, or test-owned process-cleanup failure. Sanitized
  evidence is in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28-post-t64.md`.
  T37 is promoted to `Next`, Codex T3 to `Soon`; no provider or large scenario ran.

- `2026-07-28` `W36-E7-S4-T64` is complete: both Implement journey entries now
  wait for `domcontentloaded`, exact work-item identity, and selected-runtime
  readiness before rendering evidence. Implementation recovery passes `3/3` across
  its five-viewport loop, the full Implement file passes `2/2` in `64.58s`, no
  `networkidle` wait remains, Ruff and standard mypy pass, and the full Python run
  has `2145` passing tests; its only failure was the corrected planning mismatch.
  T36 is promoted to `Next`, T37 to `Soon`; providers and large scenarios remain
  unstarted.

- `2026-07-28` the post-T63 T36 rerun passed historical cases `4/4` in
  `64.11s`, intervention/terminal families `24/24` in `396.10s`, and packaged
  journeys `79/79` with exact ID parity and no failed ID. The full browser suite
  then reported `187/188` in `3297.71s`: implementation recovery timed out in its
  first global `networkidle` navigation before product assertions, while isolated
  rerun passed `1/1` in `54.55s`. `W36-E7-S4-T64` is promoted to `Next`, T36
  returns to `Soon`, and T37/provider acceptance remain parked. No provider or
  large scenario ran.

- `2026-07-28` `W36-E7-S4-T63` is complete: the downstream-blocked
  intervention journey now waits for `domcontentloaded` and the exact work-item
  surface before durable Plan assertions. The failed `390x844` case passes `3/3`
  in isolation, complete intervention/terminal families pass `24/24` in `599.24s`,
  Ruff and standard mypy pass, and the full Python run has `2145` passing tests;
  its only failure was the corrected planning status mismatch. T36 is promoted to
  `Next`, T37 to `Soon`; providers and large scenarios remain unstarted.

- `2026-07-28` the post-T62 T36 gate passed its historical matrix `4/4` in
  `123.69s`, then the complete intervention/terminal families reported `23/24`.
  The sole `390x844` downstream-blocked intervention failure timed out in initial
  global `networkidle` before any durable product assertion; isolated rerun passed
  `1/1` in `47.75s`. `W36-E7-S4-T63` is promoted to `Next` for that one browser
  readiness boundary, T36 returns to `Soon`, and T37/provider acceptance remain
  parked. No packaged/full browser layer, provider evaluator, or large scenario ran.

- `2026-07-28` `W36-E7-S4-T62` is complete: the macOS isolation backend now resolves
  the active trusted `xcode-select` developer root and grants it read-only Seatbelt
  access. A real isolated `/usr/bin/git clone --no-local` passes while source and
  developer tools remain read-only, own provider state is writable, and operator
  HOME plus sibling state stay denied. Focused isolation passes `3/3`, auth/session
  `41/41`, harness `379/379`, Ruff and mypy pass, the full Python run has `2145`
  passing tests, and the corrected planning/docs rerun passes `50/50`. T36 is
  promoted to `Next` and T37 to `Soon`; candidate `98d97c7` remains invalidated
  and provider acceptance stays parked.

- `2026-07-28` the first Codex T3 root stopped before install or provider allocation:
  macOS Seatbelt denied `libxcrun.dylib` while `/usr/bin/git` prepared the pinned
  target clone. This is an AIDD isolation-backend defect rather than auth, network,
  provider, or model failure. `W36-E7-S4-T62` is promoted to `Next` to authorize the
  active `xcode-select` developer root read-only and prove Git through the real
  boundary. Its code change invalidates candidate `98d97c7`; T36 returns to `Soon`,
  while T37 and both provider acceptances are parked. The failed root will not be
  resumed, and no large scenario was launched.

- `2026-07-28` `W36-E7-S4-T37` is complete on exact candidate `98d97c7`, tree
  `ebda9cd`, tracked-index digest `01f9da4`, tracked archive `098d587`, and wheel
  `3b6b8cf`. Ruff, mypy across `228` modules, Python `2145/2145`, exact-SHA
  Chromium `188/188`, isolated install/doctor, both eval-doctors, pinned Hono
  setup with Vitest `233/233` and `tsc --noEmit`, bundle seal/readback after
  mutable-root deletion, dual private-auth Seatbelt canaries, and source postflight
  pass. The Claude probe uses only the launcher's explicitly selected
  `ANTHROPIC_AUTH_TOKEN`; credential values and digests are not recorded. Sanitized
  evidence is in `docs/e2e/candidate-readiness-2026-07-28.md`. Codex medium
  acceptance T3 is promoted to `Next`, Claude T4 to `Soon`; no evaluator or large
  scenario has started.

- `2026-07-28` the post-T61 `W36-E7-S4-T36` rerun is complete on clean source
  `21c12ed` and tree `7185fbd`: historical cases pass `4/4`, intervention/terminal
  families `24/24`, packaged journeys `79/79` with exact discovered/executed ID parity and no
  failed ID, and the full Chromium suite `188/188`. All five viewports complete without console,
  page, failed-request, overflow, accessibility, or test-owned process-cleanup failures. The
  sanitized evidence is `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28.md`.
  T37 is promoted to `Next`, Codex medium acceptance T3 to `Soon`; no provider or large scenario
  has started.

- `2026-07-28` `W36-E7-S4-T61` is complete: the runtime/validation Recovery browser
  journey now waits for `domcontentloaded` and exact work-item surface readiness rather than
  global network idle. The isolated `runtime-no-progress` case passes `3/3`, the complete
  Recovery family passes `9/9` across all viewports and parity selectors, Ruff passes, and no
  `networkidle` wait remains in the file. Production Studio, fixture state, and timeout budgets
  are unchanged. T36 is promoted to `Next`, T37 to `Soon`; provider and large scenarios remain
  unstarted.

- `2026-07-28` the post-merge `W36-E7-S4-T36` revalidation on clean source `bbed868`
  passed the historical matrix `4/4`, intervention/terminal families `24/24`, and the packaged
  registry `79/79` with exact ID parity. The complete browser suite then failed after `108`
  passing tests because the `runtime-no-progress` Recovery fixture exceeded its 30-second global
  `networkidle` navigation wait before durable product assertions. An isolated rerun passed
  `1/1`, classifying the boundary as a suite-order browser synchronization race.
  `W36-E7-S4-T61` is promoted to `Next`, T36 returns to `Soon`, and T37/Codex acceptance remain
  parked. No provider or large scenario was launched.

- `2026-07-27` `W36-E7-S4-T37` is paused, not complete, on exact source `c5747a0`
  and tree `2a946c5`. Ruff, mypy across `228` modules, and full pytest `2145/2145`
  pass. The exact-SHA Chromium run was operator-stopped after `67` passing tests, so it must
  restart from zero; this is incomplete evidence rather than a browser defect. No new archive,
  wheel, digest, installed doctor, target readiness, bundle, private-auth, or source-postflight
  candidate record exists. `T37` remains `Next`, Codex medium acceptance `T3` remains `Soon`,
  and the live medium scenario has not yet passed.

- `2026-07-27` the post-auth `W36-E7-S4-T36` rerun is complete on clean source
  `314aedf` and tree `9703b02`: the exact historical matrix passes `4/4`, complete
  intervention/terminal families pass `24/24`, the twelve packaged journeys pass `79/79` with
  exact discovered/executed ID parity and no failed ID, and the full Chromium suite passes
  `188/188`. All five viewports complete without console, page, failed-request, overflow,
  accessibility, or test-owned process-cleanup failures. Sanitized evidence is recorded in
  `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-27.md`; exact-SHA readiness `T37`
  is promoted to `Next` and Codex acceptance `T3` to `Soon`.

- `2026-07-27` `W36-E7-S4-T60` is complete: fresh Codex and Claude Code launchers can
  seed only their T59 auth file, both status commands run inside the OS boundary before evaluator
  execution, unseeded private homes return a redacted `provider-auth` blocker, and resume reuses
  the retained private credential. Preflight now reports private-auth pending rather than trusting
  host OAuth; session schema v2 records only sanitized auth lifecycle fields. Real Seatbelt tests
  keep operator HOME and sibling state unreadable and source bytes read-only. Launcher tests pass
  `17/17`, full harness `378/378`, Ruff, mypy across `228` modules, and full pytest `2145/2145`.
  The code change invalidates candidate `43d740c`, so browser gate `T36` is promoted to `Next`
  and exact-SHA readiness `T37` to `Soon`; Codex `T3` and Claude `T4` remain parked.

- `2026-07-27` `W36-E7-S4-T59` is complete: a typed, runtime-allowlisted seed operation
  copies only Codex `.codex/auth.json` or Claude Code `.claude.json` into a distinct
  provider-private home through verified staging and atomic publication. It rejects traversal,
  source/destination symlinks, hard links, oversized or changing files, existing destinations,
  and injected partial-copy failure; directories are `0700`, credentials are `0600`, and its
  public result contains no payload, absolute source path, or digest. The focused matrix passes
  `11/11`; isolated probe integration `T60` is promoted to `Next`.

- `2026-07-27` the first post-candidate Codex readiness probe found that host OAuth is valid
  while the intentionally empty provider-private home is unauthenticated. `W36-E7-S4-T59`
  owns the minimal allowlisted auth snapshot and is promoted to `Next`; `T60` owns isolated
  status-probe integration in `Soon`. The accepted `43d740c` candidate remains immutable
  historical evidence, but any implementation change requires fresh `T36 -> T37` gates before
  Codex `T3` and Claude `T4` return from Parking.

- `2026-07-26` `W36-E7-S4-T37` is complete: clean candidate `43d740c`, tree
  `a780ce9`, source archive `b416b44`, and wheel `b93257d` pass Ruff, mypy, Python
  `2126/2126`, Chromium `188/188`, isolated install/doctor, both provider eval-doctors,
  fresh pinned Hono setup and authored smoke, bundle seal/readback after target deletion,
  public preflight, dual `macos-seatbelt` canaries, and source-integrity postflight. The
  exact identities and sanitized signals are recorded in
  `docs/e2e/candidate-readiness-2026-07-26.md`; the record commit is not a replacement
  candidate. Codex acceptance `T3` is promoted to `Next`, with Claude `T4` at `Soon`.

- `2026-07-26` `W36-E7-S4-T36` is complete on clean source `17213af` and tree
  `601aeb7`: the exact historical matrix passes `4/4`, complete intervention/terminal
  families pass `24/24`, the twelve packaged journeys pass `79/79` with identical
  discovered/executed IDs and no failed ID, and the full Chromium suite passes `188/188`
  in `2617.84s`. All five viewports finish with clean console, page, request, overflow,
  accessibility, and bounded process-cleanup diagnostics. Exact-SHA readiness `T37` is
  promoted to `Next`; Codex acceptance `T3` is `Soon` but remains blocked until `T37`.

- `2026-07-26` `W36-E7-S4-T58` is complete: stage-interact now synchronously persists one
  typed intervention request, returns its canonical work-item/run/stage/id/path/excerpt winner
  in the accepted job envelope, and reuses that prepared request during asynchronous execution
  without duplication. Frontend reconciliation clears only the immutable submitted draft before
  job polling and retains durable dashboard readback as a compatibility fallback. Focused
  CLI/frontend coverage passes `17/17`, the full intervention/browser/static selection passes
  `28/28`, and all five allowed viewports prove the draft is cleared while the runtime job remains
  running. Provider-free Chromium acceptance `T36` is promoted to `Next`; exact-SHA readiness
  `T37` is promoted to `Soon`.

- `2026-07-26` the second `W36-E7-S4-T36` attempt on source `cff519b` stopped at the
  historical matrix with `2/4` passing. At `320x568` and `1280x900`, the accepted
  intervention produced one OK POST and one correct canonical request, but the submitted draft
  remained through the 30-second bound. `T56` fixed immutable identity and job-poll ordering,
  but the accepted UI job envelope still omits the already-persisted request winner, so later
  dashboard readback can remain coupled to runtime execution. `T58` owns that single boundary;
  `T36` returns to `Soon`, while exact-SHA `T37` remains parked.

- `2026-07-26` `W36-E7-S4-T53` is complete: the shared bounded log reader enforces a
  256 KiB hard limit and reports requested/retained bytes, exact ranges, head/tail truncation,
  partial-line edges, and oversized-line status. CLI, operator UI/read models, and live harness
  heartbeats now use it while the complete durable log remains unchanged. Sparse 64 MiB,
  oversized-line, CLI, and read-model tests pass `12/12`; UI log API tests pass `5/5`; all `41`
  doc checks pass. `T54` is promoted to `Next` and `T55` to `Soon`.

- `2026-07-26` `W36-E7-S4-T52` is complete: ignored/cache paths now persist as bounded
  inventories with total/group counts, root/type groups, full-set SHA-256, a 50-path sample, and
  path/group truncation flags; ignored findings are bounded too. Tracked, modified, deleted, and
  non-ignored untracked product paths remain exact, and legacy full-list snapshots still read.
  The 20,000-path fixture remains under fixed JSON budgets; repository tests pass `9/9`, the live
  setup-baseline flow passes, and all `41` doc checks pass. `T53` is promoted to `Next` and `T54`
  to `Soon`.

- `2026-07-26` `W36-E7-S4-T51` is complete: product summary schema v2 now reports
  independent execution, manual-review, counted-clean, manual-stop, and legacy-degraded signals
  with explicit not-clean reasons. Terminal refresh incorporates newly added manual reports,
  rematerializes and reseals the bundle, while retaining byte-identical `verdict.md` and
  `grader.json`. The five-state unit matrix passes `5/5`, terminal pre/post-review refresh passes
  `2/2`, and all `41` live-document consistency checks pass. `T52` is promoted to `Next` and
  `T53` to `Soon`.

- `2026-07-26` `W36-E7-S4-T50` is complete: `live-bundle-manifest.json` is now the
  atomically-published final commit marker over the validated T49 index, exact tracked AIDD source
  archive, installed wheel, source commit/tree, target pin, all bundle file sizes/digests, and
  browser run/viewport identities. Readback rejects changed bytes, incomplete materialization,
  orphan files, identity drift, and wrong browser provenance; repeat sealing is stable. The
  combined manifest/materialization/terminal-flow matrix passes `79/79`. `T51` is promoted to
  `Next` and `T52` to `Soon`.

- `2026-07-26` `W36-E7-S4-T49` is complete: the typed live result materializer now copies
  work-item stage outputs, task/run/finalization evidence, target patch, final reports,
  approval/remediation records, and browser artifacts into `canonical-evidence`. Its
  `live-result-index.json` uses only bundle-relative size/digest-backed references; containment,
  identity, symlink, dangling-link, and digest checks fail closed, while old absolute references
  require explicit `legacy-degraded` read mode. The source/work/target deletion matrix and
  terminal-flow compatibility suite pass `74/74`. `T50` is promoted to `Next` and `T51` to
  `Soon`.

- `2026-07-26` `W36-E7-S4-T48` is complete: bounded target Git preparation and dependency setup
  now precede a typed `target-readiness.json` gate. The gate derives provider-free smoke from the
  selected authored task, defers only future `.aidd` artifacts, checks relative generated/native
  executables, and classifies missing dependencies, non-zero commands and timeouts as
  `target-setup` before any `run-stage`. The focused matrix passes `26/26`; the completed
  lifecycle group passes Ruff, mypy across `221` modules and all `2096` Python tests. `T49` is
  promoted to `Next` and `T50` moves to `Soon`.

- `2026-07-22` `W36-E7-S4-T35` is complete: runtime-readiness updates now use a
  generation-aware scoped renderer and cannot replace the decision-owning Studio cockpit.
  Flow Complete disclosure state is retained by durable handoff identity; intervention and
  archive actions use immutable descriptors, one guarded POST, and authoritative durable
  readback without clearing a newer browser draft or rewriting the completed source run.
  The four characterized cases pass `4/4`, the complete intervention and terminal families
  pass `14/14` and `10/10`, and all 97 frontend state tests pass. `T38` is promoted to `Next`;
  its direct successor `T39` moves to `Soon`.

- `2026-07-22` `W36-E7-S4-T34` is complete: the exact failures were intervention
  viewports `320x568`, `1280x900`, and `1440x900`, plus terminal `1280x900`.
  Isolated `4/4` reruns proved that intervention created one durable request despite
  an asynchronous observer count of zero, while a delayed-readiness probe proved
  that the terminal action was replaced by a second full cockpit render before
  dispatch. The normalized evidence is recorded in
  `docs/e2e/operator-ui-chromium-race-characterization-2026-07-22.md`. `T35` is now
  `Next`; `T38` is its direct successor in `Soon`.

- `2026-07-22` static review plus forensic analysis of 64 historical `AIDD-LIVE-007` bundles
  found provider sibling-root visibility, unsafe live resume lookup, advisory-only integrity
  checks, direct harness stage-state mutation, uncontained browser evidence imports, provisional
  frontend false failures, stale running owners, reset aggregate timing, incomplete remediation
  diagnostics, repeated target-setup failures, dangling acceptance references, stale summaries,
  and unbounded duplicated evidence. Runtime-neutral tasks `W36-E7-S4-T38..T55` split those
  findings by owner and verification signal. The queue remains `T34 -> T35`; then `T38..T55`
  complete all code changes before final Chromium evidence `T36` and exact-SHA readiness `T37`.
  Codex `T3`, Claude `T4`, observed sessions, and final same-wheel `T5` remain parked until those
  provider-free gates pass.

- `2026-07-22` the exact-`a3d5aa1` preflight passed 88 frontend tests, Ruff, mypy across 210
  source files, and all 1980 Python tests, then the full Chromium lane reported four failures
  (`183 passed`). Three intervention cases observed no matching stage-interact POST after
  History/Back restoration, and one terminal case could not click Archive because polling
  repeatedly detached or hid the Flow Complete action. `W36-E7-S4-T34..T37` split
  characterization, shared synchronization repair, full browser acceptance, and exact-SHA
  package/isolation readiness into separate reviewable outputs. `T34` is promoted to `Next`,
  `T35` to `Soon`; Codex `T3` and Claude `T4` return to Parking until the provider-free gate is
  completely green.

- `2026-07-21` `W36-E7-S4-T33` is complete: Plan semantic validation now resolves the canonical
  allowed-write scope and fails closed with `SEM-PLAN-SCOPE-MISMATCH` when `Milestones` or
  `Implementation strategy` proposes an out-of-scope or unsafe repository write. Read-only
  evidence and executable command references remain outside this rule, malformed scope is a
  high-severity finding, and missing optional scope preserves legacy unrestricted planning. The
  live-shaped helper regression, unsafe-path matrix, protocol/renderer inventory, all validator
  tests, docs/planning checks, and focused Ruff pass. Codex `T3` returns to `Next`; Claude `T4`
  is its direct successor in `Soon`.

- `2026-07-21` `W36-E7-S4-T32` is complete: the Plan contract and initial/repair prompts now read
  canonical `context/allowed-write-scope.md` as an exhaustive implementation-write boundary,
  distinguish read-only evidence/commands, forbid invented out-of-scope helpers and modules, and
  require a private helper inside allowed files or a blocking question instead of scope widening.
  The provider-free Plan stagepack now materializes the scope and verifies it in the packaged
  stage brief. The public `aidd eval execute` smoke passes; 146 prompt/scenario/packaging/docs/
  planning tests and focused Ruff pass. `W36-E7-S4-T33` is promoted to `Next` for fail-closed
  semantic enforcement; Codex `T3` remains its direct successor and Claude `T4` stays parked.

- `2026-07-21` two independent fresh Codex candidates on exact revision `bc248b2` passed Idea and
  Research quality review, then each produced a structurally valid Plan that explicitly proposed
  `src/utils/error.ts` outside the four-file canonical allowed-write scope. Manual quality review
  stopped both candidates as `manual-quality-stop` before Review Spec or Tasklist. Because the
  same scope leak repeated across isolated roots, `W36-E7-S4-T32` is promoted to `Next` for a
  runtime-neutral Plan contract/prompt regression; Codex `T3` moves to `Soon`, and Claude `T4`
  returns to Parking until a fresh exact-SHA preflight and Codex run pass.

- `2026-07-21` `W36-E7-S4-T31` is complete: after the clean 187-case browser pass, the full Python
  suite passed 1968 of 1969 tests and exposed one load-sensitive harness success fixture. Its
  helper writes a heartbeat immediately and every 100 milliseconds, but the one-second
  no-progress budget expired before the process received enough host scheduling; the decisive
  probe remained `exists: false`. Five isolated reruns passed, with one taking 12.94 seconds end to
  end despite 0.5 seconds of helper work. The success fixture now uses separate bounded three- and
  eight-second budgets; the adjacent one-second silent-process test keeps production no-progress
  classification covered. Codex `T3` remains blocked pending a clean exact-SHA full suite.

- `2026-07-21` `W36-E7-S4-T30` is complete: the post-`T29` full Chromium lane passed 184 of 187
  cases and exposed three global network-idle timeouts in two stateful journey families. Both
  intervention tests and terminal `1440x900` failed before their first business assertion while
  waiting for background Studio polling to become silent. A shared test-owned helper now waits
  after DOM readiness for the exact rendered work-item identity, and every navigation/reload in
  those owning files uses that durable boundary. Product polling, rendering, APIs, mutations, and
  runtime behavior are unchanged; Codex `T3` remains blocked pending focused and full gates.

- `2026-07-21` `W36-E7-S4-T29` is complete: the full exact-`6f9d64c` Chromium lane passed 186 of
  187 cases and exposed one remaining Inbox-only short wait. The job endpoint and `/api/inbox`
  had already confirmed the same Running-now identity, but the `768x1024` render was allowed 15
  seconds instead of the journey's shared bounded 30-second surface budget. The unchanged isolated
  case passed in 97 seconds end to end, confirming load-sensitive test synchronization rather than
  lost durable state. Running-now now uses the shared budget; Codex `T3` remains blocked until the
  focused five-viewport matrix and a new full browser lane pass on this commit.

- `2026-07-21` `W36-E7-S4-T28` is complete: explicit backticked `sh -c`, `bash -c`, and
  `zsh -c` verification commands are now recognized by the existing command-shaped evidence
  predicate, while prose-only shell names remain non-executable evidence. The live-shaped cleanup
  regression and the complete focused validator/docs/planning matrix pass (`94 passed`), with Ruff
  clean. Codex `T3` returns to `Next` for a fresh external run; Claude `T4` is its direct successor.

- `2026-07-21` the fresh Codex run on exact revision `3d75c07` passed manual quality review through
  Tasklist and exercised two successful fail-closed Tasklist repairs. Implement `T1` then produced
  the correct bounded `src/compose.ts` patch, passed 233 focused Vitest cases and `tsc --noEmit`,
  but exhausted all three report-repair attempts on `SEM-UNVERIFIABLE-CHECK-CLAIM`. The decisive
  bullet contains an exact backticked `sh -c '...'` command and exit-code evidence; semantic
  extraction preserves it, but the executable registry omits shell interpreters and classifies it
  as prose. `W36-E7-S4-T28` is promoted to `Next`; Codex `T3` moves to `Soon` pending a
  provider-free regression and a fresh external root, while Claude `T4` returns to Parking.

- `2026-07-21` `W36-E7-S4-T27` is complete: the Inbox browser journey no longer waits for global
  network silence from a polling Studio or reads its lexical JavaScript state. Navigation and
  reload now wait for DOM readiness followed by exact rendered work-item, Inbox, and question
  surfaces under one bounded 30-second budget. The two originally failing edge viewports pass
  repeatedly, the complete five-viewport Inbox matrix passes, and docs/planning plus Ruff checks
  pass; production routing, polling, rendering, APIs, and provider behavior are unchanged. Codex
  `T3` returns to `Next`; Claude `T4` is its direct successor.

- `2026-07-21` the exact-`266cf5c` provider-free preflight passed 88 frontend tests, Ruff, mypy,
  doctor/readiness, and 1964 Python tests, then the full Chromium lane reported two failures in the
  same Inbox journey (`185 passed, 2 failed`). One failure waited for global `networkidle` while
  Studio polling was healthy; the other observed canonical route/dashboard identity before the
  bounded question surface render. Isolated rerun passed the mobile case and reproduced the
  desktop failure at a later `networkidle` wait, proving test synchronization rather than durable
  state loss. `W36-E7-S4-T27` is promoted to `Next`; live execution remains blocked until all five
  viewports and the full browser lane pass on a new exact SHA.

- `2026-07-21` `W36-E7-S4-T26` is complete: plan/tasklist cross-document validation now parses
  explicit `before`, `after`, `depends on`, and `requires` clauses in their authored direction,
  including a shared `M2 and M3 ... after M1, but both ... before M4` subject. A provider-free
  live-shaped graph passes while removal of a real prerequisite remains fail-closed. Focused
  cross-document, docs/planning, and Ruff checks pass. Codex `T3` returns to `Next`; Claude `T4`
  is its direct successor.

- `2026-07-21` the fresh Codex run on `d4883d2` passed manual quality review for Idea, Research,
  Plan, and Review Spec, then exhausted Tasklist repair on four inverted
  `CROSS-TASKLIST-PLAN-DEPENDENCY` findings. The authored graph correctly maps
  `T1 -> T2/T3 -> T4/T5 -> T6`; the validator instead treated the first milestone in canonical
  `before` and mixed `after ... before` clauses as the dependent target. Runtime attempts all
  succeeded and final validation failed closed. `W36-E7-S4-T26` is promoted to `Next`; Codex `T3`
  is blocked pending a clause-direction regression and a fresh external root.

- `2026-07-21` `W36-E7-S4-T25` is complete: the UI runtime-cancellation fixture now waits for its
  live-log startup marker with an explicit monotonic ten-second deadline instead of assuming host
  scheduling within one second. Five isolated repetitions, docs/planning checks, and Ruff pass;
  runtime launch, cancellation, and evidence semantics are unchanged. Codex `T3` returns to `Next`
  for a fresh clean-HEAD preflight, followed by independent Claude `T4`.

- `2026-07-21` the exact-`7c29b14` preflight passed Ruff, mypy, and 1961 Python tests, but the UI
  runtime-cancellation fixture failed its fixed one-second log-start polling window. An isolated
  rerun passed once and failed once, proving load-sensitive synchronization rather than a provider
  result. `W36-E7-S4-T25` is promoted to `Next`; Codex `T3` is blocked before any external root or
  provider run is created.

- `2026-07-21` the operator reset the Codex provider limit. `W36-E7-S4-T3` is restored to `Next`
  for a fresh external run from clean tracked HEAD; `W36-E7-S4-T4` moves to `Soon` and remains
  dependent on a clean Codex result on the same AIDD revision.

- `2026-07-21` `W36-E7-S4-T24` is complete: cross-document repair traceability now derives the
  active repair requirement from the latest canonical attempt-history entry. A completed repair
  retained for an earlier rich task no longer requires a current task's removed canonical
  `repair-brief.md`; a latest repair attempt and legacy unstructured repair mention remain
  fail-closed. Cross-document, stage-runner, docs, planning, and Ruff checks pass. Product-owned
  defects found by the independent Claude diagnostic runs are closed; provider acceptance remains
  blocked by the Codex account quota before a fresh exact-revision run can begin.

- `2026-07-21` `W36-E7-S4-T23` is complete: Implement allowed-scope validation now reads only the
  canonical leading path token from each top-level `Touched files` entry. Descriptive backticked
  code identifiers such as `context.error` no longer become fabricated repository paths, while
  missing, malformed, or genuinely out-of-scope leading paths retain fail-closed validation.
  Focused semantic/scope/docs/planning tests and Ruff pass. `W36-E7-S4-T24` is promoted to `Next`;
  provider acceptance remains blocked pending its independent repair-history regression.

- `2026-07-21` the fresh Claude retry on exact revision `c19d396` proved task-local repository
  diff recovery, then failed T2 on two runtime-neutral validator boundaries: the Implement
  semantic rule interpreted descriptive backticked identifier `context.error` as a second touched
  path, and cross-document validation required a current repair brief for retained stage-wide T1
  repair history while validating clean T2. Task diff evidence itself was exact and T1 remained
  succeeded. `W36-E7-S4-T23` is promoted to `Next`, `T24` to `Soon`; provider runs remain blocked
  pending separate regressions and fresh roots. The Codex diagnostic attempt was independently
  blocked by provider quota rather than an AIDD defect.

- `2026-07-21` `W36-E7-S4-T22` is complete: stage-scoped operator request Markdown is rendered to
  a unique sibling staging file and atomically renamed to its canonical `request-*.md` path. A
  concurrent-reader regression blocks immediately before publication and proves the canonical path
  is absent until complete content is available; a simulated publication failure leaves neither a
  partial canonical file nor staging residue. Core/CLI/docs/planning tests, Ruff, mypy, and all five
  intervention browser viewports pass with one POST and one durable request. Codex `T3` returns to
  `Next`; Claude `T4` is its direct successor.

- `2026-07-21` the exact-`96d18fc` browser gate passed 83 cases, then the mobile intervention
  journey observed canonical `request-0001.md` as an empty file immediately after the single POST.
  Draft restoration, routing, and mutation count were correct; the first decisive boundary is a
  direct non-atomic `Path.write_text` in core operator-intervention persistence. The run was stopped
  after preserving the traceback. `W36-E7-S4-T22` is promoted to `Next`; Codex `T3` remains blocked
  until atomic publication has provider-free regression coverage and the complete browser lane is
  green on a new exact SHA.

- `2026-07-21` `W36-E7-S4-T21` is complete: shared streaming now records normal parent exit before
  applying later cancellation/completion/runtime deadlines during bounded descendant and inherited
  pipe cleanup. A deterministic regression forces cleanup across the configured runtime deadline
  and preserves the normal result, while real pre-exit timeout remains unchanged. The large
  bidirectional success characterization now uses a distinct bounded runtime budget under its
  existing outer watchdog. All 304 adapter/docs/planning tests, Ruff, and mypy pass. Codex `T3`
  returns to `Next`; Claude `T4` is its direct successor.

- `2026-07-21` the exact-`2c00d89` full Python gate passed 1956 tests and exposed two shared
  process-lifecycle deadline races. The bidirectional success characterization used the same
  200-millisecond budget as a timeout stress case and fails deterministically under current load.
  Separately, a normally exited parent can be labelled timeout when bounded inherited-pipe cleanup
  crosses the runtime deadline because deadline polling precedes parent-exit recognition. The
  first decisive boundary is runtime-neutral subprocess supervision/test budgeting, not provider
  behavior. `W36-E7-S4-T21` is promoted to `Next`; Codex `T3` is blocked until the regression and
  a clean exact-SHA full gate.

- `2026-07-21` `W36-E7-S4-T20` is complete: the Implement document/stage contracts plus initial
  and repair prompts now define rich-task `Touched files` as the exact current task baseline/final
  diff. Successful prerequisite-only paths are excluded unless changed again, new current-task
  files remain mandatory, and aggregate finalization owns cumulative evidence. Repair guidance
  removes unsupported cumulative claims without reverting preserved prior-task outcomes. Focused
  prompt, contract, planning, packaging, and repository-evidence regressions pass. Codex `T3`
  returns to `Next`; Claude `T4` is its direct successor on the new accepted revision.

- `2026-07-21` fresh Codex run `eval-live-007-codex-20260720T231452Z` on `a6c79f9`
  passed and was manually accepted through Tasklist, proving the new canonical scope guard. During
  Implement, T1 succeeded; T2 initially reported prerequisite `src/compose.ts` as task-local and
  passed after normal `SEM-TASK-DIFF-MISMATCH` repair; T3 repeated the same cumulative-workspace
  claim for `src/compose.ts` and `src/hono-base.ts`, then failed closed after the stage-wide repair
  budget was exhausted. The validator, ledger preservation, and fail-fast behavior are correct.
  The first decisive boundary is contradictory generic Implement guidance: it asks each rich-task
  report to list the whole changed workspace while validation owns the current task baseline/final
  diff. `W36-E7-S4-T20` is promoted to `Next`; Codex `T3` remains blocked pending a provider-free
  contract/prompt regression and a fresh external run.

- `2026-07-20` `W36-E7-S4-T19` is complete: terminal polling now retains the active job identity
  until dashboard, project-home, and Inbox durable readback all finish, then releases volatile
  buffers immediately before the final render. A new deferred-promise frontend regression proves
  that no intermediate readback advertises completion, and the complete active-Studio journey
  passes all five viewports with persisted `runtime.log` visible after cancellation. Job APIs,
  cancellation semantics, and durable evidence are unchanged. Codex `T3` returns to `Next`;
  Claude `T4` is its direct successor.

- `2026-07-20` the post-`T18` full browser gate passed 56 cases before the active-Studio journey
  timed out at `1440x900` after cancellation: volatile `activeJobId` had already cleared, while
  persisted `runtime.log` had not rendered. The exact case then passed six isolated reruns, with
  duration varying from 17 to 69 seconds. Source inspection identifies a presentation ordering
  race: terminal reconciliation clears volatile job state after dashboard readback but before
  project-home/Inbox readback and final render. `W36-E7-S4-T19` is promoted to `Next`; Codex `T3`
  remains blocked until a deterministic regression and a clean full browser lane.

- `2026-07-20` `W36-E7-S4-T18` is complete: Tasklist cross-document validation now resolves the
  canonical allowed-write scope and rejects each task card containing an out-of-bound local path
  with actionable `SEM-TASK-SCOPE-MISMATCH` evidence before Implement begins. Contracts plus
  initial and repair prompts require component-boundary containment and prohibit widening the
  operator-authored global scope. Provider-free coverage includes exact paths, permitted
  descendants, the live-discovered incompatible-card shape, `src`/`src2`, malformed scope, and
  the existing unrestricted behavior when the optional document is absent. Codex `T3` returns to
  `Next`; Claude `T4` is its direct successor on the same accepted revision.

- `2026-07-20` fresh Codex run `eval-live-007-codex-20260720T195547Z` on `a4935d8`
  passed Idea through Tasklist, including canonical milestone repair, then failed closed during
  the first implementation task. Tasklist had accepted `T1` paths under `src/utils/` and
  `package.json` even though the authored global scope allowed only four Hono/compose files.
  Implement preserved three attempts, passing target Vitest and TypeScript checks while refusing
  publication with `SEM-TASK-SCOPE-MISMATCH`. The first decisive boundary is a runtime-neutral
  tasklist/allowed-scope validation gap; `W36-E7-S4-T18` is promoted to `Next`, Codex `T3` is
  blocked pending its regression and a fresh external run, and Claude `T4` returns to Parking.

- `2026-07-20` `W36-E7-S4-T17` is complete: the approvals surface now owns one browser-only
  session-confirmation identity and reason, captures it before polling replaces the DOM, and
  restores it only while canonical readback still reports the same request pending. A new job,
  explicit Back, durable winner, terminal readback, or reconciled job cleanup clears the ephemeral
  state. Endpoints and decision CAS are unchanged. Frontend tests force the re-render boundary;
  approval parity and all five browser viewports pass. Codex `T3` returns to `Next`; Claude `T4`
  is its direct successor.

- `2026-07-20` the final T16 browser gate passed 186 of 187 cases and exposed a timing-dependent
  approval presentation race at `1280×900`: `Allow session` opens an ephemeral confirmation, while
  concurrent polling can replace the approvals DOM and discard it before operator confirmation.
  The isolated case and three concurrent reruns passed, confirming nondeterminism rather than a
  stable markup failure; source inspection proves the unowned ephemeral state boundary. No
  decision was fabricated and durable CAS remains correct. Presentation-only task
  `W36-E7-S4-T17` is promoted to `Next`; Codex `T3` remains blocked pending a regression and a
  clean browser lane.

- `2026-07-20` `W36-E7-S4-T16` is complete: the durable tasklist contract plus initial and
  repair prompts now name the four canonical milestone mapping locations consumed by
  cross-document validation (`Outcome`, `Context`, acceptance criteria, and task-local
  `Verification notes`). Milestone findings and generated repair briefs repeat the same actionable
  locations and explicitly reject ad hoc `Milestone`/`Plan milestone` fields without widening the
  rich-task grammar. Provider-free regressions cover all four valid locations and replay the exact
  unsupported-field shape from the historical live failure. Codex `T3` returns to `Next`; Claude
  `T4` is its direct successor.

- `2026-07-20` the fresh `76a4579` Codex run proved corrected milestone validation but exhausted
  all three tasklist attempts because the authoring and repair guidance did not name the mapping
  fields consumed by the rule. Codex added intuitive `Plan milestone`/`Milestone` card fields on
  repair, while the canonical predicate intentionally reads only `Outcome`, `Context`, acceptance
  criteria, and `Verification notes`. Runtime/provider startup and frontend checkpoints passed;
  the first decisive boundary is ambiguous contract/validator/prompt repair guidance. The run is
  historical and stopped before implementation. Runtime-neutral task `W36-E7-S4-T16` is promoted
  to `Next`; Codex `T3` remains blocked pending regression coverage and a fresh run.

- `2026-07-20` `W36-E7-S4-T15` is complete: tasklist/plan cross-validation now recognizes both
  colon-delimited and canonical whitespace-delimited milestone list items. A provider-free
  regression replays the missed grammar and proves unmapped cards plus uncovered milestones no
  longer skip validation; dependency and exact-command checks retain their existing behavior.
  The historical live tasklist now produces ten high milestone findings under the corrected
  source validator. Focused checks, frontend tests, Ruff, mypy, and all 1947 Python tests pass.
  Codex `T3` returns to `Next`; Claude `T4` is its direct successor.

- `2026-07-20` the fresh `ee30835` Codex run passed and was manually audited through
  `review-spec`, then exposed a tasklist/plan validator gap before implementation. The generated
  task cards omitted exact `M1`-`M5` references, but cross-document validation reported pass
  because its milestone collector accepted only `- M1: ...` while the production plan grammar
  accepted `- M1 ...`. The external run remains historical at `awaiting-quality-review`.
  Runtime-neutral validator task `W36-E7-S4-T15` is promoted to `Next`; Codex `T3` remains blocked
  pending regression coverage, full checks, and another fresh tracked-snapshot run.

- `2026-07-20` `W36-E7-S4-T14` is complete: installed-UI checkpoints now give cold startup a
  bounded 30-second deadline and each sequential API request a bounded 10-second response budget.
  Transcript evidence reports the full phase bound and recognizes socket timeouts even when the
  semantic failure summary is generic. Provider-free fixtures prove a response after the legacy
  two-second boundary succeeds, a real timeout remains bounded, and the full transition/cleanup
  matrix remains compatible. Codex `T3` returns to `Next`; Claude `T4` is its direct successor.

- `2026-07-20` two fresh Codex runs on `27e4771` independently passed their product stages and
  validators, then failed the harness post-stage frontend gate at its fixed 10-second boundary.
  r5 started UI but the two-second dashboard request timed out; five read-only reproductions on
  the same installed run returned 200 in 1.71-1.91 seconds. r6 did not finish cold UI startup
  within the same shared 10-second budget. Both bundles remain historical and external. Bounded
  runtime-neutral checkpoint-supervision task `W36-E7-S4-T14` is promoted to `Next`; Codex `T3`
  remains blocked pending provider-free timeout coverage and another fresh run.

- `2026-07-20` `W36-E7-S4-T13` is complete: authored live tasks may declare exact canonical
  repository-relative scope prefixes, manifest loading rejects unsafe values through the shared
  parser, bootstrap renders only those values, and prose-only legacy tasks omit the optional scope
  document instead of creating invalid policy. The Hono medium scenario now bounds its four
  runtime/test files. Focused harness checks, Ruff, mypy, wheel build, and all 1942 Python tests
  pass. Codex `T3` returns to `Next` for a fresh tracked-snapshot run, followed by Claude `T4`.

- `2026-07-20` the fresh `e64a923` Codex run passed and was manually audited through `tasklist`,
  then failed closed on Implement T1 because live bootstrap wrote prose-only
  `allowed-write-scope.md`. The canonical parser correctly rejected the document and the bounded
  repair path removed task-local test edits but could not repair harness-owned context. The
  historical bundle remains external. Runtime-neutral manifest/bootstrap task
  `W36-E7-S4-T13` is promoted to `Next`; Codex `T3` is blocked pending its regression and a fresh
  tracked-snapshot run.

- `2026-07-20` `W36-E7-S4-T12` is complete: validator-verdict reconciliation now distinguishes
  an existing byte-equal canonical match from an absent field, collapses legacy duplicates, and
  is byte-stable across repeated calls. Focused core/CLI and full stage-run matrices pass. Codex
  `T3` returns to `Next` for another fresh tracked-snapshot run, followed by Claude `T4`.

- `2026-07-20` the first `9fde2f1` Codex idea checkpoint exposed non-idempotent success
  reconciliation: an already canonical validator-verdict line was treated as if no regex match
  existed because replacement text was byte-equal, so each reconciliation appended another
  `Validator verdict: pass`. The run is stopped before research. Bounded terminal-normalization
  task `W36-E7-S4-T12` is promoted to `Next`; Codex `T3` remains blocked pending a fresh run.

- `2026-07-20` `W36-E7-S4-T11` is complete: success-owned stage-result fields are normalized and
  fully validated before the repair-budget decision. Duplicate/non-monotonic attempt history now
  produces canonical findings, a repair brief, and a bounded retry instead of a terminal core
  exception; exhausted retries remain fail-closed. Codex `T3` returns to `Next` for a fresh
  tracked-snapshot run, followed by independent Claude `T4`.

- `2026-07-20` the fresh post-continuation Codex run passed `idea` and `research`, then exposed a
  general validation-order defect in `plan`: duplicate `Attempt 1` entries correctly emitted
  `SEM-INCOMPLETE-SECTION`, but only after success normalization, where the finding became a hard
  orchestration exception instead of consuming the configured repair budget. The failed bundle
  remains historical. Bounded runtime-neutral task `W36-E7-S4-T11` is promoted to `Next`; Codex
  `T3` is blocked until a provider-free repair regression passes and a fresh run starts.

- `2026-07-20` `W36-E7-S4-T10` is complete: immutable unbounded run manifests now accept only
  canonical forward stage reuse after every preceding stage in that run has succeeded. Public CLI
  coverage proves `research -> plan` progression while core matrices keep skipped, failed,
  backward, runtime-mismatched, and configuration-mismatched reuse fail-closed. The historical
  failed Codex bundle is retained; `S4-T3` returns to `Next` for a fresh tracked-snapshot run.

- `2026-07-20` the first installed Codex medium run passed `idea` and its quality checkpoint, then
  exposed a general public-stage continuation defect before `research`: the immutable manifest
  retained `stage_target=idea`, while the next canonical `stage run research --run-id ...` was
  rejected as a target mismatch before adapter launch. The historical run is not repaired in
  place. Bounded core/CLI regression task `W36-E7-S4-T10` is promoted to `Next`; Codex `T3` is
  explicitly blocked and parked until a fresh tracked-snapshot run can start.

- `2026-07-20` `W36-E7-S4-T9` is complete: browser diagnostics now retain deliberate
  `net::ERR_ABORTED` route-restoration cancellations separately from network failures. The exact
  runtime-readiness cancellation is asserted, while console, page, origin, HTTP, and real request
  failures remain gating. Codex medium execution `S4-T3` returns to `Next`, followed by Claude
  `T4`.

- `2026-07-20` `W36-E7-S4-T8` is complete: the token-driven mobile topbar uses one-pixel
  vertical padding, restoring the measured 80-pixel maximum while retaining 44-pixel controls,
  primary-before-maintenance order, desktop composition, and clean frontend behavior at both
  mobile viewports. Route-cancellation diagnostics `T9` is promoted to `Next`.

- `2026-07-20` `W36-E7-S4-T7` is complete: generic browser descriptors now read exact
  core-owned runtime selection and terminal recommendations, and clean-terminal follow-up draft
  coverage opens the supported secondary-action disclosure before preserving its session state.
  Twenty rendered fixture/draft cases pass. Mobile header correction `T8` is promoted to `Next`,
  followed by route-cancellation diagnostics `T9`.

- `2026-07-20` the first clean sequential full browser gate reached 179 passes and exposed
  three independent acceptance defects: stale generic fixture actions/markers, a reproducible
  81-pixel mobile header against the 80-pixel contract, and intentional route-reload request
  cancellation reported as network failure. Tasks `S4-T7..T9` split those outputs; `T7` is
  promoted to `Next`, while provider execution remains parked behind a green full browser gate.

- `2026-07-20` `W36-E7-S4-T6` is complete: active-Studio shell, Document Canvas, and
  Evidence Inspector browser contracts now use a nonterminal stale-QA fixture, while fresh
  terminal QA remains exclusively owned by Flow Complete. All affected rendered cases pass with
  production Studio behavior unchanged. Codex medium execution `S4-T3` returns to `Next`,
  followed by Claude `T4`.

- `2026-07-20` pre-live final acceptance exposed browser-test contract drift: three tests
  expected active Studio context, Document Canvas, or Evidence Inspector from fresh terminal QA,
  where the accepted contract correctly renders Flow Complete. Bounded test-only task
  `W36-E7-S4-T6` is inserted in `Next`; the Codex run returns to `Soon`. A concurrently observed
  lifecycle timeout and History timeout passed isolated reruns and remain classified as resource
  contention, not product defects.

- `2026-07-20` `W36-E7-S4-T2` is complete: a provider-neutral executable preflight now
  validates clean tracked source, external provider layouts, scenario containment, full live
  scope, command readiness, and post-run source identity without allocating run state. Static
  boundaries reject live scenario literals in runtime product/prompts/contracts and reject
  harness imports outside the explicit eval facade. Codex execution `S4-T3` is promoted to
  `Next`, followed by independent Claude execution `T4`.

- `2026-07-20` `W36-E7-S4-T1` is complete: the Wave 36 prod-like contract fixes
  `AIDD-LIVE-007`, its Hono revision, installed tracked-snapshot wheel, external provider roots,
  public operator surfaces, manual stage/final quality audits, rendered Studio inspection, and
  strict product/evaluator isolation. Provider-free conformance `S4-T2` is promoted to `Next`,
  followed by the first Codex execution `T3`.

- `2026-07-20` Wave 36 final acceptance now includes the isolated prod-like slice
  `W36-E7-S4`. The installed medium `AIDD-LIVE-007` flow runs through Codex and Claude Code
  before observed sessions, and both providers are repeated on the final post-reconciliation
  revision. `S4-T1` is active, followed by provider-free isolation gates `T2`; raw worktrees,
  provider state, and evidence remain outside the source checkout.

- `2026-07-18` `W36-E7-S2-T8` is complete: final full-suite acceptance now follows
  Studio-only module ownership for quality gates, History, and next-flow fields; the no-run task
  endpoint asserts its truthful blocker; mobile controls consume the shared touch token; and
  process-tree tests wait for the child signal handler before requesting termination. The
  non-gating manual-evidence fixture also accepts the canonical bounded frontend `skipped` state
  while still rejecting failures. Public UI and runtime semantics are unchanged. The active queue
  remains the five real sessions `S3-T2`.

- `2026-07-18` `W36-E7-S2-T7` is complete: four pre-existing overlong browser-fixture
  source lines are mechanically wrapped without changing JavaScript evaluation or rendered DOM.
  The repository-wide Ruff gate and the owning History/Recovery fixtures now share the same
  maintained formatting boundary. The active queue remains the real-session task `E7-S3-T2`.

- `2026-07-18` `W36-E7-S3-T1` is complete: the observed-acceptance contract defines
  eight bounded first-time-operator tasks for Setup, Inbox, monitoring, question/runtime
  recovery, QA remediation, History, and terminal continuation. Every task records completion,
  time, wrong actions, assistance, confidence, first decisive confusion, durable outcome, and a
  stable finding id; the session summary is anonymized and explicitly separate from automation.
  The five real sessions `T2` are promoted to `Next`, followed by reconciliation `T3`.

- `2026-07-18` `W36-E7-S2-T5` and slice `W36-E7-S2` are complete: commit
  `28f8e26` passed the source-installed packaged-UI runner with Chromium `149.0.7827.55`,
  exact discovery/execution of all 12 journeys, all five viewports, clean browser diagnostics,
  loopback-only requests, and bounded cleanup. The accepted schema-v1 record contains no
  generated workspace or human-session data. Browser rollout also closes `W36-E7-S1`, the
  Studio cutover slice `W36-E5-S10`, and Epic `W36-E5`. Observed-operator scripting `S3-T1`
  is promoted to `Next`, followed by the five-session task `T2`.

- `2026-07-18` `W36-E7-S2-T6` is complete: Document/Evidence now uses canonical
  Studio route context against a nonterminal stale fixture, the intervention journey keeps its
  canonical recovery mode through History/Back and readiness refresh, and Studio removes nested
  document/recent-artifact scroll owners. Measured CI and release timeouts remain bounded at 45
  minutes. The complete runner discovered and executed all 12 journeys with no failed ids; the
  formal evidence record `T5` returns to `Next`, followed by observed-operator scripting `S3-T1`.

- `2026-07-18` the first full `W36-E7-S2-T5` attempt discovered and executed all 12
  declared journeys but exposed two browser-contract regressions after selector retirement:
  Document/Evidence used a presentation-only query without canonical Studio context, and an
  intervention History/Back case could race a readiness rerender. Bounded regression task
  `W36-E7-S2-T6` is inserted in `Next`; the evidence pass remains unaccepted in `Soon`.

- `2026-07-18` `W36-E7-S2-T4` is complete: release preflight now invokes the same
  packaged-UI journey runner used locally and in CI. Journey failures, runner/preflight errors,
  browser absence, launch infrastructure errors, and timeout produce explicit failing checks;
  none are treated as skips. The source-installed full pass `T5` is promoted to `Next`, followed
  by the observed-operator script `S3-T1`.

- `2026-07-18` `W36-E7-S2-T3` is complete: the local-project contract now has a
  schema-v1 provider-free browser-pass template covering source version, fixture, all five
  viewports, the 12 discovered/executed journeys, accessibility, geometry, console/network
  diagnostics, and bounded cleanup. Human timing and confidence remain a separate acceptance
  record. Release-preflight enforcement `T4` is promoted to `Next`, followed by the full pass
  `T5`.

- `2026-07-18` `W36-E7-S2-T2` is complete: CI now runs the shared packaged-UI
  journey command in a dedicated provider-free Python 3.12 job with a pinned Chromium cache,
  bounded timeout, and an explicit build dependency. The full-pass evidence template `T3` is
  promoted to `Next`, followed by release-preflight enforcement `T4`.

- `2026-07-18` `W36-E5-S10-T5` is complete: README, operator handbook, local-project
  E2E, and frontend architecture now describe the shipped Studio-only surface. The accepted
  rollback record is explicitly historical and non-normative. Packaged browser CI `E7-S2-T2` is
  promoted to `Next`, followed by the full-pass evidence template `T3`.

- `2026-07-18` `W36-E5-S10-T4` is complete: the packaged UI no longer ships the
  presentation selector or legacy renderer branches. Studio renderers are called directly, dead
  rollback templates and CSS selectors are removed, and an asset-boundary test prevents their
  return. Studio-only documentation reconciliation `T5` is promoted to `Next`, followed by the
  packaged browser CI gate `E7-S2-T2`.

- `2026-07-18` `W36-E5-S10-T3` is complete: the temporary browser presentation
  selector no longer branches renderer selection. Missing, invalid, `ui=studio`, and the former
  `ui=legacy` value all resolve to Studio without changing API requests or durable state. Legacy
  asset removal `T4` is promoted to `Next`, followed by Studio-only docs reconciliation `T5`.

- `2026-07-18` `W36-E5-S10-T2` is complete: a source-installed Chromium check proved
  exact dashboard/timeline payload parity and identical guarded action availability between the
  default Studio and explicit legacy presentations. The completed source manifest remained
  byte-identical and browser diagnostics were clean. Selector removal `T3` is promoted to `Next`,
  followed by legacy renderer removal `T4`.

- `2026-07-18` `W36-E5-S10-T1` is complete: an absent presentation selector now
  resolves all parity-closed surfaces to Studio, while explicit `ui=legacy` remains the supported
  rollback path and invalid explicit values still fail back to legacy. Both presentations use
  the same API and mutation services. Rollback-window evidence `T2` is promoted to `Next`,
  followed by selector removal `T3`.

- `2026-07-18` `W36-E7-S2-T1` is complete: the developer-facing packaged-UI
  runner evaluates the packaged parity manifest through bounded Node `vm`, validates an explicit
  Python pytest-node registry, rejects duplicate/missing/live-provider entries before execution,
  runs all 12 journeys in stable numeric order, continues after failures, and verifies exact
  discovered/executed identity. Studio-default cutover `E5-S10-T1` is promoted to `Next`,
  followed by rollback-window evidence `T2`.

- `2026-07-18` `W36-E5-S9-T9` is complete: Flow Complete is now
  `parity_closed` after the full terminal journey proved core recommendation, drafts, independent
  clone identity, manual eval, archive readback, stale exclusion, and immutable source evidence.
  Legacy remains an explicit rollback presentation until cutover. Slice `W36-E5-S9` is closed;
  packaged-UI runner `E7-S2-T1` is promoted to `Next`, followed by default cutover `E5-S10-T1`.

- `2026-07-18` `W36-E7-S1-T8` is complete: all five viewports exercise the
  core-recommended terminal decision, session follow-up draft, independent clone identity,
  non-mutating eval handoff, and append-only archive readback while preserving the completed
  source manifest hash. Clean, warning, failed, and blocked fresh QA use the exact core outcome;
  stale QA has no Flow Complete. Parity closure `S9-T9` is promoted to `Next`, followed by the
  packaged-UI runner `E7-S2-T1`.

- `2026-07-18` `W36-E5-S9-T8` is complete: mobile Flow Complete removes redundant
  cockpit chrome, places final QA status and the core recommendation before supporting evidence,
  keeps the primary control touch-sized, and leaves secondary outcomes in a keyboard-accessible
  disclosure without horizontal overflow at `320x568` or `390x844`. Terminal journey
  `W36-E7-S1-T8` is promoted to `Next`, followed by parity closure `S9-T9`.

- `2026-07-18` `W36-E5-S9-T7` is complete: Studio archive confirmation and durable
  readback use the existing append-only archive endpoint. The presentation names the operation
  as visibility metadata, keeps the completed source run immutable, and returns canonical
  dashboard state without hiding retained evidence. Mobile terminal presentation `T8` is
  promoted to `Next`, followed by terminal journey `W36-E7-S1-T8`.

- `2026-07-18` `W36-E5-S9-T6` is complete: Studio's manual eval handoff names
  the exact source work item/run, installed AIDD version, operator-selected scenario source, and
  supported `aidd eval execute` command. Opening it changes browser presentation state only and
  sends no workflow, repair, or eval mutation. Archive disposition `T7` is promoted to `Next`,
  followed by mobile terminal composition `T8`.

- `2026-07-18` `W36-E5-S9-T5` is complete: Studio clone uses the shared wizard host
  but remains bound to the existing clone-draft and clone-preflight services, with an explicit
  clone lineage relationship and independent work-item/run identity. No source-run mutation or
  follow-up payload alias was introduced. Manual eval handoff `T6` is promoted to `Next`,
  followed by archive disposition `T7`.

- `2026-07-18` `W36-E5-S9-T4` is complete: Studio hosts the existing follow-up
  source-selection, session-draft, definition, preflight, guarded mutation, and launch sequence
  instead of introducing a second wizard or service path. The source run remains read-only and
  matching durable success remains the only draft-clear boundary. Clone `T5` is promoted to
  `Next`, followed by manual eval handoff `T6`.

- `2026-07-18` `W36-E5-S9-T3` is complete: Studio Flow Complete renders only when
  the additive terminal-handoff contract carries a valid core-owned recommendation. Its primary
  action and rationale are read directly from that contract; alternative allowed outcomes remain
  under Other next actions. Missing, stale, malformed, and nonterminal QA do not render the
  surface. Follow-up `T4` is promoted to `Next`, followed by clone `T5`.

- `2026-07-18` `W36-E5-S8-T7` is complete: the History surface is now
  `parity_closed` after the five-viewport journey proved canonical timeline, comparison,
  lineage, archive, and evidence reachability. Default and explicit legacy renderers remain
  available as rollback presentations until cutover. Slice `W36-E5-S8` is closed; Flow Complete
  `S9-T3` is promoted to `Next`, followed by follow-up `S9-T4`.

- `2026-07-18` `W36-E7-S1-T5` is complete: the provider-free History journey passes
  all five viewports with typed frames, retained comparison, parent deep-link navigation,
  Back/reload restoration, archive readback, clean browser diagnostics, and byte-identical
  current/source manifests. History parity closure `S8-T7` is promoted to `Next`, followed by
  Flow Complete renderer `S9-T3`.

- `2026-07-18` `W36-E5-S8-T6` is complete: at `320x568` and `390x844`, Studio
  History uses a single-column chronological drill-down with full-width touch controls, visible
  overflow, and no nested horizontal Filmstrip. The History browser journey `W36-E7-S1-T5` is
  promoted to `Next`, followed by parity closure `S8-T7`.

- `2026-07-18` `W36-E5-S8-T5` is complete: Studio History renders the canonical
  append-only archive disposition with legacy-fallback source labeling and retains direct
  navigation to run History, artifacts, and logs. The renderer does not mutate completed-run
  evidence. Mobile chronological History `T6` is promoted to `Next`, followed by journey `T5`.

- `2026-07-18` `W36-E5-S8-T4` is complete: Studio History renders the canonical
  parent/current/child lineage projection and routes every retained relation through the shared
  safe route-intent codec. The renderer is navigation-only and owns no workflow mutation or
  lineage persistence. Append-only archive disposition `T5` is promoted to `Next`, followed by
  the mobile chronological presentation `T6`.

- `2026-07-18` `W36-E5-S8-T3` is complete: Studio History reuses the canonical bounded
  run-comparison endpoint and renders prompt, stage, artifact, and validator deltas only with
  retained baseline/target paths. Missing paths and snapshots are explicit unavailable states;
  no historical content is reconstructed. Legacy comparison remains unchanged. Immutable
  lineage `T4` is promoted to `Next`, followed by archive overlay `T5`.

- `2026-07-18` `W36-E5-S8-T2` is complete: a separate packaged Studio History
  renderer consumes typed frames, exposes a collapsed Filmstrip and selected-frame evidence,
  pauses only browser auto-follow for historical selection, and returns to live without a
  runtime mutation. Legacy History remains the rollback renderer and the surface is now a
  reachable `candidate`. Retained-evidence comparison `T3` is promoted to `Next`.

- `2026-07-18` `W36-E5-S8-T1` is complete: `/api/run/timeline` retains its existing
  `events` and warnings and additively exposes immutable stage-attempt, task-attempt,
  finalization-attempt, and event-marker frames. Every frame has a stable durable identity,
  status, stage/task/attempt coordinates, timestamp when authored, and only retained evidence
  references. Filmstrip renderer `T2` is promoted to `Next`, followed by comparison `T3`.

- `2026-07-18` `W36-E5-S7-T5` and slice `W36-E5-S7` are complete: Implement and
  Review/QA are `parity_closed`. Default legacy, explicit legacy, and Studio consume
  byte-equivalent canonical task, implementation, Review, and QA read models, while keeping
  the same task/finalization and remediation mutation hooks. History frame projection
  `W36-E5-S8-T1` is promoted to `Next`, followed by its renderer `T2`.

- `2026-07-18` `W36-E7-S1-T4` is complete: provider-free Review/QA fixtures render
  exact finding, acceptance, evidence, risk, and issue identities across all five viewports;
  rejected/not-ready QA stays nonterminal. One selected Review finding creates one durable
  stage-scoped remediation request, while stale QA survives reload and requires the guarded
  downstream rerun. Journey accessibility also fixes Decision Bar and QA-choice target sizes.
  Parity closure `W36-E5-S7-T5` is promoted to `Next`, followed by History frame projection.

- `2026-07-18` `W36-E7-S1-T9` is complete: provider-free Chromium fixtures preserve a
  succeeded dependency when the next task fails, expose Resume and finalization retry, render
  modified/untracked/deleted repository evidence with canonical scope, and open Review only
  after successful aggregate finalization. The journey also promotes the implemented
  Implement and Review/QA renderers to reachable `candidate` status. Review/QA journey `T4`
  is promoted to `Next`, followed by parity closure `W36-E5-S7-T5`.

- `2026-07-18` `W36-E5-S7-T4` is complete: selected Review/QA identities still launch
  the guarded canonical remediation service, while Studio now exposes pending implement
  readback, exact stale Review/QA stages and invalidator identity, and the existing guarded
  downstream rerun. Terminal handoff remains explicitly blocked while stale evidence exists.
  Implement journey `W36-E7-S1-T9` is promoted to `Next`, followed by Review/QA journey `T4`.

- `2026-07-18` `W36-E5-S7-T3` is complete: Studio Review/QA gates render exact
  finding identities, severity/disposition, acceptance and evidence references, residual
  risks, known issues, and explicit missing/rejected/not-ready blockers. Existing API fields
  remain compatible; acceptance and evidence-reference fields are additive. Remediation and
  stale state `T4` is promoted to `Next`, Implement journey `W36-E7-S1-T9` to `Soon`.

- `2026-07-18` `W36-E5-S7-T2` is complete: Studio renders canonical repository and
  implementation evidence in a Document Canvas with textual Added/Removed/Changed markers,
  allowed/project scope, `.aidd/` separation, and explicit report/repository claim mismatch.
  The legacy diff renderer remains unchanged. Review/QA gate `T3` is promoted to `Next` and
  remediation/stale state `T4` to `Soon`.

- `2026-07-18` `W36-E5-S7-T1` is complete: Studio has a separate implementation
  quality-gate renderer over canonical `/api/tasks`; dependency readiness, task attempts,
  blockers, finalization eligibility, and Review progression remain core-owned. The legacy
  control-center renderer remains available for rollback. Repository evidence `T2` is
  promoted to `Next` and Review/QA gate `T3` to `Soon`.

- `2026-07-18` `W36-E5-S6-T6` is complete: runtime/validation Recovery is
  `parity_closed`; Studio, default legacy, and explicit legacy resolve identical durable
  first-failure, repair-history, raw-log, evidence-path, and intervention read models.
  Slice `W36-E5-S6` is closed. Implement Studio `W36-E5-S7-T1` is promoted to `Next`
  and repository evidence `T2` to `Soon`.

- `2026-07-18` `W36-E7-S1-T3` is complete: launch, authentication, timeout,
  cancellation, no-progress, repair-available, and repair-exhausted durable fixtures pass
  the five-viewport Studio journey with exact first-failure evidence, truthful stopped state,
  no implicit mutation, and bounded browser/UI cleanup. Recovery parity `W36-E5-S6-T6`
  is promoted to `Next` and Implement Studio `W36-E5-S7-T1` to `Soon`.

- `2026-07-18` `W36-E5-S6-T5` is complete: mobile runtime failure, repair-available,
  and repair-exhausted Recovery order failure, one primary decision, then evidence;
  both target mobile viewports retain 44px controls, one scroll owner, and no horizontal
  overflow. Recovery journey `W36-E7-S1-T3` is promoted to `Next` and parity closure
  `W36-E5-S6-T6` to `Soon`.

- `2026-07-18` `W36-E5-S6-T4` is complete: repair-exhausted and explicit-stop
  Recovery expose one stage-scoped `Request Change` primary action, retain supporting
  evidence, and contain no enabled repair mutation. Mobile Recovery `T5` is promoted to
  `Next` and the provider-free Recovery journey `W36-E7-S1-T3` to `Soon`.

- `2026-07-18` `W36-E5-S6-T3` is complete: every rendered validator finding exposes
  its exact code/rule, category, document path, line, severity, occurrence count, and
  validator-report provenance. `Run Repair` remains enabled only for the backend-owned
  `repair-available` status. Repair-exhaustion Recovery `T4` is promoted to `Next` and mobile
  Recovery layout `T5` to `Soon`.

- `2026-07-18` `W36-E5-S6-T2` is complete: reconnecting, recovered, offline,
  expired-job, and manual reconnect surfaces retain the absolute log cursor, state explicitly
  that no terminal runtime evidence was observed, and route operators to durable `runtime.log`.
  Existing bounded retry, expired-job reconciliation, and server-authoritative readback remain
  unchanged. Validator Recovery `T3` is promoted to `Next` and repair-exhaustion Recovery `T4`
  to `Soon`.

- `2026-07-18` `W36-E5-S6-T1` is complete: runtime/validation Recovery enters
  `candidate` rollout with typed launch, authentication, timeout, cancellation, provider,
  no-progress, and legacy failures. The surface exposes stopped state and the exact last
  durable signal; an eligible same-stage retry is primary while runtime failure explicitly
  leaves validation repair budget untouched. Connection Recovery `T2` is promoted to `Next`
  and validator Recovery `T3` to `Soon`.

- `2026-07-18` `W36-E5-S5-T7` is complete: runtime approval Recovery is
  `parity_closed`. Studio and explicit legacy presentation both launch the same provider-free
  waiting job, post through the same decision endpoint, and render the same single durable
  winner; the full action/conflict matrix remains covered by journey `W36-E7-S1-T11`.
  Human-decision Recovery slice `W36-E5-S5` is closed. Runtime-failure Recovery `S6-T1` is
  promoted to `Next` and connection Recovery `S6-T2` to `Soon`.

- `2026-07-18` `W36-E5-S5-T6` is complete: intervention Recovery is
  `parity_closed`. Studio and explicit legacy presentation both use the same guarded
  stage-interact service: allowed fixtures create one durable request and downstream-blocked
  fixtures create none. Approval parity `T7` is promoted to `Next`; runtime-failure Recovery
  `W36-E5-S6-T1` waits in `Soon`.

- `2026-07-18` `W36-E5-S5-T5` is complete: question Recovery is `parity_closed`.
  Studio and explicit legacy presentation both submit the exact same `/api/answers` payload,
  persist the same resolved answer, and clear only the owning session draft. Intervention
  parity `T6` is promoted to `Next` and approval parity `T7` to `Soon`.

- `2026-07-18` `W36-E7-S1-T11` is complete: a real provider-free live approval job
  exercises scope, risk, pending state, allow, deny, cancel, explicit session confirmation,
  and a concurrent opposite-decision conflict across the five browser viewports. Every case
  resolves to one durable CAS winner and matching audit row with exact runtime/stage identity.
  Question parity `W36-E5-S5-T5` is promoted to `Next` and intervention parity `T6` to
  `Soon`.

- `2026-07-18` `W36-E7-S1-T10` is complete: allowed and downstream-blocked
  intervention journeys run provider-free across all five browser viewports. They prove
  session draft restore across reload and Back, exact run/stage identity, one guarded
  stage-interact request, successful draft cleanup, downstream-success remediation routing,
  and zero durable requests when ineligible. Runtime approval journey `T11` is promoted to
  `Next`; question parity closure `W36-E5-S5-T5` waits in `Soon` for the complete journey set.

- `2026-07-18` `W36-E7-S1-T6` is complete: the question Recovery journey runs
  provider-free across all five browser viewports and covers partial/deferred blocking,
  session draft restore, reload and Back restoration, failed-answer preservation, successful
  durable readback, and answer/resume through the existing stage service. The journey exposed
  and closed a readiness-refresh race before resume. Intervention journey `T10` is promoted
  to `Next` and approval journey `T11` to `Soon`.

- `2026-07-18` `W36-E5-S5-T4` is complete: question, intervention, and approval
  Recovery share a decision-first mobile contract at `320x568` and `390x844`. Compact
  surfaces remove competing shell chrome, keep the primary control in the initial viewport,
  enforce 44px visible controls, place evidence after the decision, and avoid page-level
  horizontal overflow. Question journey `W36-E7-S1-T6` is promoted to `Next` and the
  intervention journey `T10` to `Soon`.

- `2026-07-18` `W36-E5-S5-T3` is complete: approval Recovery is a Studio candidate
  with explicit request scope, breadth, risk, pending status, reason capture, session-wide
  confirmation, and durable-winner markers. The existing guarded decision endpoint remains
  authoritative: allow/deny/cancel are idempotent, conflicts render the compare-and-set winner,
  and session approval cannot post before confirmation. Human-decision mobile layout `T4` is
  promoted to `Next` and the question journey `W36-E7-S1-T6` to `Soon`.

- `2026-07-18` `W36-E5-S5-T2` is complete: intervention Recovery is a Studio
  candidate with explicit work-item/run/stage identity, core-owned eligibility, session
  draft preservation, and one guarded `/api/stage/interact` path. Allowed submit creates one
  stage-scoped operator request; succeeded downstream evidence disables submit, routes the
  operator toward existing remediation/follow-up surfaces, and creates no request. Approval
  `T3` is promoted to `Next` and decision-first mobile layout `T4` to `Soon`.

- `2026-07-18` `W36-E5-S5-T1` is complete: question Recovery is a Studio candidate
  with exact durable QID, resolved/partial/deferred status markers, explicit editor
  resolution, and a visible restored-session-draft indicator. Existing guarded answer
  submission still preserves failed drafts, clears only after matching durable readback,
  and leaves partial/deferred blocking. Intervention `T2` is promoted to `Next` and
  approval `T3` to `Soon`.

- `2026-07-18` `W36-E5-S4-T5` is complete: active Studio and Document/Evidence are
  `parity_closed`; `ui=studio` renders one workbench and one bounded Document Canvas, while
  missing/default and `ui=legacy` retain the legacy cockpit plus Recovery, Evidence, and
  persisted-log reachability. The accepted active/reconnect and Document/Evidence journeys
  continue to own their five-viewport evidence. Slice `W36-E5-S4` is closed; question
  Recovery `W36-E5-S5-T1` is promoted to `Next` and intervention `T2` to `Soon`.

- `2026-07-18` `W36-E5-S3-T5` is complete: Inbox is `parity_closed`; explicit
  `ui=studio` renders one Studio Inbox, while missing/default and `ui=legacy` retain one
  Project Home with no presentation-only dismissal. The accepted five-viewport journey
  continues to own priority, routing, and Running now evidence. Slice `W36-E5-S3` is closed;
  active Studio parity `W36-E5-S4-T5` is promoted to `Next`, with `Soon` empty until the
  ordered cross-slice series reaches Recovery.

- `2026-07-18` `W36-E4-S1-T7` is complete: Guided Setup is `parity_closed`; the full
  five-viewport Studio journey remains green, while an explicit `ui=legacy` browser check
  reaches the rollback presentation through the same `/api/onboarding/project` service and
  identical project-root payload. Slice `W36-E4-S1` and Epic `W36-E4` are closed. Inbox
  parity `W36-E5-S3-T5` is promoted to `Next`; `Soon` remains empty until the ordered
  cross-slice parity series advances.

- `2026-07-18` `W36-E7-S1-T12` is complete: all five viewports verify durable Inbox
  priority, bounded Running now correlation, exact work-item/run/stage routing, a single
  core-approved action, first-viewport visibility, keyboard activation, reload restoration,
  and blocking-item non-dismissal. Cross-work-item routing reuses the canonical resume
  service before browser navigation, and intentional navigation aborts are distinguished
  from request failures. Guided Setup parity `W36-E4-S1-T7` is promoted to `Next`;
  `Soon` remains empty until the ordered parity series reaches Inbox.

- `2026-07-18` `W36-E7-S1-T7` is complete: all five viewports exercise bounded
  Preview/Source/Diff, exact validator/source/provenance evidence, explicit missing
  requirements, safe artifact-key selection, reload and Back restoration, and persisted
  runtime-log drill-down. The browser boundary rejects traversal-like keys without reading
  arbitrary paths, zero-value Inspector behavior remains covered, Studio presentation now
  survives canonical navigation, and mobile evidence controls satisfy the shared touch and
  scroll-owner gates. Inbox journey `S1-T12` is promoted to `Next`; `Soon` remains empty
  until the ordered parity-closure series begins.

- `2026-07-18` `W36-E7-S1-T2` is complete: all five viewports exercise a real
  provider-free UI job through measured output, explicit silence, one intentional
  transient polling failure, cursor-preserving recovery, cancellation, terminal durable
  readback, and persisted `runtime.log`. The journey also removed the remaining Activity
  nested-scroll trap, corrected content-growing Studio rows and bounded long identities,
  and fixed interactive hover contrast. Document/Evidence journey `S1-T7` is promoted to
  `Next`; `Soon` remains empty because Inbox journey `T12` is not its direct dependency
  successor.

- `2026-07-18` `W36-E7-S1-T1` is complete: the provider-free Guided Setup journey now
  validates both create and resume branches across all five viewports, preserves the
  selected runtime through readiness refresh, launches the workflow through the shared
  mutation seam, and exposes the correlated Running now Inbox item. The executable gates
  also corrected stale Decision Bar rendering, Inbox refresh on navigation, touch-target
  sizing, and hover contrast without changing service payloads. `S1-T2` is promoted to
  `Next`; `Soon` remains empty because the following document journey is not its direct
  dependency successor.

- `2026-07-18` `W36-E5-S2-T4` is complete: all eight stage controls retain exact stage
  identity, durable status in their accessible name, a touch-safe height, and unclipped
  bounds at `320x568` and `390x844`. The existing compact two-column navigation already
  met the contract, so the accepted change is its executable regression guard. `W36-E5-S2`
  is closed; Guided Setup journey `W36-E7-S1-T1` is promoted to `Next` and active Studio
  journey `T2` to `Soon`.

- `2026-07-18` `W36-E5-S2-T3` is complete: one declarative mobile priority attribute now
  orders every operator mode as cockpit/decision → stage context → sidebar evidence →
  history/activity drill-down. The repeated recovery/live/terminal/stale ordering selectors
  are removed, and the full eight-case mobile regression remains green. `S2-T4` is promoted
  to `Next`; `Soon` stays empty until its cross-slice journey successor is selected.

- `2026-07-18` `W36-E5-S2-T2` is complete: no-run Studio, durable-running Studio, and
  Inbox place their actual primary control inside the initial `320x568` and `390x844`
  viewport. The mobile presentation puts decision controls before supporting progress,
  hides empty Inbox sections, and keeps sidebar/evidence surfaces below the decision.
  `S2-T3` is promoted to `Next` and `S2-T4` to `Soon`.

- `2026-07-18` `W36-E5-S2-T1` is complete: the Studio mobile header is bounded to 80px
  at `320x568` and `390x844`, retains compact work-item/run context and runtime selection,
  and visually places the existing keyboard-accessible maintenance overflow in the header
  without moving it ahead of the primary decision in document/focus order. `S2-T2` is
  promoted to `Next` and `S2-T3` to `Soon`.

- `2026-07-18` `W36-E4-S2-T3` is complete: Guided Setup and Studio now present binary,
  execution-command, authentication, capability, protected-write-scope, and latest-launch
  evidence as separate dimensions. Malformed scope is explicit and the UI makes no generic
  `ready` or `No upstream write` claim. `W36-E4-S2` is closed; compact mobile shell `S2-T1`
  is promoted to `Next` and its direct successor `S2-T2` to `Soon`.

- `2026-07-18` `W36-E5-S4-T4` is complete: Studio observation displays only measured
  job elapsed/output age, durable stage milestones, backend silence/cancellation state,
  and an explicit live-or-persisted log transition; it never renders synthetic percent
  progress or embeds raw logs in the default viewport. `W36-E4-S2-T3` is promoted to
  `Next`; the mobile shell remains parked until that standalone readiness task completes.

- `2026-07-18` `W36-E5-S4-T3` is complete: Studio projects findings, exact contract
  source references, version provenance, and related artifacts from the already loaded
  workbench snapshot, while zero-value evidence keeps the Inspector absent. `S4-T4` is
  promoted to `Next`; runtime-readiness presentation `W36-E4-S2-T3` remains parked until
  the active-Studio implementation sequence completes.

- `2026-07-18` `W36-E5-S4-T2` is complete: candidate Studio loads its Document Canvas
  from the canonical bounded stage-workbench endpoint and switches Preview, Source, and
  Diff over the same safe selected key. Missing, escaped, and truncated documents remain
  explicit; no arbitrary path reader or duplicate document grammar was added. `S4-T3` is
  promoted to `Next` and dependency-ready `S4-T4` to `Soon`.

- `2026-07-18` `W36-E5-S4-T1` is complete: the active-Studio candidate composes the
  existing mode navigation, compact durable context, canonical stage rail, one authoritative
  decision slot, and a read-only stage summary without duplicating service actions. No-run,
  active, blocked, and terminal Chromium fixtures retain context and one marked primary action.
  `S4-T2` is promoted to `Next` and `S4-T3` to `Soon`.

- `2026-07-18` `W36-E5-S3-T4` is complete: `ui=studio` renders the four ordered Inbox
  sections from the additive read model, preserves server-owned actions and exact
  work-item/run/stage routes, and keeps missing/default plus explicit legacy presentation
  on Project Home. `W36-E5-S4-T1` is promoted to `Next` and `S4-T2` to `Soon`; Inbox
  parity `S3-T5` remains gated by browser journey `W36-E7-S1-T12`.

- `2026-07-18` `W36-E5-S3-T3` is complete: `GET /api/inbox` now exposes the
  durable core projection plus bounded Running now state, rejects external project/path
  selectors, and leaves all mutation endpoints unchanged. `W36-E5-S3-T4` is promoted to
  `Next`; `Soon` remains empty until the Inbox implementation slice reaches its parity gate.

- `2026-07-18` `W36-E5-S3-T2` is complete: bounded UI job summaries now carry
  monotonic work-item/run/stage identity, and the Running now composition filters terminal
  jobs, retains explicit legacy-identity gaps, and leaves durable Inbox eligibility intact.
  `W36-E5-S3-T3` is promoted to `Next` and `T4` to `Soon`.

- `2026-07-18` `W36-E5-S3-T1` is complete: immutable core Inbox sections now
  project durable work-item/run/stage identity and the existing core-approved next action
  in deterministic order without inventing live-job state. `W36-E5-S3-T2` is promoted to
  `Next` and `T3` to `Soon`.

- `2026-07-18` `W36-E5-S1-T5` and slice `W36-E5-S1` are complete: the desktop
  Studio shell owns the single primary vertical scroll path, while stage navigation,
  content, Inspector, drawers, and Filmstrip remain reachable without nested scroll traps.
  `W36-E5-S3-T1` is promoted to `Next` and `T2` to `Soon`.

- `2026-07-18` `W36-E5-S1-T4` is complete: Refresh, Open `.aidd`, Stop server, and
  other service-maintenance controls now live in one labelled native overflow after the
  current Studio decision in visual and keyboard order. `W36-E5-S1-T5` is promoted to
  `Next`; `Soon` remains empty until the shell-foundation slice closes.

- `2026-07-17` `W36-E5-S1-T3` is complete: vertical surfaces share one
  policy-free primary-action slot that renders only the supplied service action or an
  explicit no-action explanation. `W36-E5-S1-T4` is promoted to `Next` and `T5` to `Soon`.

- `2026-07-17` `W36-E4-S1-T8` is complete: project inspection now resolves runtime
  readiness without reading context-owned launch history before a work item exists; active
  contexts retain canonical launch outcomes. `W36-E5-S1-T3` is promoted to `Next` and
  `W36-E5-S1-T4` to `Soon`.

- `2026-07-17` `W36-E5-S1-T2` is complete: Studio recovery now has one Decision Bar
  Recovery Summary with one decisive failure, one primary action, and one Evidence link;
  duplicate hero/sidebar/screen summaries are removed. A separately reviewable onboarding
  readiness regression is recorded as `W36-E4-S1-T8` and promoted to `Next`.

- `2026-07-17` `W36-E5-S1-T1` is complete: one value-aware visibility policy hides
  an empty Evidence Inspector and keeps Filmstrip/runtime-log evidence undisclosed until
  the operator requests History or Logs. `W36-E5-S1-T2` is promoted to `Next` and
  `W36-E5-S1-T3` to `Soon`.

- `2026-07-17` `W36-E4-S1-T6` is complete: Guided Review & Launch and legacy
  controls resolve through one task-aware workflow/stage dispatcher, keyed duplicate
  suppression, and durable winner readback. Guided Setup parity `W36-E4-S1-T7` remains
  planned until `W36-E7-S1-T1`; `W36-E5-S1-T1` is promoted to `Next` and `T2` to `Soon`.

- `2026-07-17` `W36-E4-S1-T5` is complete: Guided Delivery is a browser-only
  presentation preference with step-specific context; toggling it preserves project,
  work item, run, stage, runtime, request payload, and durable result. `W36-E4-S1-T6`
  is promoted to `Next` and its parity successor `W36-E4-S1-T7` to `Soon`.

- `2026-07-17` `W36-E4-S1-T4` is complete: first-run setup no longer presents mode
  cards whose selections share one service outcome; distinct run and stage launch controls
  remain, while terminal follow-up, clone, eval, and archive stay outside Guided Setup.
  `W36-E4-S1-T5` is promoted to `Next` and `W36-E4-S1-T6` to `Soon`.

- `2026-07-17` `W36-E4-S1-T3` is complete: project-set editing, AIDD root, and config
  details remain reachable inside a collapsed Advanced disclosure while the primary
  Create/Resume decision stays visible. `W36-E4-S1-T4` is promoted to `Next` and
  `W36-E4-S1-T5` to `Soon`.

- `2026-07-17` `W36-E4-S1-T2` is complete: Create and Resume share one work-item
  decision surface before runtime selection; Resume opens saved context without runtime
  or launch, while Create retains the runtime gate before its mutation.
  `W36-E4-S1-T3` is promoted to `Next` and `W36-E4-S1-T4` to `Soon`.

- `2026-07-17` `W36-E4-S1-T1` is complete: Guided Setup now has a pure four-step
  Project -> Work item -> Runtime -> Review/Launch reducer with deterministic create,
  resume, Back, Continue, validation, and launch-readiness transitions.
  `W36-E4-S1-T2` is promoted to `Next` and `W36-E4-S1-T3` to `Soon`.

- `2026-07-17` `W36-E4-S2-T2` is complete: readiness now includes the latest canonical
  attempt outcome per runtime with artifact-index timestamp and evidence path; legacy or
  malformed attempts degrade explicitly without fabricated provenance. `W36-E4-S1-T1`
  is promoted to `Next` and `W36-E4-S1-T2` to `Soon`; readiness rendering `S2-T3`
  remains deferred until Guided Setup and the active Studio shell exist.

- `2026-07-17` `W36-E4-S2-T1` is complete: binary, execution command,
  authentication, and adapter capability evidence now have independent typed statuses;
  legacy provider/command booleans remain additive compatibility fields and no overall
  readiness is inferred. `W36-E4-S2-T2` is promoted to `Next`; no task is placed in
  `Soon` because readiness rendering remains blocked on the Guided Setup/Studio shells.

- `2026-07-17` `W36-E5-S0-T2` and slice `W36-E5-S0` are complete: the additive
  terminal-handoff API preserves source identity and all allowed outcomes while exposing
  the core recommendation; legacy or malformed payloads resolve to explicit
  no-recommendation compatibility states. `W36-E4-S2-T1` is promoted to `Next` and
  `W36-E4-S2-T2` to `Soon`.

- `2026-07-17` `W36-E5-S0-T1` is complete: the core terminal handoff now recommends
  independent work only for fresh clean QA, recommends a lineage-preserving follow-up
  for failed/blocked/risk-bearing QA, and emits no recommendation for missing, stale, or
  nonterminal evidence. `W36-E5-S0-T2` is promoted to `Next`.

- `2026-07-17` `W36-E6-S4-T6`, slice `W36-E6-S4`, and Epic `W36-E6` are complete:
  approval decisions share one request-scoped guard, reconcile CAS and terminal 409s
  through the durable decision/audit read model, and never leave stale pending controls.
  `W36-E5-S0-T1` is promoted to `Next` and `W36-E5-S0-T2` to `Soon`.

- `2026-07-17` `W36-E6-S4-T5` is complete: approval cards capture a decision reason,
  session-wide breadth is shown in an explicit confirmation preview, no
  `allow_for_session` POST occurs before confirmation, and request controls remain
  disabled while the decision is submitted. `W36-E6-S4-T6` is promoted to `Next`.

- `2026-07-17` `W36-E6-S4-T4` is complete: clone/follow-up draft materialization,
  preflight, and launch now use source/target-scoped mutation keys; repeated launch
  input creates and polls one job, failures preserve the browser draft, and source-run
  evidence remains unchanged. `W36-E6-S4-T5` is promoted to `Next` and
  `W36-E6-S4-T6` to `Soon`.

- `2026-07-17` `W36-E6-S4-T3` is complete: answer and intervention submissions now
  share bounded mutation keys, disable duplicate controls, retain drafts after failed
  writes, clear them only after durable success or conflict reconciliation, and attach
  intervention polling once. `W36-E6-S4-T4` is promoted to `Next` and
  `W36-E6-S4-T5` to `Soon`.

- `2026-07-17` `W36-E6-S4-T2` is complete: workflow, stage, task, finalization,
  stale-downstream, and remediation launches now share keyed in-flight work, disable
  their duplicate controls immediately, start polling once, and resolve 409 by rendering
  the durable dashboard winner. `W36-E6-S4-T3` is promoted to `Next` and
  `W36-E6-S4-T4` to `Soon`.

- `2026-07-17` `W36-E6-S4-T1` is complete: the packaged guard shares one in-flight
  Promise per bounded key, permits different keys concurrently, resolves 409 through
  durable winner readback, retains retryable failure state, and bounds terminal state
  retention. `W36-E6-S4-T2` is promoted to `Next` and `W36-E6-S4-T3` to `Soon`.

- `2026-07-17` `W36-E6-S3-T3` and slice `W36-E6-S3` are complete: recovery now
  re-reads server stage/run while retaining cursor/chunks, and terminal or evicted jobs
  release volatile live buffers only after dashboard reconciliation so saved logs and
  artifacts remain authoritative. `W36-E6-S4-T1` is promoted to `Next` and
  `W36-E6-S4-T2` to `Soon`.

- `2026-07-17` `W36-E6-S3-T2` is complete: live observation names reconnecting,
  recovered, offline, and expired-job states, preserves the nonterminal runtime claim,
  and offers bounded Reconnect or durable-state refresh actions. `W36-E6-S3-T3` is
  promoted to `Next` and `W36-E6-S4-T1` to `Soon`.

- `2026-07-17` `W36-E6-S3-T1` is complete: live polling now uses one generation-scoped
  timeout, preserves the accepted cursor, retries at 0.5/1/2/4 seconds, caps at an
  explicit offline state, and cannot append late chunks after cancellation or terminal
  invalidation. `W36-E6-S3-T2` is promoted to `Next` and `W36-E6-S3-T3` to `Soon`.

- `2026-07-17` `W36-E6-S2-T3` and slice `W36-E6-S2` are complete: follow-up and clone
  definitions merge the exact source-run session draft after Back/reload, preserve it
  through preflight and launch failure, and clear it only after authoritative launch-job
  readback. `W36-E6-S3-T1` is promoted to `Next` and `W36-E6-S3-T2` to `Soon`.

- `2026-07-17` `W36-E6-S2-T2` is complete: question and intervention edits persist per
  project/work-item/run/stage/source, restore after rerender and reload, raise a dirty
  leave warning, survive failed submission, and clear only after authoritative durable
  readback. `W36-E6-S2-T3` is promoted to `Next` and `W36-E6-S3-T1` to `Soon`.

- `2026-07-17` `W36-E6-S2-T4` is complete: the shared packaged session store validates
  all six key dimensions, purges malformed/expired records, enforces the 32-entry and
  byte budgets, rejects secret-shaped values, and clears only an exact owner key.
  `W36-E6-S2-T2` is promoted to `Next` and `W36-E6-S2-T3` to `Soon`.

- `2026-07-17` `W36-E6-S2-T1` is complete: the architecture fixes the six-dimensional
  session key, schema-v1 value, 24-hour expiry, bounded eviction, dirty warning, and exact
  owner-only cleanup after durable readback; browser drafts never enter `.aidd/`.
  `W36-E6-S2-T4` is promoted to `Next` and `W36-E6-S2-T2` to `Soon`.

- `2026-07-17` `W36-E6-S1-T3` and slice `W36-E6-S1` are complete: Inbox, historical
  run, parent, child, and artifact inspection actions resolve through one fail-closed
  intent registry, and archived runs retain both read-only inspection paths.
  `W36-E6-S2-T1` is promoted to `Next` and `W36-E6-S2-T4` to `Soon`.

- `2026-07-17` `W36-E6-S1-T2` is complete: explicit transitions push canonical route
  entries, derived renders replace them, and `popstate` plus reload restore the selected
  Studio view, stage, run, and artifact through one read-only path. The real Chromium
  Back/Forward/reload sequence is green. `W36-E6-S1-T3` is promoted to `Next` and
  `W36-E6-S2-T1` to `Soon`.

- `2026-07-17` `W36-E6-S1-T1` is complete: a pure packaged codec round-trips Inbox,
  Studio, and History context in stable query order, dual-reads the bounded legacy
  aliases, and drops invalid, stale, path-like, or ambiguous detail with stable warnings.
  `W36-E6-S1-T2` is promoted to `Next` and `W36-E6-S1-T3` to `Soon`.

- `2026-07-17` `W36-E3-S4-T3`, slice `W36-E3-S4`, and Epic `W36-E3` are complete:
  microcopy has a `12px` readable floor and stronger secondary contrast, while timers,
  attempts, counts, and status metrics use tabular numerals for stable scanning. The
  rendered contrast gate is green. `W36-E6-S1-T1` is promoted to `Next` and
  `W36-E6-S1-T2` to `Soon`.

- `2026-07-17` `W36-E3-S4-T2` is complete: all eight stage controls derive their
  accessible name from the visible stage label plus explicit status, and dynamic
  onboarding, remediation, intervention, comparison, source-selection, and follow-up
  fields now have stable ids, names, and associated labels. `W36-E3-S4-T3` is promoted
  to `Next`; `Soon` remains empty until the accessibility slice closes.

- `2026-07-17` `W36-E3-S4-T1` is complete: a first-focus skip link resolves the
  currently rendered primary decision before maintenance controls, detail navigation
  enters the cockpit deterministically, and Escape returns to the connected trigger or
  selected mode fallback. `W36-E3-S4-T2` is promoted to `Next` and `W36-E3-S4-T3` to
  `Soon`.

- `2026-07-17` `W36-E3-S3-T6` and slice `W36-E3-S3` are complete: question,
  approval, runtime, validation, intervention, and quality-gate Recovery Summaries keep
  exactly one decisive failure, one evidence path, and one primary recovery slot, with a
  single-column touch-safe mobile layout. `W36-E3-S4-T1` is promoted to `Next` and
  `W36-E3-S4-T2` to `Soon`.

- `2026-07-17` `W36-E3-S3-T5` is complete: current, complete, invalid, optional, and
  disabled Guided Steps retain the same explanation, labelled input group, one primary
  action, Back action, and Advanced disclosure, with mobile control geometry verified.
  `W36-E3-S3-T6` is promoted to `Next`; `Soon` remains empty until the surface slice
  closes.

- `2026-07-17` `W36-E3-S3-T4` is complete: the shared Inbox Item renders blocking,
  running, ready, terminal, and malformed states while preserving the exact
  service-owned route, action, and eligibility; visible status text and mobile action
  geometry do not rely on color alone. `W36-E3-S3-T5` is promoted to `Next` and
  `W36-E3-S3-T6` to `Soon`.

- `2026-07-17` `W36-E3-S3-T3` is complete: Document Canvas is the single framed
  primary surface, Evidence Inspector is conditional and visually supporting, and
  History separates its primary filmstrip from supporting events. Desktop/mobile
  geometry proves the hierarchy without overflow or empty peer frames. `W36-E3-S3-T4`
  is promoted to `Next` and `W36-E3-S3-T5` to `Soon`.

- `2026-07-17` `W36-E3-S3-T2` is complete: empty, loading, error, reconnecting, and
  unavailable states now share a title/consequence/recovery anatomy with truthful
  `role`, live-region, and busy semantics; Guided Setup readiness uses the primitive.
  `W36-E3-S3-T3` is promoted to `Next` and `W36-E3-S3-T4` to `Soon`.

- `2026-07-17` `W36-E3-S3-T1` is complete: a packaged Decision Bar now owns one
  primary slot and a visible, non-color Status Marker for action, pending, blocked,
  complete, stale, and no-action states without deriving journey policy. Existing
  Review/QA summaries render through the primitive. `W36-E3-S3-T2` is promoted to
  `Next` and `W36-E3-S3-T3` to `Soon`.

- `2026-07-17` `W36-E3-S2-T3` and slice `W36-E3-S2` are complete: filters, document
  modes, radio-like setup/runtime cards, evidence selections, and current work-item rows
  now expose the same selected state visually and through `aria-pressed`, `aria-checked`,
  or `aria-current`; mobile rows retain the shared touch density. `W36-E3-S3-T1` is
  promoted to `Next` and `W36-E3-S3-T2` to `Soon`.

- `2026-07-17` `W36-E3-S2-T2` is complete: shared native-control states now cover
  pointer hover/active, keyboard focus, disabled, invalid, pending/loading, and selected
  semantics while retaining the mobile touch target. `W36-E3-S2-T3` is promoted to
  `Next`; `Soon` is empty until the control slice closes.

- `2026-07-17` `W36-E3-S2-T1` is complete: button, text input, select, textarea, and
  checkbox anatomy now share typography, border, radius, focus, sizing, and accent roles;
  journey-form computed styles prove the common contract. `W36-E3-S2-T2` is promoted
  to `Next` and `W36-E3-S2-T3` to `Soon`.

- `2026-07-17` `W36-E3-S1-T3` and slice `W36-E3-S1` are complete: desktop and mobile
  controls now resolve a shared density token to `32px` and `44px` respectively, with
  rendered Chromium coverage proving the token-driven switch. `W36-E3-S2-T1` is
  promoted to `Next` and its direct successor `W36-E3-S2-T2` to `Soon`.

- `2026-07-17` `W36-E3-S1-T2` is complete: repeated status and surface colors now
  resolve through semantic roles, raw duplicate palettes outside the token layer are
  rejected, and rendered success/warning/danger/info fixtures meet accepted text contrast.
  `W36-E3-S1-T3` is promoted to `Next`; `Soon` remains empty until density modes close
  the token slice.

- `2026-07-17` `W36-E3-S1-T1` is complete: `operator-tokens.css` now owns semantic
  typography, spacing, radius, elevation, control-size, state, focus, and motion roles,
  while an inventory test prevents the existing raw-value surface outside the token layer
  from growing. `W36-E3-S1-T2` is promoted to `Next` and `W36-E3-S1-T3` to `Soon`.

- `2026-07-17` `W36-E2-S3-T4`, slice `W36-E2-S3`, and Epic `W36-E2` are complete:
  one pure resolver now applies the selector/rollout truth table per surface, exposes
  mixed Studio/legacy resolution without changing shared service requests, and fails
  unknown surfaces explicitly. `W36-E3-S1-T1` is promoted to `Next` and
  `W36-E3-S1-T2` to `Soon`.

- `2026-07-17` `W36-E2-S3-T3` is complete: a validated packaged manifest now assigns
  each of the twelve journey-owned surfaces exactly one slice owner, rollout state,
  rollback renderer, required fixture, browser journey, and removal gate; all entries
  begin as `legacy_only`. `W36-E2-S3-T4` is promoted to `Next`; `Soon` remains empty
  until the migration resolver is accepted.

- `2026-07-17` `W36-E2-S3-T2` is complete: the packaged browser now accepts only
  `ui=studio|legacy`, treats missing or invalid values as legacy, and records an explicit
  legacy fallback for Studio while every surface is still legacy-only; service routes and
  request payloads are unchanged. `W36-E2-S3-T3` is promoted to `Next` and
  `W36-E2-S3-T4` to `Soon`.

- `2026-07-17` `W36-E2-S3-T1` is complete: one packaged dashboard/action seam now owns
  non-next-flow loading, server-derived context reconciliation, and workflow/stage/task/
  remediation dispatch, while legacy rendering and next-flow behavior retain equivalent
  requests and durable readback. `W36-E2-S3-T2` is promoted to `Next` and
  `W36-E2-S3-T3` to `Soon`.

- `2026-07-17` `W36-E2-S2-T3` and slice `W36-E2-S2` are complete: schema-v1 browser
  evidence now atomically records bounded viewport metadata, screenshots, DOM measures,
  console/network summaries, accessibility/geometry results, and cleanup status outside
  the repository worktree. `W36-E2-S3-T1` is promoted to `Next` and `W36-E2-S3-T2` to
  `Soon`.

- `2026-07-17` `W36-E2-S2-T2` is complete: browser geometry assertions now diagnose
  sticky-header budget, first-viewport primary action, clipping, overlap, nested scroll,
  and horizontal overflow at the owning viewport and selector. `W36-E2-S2-T3` is promoted
  to `Next` and `W36-E2-S3-T1` to `Soon`.

- `2026-07-17` `W36-E2-S2-T1` is complete: the browser assertion layer now reports
  accessible-name, label, focus-order, contrast, target-size, and reduced-motion failures
  with the owning selector and measured value. `W36-E2-S2-T2` is promoted to `Next` and
  `W36-E2-S2-T3` to `Soon`.

- `2026-07-17` `W36-E2-S1-T3` and slice `W36-E2-S1` are complete: nine immutable,
  provider-free descriptors now seed canonical setup, active, recovery, quality,
  remediation, and terminal evidence through production persistence helpers and verify the
  public loopback UI without external reads. `W36-E2-S2-T1` is promoted to `Next` and
  `W36-E2-S2-T2` to `Soon`.

- `2026-07-17` `W36-E2-S1-T2` is complete: the reusable browser harness starts the public
  loopback CLI under one deadline, isolates all five contract viewports, captures browser
  and network failures, and bounds server/process cleanup plus temporary workspace removal.
  `W36-E2-S1-T3` is promoted to `Next` and `W36-E2-S2-T1` to `Soon`.

- `2026-07-17` `W36-E2-S1-T4` is complete: Python Playwright is locked only in the dev
  extra, the wheel remains runtime-clean, and a real loopback `aidd ui` Chromium smoke
  fails with the maintained install command when the browser is missing.
  `W36-E2-S1-T2` is promoted to `Next` and `W36-E2-S1-T3` to `Soon`.

- `2026-07-17` `W36-E2-S1-T1` is complete: the provider-free browser policy selects the
  Python Playwright sync API with one external-cache Chromium target, an isolated
  `browser_tests/` lane, and no Node/Vite product runtime. `W36-E2-S1-T4` is promoted to
  `Next` and `W36-E2-S1-T2` to `Soon`.

- `2026-07-17` `W36-E1-S2-T3`, slice `W36-E1-S2`, and Epic `W36-E1` are complete:
  local-project evidence now records viewport geometry, accessibility, scroll ownership,
  completion, timing, wrong actions, assistance, confidence, and decisive confusion.
  `W36-E2-S1-T1` is promoted to `Next` and `W36-E2-S1-T4` to `Soon`.

- `2026-07-17` `W36-E1-S2-T2` is complete: runtime detection, command availability,
  authentication evidence, capability, permission/write scope, approval breadth,
  connectivity, and mutations now have separate observable vocabularies.
  `W36-E1-S2-T3` is promoted to `Next` and `W36-E2-S1-T1` to `Soon`.

- `2026-07-17` `W36-E1-S2-T1` is complete: every setup, execution, next-flow, and archive
  action now names its real endpoint/service, durable result, and conflict boundary; eval is
  explicitly an external/manual handoff. `W36-E1-S2-T2` is promoted to `Next` and
  `W36-E1-S2-T3` to `Soon`.

- `2026-07-17` `W36-E1-S1-T3` and slice `W36-E1-S1` are complete: the local-project
  evidence contract now maps Guided Setup, Inbox, Studio recovery/quality states, Flow
  Complete, and History to logical route intents and fail-closed context recovery.
  `W36-E1-S2-T1` is promoted to `Next` and `W36-E1-S2-T2` to `Soon`.

- `2026-07-17` `W34-E8-S2-T2`, slice `W34-E8-S2`, Epic `W34-E8`, and Wave 34 are
  complete: architecture now distinguishes live stdout/stderr forwarding from durable
  `runtime.log` persistence and documents full/tail replay plus separate structured audit
  evidence. `W36-E1-S1-T3` is promoted to `Next` and `W36-E1-S2-T1` to `Soon`.

- `2026-07-17` `W34-E8-S2-T1` is complete: target architecture now states stable
  implemented frontend, project-set, provenance, approval-audit, and immutable-run
  ownership without using a completed wave or an undecided browser driver as policy.
  `W34-E8-S2-T2` is promoted to `Next`; `Soon` is empty.

- `2026-07-17` `W34-E8-S1-T3` and slice `W34-E8-S1` are complete: one generic
  roadmap/backlog parser now enforces hierarchy, unique local tasks, queue/status parity,
  terminal exclusion, and direct or explicit `Soon` succession. `W34-E8-S2-T1` is
  promoted to `Next` and `W34-E8-S2-T2` to `Soon`.

- `2026-07-17` `W34-E8-S1-T2` is complete: planning entities now use a canonical
  level-specific status vocabulary, backlog placement projects exact local-task status,
  and historical outcomes are ordinary disposition notes. `W34-E8-S1-T3` is promoted
  to `Next` and `W34-E8-S2-T1` to `Soon`.

- `2026-07-17` `W34-E7-S2-T3`, slice `W34-E7-S2`, and Epic `W34-E7` are complete:
  scenario, runtime, eval-run, and result-bundle identifiers now share the canonical
  containment boundary without changing valid bundle layouts. `W34-E8-S1-T2` is
  promoted to `Next` and `W34-E8-S1-T3` to `Soon`.

- `2026-07-17` `W34-E7-S3-T1` and slice `W34-E7-S3` are complete: configuration now
  distinguishes absent defaults from explicit blanks and rejects unknown or malformed
  keys before runtime execution. `W34-E7-S2-T3` is promoted to `Next` and
  `W34-E8-S1-T2` to `Soon`.

- `2026-07-16` `W34-E3-S4-T4`, slice `W34-E3-S4`, and Epic `W34-E3` are complete:
  next-flow mutations remain in the compatible controller asset while terminal,
  lineage/history, wizard, readiness/error, and next-action presentation now live in
  a separately packaged view asset loaded before the remaining UI wiring.
  `W34-E7-S3-T1` is promoted from Parking lot to `Next`; `Soon` remains empty.

- `2026-07-16` `W34-E3-S4-T3` is complete: dashboard filesystem/read-model collection
  now produces one immutable evidence snapshot with request-local source caching, while
  a pure reducer projects that evidence into the unchanged serialized dashboard view.
  `S4-T4` is promoted to `Next`; `Soon` is empty.

- `2026-07-16` `W34-E3-S4-T2` is complete: exact and dynamic route dispatch, static
  assets, query/body handling, HTTP exception mapping, and the server handler now live
  behind a thin router while `OperatorUiService` retains business state and compatible
  `handle_get`/`handle_post` facades. `S4-T3` is promoted to `Next`; `S4-T4` is in
  `Soon`.

- `2026-07-16` `W34-E3-S4-T1` is complete: normalized characterization fixtures now
  pin route responses, mutation conflicts, approval CAS, cancellation, retention, and
  running/blocked/failed/stale/terminal dashboard states. `S4-T2` is promoted to
  `Next`; `S4-T3` is in `Soon`.

- `2026-07-16` `W34-E6-S2-T3`, slice `W34-E6-S2`, and Epic `W34-E6` are complete:
  maintained checkout, Python setup, uv setup, artifact download, and Scorecard actions
  are pinned to their compatible current releases with workflow contracts intact.
  `W34-E3-S4-T1` is promoted to `Next`; its direct successor `S4-T2` is in `Soon`.

- `2026-07-16` `W34-E6-S2-T2` is complete: the retained lock now resolves Typer
  0.27.0, pytest 9.1.1, Ruff 0.15.22, and mypy 2.3.0 without changing declared lower
  bounds; CLI compatibility, locked sync, lint, strict typing, packaging smoke, and
  1810 tests pass. `S2-T3` is promoted to `Next`.

- `2026-07-16` `W34-E6-S2-T1` is complete: obsolete Dependabot proposals for removed
  direct dependencies `pydantic`, `markdown-it-py`, and `python-frontmatter` are closed
  with cleanup provenance. `S2-T2` is promoted to `Next`; `S2-T3` is in `Soon`.

- `2026-07-16` `W34-E6-S1-T5` and slice `W34-E6-S1` are complete: the dormant docs
  extra, MkDocs lock subtree, and Dependabot pattern are removed, while wheel resources
  remain independently verified. `W34-E6-S2-T1` is promoted to `Next`, `S2-T2` to
  `Soon`, and `S2-T3` remains parked.

- `2026-07-16` `W34-E6-S1-T4` is complete: the stale generated `manifest.txt` inventory
  is removed, tracked cache/bytecode paths are rejected, and historical `MANIFEST.md`
  remains available. `T5` is promoted to `Next`.

- `2026-07-16` `W34-E6-S1-T3` is complete: `python-frontmatter`, `markdown-it-py`, and
  `pydantic` are no longer direct runtime requirements; wheel metadata retains PyYAML
  and excludes the removed direct dependencies. `T4` is promoted to `Next`; `T5` is in
  `Soon`.

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
