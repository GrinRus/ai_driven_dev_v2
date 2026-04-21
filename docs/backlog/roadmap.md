# Roadmap

This file is the canonical implementation plan for AIDD.

## Status vocabulary

- `done` — completed in the repo
- `next` — the preferred immediate target
- `planned` — accepted but not active
- `later` — useful but intentionally deferred

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

---

## Wave 0 — bootstrap artifacts and contributor ergonomics (`done`)

### Epic W0-E1 — root docs and architecture (`done`)
Linked stories: `US-01`, `US-02`, `US-07`, `US-09`, `US-10`, `US-13`

#### Slice W0-E1-S1 — root documentation set (`done`)
Goal: provide a clear project overview and contributor entrypoint.

Local tasks:

- `W0-E1-S1-T1` Write `README.md`.
- `W0-E1-S1-T2` Write lightweight root `AGENTS.md`.
- `W0-E1-S1-T3` Add `CLAUDE.md` as a compatibility entrypoint.

#### Slice W0-E1-S2 — architecture baseline (`done`)
Goal: fix the initial architecture and protocol decisions.

Local tasks:

- `W0-E1-S2-T1` Write target architecture.
- `W0-E1-S2-T2` Write adapter protocol.
- `W0-E1-S2-T3` Write document contract rules.
- `W0-E1-S2-T4` Write eval/harness integration.
- `W0-E1-S2-T5` Write runtime matrix and distribution notes.

### Epic W0-E2 — planning system and agent ergonomics (`done`)
Linked stories: `US-10`, `US-11`, `US-13`

#### Slice W0-E2-S1 — planning model (`done`)
Goal: make work selection explicit and hierarchical.

Local tasks:

- `W0-E2-S1-T1` Define wave/epic/slice/local-task planning.
- `W0-E2-S1-T2` Write the canonical roadmap.
- `W0-E2-S1-T3` Write the short backlog queue.

#### Slice W0-E2-S2 — agent ergonomics (`done`)
Goal: reduce repeated prompting for coding agents.

Local tasks:

- `W0-E2-S2-T1` Add nested `AGENTS.md` files.
- `W0-E2-S2-T2` Move team skills into `.agents/skills/`.
- `W0-E2-S2-T3` Add root skills for navigation, backlog work, story checks, live E2E, and log triage.

### Epic W0-E3 — live E2E discovery (`done`)
Linked stories: `US-07`, `US-11`

#### Slice W0-E3-S1 — repository selection (`done`)
Goal: define a first public-repo live E2E set.

Local tasks:

- `W0-E3-S1-T1` Select public repositories.
- `W0-E3-S1-T2` Define starter scenarios.
- `W0-E3-S1-T3` Add starter scenario manifests.

---

## Wave 1 — package, local developer loop, and release scaffolding (`done`)

### Epic W1-E1 — package and CLI scaffold (`done`)
Linked stories: `US-09`, `US-13`

#### Slice W1-E1-S1 — installable Python package (`done`)
Goal: make the repo runnable from source with a real console entrypoint.

Local tasks:

- `W1-E1-S1-T1` Add `pyproject.toml`.
- `W1-E1-S1-T2` Add `src/aidd/__init__.py`.
- `W1-E1-S1-T3` Add a working CLI scaffold.
- `W1-E1-S1-T4` Add CLI smoke tests.

#### Slice W1-E1-S2 — local workspace bootstrap (`done`)
Goal: provide a minimal useful local command.

Local tasks:

- `W1-E1-S2-T1` Implement `aidd doctor`.
- `W1-E1-S2-T2` Implement `aidd init`.
- `W1-E1-S2-T3` Add a sample config file.

### Epic W1-E2 — repository health files (`done`)
Linked stories: `US-09`, `US-10`, `US-13`

#### Slice W1-E2-S1 — contribution and license docs (`done`)
Goal: make the repo ready for external contributors.

Local tasks:

- `W1-E2-S1-T1` Write `CONTRIBUTING.md`.
- `W1-E2-S1-T2` Add `LICENSE`.
- `W1-E2-S1-T3` Add a PR template.

#### Slice W1-E2-S2 — CI and release scaffolding (`done`)
Goal: prepare standard automation for a Python CLI project.

Local tasks:

- `W1-E2-S2-T1` Add CI workflow.
- `W1-E2-S2-T2` Add release workflow.
- `W1-E2-S2-T3` Add `Makefile` and `.gitignore`.

---

## Wave 2 — document contracts and validator foundations (`next`)

### Epic W2-E1 — common and stage-specific contracts (`next`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-05`

#### Slice W2-E1-S1 — normative common document templates (`next`)
Goal: turn the current document placeholders into normative contracts.

Primary outputs:

- `contracts/documents/stage-brief.md`
- `contracts/documents/stage-result.md`
- `contracts/documents/questions.md`
- `contracts/documents/answers.md`
- `contracts/documents/validator-report.md`
- `contracts/documents/repair-brief.md`
- `contracts/examples/common-documents/`

Touched areas:

- `contracts/documents/`
- `contracts/examples/`

Dependencies:

- none

Local tasks:

- `W2-E1-S1-T1` (done) Write the required heading set, field notes, and authoring rules for `stage-brief.md`.
- `W2-E1-S1-T2` (done) Write the required heading set, attempt-history rules, and terminal-state notes for `stage-result.md`.
- `W2-E1-S1-T3` (done) Write the required heading set and blocking-question markers for `questions.md`.
- `W2-E1-S1-T4` (done) Write the required heading set and answer-resolution markers for `answers.md`.
- `W2-E1-S1-T5` (done) Write the required heading set, issue-code vocabulary, and severity rules for `validator-report.md`.
- `W2-E1-S1-T6` (done) Write the required heading set, rerun-budget notes, and fix-plan rules for `repair-brief.md`.
- `W2-E1-S1-T7` (done) Add one worked example bundle that includes every common document type and cross-links them correctly.

Exit evidence:

- every common contract file contains normative headings and section intent;
- one example bundle is reviewable end to end without missing document types.

#### Slice W2-E1-S2 — `idea` stage contract (`planned`)
Goal: define one stage contract that can capture a product idea before deeper research.

Primary outputs:

- `contracts/stages/idea.md`
- `prompt-packs/idea/`
- `contracts/examples/idea/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S1`

Local tasks:

- `W2-E1-S2-T1` Define the required input documents and optional context documents for the `idea` stage.
- `W2-E1-S2-T2` Define the required output documents and exit states for the `idea` stage.
- `W2-E1-S2-T3` Define stage-specific validation rules, including minimum completeness and no-placeholder requirements.
- `W2-E1-S2-T4` Define when `idea` may ask the user questions and which questions block progression.
- `W2-E1-S2-T5` Create the `idea` prompt-pack scaffold with system, task, and repair instructions.
- `W2-E1-S2-T6` Add one worked `idea` example bundle that matches the contract and prompt pack.

Exit evidence:

- `idea` can be run document-first with explicit input/output requirements;
- a validator can determine whether an `idea` result is acceptable without runtime-specific knowledge.

#### Slice W2-E1-S3 — `research` stage contract (`planned`)
Goal: define the research stage as a durable document exchange rather than an adapter-specific behavior.

Primary outputs:

- `contracts/stages/research.md`
- `prompt-packs/research/`
- `contracts/examples/research/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S1`

Local tasks:

- `W2-E1-S3-T1` Define the required `research` input bundle, including idea outputs and repository context.
- `W2-E1-S3-T2` Define the required `research` outputs, citation expectations, and evidence trace sections.
- `W2-E1-S3-T3` Define `research` validator rules for source grounding, uncertainty notes, and stale-fact handling.
- `W2-E1-S3-T4` Define `research` interview triggers for missing constraints, target repos, or ambiguous goals.
- `W2-E1-S3-T5` Create the `research` prompt-pack scaffold, including explicit evidence and question-generation guidance.
- `W2-E1-S3-T6` Add one worked `research` example bundle that includes unresolved-question and answered-question variants.

Exit evidence:

- `research` inputs and outputs are explicit enough for any adapter to run the stage;
- validators can reject unsupported assertions and incomplete research bundles.

#### Slice W2-E1-S4 — `plan` stage contract (`planned`)
Goal: define the planning stage that turns research into a bounded execution plan.

Primary outputs:

- `contracts/stages/plan.md`
- `prompt-packs/plan/`
- `contracts/examples/plan/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S1`

Local tasks:

- `W2-E1-S4-T1` Define the required `plan` input bundle and the dependency on `research` artifacts.
- `W2-E1-S4-T2` Define the required `plan` outputs, including milestones, risks, and verification notes.
- `W2-E1-S4-T3` Define validator rules for plan completeness, sequencing clarity, and user-approval readiness.
- `W2-E1-S4-T4` Define interview triggers for unresolved scope, sequencing disputes, or missing acceptance signals.
- `W2-E1-S4-T5` Create the `plan` prompt-pack scaffold with explicit roadmap-style reasoning rules.
- `W2-E1-S4-T6` Add one worked `plan` example bundle with a valid output and a validator-failing output.

Exit evidence:

- the `plan` stage can be evaluated from Markdown artifacts alone;
- validators can distinguish a reviewable plan from a vague or unsafely broad one.

#### Slice W2-E1-S5 — `review-spec` stage contract (`planned`)
Goal: define the specification-review stage that pressure-tests the plan before task generation.

Primary outputs:

- `contracts/stages/review-spec.md`
- `prompt-packs/review-spec/`
- `contracts/examples/review-spec/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E1-S4`

Local tasks:

- `W2-E1-S5-T1` Define the required `review-spec` inputs, especially the plan artifact and review context.
- `W2-E1-S5-T2` Define the required `review-spec` outputs, including issue lists, recommendation summaries, and readiness states.
- `W2-E1-S5-T3` Define validator rules for issue quality, actionable recommendations, and explicit sign-off status.
- `W2-E1-S5-T4` Define interview triggers for contradictory constraints or missing baseline assumptions.
- `W2-E1-S5-T5` Create the `review-spec` prompt-pack scaffold.
- `W2-E1-S5-T6` Add one worked `review-spec` example bundle.

Exit evidence:

- the `review-spec` stage can block downstream work with durable review artifacts;
- validators can distinguish actionable spec review from shallow commentary.

#### Slice W2-E1-S6 — `tasklist` stage contract (`planned`)
Goal: define the stage that converts approved plans into concrete engineering tasks.

Primary outputs:

- `contracts/stages/tasklist.md`
- `prompt-packs/tasklist/`
- `contracts/examples/tasklist/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E1-S5`

Local tasks:

- `W2-E1-S6-T1` Define the required `tasklist` inputs, including approved plan and spec-review results.
- `W2-E1-S6-T2` Define the required `tasklist` outputs, including task granularity, dependencies, and verification notes.
- `W2-E1-S6-T3` Define validator rules for task independence, ordering clarity, and reviewability.
- `W2-E1-S6-T4` Define interview triggers for unresolved sequencing or staffing assumptions.
- `W2-E1-S6-T5` Create the `tasklist` prompt-pack scaffold.
- `W2-E1-S6-T6` Add one worked `tasklist` example bundle.

Exit evidence:

- `tasklist` produces durable execution units rather than vague bullet lists;
- validators can reject oversized or ambiguous task decompositions.

#### Slice W2-E1-S7 — `implement` stage contract (`planned`)
Goal: define the stage that applies code or document changes in a runtime-agnostic way.

Primary outputs:

- `contracts/stages/implement.md`
- `prompt-packs/implement/`
- `contracts/examples/implement/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E1-S6`

Local tasks:

- `W2-E1-S7-T1` Define the required `implement` inputs, including task selection, repository state, and allowed write scope.
- `W2-E1-S7-T2` Define the required `implement` outputs, including change summary, touched files, and verification notes.
- `W2-E1-S7-T3` Define validator rules for missing diffs, unverifiable claims, and incomplete execution summaries.
- `W2-E1-S7-T4` Define repair expectations for invalid implementation runs and no-op outputs.
- `W2-E1-S7-T5` Create the `implement` prompt-pack scaffold with explicit edit and verification guidance.
- `W2-E1-S7-T6` Add one worked `implement` example bundle with both success and repair-needed variants.

Exit evidence:

- `implement` has a contract that does not rely on any one runtime's native schema;
- validators can force repair when execution claims are unsupported by artifacts.

#### Slice W2-E1-S8 — `review` stage contract (`planned`)
Goal: define the code or artifact review stage as a first-class document protocol.

Primary outputs:

- `contracts/stages/review.md`
- `prompt-packs/review/`
- `contracts/examples/review/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E1-S7`

Local tasks:

- `W2-E1-S8-T1` Define the required `review` inputs, including implementation output, diff context, and acceptance criteria.
- `W2-E1-S8-T2` Define the required `review` outputs, including findings, severity, and approval status.
- `W2-E1-S8-T3` Define validator rules for unsupported findings, missing severity labels, and absent disposition.
- `W2-E1-S8-T4` Define interview triggers for contradictory instructions or missing review baseline.
- `W2-E1-S8-T5` Create the `review` prompt-pack scaffold.
- `W2-E1-S8-T6` Add one worked `review` example bundle.

Exit evidence:

- `review` can be executed and judged from durable Markdown artifacts;
- validators can distinguish a real review from a superficial summary.

#### Slice W2-E1-S9 — `qa` stage contract (`planned`)
Goal: define the QA stage that translates artifacts and test evidence into a final quality verdict.

Primary outputs:

- `contracts/stages/qa.md`
- `prompt-packs/qa/`
- `contracts/examples/qa/`

Touched areas:

- `contracts/stages/`
- `prompt-packs/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S1`
- `W2-E1-S7`
- `W2-E1-S8`

Local tasks:

- `W2-E1-S9-T1` Define the required `qa` inputs, including implementation, review findings, and verification artifacts.
- `W2-E1-S9-T2` Define the required `qa` outputs, including verdict, residual risk, and release recommendation.
- `W2-E1-S9-T3` Define validator rules for unsupported verdicts and missing evidence references.
- `W2-E1-S9-T4` Define interview triggers for blocked verification or missing execution artifacts.
- `W2-E1-S9-T5` Create the `qa` prompt-pack scaffold.
- `W2-E1-S9-T6` Add one worked `qa` example bundle.

Exit evidence:

- `qa` produces a durable, auditable release-quality decision;
- validators can block downstream verdict use when evidence is missing.

### Epic W2-E2 — validator engine foundation (`next`)
Linked stories: `US-03`, `US-04`, `US-07`

#### Slice W2-E2-S1 — markdown document loader (`next`)
Goal: load and classify document artifacts from the workspace.

Primary outputs:

- `src/aidd/validators/document_loader.py`
- `src/aidd/validators/models.py`
- tests for loader behavior

Touched areas:

- `src/aidd/validators/`
- `tests/validators/`

Dependencies:

- `W1-E1-S1`

Local tasks:

- `W2-E2-S1-T1` (done) Implement workspace-relative path resolution for stage documents and common documents.
- `W2-E2-S1-T2` (done) Implement Markdown file loading that returns raw body text plus file metadata.
- `W2-E2-S1-T3` (done) Implement optional frontmatter parsing without making frontmatter required.
- `W2-E2-S1-T4` (done) Implement document-type classification from path and filename conventions.
- `W2-E2-S1-T5` (done) Add loader tests for missing files, malformed frontmatter, duplicate paths, and path normalization.

Exit evidence:

- workspace documents can be loaded and addressed by stage and document type;
- malformed documents fail with actionable loader errors.

#### Slice W2-E2-S2 — structural validation (`planned`)
Goal: validate required files and required sections before semantic checks run.

Primary outputs:

- `src/aidd/validators/structural.py`
- `src/aidd/validators/reports.py`
- tests for structural validation

Touched areas:

- `src/aidd/validators/`
- `tests/validators/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S1`
- `W3-E2-S1`

Local tasks:

- `W2-E2-S2-T1` Implement required-document existence checks from stage manifests.
- `W2-E2-S2-T2` Implement Markdown heading extraction for contract section validation.
- `W2-E2-S2-T3` Implement required-section checks against common-document and stage-document contracts.
- `W2-E2-S2-T4` Implement validator issue objects with stable codes, severity, and source location fields.
- `W2-E2-S2-T5` Implement `validator-report.md` rendering from collected structural issues.
- `W2-E2-S2-T6` Add regression tests for missing documents, missing headings, duplicated headings, and empty sections.

Exit evidence:

- structural validation can fail before runtime-specific interpretation happens;
- validator reports are durable Markdown artifacts, not console-only output.

#### Slice W2-E2-S3 — semantic and cross-document validation (`planned`)
Goal: validate deeper contract rules after structural checks pass.

Primary outputs:

- `src/aidd/validators/semantic.py`
- `src/aidd/validators/cross_document.py`
- regression tests for semantic rules

Touched areas:

- `src/aidd/validators/`
- `tests/validators/`

Dependencies:

- `W2-E1-S2` through `W2-E1-S9`
- `W2-E2-S2`

Local tasks:

- `W2-E2-S3-T1` Implement stage-specific semantic validators for completeness, unsupported claims, and placeholder detection.
- `W2-E2-S3-T2` Implement cross-document consistency checks for questions, answers, repair briefs, and stage results.
- `W2-E2-S3-T3` Implement validation rules for unresolved blocking questions and exhausted repair budgets.
- `W2-E2-S3-T4` Add semantic regression fixtures with both valid and invalid document bundles.
- `W2-E2-S3-T5` Add false-positive and false-negative tests for representative stage bundles.

Exit evidence:

- validators can explain why a bundle fails beyond missing headings;
- cross-document state drift is caught before progression.

---

## Wave 3 — orchestration core (`planned`)

### Epic W3-E1 — workspace and run store (`planned`)
Linked stories: `US-02`, `US-07`, `US-09`

#### Slice W3-E1-S1 — workspace bootstrap service (`next`)
Goal: move workspace creation logic from the CLI helper into reusable core code.

Primary outputs:

- `src/aidd/core/workspace.py`
- `src/aidd/core/work_item.py`
- updated `aidd init`

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`

Dependencies:

- `W1-E1-S2`

Local tasks:

- `W3-E1-S1-T1` (done) Define the canonical workspace directory layout and reserved file names.
- `W3-E1-S1-T2` (done) Implement a reusable service that creates the workspace directory tree.
- `W3-E1-S1-T3` (done) Implement starter document seeding for the first work item and default contract files.
- `W3-E1-S1-T4` (done) Define and write the work-item metadata file with stable identifiers and timestamps.
- `W3-E1-S1-T5` (done) Refactor `aidd init` to use the new workspace bootstrap service.
- `W3-E1-S1-T6` (done) Add bootstrap tests for fresh directories, existing directories, and partially initialized workspaces.

Exit evidence:

- workspace creation can be called from code without going through CLI-specific logic;
- repeated initialization attempts fail or recover in a predictable way.

#### Slice W3-E1-S2 — run metadata and storage (`planned`)
Goal: persist runs and attempts durably.

Primary outputs:

- `src/aidd/core/run_store.py`
- `src/aidd/core/models/run.py`
- tests for run persistence

Touched areas:

- `src/aidd/core/`
- `tests/core/`

Dependencies:

- `W3-E1-S1`

Local tasks:

- `W3-E1-S2-T1` (done) Define the run directory layout, including stage and attempt subdirectories.
- `W3-E1-S2-T2` (done) Implement run-manifest creation with runtime id, stage target, and config snapshot.
- `W3-E1-S2-T3` (done) Implement attempt-directory creation with monotonic attempt numbering.
- `W3-E1-S2-T4` (done) Persist stage status changes and timestamps in durable metadata files.
- `W3-E1-S2-T5` (done) Implement an artifact index that records canonical paths for stage documents and logs.
- `W3-E1-S2-T6` (done) Add run-store tests for fresh runs, repeated attempts, and interrupted writes.

Exit evidence:

- each run has durable storage that can be inspected after process exit;
- attempt history survives retries and repairs.

#### Slice W3-E1-S3 — run lookup and resume helpers (`planned`)
Goal: make existing runs addressable and resumable.

Primary outputs:

- `src/aidd/core/run_lookup.py`
- CLI wiring for resume helpers
- tests for run lookup

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`

Dependencies:

- `W3-E1-S2`

Local tasks:

- `W3-E1-S3-T1` (done) Implement helpers that resolve the latest run and latest attempt for a work item.
- `W3-E1-S3-T2` (done) Implement helpers that resolve artifact paths for a named stage and attempt.
- `W3-E1-S3-T3` (done) Implement resume guards that refuse to resume closed or corrupted runs.
- `W3-E1-S3-T4` (done) Expose run lookup in CLI-facing utilities used by later commands.
- `W3-E1-S3-T5` (done) Add tests for ambiguous runs, missing manifests, and resume-on-closed-run cases.

Exit evidence:

- the orchestration layer can reopen a run without scanning the workspace ad hoc;
- invalid resume targets fail with clear errors.

### Epic W3-E2 — stage controller (`planned`)
Linked stories: `US-01`, `US-02`, `US-03`

#### Slice W3-E2-S1 — stage manifest loader (`planned`)
Goal: load stage definitions and required documents.

Primary outputs:

- `src/aidd/core/stage_manifest.py`
- `src/aidd/core/stage_registry.py`
- tests for manifest loading

Touched areas:

- `src/aidd/core/`
- `contracts/stages/`
- `tests/core/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S1`

Local tasks:

- `W3-E2-S1-T1` (done) Define the Python model for a stage manifest and its required input/output declarations.
- `W3-E2-S1-T2` (done) Implement loading of stage manifests from `contracts/stages/`.
- `W3-E2-S1-T3` (done) Implement validation of manifest references to document contracts and prompt-pack paths.
- `W3-E2-S1-T4` (done) Implement resolution of required input documents for a selected stage.
- `W3-E2-S1-T5` (done) Implement resolution of expected output documents and validator targets for a selected stage.
- `W3-E2-S1-T6` (done) Add tests for valid manifests, missing references, and duplicate stage ids.

Exit evidence:

- stage metadata can be loaded from files rather than hardcoded in adapters;
- invalid contract references are caught before stage execution starts.

#### Slice W3-E2-S2 — stage state machine (`planned`)
Goal: run one stage through prepare -> execute -> validate -> advance/repair/block.

Primary outputs:

- `src/aidd/core/stage_runner.py`
- `src/aidd/core/state_machine.py`
- stage-runner tests

Touched areas:

- `src/aidd/core/`
- `tests/core/`

Dependencies:

- `W3-E1-S2`
- `W3-E2-S1`
- `W2-E2-S2`

Local tasks:

- `W3-E2-S2-T1` (done) Define the canonical stage states and legal transitions.
- `W3-E2-S2-T2` (done) Implement preparation logic that assembles the stage brief and expected input bundle.
- `W3-E2-S2-T3` Implement execution-state persistence before handing off to an adapter.
- `W3-E2-S2-T4` Implement validation-state persistence and transition decisions after validator completion.
- `W3-E2-S2-T5` Implement terminal transition handling for success, blocked, failed, and repair-needed outcomes.
- `W3-E2-S2-T6` Add tests that cover happy-path, validator-failure, blocked-question, and adapter-failure transitions.

Exit evidence:

- stage progression is modeled explicitly rather than hidden in CLI branching;
- every terminal state leaves durable stage metadata behind.

#### Slice W3-E2-S3 — stage dependency resolution and advancement (`planned`)
Goal: decide whether a stage may run and which stage should run next.

Primary outputs:

- `src/aidd/core/stage_graph.py`
- advancement helpers
- tests for dependency logic

Touched areas:

- `src/aidd/core/`
- `tests/core/`

Dependencies:

- `W3-E2-S1`
- `W3-E2-S2`

Local tasks:

- `W3-E2-S3-T1` Implement stage dependency resolution from manifest-declared upstream stages.
- `W3-E2-S3-T2` Implement eligibility checks for missing prerequisites, blocked questions, and failed required stages.
- `W3-E2-S3-T3` Implement the selection of the next runnable stage in a workflow sequence.
- `W3-E2-S3-T4` Implement advancement summaries that explain why a stage can or cannot run.
- `W3-E2-S3-T5` Add dependency-resolution tests for branching, skipped stages, and blocked upstream states.

Exit evidence:

- the orchestrator can explain readiness instead of silently skipping stages;
- stage order is derived from contracts, not adapter code.

### Epic W3-E3 — interview and repair controllers (`planned`)
Linked stories: `US-04`, `US-05`, `US-06`

#### Slice W3-E3-S1 — interview controller (`planned`)
Goal: persist and gate user questions.

Primary outputs:

- `src/aidd/core/interview.py`
- CLI question/answer helpers
- tests for interview control

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S3`
- `W3-E2-S2`

Local tasks:

- `W3-E3-S1-T1` Implement the interview policy model that distinguishes blocking and non-blocking questions.
- `W3-E3-S1-T2` Implement persistence of `questions.md` from stage output or adapter-detected question events.
- `W3-E3-S1-T3` Implement persistence and merging of `answers.md` without losing prior answers.
- `W3-E3-S1-T4` Implement stage gating that blocks progression when blocking questions remain unresolved.
- `W3-E3-S1-T5` Implement CLI helpers that display pending questions and guide the operator to answer them.
- `W3-E3-S1-T6` Implement state updates that unblock the stage once required answers are present.
- `W3-E3-S1-T7` Add tests for question persistence, partial answers, and unblock transitions.

Exit evidence:

- user questions become durable workflow artifacts rather than transient console prompts;
- blocked stages can resume only after required answers exist.

#### Slice W3-E3-S2 — repair controller (`planned`)
Goal: rerun invalid stages with bounded repair.

Primary outputs:

- `src/aidd/core/repair.py`
- repair state integration with the stage runner
- tests for repair flow

Touched areas:

- `src/aidd/core/`
- `tests/core/`

Dependencies:

- `W2-E1-S1`
- `W2-E2-S3`
- `W3-E2-S2`

Local tasks:

- `W3-E3-S2-T1` Implement repair-budget configuration and attempt counters for each stage.
- `W3-E3-S2-T2` Implement generation of `repair-brief.md` from a validator report and prior stage artifacts.
- `W3-E3-S2-T3` Implement rerun preparation that injects repair context into the next adapter invocation.
- `W3-E3-S2-T4` Implement durable repair-history recording in stage metadata and `stage-result.md`.
- `W3-E3-S2-T5` Implement terminal blocking when the repair budget is exhausted.
- `W3-E3-S2-T6` Add tests for one-shot repair success, repeated repair failure, and exhausted-budget blocking.

Exit evidence:

- repair loops are explicit, bounded, and auditable;
- stages never rerun indefinitely after repeated validation failure.

---

## Wave 4 — runtimes and operator UX (`planned`)

### Epic W4-E1 — `generic-cli` adapter (`planned`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W4-E1-S1 — runtime probing (`next`)
Goal: detect whether a generic CLI target is available.

Primary outputs:

- `src/aidd/adapters/generic_cli/probe.py`
- `aidd doctor` integration
- probe tests

Touched areas:

- `src/aidd/adapters/generic_cli/`
- `src/aidd/cli/`
- `tests/adapters/`

Dependencies:

- `W1-E1-S2`

Local tasks:

- `W4-E1-S1-T1` (done) Implement command discovery for the configured generic CLI executable.
- `W4-E1-S1-T2` (done) Capture version or identity information from the discovered CLI.
- `W4-E1-S1-T3` (done) Derive a minimal capability map for the generic adapter from config and probe results.
- `W4-E1-S1-T4` (done) Expose generic-cli probe results in `aidd doctor`.
- `W4-E1-S1-T5` (done) Add probe tests for found binaries, missing binaries, and non-zero version commands.

Exit evidence:

- operators can tell whether the generic adapter is runnable before starting a stage;
- doctor output reports both availability and a minimal capability summary.

#### Slice W4-E1-S2 — stage execution (`planned`)
Goal: run one stage through a generic command adapter.

Primary outputs:

- `src/aidd/adapters/generic_cli/runner.py`
- subprocess streaming and persistence
- adapter execution tests

Touched areas:

- `src/aidd/adapters/generic_cli/`
- `src/aidd/core/`
- `tests/adapters/`

Dependencies:

- `W4-E1-S1`
- `W3-E2-S2`
- `W3-E1-S2`

Local tasks:

- `W4-E1-S2-T1` Implement command assembly from adapter config, stage context, and prompt-pack path.
- `W4-E1-S2-T2` Implement environment-variable injection for workspace, stage, and run metadata.
- `W4-E1-S2-T3` Implement workspace and prompt-pack path exposure for subprocess execution.
- `W4-E1-S2-T4` Implement stdout and stderr streaming to the CLI while the subprocess runs.
- `W4-E1-S2-T5` Persist raw `runtime.log` and basic exit metadata for each attempt.
- `W4-E1-S2-T6` Implement timeout, cancellation, and non-zero exit classification.
- `W4-E1-S2-T7` Add tests for successful runs, timed-out runs, cancelled runs, and non-zero exits.

Exit evidence:

- the generic adapter can execute a stage without hiding native output;
- adapter failures are separated from validator failures in durable metadata.

#### Slice W4-E1-S3 — document handshake and question surfacing (`planned`)
Goal: connect generic subprocess execution to document validation and interview flow.

Primary outputs:

- generic adapter document-handshake helpers
- question detection rules
- integration tests

Touched areas:

- `src/aidd/adapters/generic_cli/`
- `src/aidd/core/`
- `tests/adapters/`

Dependencies:

- `W4-E1-S2`
- `W3-E3-S1`
- `W2-E2-S2`

Local tasks:

- `W4-E1-S3-T1` Implement input-bundle preparation for a stage attempt before subprocess launch.
- `W4-E1-S3-T2` Implement post-run output discovery that finds expected Markdown artifacts in the workspace.
- `W4-E1-S3-T3` Trigger structural validation immediately after output discovery and persist the report path.
- `W4-E1-S3-T4` Detect unresolved questions from `questions.md` and route them into the interview controller.
- `W4-E1-S3-T5` Implement resume behavior after answers are added for a generic-cli stage.
- `W4-E1-S3-T6` Add integration tests for valid output, invalid output, and question-blocked output.

Exit evidence:

- the generic adapter participates in the same document-first orchestration loop as richer adapters;
- question files are handled consistently even without runtime-native question events.

### Epic W4-E2 — `claude-code` adapter (`planned`)
Linked stories: `US-01`, `US-05`, `US-06`, `US-08`

#### Slice W4-E2-S1 — runtime probing (`next`)
Goal: detect Claude Code availability and adapter capability flags.

Primary outputs:

- `src/aidd/adapters/claude_code/probe.py`
- `aidd doctor` integration
- probe tests

Touched areas:

- `src/aidd/adapters/claude_code/`
- `src/aidd/cli/`
- `tests/adapters/`

Dependencies:

- `W1-E1-S2`

Local tasks:

- `W4-E2-S1-T1` (done) Implement Claude Code command discovery for the configured executable name or path.
- `W4-E2-S1-T2` (done) Capture version or identity information from the Claude Code CLI.
- `W4-E2-S1-T3` (done) Detect advertised capability flags that matter to AIDD, such as streaming or non-interactive support.
- `W4-E2-S1-T4` (done) Expose Claude Code probe results and capability flags in `aidd doctor`.
- `W4-E2-S1-T5` (done) Add probe tests for found binaries, missing binaries, and unexpected version output.

Exit evidence:

- operators can verify whether the Claude Code adapter is usable on the current machine;
- the adapter advertises its supported features before first execution.

#### Slice W4-E2-S2 — stage execution and command assembly (`planned`)
Goal: launch Claude Code in a way that keeps the core runtime-agnostic.

Primary outputs:

- `src/aidd/adapters/claude_code/runner.py`
- adapter launch tests

Touched areas:

- `src/aidd/adapters/claude_code/`
- `src/aidd/core/`
- `tests/adapters/`

Dependencies:

- `W4-E2-S1`
- `W3-E2-S2`
- `W3-E1-S2`

Local tasks:

- `W4-E2-S2-T1` Implement Claude Code command assembly from stage brief, workspace path, and prompt-pack inputs.
- `W4-E2-S2-T2` Implement adapter-side mapping of sandbox, permission, and config flags into the launch command.
- `W4-E2-S2-T3` Implement environment and working-directory setup for Claude Code runs.
- `W4-E2-S2-T4` Implement timeout and cancellation handling that maps process outcomes into adapter statuses.
- `W4-E2-S2-T5` Add execution tests for a dry-run or fixture command path that covers launch, cancel, and timeout handling.

Exit evidence:

- the Claude Code adapter can be launched repeatedly with deterministic inputs;
- launch configuration stays isolated inside the adapter boundary.

#### Slice W4-E2-S3 — log streaming and event normalization (`planned`)
Goal: preserve native Claude Code output while also producing normalized run artifacts.

Primary outputs:

- log streaming helpers
- `events.jsonl` normalization
- log tests

Touched areas:

- `src/aidd/adapters/claude_code/`
- `src/aidd/core/`
- `tests/adapters/`

Dependencies:

- `W4-E2-S2`
- `W3-E1-S2`

Local tasks:

- `W4-E2-S3-T1` Stream raw Claude Code stdout and stderr to the operator CLI in real time.
- `W4-E2-S3-T2` Persist a full `runtime.log` that matches the raw streamed output as closely as possible.
- `W4-E2-S3-T3` Normalize any machine-readable Claude Code events into a durable `events.jsonl` artifact when available.
- `W4-E2-S3-T4` Implement exit classification that distinguishes adapter, runtime, and user-cancelled outcomes.
- `W4-E2-S3-T5` Add tests that verify raw-log persistence, event normalization, and exit classification.

Exit evidence:

- operators can see native runtime logs during execution;
- evals can consume normalized events without losing the raw source log.

#### Slice W4-E2-S4 — question surfacing and resume (`planned`)
Goal: map runtime-native pauses or questions into the AIDD interview flow.

Primary outputs:

- question-event mapping for Claude Code
- resume helpers
- integration tests

Touched areas:

- `src/aidd/adapters/claude_code/`
- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/adapters/`

Dependencies:

- `W4-E2-S3`
- `W3-E3-S1`

Local tasks:

- `W4-E2-S4-T1` Detect Claude Code question or pause events when the runtime exposes them.
- `W4-E2-S4-T2` Fall back to file-based unresolved-question detection when runtime-native events are absent.
- `W4-E2-S4-T3` Persist surfaced questions into the standard `questions.md` artifact and stage metadata.
- `W4-E2-S4-T4` Implement adapter-side resume behavior after the operator provides answers.
- `W4-E2-S4-T5` Add tests for runtime-native questions, file-based questions, and resume-after-answer behavior.

Exit evidence:

- the Claude Code adapter enters the same interview loop as the generic adapter;
- unanswered questions block the stage instead of disappearing into runtime logs.

### Epic W4-E3 — operator CLI experience (`planned`)
Linked stories: `US-05`, `US-06`, `US-09`

#### Slice W4-E3-S1 — run summaries (`planned`)
Goal: give the operator a useful end-of-run summary.

Primary outputs:

- CLI summary formatting
- summary tests

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/`
- `tests/cli/`

Dependencies:

- `W3-E2-S2`
- `W2-E2-S2`

Local tasks:

- `W4-E3-S1-T1` Implement stage-result summaries that show final state, runtime, and attempt count.
- `W4-E3-S1-T2` Implement validator-outcome summaries that show pass/fail counts and report paths.
- `W4-E3-S1-T3` Implement artifact path summaries for logs, documents, and repair outputs.
- `W4-E3-S1-T4` Add CLI tests for success, blocked, repair-needed, and failed summaries.

Exit evidence:

- a completed run leaves the operator with a direct path to the important artifacts;
- summary output is consistent across adapters.

#### Slice W4-E3-S2 — live log follow mode (`planned`)
Goal: make long-running stages observable without leaving the CLI.

Primary outputs:

- CLI follow mode
- follow-mode tests

Touched areas:

- `src/aidd/cli/`
- `src/aidd/adapters/`
- `tests/cli/`

Dependencies:

- `W4-E1-S2` or `W4-E2-S3`

Local tasks:

- `W4-E3-S2-T1` Add a CLI flag that enables explicit live-log follow behavior for stage runs.
- `W4-E3-S2-T2` Prefix streamed runtime lines with adapter and stage context when multiple streams are possible.
- `W4-E3-S2-T3` Add tests for follow-mode formatting and graceful shutdown on process end or cancellation.

Exit evidence:

- operators can follow runtime-native logs without opening artifact files manually.

#### Slice W4-E3-S3 — run inspection commands (`planned`)
Goal: make stored artifacts easy to inspect after execution.

Primary outputs:

- `aidd run show`
- `aidd run logs`
- `aidd run artifacts`
- CLI tests

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/`
- `tests/cli/`

Dependencies:

- `W3-E1-S3`
- `W3-E1-S2`

Local tasks:

- `W4-E3-S3-T1` Add a command that prints the stored metadata for a run and its stages.
- `W4-E3-S3-T2` Add a command that prints or tails the persisted runtime log for a selected attempt.
- `W4-E3-S3-T3` Add a command that lists document and report artifact paths for a selected attempt.
- `W4-E3-S3-T4` Add CLI tests for missing runs, valid runs, and ambiguous run selection.

Exit evidence:

- stored run artifacts are inspectable without manual filesystem traversal.

---

## Wave 5 — harness, eval, and log analysis (`planned`)

### Epic W5-E1 — scenario runner (`planned`)
Linked stories: `US-07`, `US-11`, `US-12`

#### Slice W5-E1-S1 — scenario manifest loader (`planned`)
Goal: load live and local eval scenarios from durable manifest files.

Primary outputs:

- `src/aidd/harness/scenario_loader.py`
- scenario model tests

Touched areas:

- `src/aidd/harness/`
- `harness/scenarios/`
- `tests/harness/`

Dependencies:

- `W1-E1-S1`

Local tasks:

- `W5-E1-S1-T1` Define the Python model for scenario manifests, including repo source, setup steps, run config, and verification steps.
- `W5-E1-S1-T2` Implement YAML manifest loading with stable validation errors for missing keys and invalid values.
- `W5-E1-S1-T3` Implement variable substitution for runtime id, workspace path, and scenario-scoped parameters.
- `W5-E1-S1-T4` Add tests for valid manifests, missing fields, and parameter substitution.

Exit evidence:

- scenarios can be loaded without hardcoded repo-specific logic;
- invalid manifests fail before repository preparation begins.

#### Slice W5-E1-S2 — repository preparation (`planned`)
Goal: prepare a clean repository workspace for each scenario run.

Primary outputs:

- `src/aidd/harness/repo_prep.py`
- repo-prep tests

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`

Dependencies:

- `W5-E1-S1`

Local tasks:

- `W5-E1-S2-T1` Implement repository clone or fetch logic for scenario targets.
- `W5-E1-S2-T2` Implement revision pinning so a scenario runs against a stable commit or tag.
- `W5-E1-S2-T3` Implement clean working-copy preparation for each scenario invocation.
- `W5-E1-S2-T4` Implement cleanup rules for previous scenario artifacts and transient files.
- `W5-E1-S2-T5` Add tests for first clone, repeated runs, invalid revisions, and dirty-workspace cleanup.

Exit evidence:

- every scenario run starts from a deterministic repository state;
- repo preparation failures are distinguishable from AIDD execution failures.

#### Slice W5-E1-S3 — setup, run, and verification execution (`planned`)
Goal: execute the full harness lifecycle for one scenario.

Primary outputs:

- `src/aidd/harness/runner.py`
- step-execution tests

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`

Dependencies:

- `W5-E1-S2`
- `W3-E2-S2`
- `W4-E1-S2` or `W4-E2-S2`

Local tasks:

- `W5-E1-S3-T1` Implement setup-step execution before AIDD is invoked.
- `W5-E1-S3-T2` Implement AIDD invocation with runtime, scenario, and work-item parameters.
- `W5-E1-S3-T3` Implement verification-step execution after the AIDD run completes.
- `W5-E1-S3-T4` Capture durations, exit codes, and command transcripts for setup, run, and verification steps.
- `W5-E1-S3-T5` Implement teardown handling that runs even after a failed scenario.
- `W5-E1-S3-T6` Add integration tests for passing scenarios, failing setup steps, failing verification steps, and interrupted runs.

Exit evidence:

- a single harness command can prepare, run, verify, and archive one scenario;
- step boundaries remain visible in logs and metadata.

#### Slice W5-E1-S4 — scenario result bundle (`planned`)
Goal: persist a stable artifact set for each scenario run.

Primary outputs:

- `src/aidd/harness/result_bundle.py`
- result-bundle tests

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`

Dependencies:

- `W5-E1-S3`
- `W3-E1-S2`

Local tasks:

- `W5-E1-S4-T1` Define the scenario run directory layout and stable artifact names.
- `W5-E1-S4-T2` Persist harness metadata, command transcripts, and references to AIDD run artifacts.
- `W5-E1-S4-T3` Copy or link validator reports, runtime logs, and verdict files into the bundle.
- `W5-E1-S4-T4` Add tests that verify bundle completeness for pass, fail, and blocked runs.

Exit evidence:

- every scenario run leaves behind one self-contained artifact bundle.

### Epic W5-E2 — graders and verdicts (`planned`)
Linked stories: `US-07`, `US-12`

#### Slice W5-E2-S1 — verdict writing (`planned`)
Goal: write a durable verdict artifact for each scenario run.

Primary outputs:

- `src/aidd/evals/verdicts.py`
- verdict tests

Touched areas:

- `src/aidd/evals/`
- `tests/evals/`

Dependencies:

- `W5-E1-S4`

Local tasks:

- `W5-E2-S1-T1` Define the verdict model and Markdown artifact layout.
- `W5-E2-S1-T2` Map harness outcomes into `pass`, `fail`, `blocked`, and `infra-fail` verdict states.
- `W5-E2-S1-T3` Record linked artifacts, first-failure notes, and verification summaries in the verdict.
- `W5-E2-S1-T4` Add tests for verdict generation across each terminal outcome.

Exit evidence:

- every scenario run produces one durable verdict artifact with traceable evidence links.

#### Slice W5-E2-S2 — log analysis (`planned`)
Goal: classify first failure boundaries from logs.

Primary outputs:

- `src/aidd/evals/log_analysis.py`
- failure-taxonomy tests

Touched areas:

- `src/aidd/evals/`
- `tests/evals/`

Dependencies:

- `W5-E1-S4`
- `W4-E2-S3`

Local tasks:

- `W5-E2-S2-T1` Implement parsing of `runtime.log` into coarse runtime events.
- `W5-E2-S2-T2` Implement parsing of `events.jsonl` when a runtime exposes normalized events.
- `W5-E2-S2-T3` Implement parsing of `validator-report.md` and stage-result metadata for validation failures.
- `W5-E2-S2-T4` Implement the failure taxonomy that separates environment, adapter, runtime, validation, and scenario-verification failures.
- `W5-E2-S2-T5` Implement first-failure-boundary selection from competing log signals.
- `W5-E2-S2-T6` Add regression tests for ambiguous failures, multi-error runs, and empty-log cases.

Exit evidence:

- evals can explain where a run failed instead of only reporting that it failed.

#### Slice W5-E2-S3 — eval summary reports (`planned`)
Goal: aggregate scenario verdicts into operator-friendly reports.

Primary outputs:

- `src/aidd/evals/reporting.py`
- report tests

Touched areas:

- `src/aidd/evals/`
- `src/aidd/cli/`
- `tests/evals/`

Dependencies:

- `W5-E2-S1`
- `W5-E2-S2`

Local tasks:

- `W5-E2-S3-T1` Implement per-scenario summary rows with verdict, runtime, duration, and failure boundary.
- `W5-E2-S3-T2` Implement runtime-level summary aggregation across many scenarios.
- `W5-E2-S3-T3` Render a Markdown summary report suitable for CI artifacts.
- `W5-E2-S3-T4` Add a CLI summary command that prints the latest eval report.
- `W5-E2-S3-T5` Add tests for empty eval sets, mixed outcomes, and repeated scenario runs.

Exit evidence:

- operators can compare many scenario runs without opening each artifact bundle individually.

### Epic W5-E3 — live E2E lanes (`planned`)
Linked stories: `US-07`, `US-11`, `US-12`

#### Slice W5-E3-S1 — Typer smoke lane (`planned`)
Goal: make one minimal Typer scenario pass under the harness.

Primary outputs:

- Typer scenario manifest
- Typer harness notes
- Typer smoke verification

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`
- `tests/harness/` or integration fixtures

Dependencies:

- `W5-E1-S3`
- `W5-E2-S1`

Local tasks:

- `W5-E3-S1-T1` Pin the Typer repository revision and record the target scenario objective.
- `W5-E3-S1-T2` Define setup steps and AIDD invocation parameters for the Typer smoke scenario.
- `W5-E3-S1-T3` Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S1-T4` Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- Typer smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S2 — HTTPX smoke lane (`planned`)
Goal: make one minimal HTTPX scenario pass under the harness.

Primary outputs:

- HTTPX scenario manifest
- HTTPX smoke verification

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`

Dependencies:

- `W5-E1-S3`
- `W5-E2-S1`

Local tasks:

- `W5-E3-S2-T1` Pin the HTTPX repository revision and record the target scenario objective.
- `W5-E3-S2-T2` Define setup steps and AIDD invocation parameters for the HTTPX smoke scenario.
- `W5-E3-S2-T3` Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S2-T4` Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- HTTPX smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S3 — sqlite-utils smoke lane (`planned`)
Goal: make one minimal sqlite-utils scenario pass under the harness.

Primary outputs:

- sqlite-utils scenario manifest
- sqlite-utils smoke verification

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`

Dependencies:

- `W5-E1-S3`
- `W5-E2-S1`

Local tasks:

- `W5-E3-S3-T1` Pin the sqlite-utils repository revision and record the target scenario objective.
- `W5-E3-S3-T2` Define setup steps and AIDD invocation parameters for the sqlite-utils smoke scenario.
- `W5-E3-S3-T3` Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S3-T4` Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- sqlite-utils smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S4 — Hono smoke lane (`planned`)
Goal: make one minimal Hono scenario pass under the harness.

Primary outputs:

- Hono scenario manifest
- Hono smoke verification

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`

Dependencies:

- `W5-E1-S3`
- `W5-E2-S1`

Local tasks:

- `W5-E3-S4-T1` Pin the Hono repository revision and record the target scenario objective.
- `W5-E3-S4-T2` Define setup steps and AIDD invocation parameters for the Hono smoke scenario.
- `W5-E3-S4-T3` Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S4-T4` Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- Hono smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S5 — sqlite-utils interview lane (`planned`)
Goal: prove user-question handling in a live repository scenario.

Primary outputs:

- sqlite-utils interview scenario manifest
- interview reference bundle

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`

Dependencies:

- `W3-E3-S1`
- `W5-E1-S3`

Local tasks:

- `W5-E3-S5-T1` Define the sqlite-utils scenario conditions that force at least one user question.
- `W5-E3-S5-T2` Define the operator answer file or CLI-answer flow used by the scenario.
- `W5-E3-S5-T3` Define verification steps that prove the run blocked, resumed, and completed correctly.
- `W5-E3-S5-T4` Run the scenario once end to end and archive the reference blocked-and-resumed bundle.

Exit evidence:

- one live scenario proves that the AIDD interview loop works outside synthetic fixtures.

#### Slice W5-E3-S6 — Hono interview lane (`planned`)
Goal: prove user-question handling in a second live repository scenario.

Primary outputs:

- Hono interview scenario manifest
- interview reference bundle

Touched areas:

- `harness/scenarios/live/`
- `docs/e2e/`

Dependencies:

- `W3-E3-S1`
- `W5-E1-S3`

Local tasks:

- `W5-E3-S6-T1` Define the Hono scenario conditions that force at least one user question.
- `W5-E3-S6-T2` Define the operator answer file or CLI-answer flow used by the scenario.
- `W5-E3-S6-T3` Define verification steps that prove the run blocked, resumed, and completed correctly.
- `W5-E3-S6-T4` Run the scenario once end to end and archive the reference blocked-and-resumed bundle.

Exit evidence:

- question handling works across more than one public repository and stack.

---

## Wave 6 — canonical stage packs (`planned`)

### Epic W6-E1 — strategy stages (`planned`)
Linked stories: `US-02`, `US-03`, `US-05`

#### Slice W6-E1-S1 — `idea` stage pack (`planned`)
Goal: make the `idea` stage runnable with a real prompt pack, validator, and fixtures.

Primary outputs:

- `prompt-packs/idea/`
- stage-specific validator rules
- `contracts/examples/idea/`

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S2`
- `W2-E2-S3`
- `W4-E1-S3` or `W4-E2-S4`

Local tasks:

- `W6-E1-S1-T1` Write the `idea` base prompt that explains the stage objective and required outputs.
- `W6-E1-S1-T2` Write the `idea` repair prompt that maps validator failures into concrete fixes.
- `W6-E1-S1-T3` Implement `idea`-specific semantic validators.
- `W6-E1-S1-T4` Add valid and invalid `idea` fixtures for regression tests.
- `W6-E1-S1-T5` Add unit tests that execute the `idea` validator against the fixtures.
- `W6-E1-S1-T6` Run one smoke execution of `idea` through an adapter and archive the output bundle.

Exit evidence:

- the `idea` stage is more than a contract file; it is runnable, validated, and repairable.

#### Slice W6-E1-S2 — `research` stage pack (`planned`)
Goal: make the `research` stage runnable with evidence-aware validation.

Primary outputs:

- `prompt-packs/research/`
- stage-specific validator rules
- `contracts/examples/research/`

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S3`
- `W2-E2-S3`
- `W4-E1-S3` or `W4-E2-S4`

Local tasks:

- `W6-E1-S2-T1` Write the `research` base prompt with explicit evidence, citation, and uncertainty guidance.
- `W6-E1-S2-T2` Write the `research` repair prompt for unsupported claims and missing evidence.
- `W6-E1-S2-T3` Implement `research`-specific semantic validators.
- `W6-E1-S2-T4` Add valid and invalid `research` fixtures, including missing-source and unresolved-question cases.
- `W6-E1-S2-T5` Add unit tests that execute the `research` validator against the fixtures.
- `W6-E1-S2-T6` Run one smoke execution of `research` through an adapter and archive the output bundle.

Exit evidence:

- `research` can produce auditable outputs and fail predictably when evidence is weak.

#### Slice W6-E1-S3 — `plan` stage pack (`planned`)
Goal: make the `plan` stage runnable with planning-specific validation and harness coverage.

Primary outputs:

- `prompt-packs/plan/`
- stage-specific validator rules
- `contracts/examples/plan/`

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`
- `tests/harness/` or scenario fixtures

Dependencies:

- `W2-E1-S4`
- `W2-E2-S3`
- `W5-E1-S3`

Local tasks:

- `W6-E1-S3-T1` Write the `plan` base prompt with milestone, dependency, and verification expectations.
- `W6-E1-S3-T2` Write the `plan` repair prompt for vague sequencing, missing risks, or unreviewable scope.
- `W6-E1-S3-T3` Implement `plan`-specific semantic validators.
- `W6-E1-S3-T4` Add valid and invalid `plan` fixtures.
- `W6-E1-S3-T5` Add unit tests that execute the `plan` validator against the fixtures.
- `W6-E1-S3-T6` Add one harness smoke scenario that exercises `plan` and archives the resulting artifacts.

Exit evidence:

- `plan` is fully wired into validation and harness execution.

### Epic W6-E2 — delivery stages (`planned`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-05`

#### Slice W6-E2-S1 — `review-spec` stage pack (`planned`)
Goal: make `review-spec` runnable with actionable review outputs.

Primary outputs:

- `prompt-packs/review-spec/`
- validators and fixtures

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S5`
- `W2-E2-S3`

Local tasks:

- `W6-E2-S1-T1` Write the `review-spec` base prompt.
- `W6-E2-S1-T2` Write the `review-spec` repair prompt.
- `W6-E2-S1-T3` Implement `review-spec` semantic validators.
- `W6-E2-S1-T4` Add valid and invalid `review-spec` fixtures.
- `W6-E2-S1-T5` Add unit tests for `review-spec` validation.
- `W6-E2-S1-T6` Run one smoke execution of `review-spec` and archive the artifacts.

Exit evidence:

- `review-spec` can block downstream work with durable, validated review findings.

#### Slice W6-E2-S2 — `tasklist` stage pack (`planned`)
Goal: make `tasklist` runnable with decomposition-aware validation.

Primary outputs:

- `prompt-packs/tasklist/`
- validators and fixtures

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S6`
- `W2-E2-S3`

Local tasks:

- `W6-E2-S2-T1` Write the `tasklist` base prompt.
- `W6-E2-S2-T2` Write the `tasklist` repair prompt.
- `W6-E2-S2-T3` Implement `tasklist` semantic validators for granularity and dependency clarity.
- `W6-E2-S2-T4` Add valid and invalid `tasklist` fixtures.
- `W6-E2-S2-T5` Add unit tests for `tasklist` validation.
- `W6-E2-S2-T6` Run one smoke execution of `tasklist` and archive the artifacts.

Exit evidence:

- `tasklist` produces reviewable execution units and fails predictably when decomposition is poor.

#### Slice W6-E2-S3 — `implement` stage pack (`planned`)
Goal: make `implement` runnable with repair-loop expectations and log-aware validation.

Primary outputs:

- `prompt-packs/implement/`
- validators and fixtures
- harness coverage for repair

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`
- `tests/harness/`

Dependencies:

- `W2-E1-S7`
- `W2-E2-S3`
- `W3-E3-S2`
- `W5-E1-S3`

Local tasks:

- `W6-E2-S3-T1` Write the `implement` base prompt with edit-scope, verification, and summary expectations.
- `W6-E2-S3-T2` Write the `implement` repair prompt for validator-driven reruns.
- `W6-E2-S3-T3` Implement `implement` semantic validators.
- `W6-E2-S3-T4` Add valid and invalid `implement` fixtures, including no-op and incomplete-verification cases.
- `W6-E2-S3-T5` Add unit tests for `implement` validation.
- `W6-E2-S3-T6` Add one harness or integration scenario that proves the `implement` repair loop end to end.

Exit evidence:

- `implement` can fail, repair, and succeed through the same document-first loop.

### Epic W6-E3 — assurance stages (`planned`)
Linked stories: `US-03`, `US-04`, `US-07`

#### Slice W6-E3-S1 — `review` stage pack (`planned`)
Goal: make `review` runnable with severity-aware findings and approval states.

Primary outputs:

- `prompt-packs/review/`
- validators and fixtures

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S8`
- `W2-E2-S3`

Local tasks:

- `W6-E3-S1-T1` Write the `review` base prompt.
- `W6-E3-S1-T2` Write the `review` repair prompt.
- `W6-E3-S1-T3` Implement `review` semantic validators.
- `W6-E3-S1-T4` Add valid and invalid `review` fixtures.
- `W6-E3-S1-T5` Add unit tests for `review` validation.
- `W6-E3-S1-T6` Run one smoke execution of `review` and archive the artifacts.

Exit evidence:

- `review` findings are durable, severity-labeled, and validator-backed.

#### Slice W6-E3-S2 — `qa` stage pack (`planned`)
Goal: make `qa` runnable with eval-ready verdict artifacts.

Primary outputs:

- `prompt-packs/qa/`
- validators and fixtures
- verdict integration coverage

Touched areas:

- `prompt-packs/`
- `src/aidd/validators/`
- `src/aidd/evals/`
- `contracts/examples/`

Dependencies:

- `W2-E1-S9`
- `W2-E2-S3`
- `W5-E2-S1`

Local tasks:

- `W6-E3-S2-T1` Write the `qa` base prompt.
- `W6-E3-S2-T2` Write the `qa` repair prompt.
- `W6-E3-S2-T3` Implement `qa` semantic validators.
- `W6-E3-S2-T4` Add valid and invalid `qa` fixtures.
- `W6-E3-S2-T5` Add unit tests for `qa` validation.
- `W6-E3-S2-T6` Add one integration scenario that converts `qa` output into an eval verdict artifact.

Exit evidence:

- `qa` can feed directly into harness verdict writing with auditable evidence links.

---

## Wave 7 — runtime widening and release hardening (`later`)

### Epic W7-E1 — `codex` adapter (`later`)
Linked stories: `US-01`, `US-08`, `US-12`, `US-13`

#### Slice W7-E1-S1 — runtime probing (`later`)
Goal: detect Codex CLI availability and supported features.

Primary outputs:

- `src/aidd/adapters/codex/probe.py`
- doctor integration
- tests

Touched areas:

- `src/aidd/adapters/codex/`
- `src/aidd/cli/`
- `tests/adapters/`

Dependencies:

- `W4-E2-S1`

Local tasks:

- `W7-E1-S1-T1` Implement Codex command discovery.
- `W7-E1-S1-T2` Capture Codex version or identity output.
- `W7-E1-S1-T3` Derive Codex capability flags relevant to AIDD.
- `W7-E1-S1-T4` Expose Codex probe results in `aidd doctor`.
- `W7-E1-S1-T5` Add probe tests for found, missing, and malformed-version cases.

Exit evidence:

- the Codex adapter can be discovered and reported without execution support yet being complete.

#### Slice W7-E1-S2 — stage execution and logs (`later`)
Goal: implement document-first execution for Codex.

Primary outputs:

- Codex runner
- log persistence
- execution tests

Touched areas:

- `src/aidd/adapters/codex/`
- `tests/adapters/`

Dependencies:

- `W7-E1-S1`
- `W3-E2-S2`

Local tasks:

- `W7-E1-S2-T1` Implement Codex command assembly from stage inputs.
- `W7-E1-S2-T2` Implement workspace and environment setup for Codex runs.
- `W7-E1-S2-T3` Implement raw log streaming and `runtime.log` persistence.
- `W7-E1-S2-T4` Implement exit classification, timeout handling, and cancellation handling.
- `W7-E1-S2-T5` Add execution tests for success, failure, timeout, and cancellation paths.

Exit evidence:

- Codex participates in the same execution contract as the first-wave adapters.

#### Slice W7-E1-S3 — parity scenarios (`later`)
Goal: prove Codex parity on selected harness scenarios.

Primary outputs:

- parity scenario matrix
- Codex reference bundles

Touched areas:

- `harness/scenarios/`
- `docs/e2e/`

Dependencies:

- `W7-E1-S2`
- `W5-E3-S1` through `W5-E3-S6`

Local tasks:

- `W7-E1-S3-T1` Select the minimum parity scenario set for Codex.
- `W7-E1-S3-T2` Run Codex on the smoke lane and capture reference bundles.
- `W7-E1-S3-T3` Run Codex on at least one interview lane and capture reference bundles.
- `W7-E1-S3-T4` Document known parity gaps and adapter-specific limitations.

Exit evidence:

- Codex can be compared to Claude Code and generic-cli on shared scenarios.

### Epic W7-E2 — `opencode` adapter (`later`)
Linked stories: `US-01`, `US-08`, `US-12`

#### Slice W7-E2-S1 — runtime probing (`later`)
Goal: detect OpenCode CLI availability and supported features.

Primary outputs:

- `src/aidd/adapters/opencode/probe.py`
- doctor integration
- tests

Touched areas:

- `src/aidd/adapters/opencode/`
- `src/aidd/cli/`
- `tests/adapters/`

Dependencies:

- `W4-E2-S1`

Local tasks:

- `W7-E2-S1-T1` Implement OpenCode command discovery.
- `W7-E2-S1-T2` Capture OpenCode version or identity output.
- `W7-E2-S1-T3` Derive OpenCode capability flags relevant to AIDD.
- `W7-E2-S1-T4` Expose OpenCode probe results in `aidd doctor`.
- `W7-E2-S1-T5` Add probe tests for found, missing, and malformed-version cases.

Exit evidence:

- the OpenCode adapter can be discovered and reported before execution support is added.

#### Slice W7-E2-S2 — stage execution and logs (`later`)
Goal: implement document-first execution for OpenCode.

Primary outputs:

- OpenCode runner
- log persistence
- execution tests

Touched areas:

- `src/aidd/adapters/opencode/`
- `tests/adapters/`

Dependencies:

- `W7-E2-S1`
- `W3-E2-S2`

Local tasks:

- `W7-E2-S2-T1` Implement OpenCode command assembly from stage inputs.
- `W7-E2-S2-T2` Implement workspace and environment setup for OpenCode runs.
- `W7-E2-S2-T3` Implement raw log streaming and `runtime.log` persistence.
- `W7-E2-S2-T4` Implement exit classification, timeout handling, and cancellation handling.
- `W7-E2-S2-T5` Add execution tests for success, failure, timeout, and cancellation paths.

Exit evidence:

- OpenCode participates in the same execution contract as the first-wave adapters.

#### Slice W7-E2-S3 — parity scenarios (`later`)
Goal: prove OpenCode parity on selected harness scenarios.

Primary outputs:

- parity scenario matrix
- OpenCode reference bundles

Touched areas:

- `harness/scenarios/`
- `docs/e2e/`

Dependencies:

- `W7-E2-S2`
- `W5-E3-S1` through `W5-E3-S6`

Local tasks:

- `W7-E2-S3-T1` Select the minimum parity scenario set for OpenCode.
- `W7-E2-S3-T2` Run OpenCode on the smoke lane and capture reference bundles.
- `W7-E2-S3-T3` Run OpenCode on at least one interview lane and capture reference bundles.
- `W7-E2-S3-T4` Document known parity gaps and adapter-specific limitations.

Exit evidence:

- OpenCode can be compared to Claude Code, Codex, and generic-cli on shared scenarios.

### Epic W7-E3 — public release hardening (`later`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W7-E3-S1 — operator handbook (`later`)
Goal: document how to install, configure, and operate AIDD in real environments.

Primary outputs:

- operator handbook
- troubleshooting guide
- support notes

Touched areas:

- `docs/`
- `README.md`

Dependencies:

- `W4-E3-S3`
- `W5-E2-S3`

Local tasks:

- `W7-E3-S1-T1` Write the operator handbook for installation, configuration, and first run.
- `W7-E3-S1-T2` Write the troubleshooting guide for runtime, validator, and harness failures.
- `W7-E3-S1-T3` Write the support policy and issue-reporting instructions.
- `W7-E3-S1-T4` Add links from `README.md` and `CONTRIBUTING.md` into the new operator docs.

Exit evidence:

- a new operator can install and diagnose AIDD without reading the source tree.

#### Slice W7-E3-S2 — release operations (`later`)
Goal: finalize repeatable packaging and publishing operations.

Primary outputs:

- release checklist
- packaging workflow updates
- distribution docs

Touched areas:

- `.github/workflows/`
- `README.md`
- packaging config

Dependencies:

- `W1-E2-S2`

Local tasks:

- `W7-E3-S2-T1` Finalize PyPI publishing configuration and release tagging rules.
- `W7-E3-S2-T2` Finalize container publishing configuration and image tagging rules.
- `W7-E3-S2-T3` Add a human-readable release checklist that covers package, image, and changelog steps.
- `W7-E3-S2-T4` Add release-verification steps that prove the published CLI can still run `aidd doctor`.

Exit evidence:

- releases can be published and verified through a documented, repeatable path.

#### Slice W7-E3-S3 — compatibility and maintenance policy (`later`)
Goal: define how AIDD supports runtimes, Python versions, and scenario baselines over time.

Primary outputs:

- compatibility matrix
- maintenance policy
- deprecation notes

Touched areas:

- `docs/`
- `README.md`
- `AGENTS.md`

Dependencies:

- `W5-E3`
- `W7-E1`
- `W7-E2`

Local tasks:

- `W7-E3-S3-T1` Define the supported Python-version window and platform support policy.
- `W7-E3-S3-T2` Define runtime-support tiers for generic-cli, Claude Code, Codex, and OpenCode.
- `W7-E3-S3-T3` Define the policy for refreshing live E2E scenario baselines and pinned revisions.
- `W7-E3-S3-T4` Define deprecation rules for contract changes, adapters, and scenario manifests.

Exit evidence:

- contributors and operators know what support guarantees AIDD actually makes.
