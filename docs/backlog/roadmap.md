# Roadmap

This file is the canonical implementation plan for AIDD.

## Status vocabulary

Waves, epics, and slices use exactly `planned` or `done`. Local tasks use exactly:

- `planned` — accepted but not in the actionable queue;
- `next` — the preferred immediate target in backlog `Next`;
- `soon` — a direct successor in backlog `Soon`;
- `parked` — consciously deferred in backlog `Parking lot`;
- `blocked` — accepted but stopped by an explicit dependency gap;
- `done` — completed in the repository and absent from backlog.

Every planning entity has an explicit marker. Backlog placement is an exact projection
of local-task status: `Next` maps to `next`, `Soon` to `soon`, and `Parking lot` to
`parked`. Historical outcomes such as `superseded`, `legacy`, or `not applicable` are
ordinary disposition notes, not status values.

## Planning model

- **Wave** — broad delivery phase
- **Epic** — coherent theme inside the wave
- **Slice** — smallest meaningful outcome
- **Local task** — one reviewable implementation step

ID format:

`W<wave>-E<epic>-S<slice>-T<task>`

Example: `W3-E2-S1-T2`

## Local-task quality bar

Every local task should be reviewable without extra decomposition. A good local task has:

- one clear output;
- one dominant touched area;
- one main verification signal;
- explicit upstream dependencies;
- wording that starts with a concrete verb.

When a task touches multiple subsystem families, mixes design and rollout, or has more than one independent verification path, split it before coding.

## Completed work and queue restoration

This roadmap contains open work, the current cleanup, and the newly integrated Focus Canvas rollout. Completed task definitions,
dated execution notes, and superseded plans are available in Git history. References to completed
prerequisites describe functionality already present in the current implementation.

When the queue is empty, select an unresolved user-story outcome, define a bounded local task
under its owning wave/epic/slice here, then add that task to the backlog. Do not resurrect completed
history as an active queue.

## Wave 36 — Document & Evidence Studio migration (`planned`)

Goal: migrate the capability-rich packaged Operator UI to the accepted Document & Evidence
Studio experience through bounded vertical slices across Guided Setup, Inbox, Studio,
Recovery, History, and Flow Complete without changing the canonical stage graph, mutation
semantics, artifact ownership, or `aidd ui` entrypoint.

### Epic W36-E7 — executable UX acceptance and rollout evidence (`planned`)

#### Slice W36-E7-S3 — observed first-time-operator acceptance (`planned`)

Goal: verify that the simplified UI is understandable to operators who did not implement
it.

- `W36-E7-S3-T2` (parked) Record five first-time-operator sessions against the source-installed
  packaged UI.
  - Dependencies: `W36-E7-S3-T1`, `W36-E7-S4-T4` as the direct queue predecessor.
  - Scope: manual operator acceptance evidence.
  - Verification: one anonymized report contains all required task metrics, browser and
    viewport context, blockers, and no sensitive project/runtime evidence.

- `W36-E7-S3-T3` (parked) Reconcile accepted session findings into roadmap tasks and beta-readiness
  evidence.
  - Dependencies: `W36-E7-S3-T2` as the direct queue predecessor.
  - Scope: planning and product-readiness docs.
  - Verification: every reportable finding is closed, deferred with rationale, or mapped
    to a reviewable roadmap task before beta UX is claimed.

#### Slice W36-E7-S4 — isolated prod-like provider acceptance (`planned`)

Goal: prove the installed Studio and governed full flow against one pinned medium public-repository
task through both maintained native providers without coupling live-evaluation behavior to product
runtime semantics.

- `W36-E7-S4-T4` (parked) Run `AIDD-LIVE-007` through Claude Code from an independent root on
  the same AIDD revision and target pin.
  - Dependencies: `W36-E7-S4-T3` as the direct queue predecessor.
  - Scope: external Claude Code live execution and evidence only.
  - Verification: the Claude bundle meets the Codex evidence bar without reusing target state,
    answers, attempts, patches, or provider evidence.

- `W36-E7-S4-T5` (parked) Record a final same-revision Codex and Claude acceptance pass after
  observed-session reconciliation.
  - Dependencies: `W36-E7-S4-T4`, `W36-E7-S3-T3` as direct queue predecessors.
  - Scope: sanitized live acceptance evidence and Wave 36 closure only.
  - Verification: both fresh bundles name the same clean AIDD SHA, scenario and target revision,
    pass terminal quality gates, and match an anonymized digest-backed tracked summary.

## Wave 42 — task-centered operator experience (`planned`)

Goal: replace the implemented document-first shell's ambiguous `Intent` vocabulary and weak task
affordances with one organic operator flow: create a Work Item, select an eligible Runner at the
point of execution, work dependency-ready Tasks, read or author Markdown through explicit
ownership boundaries, recover from exact failures, and finish with an immutable handoff.

### Epic W42-E7 — executable UX acceptance (`planned`)

Goal: prevent another visual-only redesign by requiring deterministic surface fixtures, browser
behavior, accessibility, responsive geometry, and observed first-time use before cutover.

#### Slice W42-E7-S2 — responsive browser journeys and observed usability (`planned`)

Primary output: measured browser evidence and one observed novice journey that gates default
routing.

- `W42-E7-S2-T3` (parked) Record one genuine uncoached first-time operator observation.
  - Scope: observe one participant completing create -> choose Codex Runner -> launch -> answer
    question -> resume without coaching and retain only anonymized usability evidence. This
    human-usability gate is intentionally deferred from the Codex-only alpha execution lane and
    must not be represented as passed or substituted with a scripted rehearsal.
  - Verification: `wave42-first-time-operator-journey-v1` uses
    `uncoached-human-observation`, records completion, timings, wrong turns, assistance, confidence,
    first confusion, resulting roadmap tasks, and routing decision; missing participant/runtime is
    `environment-blocked`, never pass. The task remains deferred while Codex-only Wave 43 work
    proceeds.

## Wave 43 — validation and repair resilience (`planned`)

Goal: make the document-first workflow reliable across maintained and lower-capability runtimes
by separating runtime-authored content from AIDD-owned workflow records, preserving canonical
interview state, producing root-cause validation evidence, and providing one audited recovery
path after automatic repair exhaustion without weakening fail-closed progression.

### Epic W43-E5 — resilience regression and Codex-only evidence (`planned`)

Goal: prove the ownership, interview, tasklist, and repair-extension behavior deterministically,
then measure repeatability through a Codex-only live lane without claiming cross-provider readiness.

#### Slice W43-E5-S2 — Codex stability lane (`planned`)

Primary output: a repeatable Codex profile that measures whether Wave 43 reduces false repair
exhaustion without weakening validation; cross-runtime comparison remains deferred.

- `W43-E5-S2-T3` (parked) Run a future cross-runtime lower-capability comparison.
  - Scope: preserve the original lower-capability comparison objective for a later provider lane
    without changing Codex-only alpha acceptance or core/provider boundaries.
  - Verification: a future report compares the same profile across maintained and lower-capability
    runtimes and retains explicit environment-blocked verdicts when prerequisites are absent.

## Wave 46 — operator multi-context navigation and request clarity (`planned`)

Goal: let an active UI runtime job continue in its own captured project context while the operator
navigates elsewhere, and expose Work Item request information as separate title, brief, context,
constraint, and additional-information fields without changing the canonical workflow or task
execution semantics.

### Epic W46-E1 — multi-context UI jobs (`planned`)

#### Slice W46-E1-S2 — context-aware navigation and job visibility (`planned`)

Goal: remove the over-broad project-switch guard while keeping safe job inspection and mutation.

- `W46-E1-S2-T4` (parked) Add a provider-free two-project browser scenario for navigation and isolation.
  - Output: deterministic UI scenario and retained evidence for switching, logs, and artifacts.
  - Scope: `browser_tests/test_journey_inbox.py`, `tests/test_packaged_ui_scenarios.py`, scenario
    assets, and E2E docs.
  - Verification: packaged browser gate passes without console errors or cross-project artifacts.

### Epic W46-E2 — structured Work Item context (`planned`)

#### Slice W46-E2-S2 — clean Work Item and Task headers (`planned`)

Goal: keep headers concise and make detailed information available in explicit lower-level surfaces.

- `W46-E2-S2-T4` (parked) Add responsive and browser acceptance for long request/task content.
  - Output: provider-free geometry/accessibility coverage for desktop and mobile states.
  - Scope: `browser_tests/`, `tests/test_packaged_ui_scenarios.py`, static UI tests, and E2E docs.
  - Verification: no overflow, keyboard-inaccessible details, or lost request fields.

## Wave 47 — Focus Canvas production rollout (`done`)

Goal: bring the selected Focus Canvas visual and interaction direction into the production
Operator UI while preserving the canonical workflow, document-first artifacts, core-owned
readiness, runtime boundaries, and retained evidence.

Linked stories: `US-02`, `US-03`, `US-05`, `US-06`, `US-11`, `US-13`

Dependencies: the implemented Wave 42 task-centered target, the Wave 46 project/workspace job
context, and the existing `/api/answers` durable write/read models.

### Epic W47-E1 — decision-first operator surface (`done`)

Goal: make one operator decision easy to understand, save, verify, and resume without conflating
human input with runtime execution, then reuse the same truthful surface for recovery states.

#### Slice W47-E1-S1 — durable decision lifecycle (`done`)

Goal: separate answer persistence, durable readback, readiness, stage resume, live output, and
validation into explicit operator-visible states.

Dependencies: `W42-E5-S1`, `W42-E5-S2`, and the current question/answer service semantics.

Primary output: a production Decision Workbench in which saving an answer never falsely claims that
the stage already resumed or advanced.

Local tasks:

- `W47-E1-S1-T1` (done) Define the Focus Canvas decision state transition contract.
  - Output: update `docs/architecture/operator-frontend-target-ux.md` with explicit save/readback,
    resolution, resume, readiness, runtime, validation, and recovery semantics derived from the
    selected prototype audit.
  - Scope: architecture and acceptance wording only; do not change runtime or UI code.
  - Verification: docs/planning consistency checks and architecture review confirm that each state
    has one truthful primary action and that Partial/Deferred remain blocked.
  - Completion evidence: the Decision lifecycle contract was added to the target UX document;
    docs/planning checks passed (`52 passed` on 2026-09-05).

- `W47-E1-S1-T2` (done) Separate durable answer save from stage resume in the question workbench.
  - Output: `operator-questions.js` and event dispatch persist `/api/answers`, wait for matching
    durable readback, and expose Resume as a separate mutation instead of calling `startStage` from
    the save path.
  - Scope: `src/aidd/cli/static/operator-questions.js`, `operator-main.js`, and focused frontend
    tests; preserve existing API payloads and core semantics.
  - Verification: Node synchronization tests prove one answer POST, durable winner reconciliation,
    no duplicate resume, and no stage launch during save.
  - Completion evidence: answer save now has its own visible mutation and local-draft action;
    Resume performs a fresh durable question readback and readiness-checked stage launch. Focused
    frontend tests passed (`45 passed`) and UI asset contracts passed (`53 passed`) on 2026-09-05.

- `W47-E1-S1-T3` (done) Render resolution-aware durable and resume-ready states.
  - Output: Resolved, Partial, Deferred, pending, conflict, failed, and readback-confirmed states
    show the correct consequence, destination, runner readiness, and one primary action.
  - Scope: question renderer, shared decision state, and frontend fixtures only unless a missing
    core projection is proven; never infer eligibility in the browser.
  - Verification: frontend UI-state tests cover all resolution branches and assert that only a
    fully resolved blocker set exposes Resume.
  - Completion evidence: question cards now expose one primary save/resume action, server-resolved
    answers expose a separate `Resume <stage>` action, and the impact panel is resolution-aware.
    Frontend tests passed (`47 passed`), asset contracts passed (`53 passed`), and docs/planning
    checks passed (`105 passed`) on 2026-09-05.

- `W47-E1-S1-T4` (done) Add the provider-free question recovery journey for the new lifecycle.
  - Output: browser scenario and retained evidence for save, durable readback, Partial/Deferred
    blocking, Resume, live output, validation pass, validation failure, and runtime failure.
  - Scope: `browser_tests/test_journey_question_recovery.py`, packaged UI scenario assets, and
    E2E documentation.
  - Verification: browser journey passes without console errors and preserves Work Item, stage,
    QID, draft, attempt, and log context across transitions.
  - Completion evidence: the durable save/readback/resume journey passed on mobile and desktop;
    rejected-candidate, validation, and runtime recovery variants also passed with clean browser
    diagnostics. The live acceptance record is `docs/e2e/focus-canvas-live-acceptance-2026-09-05.md`.

#### Slice W47-E1-S2 — Focus Canvas composition and responsive action (`done`)

Goal: apply the selected visual hierarchy to the production decision surface without changing
workflow ownership or inventing state.

Dependencies: `W47-E1-S1`.

Local tasks:

- `W47-E1-S2-T1` (done) Render the desktop Focus Canvas decision composition.
  - Output: focused question surface with canonical Project, Work Item, Stage, QID, consequence,
    evidence, destination, and contextual Runner placement.
  - Scope: `operator-questions.js`, `operator-tokens.css`, `operator-components.css`, and related
    layout styles.
  - Verification: rendered browser captures at `1280x900` and `1440x900` meet first-action and
    hierarchy acceptance without changing route or API contracts.
  - Completion evidence: production `operator-questions.js` and `operator-intent-shell.css` now
    render the Focus Canvas hierarchy; the five-viewport hierarchy gate passed, including both
    desktop target widths.

- `W47-E1-S2-T2` (done) Add the evidence and provenance inspector for a decision.
  - Output: bounded evidence disclosure with source path, attempt, freshness, retained destination,
    provenance, and a safe link to the canonical Markdown document.
  - Scope: decision renderer and document/evidence navigation only.
  - Verification: DOM and browser checks preserve the answer draft while opening and closing
    evidence and never present generated Markdown as editable.
  - Completion evidence: the production decision surface exposes `data-evidence-drawer`, source
    document/retained-attempt facts, durable destination, and a provenance strip; UI-state and
    browser hierarchy tests passed.

- `W47-E1-S2-T3` (done) Make the decision action reachable and accessible on mobile.
  - Output: sticky primary action, local field error/focus behavior, visible focus, wrapping paths,
    and no horizontal overflow for the target mobile sizes.
  - Scope: `operator-responsive.css` and focused interaction tests.
  - Verification: `320x568`, `390x844`, and `768x1024` pass first-action, keyboard-order, target-size,
    contrast, and overflow checks.
  - Completion evidence: mobile Focus Canvas puts Decision Impact first and keeps one touch-sized
    fixed primary action; the five-viewport hierarchy gate and mobile durable-resume journey passed.

#### Slice W47-E1-S3 — shared recovery variants (`done`)

Goal: reuse the truthful Workbench composition for approvals and recovery without sharing misleading
labels or consequences.

Dependencies: `W47-E1-S1` and `W47-E1-S2`.

Local tasks:

- `W47-E1-S3-T1` (done) Align the runtime approval Workbench with the Focus Canvas action model.
  - Output: approval-specific consequence, permission scope, pending, approved, denied, cancelled,
    and policy-blocked states.
  - Scope: approval/intervention renderer and frontend fixtures.
  - Verification: approval browser journey exposes exactly one eligible primary action per state.
  - Completion evidence: approval Workbench browser hierarchy passed across all five supported
    viewports with one eligible primary action and clean accessibility/overflow diagnostics.

- `W47-E1-S3-T2` (done) Align validation repair with the Focus Canvas evidence hierarchy.
  - Output: finding, rule, retained location, repair budget, repair action, and Request Change path
    are visible without implying that a repair already succeeded.
  - Scope: validation recovery renderer and responsive styles.
  - Verification: validation recovery journey distinguishes repair, change, and blocked states.
  - Completion evidence: validation/review recovery gates passed at desktop and mobile; repair,
    Request Change, finding evidence, and repair exhaustion remain distinct.

- `W47-E1-S3-T3` (done) Align runtime failure and repair exhaustion recovery.
  - Output: raw runtime evidence, retry eligibility, repair budget, and safe next action remain
    distinct from validation failure.
  - Scope: runtime/recovery renderers and frontend tests.
  - Verification: runtime recovery journey proves retry does not consume validation repair budget.
  - Completion evidence: runtime retry/recovery passed on mobile and desktop and the runtime
    validation recovery matrix passed without mutation or console errors.

#### Slice W47-E1-S4 — live production acceptance (`done`)

Goal: prove the target UI on a genuinely running project, not only in provider-free fixtures.

Dependencies: `W47-E1-S1`, `W47-E1-S2`, `W47-E1-S3`, and an eligible local runtime/project.

Local tasks:

- `W47-E1-S4-T1` (done) Run and retain the live Focus Canvas operator journey.
  - Output: auditable live-project evidence covering Inbox, Work Item, Decision Workbench, durable
    answer save, separate Resume, live logs, validation, and at least one recovery branch.
  - Scope: live E2E manifest, retained screenshots/logs, and acceptance report; no provider-specific
    shortcut in core behavior.
  - Verification: the live project reaches the expected state transitions with no console errors,
    false advancement, lost context, or missing durable evidence.
  - Completion evidence: live loopback project acceptance is recorded in
    `docs/e2e/focus-canvas-live-acceptance-2026-09-05.md`, with fresh desktop/mobile captures and
    Inbox → Work Item → Decision Workbench → durable readback → separate Resume → live logs →
    recovery evidence.

- `W47-E1-S4-T2` (done) Reconcile documentation, roadmap, backlog, and acceptance evidence.
  - Output: final target UX wording, task statuses, screenshots, and live acceptance report agree
    with the shipped behavior and remaining gaps.
  - Scope: docs/planning/evidence only after implementation is complete.
  - Verification: planning/docs checks pass and the requirement-by-requirement completion audit is
    fully evidenced.
  - Completion evidence: target UX, roadmap/backlog, browser tests, and the live acceptance record
    agree; docs/planning checks passed (`105 passed`) on 2026-09-05.

## Wave 51 — agent development instruction consistency (`done`)

The maintainer instruction hierarchy, executable workflow checks, runtime document ownership,
and bootstrap regressions were integrated by PR #515 and its follow-up fixes. Their completed
local-task definitions and execution records remain in Git history. Current guidance is in
`docs/agent-development.md`; the checks remain in CI. The cleanup below replaces the historical
archive and frozen prompt hashes with bounded planning and semantic prompt checks.

## Wave 52 — repository cleanup and current-format boundary (`planned`)

Goal: remove unused code, obsolete compatibility, misleading instructions, and historical
repository clutter while preserving current workflow, validation, repair, and evidence behavior.

Integration note: authored as Wave 47 on `f2819535`, this cleanup is rekeyed to Wave 52
when integrating `191dfb16`. The upstream Focus Canvas Wave 47 and instruction Wave 51
keep their identities. Waves 48–50 remain reserved by the accepted remediation plan in
`docs/analysis/project-quality-remediation-plan-2026-09-05.md`; its unpromoted work is not
claimed complete by this cleanup.

### Epic W52-E1 — current contracts and core (`planned`)

#### Slice W52-E1-S1 — canonical document authoring (`done`)

- `W52-E1-S1-T1` (done) Align repair/intervention prompts and stage-brief contracts with AIDD-owned records.
  - Output: consistent prompts, contracts, examples, and normative architecture.
  - Scope: prompt packs and document ownership guidance.
  - Verification: prompt-quality, contract examples, stage preparation, and deterministic scenario checks.

#### Slice W52-E1-S2 — core and adapter cleanup (`planned`)

- `W52-E1-S2-T1` (done) Remove unused core APIs and obsolete artifact readers; consolidate active duplicates.
  - Output: current-only core readers and shared helpers with current behavior preserved.
  - Scope: core modules and their focused tests.
  - Verification: core tests cover current round trips and explicit rejection of retired formats.

- `W52-E1-S2-T2` (done) Remove adapter residue and obsolete configuration compatibility.
  - Output: smaller adapters/configuration without unused APIs, shadowed TypeVars, or logging.mode.
  - Scope: adapters, root configuration modules, and relevant CLI config display.
  - Verification: adapter/configuration tests and type checking.

- `W52-E1-S2-T3` (done) Remove dead validator grammar and retired vocabulary.
  - Output: one current tasklist grammar and canonical report vocabulary.
  - Scope: validators and validator tests.
  - Verification: validator suite preserves current valid/invalid document outcomes.

- `W52-E1-S2-T4` (next) Remove unused core and adapter facades confirmed by the second audit.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: current core functions and adapter surfaces without unconsumed wrappers or
    disconnected provider scaffolding.
  - Scope: core/adapter helpers, projections, exports, and their tests in the second cleanup PR.
  - Verification: complete reference review; preserve current output ownership, path containment,
    atomic writes, repair eligibility, command assembly, raw-byte capture, and capability guards.

- `W52-E1-S2-T5` (soon) Remove unconsumed validator aliases, path facades, and reverse lookup.
  - Dependencies: `W52-E1-S2-T4` and the second cleanup PR merged into main.
  - Output: validator consumers use the existing typed failure object and kind-based resolver.
  - Scope: document loader/protocol, structural and placeholder helpers, and direct tests;
    the third cleanup PR after a fresh audit.
  - Verification: complete reference review and readable, malformed, missing, and failed-read
    regressions preserve the current issue codes and fail-closed behavior; required CI passes.

- `W52-E1-S2-T6` (soon) Reject retired or incomplete persisted formats at current read boundaries.
  - Dependencies: `W52-E1-S2-T4` and the second cleanup PR merged into main.
  - Output: existing ledger, stage metadata, repair grant, repository snapshot, run manifest,
    and remediation documents require their current schema and required evidence fields.
  - Scope: current core readers, owning contracts, and negative/integration regressions in
    the third cleanup PR; no automatic version upgrade or invented lifecycle history.
  - Verification: current round trips and task/resume flows pass; missing/retired/unknown
    versions and malformed required fields stop explicitly. Preserve absent pre-execution
    documents, nullable initial fields, and read-only unavailable-evidence diagnostics.

### Epic W52-E2 — execution surfaces (`planned`)

#### Slice W52-E2-S1 — harness cleanup (`planned`)

- `W52-E2-S1-T1` (done) Remove dead harness implementations and obsolete evidence compatibility.
  - Output: authoritative report/process helpers and current evidence readers.
  - Scope: harness/evals and their tests.
  - Verification: harness/eval tests and deterministic scenario lane.

- `W52-E2-S1-T2` (next) Remove unused harness and eval projections found by the second audit.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: evidence parsing, verdict writing, teardown, and source/owner observation use
    their maintained paths without alternate test-only facades.
  - Scope: harness/eval helpers and their tests in the second cleanup PR.
  - Verification: preserve failure precedence, simultaneous execution/teardown failure evidence,
    source-integrity and real-PID observations; retain documented manual and CI entrypoints.

#### Slice W52-E2-S2 — operator UI cleanup (`planned`)

- `W52-E2-S2-T1` (done) Remove unused UI functions and dormant test-only components.
  - Output: maintained UI assets and tests represent rendered product behavior.
  - Scope: CLI/static assets, frontend/browser tests, and UI-only helpers.
  - Verification: frontend Node tests, UI tests, JavaScript syntax, and packaged browser journeys.
  - Evidence: all 12 packaged journey selections passed before integration (78 cases plus
    10 focused browser checks). After integrating Focus Canvas, the complete question/Inbox
    files passed 17 cases; all 140 Node tests and 25 JavaScript syntax checks passed.

- `W52-E2-S2-T2` (next) Remove unreachable UI renderers, selectors, and empty calls.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: current History, recovery inspector, and Focus Canvas retain their behavior while
    obsolete renderers, transitive helpers, duplicate state lists, and unused CSS disappear.
  - Scope: packaged JavaScript/CSS and current UI assertions in the second cleanup PR.
  - Verification: source references, JavaScript syntax, Node state tests, asset contracts,
    and all packaged browser journeys; keep current actions, routes, accessibility and geometry.

### Epic W52-E3 — repository maintenance (`planned`)

#### Slice W52-E3-S1 — active documentation (`planned`)

- `W52-E3-S1-T1` (done) Remove historical reports and stale planning history; repair active references.
  - Output: current documentation index, compact planning, and no stale active file references.
  - Scope: historical docs/reports, roadmap/backlog, contributor instructions, documentation tests.
  - Verification: documentation consistency, repository hygiene, and local-link checks.

- `W52-E3-S1-T2` (next) Reconcile remaining obsolete compatibility statements and planning overlap.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: maintained documents describe current readers and recovery; the accepted audit plan
    distinguishes remaining work from already merged cleanup without rewriting historical findings.
  - Scope: normative documentation and bounded planning reconciliation in the second cleanup PR.
  - Verification: implementation/reference review, documentation/planning checks and link audit.

#### Slice W52-E3-S2 — integration verification (`done`)

- `W52-E3-S2-T1` (done) Verify the integrated cleanup and reconcile remaining residue.
  - Dependencies: `W52-E3-S1-T1`, `W52-E1-S1-T1`, `W52-E1-S2-T1`, `W52-E1-S2-T2`, `W52-E1-S2-T3`, `W52-E2-S1-T1`, `W52-E2-S2-T1`.
  - Output: lint/type/test/scenario evidence and a reconciled current queue.
  - Scope: integration fixes and verification only.
  - Verification: complete repository quality gates and inspection of current workflow outputs.
  - Local evidence: integration coverage includes 517 core/adapter/CLI cases, contract and
    packaging checks, 140 Node tests, 17 Focus Canvas question/Inbox browser cases, Ruff,
    strict mypy (231 source files), instruction/planning checks, and all five CI scenarios.
    Scenario evidence confirms 29 executed verification commands, 15 matching artifact digests,
    20 scoped stage attempts, and no repairs. The two plan-only fixtures also retain four
    preexisting upstream attempt indexes; those are not additional executed attempts.
  - Merged evidence: PR #533 merged as `82dc9b3c` on 2026-09-06; its tree matches reviewed
    head `08d304c1`. Required CI passed on Python 3.12/3.13/3.14 (2697 passed, 8 platform/environment
    skips each), all 12 packaged browser journeys (78 cases), all five CI scenarios, adapter
    conformance, wheel/sdist build, dependency review, CodeQL, and Scorecard. Fresh follow-up
    findings are owned by the second and third cleanup PR tasks above.
