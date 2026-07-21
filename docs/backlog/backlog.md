# Active Backlog

This file is the short actionable queue.

Use `docs/backlog/roadmap.md` for the full hierarchy and status of every wave, epic,
slice, and local task.

## Next

- `W36-E7-S4-T3` — Run the medium scenario through Codex from a fresh isolated root.

## Soon

- `W36-E7-S4-T4` — Repeat the medium scenario through Claude Code from an independent root.

## Parking lot

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
