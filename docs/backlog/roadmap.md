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

This roadmap contains open work and the current cleanup only. Completed task definitions,
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

## Wave 47 — repository cleanup and current-format boundary (`planned`)

Goal: remove unused code, obsolete compatibility, misleading instructions, and historical
repository clutter while preserving current workflow, validation, repair, and evidence behavior.

### Epic W47-E1 — current contracts and core (`done`)

#### Slice W47-E1-S1 — canonical document authoring (`done`)

- `W47-E1-S1-T1` (done) Align repair/intervention prompts and stage-brief contracts with AIDD-owned records.
  - Output: consistent prompts, contracts, examples, and normative architecture.
  - Scope: prompt packs and document ownership guidance.
  - Verification: prompt-quality, contract examples, stage preparation, and deterministic scenario checks.

#### Slice W47-E1-S2 — core and adapter cleanup (`done`)

- `W47-E1-S2-T1` (done) Remove unused core APIs and obsolete artifact readers; consolidate active duplicates.
  - Output: current-only core readers and shared helpers with current behavior preserved.
  - Scope: core modules and their focused tests.
  - Verification: core tests cover current round trips and explicit rejection of retired formats.

- `W47-E1-S2-T2` (done) Remove adapter residue and obsolete configuration compatibility.
  - Output: smaller adapters/configuration without unused APIs, shadowed TypeVars, or logging.mode.
  - Scope: adapters, root configuration modules, and relevant CLI config display.
  - Verification: adapter/configuration tests and type checking.

- `W47-E1-S2-T3` (done) Remove dead validator grammar and retired vocabulary.
  - Output: one current tasklist grammar and canonical report vocabulary.
  - Scope: validators and validator tests.
  - Verification: validator suite preserves current valid/invalid document outcomes.

### Epic W47-E2 — execution surfaces (`planned`)

#### Slice W47-E2-S1 — harness cleanup (`done`)

- `W47-E2-S1-T1` (done) Remove dead harness implementations and obsolete evidence compatibility.
  - Output: authoritative report/process helpers and current evidence readers.
  - Scope: harness/evals and their tests.
  - Verification: harness/eval tests and deterministic scenario lane.

#### Slice W47-E2-S2 — operator UI cleanup (`planned`)

- `W47-E2-S2-T1` (next) Remove unused UI functions and dormant test-only components.
  - Output: maintained UI assets and tests represent rendered product behavior.
  - Scope: CLI/static assets, frontend/browser tests, and UI-only helpers.
  - Verification: frontend Node tests, UI tests, JavaScript syntax, and packaged browser journeys.

### Epic W47-E3 — repository maintenance (`planned`)

#### Slice W47-E3-S1 — active documentation (`done`)

- `W47-E3-S1-T1` (done) Remove historical reports and stale planning history; repair active references.
  - Output: current documentation index, compact planning, and no stale active file references.
  - Scope: historical docs/reports, roadmap/backlog, contributor instructions, documentation tests.
  - Verification: documentation consistency, repository hygiene, and local-link checks.

#### Slice W47-E3-S2 — integration verification (`planned`)

- `W47-E3-S2-T1` (soon) Verify the integrated cleanup and reconcile remaining residue.
  - Dependencies: `W47-E3-S1-T1`, `W47-E1-S1-T1`, `W47-E1-S2-T1`, `W47-E1-S2-T2`, `W47-E1-S2-T3`, `W47-E2-S1-T1`, `W47-E2-S2-T1`.
  - Output: lint/type/test/scenario evidence and a reconciled current queue.
  - Scope: integration fixes and verification only.
  - Verification: complete repository quality gates and inspection of current workflow outputs.
