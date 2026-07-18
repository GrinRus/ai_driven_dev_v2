# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W36-E7-S1-T12` — Add the project-local Inbox priority and routing browser journey.

## Soon

No task is currently queued here. The first parity closure after the Inbox journey
belongs to a separate already-complete dependency chain rather than being its direct
successor.

## Parking lot

- `W36-E5-S5-T1` — Render blocking questions with durable resolution and draft-recovery
  semantics in Recovery Studio.
- `W36-E5-S6-T1` — Render typed runtime failure and the eligible recovery action without
  conflating validation repair.
- `W36-E5-S7-T1` — Render canonical implement tasks, attempts, recovery, and aggregate
  finalization inside Studio.
- `W36-E5-S8-T1` — Implement the typed Filmstrip frame projection from durable attempts,
  task attempts, and finalization milestones.
- `W36-E5-S10-T1` — Switch the default renderer to Studio only after all per-surface
  parity entries close.

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
