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

- `W36-E7-S4-T9` (done) Preserve the task-local repository baseline across implementation repairs.
  - Dependencies: `W36-E7-S4-T8` and the existing task-attempt lifecycle contract.
  - Output: retries and resumes of one rich implementation task compare repository evidence with
    that task's first-attempt baseline, so partial edits from a failed attempt remain observable
    without folding in successful prerequisite-task changes.
  - Scope: `src/aidd/core/task_attempt_lifecycle.py`, task repository evidence tests, and the
    implementation/task-attempt contracts and prompts; no UI-owned paths, provider adapters, or
    live target repositories.
  - Verification: a partial first task attempt followed by a repair reports the original changed
    path and succeeds when the final report matches it; malformed retained baseline evidence fails
    closed; focused lifecycle/evidence, validator, prompt-quality, and planning checks pass.
  - Completion evidence: retained first-attempt baselines now survive task repairs/resumes and fail
    closed when corrupt or missing. Focused lifecycle/evidence tests, full `make check` (3,292
    Python tests plus JS/type/instruction lanes), and commit `617b31c9` passed; no UI-owned paths
    changed.

- `W36-E7-S4-T10` (done) Make QA upstream-verdict validation honor review finding dispositions.
  - Dependencies: `W36-E7-S4-T9` and the existing QA cross-document contract.
  - Output: QA blocks only rejected reviews or review findings whose parsed disposition is
    `must-fix`; explanatory mentions of `must-fix` inside approved `follow-up` findings do not
    produce a false critical blocker.
  - Scope: `src/aidd/validators/cross_document_rules/qa_upstream.py`, validator regression tests,
    and the owning QA validation contract/prompt references if required; no UI, provider adapter,
    or live target repository changes.
  - Verification: an approved review with a `follow-up` finding that explains it is not must-fix
    passes QA upstream validation; a rejected review or actual `must-fix` disposition still
    requires `not-ready`/`hold`; focused cross-document, semantic, prompt, contract, and planning
    checks pass.
  - Completion evidence: `extract_review_disposition` now drives unresolved-finding detection,
    preventing explanatory `not must-fix` wording in approved follow-ups from becoming a blocker;
    focused validator/prompt/contract/docs/planning checks (282 tests) and full `make check`
    (3,293 Python tests plus JS/type/instruction lanes) passed in commit `68f7a9fe`.

- `W36-E7-S4-T4` (done) Run `AIDD-LIVE-007` through Claude Code from an independent root on
  the same AIDD revision and target pin.
  - Dependencies: `W36-E7-S4-T10` as the direct queue predecessor; `W36-E7-S4-T7` and
    `W36-E7-S4-T3` remain the provider-setup predecessors.
  - Scope: external Claude Code live execution and evidence only.
  - Verification: the Claude bundle meets the Codex evidence bar without reusing target state,
    answers, attempts, patches, or provider evidence.
  - 2026-09-09 attempt `eval-live-007-claude-code-20260909T071417Z` reached `implement` but
    failed canonical task-diff validation after TL-1/TL-2/TL-3 implementation evidence; this
    historical failure was superseded by the fresh run below. See
    `docs/e2e/aidd-live-007-claude-2026-09-09.md`.
  - Completion evidence: fresh independent-root run `eval-live-007-claude-code-20260914T112909Z`
    passed all stages and verify/finish with macOS Seatbelt isolation, source pre/postflight
    integrity, and `deepseek-flash` provider auth probe passing. Eight manual stage-quality audits,
    review approval, QA `ready-with-risks`/`proceed-with-conditions`, and final manual reports are
    retained in `/tmp/aidd-live-acceptance-20260914-r5`; no UI-owned paths were changed.

- `W36-E7-S4-T8` (done) Harden aggregate implementation evidence rendering for wrapped touched-file
  entries.
  - Dependencies: `W36-E7-S4-T7` and the existing implementation-finalization contract.
  - Output: aggregate finalization publishes only canonical touched-file paths from task evidence;
    wrapped or nested Markdown bullets cannot be promoted to phantom paths, while verification-only
    tasks continue to publish `- none`.
  - Scope: `src/aidd/core/implementation_finalization.py` and focused core finalization tests;
    no UI-owned paths, provider adapters, or live target repositories.
  - Verification: a multiline/continuation-bullet fixture produces only the observed file paths,
    the aggregate implementation report passes semantic validation, and focused finalization plus
    semantic implementation tests remain green.
  - Completion evidence: aggregate finalization now filters rich task reports against
    `task-diff.json` paths and retains a legacy canonical-bullet fallback. The regression and
    neighboring core/application/validator checks passed (1549 tests), with Ruff and strict mypy
    clean; no UI-owned paths or provider adapters changed.

- `W36-E7-S4-T5` (parked) Record a final same-revision Codex and Claude acceptance pass after
  observed-session reconciliation.
  - Dependencies: `W36-E7-S4-T4`, `W36-E7-S3-T3` as direct queue predecessors.
  - Scope: sanitized live acceptance evidence and Wave 36 closure only.
  - Verification: both fresh bundles name the same clean AIDD SHA, scenario and target revision,
    pass terminal quality gates, and match an anonymized digest-backed tracked summary.

- `W36-E7-S4-T6` (done) Preserve explicit Claude provider configuration in isolated live runs.
  - Dependencies: `W36-E7-S4-T3`; the task addresses the observed isolated auth blocker before
    `W36-E7-S4-T4` is resumed.
  - Output: provider-private launches retain non-secret `ANTHROPIC_BASE_URL` and
    `ANTHROPIC_MODEL` configuration while credentials remain explicitly allowlisted and seeded.
  - Scope: live acceptance isolation environment policy, deterministic isolation regression tests,
    and the prod-like provider acceptance runbook; no UI-owned paths.
  - Verification: a seeded Claude auth file plus `--credential-environment-key
    ANTHROPIC_AUTH_TOKEN` passes the isolated probe and session guard, the Kimi model/endpoint
    values survive into the private environment, and unrelated or sibling credentials remain
    excluded.
  - Completion evidence: PR #644 merged to `origin/main` at `3df6a34e`; isolated provider
    launches preserve non-secret `ANTHROPIC_BASE_URL`/`ANTHROPIC_MODEL` while credentials remain
    explicit and seeded. Focused isolation/planning/docs tests (90), instruction checks, full
    `make check` (3,283 tests), and the clean Seatbelt smoke probe passed. No UI-owned paths
    changed; the neighboring checkout remains read-only at `4c1356bc`.

- `W36-E7-S4-T7` (done) Preserve Claude Code's private temporary directory in isolated adapter
  launches.
  - Dependencies: `W36-E7-S4-T3`; this is a blocker discovered while resuming `W36-E7-S4-T4`.
  - Output: the Claude Code adapter maps the isolation-provided private `TMPDIR` to
    `CLAUDE_CODE_TMPDIR` without changing ordinary non-isolated launches.
  - Scope: Claude Code adapter environment construction, provider-free regression tests, and
    the prod-like acceptance runbook; no UI-owned paths.
  - Verification: an isolated Claude print launch can create its runtime temp state inside the
    provider subtree; the mapping is absent for ordinary launches and cannot be overridden by an
    outside path when the isolation marker is active.
  - Completion evidence: PR #647 merged to `origin/main` at `c472cf4e`; the adapter maps the
    private `TMPDIR` to `CLAUDE_CODE_TMPDIR` only for isolated launches and rejects outside
    overrides. Focused adapter/conformance/planning/docs tests (138), instruction checks (45),
    Ruff, mypy, full CI including Python 3.12–3.14, coverage, deterministic scenarios,
    packaged-browser, build, and security lanes passed. A direct Seatbelt Kimi Claude print
    smoke exited `0` with the private temp mapping. No UI-owned paths changed; the neighboring
    checkout remains read-only at `4c1356bc`.

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

### Epic W49-E2 — behavior-preserving hotspot reduction (`done`)

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

#### Slice W49-E2-S2 — post-Focus-Canvas service-boundary stabilization (`done`)

Primary output: server-side UI orchestration is decomposed without revisiting W47 presentation or
changing its public behavior.

- `W49-E2-S2-T1` (done) Extract UI job registry/lifecycle from `cli/ui.py`.
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
  - Completion evidence: PR #603 merged to `origin/main` at `058331b3`; job state, bounded log
    retention, cancellation, terminal evidence, and project/workspace projections now have one
    focused owner in `aidd.cli.ui_jobs`, while `ui.py` retains compatible imports and routing.
    Two-project isolation/ownership checks and the full CLI suite (341 tests) passed, along with
    Ruff, strict mypy, and all required CI/security lanes. No static UI, frontend tests, or
    neighboring UI checkout files changed.

- `W49-E2-S2-T2` (done) Compose existing HTTP codecs/router behind a CLI transport boundary.
  - Pre-implementation reconciliation: the JSON body/response codecs already have a focused owner
    in `aidd.cli.ui_http`, and generic route dispatch is owned by `aidd.cli.ui_routing` (W21).
    The remaining slice is therefore resliced to compose those owners behind one transport boundary
    and add endpoint contract fixtures; no duplicate codec or router implementation is permitted.
  - Output: service/controller composition and handler construction move behind a focused CLI
    transport module while preserving the existing `ui_http` codecs, stable routes, and status/body
    shapes.
  - Scope: server-side CLI transport and contract tests; no `src/aidd/cli/static/**`,
    `tests/frontend/**`, UI browser journeys, or neighboring UI checkout edits.
  - Verification: endpoint contract fixtures preserve success, validation, not-found, and
    explicit-failure response shapes across project contexts.
  - Dependencies: W49-E2-S2-T1, the merged W47 UI baseline, and a fresh `origin/main`.
  - Completion evidence: PR #605 merged to `origin/main` at `0c5af159`; `aidd.cli.ui_transport`
    composes the existing `ui_http` codecs and `ui_routing` dispatch without duplicate logic.
    Endpoint contracts cover success, validation, not-found, explicit failure, and two project
    contexts; focused/full CLI suites (10 and 345 tests), planning/traceability/CI tests (52),
    Ruff, strict mypy, and required CI/security lanes passed. No static UI, frontend tests, or
    neighboring UI checkout files changed.

- `W49-E2-S2-T3` (done) Replace dashboard `_next_action` branching with ordered typed rules.
  - Output: dashboard next-action selection is evaluated through a typed context and a fixed
    priority-ordered rule set, returning exactly one deterministic action without changing the
    `OperatorNextAction` payload contract.
  - Scope: core dashboard evidence and state-matrix tests; no `src/aidd/cli/static/**`,
    `tests/frontend/**`, UI browser journeys, or neighboring UI checkout edits.
  - Verification: full state matrix covers runtime selection, stale/blocked/question/recovery,
    review/QA/terminal evidence, runnable, and no-runnable states; repeated evaluation is stable.
  - Dependencies: W49-E2-S2-T2, the merged W47 UI baseline, and a fresh `origin/main`.
  - Completion evidence: PR #606 merged to `origin/main` at `2e4c42b3`; ordered typed rules now
    own the dashboard next-action priority while the `OperatorNextAction` payload and compatibility
    wrappers remain unchanged. The state matrix covers runtime selection, stale/blocked/questions,
    validation/intervention, review/QA/terminal evidence, runnable, and no-runnable states, with
    repeated-evaluation stability checks. Focused/core/inbox checks (88), the full core suite
    (1106), Ruff, strict mypy, and required CI/security lanes passed; the packaged-browser lane
    needed two transient UI-owned reruns before passing. No static UI, frontend tests, or
    neighboring UI checkout files changed.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S2-T1` | Extract UI job registry/lifecycle from `cli/ui.py`. | CLI application service | Two-project job lifecycle tests preserve isolation. | 1.5d |
| `W49-E2-S2-T2` | Compose existing HTTP codecs/router behind a CLI transport boundary and add endpoint contracts. | CLI transport | Endpoint contract suite preserves status/body shapes. | 2d |
| `W49-E2-S2-T3` | Replace dashboard `_next_action` branching with ordered typed rules. | Core dashboard evidence | Full state matrix yields exactly one deterministic action. | 1d |

Dependencies: merged W47 UI PR and a green post-merge CLI/frontend/browser compatibility baseline.
Before promoting each task, compare it with the final W47 diff. If W47 already produces the
output, record that evidence and reslice only the remaining hotspot; do not repeat the refactor.

#### Slice W49-E2-S3 — complexity-tail ratchet (`done`)

- `W49-E2-S3-T1` (done) Add a reviewed complexity baseline and no-new-E/F ratchet.
  - Output: the repository records a reviewed baseline for existing high-complexity functions and
    a deterministic check that fails when a new E/F-complexity block is introduced.
  - Scope: quality tooling, baseline data, and focused tests only; no runtime or UI-owned paths.
  - Verification: current baseline passes; a synthetic new E/F block fails with an actionable
    message; existing complexity debt remains explicitly enumerated for follow-up slices.
  - Dependencies: W49-E2-S2-T3, a fresh `origin/main`, and the merged W47 UI baseline.
  - Completion evidence: PR #608 merged to `origin/main` at `cb37d4eb`; Radon 6.0.1 now records
    the reviewed E/F production-source baseline, while `scripts/check_complexity.py` fails for
    new E/F blocks, complexity increases, malformed baseline data, or stale entries. The check
    is exposed through `make check-complexity` and the CI lint lane; repository and synthetic
    regression tests passed, together with the full 3212-test Python suite, 141 Node DOM tests,
    Ruff, strict mypy, all deterministic/conformance/browser/build lanes, and security checks.
    No runtime or UI-owned files changed.

- `W49-E2-S3-T2` (done) Decompose `build_task_flow_checkpoint`.
  - Output: task-flow checkpoint assembly is split by responsibility while preserving byte-level
    checkpoint fixtures, failure evidence, and the existing public facade.
  - Scope: `src/aidd/harness/task_flow_checkpoint.py` and its focused tests only; no runtime or
    UI-owned paths, no neighboring UI checkout edits.
  - Verification: characterization fixtures remain byte-equivalent and the complexity baseline
    moves the extracted production blocks to grade C or lower without hiding unrelated E/F debt.
  - Dependencies: W49-E2-S3-T1, a fresh `origin/main`, and the merged W47 UI baseline.
  - Completion evidence: PR #610 merged to `origin/main` at `cfcfe33c`; the public checkpoint
    facade now delegates to typed path/state helpers and responsibility-specific finding and
    payload builders. The focused checkpoint suite (9 tests), full harness suite (479 tests),
    Ruff, strict mypy, complexity ratchet, and all required CI/security/browser/build lanes passed.
    The facade is complexity grade A and extracted production blocks are grade C or lower; the
    existing Markdown/JSON fixtures and finding order remain byte-equivalent. No runtime, static
    UI, frontend-test, or neighboring UI checkout files changed.

- `W49-E2-S3-T3` (done) Decompose `_validate_scenario_contract`.
  - Output: scenario-manifest validation is split by contract concern while preserving the
    current typed findings, fail-closed behavior, and public loader/report surfaces.
  - Scope: `src/aidd/harness/scenarios.py` and its focused validation tests only; no runtime,
    static UI, frontend-test, or neighboring UI checkout paths.
  - Verification: the invalid-manifest characterization matrix remains unchanged, every malformed
    contract still yields an actionable validation result, and the complexity baseline moves the
    extracted production blocks to grade C or lower without suppressing unrelated debt.
  - Dependencies: W49-E2-S3-T2, a fresh `origin/main`, the merged W47 UI baseline, and a read-only
    comparison with the neighboring UI refactor before implementation.
  - Completion evidence: PR #612 merged to `origin/main` at `91b088d9`; the contract validator
    now delegates baseline, live-runtime, task-metadata, flow, and deterministic checks to
    responsibility-specific helpers while preserving typed findings and fail-closed loading.
    The focused invalid-manifest suite (50 tests), full harness suite (479 tests), Ruff, strict
    mypy, complexity ratchet, and all required CI/security/browser/build lanes passed. No runtime,
    static UI, frontend-test, or neighboring UI checkout files changed.

- `W49-E2-S3-T4` (done) Decompose `_run_single_stage_orchestration` after W48.
  - Output: core stage preparation, adapter execution, terminal handling, validation, and
    persistence are responsibility-specific helpers behind the unchanged orchestration facade.
  - Scope: `src/aidd/core/stage_runner.py` and existing core transition/failure/repair/interview
    tests only; preserve resume/intervention modes, repair budgets, timestamps, evidence indexes,
    and all public result/transition shapes. Do not touch runtime adapters, `src/aidd/cli/static/**`,
    `tests/frontend/**`, UI browser journeys, or the neighboring UI checkout.
  - Verification: the stage-runner/operator transition matrix remains unchanged, full core tests
    stay green, the extracted helpers are complexity grade C or lower, and the complexity baseline
    removes only the completed hotspot without hiding unrelated debt.
  - Dependencies: W49-E2-S3-T3, a fresh `origin/main`, the merged W47 UI baseline, and a read-only
    comparison with the neighboring UI refactor before implementation.
  - Completion evidence: PR #613 merged to `origin/main` at `d9d17bfa`; stage preparation, adapter
    execution, terminal handling, validation, and persistence now have focused helpers behind the
    unchanged facade. The full core suite (1106 tests), Ruff, strict mypy, complexity ratchet, and
    all required CI/security/browser/build lanes passed. No runtime, static UI, frontend-test, or
    neighboring UI checkout files changed.

- `W49-E2-S3-T5` (done) Decompose the Codex live transport.
  - Output: Codex live session startup, initialization, turn execution, and event polling are
    responsibility-specific helpers while raw transcript, approvals, cancellation, timeout, and
    protocol-failure evidence remain unchanged.
  - Scope: `src/aidd/adapters/codex/live.py` and its focused adapter tests only; preserve typed
    selector payloads, operator broker semantics, process ownership, and all public result shapes.
    Do not touch workflow semantics, static UI, frontend tests, or the neighboring UI checkout.
  - Verification: the Codex bytes/events/timeout/cancel and approval matrix remains green, adapter
    tests stay green, all extracted helpers are complexity grade C or lower, and only the completed
    Codex hotspot is removed from the complexity baseline.
  - Dependencies: W49-E2-S3-T4, a fresh `origin/main`, the merged W47 UI baseline, and a read-only
    comparison with the neighboring UI refactor before implementation.
  - Completion evidence: PR #615 merged to `origin/main` at `037a35ef`; 25 focused Codex live tests
    and 318 adapter tests passed, as did Ruff, strict mypy, complexity ratchet, and all required
    CI/security/browser/build lanes. No UI-owned files changed.

- `W49-E2-S3-T6` (done) Decompose the Qwen live transport.
  - Output: Qwen live transport lifecycle responsibilities are split without changing its public
    result, raw evidence, approval, timeout, cancellation, or process-ownership contracts.
  - Scope: `src/aidd/adapters/qwen/live.py` and focused adapter tests only; no workflow, static UI,
    frontend-test, or neighboring UI checkout edits.
  - Verification: Qwen bytes/events/timeout/cancel and approval fixtures remain green, extracted
    helpers are complexity grade C or lower, and the baseline removes only the completed hotspot.
  - Dependencies: W49-E2-S3-T5, a fresh `origin/main`, the merged W47 UI baseline, and a read-only
    comparison with the neighboring UI refactor before implementation.
  - Completion evidence: PR #617 merged to `origin/main` at `18a71f2e`; Qwen live session startup,
    polling, finalization, and result mapping now have responsibility-specific helpers while the
    public result, raw evidence, approval, timeout, cancellation, and process-ownership contracts
    remain unchanged. The focused Qwen suite (18 tests), full adapter suite (318 tests), Ruff,
    strict mypy, complexity ratchet, and all required CI/security/browser/build lanes passed. The
    Qwen hotspot moved from F(42) to a C-or-lower helper set and only its baseline entry was
    removed. No UI-owned files changed; the neighboring UI checkout remained read-only.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S3-T1` | Add a reviewed complexity baseline and no-new-E/F ratchet. | Quality tooling | Synthetic new E/F block fails the check. | 1d |
| `W49-E2-S3-T2` | Decompose `build_task_flow_checkpoint`. | Task checkpoint | Complexity is C or lower and checkpoint fixtures are byte-equivalent. | 2d |
| `W49-E2-S3-T3` | Decompose `_validate_scenario_contract`. | Scenario validation | Complexity is C or lower and invalid-manifest matrix is unchanged. | 1.5d |
| `W49-E2-S3-T4` | Decompose `run_single_stage_orchestration` after W48. | Core stage lifecycle | Transition matrix remains green and complexity is C or lower. | 2d |
| `W49-E2-S3-T5` | Decompose the Codex live transport. | Codex adapter | Codex adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |
| `W49-E2-S3-T6` | Decompose the Qwen live transport. | Qwen adapter | Qwen adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |

Dependencies: T1 first; every remaining task is independent and behavior-preserving. All six
tasks are now complete, so this slice rolls up to `done`.

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

### Epic W49-E4 — assurance ratchets (`done`)

#### Slice W49-E4-S1 — formatter baseline (`done`)

- `W49-E4-S1-T1` (done) Decide formatter scope/exclusions and apply one isolated mechanical
  baseline.
  - Output: the repository has an explicit formatter scope and one isolated mechanical baseline
    with no semantic AST change.
  - Scope: Python formatting configuration and source files selected by the reviewed scope; no
    runtime behavior, UI-owned files, frontend tests, or neighboring UI checkout edits.
  - Verification: Ruff format check, Ruff lint, strict mypy, focused owning tests, and an AST
    equivalence check pass; the diff contains formatting-only changes.
  - Dependencies: W49-E2-S3-T6, a fresh `origin/main`, and the merged W47 UI baseline. Run after
    hotspot refactors so the baseline does not create permanent merge conflicts.
  - Completion evidence: PR #619 merged to `origin/main` at `d8b0f379`; Ruff formatted 268
    tracked Python files under the reviewed non-UI scope and excludes `browser_tests` to preserve
    the neighboring UI boundary. AST equivalence, `ruff format --check .`, Ruff lint, strict
    mypy, complexity, 73 focused docs/planning/CI tests, and all required CI/security/browser/build
    checks passed. The full local suite reached 2106 passed before a manual stop due runtime;
    CI executed the complete Python suite. No `src/aidd/cli/static/**`, `tests/frontend/**`, or
    neighboring UI checkout files changed.

- `W49-E4-S1-T2` (done) Add `ruff format --check .` to CI.
  - Output: CI rejects intentional Python formatting drift through a required deterministic check.
  - Scope: CI workflow and focused check fixtures only; no runtime or UI-owned paths.
  - Verification: a synthetic formatting drift fails the check and the clean tree passes.
  - Dependencies: `W49-E4-S1-T1`.
  - Completion evidence: PR #622 merged to `origin/main` at `765f051a`; the lint/type/test
    matrix runs `uv run --extra dev ruff format --check .` as a required step, with the workflow
    contract covered by a focused test. The clean formatter check, 74 focused planning/docs/CI
    tests, all Python matrix lanes, deterministic/conformance/browser/build lanes, and security
    checks passed. No runtime or UI-owned paths changed.

#### Slice W49-E4-S2 — critical-module coverage (`done`)

- `W49-E4-S2-T1` (done) Record line/branch coverage for lifecycle, evidence, adapters, and
  scenario gates.
  - Output: a reviewed coverage baseline is tied to the exact SHA and command for critical
    modules without imposing a vanity global percentage.
  - Scope: coverage tooling, baseline data, and focused tests; no UI-owned paths.
  - Verification: the baseline records module identity, command, and revision and is reproducible
    from a clean checkout.
  - Dependencies: `W49-E4-S1` and a fresh `origin/main`.
  - Completion evidence: PR #624 merged to `origin/main` at `a144fbae`; the baseline records
    23 critical modules across the four categories, line/branch counts, source revision
    `951e3f8c`, Python/Coverage versions, and the exact 369-test pytest command. The checker and
    focused regression tests pass, as do all Python, adapter, deterministic, browser, build, and
    security lanes. No UI-owned paths changed.

- `W49-E4-S2-T2` (done) Add non-decreasing per-module thresholds in one CI job.
  - Output: critical-module coverage cannot regress below its reviewed baseline in CI.
  - Scope: CI coverage gate and regression fixtures; no runtime or UI-owned paths.
  - Verification: a synthetic critical-module regression fails while unrelated global coverage
    changes do not block the gate.
  - Dependencies: `W49-E4-S2-T1`.
  - Completion evidence: PR #626 merged to `origin/main` at `63fa1d7e`; the required CI job runs
    the exact 369-test line/branch command and fails closed on any reviewed-module regression,
    while unlisted modules remain outside the gate. A Linux-specific process-group coverage
    difference was identified on the first CI run and corrected by recording the CI-native metric
    and pinning the baseline interpreter to Python 3.13.7. The workflow contract, checker
    regression, full Python matrix, adapter, deterministic, packaged-browser, build, and security
    lanes passed. No runtime or UI-owned paths changed.

#### Slice W49-E4-S3 — browser JavaScript security analysis (`done`)

- `W49-E4-S3-T1` (done) Add JavaScript/TypeScript CodeQL analysis for packaged frontend source.
  - Output: the security workflow uploads both Python and packaged-frontend analysis results.
  - Scope: security workflow configuration only; do not edit `src/aidd/cli/static/**`,
    `tests/frontend/**`, UI browser tests, or the neighboring UI checkout.
  - Verification: the workflow configuration validates both language analyses and existing
    Python CodeQL results remain available.
  - Dependencies: W47 Focus Canvas merge, a fresh `origin/main`, and a read-only comparison with
    the neighboring UI refactor.
  - Completion evidence: PR #627 merged to `origin/main` at `c165eb5d`; the pinned CodeQL
    initialization now analyzes both `python` and `javascript-typescript`, with the existing
    analyze/upload flow retained. The security workflow, Python 3.12–3.14 matrix, deterministic,
    adapter, critical-coverage, packaged-browser, and build lanes passed. No static UI,
    frontend-test, browser-test, or neighboring UI checkout files changed.

Dependencies: `W49-E4-S1-T1` → `W49-E4-S1-T2`; `W49-E4-S1` → `W49-E4-S2-T1` →
`W49-E4-S2-T2`; the browser security task is independent after the W47 merge.

## Wave 50 — current and retrievable beta acceptance (`planned`)

Goal: produce one exact-candidate decision whose deterministic, browser, install, provider, and
human evidence is current, immutable, and retrievable.

### Epic W50-E1 — evidence freshness and retention (`done`)

#### Slice W50-E1-S1 — freshness model (`done`)

- `W50-E1-S1-T1` (done) Define `current/stale/incompatible/unavailable` from candidate SHA,
  schema, target pin, and evidence locator.
  - Output: one typed freshness contract with deterministic precedence and actionable reasons.
  - Scope: evidence freshness contract and focused deterministic tests; no UI-owned paths.
  - Verification: an historical bundle on another candidate SHA is `stale`, incompatible schema
    or target metadata is `incompatible`, missing evidence is `unavailable`, and an exact matching
    bundle is `current`.
  - Dependencies: W48 exit gate, W49 assurance ratchets, and a fresh `origin/main`.
  - Completion evidence: PR #629 merged to `origin/main` at `71c3779a`; the core-only typed
    classifier and 16 deterministic state/validation tests passed with strict mypy, Ruff, and
    the full required CI/security/browser/build lanes. No UI-owned paths changed.

- `W50-E1-S1-T2` (done) Project freshness consistently into reports and the operator read model.
  - Output: service/report projections preserve freshness state and reason without changing
    verdict history.
  - Scope: evidence read model and tests; any UI projection must preserve the merged W47 Focus
    Canvas hierarchy and remain separate from the neighboring UI checkout.
  - Verification: service and presentation fixtures expose the same state/reason matrix.
  - Dependencies: `W50-E1-S1-T1` and the merged W47 UI baseline.
  - Completion evidence: PR #631 merged to `origin/main` at `6cac4a82`; verdict reports,
    grader payloads, harness metadata, operator run summaries, dashboard views, and terminal
    handoffs now project the shared state/reason matrix while preserving verdict history and
    terminal recommendation safety. Focused (135 tests), full `make check`, security,
    packaged-browser, and build lanes passed. No static UI, frontend-test, browser-test, or
    neighboring UI checkout files changed; the neighboring checkout remains read-only at
    `4c1356bc`.

#### Slice W50-E1-S2 — immutable sanitized bundle export (`done`)

- `W50-E1-S2-T1` (done) Define retention locator, digest, size, revision, target pin, and
  redaction contract.
  - Output: one typed archive-retention contract that rejects locators without integrity and
    provenance metadata.
  - Scope: evidence archive contract and focused deterministic tests; no static UI, frontend,
    browser-test, or neighboring checkout paths.
  - Verification: valid metadata round-trips, while missing digest, size, revision, target pin,
    or redaction guarantees fail closed.
  - Dependencies: completed `W50-E1-S1` and W48 bundle v2.

- `W50-E1-S2-T2` (done) Export and read back a sanitized immutable archive.
  - Output: a portable evidence archive with verified digest, size, revision, target pin, and
    redaction metadata that can be read after the mutable workspace bundle is removed.
  - Scope: bundle exporter/verifier and deterministic archive round-trip tests; no static UI,
    frontend, browser-test, or neighboring checkout paths.
  - Verification: a fresh checkout verifies the archive after mutable `.aidd` deletion, while
    tampered bytes or incomplete provenance fail closed.
  - Dependencies: `W50-E1-S2-T1` and W48 bundle v2.
  - Completion evidence: PR #634 merged to `origin/main` at `7dab7e0d`; sealed W48 bundles
    export as deterministic sanitized POSIX tar archives with sibling retention sidecars,
    sanitized inventory/digest indexes, and verified read/extract after source `.aidd` deletion.
    Focused (114 tests), full CI, security, packaged-browser, and build lanes passed. No static
    UI, frontend-test, browser-test, or neighboring UI checkout files changed; that checkout
    remains read-only at `4c1356bc`.

### Epic W50-E2 — exact artifact candidate gate (`done`)

#### Slice W50-E2-S1 — freeze and local acceptance (`done`)

- `W50-E2-S1-T1` (done) Freeze candidate SHA, source tree, wheel digest, scenario inventory,
  and test commands.
  - Output: one complete candidate manifest bound to a clean worktree, source tree, wheel,
    scenario inventory, and reproducible verification commands.
  - Scope: candidate manifest and deterministic release-preflight tests; no static UI,
    frontend, browser-test, or neighboring checkout paths.
  - Verification: the record is complete, identity fields agree with the checked-out candidate,
    and a dirty worktree or missing digest blocks publication.
  - Dependencies: completed W50-E1 and W48 bundle v2.
  - Completion evidence: PR #636 merged to `origin/main` at `88ac8a1d`; the candidate manifest
    freezes clean-worktree Git SHA/tree, package version, wheel digest/size, CI scenario inventory,
    and reproducible verification commands, while fail-closed validation rejects drift and
    non-wheel artifacts. Focused candidate/release tests, full local `make check`, Python matrix,
    critical coverage, adapter conformance, deterministic scenarios, packaged-browser, build,
    CodeQL, Scorecard, and dependency-review lanes passed. No UI-owned paths changed; the
    neighboring checkout remains read-only at `4c1356bc`.

- `W50-E2-S1-T2` (done) Run full static/unit/integration/browser/security/build gates on the
  frozen candidate.
  - Output: one signed/hashed readiness record linking every required result for the exact
    candidate SHA.
  - Scope: candidate acceptance coordinator and release evidence; no UI implementation changes.
  - Verification: a failed or mismatched lane cannot render the candidate ready.
  - Dependencies: `W50-E2-S1-T1` and the merged W47 Focus Canvas baseline.
  - Completion evidence: PR #638 merged to `origin/main` at `1abd1291`; the hashed readiness
    contract binds all Python matrix, critical-coverage, adapter, deterministic, packaged-browser,
    build, CodeQL, dependency-review, and Scorecard results to the candidate manifest digest and
    source tree, rejecting missing, duplicate, failed, mismatched, non-HTTPS, or tampered evidence.
    Focused/full local checks and all required CI/security/browser/build lanes passed. No UI-owned
    paths changed; the neighboring checkout remains read-only at `4c1356bc`.

- `W50-E2-S1-T3` (done) Run the installed deterministic happy/failure/repair/interview/task/
  project-set/bundle matrix.
  - Output: exact wheel passes every typed assertion with self-contained bundles.
  - Scope: installed candidate evaluation and deterministic evidence; no UI implementation changes.
  - Verification: every declared scenario runs against the frozen wheel and retains provenance,
    terminal, repair, intervention, project-set, and bundle-integrity assertions.
  - Dependencies: `W50-E2-S1-T2` and W48 bundle v2.
  - Completion evidence: PR #640 merged to `origin/main` at `add04c05`; the runner installs the
    exact manifest-bound wheel in an isolated environment, executes every CI-marked deterministic
    scenario through the installed `aidd` CLI, preserves stdout/stderr digests and bundle paths,
    and emits a hashed fail-closed matrix. Focused tests (4), full Python matrix, critical
    coverage, adapter conformance, deterministic scenarios, packaged-browser, build, CodeQL,
    Scorecard, and dependency-review lanes passed. A review regression fixed manifest-relative
    scenario paths before merge. No UI-owned paths changed; the neighboring checkout remains
    read-only at `4c1356bc`.

- `W50-E2-S1-T4` (done) Verify `pipx` and `uv tool` clean install and upgrade for the exact wheel.
  - Output: installed package version and wheel digest match the candidate manifest.
  - Scope: isolated package-channel verification; no UI implementation changes.
  - Verification: runner-owned `pipx` and `uv tool` environments execute the installed `aidd`
    binary and `doctor`, with a mismatched or unavailable artifact blocked.
  - Dependencies: `W50-E2-S1-T3` and the exact candidate wheel.
  - Completion evidence: PR #642 merged to `origin/main` at `c9127799`; the read-only runner
    performs clean install and exact-wheel replacement through both `pipx` and `uv tool` in
    temporary runner-owned directories, executes the installed `aidd --version` and `doctor`,
    verifies the PEP 610 `direct_url.json` wheel hash, and writes a canonical fail-closed report.
    Focused release/docs/planning tests (98), full Python matrix, critical coverage, adapter
    conformance, deterministic scenarios, packaged-browser (successful rerun after one unrelated
    UI-baseline HTTP-400 flake), build, CodeQL, Scorecard, and dependency-review lanes passed.
    No UI-owned paths changed; the neighboring checkout remains read-only at `4c1356bc`.

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

## Wave 53 — operator recovery and evidence navigation (`done`)

This wave is accepted from the operator report for IUIT-1527: implementation recovery must
launch the canonical task mutation, Runner controls must be visible at the recovery decision,
and retained documents must remain readable while technical evidence stays available on demand.

### Epic W53-E1 — recoverable implementation runs (`done`)

#### Slice W53-E1-S1 — task-scoped recovery controls (`done`)

- `W53-E1-S1-T1` (done) Make implementation recovery launch the canonical eligible task or
  finalization target and expose the selected Runner controls at that decision.
  - Output: failed or blocked implementation recovery targets `/api/tasks/run` for the eligible
    task, finalization recovery targets `/api/tasks/finalize`, and Runner model/reasoning settings
    plus readiness evidence are available without leaving the recovery surface.
  - Scope: operator quality-gate/shell/action assets and their frontend/browser checks; preserve
    core task eligibility, run leases, provenance, and existing stage routes.
  - Verification: deterministic frontend and browser evidence proves the failed-task action
    creates a task attempt request rather than a no-op aggregate stage run; unsupported Runner
    selectors remain disabled with an explicit reason; desktop and compact recovery surfaces
    expose one actionable recovery target.
  - Local evidence: `node --test tests/frontend/operator-implementation-recovery.test.mjs` -> 3
    passed; `make test-frontend` -> 146 passed; `make test-browser` -> 5 passed.

#### Slice W53-E1-S2 — evidence workspace hierarchy (`done`)

- `W53-E1-S2-T1` (done) Reduce document-reader density and make Work Item navigation task-oriented.
  - Output: the primary document reader, supporting evidence, and Work Item context are visually
    distinct; technical detail stays collapsible; tabs retain stable context and do not overlap or
    force the operator to reconstruct the current location.
  - Scope: packaged operator document/navigation assets, CSS, and rendered frontend/browser checks;
    preserve artifact ownership, bounded reads, source/compare modes, keyboard access, and routes.
  - Verification: rendered desktop and 390px evidence shows no overlap or horizontal clipping, one
    primary reader/action hierarchy, readable document headings, and keyboard-reachable navigation.
  - Local evidence: `uv run --extra dev pytest -q browser_tests/test_w44_documents_attempt_layout.py` -> 7
    passed; `uv run --extra dev pytest -q browser_tests/test_journey_review_qa.py` -> 4 passed; `make
    test-browser` -> 5 passed.

## Wave 54 — operator evidence truth hardening (`done`)

This wave is accepted from the follow-up audit of the IUIT-1527 operator report and targets
the remaining fail-open verification projections discovered after W53: incomplete evidence
payloads and outcome-only claims must never appear as verified work.

### Epic W54-E1 — fail-closed implementation evidence (`done`)

#### Slice W54-E1-S1 — canonical verification truth (`done`)

- `W54-E1-S1-T1` (done) Make implementation evidence fail closed across parsing and Operator UI.
  - Output: missing verification status/results, legacy command-only payloads, and outcome-only
    claims remain explicitly unverifiable; Review stays blocked until every recorded check has
    same-item executable command evidence and an observed passing result.
  - Scope: `src/aidd/core/operator_reports.py`, the shared implementation-evidence helpers and
    semantic/cross-document/harness projections in `src/aidd/validators/` and `src/aidd/harness/`,
    implementation and intervention mutation selector propagation in `src/aidd/cli/ui.py`,
    `src/aidd/cli/stage_run.py`, and `src/aidd/cli/task.py`, packaged implementation-review
    assets, and their focused
    core/validator/CLI/frontend/browser regression tests; preserve the Markdown report contract,
    canonical task routes, and validator ownership.
  - Verification: focused parser, shared-helper, validator, harness, mutation propagation, and
    UI tests plus the implementation review browser journey prove legacy, malformed, mixed,
    failed, not-run, and fully verified evidence states render and gate truthfully without
    treating result words inside executable command arguments as observed outcomes, and prove
    model/reasoning overrides reach every implementation mutation route.
  - Completion evidence: the parser keeps outcome-only claims explicitly unverifiable, the
    Operator UI no longer upgrades legacy/malformed payloads to pass, canonical recovery and
    Inbox actions dispatch to their owned routes or visibly disable ineligible mutations, and
    run-scoped selections plus model/reasoning overrides are cleared/propagated at the correct
    boundaries. `uv run --extra dev pytest -q tests/cli/test_ui.py tests/cli/test_stage_run.py
    tests/cli/test_ui_assets_contracts.py tests/test_planning_integrity.py` -> 252 passed;
    `make test-frontend` -> 149 passed; the focused browser journeys -> 31 passed and the
    post-patch `uv run --extra dev pytest -q browser_tests/test_journey_inbox.py` smoke -> 9
    passed;
  `make check-js` -> checked 25 packaged JavaScript assets; scoped Ruff and
  `git diff --check` -> pass. The broader pre-existing `make check` attempt remains limited
  by two adapter subprocess timing failures outside this wave's touched paths.

## Wave 55 — post-W54 residual operator integrity audit (`done`)

This wave is accepted from the next operator audit request: after the W53/W54 repairs,
inspect the remaining repository-wide action, state, rendered UI, and evidence projections
for confirmed defects of the same class and repair them with provider-free evidence.

### Epic W55-E1 — residual operator and evidence hardening (`done`)

#### Slice W55-E1-S1 — repository-wide confirmed-defect repair (`done`)

- `W55-E1-S1-T1` (done) Audit and repair all remaining confirmed operator, UI-state, and
  evidence-integrity defects of the W53/W54 class.
  - Output: every confirmed residual no-op or misrouted action, stale route/selection state,
    inaccessible Runner/model/reasoning/readiness control, rendered overlap/overflow or weak
    interaction state, and fail-open evidence projection in the audited scope has an owning-path
    fix and a regression check; no unsupported state is silently treated as success or ignored.
  - Scope: `src/aidd/core/`, `src/aidd/cli/`, packaged `src/aidd/cli/static/`,
    `src/aidd/validators/`, `src/aidd/harness/`, relevant contracts/docs, and nearest
    `tests/`, `tests/frontend/`, and `browser_tests/`; preserve runtime-agnostic core,
    canonical routes, evidence ownership, and validation gates.
  - Dependencies: W54-E1-S1-T1; existing W53/W54 UI and evidence baselines; no provider
    credentials required for discovery or regression verification.
  - Verification: targeted static ownership audit, core/CLI/validator/harness tests, packaged
    JS checks, frontend state/route tests, rendered desktop/mobile browser journeys, keyboard
    and disabled/error/loading-state checks, planning integrity, and the broadest feasible
    repository checks with exact external blockers recorded.
  - Completion evidence: the audit repaired late onboarding/dashboard/refresh responses that
    could overwrite newer context; stale task/recovery/question actions that could act on a
    different run or bypass current Runner readiness; and project/project-set validation results
    that could incorrectly approve edited inputs. Run changes now clear run-owned selections, and
    asynchronous readers/actions reject responses whose request generation or route identity is
    stale. `make test-frontend` -> 164 passed; `make check-js` -> checked 25 packaged JavaScript
    assets; `uv run --extra dev ruff check src/aidd/cli/stage_run.py src/aidd/cli/task.py
    src/aidd/cli/ui.py src/aidd/core/operator_reports.py
    src/aidd/harness/live_e2e_black_box_orchestration.py
    src/aidd/validators/cross_document_rules/qa_upstream.py
    src/aidd/validators/semantic_rules/common.py src/aidd/validators/semantic_rules/evidence.py
    src/aidd/validators/semantic_rules/implement.py tests/cli/test_ui.py
    tests/cli/test_ui_assets_contracts.py tests/core/test_operator_reports.py
    tests/harness/test_live_e2e_black_box.py tests/validators/test_implementation_evidence.py
    tests/validators/test_semantic_implement.py` -> all checks passed; `uv run --extra dev
    pytest -q tests/cli/test_stage_run.py tests/cli/test_task.py` -> 61 passed; `uv run --extra
    dev pytest -q tests/cli/test_ui_assets_contracts.py` -> 53 passed; `make test-frontend` ->
    164 passed; `uv run --extra dev pytest -q browser_tests/test_journey_guided_setup.py` -> 6
    passed; `uv run --extra dev pytest -q browser_tests/test_journey_document_evidence.py` -> 6
    passed, including all five responsive widths. The full `make test-browser` executed all 12
    registered journeys; its first run had one 1440px Document Canvas visibility timeout while
    concurrent CLI/Python suites were consuming the host. The exact 1440px case then passed
    alone (1 passed), and the full document journey passed alone (6 passed); the other 11
    journeys passed in the packaged run. A combined Python audit run reported 428 passed and two
    obsolete UI-asset source-text assertions; those assertions were corrected to encode factual
    cancellation wording and the current refresh-generation guard, and the complete asset
    contract module passed (53 passed); `uv run --extra dev pytest -q
    tests/test_docs_consistency.py tests/test_planning_integrity.py` -> 70 passed;
    `git diff --check` -> pass. The broader `make check` was not rerun in this wave; the
    previously recorded two adapter subprocess timing failures remain outside the audited paths.

## Wave 56 — product-claim and operator-surface parity audit (`done`)

This wave follows the 2026-09-24 request to find and repair functional gaps between current
product claims, the installed CLI, and the local Operator UI. It starts from the completed W55
operator-integrity baseline and records only reproduced defects against current user-visible
contracts; external provider execution is not required for this audit.

### Epic W56-E1 — reliable onboarding and task inspection (`done`)

Linked stories: `US-09`, `US-11`, `US-13`

#### Slice W56-E1-S1 — project-contained absolute workspace roots (`done`)

- `W56-E1-S1-T1` (done) Support absolute workspace roots during clean Guided Setup.
  - Output: `aidd ui --root <absolute-project>/.aidd` can validate the selected project and
    create or resume work while keeping `.aidd` inside that project; an absolute root outside
    the selected project remains an explicit error.
  - Scope: `src/aidd/core/onboarding.py`, `tests/core/test_onboarding.py`,
    `tests/cli/test_ui.py`, and the relevant operator handbook guidance; preserve symlink and
    project-boundary checks.
  - Dependencies: W55-E1-S1-T1 and the current Guided Setup onboarding contract.
  - Verification: focused onboarding and UI service evidence covers valid absolute, outside-root,
    and existing relative workspace paths; a rendered clean-setup journey confirms work-item
    creation without launching a runtime.
  - Completion evidence: the onboarding and UI regressions prove an absolute workspace inside the
    project can be inspected and created, while an outside-project root remains rejected. The
    local UI was launched from a clean temp project with an absolute `.aidd` path; Guided Setup
    validated it, created `WI-ABS-ROOT`, and opened Studio without selecting or invoking a runtime.
    The five-module focused suite passed (227 tests); Ruff and `git diff --check` passed.

#### Slice W56-E1-S2 — task-command prerequisite diagnostics (`done`)

- `W56-E1-S2-T1` (done) Report task-command preconditions without tracebacks.
  - Output: `aidd task list` and `aidd task show` return a concise actionable CLI error before a
    tasklist is published; expected domain failures from task execution/finalization also use the
    CLI error surface. Valid task inspection and fail-closed execution stay unchanged.
  - Scope: `src/aidd/cli/task.py` and `tests/cli/test_task.py`.
  - Dependencies: W55-E1-S1-T1; the tasklist remains the required source of task definitions.
  - Verification: focused CLI evidence covers missing and valid tasklists, nonzero failure status,
    absence of an uncaught traceback, and malformed-ledger rejection before runtime or state writes.
  - Completion evidence: `tests/cli/test_task.py` passed (12 tests); `aidd task list/show` on a
    newly initialized item now return exit code 2, explain that the `tasklist` stage must run
    first, and show no Python traceback. The full five-module focused suite passed (227 tests).

## Wave 57 — grounded requirements and owned verification (`planned`)

Goal: Ground original requirements and decisions in exact sources, execute registered checks
through AIDD, and distinguish current verification evidence from behavioral acceptance before
changing orchestration.

Accepted on 2026-10-01 from the [iterative delivery migration
plan](../analysis/iterative-delivery-migration-plan-2026-10-01.md). W57–W59 contain the 39 original
migration tasks plus the user-requested positioning/UX precursor W57-E1-S1-T3 (40 total);
this roadmap owns their definitions, dependencies, and statuses. The dated plan
retains design rationale, adversarial cases, and measurement proposals. Acceptance of this work
does not claim that migration behavior is already implemented.

The [accepted architecture contract](../architecture/iterative-delivery-contract.md) and
[ADR 009](../architecture/iterative-delivery-decisions.md#adr-009-direct-breaking-replacement)
supersede the proposal's coexistence/default-switch/retirement sequence: implement bounded
internal slices, then accept one complete breaking replacement without backward compatibility.

Linked stories: `US-02`, `US-03`, `US-04`, `US-05`, `US-07`, `US-10`, `US-11`, `US-13`.
The internal pilot establishes source authority and owned proof before changing orchestration;
it is not a publicly supported parallel engine. Each behavior task includes contract/prompt alignment and
its direct regression; the final scenario task integrates these results rather than
postponing their tests.

### Epic W57-E1 — source and decision authority (`planned`)

Goal: Establish protected source/criterion identity and scoped decision authority without
blanket approval of generated plans.

#### Slice W57-E1-S1 — define the target and comparison contract (`planned`)

Dependencies: No upstream local task for slice entry. Task-specific dependencies below govern
later work.

- `W57-E1-S1-T3` (done) Establish product positioning and the iterative Operator UX direction.
  - Output: durable product positioning, a target journey/screen/state/action blueprint,
    a bounded current-UI audit, and an inspectable concept with explicit fixture status.
  - Scope: product/architecture docs, README framing, and a separate design concept;
    no production UI, orchestration, or stage-contract implementation.
  - Dependencies: none; this user-requested design precursor informs the contracts below.
  - Verification: inspect current rendered UI and the concept, check documentation/planning
    consistency, and preserve current-versus-target claims. Human usability remains unverified.
  - Completion evidence: [product positioning](../product/product-positioning.md),
    [iterative UX blueprint](../architecture/iterative-operator-ux.md), and
    [current-UI audit/concept walkthrough](../design/iterative-operator/README.md) recorded
    on 2026-10-01. Current UI and concept screenshots inspected; decision/save/start/review,
    failure retention, stale proof, narrow layouts, and keyboard interactions checked.
    Documentation/planning suite: 70 passed; concept syntax and error-level console clean.
    Production UI/runtime and genuine human usability acceptance are not implemented or claimed.

- `W57-E1-S1-T1` (done) Define outcome, authority, routing, and iteration contracts.
  - Output: accepted architecture decisions, concrete record/lifecycle and ownership contract,
    story changes, and stage/route migration map, including direct breaking replacement policy.
  - Scope: product/architecture/compatibility docs, document ownership, traceability registry;
    no runtime implementation. Clarify `US-13` “approved tasklist” authority and `US-11` routes.
    Use the [positioning](../product/product-positioning.md) and
    [iterative UX blueprint](../architecture/iterative-operator-ux.md) as the product baseline.
  - Dependencies: `W57-E1-S1-T3`.
  - Verification: documentation/traceability consistency; review that material decisions,
    permissions, model reviews, and ordinary retries have distinct consequences.
  - Progress on 2026-10-01: [ADR 001](../architecture/iterative-delivery-decisions.md#adr-001-requirement-authority)
    accepted by the operator. Explicit source requirements have authority; additions,
    ambiguity, and conflicts require scoped decisions.
    [ADR 002](../architecture/iterative-delivery-decisions.md#adr-002-verification-execution)
    accepted by the operator: an AIDD verification service runs registered local checks
    through a provider-independent execution port and retains actual results and code identity.
    [ADR 003](../architecture/iterative-delivery-decisions.md#adr-003-criterion-acceptance)
    accepted by the operator: automatically assess criteria with independent expected behavior
    and current evidence, clarify ambiguity, and use scoped manual assessment when needed.
    Unassessed or inconclusive mandatory criteria prevent completion.
    [ADR 004](../architecture/iterative-delivery-decisions.md#adr-004-project-check-registry)
    accepted by the operator: register project checks and parameter bounds, select checks
    by declared policy, retain mandatory checks, and register new or changed execution
    definitions separately.
    [ADR 005](../architecture/iterative-delivery-decisions.md#adr-005-preparation-depth-and-routing)
    accepted by the operator: core policy selects focused/investigate/design from explicit
    evidence, exposes the rationale, and escalates uncertainty; required verification,
    review, and QA remain.
    [ADR 006](../architecture/iterative-delivery-decisions.md#adr-006-iteration-identity-and-history)
    accepted by the operator: revised plans create child runs of the same Work Item,
    preserve immutable predecessor history, and retain ordinary fixes/retries within a
    compatible unchanged run.
    [ADR 007](../architecture/iterative-delivery-decisions.md#adr-007-carry-forward-and-invalidation)
    accepted by the operator: re-execute affected tasks and dependents, carry compatible
    retained work with original attempt attribution, and refresh stale verification;
    required final checks apply to the current final tree.
    [ADR 008](../architecture/iterative-delivery-decisions.md#adr-008-bounded-automatic-control)
    accepted by the operator: automatically fix, verify, and replan within authorized bounds
    and shared finite objective limits; exhaustion, no progress, and unresolved authority
    stop or ask. Children do not reset budgets, and recovery cannot silently duplicate
    execution.
    [ADR 009](../architecture/iterative-delivery-decisions.md#adr-009-direct-breaking-replacement)
    accepted by the operator: one complete replacement release with no coexistence, legacy
    readers, automatic conversion or in-engine rollback. The
    [unified target contract](../architecture/iterative-delivery-contract.md) defines records,
    ownership, source/assessment limits, finite routes, input substitutions, lifecycle/budgets,
    recovery, story mapping and direct cutover.
  - Completion evidence on 2026-10-01: ADR 001–ADR 009 and the unified contract recorded;
    user stories/traceability, compatibility, product/UX direction and W57–W59 reconciled.
    Planning/document/traceability suite: 75 passed; `make check-agents`: 52 instruction
    documents checked and 45 tests passed; generated traceability and local links checked.
    Current runtime behavior, active stage contracts/prompts, native/human acceptance and
    publication are not implemented or claimed by this architecture task.

- `W57-E1-S1-T2` (next) Pin the baseline and predeclare migration acceptance.
  - Output: comparison protocol, fixed tasks/fixtures, independent expected behavior,
    failure taxonomy, comprehension questions, and predeclared migration acceptance thresholds.
  - Scope: eval/E2E protocols and baseline inventory. Pin the earlier package/revision and
    retained traces in a separate checkout/environment; record model/runtime/reasoning,
    prompts, commit, environment, bundle identity and intentional AIDD/prompt differences.
    Pin finite budget defaults, waiting-time accounting and no-progress thresholds before eval.
    Assess a bounded [SWE-bench fixture proposal](../analysis/swe-bench-migration-evaluation-2026-10-06.md)
    for independent code-correctness cases; qualify exact source/test/environment identities
    before selecting it. Benchmark cases cannot replace authority, iteration or human/UI lanes.
  - Accepted parameters on 2026-10-05/06: [P01–P07](../architecture/iterative-delivery-decisions.md#baseline-protocol-decisions)
    record active-time accounting; 40 execution starts, 3 children and 2 active hours per
    Work Item; stop after 2 consecutive correction/check cycles without confirmed progress;
    mandatory correctness/understanding with overhead diagnostics; 5 first-time participants,
    at least 4 unassisted successes and no serious interface-caused error; 3 native repetitions
    of 4 task classes on each version, 24 initial trials per runtime configuration; and
    expected outcomes in all 3 counted candidate repetitions, with replacement of only a
    diagnosed externally interrupted trial. All attempts remain retained. These choices
    do not complete case/oracle selection, baseline inventory or the protocol; status stays Next.
  - Dependencies: `W57-E1-S1-T1`.
  - Verification: the earlier release and replacement candidate can be evaluated separately
    against the same task/oracle without generated plans as the answer key or classic
    support in the new engine; missing baseline evidence stays unavailable.

#### Slice W57-E1-S2 — ground criteria and applied answers (`planned`)

Dependencies: `W57-E1-S1-T1`. Task-specific dependencies below govern later work.

- `W57-E1-S2-T1` (next) Add source-bound criteria and scoped product decisions.
  - Output: compact Markdown criterion proposal plus AIDD-owned authority/decision records,
    stable source anchors/digests, revision identity, and eligibility for unresolved decisions.
  - Scope: document contracts/ownership, core source/decision services, validation context,
    and minimal CLI question/decision integration; protect operator-authored originals.
  - Dependencies: `W57-E1-S1-T1`.
  - Verification: explicit criteria continue without blanket approval; proposed additions
    and conflicts block; runtime permission, document opening, and model sign-off cannot
    confer product authority; stale source decisions are detected. Decomposition changes
    reuse authority only within unchanged criterion/constraint/authorized-scope bounds;
    ambiguous equivalence blocks without model self-certification.

- `W57-E1-S2-T2` (soon) Dereference evidence paths, IDs, and criterion coverage.
  - Output: deterministic reference resolution across request, criteria, plan/tasklist,
    review-spec, implementation, review, and QA, with precise missing/stale findings.
  - Scope: `validators/cross_document_rules`, semantic evidence rules, source context and
    fixtures; load consumed protected request/answer/criterion/decision revisions into
    context. Pin those revisions in the current run, then adopt the unified resolver in
    W58-E1-S2-T2. Implement locator identity/bounded fragments, not NLP truth heuristics.
  - Dependencies: `W57-E1-S2-T1`.
  - Verification: nonexistent file/line/ID, changed digest, unrelated ID, and internally
    consistent documents omitting an original constraint cannot produce complete coverage.

- `W57-E1-S2-T3` (planned) Track answer application through decisions and behavior.
  - Output: QID → answer revision → affected criteria/tasks → resulting evidence mapping;
    distinguish recorded, linked, and actually assessed application.
  - Scope: interview consistency, input compiler, criterion revisions, question projections,
    and focused CLI fixtures. Add no duplicate free-text summary requirement.
  - Dependencies: `W57-E1-S2-T1`, `W57-E1-S2-T2`.
  - Verification: resolving a QID without applying the answer leaves a coverage/assessment
    gap; changed answers invalidate affected criteria; unrelated criteria stay intact.
    A correct QID link with unchanged wrong behavior passes link integrity but is rejected
    or remains inconclusive under behavioral assessment; linking alone cannot prove application.

### Epic W57-E2 — product-owned verification and honest acceptance (`planned`)

Goal: Make product task success depend on AIDD-owned current verification and final delivery
depend on attributed criterion assessment.

#### Slice W57-E2-S1 — declare, execute, and bind checks (`planned`)

Dependencies: `W57-E1-S1-T1`, `W57-E1-S2-T1`. Task-specific dependencies below govern later
work.

- `W57-E2-S1-T1` (soon) Register declared check definitions and execution policy.
  - Output: typed check registry with stable IDs, exact command/argv or declared shell form,
    cwd/project ownership, timeouts, expected result, prerequisites, `authority_source`,
    definition registration event and authority digest; include a declared-input manifest.
  - Scope: configuration boundary, check-definition Markdown/current state, project-set
    policy, task criterion references, doctor/preflight, and deterministic fixtures.
  - Dependencies: `W57-E1-S1-T1`, `W57-E1-S2-T1`.
  - Verification: runtime report text cannot register/execute a new command; undeclared cwd,
    incompatible configuration, changed check definitions, and absent prerequisites stop
    explicitly. Model-authored tasklist verification is also a proposal until registered
    under authorized policy. Test full-access/brokered distinctions honestly.

- `W57-E2-S1-T2` (planned) Execute checks through AIDD and retain check receipts.
  - Output: application verification service with an injected execution port, process
    ownership, stdout/stderr, exit/timeout/cancel status, duration, and sealed receipt.
  - Scope: shared narrow process infrastructure, application composition, core lifecycle,
    receipt retention, and direct executor fixtures. Keep this task centered on the product
    execution/receipt lifecycle; wire CLI/task gates in W57-E2-S2-T1 and harness scenarios in
    W57-E2-S2-T3. Do not import harness orchestration into product core.
  - Dependencies: `W57-E2-S1-T1`.
  - Verification: false “pass” reports, all-skipped checks, timeout, cancellation, missing
    executable, and interrupted process retain truthful results and block required progression.
    A substituted harness transcript cannot satisfy the product receipt gate.

- `W57-E2-S1-T3` (planned) Bind proof to code, check, source, and environment identity.
  - Output: freshness policy for tree content including uncommitted/untracked inputs,
    applied answer/criterion/check/config digests, cwd/project set, and declared lock/tool/
    environment/ignored/generated inputs, with the receipt identity specified in the migration plan.
  - Scope: repository evidence, receipt schema, freshness service, finalization publication,
    and non-Git/declared generated-input fixtures. Avoid exposing secrets in environment logs.
  - Dependencies: `W57-E1-S2-T2`, `W57-E1-S2-T3`, `W57-E2-S1-T2`.
  - Verification: stale code, modified test/oracle, replaced checkout, changed criterion,
    check/cwd/config, and required ignored input invalidate proof. Classify verification
    byproducts so output generation does not spuriously alter product identity.

#### Slice W57-E2-S2 — gate task and delivery outcomes (`planned`)

Dependencies: `W57-E2-S1-T3`. Task-specific dependencies below govern later work.

- `W57-E2-S2-T1` (planned) Require owned verification for task and finalization success.
  - Output: task gate and final aggregate gate; reports distinguish runtime claims from
    observed receipts, and required checks run on the final implementation tree. Separate
    implementation-stage success from downstream Work Item delivery acceptance.
  - Scope: task attempt executor, ledger, aggregate finalizer, stage reconciliation,
    CLI task/run output, implementation validators, and repair accounting.
  - Dependencies: `W57-E2-S1-T3`.
  - Verification: a structurally valid implementation report with no/currently failing
    receipts cannot succeed; fixes can resume the affected task; finalization changes require
    fresh aggregate checks; prior successful evidence remains retained.

- `W57-E2-S2-T2` (planned) Separate execution success from behavioral acceptance.
  - Output: criterion assessment contract and completion policy referencing independent
    expected behavior, counterexamples, regression oracles, or explicit manual acceptance;
    oracle source/owner/version/digest is sealed before implementation.
  - Scope: review/QA contracts, assessment service, core delivery completion, graders,
    semantic rules, and honest operator labels. Model conclusions retain attribution.
  - Dependencies: `W57-E1-S1-T2`, `W57-E1-S2-T3`, `W57-E2-S2-T1`.
  - Verification: code/tests/documents agreeing on the wrong behavior fail the independent
    oracle; exit zero alone cannot confirm a subjective criterion; red-before/green-after
    regression evidence demonstrates that a check detects the relevant defect. Inconclusive/
    unassessed mandatory criteria permit only a stopped/partial outcome, never complete.

- `W57-E2-S2-T3` (planned) Demonstrate the complete grounded task pilot.
  - Output: installed deterministic positive/negative scenarios spanning request → criterion
    → task → diff → receipt → assessment, with retained audit bundles and grader verdicts.
  - Scope: deterministic scenarios/harness/evals and pilot evidence report. Adapt the pinned
    Hono non-error-throw behavior as one oracle without requiring a live provider for this gate.
  - Dependencies: `W57-E2-S2-T2`.
  - Verification: the migration plan’s truth/authority adversarial cases produce the expected first decisive
    failure; an actual correct change passes; evidence inspection agrees with exit status.

## Wave 58 — bounded iterative delivery (`planned`)

Goal: Replace mandatory contiguous preparation with finite policy-selected routes and bounded
child-run iterations of the same Work Item, preserving immutable inputs, addressed task
invalidation, and recovery evidence.

The current eight-stage workflow remains the execution baseline until its owning tasks are
completed. The accepted replacement reuses stage identifiers with policy-selected
operations and explicit prerequisite substitutes; it never creates successful skipped stages.
Models, runtime tiers, and optional multi-agent defaults are outside this migration.

Linked stories: `US-01`, `US-03`, `US-04`, `US-05`, `US-08`, `US-10`, `US-12`, `US-13`.
Develop one replacement policy rather than an opt-in second engine. Change graph consumers
and input resolution deliberately; adding a child-run link while retaining mandatory
eight-stage preparation would leave the main product problem unresolved.

### Epic W58-E1 — policy identity and immutable plan revisions (`planned`)

Goal: Pin the sole executable policy and resolve versioned task plans from exact immutable run
inputs.

#### Slice W58-E1-S1 — make preparation policy explicit (`planned`)

Dependencies: `W57-E1-S1-T1`, `W57-E2-S2-T3`. Task-specific dependencies below govern later
work.

- `W58-E1-S1-T1` (planned) Persist sole policy, route, and objective budgets.
  - Output: explicit iterative current-format run identity, selected operations,
    policy/contract versions, runtime selectors, provenance, and inherited objective budgets.
  - Scope: `config.py`, run/store/manifest models, workflow/stage entrypoints, preflight,
    installed resource selection, and continuation identity checks.
    Pin [P01–P03](../architecture/iterative-delivery-decisions.md#p02-pilot-automation-limits)
    pilot defaults/accounting/progress-policy identity in the shared objective configuration;
    persist those settings before execution and retain them through child creation/resume.
  - Dependencies: `W57-E1-S1-T1`, `W57-E2-S2-T3`.
  - Verification: policy/config changes cannot alter an existing continuation; missing or
    unsupported format stops before mutation; no classic selector or compatibility fallback
    remains. Model/provider choices stay in configuration.

- `W58-E1-S1-T2` (planned) Resolve stage contracts and dependencies per selected route.
  - Output: finite executable routes, route input/output/ownership contracts, and updated
    registry/eligibility/publication consumers; selected operation/predecessor maps and
    `not-selected` dispositions replace the universal contiguous-stage requirement.
  - Scope: stage manifests/graph/registry/preparation, validators, packaged contracts,
    `workflow_service.py`, `cli/run.py`, `cli/stage_run.py`, `cli/ui.py`, read models,
    direct-stage/run parity, and scenario declarations.
  - Dependencies: `W58-E1-S1-T1`.
  - Verification: focused route runs without research/plan/review-spec output; omitted
    prerequisites have explicit substitutes; no skipped stage is marked succeeded;
    investigate/design routes and direct-stage entrypoints retain their declared requirements.

- `W58-E1-S1-T3` (planned) Select preparation depth from deterministic evidence signals.
  - Output: policy selector and durable route rationale for focused/investigate/design;
    escalation and question behavior for uncertain ownership or missing verification.
  - Scope: small core policy service, preflight/input discovery, next-action baseline,
    config policy settings, and table-driven scenarios.
  - Dependencies: `W58-E1-S1-T2`, `W57-E1-S2-T3`, `W57-E2-S2-T2`.
  - Verification: bounded bug fix avoids full preparation; unknown interface effects invoke
    investigation/design; material ambiguity asks; free confidence/provider names cannot
    downgrade preparation. Every route retains completion gates.

#### Slice W58-E1-S2 — version inputs and preserve reusable work (`planned`)

Dependencies: `W58-E1-S1-T2`, `W57-E1-S2-T2`. Task-specific dependencies below govern later
work.

- `W58-E1-S2-T1` (planned) Version task plans and require explicit revision mappings.
  - Output: immutable Markdown task plan revision, retained/changed/removed/new mappings,
    stable criterion/task references, and fingerprints of task meaning and execution scope.
  - Scope: tasklist contracts/parser, ledger initialization, source mismatch handling,
    fixtures and targeted planning prompts. Keep the current plan immutable in each run.
  - Dependencies: `W58-E1-S1-T2`, `W57-E1-S2-T2`.
  - Verification: duplicate/ambiguous mappings stop; same ID with changed scope/criterion is
    treated as changed; an in-place tasklist edit cannot silently redefine a running ledger.
    Revision checks enforce the unchanged product authority bounds without requiring
    re-approval solely for a dependency/decomposition change.

- `W58-E1-S2-T2` (planned) Resolve all consumed artifacts from immutable run snapshots.
  - Output: exact-run input resolver and publication/index semantics for current outputs,
    parent sources, source digests, run-local runtime staging roots, and active projections;
    durable publication phases and coherent validated bundle commit.
  - Scope: stage/task preparation and readers, finalization eligibility, stage outputs,
    run inspection/artifact index, and source snapshots; include failed/blocked sources.
  - Dependencies: `W58-E1-S1-T1`, `W58-E1-S2-T1`.
  - Verification: different runs in one Work Item consume different tasklists safely; latest
    publication cannot alter historical inputs; missing/stale/failed parent artifacts are
    rejected; crash recovery never combines half-published revisions. Uncommitted or blocked
    child documents leave the committed parent projection intact.

- `W58-E1-S2-T3` (planned) Invalidate affected tasks and carry forward verified work.
  - Output: finding-to-task dependency closure and revision-specific ledger initialization
    with an explicit executed/reused disposition, immutable source-run/task-attempt/digest
    references, task fingerprints, retained work, and required re-verification.
  - Scope: task plan/ledger/evidence, repository snapshots, task read model, and finalization;
    revise ledger completion predicates deliberately rather than equating reuse to an attempt.
  - Dependencies: `W58-E1-S2-T1`, `W58-E1-S2-T2`, `W57-E2-S1-T3`.
  - Verification: changed criterion/task and dependents rerun; independent work remains
    attributable; stale whole-tree proof reruns checks; absent retained code or ambiguous
    finding prevents reuse. Reused work cannot satisfy final proof without required checks
    on the new final tree. No blind “reopen last task” in the iterative path.

### Epic W58-E2 — bounded controller and task-local context (`planned`)

Goal: Use current evidence to continue, repair, replan, ask, or stop while keeping execution
bounded and prompts task-local.

#### Slice W58-E2-S1 — implement the evidence-driven control loop (`planned`)

Dependencies: `W58-E1-S1-T3`, `W58-E1-S2-T2`, `W58-E1-S2-T3`, `W57-E2-S2-T2`. Task-specific
dependencies below govern later work.

- `W58-E2-S1-T1` (planned) Create child iterations through a bounded controller.
  - Output: `continue/repair/replan/ask/stop` decision service and same-Work-Item child-run
    creation with sealed predecessor, source authority, invalidation, and atomic lease
    handoff; stable decision/idempotency identity and durable decision-to-child index.
  - Scope: workflow service, child-run application service, run/store/attempt lineage,
    decision records and deterministic controller scenarios; no adapter policy branches.
    Implement the [P01–P03](../architecture/iterative-delivery-decisions.md#p01-objective-time-accounting)
    pilot limits and progress rule; children/retries do not reset shared counters, and
    admitting the final allowed start/child does not cancel it merely because its count is reached.
  - Dependencies: `W58-E1-S1-T3`, `W58-E1-S2-T2`, `W58-E1-S2-T3`, `W57-E2-S2-T2`.
  - Verification: execution proof changes the next action; valid failed/blocked/succeeded
    sources are handled deliberately; active or malformed parent is rejected; limits stop
    repeated replans; unrelated task successes and parent evidence remain intact.

- `W58-E2-S1-T2` (planned) Reconcile crash, cancellation, questions, and budget accounting.
  - Output: explicit lifecycle/accounting rules for repair, retry, answer continuation,
    verification, fix, and iteration, including no-progress detection and partial receipts.
  - Scope: attempt lineage, owned process lifecycle, leases/jobs, recovery/reconciliation,
    budget provenance, and failure classification.
    Apply P01 waiting exclusions only after all executions are confirmed stopped; retain
    active-time intervals and P02 debits across recovery, and P03 blocker lineage across children.
  - Dependencies: `W58-E2-S1-T1`.
  - Verification: injected crashes around command completion and child publication do not
    double-execute or reset budgets; resumed questions use current answers; cancellation
    leaves truthful terminal state and first decisive failure evidence. Crashes before/after
    manifest/index commit return the same child or explicit incomplete transaction;
    iteration debit and actual receipt cost/time accounting happen once.

- `W58-E2-S1-T3` (planned) Route remediation and feedback to the affected iteration.
  - Output: route-aware correction/change service shared by run/stage/task/CLI/UI paths;
    distinguish same-plan fix, replan, product change, and new-objective follow-up.
  - Scope: remediation/intervention/next-flow/application entrypoints, request documents,
    task routing and core/CLI regressions under the sole replacement policy.
  - Dependencies: `W58-E2-S1-T2`, `W58-E1-S2-T3`.
  - Verification: review/QA findings address exact tasks; forbidden stage intervention does
    not bypass downstream authority; feedback cannot silently expand the objective; unchanged
    authorized corrections do not add blanket approval; source lineage survives follow-up.

#### Slice W58-E2-S2 — deliver compact context without a summary cascade (`planned`)

Dependencies: `W58-E1-S2-T2`, `W58-E1-S2-T3`, `W57-E1-S2-T3`. Task-specific dependencies below
govern later work.

Change one workload prompt group at a time. For every task below, keep model/provider/
reasoning, scenario, and other prompt groups pinned; compare representative traces before
and after. Group-specific regressions belong in the same task.

- `W58-E2-S2-T1` (planned) Compile task-local briefs from exact source artifacts.
  - Output: deterministic bounded brief containing the selected criterion, scope,
    dependencies, constraints, current finding, declared checks, and exact source locators.
  - Scope: application/stage preparation, task attempt executor, prompt assembly/provenance,
    and fixture traces. Full sources remain inspectable rather than copied into every prompt.
  - Dependencies: `W58-E1-S2-T2`, `W58-E1-S2-T3`, `W57-E1-S2-T3`.
  - Verification: required constraints/answers survive compaction; stale input cannot be
    substituted; task context excludes unrelated reports while preserving source identity.

- `W58-E2-S2-T2` (planned) Adapt intake and discovery prompts to criterion-first outputs.
  - Output: lean idea/research role prompts and route outputs centered on outcome,
    source evidence, concrete unknowns, and decisions; detailed discovery only when selected.
  - Scope: intake/discovery prompt packs, document examples/contracts and pinned trace/eval
    comparisons. Change individual stage prompts sequentially within this workload group.
  - Dependencies: `W58-E2-S2-T1`, `W58-E1-S1-T3`.
  - Verification: explicit constraints stay visible; unsupported product assumptions create
    questions/proposals; focused runs do not produce a mandatory long research narrative.

- `W58-E2-S2-T3` (planned) Adapt planning prompts to bounded versioned task cards.
  - Output: tasklist/optional design review prompts with criterion IDs, task-local proof,
    revision mapping, and only necessary design decisions; no unconditional full specification.
  - Scope: planning prompt group, plan/review-spec/tasklist contracts/examples and trace
    comparisons, with intake/delivery prompts pinned.
  - Dependencies: `W58-E2-S2-T1`, `W58-E1-S2-T1`, `W58-E2-S2-T2`.
  - Verification: focused and design routes both yield executable coverage; replans retain
    identity correctly; concise output does not omit dependencies, boundaries, or checks.

- `W58-E2-S2-T4` (planned) Adapt implementation prompts to task changes and attributed claims.
  - Output: lean task execution/finalization instructions and reports pointing to owned
    receipt IDs, changed paths, residual gaps, and scope violations.
  - Scope: implementation prompt group and Markdown report contracts/examples; preserve
    existing runtime capabilities and model defaults.
  - Dependencies: `W58-E2-S2-T1`, `W58-E2-S2-T3`, `W57-E2-S2-T1`.
  - Verification: a task-local trace applies its criterion and constraints; model text
    cannot fabricate an AIDD receipt or enlarge check/project authority.

- `W58-E2-S2-T5` (planned) Adapt review and QA prompts to criterion assessments and findings.
  - Output: attributed, addressable findings and assessments against original criteria,
    current changes, and check evidence; distinguish observations from proposed conclusions.
  - Scope: review/QA prompt group, document contracts, graders and pinned trace comparisons.
  - Dependencies: `W58-E2-S2-T4`, `W57-E2-S2-T2`.
  - Verification: wrong but internally consistent code is rejected by the oracle; review
    gives criterion/task locators usable for replan; missing proof remains inconclusive.

#### Slice W58-E2-S3 — prove integrated iteration and portability (`planned`)

Dependencies: `W58-E1-S2-T3`, `W58-E2-S1-T1`, `W58-E2-S1-T2`, `W58-E2-S1-T3`, `W58-E2-S2-T5`.
Task-specific dependencies below govern later work.

- `W58-E2-S3-T1` (planned) Demonstrate route, iteration, and recovery conformance.
  - Output: installed deterministic scenario matrix for all routes, multi-iteration
    correction/replan, carry-forward/re-verification, failed/blocked sources, and explicit
    unsupported-format stops without workspace mutation.
  - Scope: harness/scenarios/evals, fake-runtime conformance and packaged-resource fixtures.
  - Dependencies: `W58-E1-S2-T3`, `W58-E2-S1-T1`, `W58-E2-S1-T2`, `W58-E2-S1-T3`, `W58-E2-S2-T5`.
  - Verification: the migration plan’s lifecycle/boundary adversarial cases and nearest core/application/CLI checks
    pass; raw runtime/verification logs and final evidence are inspected; orchestration
    policy has no provider-specific branch or newly enabled multi-agent requirement.

## Wave 59 — operator understanding and finite cutover (`planned`)

Goal: Make outcome, decisions, changes, and proof the primary CLI/UI experience, measure real
operator understanding, and finish the migration through one accepted breaking replacement
with aligned current formats, packaged resources and operator guidance.

Coordinate W59-E2-S1-T2 with W42-E7-S2-T3 and W36-E7-S3-T2/T3, and W59-E2 acceptance with
W36-E7-S4-T5 and existing W50 candidate-evidence policy. Existing parked tasks retain their
ownership and status; evidence may satisfy overlapping requirements only after exact
candidate/protocol/scope reconciliation. A scripted replay cannot close a human observation;
this migration does not imply beta readiness. Live execution, participant coordination, and
publication retain their normal authorization boundaries.

Linked stories: `US-05`, `US-06`, `US-07`, `US-09`, `US-10`, `US-11`, `US-13`.
Extend the existing Studio/Inbox/History and core next-action services. UI must not invent
eligibility, infer proof from prose, or require a Spec Tour before routine execution.

### Epic W59-E1 — outcome, decision, and history surfaces (`planned`)

Goal: Expose one shared source-to-outcome projection and preserve operator, project, run, and
history authority.

#### Slice W59-E1-S1 — make outcome and proof the primary view (`planned`)

Dependencies: `W58-E2-S3-T1`. Task-specific dependencies below govern later work.

- `W59-E1-S1-T1` (planned) Project criterion coverage and one authoritative next action.
  - Output: shared core payload `source → criterion → task → change → receipt → assessment`,
    with unknown/stale states, exact locators, selected operations, and scoped decision/action.
  - Scope: operator read models, reports/Inbox/next action, task projections, application DTOs.
  - Dependencies: `W58-E2-S3-T1`.
  - Verification: projection derives from persisted facts; partial coverage cannot become
    “verified”; required decision, runtime permission, question, and failed check remain
    distinct blockers; reused work is not displayed as a new successful attempt.

- `W59-E1-S1-T2` (planned) Expose outcome, proof, and scoped decisions through CLI.
  - Output: inspect/decide/change commands and truthful run/task summaries using the shared
    application services, with durable decision readback and exact evidence navigation.
  - Scope: CLI run/stage/task surfaces and focused tests; retain logs/artifacts inspection.
  - Dependencies: `W59-E1-S1-T1`.
  - Verification: same cases as UI yield the same blocker/action/outcome; stale and repeated
    decisions have explicit conflict/idempotency behavior; product decisions do not mask
    runtime permission, unanswered questions, or failing receipts.

- `W59-E1-S1-T3` (planned) Render criterion, change, and proof cards in Operator UI.
  - Output: primary outcome view showing before/after behavior, affected tasks/diff,
    actual checks, uncertainty, and needed decision; dynamic operation navigation/progress.
  - Scope: existing Studio components/static assets, payload consumers, DOM/browser fixtures.
    Follow the [iterative UX blueprint](../architecture/iterative-operator-ux.md) and
    [concept reference](../design/iterative-operator/README.md); use the core projection,
    not the concept's synthetic state machine.
  - Dependencies: `W59-E1-S1-T1`, `W57-E1-S1-T3`.
  - Verification: representative focused/design/correction routes have truthful progress;
    one primary action comes from core; source/diff/receipt/log opens exact retained evidence;
    no mandatory generated prose tour or second planning mode appears.

- `W59-E1-S1-T4` (planned) Show how an answer or change request affected delivery.
  - Output: operator feedback/answer surfaces linked to criterion revision, affected tasks,
    child decision, resulting change/check, and any remaining application gap.
  - Scope: existing question/change/recovery forms, CLI readback, shared change service,
    source comparison and UI projections.
  - Dependencies: `W59-E1-S1-T2`, `W59-E1-S1-T3`, `W58-E2-S1-T3`.
  - Verification: an ignored answer is visible as a gap; material change asks for scoped
    authority; ordinary correction preserves prior authority; no action silently expands
    project set or loses authored feedback after navigation.

#### Slice W59-E1-S2 — preserve identity across time and navigation (`planned`)

Dependencies: `W59-E1-S1-T4`, `W58-E1-S2-T2`, `W58-E2-S3-T1`. Task-specific dependencies below
govern later work.

- `W59-E1-S2-T1` (planned) Join criteria, plan revisions, decisions, and iterations in History.
  - Output: timeline/Filmstrip and CLI inspection for parent/child runs, criterion/plan diffs,
    reused attempts, decisions, receipts, assessments, and stale/downstream consequences.
  - Scope: existing History/Compare/artifact-index read models and browser fixtures.
  - Dependencies: `W59-E1-S1-T4`, `W58-E1-S2-T2`, `W58-E2-S3-T1`.
  - Verification: history reads exact snapshots and shows unavailable evidence honestly;
    latest work-item files cannot reconstruct old state; runtime permissions remain separate.

- `W59-E1-S2-T2` (planned) Preserve project and job authority across iteration transitions.
  - Output: correct originating project/run/child context in background jobs, Inbox,
    refreshes, links, mutation guards, and cancellation/resume surfaces.
  - Scope: UI job/context routing and existing stale-response protections, CLI parity,
    DOM/browser journey regressions; preserve selected model/reasoning propagation.
  - Dependencies: `W59-E1-S1-T4`, `W59-E1-S2-T1`.
  - Verification: switching project or active iteration while a job runs cannot apply an
    old decision to a new run; stale responses cannot render completion or enable a mutation;
    task, question, approval, review/QA, and recovery journeys still work.

### Epic W59-E2 — acceptance and direct breaking cutover (`planned`)

Goal: Collect exact-candidate correctness and understanding evidence, validate installed
delivery, and remove the retired executable path.

#### Slice W59-E2-S1 — measure correctness and understanding (`planned`)

Dependencies: `W57-E1-S1-T2`, `W58-E2-S3-T1`, `W59-E1-S2-T2`. Task-specific dependencies below
govern later work.

- `W59-E2-S1-T1` (planned) Compare the pinned earlier release and replacement native-runtime runs.
  - Output: paired evidence bundles and independent product-quality report for bounded
    fix, ambiguous requirement, design change, and correction/replan cases. Pin target repo
    commit, fixture/oracle, runtime/model/reasoning and environment across variants; record
    exact AIDD/prompt revisions and intentional policy/prompt differences separately.
    Run the earlier package/revision in a separate checkout/environment; the replacement
    does not include classic execution or old-format readers for comparison.
  - Scope: existing manual live E2E manifests/catalog/rubric and maintained runtime lanes.
    Follow `live-e2e` for authorized execution; do not change models/prompts/pins to rescue
    one side of the comparison. Native behavior evidence is separate from fake-runtime tests.
    Use [P06](../architecture/iterative-delivery-decisions.md#p06-native-comparison-repetitions)
    for the 4-class/3-repeat/2-version matrix and
    [P07](../architecture/iterative-delivery-decisions.md#p07-native-acceptance-and-external-failure-replacement)
    for expected outcomes in all 3 counted candidate repetitions and diagnosed external-failure
    replacement; preserve every attempt and separate scenario trials from execution starts.
  - Dependencies: `W57-E1-S1-T2`, `W58-E2-S3-T1`, `W59-E1-S2-T2`.
  - Verification: original requirements and counterexamples determine quality; cost/time,
    reading burden, first verified change, failures, and interventions are recorded. Tier 1
    defects block release; other tiers retain their existing policy and explicit caveats.

- `W59-E2-S1-T2` (planned) Observe real operators using the new outcome flow.
  - Output: uncoached task observations and paired comprehension report with confusion,
    wrong actions, assistance, exact decision/evidence understanding, and follow-up findings;
    matched fixtures, pinned runtime/model/environment, and counterbalanced observation order.
  - Scope: existing observed-acceptance protocol and anonymized retained evidence. Reconcile
    W42-E7-S2-T3 and W36-E7-S3-T2/T3 rather than duplicating or silently closing them.
    Apply [P05](../architecture/iterative-delivery-decisions.md#p05-first-replacement-operator-observation):
    5 eligible first-time participants, at least 4 completing every key task without coaching,
    and no serious interface-caused error in any session; retain all participant outcomes.
  - Dependencies: `W57-E1-S1-T2`, `W58-E2-S3-T1`, `W59-E1-S1-T3`, `W59-E1-S1-T4`, `W59-E1-S2-T2`.
  - Verification: genuine participants explain the migration plan’s comprehension questions and complete recovery;
    scripted browser replay does not count. Missing participants/environment are outstanding
    evidence, not a pass. A beta claim still requires its broader existing readiness gate.

- `W59-E2-S1-T3` (planned) Audit implementation-candidate readiness before final packaging.
  - Output: go/no-go report tying correctness, human observations, failure taxonomy,
    deterministic/browser/native evidence, runtime tiers, known gaps and thresholds to
    one implementation candidate; it permits packaging/cutover preparation, not release.
  - Scope: eval aggregation and acceptance docs; fixes return to the owning accepted task
    with new evidence, not a threshold rewrite or silent baseline replacement.
    Apply [P04](../architecture/iterative-delivery-decisions.md#p04-mandatory-acceptance-and-overhead-diagnostics)
    quality/understanding gates with diagnostic overhead metrics, plus P05–P07 sample,
    expected-outcome and replacement rules. Preserve existing runtime-tier release consequences.
  - Dependencies: `W59-E2-S1-T1`, `W59-E2-S1-T2`.
  - Verification: predeclared implementation-readiness gates are met with inspectable
    evidence, or report an explicit no-go with the replacement unaccepted. No public
    opt-in coexistence lane or later classic-removal phase is created. Installation,
    final routing/cleanup and the final package gate remain W59-E2-S2 obligations.

#### Slice W59-E2-S2 — finish the migration in current formats (`planned`)

Dependencies: `W59-E2-S1-T3`. Task-specific dependencies below govern later work.

- `W59-E2-S2-T1` (planned) Validate installation and operator guidance for the candidate.
  - Output: packaged contracts/prompts/UI, clean pipx/uv-tool candidate evidence, doctor
    behavior, and README/handbook/config/current-format migration instructions.
  - Scope: packaging/resources, distribution/release docs, install harness and checklists;
    local candidate preparation does not authorize external publication.
  - Dependencies: `W59-E2-S1-T3`.
  - Verification: installed tool runs the same scenarios and UI as the source candidate;
    no resource lookup depends on checkout-only paths; instructions explain authority,
    receipts, iteration, historical evidence, and explicit unsupported-format stops.

- `W59-E2-S2-T2` (planned) Finalize the sole iterative policy in the replacement candidate.
  - Output: one current executable policy and aligned launch/configuration/provenance;
    explicit recreation and return-to-earlier-version guidance without automatic conversion.
  - Scope: configuration/routing, provenance, CLI/UI launch, docs and regressions.
  - Dependencies: `W59-E2-S1-T3`, `W59-E2-S2-T1`.
  - Verification: every supported launch uses the sole iterative policy and pins its
    identity. No old artifacts/manifests are rewritten or resumability promised across
    incompatible engine/format versions. Rollback explicitly uses the earlier package/
    revision and its compatible retained workspace, without an in-engine classic fallback.

- `W59-E2-S2-T3` (planned) Audit removal of obsolete execution and format consumers.
  - Output: the replacement candidate contains no retired classic implementation,
    selectors, aliases, compatibility readers or automatic converters; unsupported-input
    diagnostics and retained raw-history inspection agree with the direct cutover contract.
  - Scope: core/application/CLI/UI/resources/tests plus explicit changelog/compatibility notes.
  - Dependencies: `W59-E2-S2-T2`; the direct replacement gate is `W59-E2-S1-T3`.
  - Verification: current inputs pass; retired inputs stop clearly; source/resource scan
    finds no retired executable consumers. Raw historical evidence remains available for
    direct/archive inspection; recreation is deliberate, not a silent format conversion.

- `W59-E2-S2-T4` (planned) Seal final migration and release-readiness evidence.
  - Output: final go/no-go for the exact final tree/wheel after routing/cleanup, reconciled
    stories/traceability/roadmap, deterministic/browser/native acceptance, human-understanding
    and install evidence, release notes and outstanding limitations.
  - Scope: final installed candidate and documentation; use `release-publish` only if actual
    publishing is subsequently requested. Do not label the alpha beta-ready by inference.
  - Dependencies: `W59-E2-S2-T3`.
  - Verification: `make check`, `make test-browser`, required runtime/installation lanes and
    candidate evidence agree on the exact final revision; distinguish unrun/blocked checks
    from passed ones. Earlier implementation-readiness evidence cannot qualify changed
    behavior by itself. Human observations require explicit scope/impact/revision validation
    against the final candidate; changes to observed behavior/UI require new observations.
    Release readiness requires final-candidate evidence and does not authorize publication.
