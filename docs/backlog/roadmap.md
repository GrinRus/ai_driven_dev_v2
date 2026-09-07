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

### Parent-status algebra and archive authority

Wave, epic, and slice headings expose only `planned` or `done`; local tasks use the six
statuses above. A parent status is derived from its declared children, recursively, rather
than from its prose or queue placement:

| Child state | Parent status | Rule |
| --- | --- | --- |
| One or more children exist and every child is `done` | `done` | The parent has no unresolved child outcome. |
| Any child is `planned`, `next`, `soon`, `parked`, or `blocked` | `planned` | The parent still has unresolved or deferred work. |
| No child task/container is declared | `planned` | An empty container cannot claim completion. |

Examples: children `[done, done]` roll up to `done`; `[done, planned]`, `[done, blocked]`,
and `[done, parked]` roll up to `planned`; `[parked, parked]` also remains `planned`.

`parked` means consciously deferred, not completed: a parked child keeps its parent
`planned`, remains visible in the backlog `Parking lot`, and must not be converted into
completion evidence. `blocked` has the same non-terminal roll-up but must retain the
dependency gap that prevents execution. `next` and `soon` are actionable queue projections;
they also keep the parent `planned`. A parent may become `done` only after every declared
child has an explicit `done` marker and the corresponding completion evidence is present.

The current-state authorities are separate from the archive: `roadmap.md` is canonical for
hierarchy, task definitions, dependencies, and statuses, while `backlog.md` is the exact
projection of non-done queue statuses (`next`, `soon`, and `parked`), with `parked` reserved
for deferred rather than actionable work. Completed task
definitions, dated reconciliation notes, and their evidence are archived by the merged Git
history reachable from `origin/main` (PR/commit SHAs are the retrieval keys). Unmerged
branches, working trees, and historical prose never override the current roadmap or queue;
a future history document may improve discoverability but is not a second status authority.

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

### Epic W46-E1 — multi-context UI jobs (`done`)

#### Slice W46-E1-S2 — context-aware navigation and job visibility (`done`)

Goal: remove the over-broad project-switch guard while keeping safe job inspection and mutation.

- `W46-E1-S2-T4` (done) Add a provider-free two-project browser scenario for navigation and isolation.
  - Output: deterministic UI scenario and retained evidence for switching, logs, and artifacts.
  - Scope: `browser_tests/test_journey_inbox.py`, `tests/test_packaged_ui_scenarios.py`, scenario
    assets, and E2E docs.
  - Verification: packaged browser gate passes without console errors or cross-project artifacts.
  - Completion evidence: PR #540 was squash-merged as `6a12a338`; the provider-free packaged
    browser gate, Python 3.12/3.13/3.14 lint/type/test matrix, adapter conformance, deterministic
    scenarios, build, CodeQL, dependency review, and Scorecard all passed. The journey records
    captured origin context and live job logs across a sibling-project switch, then verifies
    selected-project artifact/log isolation after returning to the origin workspace.

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

## Wave 48 — lifecycle and evidence truth (`done`)

Goal: make attempt evidence explicit and prevent ordinal storage numbers from being interpreted as
repair history.

### Epic W48-E3 — truthful eval evidence (`done`)

#### Slice W48-E3-S1 — explicit attempt lineage (`done`)

Primary output: stage, task, and aggregate-finalization attempts share a versioned lineage contract
while retired ordinal-only evidence is rejected rather than silently upgraded.

- `W48-E3-S1-T1` (done) Define versioned stage/task/finalization attempt lineage with current-format
  rejection of retired ordinal-only evidence.
  - Output: typed core lineage model, current artifact-index/task-reference/finalization views,
    explicit retired-format rejection, and normative contract updates.
  - Scope: `src/aidd/core/attempt_lineage.py`, core evidence models, task/finalization state,
    `docs/architecture/`, `contracts/documents/`, and focused core tests; no UI-owned paths.
  - Verification: round-trip fixtures distinguish `initial`, `repair`, `resume`, `intervention`,
    `repair-extension`, `task`, and `finalization`; retired ordinal-only payloads are rejected.
  - Completion evidence: PR #542 merged to `origin/main` at `08c902af`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local core, CLI/eval, remaining non-UI, and planning/docs
    suites passed; the adjacent UI checkout remained untouched.
- `W48-E3-S1-T2` (done) Persist lineage from each owning lifecycle service.
  - Dependencies: `W48-E3-S1-T1` and W48-E1 terminalization.
  - Output: stage preparation, task-attempt lifecycle, task evidence references, and aggregate
    finalization publish one explicit lineage object before their durable state is exposed.
  - Scope: core lifecycle/evidence writers, focused lifecycle tests, and architecture guidance;
    no UI-owned paths.
  - Verification: three dependency-ordered clean task attempts retain `scope: task` lineage in
    state and reference manifests, finalization retains `scope: finalization`, and no repair edge
    is inferred from empty or ordinal-only stage references.
  - Completion evidence: PR #544 merged to `origin/main` at `8deed571`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local core (1087), planning (13), Ruff, and strict mypy
    checks passed; the adjacent UI checkout remained untouched.
- `W48-E3-S1-T3` (done) Derive timing, repair history, and repair matrix only from lineage.
  - Dependencies: `W48-E3-S1-T2`.
  - Output: evaluation projections classify repairs from explicit stage lineage rather than
    attempt ordinals.
  - Scope: `stage_timing.py`, repair-history projections, deterministic evidence tests, and
    related documentation; no UI-owned paths.
  - Verification: DET-004 reports zero repairs for clean attempts; one injected `repair` lineage
    reports exactly one repair without treating resume or intervention as repair.
  - Completion evidence: PR #546 merged to `origin/main` at `2ad81274`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local stage-timing (6), live black-box harness (66),
    eval/failure-evidence (144), Ruff, and strict mypy checks passed; the adjacent UI checkout
    remained untouched.

#### Slice W48-E3-S2 — one failure-cause model (`done`)

Primary output: execution verdict and first decisive cause remain compatible across every report.

- `W48-E3-S2-T1` (done) Define typed failure cause, phase, source, reason, evidence link, and
  legacy mapping.
  - Output: one versioned failure-cause contract with a fail-closed compatibility table for
    execution verdicts and first decisive causes.
  - Scope: eval contracts and focused model/projection tests; no UI-owned paths.
  - Verification: contradictory verdict/cause combinations are rejected, while setup failure,
    provider/runtime failure, validation failure, and infrastructure failure retain distinct
    report semantics.
  - Completion evidence: PR #548 merged to `origin/main` at `f45c4d84`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local failure-cause (26), eval/failure-evidence (215),
    Ruff, and strict mypy checks passed; the adjacent UI checkout remained untouched.
- `W48-E3-S2-T2` (done) Preserve partial phase transcripts and the failing command.
  - Dependencies: `W48-E3-S2-T1`.
  - Output: a failed phase retains all completed command records, the failing command, and its
    typed primary cause before later evidence enrichment.
  - Scope: harness runner and focused harness/eval evidence tests; no UI-owned paths and no
    verdict/report projection changes beyond the persisted failure-cause seam.
  - Verification: a two-command phase whose second command fails records commands one and two,
    preserves the original cause, and remains readable after enrichment failure.
  - Completion evidence: PR #550 merged to `origin/main` at `d11d56c8`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local harness, eval, planning/docs, Ruff, and strict
    mypy checks passed; the adjacent UI checkout remained untouched.
- `W48-E3-S2-T3` (done) Propagate the cause through log analysis, grader, verdict, and summary.
  - Dependencies: `W48-E3-S2-T2`.
  - Output: one typed first-decisive cause is carried into log-analysis, grader, verdict, and
    summary projections without synthesizing validation findings for infrastructure failures.
  - Scope: eval log analysis/reporting/verdict writers and focused regression tests; no UI-owned
    paths and no browser payload changes.
  - Verification: DET-002 is classified as `infra-fail` with an `infrastructure`/`setup` cause,
    while malformed Markdown remains `fail` with a `validation` cause; contradictory projections
    are rejected.
  - Completion evidence: PR #552 merged to `origin/main` at `11cb9685`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Local eval suite (169), focused harness/eval regression
    suites, Ruff, and strict mypy passed; a real AIDD-DETERMINISTIC-002 run produced
    `infra-fail` / `infrastructure` / `setup` without synthetic validator findings. The adjacent
    UI checkout remained untouched.

#### Slice W48-E3-S3 — self-contained bundle v2 (`done`)

Primary output: a PASS bundle remains fully auditable after harness cache deletion.

- `W48-E3-S3-T1` (done) Define conditional bundle inventory, separate eval/product IDs, relative
  references, and legacy policy.
  - Dependencies: `W48-E3-S1-T1` and `W48-E3-S2-T1`.
  - Output: current bundle contract distinguishes evaluation identity from product-run identity,
    validates conditional artifact inventory and workspace-relative references, and rejects
    ambiguous or legacy-only evidence instead of guessing.
  - Scope: result-bundle/eval contracts and focused integrity fixtures; no UI-owned paths.
  - Verification: fixtures reject dangling links and ambiguous identity while preserving valid
    pass/fail/infra-fail bundle reads.
  - Completion evidence: PR #554 merged to `origin/main` at `70f4731e`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Full `make check` passed (3107 Python tests, Ruff,
    strict mypy, JavaScript, instruction, and planning checks); focused bundle contract fixtures
    passed (13). The adjacent UI checkout remained untouched.
- `W48-E3-S3-T2` (done) Persist actual product run ID, feature selection, and phase metadata.
  - Dependencies: `W48-E3-S3-T1`.
  - Output: successful runs retain distinct eval/product IDs and an existing feature-selection
    record with phase metadata.
  - Scope: eval report preparation/materialization; no UI-owned paths.
  - Verification: successful bundle references distinct IDs and a readable feature-selection
    artifact.
  - Completion evidence: PR #556 merged to `origin/main` at `70929f5a`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Full `make check` passed (3107 Python tests, Ruff,
    strict mypy, JavaScript, instruction, and planning checks); focused eval/harness coverage
    passed (186 tests). The adjacent UI checkout remained untouched.
- `W48-E3-S3-T3` (done) Materialize raw attempt logs/exits/events, stage validators, task
  ledger, and finalization evidence.
  - Dependencies: `W48-E3-S3-T2`.
  - Output: all required raw and canonical evidence is copied into the bundle before cache cleanup.
  - Scope: result-bundle materializer and focused evidence tests; no UI-owned paths.
  - Verification: references survive deletion of product and harness `.aidd` roots.
  - Completion evidence: PR #558 merged to `origin/main` at `432ca93e`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Focused result-bundle/eval coverage passed (32 tests);
    Ruff and strict mypy passed for changed modules. The adjacent UI checkout remained untouched.
- `W48-E3-S3-T4` (done) Atomically seal and validate inventory, digests, sizes, and identities
  before PASS.
  - Dependencies: `W48-E3-S3-T3`.
  - Output: missing, mutated, orphaned, or identity-ambiguous evidence converts candidate PASS to
    an explicit bundle-integrity failure.
  - Scope: bundle finalization and integrity validator; no UI-owned paths.
  - Verification: integrity fixtures exercise missing, mutated, orphaned, and mismatched identity
    evidence before allowing PASS.
  - Completion evidence: PR #560 merged to `origin/main` at `b85db4e8`; Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. Full local Python regression reached 3112 tests; after
    correcting a provider-free smoke fixture, targeted lifecycle/eval coverage passed (15),
    result-bundle sealing/contract coverage passed (34), Ruff and strict mypy passed. The adjacent
    `codex/ui-completion` checkout remained untouched.

Dependencies: T1 → T2/T3 → T4.

## Wave 49 — product boundaries and sustainable maintenance (`planned`)

### Epic W49-E1 — truthful product and provider boundaries (`done`)

#### Slice W49-E1-S1 — project-set policy and implement gate (`done`)

The mode-specific capability decision keeps full-access detection/attribution distinct from
preventive containment in brokered or isolated modes. Later W49 tasks remain in the accepted
remediation plan until their dependencies are promoted into this canonical roadmap.

- `W49-E1-S1-T1` (done) Publish a mode-specific project-set capability matrix in US-12 and
  architecture.
  - Output: product wording and architecture describe declaration, attribution, detection, and
    fail-closed progression for full-access mode, while reserving preventive containment claims
    for brokered/isolated modes.
  - Scope: `docs/product/user-stories.md` and `docs/architecture/`; no UI-owned paths.
  - Verification: documentation checks reject unconditional containment wording and preserve the
    declared project-set workflow. Completed in PR #562, merged as `3d75b674`; the focused docs,
    planning, and agent-workflow checks passed (63 tests), and the required Python, adapter,
    deterministic, packaged UI, build, CodeQL, Scorecard, and dependency-review checks passed.

- `W49-E1-S1-T2` (done) Block aggregate finalization when repository evidence contains
  outside-set changes.
  - Output: full-access runs detect exact outside-root paths and prevent Review/QA progression
    until the evidence is explicitly handled; brokered/isolated containment behavior remains
    unchanged.
  - Scope: core project-set diff/evidence reader, aggregate implementation finalization gate,
    and focused lifecycle/evidence tests; no UI-owned paths.
  - Verification: a two-root implementation fixture with an intentional outside-root change
    leaves exact path evidence and blocks aggregate finalization and downstream Review/QA.
  - Completion evidence: PR #564 merged to `origin/main` at `0b671901`; the focused docs,
    planning, lifecycle, evidence, implementation-service, and CLI conformance checks passed
    (127 tests), Ruff and strict mypy passed, and all required Python 3.12–3.14, adapter-
    conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard, and
    dependency-review checks passed. The adjacent `codex/ui-completion` checkout remained
  untouched.

- `W49-E1-S1-T3` (done) Add two-root positive and outside-root negative implement scenarios.
  - Output: deterministic project-set fixtures prove both the positive two-root workflow and the
    outside-root rejection path without weakening the aggregate finalization gate.
  - Scope: deterministic scenario manifests, fixtures, and assertions; no new UI presentation
    pattern and no runtime-specific logic in core.
  - Verification: the positive run changes both declared roots, while the negative run preserves
    exact outside-root evidence and stops Review/QA progression.
  - Completion evidence: PR #579 merged to `origin/main` at `f434a977`; the positive and negative
    deterministic scenarios passed in the full CI lane, including expected fail-closed exit code,
    exact outside-root/task attribution, and Review/QA non-progression. Focused loader, verdict,
    lifecycle, documentation, and scenario tests passed; the required Python 3.12–3.14, adapter-
    conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard, and
    dependency-review checks passed on the exact candidate. No UI-owned files were changed.
  - Dependencies: `W49-E1-S1-T2` and the completed UI copy/browser acceptance in
    `W49-E1-S1-T4`.

- `W49-E1-S1-T4` (done) Align UI copy with detected/rejected versus preventively contained
  modes.
  - Output: the operator UI distinguishes full-access detection/attribution warnings from
    brokered or isolated preventive containment while reusing the merged Focus Canvas components.
  - Scope: UI presentation copy and its DOM/browser acceptance; no parallel presentation pattern.
  - Verification: full-access and enforced-containment fixtures render distinct copy and preserve
    the shared core recommendation.
  - Dependency note: the neighboring UI refactor is now integrated by PR #574 at `45a1a8f7`;
    this task owned the remaining UI copy/browser acceptance and reused the integrated Focus Canvas
    surfaces. Keep the adjacent checkout read-only; integration is through `origin/main`.
  - Completion evidence: PR #577 merged to `origin/main` at `4237289b`; the exact persisted
    `runtime_permission_policy` is projected into the run summary and mode-specific copy is covered
    by frontend, manifest, core, characterization, responsive-browser, and documentation checks.
    The required Python 3.12–3.14, adapter-conformance, deterministic-scenarios,
    packaged-ui-browser, build, CodeQL, Scorecard, and dependency-review lanes passed on the exact
    candidate. The adjacent UI PR #574 remains the shared presentation baseline.

Dependencies: W48 exit gate → `W49-E1-S1-T1` → `W49-E1-S1-T2` → `W49-E1-S1-T4` →
`W49-E1-S1-T3`. T4 was implemented only after the merged W47 UI work; all four local tasks are
now complete and the slice is marked `done` by the planning-hygiene roll-up.

#### Slice W49-E1-S2 — adapter-owned provider metadata (`done`)

Primary output: adding a runtime does not require provider literals or credential filenames in
runtime-neutral core.

- `W49-E1-S2-T1` (done) Define adapter security/capability descriptor.
  - Output: an adapter-owned descriptor contract covers protected paths, credentials, config,
    and runtime capabilities without provider-specific branches in core.
  - Scope: adapter protocol and runtime-neutral metadata types, with focused contract tests; no
    UI-owned paths.
  - Verification: a descriptor contract test accepts a fake runtime descriptor containing
    protected paths, credential/config metadata, and capabilities without editing core provider
    literals.
  - Completion evidence: PR #566 merged to `origin/main` at `53834da5`; the focused adapter,
    documentation, planning, and workflow checks passed (377 tests), Ruff and strict mypy passed,
    and all required Python 3.12–3.14, adapter-conformance, deterministic-scenarios,
    packaged-ui-browser, build, CodeQL, Scorecard, and dependency-review checks passed. The
    adjacent `codex/ui-completion` checkout remained untouched.

- `W49-E1-S2-T2` (done) Implement descriptors for built-in runtimes.
  - Output: every maintained runtime surface supplies a validated adapter-owned descriptor for
    protected, credential, and config paths plus supported capabilities.
  - Scope: built-in adapter packages, runtime-surface registration, and contract tests; no core
    provider literals and no UI-owned paths.
  - Verification: a contract table resolves a descriptor for every `runtime_ids()` entry, keeps
    runtime IDs stable, rejects unsafe metadata, and confirms the core has no new provider-specific
    branches.
  - Completion evidence: PR #568 merged to `origin/main` at `a211670e`; all maintained surfaces
    now expose adapter-owned descriptors and the marker table covers every runtime. Focused and
    full adapter, documentation, planning, and workflow checks passed (378 tests), Ruff and strict
    mypy passed, and all required CI lanes passed after one documented flaky packaged-browser
    rerun. The adjacent `codex/ui-completion` checkout remained untouched.

- `W49-E1-S2-T3` (done) Consume protected-path metadata and remove provider literals from core.
  - Output: runtime policy consumes adapter-owned protected, credential, and config markers through
    an injected runtime-neutral seam; provider names and filenames are absent from core policy
    branches while existing protection classifications remain fail-closed.
  - Scope: runtime-neutral policy inputs, adapter-to-core composition, and security/lifecycle tests;
    no UI-owned paths.
  - Verification: the existing protection matrix passes for every built-in runtime, an injected
    descriptor drives classification for a fake runtime, and a source guard rejects new provider
    literals in `aidd.core`.
  - Completion evidence: PR #570 merged to `origin/main` at `82b7bdb1`; core and adapter suites
    passed (1405 tests), Ruff and strict mypy passed, and all required Python, adapter,
    deterministic, packaged-ui-browser, build, CodeQL, Scorecard, and dependency-review checks
    passed. The adjacent `codex/ui-completion` checkout remains untouched.

- `W49-E1-S2-T4` (done) Drive built-in registration/config compatibility from descriptors.
  - Output: built-in runtime registration and configuration compatibility consume adapter-owned
    descriptors without central provider branches; existing runtime IDs and TOML remain stable.
  - Scope: adapter registry/config composition and compatibility tests; no UI-owned paths.
  - Verification: existing runtime IDs and TOML configurations resolve unchanged, while a source
    guard prevents new provider-specific registration branches in runtime-neutral code.
  - Completion evidence: PR #572 merged to `origin/main` at `60de556a`; adapter/core suites
    passed (1409 tests), focused registry/config/docs checks passed (155 tests), Ruff, strict
    mypy, and `git diff --check` passed, and all required Python 3.12–3.14, adapter-conformance,
    deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard, and dependency-review
    checks passed. The adjacent UI work remained untouched in this task; it was subsequently
    integrated by PR #574 at `45a1a8f7`.

- `W49-E1-S2-T5` (done) Prove clean extension with an allowlisted fake external descriptor.
  - Output: a fake runtime can participate through adapter-local code and an explicit matrix row
    without a runtime-neutral core edit.
  - Scope: architecture/conformance fixtures and extension documentation; no UI-owned paths.
  - Verification: the fake descriptor passes the adapter/security matrix and core source guards
    continue to reject provider literals.
  - Completion evidence: PR #575 merged to `origin/main` at `e0fceade` after updating its base to
    the integrated UI merge `45a1a8f7`; the test-only descriptor proved catalog projection,
    all seven conformance dimensions, and protected-path policy injection without production
    registration. The extended local suite passed (557 tests), Ruff/format and diff checks
    passed, and all required Python 3.12–3.14, adapter-conformance, deterministic-scenarios,
    packaged-ui-browser, build, CodeQL, Scorecard, and dependency-review checks passed on the
    exact candidate. No UI-owned files were changed by this task.

Dependencies: W48 exit gate → `W49-E1-S2-T1` → `W49-E1-S2-T2` → `W49-E1-S2-T3` →
`W49-E1-S2-T4` → `W49-E1-S2-T5`; all W49-E1 boundary tasks are complete, and the active queue
item is `W49-E2-S2-T1` for server-side UI job lifecycle extraction.

### Epic W49-E2 — behavior-preserving hotspot reduction (`planned`)

#### Slice W49-E2-S1 — live harness decomposition (`done`)

- `W49-E2-S1-T1` (done) Characterize public live-facade artifact and event ordering.
  - Output: a deterministic characterization records the normalized artifacts and event order
    that the public live facade must preserve during later decomposition.
  - Scope: harness characterization tests and deterministic fixtures; no runtime or UI-owned paths.
  - Verification: current and extracted-path fixtures produce equivalent normalized artifacts and
    event ordering without provider credentials.
  - Dependencies: W48 evidence semantics are stable and the merged W47 UI compatibility baseline
    is available.
  - Completion evidence: PR #595 merged to `origin/main` at `0011426f`; the provider-free
    characterization runs the public facade twice and compares stable artifact inventory,
    normalized flow steps, operator event order, and completed-stage state while allowing the
    documented optional provisional running-stage checkpoint. Focused characterization, existing
    public-bundle, boundary, Ruff, and diff checks passed; all required Python, adapter,
    deterministic, packaged-browser, build, CodeQL, Scorecard, and dependency-review lanes passed
    on the exact candidate. No runtime or UI-owned files changed.

- `W49-E2-S1-T2` (done) Remove the unreachable 14-function `_legacy_*` process island.
  - Output: the live orchestrator contains no unreachable legacy process implementation while
    preserving the canonical step/report helpers and the T1 characterization contract.
  - Scope: live orchestrator cleanup and harness boundary verification; no UI-owned paths.
  - Verification: source inspection finds no `_legacy_*` process definitions, canonical helper
    imports remain in place, and the T1 characterization stays green.
  - Completion evidence: the required removal is already present on `origin/main` in commit
    `4d99b3fd` (`refactor: remove repository residue and require current formats`), which removed
    the 14-function island and obsolete imports. PR #595 revalidated the characterization and
    public bundle boundaries after that cleanup; no duplicate production edit is required.

- `W49-E2-S1-T3` (done) Extract stage execution/inspection.
  - Output: stage execution and post-stage inspection move behind a focused harness module while
    the public live facade keeps its current behavior and artifact contract.
  - Scope: live harness stage execution/inspection helpers and deterministic terminal/blocked
    fixtures; no frontend probe, report, runtime, or UI-owned paths.
  - Verification: terminal and blocked fixtures produce equivalent normalized artifacts and event
    ordering before and after extraction, without provider credentials.
  - Dependencies: `W49-E2-S1-T1` and `W49-E2-S1-T2`, stable W48 evidence semantics, and the
    merged W47 UI compatibility baseline.
  - Completion evidence: PR #597 merged to `origin/main` at `25b58943`; stage classification,
    public inspection-question detection, and the stage loop now live in
    `live_e2e_black_box_stage.py` behind callback-owned runtime seams. Focused terminal,
    blocked, quality-gate, boundary, characterization, Ruff, and strict mypy checks passed;
    all required Python, adapter, deterministic, packaged-browser, build, CodeQL, Scorecard,
    and dependency-review lanes passed on the exact candidate. No frontend, report, runtime,
    or UI-owned files changed.

- `W49-E2-S1-T4` (done) Extract frontend probes and semantic-failure classification.
  - Output: frontend HTTP probes, target selection, operator-surface checks, and semantic-failure
    classification move behind a focused harness probe module while checkpoint evidence and the
    public live facade retain their current behavior.
  - Scope: live harness frontend probe helpers and deterministic probe-state matrix; no report,
    runtime, or UI-owned paths.
  - Verification: ready, non-2xx, malformed JSON, semantic mismatch, running-stage, and rich
    task-projection probe states preserve classifications, operator checks, artifacts, and event
    ordering without provider credentials.
  - Dependencies: `W49-E2-S1-T3`, stable W48 evidence semantics, and the merged W47 UI
    compatibility baseline.
  - Completion evidence: PR #599 merged to `origin/main` at `b5b3fa47`; HTTP probes, target
    selection, semantic classification, timeout handling, and operator-surface checks now have
    one canonical owner in `live_e2e_black_box_frontend.py`, with private orchestration aliases
    retained for compatibility. The deterministic probe matrix and 96-test harness group passed,
    characterization remained green, and all required Python, adapter, deterministic,
    packaged-browser, build, CodeQL, Scorecard, and dependency-review lanes passed. No UI-owned
    files changed.

- `W49-E2-S1-T5` (done) Extract bundle/report coordination behind the facade.
  - Output: result-bundle materialization, report finalization, and terminal artifact coordination
    move behind a focused harness report module while success, blocked, and manual-stop bundles
    retain their current schemas and evidence ownership.
  - Scope: live harness bundle/report coordination and deterministic bundle fixtures; no frontend,
    runtime, or UI-owned paths.
  - Verification: success, blocked, awaiting-quality-review, and manual-stop flows preserve
    normalized bundle inventory, report content, terminal status, and event ordering without
    provider credentials.
  - Dependencies: `W49-E2-S1-T4`, stable W48 evidence semantics, and the merged W47 UI
    compatibility baseline.
  - Completion evidence: PR #601 merged to `origin/main` at `71659ca0`; canonical result-bundle
    materialization/sealing and run-transcript serialization now have one focused owner behind
    the live facade. Success, blocked, awaiting-quality-review, and manual-stop fixtures retain
    their normalized artifacts and schemas; focused bundle tests, the 99-test harness group,
    characterization, Ruff, strict mypy, and all required CI/security lanes passed. No frontend,
    runtime, or UI-owned files changed.

#### Slice W49-E2-S2 — post-Focus-Canvas service-boundary stabilization (`planned`)

Primary output: server-side UI orchestration is decomposed without revisiting W47 presentation or
changing its public behavior.

- `W49-E2-S2-T1` (next) Extract UI job registry/lifecycle from `cli/ui.py`.
  - Output: project-scoped job registration, lookup, and lifecycle transitions move behind a
    focused CLI application-service module while existing HTTP and operator behavior remains
    unchanged.
  - Scope: server-side UI orchestration and lifecycle tests; no `src/aidd/cli/static/**`,
    `tests/frontend/**`, UI browser journeys, or neighboring UI checkout edits.
  - Verification: two-project job lifecycle fixtures preserve isolation, cleanup, and terminal
    state behavior; the post-W47 CLI/frontend/browser compatibility baseline remains green.
  - Dependencies: merged W47 UI PR, completed W49-E2-S1 decomposition, and a fresh
    `origin/main` baseline. Compare the final W47 diff before implementation and reslice if that
    work already owns any lifecycle output.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S2-T1` | Extract UI job registry/lifecycle from `cli/ui.py`. | CLI application service | Two-project job lifecycle tests preserve isolation. | 1.5d |
| `W49-E2-S2-T2` | Extract HTTP payload codecs/controller dispatch. | CLI transport | Endpoint contract suite preserves status/body shapes. | 2d |
| `W49-E2-S2-T3` | Replace dashboard `_next_action` branching with ordered typed rules. | Core dashboard evidence | Full state matrix yields exactly one deterministic action. | 1d |

Dependencies: merged W47 UI PR and a green post-merge CLI/frontend/browser compatibility baseline.
Before promoting each task, compare it with the final W47 diff. If W47 already produces the
output, record that evidence and reslice only the remaining hotspot; do not repeat the refactor.

#### Slice W49-E2-S3 — complexity-tail ratchet (`planned`)

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S3-T1` | Add a reviewed complexity baseline and no-new-E/F ratchet. | Quality tooling | Synthetic new E/F block fails the check. | 1d |
| `W49-E2-S3-T2` | Decompose `build_task_flow_checkpoint`. | Task checkpoint | Complexity is C or lower and checkpoint fixtures are byte-equivalent. | 2d |
| `W49-E2-S3-T3` | Decompose `_validate_scenario_contract`. | Scenario validation | Complexity is C or lower and invalid-manifest matrix is unchanged. | 1.5d |
| `W49-E2-S3-T4` | Decompose `run_single_stage_orchestration` after W48. | Core stage lifecycle | Transition matrix remains green and complexity is C or lower. | 2d |
| `W49-E2-S3-T5` | Decompose the Codex live transport. | Codex adapter | Codex adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |
| `W49-E2-S3-T6` | Decompose the Qwen live transport. | Qwen adapter | Qwen adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |

Dependencies: T1 first; every remaining task is independent and behavior-preserving.

### Epic W49-E3 — planning and documentation truth (`done`)

#### Slice W49-E3-S1 — executable planning hygiene (`done`)

- `W49-E3-S1-T1` (done) Define parent-status algebra, including parked-child semantics and
  archive authority.
  - Output: the planning contract defines unambiguous `done`, `planned`, `parked`, and `blocked`
    roll-up behavior and identifies the authoritative archive for completed history.
  - Scope: `docs/backlog/roadmap.md`, `docs/backlog/backlog.md`, and the planning contract;
    no runtime or UI-owned paths.
  - Verification: examples for each parent status and parked-child case pass the planning
    integrity checks without inventing completion evidence.
  - Dependencies: completed W49-E1 boundary tasks and the W48 exit gate.
  - Completion evidence: PR #581 merged to `origin/main` at `2a80f526`; the recursive
    parent-status rules, parked/blocked non-terminal semantics, and merged-history archive
    authority are documented, and planning/docs checks passed (60 tests). No runtime or
    UI-owned files changed.

- `W49-E3-S1-T2` (done) Archive historical reconciliation bullets, leaving one current note.
  - Output: historical reconciliation IDs remain discoverable in Git while active docs keep one
    bounded current note.
  - Scope: `docs/backlog/backlog.md` and linked planning history; no runtime or UI-owned paths.
  - Verification: the active queue contains no stale completion bullets and every retained ID is
    still searchable in the roadmap or history. PR #583 (`8c2f6bfe`) adds the archive index for
    the 509 bullets, including its immutable revision and verified SHA-256 digest.

- `W49-E3-S1-T3` (done) Add bounded-note and parent-status roll-up validation.
  - Output: planning integrity checks reject duplicate current notes and stale completed parents,
    while applying the explicit parked-child rule.
  - Scope: planning-integrity tests and their fixtures; no runtime or UI-owned paths.
  - Verification: duplicate-note, stale-parent, done, planned, parked, and blocked examples each
    produce the documented result.
  - Completion evidence: PR #585 merged to `origin/main` at `638d9aa`; planning-integrity now
    exposes recursive parent roll-up validation and duplicate current-note detection. The focused
    planning/docs suite passed (68 tests), Ruff and diff checks passed, and no runtime or UI-owned
    files changed.

- `W49-E3-S1-T4` (done) Reconcile current wave/epic/slice statuses mechanically.
  - Output: current roadmap parent statuses agree with their child task algebra and active queue.
  - Scope: `docs/backlog/roadmap.md` and `docs/backlog/backlog.md`; no runtime or UI-owned paths.
  - Verification: the roll-up checker reports no mismatch on the current roadmap and queue.
  - Completion evidence: PR #587 merged to `origin/main` at `83db1f5`; all current wave, epic,
    and slice markers now agree with recursive child status algebra. Both roll-up and generic
    roadmap/backlog integrity checks returned no errors; the focused planning/docs suite passed
    (68 tests), and no runtime or UI-owned files changed.

Dependencies: W49-E1-S1/T2/T4/T3 completion → `W49-E3-S1-T1` → `W49-E3-S1-T2` →
`W49-E3-S1-T3` → `W49-E3-S1-T4`.

#### Slice W49-E3-S2 — executable user-story traceability (`done`)

- `W49-E3-S2-T1` (done) Correct optional-frontmatter and superseded beta-audit wording.
  - Output: architecture and analysis documents agree with the current document contract and
    declared US-13 set.
  - Scope: `docs/architecture/` and `docs/analysis/`; no runtime or UI-owned paths.
  - Verification: documentation consistency checks reject stale optional-frontmatter or
    superseded beta-audit claims while preserving current product wording.
  - Dependencies: W49-E3-S1 completion.
  - Completion evidence: PR #589 merged to `origin/main` at `9780f1c2`; 69 focused docs/planning
    tests passed locally, and all required CI lanes passed after a transient browser-lane retry.
    No runtime or UI-owned files changed.

- `W49-E3-S2-T2` (done) Define a structured US-01…US-13 traceability registry.
  - Output: each story links to its contracts, code boundaries, tests, scenarios, and evidence.
  - Scope: product traceability data and documentation checks; no runtime or UI-owned paths.
  - Verification: every referenced artifact exists and story IDs are unique.
  - Dependencies: W49-E3-S1 completion.
  - Completion evidence: PR #591 merged to `origin/main` at `dc0cca33`; the schema-versioned
    registry covers all 13 stories and the consistency guard verifies unique IDs, required groups,
    repository-relative paths, and artifact existence. The focused docs/planning/quality suite
    passed 181 tests; no runtime or UI-owned files changed.

- `W49-E3-S2-T3` (done) Generate and validate a byte-stable traceability view in CI.
  - Output: CI validates the generated story view and rejects missing required references.
  - Scope: docs tooling and deterministic documentation fixtures; no runtime or UI-owned paths.
  - Verification: removing a required test or scenario reference fails generation.
  - Dependencies: W49-E3-S2-T1 and W49-E3-S2-T2.
  - Completion evidence: PR #593 merged to `origin/main` at `ebba859d`; the generated Markdown
    view is byte-checked in CI, registry validation rejects missing/duplicate references, and the
    focused traceability/docs/planning suite passed 77 tests. All required Python 3.12–3.14,
    adapter-conformance, deterministic-scenarios, packaged-ui-browser, build, CodeQL, Scorecard,
    and dependency-review checks passed. No runtime or UI-owned files changed.

Dependencies: `W49-E3-S1` → `W49-E3-S2-T1`/`W49-E3-S2-T2` → `W49-E3-S2-T3`.

## Wave 51 — agent development instruction consistency (`planned`)

The maintainer instruction hierarchy, executable workflow checks, runtime document ownership,
and bootstrap regressions were integrated by PR #515 and its follow-up fixes. Their completed
local-task definitions and execution records remain in Git history. Current guidance is in
`docs/agent-development.md`; the checks remain in CI. The cleanup below replaces the historical
archive and frozen prompt hashes with bounded planning and semantic prompt checks.
Because this current-format section has no declared child task hierarchy, the parent-status
algebra keeps it `planned`; historical completion records do not substitute for active children.

## Wave 52 — repository cleanup and current-format boundary (`done`)

Goal: remove unused code, obsolete compatibility, misleading instructions, and historical
repository clutter while preserving current workflow, validation, repair, and evidence behavior.

Integration note: authored as Wave 47 on `f2819535`, this cleanup is rekeyed to Wave 52
when integrating `191dfb16`. The upstream Focus Canvas Wave 47 and instruction Wave 51
keep their identities. Remaining Waves 48–50 work stays governed by the accepted remediation
plan in `docs/analysis/project-quality-remediation-plan-2026-09-05.md`; only explicitly promoted
tasks such as `W48-E3-S1-T1` are claimed in the canonical roadmap.

### Epic W52-E1 — current contracts and core (`done`)

#### Slice W52-E1-S1 — canonical document authoring (`done`)

- `W52-E1-S1-T1` (done) Align repair/intervention prompts and stage-brief contracts with AIDD-owned records.
  - Output: consistent prompts, contracts, examples, and normative architecture.
  - Scope: prompt packs and document ownership guidance.
  - Verification: prompt-quality, contract examples, stage preparation, and deterministic scenario checks.

#### Slice W52-E1-S2 — core and adapter cleanup (`done`)

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

- `W52-E1-S2-T4` (done) Remove unused core and adapter facades confirmed by the second audit.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: current core functions and adapter surfaces without unconsumed wrappers or
    disconnected provider scaffolding.
  - Scope: core/adapter helpers, projections, exports, and their tests in the second cleanup PR.
  - Verification: complete reference review; preserve current output ownership, path containment,
    atomic writes, repair eligibility, command assembly, raw-byte capture, and capability guards.

- `W52-E1-S2-T5` (done) Remove unconsumed validator aliases, path facades, and reverse lookup.
  - Dependencies: `W52-E1-S2-T4` and the second cleanup PR merged into main.
  - Output: validator consumers use the existing typed failure object and kind-based resolver.
  - Scope: document loader/protocol, structural and placeholder helpers, and direct tests;
    the third cleanup PR after a fresh audit.
  - Verification: complete reference review and readable, malformed, missing, and failed-read
    regressions preserve the current issue codes and fail-closed behavior; required CI passes.

- `W52-E1-S2-T6` (done) Reject retired or incomplete persisted formats at current read boundaries.
  - Dependencies: `W52-E1-S2-T4` and the second cleanup PR merged into main.
  - Output: existing ledger, stage metadata, repair grant, repository snapshot, run manifest,
    and remediation documents require their current schema and required evidence fields.
  - Scope: current core readers, owning contracts, and negative/integration regressions in
    the third cleanup PR; no automatic version upgrade or invented lifecycle history.
  - Verification: current round trips and task/resume flows pass; missing/retired/unknown
    versions and malformed required fields stop explicitly. Preserve absent pre-execution
    documents, nullable initial fields, and read-only unavailable-evidence diagnostics.

- `W52-E1-S2-T7` (done) Remove remaining unused core and adapter projections and forwarding modules.
  - Dependencies: `W52-E1-S2-T4` and the second cleanup PR merged into main.
  - Output: current run inspection, resume, interview, and runtime APIs without test-only
    selectors, obsolete guard islands, metadata writers, projections, or import aliases.
  - Scope: core run/attempt lookup, stage resume/manifest/repair projections, adapter interview
    persistence and runtime forwarding modules, with all meaningful test consumers migrated.
  - Verification: actual CLI resume preserves unanswered blocking, one new answered attempt,
    input bundles and old evidence; current read summaries preserve terminal inspection,
    selection, ambiguity, corruption and containment; current provider event/default tests pass.

### Epic W52-E2 — execution surfaces (`done`)

#### Slice W52-E2-S1 — harness cleanup (`done`)

- `W52-E2-S1-T1` (done) Remove dead harness implementations and obsolete evidence compatibility.
  - Output: authoritative report/process helpers and current evidence readers.
  - Scope: harness/evals and their tests.
  - Verification: harness/eval tests and deterministic scenario lane.

- `W52-E2-S1-T2` (done) Remove unused harness and eval projections found by the second audit.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: evidence parsing, verdict writing, teardown, and source/owner observation use
    their maintained paths without alternate test-only facades.
  - Scope: harness/eval helpers and their tests in the second cleanup PR.
  - Verification: preserve failure precedence, simultaneous execution/teardown failure evidence,
    source-integrity and real-PID observations; retain documented manual and CI entrypoints.

- `W52-E2-S1-T3` (done) Remove remaining unconsumed verdict and lifecycle-budget projections.
  - Dependencies: `W52-E2-S1-T2` and the second cleanup PR merged into main.
  - Output: the current verdict vocabulary and process deadline owner have no obsolete aliases.
  - Scope: `FAILURE_CLASSES`, `HarnessLifecycleBudget.exhausted`, and direct test consumers.
  - Verification: current verdict evidence, before/at-deadline behavior, zero-budget no-launch,
    process-tree cleanup, and all five deterministic scenarios remain covered.

#### Slice W52-E2-S2 — operator UI cleanup (`done`)

- `W52-E2-S2-T1` (done) Remove unused UI functions and dormant test-only components.
  - Output: maintained UI assets and tests represent rendered product behavior.
  - Scope: CLI/static assets, frontend/browser tests, and UI-only helpers.
  - Verification: frontend Node tests, UI tests, JavaScript syntax, and packaged browser journeys.
  - Evidence: all 12 packaged journey selections passed before integration (78 cases plus
    10 focused browser checks). After integrating Focus Canvas, the complete question/Inbox
    files passed 17 cases; all 140 Node tests and 25 JavaScript syntax checks passed.

- `W52-E2-S2-T2` (done) Remove unreachable UI renderers, selectors, and empty calls.
  - Dependencies: `W52-E3-S2-T1` and the first cleanup PR merged into main.
  - Output: current History, recovery inspector, and Focus Canvas retain their behavior while
    obsolete renderers, transitive helpers, duplicate state lists, and unused CSS disappear.
  - Scope: packaged JavaScript/CSS and current UI assertions in the second cleanup PR.
  - Verification: source references, JavaScript syntax, Node state tests, asset contracts,
    and all packaged browser journeys; keep current actions, routes, accessibility and geometry.

- `W52-E2-S2-T3` (done) Remove remaining dormant CSS and test-only UI projections.
  - Dependencies: `W52-E2-S2-T2` and the second cleanup PR merged into main.
  - Output: current components retain their styles, resource ownership, and typed data without
    selectors for retired screens or unused snapshot/count/id properties.
  - Scope: confirmed dead CSS selector arms and unused token declarations, packaged asset snapshots,
    question/inbox/project-set
    projections, and their source/Node/browser tests.
  - Verification: preserve dynamic classes, mixed live selector arms, consumed CSS variables and resource
    equality; migrate synthetic fixtures to current components with the same contrast, ARIA,
    numeric, wrapping and geometry assertions; all packaged browser journeys pass.

### Epic W52-E3 — repository maintenance (`done`)

#### Slice W52-E3-S1 — active documentation (`done`)

- `W52-E3-S1-T1` (done) Remove historical reports and stale planning history; repair active references.
  - Output: current documentation index, compact planning, and no stale active file references.
  - Scope: historical docs/reports, roadmap/backlog, contributor instructions, documentation tests.
  - Verification: documentation consistency, repository hygiene, and local-link checks.

- `W52-E3-S1-T2` (done) Reconcile remaining obsolete compatibility statements and planning overlap.
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

- `W52-E3-S2-T2` (done) Verify the final cleanup and restore the deferred acceptance queue.
  - Dependencies: `W52-E1-S2-T5`, `W52-E1-S2-T6`, `W52-E1-S2-T7`, `W52-E2-S1-T3`, `W52-E2-S2-T3`.
  - Output: reviewed cleanup, current-format and workflow evidence, no untriaged confirmed residue,
    and the eight previously pending acceptance tasks restored without invented completion.
  - Scope: integrated checks, reference/link/resource audit, and bounded queue reconciliation.
  - Verification: nearest Python/Node checks, full lint/type checks, deterministic artifacts,
    packaged browser journeys and required PR CI; merge each iteration and verify main's tree.
  - Predecessor evidence: PR #534 merged as `d6ed8e22` on 2026-09-06, identical to reviewed head
    `72bf2521` including upstream ownership registry `95384796`. Python 3.12/3.13/3.14 each passed
    2711 tests with 8 platform/environment skips; all 12 browser journeys passed 78 cases,
    all five deterministic scenarios and four adapter conformance cases passed, as did
    wheel/sdist build, Ruff, mypy (229 files), 140 Node tests, dependency review, CodeQL and Scorecard.
  - Final local evidence: all five deterministic scenarios passed; inspected bundles contain
    29 successful verification commands, 15 matching artifact digests and 20 executed stage
    attempts, with no repairs. Current-format/mutation tests passed 197 cases; actual workflow/UI
    rejection tests passed 7; terminal reconciliation passed 17 with identity-refusal evidence
    preserved. Full validator/provider/eval groups passed 656, core/task/stage groups passed
    376, and integrated workflow/inspection/UI tests passed 183. Instruction references, all
    25 packaged JavaScript assets, 140 Node tests, Ruff and strict mypy (227 files) passed.
  - Final audit: all changed source/test files received independent full-diff review. No
    unresolved confirmed code/document/link residue remains; 121 local links and 23 concrete
    test selectors resolve. All surviving CSS declarations keep their values and consumers.
    The eight unrelated accepted tasks remain open, with `W46-E1-S2-T4` restored to Next.
  - Integration gate: the third PR must pass the complete required CI matrix, packaged browser
    journeys, scenarios, conformance, security and package build before normal merge. Verify
    the resulting main tree against the reviewed and tested head; retain final CI/merge evidence
    with the PR. Local probe failures under host load are not substituted for a passing CI run.
