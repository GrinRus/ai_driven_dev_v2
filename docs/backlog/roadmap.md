# Roadmap

This file is the canonical implementation plan for AIDD.

## Status vocabulary

- `done` — completed in the repo
- `blocked` — accepted but currently stopped by an explicit dependency gap
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
Linked stories: `US-01`, `US-02`, `US-07`, `US-09`, `US-10`

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
Linked stories: `US-10`

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
Linked stories: `US-07`

#### Slice W0-E3-S1 — repository selection (`done`)
Goal: define a first public-repo live E2E set.

Local tasks:

- `W0-E3-S1-T1` Select public repositories.
- `W0-E3-S1-T2` Define starter scenarios.
- `W0-E3-S1-T3` Add starter scenario manifests.

---

## Wave 1 — package, local developer loop, and release scaffolding (`done`)

### Epic W1-E1 — package and CLI scaffold (`done`)
Linked stories: `US-09`

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
Linked stories: `US-09`, `US-10`

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

## Wave 2 — document contracts and validator foundations (`done`)

### Epic W2-E1 — common and stage-specific contracts (`done`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-05`

#### Slice W2-E1-S1 — normative common document templates (`done`)
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

#### Slice W2-E1-S2 — `idea` stage contract (`done`)
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

- `W2-E1-S2-T1` (done) Define the required input documents and optional context documents for the `idea` stage.
- `W2-E1-S2-T2` (done) Define the required output documents and exit states for the `idea` stage.
- `W2-E1-S2-T3` (done) Define stage-specific validation rules, including minimum completeness and no-placeholder requirements.
- `W2-E1-S2-T4` (done) Define when `idea` may ask the user questions and which questions block progression.
- `W2-E1-S2-T5` (done) Create the `idea` prompt-pack scaffold with system, task, and repair instructions.
- `W2-E1-S2-T6` (done) Add one worked `idea` example bundle that matches the contract and prompt pack.

Exit evidence:

- `idea` can be run document-first with explicit input/output requirements;
- a validator can determine whether an `idea` result is acceptable without runtime-specific knowledge.

#### Slice W2-E1-S3 — `research` stage contract (`done`)
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

- `W2-E1-S3-T1` (done) Define the required `research` input bundle, including idea outputs and repository context.
- `W2-E1-S3-T2` (done) Define the required `research` outputs, citation expectations, and evidence trace sections.
- `W2-E1-S3-T3` (done) Define `research` validator rules for source grounding, uncertainty notes, and stale-fact handling.
- `W2-E1-S3-T4` (done) Define `research` interview triggers for missing constraints, target repos, or ambiguous goals.
- `W2-E1-S3-T5` (done) Create the `research` prompt-pack scaffold, including explicit evidence and question-generation guidance.
- `W2-E1-S3-T6` (done) Add one worked `research` example bundle that includes unresolved-question and answered-question variants.

Exit evidence:

- `research` inputs and outputs are explicit enough for any adapter to run the stage;
- validators can reject unsupported assertions and incomplete research bundles.

#### Slice W2-E1-S4 — `plan` stage contract (`done`)
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

- `W2-E1-S4-T1` (done) Define the required `plan` input bundle and the dependency on `research` artifacts.
- `W2-E1-S4-T2` (done) Define the required `plan` outputs, including milestones, risks, and verification notes.
- `W2-E1-S4-T3` (done) Define validator rules for plan completeness, sequencing clarity, and user-approval readiness.
- `W2-E1-S4-T4` (done) Define interview triggers for unresolved scope, sequencing disputes, or missing acceptance signals.
- `W2-E1-S4-T5` (done) Create the `plan` prompt-pack scaffold with explicit roadmap-style reasoning rules.
- `W2-E1-S4-T6` (done) Add one worked `plan` example bundle with a valid output and a validator-failing output.

Exit evidence:

- the `plan` stage can be evaluated from Markdown artifacts alone;
- validators can distinguish a reviewable plan from a vague or unsafely broad one.

#### Slice W2-E1-S5 — `review-spec` stage contract (`done`)
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

- `W2-E1-S5-T1` (done) Define the required `review-spec` inputs, especially the plan artifact and review context.
- `W2-E1-S5-T2` (done) Define the required `review-spec` outputs, including issue lists, recommendation summaries, and readiness states.
- `W2-E1-S5-T3` (done) Define validator rules for issue quality, actionable recommendations, and explicit sign-off status.
- `W2-E1-S5-T4` (done) Define interview triggers for contradictory constraints or missing baseline assumptions.
- `W2-E1-S5-T5` (done) Create the `review-spec` prompt-pack scaffold.
- `W2-E1-S5-T6` (done) Add one worked `review-spec` example bundle.

Exit evidence:

- the `review-spec` stage can block downstream work with durable review artifacts;
- validators can distinguish actionable spec review from shallow commentary.

#### Slice W2-E1-S6 — `tasklist` stage contract (`done`)
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

- `W2-E1-S6-T1` (done) Define the required `tasklist` inputs, including approved plan and spec-review results.
- `W2-E1-S6-T2` (done) Define the required `tasklist` outputs, including task granularity, dependencies, and verification notes.
- `W2-E1-S6-T3` (done) Define validator rules for task independence, ordering clarity, and reviewability.
- `W2-E1-S6-T4` (done) Define interview triggers for unresolved sequencing or staffing assumptions.
- `W2-E1-S6-T5` (done) Create the `tasklist` prompt-pack scaffold.
- `W2-E1-S6-T6` (done) Add one worked `tasklist` example bundle.

Exit evidence:

- `tasklist` produces durable execution units rather than vague bullet lists;
- validators can reject oversized or ambiguous task decompositions.

#### Slice W2-E1-S7 — `implement` stage contract (`done`)
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

- `W2-E1-S7-T1` (done) Define the required `implement` inputs, including task selection, repository state, and allowed write scope.
- `W2-E1-S7-T2` (done) Define the required `implement` outputs, including change summary, touched files, and verification notes.
- `W2-E1-S7-T3` (done) Define validator rules for missing diffs, unverifiable claims, and incomplete execution summaries.
- `W2-E1-S7-T4` (done) Define repair expectations for invalid implementation runs and no-op outputs.
- `W2-E1-S7-T5` (done) Create the `implement` prompt-pack scaffold with explicit edit and verification guidance.
- `W2-E1-S7-T6` (done) Add one worked `implement` example bundle with both success and repair-needed variants.

Exit evidence:

- `implement` has a contract that does not rely on any one runtime's native schema;
- validators can force repair when execution claims are unsupported by artifacts.

#### Slice W2-E1-S8 — `review` stage contract (`done`)
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

- `W2-E1-S8-T1` (done) Define the required `review` inputs, including implementation output, diff context, and acceptance criteria.
- `W2-E1-S8-T2` (done) Define the required `review` outputs, including findings, severity, and approval status.
- `W2-E1-S8-T3` (done) Define validator rules for unsupported findings, missing severity labels, and absent disposition.
- `W2-E1-S8-T4` (done) Define interview triggers for contradictory instructions or missing review baseline.
- `W2-E1-S8-T5` (done) Create the `review` prompt-pack scaffold.
- `W2-E1-S8-T6` (done) Add one worked `review` example bundle.

Exit evidence:

- `review` can be executed and judged from durable Markdown artifacts;
- validators can distinguish a real review from a superficial summary.

#### Slice W2-E1-S9 — `qa` stage contract (`done`)
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

- `W2-E1-S9-T1` (done) Define the required `qa` inputs, including implementation, review findings, and verification artifacts.
- `W2-E1-S9-T2` (done) Define the required `qa` outputs, including verdict, residual risk, and release recommendation.
- `W2-E1-S9-T3` (done) Define validator rules for unsupported verdicts and missing evidence references.
- `W2-E1-S9-T4` (done) Define interview triggers for blocked verification or missing execution artifacts.
- `W2-E1-S9-T5` (done) Create the `qa` prompt-pack scaffold.
- `W2-E1-S9-T6` (done) Add one worked `qa` example bundle.

Exit evidence:

- `qa` produces a durable, auditable release-quality decision;
- validators can block downstream verdict use when evidence is missing.

### Epic W2-E2 — validator engine foundation (`done`)
Linked stories: `US-03`, `US-04`, `US-07`

#### Slice W2-E2-S1 — markdown document loader (`done`)
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

#### Slice W2-E2-S2 — structural validation (`done`)
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

- `W2-E2-S2-T1` (done) Implement required-document existence checks from stage manifests.
- `W2-E2-S2-T2` (done) Implement Markdown heading extraction for contract section validation.
- `W2-E2-S2-T3` (done) Implement required-section checks against common-document and stage-document contracts.
- `W2-E2-S2-T4` (done) Implement validator issue objects with stable codes, severity, and source location fields.
- `W2-E2-S2-T5` (done) Implement `validator-report.md` rendering from collected structural issues.
- `W2-E2-S2-T6` (done) Add regression tests for missing documents, missing headings, duplicated headings, and empty sections.

Exit evidence:

- structural validation can fail before runtime-specific interpretation happens;
- validator reports are durable Markdown artifacts, not console-only output.

#### Slice W2-E2-S3 — semantic and cross-document validation (`done`)
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

- `W2-E2-S3-T1` (done) Implement stage-specific semantic validators for completeness, unsupported claims, and placeholder detection.
- `W2-E2-S3-T2` (done) Implement cross-document consistency checks for questions, answers, repair briefs, and stage results.
- `W2-E2-S3-T3` (done) Implement validation rules for unresolved blocking questions and exhausted repair budgets.
- `W2-E2-S3-T4` (done) Add semantic regression fixtures with both valid and invalid document bundles.
- `W2-E2-S3-T5` (done) Add false-positive and false-negative tests for representative stage bundles.

Exit evidence:

- validators can explain why a bundle fails beyond missing headings;
- cross-document state drift is caught before progression.

---

## Wave 3 — orchestration core (`done`)

### Epic W3-E1 — workspace and run store (`done`)
Linked stories: `US-02`, `US-07`, `US-09`

#### Slice W3-E1-S1 — workspace bootstrap service (`done`)
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

#### Slice W3-E1-S2 — run metadata and storage (`done`)
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

#### Slice W3-E1-S3 — run lookup and resume helpers (`done`)
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

#### Slice W3-E1-S4 — prompt provenance in run manifests (`done`)
Goal: record prompt provenance so prompt and workflow changes remain auditable and reproducible.

Primary outputs:

- `src/aidd/core/run_store.py`
- `src/aidd/cli/run_lookup.py`
- run-manifest regression tests

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`

Dependencies:

- `W3-E1-S2`

Local tasks:

- `W3-E1-S4-T1` (done) Record repository Git SHA + prompt-pack paths + content hashes in `run-manifest.json` and expose them via `aidd run show`.
- `W3-E1-S4-T2` (done) Persist per-attempt prompt-pack provenance in `artifact-index.json` (or a sibling artifact) for later eval reproducibility.

Exit evidence:

- a run manifest captures prompt provenance robustly enough to reproduce the exact prompt inputs used;
- run inspection commands surface the recorded provenance without manual file digging.

### Epic W3-E2 — stage controller (`done`)
Linked stories: `US-01`, `US-02`, `US-03`

#### Slice W3-E2-S1 — stage manifest loader (`done`)
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

#### Slice W3-E2-S2 — stage state machine (`done`)
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
- `W3-E2-S2-T3` (done) Implement execution-state persistence before handing off to an adapter.
- `W3-E2-S2-T4` (done) Implement validation-state persistence and transition decisions after validator completion.
- `W3-E2-S2-T5` (done) Implement terminal transition handling for success, blocked, failed, and repair-needed outcomes.
- `W3-E2-S2-T6` (done) Add tests that cover happy-path, validator-failure, blocked-question, and adapter-failure transitions.

Exit evidence:

- stage progression is modeled explicitly rather than hidden in CLI branching;
- every terminal state leaves durable stage metadata behind.

#### Slice W3-E2-S3 — stage dependency resolution and advancement (`done`)
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

- `W3-E2-S3-T1` (done) Implement stage dependency resolution from manifest-declared upstream stages.
- `W3-E2-S3-T2` (done) Implement eligibility checks for missing prerequisites, blocked questions, and failed required stages.
- `W3-E2-S3-T3` (done) Implement the selection of the next runnable stage in a workflow sequence.
- `W3-E2-S3-T4` (done) Implement advancement summaries that explain why a stage can or cannot run.
- `W3-E2-S3-T5` (done) Add dependency-resolution tests for branching, skipped stages, and blocked upstream states.

Exit evidence:

- the orchestrator can explain readiness instead of silently skipping stages;
- stage order is derived from contracts, not adapter code.

#### Slice W3-E2-S4 — published stage outputs (`done`)
Goal: make upstream references like `../<stage>/output/*.md` satisfiable after a successful run.

Primary outputs:

- `src/aidd/core/stage_runner.py`
- output publishing regression tests

Touched areas:

- `src/aidd/core/`
- `tests/core/`

Dependencies:

- `W3-E2-S1`
- `W3-E2-S2`

Local tasks:

- `W3-E2-S4-T1` (done) Implement stage-output publishing into `workitems/<id>/stages/<stage>/output/` after validation pass (copy declared primary outputs + `stage-result.md` + `validator-report.md`).
- `W3-E2-S4-T2` (done) Add regression tests proving downstream required inputs (for example `plan` reads `../idea/output/...`) become satisfiable after publish.

Exit evidence:

- downstream stage required inputs that reference `../<stage>/output/*.md` can resolve successfully after an upstream stage succeeds;
- published outputs remain stable across retries and can be diffed independently of attempt artifacts.

#### Slice W3-E2-S5 — full validation wiring (`done`)
Goal: wire semantic and cross-document validators into stage validation and render a combined report.

Primary outputs:

- `src/aidd/core/stage_runner.py`
- `src/aidd/validators/reports.py`
- validation wiring regression tests

Touched areas:

- `src/aidd/core/`
- `src/aidd/validators/`
- `tests/core/`

Dependencies:

- `W2-E2-S3`
- `W3-E2-S2`

Local tasks:

- `W3-E2-S5-T1` (done) Wire semantic and cross-document validators into the post-run validation path and render a combined `validator-report.md`.
- `W3-E2-S5-T2` (done) Add an end-to-end regression: structural passes but semantic/cross-document fails -> verdict is not `pass`, report contains `SEM-*/CROSS-*` findings.

Exit evidence:

- validator reports include semantic and cross-document buckets when applicable;
- stage progression decisions use the combined verdict rather than structural-only checks.

### Epic W3-E3 — interview and repair controllers (`done`)
Linked stories: `US-04`, `US-05`, `US-06`

#### Slice W3-E3-S1 — interview controller (`done`)
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

- `W3-E3-S1-T1` (done) Implement the interview policy model that distinguishes blocking and non-blocking questions.
- `W3-E3-S1-T2` (done) Implement persistence of `questions.md` from stage output or adapter-detected question events.
- `W3-E3-S1-T3` (done) Implement persistence and merging of `answers.md` without losing prior answers.
- `W3-E3-S1-T4` (done) Implement stage gating that blocks progression when blocking questions remain unresolved.
- `W3-E3-S1-T5` (done) Implement CLI helpers that display pending questions and guide the operator to answer them.
- `W3-E3-S1-T6` (done) Implement state updates that unblock the stage once required answers are present.
- `W3-E3-S1-T7` (done) Add tests for question persistence, partial answers, and unblock transitions.

Exit evidence:

- user questions become durable workflow artifacts rather than transient console prompts;
- blocked stages can resume only after required answers exist.

#### Slice W3-E3-S2 — repair controller (`done`)
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

- `W3-E3-S2-T1` (done) Implement repair-budget configuration and attempt counters for each stage.
- `W3-E3-S2-T2` (done) Implement generation of `repair-brief.md` from a validator report and prior stage artifacts.
- `W3-E3-S2-T3` (done) Implement rerun preparation that injects repair context into the next adapter invocation.
- `W3-E3-S2-T4` (done) Implement durable repair-history recording in stage metadata and `stage-result.md`.
- `W3-E3-S2-T5` (done) Implement terminal blocking when the repair budget is exhausted.
- `W3-E3-S2-T6` (done) Add tests for one-shot repair success, repeated repair failure, and exhausted-budget blocking.

Exit evidence:

- repair loops are explicit, bounded, and auditable;
- stages never rerun indefinitely after repeated validation failure.

---

## Wave 4 — runtimes and operator UX (`done`)

### Epic W4-E1 — `generic-cli` adapter (`done`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W4-E1-S1 — runtime probing (`done`)
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

#### Slice W4-E1-S2 — stage execution (`done`)
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

- `W4-E1-S2-T1` (done) Implement command assembly from adapter config, stage context, and prompt-pack path.
- `W4-E1-S2-T2` (done) Implement environment-variable injection for workspace, stage, and run metadata.
- `W4-E1-S2-T3` (done) Implement workspace and prompt-pack path exposure for subprocess execution.
- `W4-E1-S2-T4` (done) Implement stdout and stderr streaming to the CLI while the subprocess runs.
- `W4-E1-S2-T5` (done) Persist raw `runtime.log` and basic exit metadata for each attempt.
- `W4-E1-S2-T6` (done) Implement timeout, cancellation, and non-zero exit classification.
- `W4-E1-S2-T7` (done) Add tests for successful runs, timed-out runs, cancelled runs, and non-zero exits.

Exit evidence:

- the generic adapter can execute a stage without hiding native output;
- adapter failures are separated from validator failures in durable metadata.

#### Slice W4-E1-S3 — document handshake and question surfacing (`done`)
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

- `W4-E1-S3-T1` (done) Implement input-bundle preparation for a stage attempt before subprocess launch.
- `W4-E1-S3-T2` (done) Implement post-run output discovery that finds expected Markdown artifacts in the workspace.
- `W4-E1-S3-T3` (done) Trigger structural validation immediately after output discovery and persist the report path.
- `W4-E1-S3-T4` (done) Detect unresolved questions from `questions.md` and route them into the interview controller.
- `W4-E1-S3-T5` (done) Implement resume behavior after answers are added for a generic-cli stage.
- `W4-E1-S3-T6` (done) Add integration tests for valid output, invalid output, and question-blocked output.

Exit evidence:

- the generic adapter participates in the same document-first orchestration loop as richer adapters;
- question files are handled consistently even without runtime-native question events.

### Epic W4-E2 — `claude-code` adapter (`done`)
Linked stories: `US-01`, `US-05`, `US-06`, `US-08`

#### Slice W4-E2-S1 — runtime probing (`done`)
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

#### Slice W4-E2-S2 — stage execution and command assembly (`done`)
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

- `W4-E2-S2-T1` (done) Implement Claude Code command assembly from stage brief, workspace path, and prompt-pack inputs.
- `W4-E2-S2-T2` (done) Implement adapter-side mapping of sandbox, permission, and config flags into the launch command.
- `W4-E2-S2-T3` (done) Implement environment and working-directory setup for Claude Code runs.
- `W4-E2-S2-T4` (done) Implement timeout and cancellation handling that maps process outcomes into adapter statuses.
- `W4-E2-S2-T5` (done) Add execution tests for a dry-run or fixture command path that covers launch, cancel, and timeout handling.

Exit evidence:

- the Claude Code adapter can be launched repeatedly with deterministic inputs;
- launch configuration stays isolated inside the adapter boundary.

#### Slice W4-E2-S3 — log streaming and event normalization (`done`)
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

- `W4-E2-S3-T1` (done) Stream raw Claude Code stdout and stderr to the operator CLI in real time.
- `W4-E2-S3-T2` (done) Persist a full `runtime.log` that matches the raw streamed output as closely as possible.
- `W4-E2-S3-T3` (done) Normalize any machine-readable Claude Code events into a durable `events.jsonl` artifact when available.
- `W4-E2-S3-T4` (done) Implement exit classification that distinguishes adapter, runtime, and user-cancelled outcomes.
- `W4-E2-S3-T5` (done) Add tests that verify raw-log persistence, event normalization, and exit classification.

Exit evidence:

- operators can see native runtime logs during execution;
- evals can consume normalized events without losing the raw source log.

#### Slice W4-E2-S4 — question surfacing and resume (`done`)
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

- `W4-E2-S4-T1` (done) Detect Claude Code question or pause events when the runtime exposes them.
- `W4-E2-S4-T2` (done) Fall back to file-based unresolved-question detection when runtime-native events are absent.
- `W4-E2-S4-T3` (done) Persist surfaced questions into the standard `questions.md` artifact and stage metadata.
- `W4-E2-S4-T4` (done) Implement adapter-side resume behavior after the operator provides answers.
- `W4-E2-S4-T5` (done) Add tests for runtime-native questions, file-based questions, and resume-after-answer behavior.

Exit evidence:

- the Claude Code adapter enters the same interview loop as the generic adapter;
- unanswered questions block the stage instead of disappearing into runtime logs.

### Epic W4-E3 — operator CLI experience (`done`)
Linked stories: `US-05`, `US-06`, `US-09`

#### Slice W4-E3-S1 — run summaries (`done`)
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

- `W4-E3-S1-T1` (done) Implement stage-result summaries that show final state, runtime, and attempt count.
- `W4-E3-S1-T2` (done) Implement validator-outcome summaries that show pass/fail counts and report paths.
- `W4-E3-S1-T3` (done) Implement artifact path summaries for logs, documents, and repair outputs.
- `W4-E3-S1-T4` (done) Add CLI tests for success, blocked, repair-needed, and failed summaries.

Exit evidence:

- a completed run leaves the operator with a direct path to the important artifacts;
- summary output is consistent across adapters.

#### Slice W4-E3-S2 — live log follow mode (`done`)
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

- `W4-E3-S2-T1` (done) Add a CLI flag that enables explicit live-log follow behavior for stage runs.
- `W4-E3-S2-T2` (done) Prefix streamed runtime lines with adapter and stage context when multiple streams are possible.
- `W4-E3-S2-T3` (done) Add tests for follow-mode formatting and graceful shutdown on process end or cancellation.

Exit evidence:

- operators can follow runtime-native logs without opening artifact files manually.

#### Slice W4-E3-S3 — run inspection commands (`done`)
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

- `W4-E3-S3-T1` (done) Add a command that prints the stored metadata for a run and its stages.
- `W4-E3-S3-T2` (done) Add a command that prints or tails the persisted runtime log for a selected attempt.
- `W4-E3-S3-T3` (done) Add a command that lists document and report artifact paths for a selected attempt.
- `W4-E3-S3-T4` (done) Add CLI tests for missing runs, valid runs, and ambiguous run selection.

Exit evidence:

- stored run artifacts are inspectable without manual filesystem traversal.

#### Slice W4-E3-S4 — implement `aidd stage run` (`done`)
Goal: remove placeholder behavior in `aidd stage run` and execute one stage end to end.

Primary outputs:

- `src/aidd/cli/main.py`
- `src/aidd/core/stage_runner.py`
- stage-run integration tests

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/`
- `src/aidd/adapters/`
- `tests/cli/`

Dependencies:

- `W3-E2-S4`
- `W3-E2-S5`
- `W4-E1-S3` or `W4-E2-S4`

Local tasks:

- `W4-E3-S4-T1` (done) Implement core single-stage orchestration for `generic-cli` (prepare -> adapter run -> validation -> persist status -> publish outputs).
- `W4-E3-S4-T2` (done) Wire `aidd stage run` CLI to the orchestrator, including real `--log-follow` streaming behavior.
- `W4-E3-S4-T3` (done) Add bounded repair loop integration for stage run (retry with repair brief until budget exhausted).
- `W4-E3-S4-T4` (done) Add interview loop integration: detect unresolved blocking questions, stop as blocked, resume once answers exist.

Exit evidence:

- `aidd stage run <stage>` executes the full document-first loop and leaves durable artifacts behind;
- `--log-follow` streams runtime-native output and preserves it in `runtime.log`;
- repair and interview flows stop or resume without silently skipping required work.

#### Slice W4-E3-S5 — implement `aidd run` workflow execution (`done`)
Goal: remove placeholder behavior in `aidd run` and execute a full multi-stage workflow.

Primary outputs:

- `src/aidd/cli/main.py`
- `src/aidd/core/stage_graph.py`
- workflow-run regression tests

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/`
- `tests/cli/`

Dependencies:

- `W4-E3-S4`
- `W3-E2-S3`

Local tasks:

- `W4-E3-S5-T1` (done) Implement workflow run loop using stage dependency resolution (select next runnable stage, stop on blocked/failed).
- `W4-E3-S5-T2` (done) Add CLI progress + final summary output consistent with stored run artifacts.

Exit evidence:

- `aidd run --work-item <id>` can advance stages safely and stop with a clear reason when blocked or failed;
- run artifacts and summaries remain consistent with the stored stage metadata and validator reports.

---

## Wave 5 — harness, eval, and log analysis (`done`)

### Epic W5-E1 — scenario runner (`done`)
Linked stories: `US-07`

#### Slice W5-E1-S1 — scenario manifest loader (`done`)
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

- `W5-E1-S1-T1` (done) Define the Python model for scenario manifests, including repo source, setup steps, run config, and verification steps.
- `W5-E1-S1-T2` (done) Implement YAML manifest loading with stable validation errors for missing keys and invalid values.
- `W5-E1-S1-T3` (done) Implement variable substitution for runtime id, workspace path, and scenario-scoped parameters.
- `W5-E1-S1-T4` (done) Add tests for valid manifests, missing fields, and parameter substitution.

Exit evidence:

- scenarios can be loaded without hardcoded repo-specific logic;
- invalid manifests fail before repository preparation begins.

#### Slice W5-E1-S2 — repository preparation (`done`)
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

- `W5-E1-S2-T1` (done) Implement repository clone or fetch logic for scenario targets.
- `W5-E1-S2-T2` (done) Implement revision pinning so a scenario runs against a stable commit or tag.
- `W5-E1-S2-T3` (done) Implement clean working-copy preparation for each scenario invocation.
- `W5-E1-S2-T4` (done) Implement cleanup rules for previous scenario artifacts and transient files.
- `W5-E1-S2-T5` (done) Add tests for first clone, repeated runs, invalid revisions, and dirty-workspace cleanup.

Exit evidence:

- every scenario run starts from a deterministic repository state;
- repo preparation failures are distinguishable from AIDD execution failures.

#### Slice W5-E1-S3 — setup, run, and verification execution (`done`)
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

- `W5-E1-S3-T1` (done) Implement setup-step execution before AIDD is invoked.
- `W5-E1-S3-T2` (done) Implement AIDD invocation with runtime, scenario, and work-item parameters.
- `W5-E1-S3-T3` (done) Implement verification-step execution after the AIDD run completes.
- `W5-E1-S3-T4` (done) Capture durations, exit codes, and command transcripts for setup, run, and verification steps.
- `W5-E1-S3-T5` (done) Implement teardown handling that runs even after a failed scenario.
- `W5-E1-S3-T6` (done) Add integration tests for passing scenarios, failing setup steps, failing verification steps, and interrupted runs.

Exit evidence:

- a single harness command can prepare, run, verify, and archive one scenario;
- step boundaries remain visible in logs and metadata.

#### Slice W5-E1-S4 — scenario result bundle (`done`)
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

- `W5-E1-S4-T1` (done) Define the scenario run directory layout and stable artifact names.
- `W5-E1-S4-T2` (done) Persist harness metadata, command transcripts, and references to AIDD run artifacts.
- `W5-E1-S4-T3` (done) Copy or link validator reports, runtime logs, and verdict files into the bundle.
- `W5-E1-S4-T4` (done) Add tests that verify bundle completeness for pass, fail, and blocked runs.

Exit evidence:

- every scenario run leaves behind one self-contained artifact bundle.

### Epic W5-E2 — graders and verdicts (`done`)
Linked stories: `US-07`

#### Slice W5-E2-S1 — verdict writing (`done`)
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

- `W5-E2-S1-T1` (done) Define the verdict model and Markdown artifact layout.
- `W5-E2-S1-T2` (done) Map harness outcomes into `pass`, `fail`, `blocked`, and `infra-fail` verdict states.
- `W5-E2-S1-T3` (done) Record linked artifacts, first-failure notes, and verification summaries in the verdict.
- `W5-E2-S1-T4` (done) Add tests for verdict generation across each terminal outcome.

Exit evidence:

- every scenario run produces one durable verdict artifact with traceable evidence links.

#### Slice W5-E2-S2 — log analysis (`done`)
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

- `W5-E2-S2-T1` (done) Implement parsing of `runtime.log` into coarse runtime events.
- `W5-E2-S2-T2` (done) Implement parsing of `events.jsonl` when a runtime exposes normalized events.
- `W5-E2-S2-T3` (done) Implement parsing of `validator-report.md` and stage-result metadata for validation failures.
- `W5-E2-S2-T4` (done) Implement the failure taxonomy that separates environment, adapter, runtime, validation, and scenario-verification failures.
- `W5-E2-S2-T5` (done) Implement first-failure-boundary selection from competing log signals.
- `W5-E2-S2-T6` (done) Add regression tests for ambiguous failures, multi-error runs, and empty-log cases.

Exit evidence:

- evals can explain where a run failed instead of only reporting that it failed.

#### Slice W5-E2-S3 — eval summary reports (`done`)
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

- `W5-E2-S3-T1` (done) Implement per-scenario summary rows with verdict, runtime, duration, and failure boundary.
- `W5-E2-S3-T2` (done) Implement runtime-level summary aggregation across many scenarios.
- `W5-E2-S3-T3` (done) Render a Markdown summary report suitable for CI artifacts.
- `W5-E2-S3-T4` (done) Add a CLI summary command that prints the latest eval report.
- `W5-E2-S3-T5` (done) Add tests for empty eval sets, mixed outcomes, and repeated scenario runs.

Exit evidence:

- operators can compare many scenario runs without opening each artifact bundle individually.

### Epic W5-E3 — live E2E lanes (`done`)
Linked stories: `US-07`

#### Slice W5-E3-S1 — Typer smoke lane (`done`)
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

- `W5-E3-S1-T1` (done) Pin the Typer repository revision and record the target scenario objective.
- `W5-E3-S1-T2` (done) Define setup steps and AIDD invocation parameters for the Typer smoke scenario.
- `W5-E3-S1-T3` (done) Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S1-T4` (done) Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- Typer smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S2 — HTTPX smoke lane (`done`)
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

- `W5-E3-S2-T1` (done) Pin the HTTPX repository revision and record the target scenario objective.
- `W5-E3-S2-T2` (done) Define setup steps and AIDD invocation parameters for the HTTPX smoke scenario.
- `W5-E3-S2-T3` (done) Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S2-T4` (done) Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- HTTPX smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S3 — sqlite-utils smoke lane (`done`)
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

- `W5-E3-S3-T1` (done) Pin the sqlite-utils repository revision and record the target scenario objective.
- `W5-E3-S3-T2` (done) Define setup steps and AIDD invocation parameters for the sqlite-utils smoke scenario.
- `W5-E3-S3-T3` (done) Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S3-T4` (done) Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- sqlite-utils smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S4 — Hono smoke lane (`done`)
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

- `W5-E3-S4-T1` (done) Pin the Hono repository revision and record the target scenario objective.
- `W5-E3-S4-T2` (done) Define setup steps and AIDD invocation parameters for the Hono smoke scenario.
- `W5-E3-S4-T3` (done) Define deterministic verification steps and expected pass conditions for the scenario.
- `W5-E3-S4-T4` (done) Run the scenario once end to end and capture the first reference artifact bundle.

Exit evidence:

- Hono smoke is runnable repeatedly through the harness with a stable baseline.

#### Slice W5-E3-S5 — sqlite-utils interview lane (`done`)
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

- `W5-E3-S5-T1` (done) Define the sqlite-utils scenario conditions that force at least one user question.
- `W5-E3-S5-T2` (done) Define the operator answer file or CLI-answer flow used by the scenario.
- `W5-E3-S5-T3` (done) Define verification steps that prove the run blocked, resumed, and completed correctly.
- `W5-E3-S5-T4` (done) Run the scenario once end to end and archive the reference blocked-and-resumed bundle.

Exit evidence:

- one live scenario proves that the AIDD interview loop works outside synthetic fixtures.

#### Slice W5-E3-S6 — Hono interview lane (`done`)
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

- `W5-E3-S6-T1` (done) Define the Hono scenario conditions that force at least one user question.
- `W5-E3-S6-T2` (done) Define the operator answer file or CLI-answer flow used by the scenario.
- `W5-E3-S6-T3` (done) Define verification steps that prove the run blocked, resumed, and completed correctly.
- `W5-E3-S6-T4` (done) Run the scenario once end to end and archive the reference blocked-and-resumed bundle.

Exit evidence:

- question handling works across more than one public repository and stack.

---

## Wave 6 — canonical stage packs (`done`)

### Epic W6-E1 — strategy stages (`done`)
Linked stories: `US-02`, `US-03`, `US-05`

#### Slice W6-E1-S1 — `idea` stage pack (`done`)
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

- `W6-E1-S1-T1` (done) Write the `idea` base prompt that explains the stage objective and required outputs.
- `W6-E1-S1-T2` (done) Write the `idea` repair prompt that maps validator failures into concrete fixes.
- `W6-E1-S1-T3` (done) Implement `idea`-specific semantic validators.
- `W6-E1-S1-T4` (done) Add valid and invalid `idea` fixtures for regression tests.
- `W6-E1-S1-T5` (done) Add unit tests that execute the `idea` validator against the fixtures.
- `W6-E1-S1-T6` (done) Run one smoke execution of `idea` through an adapter and archive the output bundle.

Exit evidence:

- the `idea` stage is more than a contract file; it is runnable, validated, and repairable.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-idea-smoke-20260422T100325Z`.

#### Slice W6-E1-S2 — `research` stage pack (`done`)
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

- `W6-E1-S2-T1` (done) Write the `research` base prompt with explicit evidence, citation, and uncertainty guidance.
- `W6-E1-S2-T2` (done) Write the `research` repair prompt for unsupported claims and missing evidence.
- `W6-E1-S2-T3` (done) Implement `research`-specific semantic validators.
- `W6-E1-S2-T4` (done) Add valid and invalid `research` fixtures, including missing-source and unresolved-question cases.
- `W6-E1-S2-T5` (done) Add unit tests that execute the `research` validator against the fixtures.
- `W6-E1-S2-T6` (done) Run one smoke execution of `research` through an adapter and archive the output bundle.

Exit evidence:

- `research` can produce auditable outputs and fail predictably when evidence is weak.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-research-smoke-20260422T101720Z`.

#### Slice W6-E1-S3 — `plan` stage pack (`done`)
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

- `W6-E1-S3-T1` (done) Write the `plan` base prompt with milestone, dependency, and verification expectations.
- `W6-E1-S3-T2` (done) Write the `plan` repair prompt for vague sequencing, missing risks, or unreviewable scope.
- `W6-E1-S3-T3` (done) Implement `plan`-specific semantic validators.
- `W6-E1-S3-T4` (done) Add valid and invalid `plan` fixtures.
- `W6-E1-S3-T5` (done) Add unit tests that execute the `plan` validator against the fixtures.
- `W6-E1-S3-T6` (done) Add one harness smoke scenario that exercises `plan` and archives the resulting artifacts.

Exit evidence:

- `plan` is fully wired into validation and harness execution.
- smoke scenario added at `harness/scenarios/smoke/plan-stagepack-smoke.yaml`.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-plan-smoke-20260422T102945Z`.

### Epic W6-E2 — delivery stages (`done`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-05`

#### Slice W6-E2-S1 — `review-spec` stage pack (`done`)
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

- `W6-E2-S1-T1` (done) Write the `review-spec` base prompt.
- `W6-E2-S1-T2` (done) Write the `review-spec` repair prompt.
- `W6-E2-S1-T3` (done) Implement `review-spec` semantic validators.
- `W6-E2-S1-T4` (done) Add valid and invalid `review-spec` fixtures.
- `W6-E2-S1-T5` (done) Add unit tests for `review-spec` validation.
- `W6-E2-S1-T6` (done) Run one smoke execution of `review-spec` and archive the artifacts.

Exit evidence:

- `review-spec` can block downstream work with durable, validated review findings.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-review-spec-smoke-20260422T105603Z`.

#### Slice W6-E2-S2 — `tasklist` stage pack (`done`)
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

- `W6-E2-S2-T1` (done) Write the `tasklist` base prompt.
- `W6-E2-S2-T2` (done) Write the `tasklist` repair prompt.
- `W6-E2-S2-T3` (done) Implement `tasklist` semantic validators for granularity and dependency clarity.
- `W6-E2-S2-T4` (done) Add valid and invalid `tasklist` fixtures.
- `W6-E2-S2-T5` (done) Add unit tests for `tasklist` validation.
- `W6-E2-S2-T6` (done) Run one smoke execution of `tasklist` and archive the artifacts.

Exit evidence:

- `tasklist` produces reviewable execution units and fails predictably when decomposition is poor.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-tasklist-smoke-20260422T111757Z`.

#### Slice W6-E2-S3 — `implement` stage pack (`done`)
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

- `W6-E2-S3-T1` (done) Write the `implement` base prompt with edit-scope, verification, and summary expectations.
- `W6-E2-S3-T2` (done) Write the `implement` repair prompt for validator-driven reruns.
- `W6-E2-S3-T3` (done) Implement `implement` semantic validators.
- `W6-E2-S3-T4` (done) Add valid and invalid `implement` fixtures, including no-op and incomplete-verification cases.
- `W6-E2-S3-T5` (done) Add unit tests for `implement` validation.
- `W6-E2-S3-T6` (done) Add one harness or integration scenario that proves the `implement` repair loop end to end.

Exit evidence:

- `implement` can fail, repair, and succeed through the same document-first loop.

### Epic W6-E3 — assurance stages (`done`)
Linked stories: `US-03`, `US-04`, `US-07`

#### Slice W6-E3-S1 — `review` stage pack (`done`)
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

- `W6-E3-S1-T1` (done) Write the `review` base prompt.
- `W6-E3-S1-T2` (done) Write the `review` repair prompt.
- `W6-E3-S1-T3` (done) Implement `review` semantic validators.
- `W6-E3-S1-T4` (done) Add valid and invalid `review` fixtures.
- `W6-E3-S1-T5` (done) Add unit tests for `review` validation.
- `W6-E3-S1-T6` (done) Run one smoke execution of `review` and archive the artifacts.

Exit evidence:

- `review` findings are durable, severity-labeled, and validator-backed.
- smoke bundle archived at `.aidd/reports/evals/eval-stage-review-smoke-20260422T114904Z`.

#### Slice W6-E3-S2 — `qa` stage pack (`done`)
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

- `W6-E3-S2-T1` (done) Write the `qa` base prompt.
- `W6-E3-S2-T2` (done) Write the `qa` repair prompt.
- `W6-E3-S2-T3` (done) Implement `qa` semantic validators.
- `W6-E3-S2-T4` (done) Add valid and invalid `qa` fixtures.
- `W6-E3-S2-T5` (done) Add unit tests for `qa` validation.
- `W6-E3-S2-T6` (done) Add one integration scenario that converts `qa` output into an eval verdict artifact.

Exit evidence:

- `qa` can feed directly into harness verdict writing with auditable evidence links.
- integration scenario added at `tests/evals/test_verdicts.py` (`test_build_scenario_verdict_integration_from_qa_success_bundle`).

---

## Wave 7 — runtime widening and release hardening (`done`)

### Epic W7-E1 — `codex` adapter (`done`)
Linked stories: `US-01`, `US-08`

#### Slice W7-E1-S1 — runtime probing (`done`)
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

- `W7-E1-S1-T1` (done) Implement Codex command discovery.
- `W7-E1-S1-T2` (done) Capture Codex version or identity output.
- `W7-E1-S1-T3` (done) Derive Codex capability flags relevant to AIDD.
- `W7-E1-S1-T4` (done) Expose Codex probe results in `aidd doctor`.
- `W7-E1-S1-T5` (done) Add probe tests for found, missing, and malformed-version cases.

Exit evidence:

- the Codex adapter can be discovered and reported without execution support yet being complete.

#### Slice W7-E1-S2 — stage execution and logs (`done`)
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

- `W7-E1-S2-T1` (done) Implement Codex command assembly from stage inputs.
- `W7-E1-S2-T2` (done) Implement workspace and environment setup for Codex runs.
- `W7-E1-S2-T3` (done) Implement raw log streaming and `runtime.log` persistence.
- `W7-E1-S2-T4` (done) Implement exit classification, timeout handling, and cancellation handling.
- `W7-E1-S2-T5` (done) Add execution tests for success, failure, timeout, and cancellation paths.

Exit evidence:

- Codex participates in the same execution contract as the first-wave adapters.

#### Slice W7-E1-S3 — parity scenarios (`done`)
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

- `W7-E1-S3-T1` (done) Select the minimum parity scenario set for Codex.
- `W7-E1-S3-T2` (done) Run Codex on the smoke lane and capture reference bundles.
- `W7-E1-S3-T3` (done) Run Codex on at least one interview lane and capture reference bundles.
- `W7-E1-S3-T4` (done) Document known parity gaps and adapter-specific limitations.

Exit evidence:

- Codex can be compared to Claude Code and generic-cli on shared scenarios.

### Epic W7-E2 — `opencode` adapter (`done`)
Linked stories: `US-01`, `US-08`

#### Slice W7-E2-S1 — runtime probing (`done`)
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

- `W7-E2-S1-T1` (done) Implement OpenCode command discovery.
- `W7-E2-S1-T2` (done) Capture OpenCode version or identity output.
- `W7-E2-S1-T3` (done) Derive OpenCode capability flags relevant to AIDD.
- `W7-E2-S1-T4` (done) Expose OpenCode probe results in `aidd doctor`.
- `W7-E2-S1-T5` (done) Add probe tests for found, missing, and malformed-version cases.

Exit evidence:

- the OpenCode adapter can be discovered and reported before execution support is added.

#### Slice W7-E2-S2 — stage execution and logs (`done`)
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

- `W7-E2-S2-T1` (done) Implement OpenCode command assembly from stage inputs.
- `W7-E2-S2-T2` (done) Implement workspace and environment setup for OpenCode runs.
- `W7-E2-S2-T3` (done) Implement raw log streaming and `runtime.log` persistence.
- `W7-E2-S2-T4` (done) Implement exit classification, timeout handling, and cancellation handling.
- `W7-E2-S2-T5` (done) Add execution tests for success, failure, timeout, and cancellation paths.

Exit evidence:

- OpenCode participates in the same execution contract as the first-wave adapters.

#### Slice W7-E2-S3 — parity scenarios (`done`)
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

- `W7-E2-S3-T1` (done) Select the minimum parity scenario set for OpenCode.
- `W7-E2-S3-T2` (done; reference run `eval-live-005-opencode-20260422T142733Z`, status `harness_pass`) Run OpenCode on the smoke lane and capture reference bundles.
- `W7-E2-S3-T3` (done; reference run `eval-live-006-opencode-20260422T142812Z`, status `harness_blocked`) Run OpenCode on at least one interview lane and capture reference bundles.
- `W7-E2-S3-T4` (done) Document known parity gaps and adapter-specific limitations.

Exit evidence:

- OpenCode can be compared to Claude Code, Codex, and generic-cli on shared scenarios.

### Epic W7-E3 — public release hardening (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W7-E3-S1 — operator handbook (`done`)
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

- `W7-E3-S1-T1` (done) Write the operator handbook for installation, configuration, and first run.
- `W7-E3-S1-T2` (done) Write the troubleshooting guide for runtime, validator, and harness failures.
- `W7-E3-S1-T3` (done) Write the support policy and issue-reporting instructions.
- `W7-E3-S1-T4` (done) Add links from `README.md` and `CONTRIBUTING.md` into the new operator docs.

Exit evidence:

- a new operator can install and diagnose AIDD without reading the source tree.

#### Slice W7-E3-S2 — release operations (`done`)
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

- `W7-E3-S2-T1` (done) Finalize PyPI publishing configuration and release tagging rules.
- `W7-E3-S2-T2` (done) Finalize container publishing configuration and image tagging rules.
- `W7-E3-S2-T3` (done) Add a human-readable release checklist that covers package, image, and changelog steps.
- `W7-E3-S2-T4` (done) Add release-verification steps that prove the published CLI can still run `aidd doctor`.

Exit evidence:

- releases can be published and verified through a documented, repeatable path.

#### Slice W7-E3-S3 — compatibility and maintenance policy (`done`)
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

- `W7-E3-S3-T1` (done) Define the supported Python-version window and platform support policy.
- `W7-E3-S3-T2` (done) Define runtime-support tiers for generic-cli, Claude Code, Codex, and OpenCode.
- `W7-E3-S3-T3` (done) Define the policy for refreshing live E2E scenario baselines and pinned revisions.
- `W7-E3-S3-T4` (done) Define deprecation rules for contract changes, adapters, and scenario manifests.

Exit evidence:

- contributors and operators know what support guarantees AIDD actually makes.

#### Slice W7-E3-S4 — doc + planning consistency cleanup (`done`)
Goal: remove the remaining runtime-support and planning drift before resuming broader implementation.

Primary outputs:

- `docs/backlog/roadmap.md`
- `docs/backlog/backlog.md`
- `README.md`
- operator-facing docs updated to runtime-gate reality

Touched areas:

- `docs/`
- `docs/backlog/`

Dependencies:

- none

Local tasks:

- `W7-E3-S4-T1` (done) Update runtime-support statements in `README.md` and operator docs so they do not contradict the current CLI runtime gate.
- `W7-E3-S4-T2` (done) Replace placeholder wording for `aidd run` and `aidd stage run` with the current implemented scope.
- `W7-E3-S4-T3` (done) Add an explicit temporary limitation note that workflow execution remains `generic-cli` only until parity slices complete.
- `W7-E3-S4-T4` (done) Add a traceable roadmap/backlog sync note that records the post-audit queue restoration.

Sync notes:

- `2026-04-23` Roadmap and backlog were re-synchronized after readiness cleanup; queue restoration tracking started under `W7-E3-S4` and Wave 8 follow-up slices.
- `2026-04-23` Status consistency normalization completed: Wave 7, Epic `W7-E3`, and Slice `W7-E3-S4` were set to `done` after all local tasks were verified as done.

Exit evidence:

- docs do not claim runtime behavior that the CLI does not execute today;
- backlog queue and roadmap narrative are synchronized and reviewable;
- reopened planning work is explicit instead of hidden behind stale `done` labels.

---

## Wave 8 — readiness recovery and runtime parity (`done`)

### Epic W8-E1 — runtime execution parity (`done`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W8-E1-S1 — runtime execution contract hardening (`done`)
Goal: eliminate success-without-execution behavior for unsupported runtimes.

Primary outputs:

- CLI unsupported-runtime failure contract
- harness runtime-status mapping update
- regression tests for non-generic workflow paths

Touched areas:

- `src/aidd/cli/`
- `src/aidd/harness/`
- `tests/cli/`
- `tests/harness/`

Dependencies:

- `W4-E3-S5`
- `W5-E2-S1`

Local tasks:

- `W8-E1-S1-T1` (done) Make `aidd run --runtime <unsupported>` fail fast with non-zero exit and explicit unsupported-runtime classification.
- `W8-E1-S1-T2` (done) Make harness status mapping treat unsupported-runtime/no-op execution as fail or blocked, never pass.
- `W8-E1-S1-T3` (done) Add regression tests that lock non-generic run-path behavior in CLI and harness.

Exit evidence:

- unsupported runtime workflow invocations cannot exit as successful no-op runs;
- harness verdicts no longer report pass when stage execution was skipped.

#### Slice W8-E1-S2 — runtime adapter dispatch parity (`done`)
Goal: route stage execution through runtime-specific adapters beyond `generic-cli`.

Primary outputs:

- runtime dispatcher in `stage run`
- aligned runtime artifact persistence path
- cross-runtime smoke scenario set

Touched areas:

- `src/aidd/cli/`
- `src/aidd/adapters/`
- `tests/cli/`
- `tests/adapters/`
- `harness/scenarios/smoke/`

Dependencies:

- `W8-E1-S1`
- `W7-E1-S2`
- `W7-E2-S2`

Local tasks:

- `W8-E1-S2-T1` (done) Add runtime dispatch in `aidd stage run` for `claude-code`, `codex`, and `opencode`.
- `W8-E1-S2-T2` (done) Unify runtime artifact persistence for new dispatch paths under the existing run-store layout.
- `W8-E1-S2-T3` (done) Add cross-runtime smoke scenarios that assert required stage output documents were produced.

Exit evidence:

- stage execution can be invoked through adapter-specific paths for maintained runtimes;
- produced artifacts remain comparable across runtimes.

### Epic W8-E2 — harness verdict robustness (`done`)
Linked stories: `US-07`, `US-10`

#### Slice W8-E2-S1 — no-op resistant eval verdicts (`done`)
Goal: prevent eval verdicts from passing without verified stage outputs.

Primary outputs:

- stage-output guard in eval verdict flow
- no-op detector in log-analysis/verdict pipeline
- stronger verification expectations in scenario guidance

Touched areas:

- `src/aidd/harness/`
- `src/aidd/evals/`
- `tests/harness/`
- `tests/evals/`

Dependencies:

- `W8-E1-S1`
- `W5-E2-S2`

Blocker notes:

- `2026-04-23` `W8-E2-S1-T1` was blocked until `W8-E1-S1-T2` and `W8-E1-S1-T3` completed under strict slice-dependency policy; unblocked after `W8-E1-S1` closure.

Local tasks:

- `W8-E2-S1-T1` (done) Add a guard that forbids `pass` verdicts when required stage output artifacts are missing.
- `W8-E2-S1-T2` (done) Add a no-op execution detector and map it to fail/blocked classifications.
- `W8-E2-S1-T3` (done) Strengthen live scenario verification expectations so checks assert repository effects, not only command exit status.

Exit evidence:

- eval pass status always implies evidenced stage-output side effects;
- no-op execution paths are classified and reported as non-pass outcomes.

### Epic W8-E3 — planning governance recovery (`done`)
Linked stories: `US-10`

#### Slice W8-E3-S1 — backlog restoration policy (`done`)
Goal: define and document how to reopen execution flow when roadmap slices were previously all marked done.

Primary outputs:

- queue-restoration policy note
- planning workflow note for opening a new wave

Touched areas:

- `docs/backlog/`

Dependencies:

- none

Local tasks:

- `W8-E3-S1-T1` (done) Document the policy for restoring actionable queue state when roadmap is fully done and backlog is empty.

Queue restoration policy (roadmap all `done` + backlog empty):

1. Confirm trigger conditions:
   - `docs/backlog/backlog.md` has no task IDs in `Next`, `Soon`, or `Parking lot`;
   - active roadmap wave has no remaining `next`, `planned`, `later`, or `blocked` local tasks.
2. Open a new wave in `docs/backlog/roadmap.md` using `wave -> epic -> slice -> local task` decomposition before editing backlog.
3. Add at least one actionable local task with explicit output, dominant touched area, and one verification signal.
4. Set statuses in roadmap first (`next`/`planned`) and verify dependencies are explicit at slice level.
5. Promote queue entries in `docs/backlog/backlog.md`:
   - first actionable task(s) to `Next`;
   - dependent near-term tasks to `Soon`;
   - deferred visibility items to `Parking lot`.
6. Add a dated sync note in roadmap or backlog describing the queue restoration event and the first promoted task IDs.
7. Run the backlog sync checklist before implementation starts:
   - every backlog ID exists in roadmap;
   - only local task IDs appear in backlog;
   - no completed task remains queued.

Exit evidence:

- maintainers have a documented, repeatable procedure to reopen the next wave without governance drift.

---

## Wave 9 — backlog cycle restart and workflow parity (`done`)

### Epic W9-E0 — governance bootstrap (`done`)
Linked stories: `US-10`

#### Slice W9-E0-S1 — roadmap status normalization and queue bootstrap (`done`)
Goal: normalize planning statuses and prepare a decision-complete queue restart path.

Primary outputs:

- roadmap status-normalization note
- wave bootstrap decomposition for queue restart
- queue restoration sync readiness

Touched areas:

- `docs/backlog/`

Dependencies:

- none

Local tasks:

- `W9-E0-S1-T1` (done) Normalize roadmap status consistency for completed Wave 7 planning nodes and add a dated sync note.
- `W9-E0-S1-T2` (done) Open a decision-complete Wave 9 implementation lane for workflow runtime parity.
- `W9-E0-S1-T3` (done) Restore actionable backlog queue ordering from the new Wave 9 decomposition.

Exit evidence:

- roadmap top-level status labels match local-task reality;
- queue bootstrap tasks exist and are reviewable before implementation resumes.

### Epic W9-E1 — workflow runtime parity (`done`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W9-E1-S1 — workflow runtime dispatch and parity hardening (`done`)
Goal: execute `aidd run` through maintained runtime adapters with parity-safe artifact and regression coverage.

Primary outputs:

- runtime dispatcher in `aidd run` for maintained non-generic runtimes
- unified workflow run artifact persistence across runtimes
- workflow regression coverage for non-generic runtime paths
- cross-runtime smoke verification for produced stage output documents

Touched areas:

- `src/aidd/cli/`
- `src/aidd/adapters/`
- `src/aidd/harness/`
- `tests/cli/`
- `tests/harness/`
- `harness/scenarios/smoke/`

Dependencies:

- `W8-E1-S2`
- `W8-E2-S1`
- `W5-E2-S1`

Local tasks:

- `W9-E1-S1-T1` (done) Implement runtime dispatch in `aidd run` for `claude-code`, `codex`, and `opencode`.
- `W9-E1-S1-T2` (done) Unify workflow run artifact persistence across runtimes under the existing run-store layout.
- `W9-E1-S1-T3` (done) Add workflow-path regressions for non-generic runtimes, including success, fail, no-op, and unsupported paths.
- `W9-E1-S1-T4` (done) Add cross-runtime smoke scenario checks that require produced stage output artifacts in workflow execution lane.

Sync notes:

- `2026-04-23` `W9-E1-S1-T1` completed: `aidd run` now dispatches workflow execution for `generic-cli`, `claude-code`, `codex`, and `opencode`; unsupported runtime ids remain fail-fast with explicit `unsupported-runtime` classification.
- `2026-04-23` `W9-E1-S1-T2` completed: workflow artifact indexing now records `runtime_exit_metadata` when `runtime-exit.json` exists, and workflow run manifest persistence is regression-covered for runtime-specific command snapshots.
- `2026-04-23` `W9-E1-S1-T3` completed: workflow-path regression coverage now includes non-generic runtime success, failure, no-op, and unsupported-runtime behaviors in CLI tests.
- `2026-04-23` `W9-E1-S1-T4` completed: smoke scenario `harness/scenarios/smoke/plan-stagepack-smoke.yaml` declares cross-runtime workflow execution targets and verify checks for produced `plan.md`, `stage-result.md`, and `validator-report.md`.

Exit evidence:

- `aidd run` can execute workflow-path runs on maintained runtimes without soft-success behavior;
- workflow artifacts and regression expectations remain comparable across runtime lanes.

---

## Wave 10 — release confidence and external readiness (`done`)

### Epic W10-E0 — operator state sync (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W10-E0-S1 — current-state messaging alignment (`done`)
Goal: align operator-facing status text with actual post-W9 behavior before further external-readiness work.

Primary outputs:

- corrected `README.md` runtime-support section
- corrected `README.md` current-CLI section
- corrected `aidd doctor` footer

Touched areas:

- `README.md`
- `src/aidd/cli/`

Dependencies:

- `W9-E1-S1`

Local tasks:

- `W10-E0-S1-T1` (done) Rewrite README runtime-support and current-CLI sections to match maintained workflow and stage runtime behavior after Wave 9.
- `W10-E0-S1-T2` (done) Replace the stale `aidd doctor` footer with wording that names the remaining release-proof and live-E2E gaps instead of calling implemented subsystems roadmap work.

Sync notes:

- `2026-04-23` `W10-E0-S1-T1` completed: README runtime-support and current CLI sections now align with post-W9 workflow and stage runtime parity.
- `2026-04-23` `W10-E0-S1-T2` completed: `aidd doctor` footer now reflects post-W9 runtime parity and calls out remaining release-channel and live-E2E proof work.

Exit evidence:

- `README.md` no longer contradicts runtime parity;
- `uv run aidd doctor` prints current-state wording that matches post-W9 behavior.

### Epic W10-E1 — published install verification (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W10-E1-S1 — release-channel verification (`done`)
Goal: turn `US-09` from documented intent into automated evidence against published artifacts.

Primary outputs:

- PyPI install verification
- `uv tool install` verification
- historical GHCR verification evidence from the pre-no-container alpha policy
- release-checklist evidence requirements

Touched areas:

- `.github/workflows/`
- `docs/release-checklist.md`

Dependencies:

- `W7-E3-S2`
- `W10-E0-S1`

Local tasks:

- `W10-E1-S1-T1` (done) Add a post-publish PyPI verification job to the `release` workflow that retries up to 10 times with 30-second backoff until the tagged version is installable via `pipx`, then runs `aidd --version` and `aidd doctor`.
- `W10-E1-S1-T2` (done) Add a post-publish `uv tool install` verification job that retries up to 10 times with 30-second backoff until the tagged version is installable, then runs `aidd --version` and `aidd doctor`.
- `W10-E1-S1-T3` (done, historical) Add a post-publish GHCR verification job to the `release` workflow that retries up to 10 times with 30-second backoff until the tagged image is pullable, then runs `aidd --version` and `aidd doctor` in the container.
- `W10-E1-S1-T4` (done) Update release documentation so the three verification jobs are required release evidence for tagged builds.

Sync notes:

- `2026-04-23` `W10-E1-S1-T1` completed: release workflow now includes a post-publish PyPI verification job with bounded retries and explicit `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T2` completed: release workflow now includes a post-publish `uv tool install` verification job with bounded retries and explicit `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T3` completed under the then-current release policy: release workflow included a post-publish GHCR verification job with bounded pull retries and containerized `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T4` completed under the then-current release policy: release checklist named the three post-publish verification jobs as required tagged-release evidence.
- Later alpha distribution policy removed Docker/GHCR from the supported release contract; this
  W10 evidence is historical only.

Exit evidence:

- current tagged alpha releases require visible pass/fail evidence for `pipx` and
  `uv tool install`;
- GHCR install-path evidence is retained only as historical pre-policy traceability.

### Epic W10-E2 — adapter conformance (`done`)
Linked stories: `US-07`, `US-08`

#### Slice W10-E2-S1 — maintained-runtime conformance lane (`done`)
Goal: convert adapter-extension safety from distributed evidence into one repeatable conformance lane.

Primary outputs:

- maintained-runtime conformance matrix
- automated conformance execution across maintained runtimes

Touched areas:

- `docs/architecture/`
- `src/aidd/harness/`
- `tests/harness/`
- `.github/workflows/`

Dependencies:

- `W8-E2-S1`
- `W9-E1-S1`
- `W10-E1-S1`

Local tasks:

- `W10-E2-S1-T1` (done) Define the maintained-runtime conformance matrix for probe behavior, capability declaration, raw log capture, failure mapping, question surfacing, timeout behavior, and workspace targeting.
- `W10-E2-S1-T2` (done) Add an automated adapter-conformance lane that executes the matrix for `generic-cli`, `claude-code`, `codex`, and `opencode` and reports per-runtime pass/fail evidence.

Sync notes:

- `2026-04-23` `W10-E2-S1-T1` completed: architecture now includes a maintained-runtime conformance matrix and harness tests assert runtime and dimension completeness.
- `2026-04-23` `W10-E2-S1-T2` completed: harness now includes a deterministic adapter-conformance lane with per-runtime pass/fail tests and CI wiring.

Exit evidence:

- adding a runtime requires adapter-local changes plus one conformance entry, not scattered ad hoc checks.

### Epic W10-E3 — live workflow proof (`done`)
Linked stories: `US-01`, `US-06`, `US-07`

#### Slice W10-E3-S1 — non-generic live workflow evidence (`done`)
Goal: produce one durable public-repo workflow bundle on a maintained non-generic runtime.

Primary outputs:

- one pinned live workflow scenario
- one durable result bundle with stage outputs, verdict, and runtime logs

Touched areas:

- `harness/scenarios/live/`
- `src/aidd/harness/`
- `tests/harness/`
- `docs/e2e/`

Dependencies:

- `W10-E1-S1`
- `W10-E2-S1`

Local tasks:

- `W10-E3-S1-T1` (done) Promote one pinned live scenario to full workflow-path verification on a maintained non-generic runtime and require produced stage-output documents in the bundle.

Sync notes:

- `2026-04-23` `W10-E3-S1-T1` completed: `AIDD-LIVE-005` now serves as the primary non-generic workflow-proof lane with explicit bundle artifact requirements and updated catalog guidance.

Exit evidence:

- one public workflow lane can be rerun with preserved verdict, logs, and produced documents.

---

## Wave 11 — installed live E2E realignment (`done`)

Sync notes:

- `2026-04-23` Wave 11 was opened via `W8-E3-S1` queue-restoration policy to realign live E2E around the installed operator model. Initial queue restoration promotes `W11-E1-S1-T1` to `Next`, `W11-E1-S1-T2` and `W11-E1-S2-T1` to `Soon`, and `W11-E1-S2-T2`, `W11-E1-S2-T3`, `W11-E1-S3-T1`, `W11-E1-S3-T2`, `W11-E1-S3-T3`, `W11-E1-S3-T4`, `W11-E2-S1-T1`, and `W11-E2-S1-T2` to `Parking lot`.
- `2026-04-23` Wave 11 completed: published-package live scenario release proof now runs in release automation, operator/release docs require the evidence, and the backlog queue is empty until the next wave is opened via `W8-E3-S1`.

### Epic W11-E1 — live E2E operator model (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W11-E1-S1 — live E2E contract realignment (`done`)
Goal: redefine live E2E as an installed-CLI operator proof lane instead of a source-checkout eval shortcut.

Primary outputs:

- updated live E2E contract and terminology set
- aligned catalog and architecture wording for install-like operator runs
- separated operator-proof guidance from smoke and conformance parity lanes

Touched areas:

- `README.md`
- `docs/e2e/`
- `docs/architecture/`

Dependencies:

- `W10-E1-S1`
- `W10-E2-S1`
- `W10-E3-S1`

Local tasks:

- `W11-E1-S1-T1` (done) Define install-like semantics for live E2E and rewrite catalog/architecture wording so live scenarios are installed-CLI runs, not source-checkout eval shortcuts.
- `W11-E1-S1-T2` (done) Update README/operator docs to separate live operator proof from smoke/conformance parity lanes.

Sync notes:

- `2026-04-23` `W11-E1-S1-T1` completed: live E2E contract docs now define the lane as installed operator proof with explicit target-repository cwd, install evidence, and lane separation from smoke/conformance.
- `2026-04-23` `W11-E1-S1-T2` completed: README, operator docs, distribution notes, and eval skills now describe live operator proof separately from smoke/conformance parity work.

Exit evidence:

- live E2E docs describe installed-CLI execution from the target repository root;
- operator-facing docs no longer treat source-checkout harness behavior as the canonical live lane.

#### Slice W11-E1-S2 — packaged runtime resources (`done`)
Goal: make installed AIDD self-sufficient by shipping runtime-owned contracts and prompt packs inside the package.

Primary outputs:

- wheel-packaged contracts and prompt packs
- packaged-resource resolver for runtime-owned assets
- external-cwd regression coverage for installed CLI stage/workflow execution

Touched areas:

- `pyproject.toml`
- `src/aidd/core/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W11-E1-S1`

Local tasks:

- `W11-E1-S2-T1` (done) Package contracts and prompt packs into the wheel and expose a packaged-resource resolver.
- `W11-E1-S2-T2` (done) Switch contract/prompt-pack resolution and provenance capture to packaged resources instead of source-tree-relative paths.
- `W11-E1-S2-T3` (done) Add external-cwd regressions for installed CLI stage/workflow execution.

Sync notes:

- `2026-04-23` `W11-E1-S2-T1` completed: wheel builds now force-include `contracts/` and `prompt-packs/` under packaged AIDD resources, and a dedicated resource resolver selects packaged assets outside a source checkout.
- `2026-04-23` `W11-E1-S2-T2` completed: stage contract validation, prompt-pack execution paths, and run-store provenance now resolve against packaged resources instead of assuming `cwd` contains `contracts/` and `prompt-packs/`.
- `2026-04-23` `W11-E1-S2-T3` completed: regression coverage now proves `aidd stage run` resolves runtime-owned assets from an external project directory, and wheel-build tests assert packaged contracts/prompt packs exist.

Exit evidence:

- installed CLI no longer requires `contracts/` or `prompt-packs/` in the operator cwd;
- packaged artifacts and provenance remain available outside a source checkout.

#### Slice W11-E1-S3 — installed live harness execution (`done`)
Goal: run live harness scenarios through an installed local wheel so live E2E matches operator execution semantics.

Primary outputs:

- local-wheel install preparation for live harness runs
- target-repo-root execution model for installed AIDD
- install-aware eval bundle metadata and transcripts
- migrated canonical live scenario expectations for `AIDD-LIVE-005`

Touched areas:

- `src/aidd/harness/`
- `harness/scenarios/live/`
- `tests/harness/`
- `docs/e2e/`

Dependencies:

- `W11-E1-S2`

Local tasks:

- `W11-E1-S3-T1` (done) Build a local wheel and prepare an isolated `uv tool` install for live harness runs.
- `W11-E1-S3-T2` (done) Run installed AIDD from the target repository root and keep `.aidd` rooted in that repository.
- `W11-E1-S3-T3` (done) Persist install-channel, artifact identity, and install transcripts in the eval bundle.
- `W11-E1-S3-T4` (done) Promote `AIDD-LIVE-005` to the first canonical installed live workflow proof and update manifest expectations.

Sync notes:

- `2026-04-23` `W11-E1-S3-T1` completed: live eval runner now prepares installed AIDD artifacts through a dedicated harness install helper, with local-wheel `uv tool` install as the default development and CI path.
- `2026-04-23` `W11-E1-S3-T2` completed: live eval execution now runs installed `aidd` from the prepared target repository root, which keeps `.aidd/` rooted inside that repository.
- `2026-04-23` `W11-E1-S3-T3` completed: result bundles now include `install-transcript.json` plus harness metadata for install channel, artifact identity, execution context, and resource source.
- `2026-04-23` `W11-E1-S3-T4` completed: `AIDD-LIVE-005` now declares installed-operator expectations in its manifest, and harness tests cover the new canonical live install flow.

Exit evidence:

- live harness runs invoke installed AIDD from the prepared target repository root;
- eval bundles capture install provenance alongside runtime and verification evidence.

### Epic W11-E2 — published live artifact proof (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W11-E2-S1 — published live scenario release proof (`done`)
Goal: extend release verification from installability-only checks to one published live workflow proof.

Primary outputs:

- release verification lane that runs one pinned live scenario from the published package
- updated release/operator evidence requirements for published live-scenario proof

Touched areas:

- `.github/workflows/`
- `docs/release-checklist.md`
- `docs/architecture/`

Dependencies:

- `W11-E1-S3`
- `W10-E1-S1`

Local tasks:

- `W11-E2-S1-T1` (done) Add a release verification lane that installs the published package via `uv tool` and runs one pinned live scenario.
- `W11-E2-S1-T2` (done) Update release checklist and operator docs to require published live-scenario evidence.

Sync notes:

- `2026-04-23` `W11-E2-S1-T1` completed: release automation now installs the published package, runs `AIDD-LIVE-005` through the deterministic `generic-cli` release-proof lane, and uploads the resulting eval bundle as durable release evidence.
- `2026-04-23` `W11-E2-S1-T2` completed: the release checklist, operator docs, architecture notes, live E2E catalog, and release-workflow checks now require published live-scenario proof instead of stopping at installability-only validation.

Exit evidence:

- tagged releases prove one published install path can complete a pinned live workflow scenario;
- release docs require that evidence instead of stopping at `aidd doctor`.

---

## Wave 12 — live E2E full-flow and quality gate (`done`)

### Epic W12-E1 — full-flow live operator audit (`done`)
Linked stories: `US-01`, `US-05`, `US-07`, `US-09`, `US-10`

#### Slice W12-E1-S1 — full-flow live contract (`done`)
Goal: redefine live E2E as a deterministic installed-operator full-flow audit with curated issue selection and explicit quality inputs.

Primary outputs:

- full-flow live scenario contract
- live manifest schema for `feature_source` and `quality`
- updated live E2E docs and skills

Touched areas:

- `docs/e2e/`
- `docs/architecture/`
- `.agents/skills/`
- `harness/scenarios/live/`

Dependencies:

- `W11-E2-S1`

Local tasks:

- `W12-E1-S1-T1` (done) Define the full-flow live lane contract and update live E2E docs and skills to require installed `idea -> qa` execution plus quality artifacts.
- `W12-E1-S1-T2` (done) Add live manifest support for `feature_source` and `quality`, and reject live scenarios that are not explicit `idea -> qa`.

Exit evidence:

- live docs and skills describe one canonical installed full-flow audit lane;
- live manifests cannot omit deterministic issue selection or quality inputs.

#### Slice W12-E1-S2 — bounded workflow execution (`done`)
Goal: make workflow bounds explicit so live runs execute only the requested stage window.

Primary outputs:

- `aidd run --from-stage/--to-stage`
- bounded workflow stage selection
- run-manifest support for workflow bounds

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/`
- `tests/cli/`
- `tests/core/`

Dependencies:

- `W12-E1-S1`

Local tasks:

- `W12-E1-S2-T1` (done) Expose `--from-stage` and `--to-stage` on `aidd run` and persist workflow bounds in run metadata.
- `W12-E1-S2-T2` (done) Enforce workflow bounds in stage selection and workflow completion checks.

Exit evidence:

- workflow runs respect explicit stage bounds even when earlier or later stage metadata exists;
- live harness can force `idea -> qa` without relying on implicit workspace state.

#### Slice W12-E1-S3 — deterministic live issue selection (`done`)
Goal: seed full-flow live runs from a curated issue pool and preserve selection evidence.

Primary outputs:

- curated-issue-pool loader support
- selected issue snapshot and context seeding
- migrated full-flow live manifests

Touched areas:

- `src/aidd/harness/`
- `harness/scenarios/live/`
- `tests/harness/`

Dependencies:

- `W12-E1-S1`
- `W12-E1-S2`

Local tasks:

- `W12-E1-S3-T1` (done) Select the first issue from a manifest-curated issue pool and persist issue-selection artifacts in the target repo context and eval bundle.
- `W12-E1-S3-T2` (done) Migrate live scenarios to curated issue pools, full-flow scope, and repo-local quality commands.

Exit evidence:

- live runs derive `user-request.md` and selected-issue evidence from a deterministic issue pool;
- canonical live manifests no longer rely on static implementation-task strings as the only seed.

### Epic W12-E2 — live quality gate (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-07`, `US-10`

#### Slice W12-E2-S1 — quality scoring and artifacts (`done`)
Goal: add a second eval layer that scores flow fidelity, artifact quality, and code quality without changing execution verdict taxonomy.

Primary outputs:

- quality verdict model
- `quality-report.md`
- expanded `grader.json`

Touched areas:

- `src/aidd/evals/`
- `tests/evals/`

Dependencies:

- `W12-E1-S3`

Local tasks:

- `W12-E2-S1-T1` (done) Implement the live quality rubric, verdict mapping, and report writer for flow fidelity, artifact quality, and code quality.
- `W12-E2-S1-T2` (done) Expand `grader.json` to include separate execution and quality sections with issue selection, scores, and blocking findings.

Exit evidence:

- eval bundles contain evidence-backed quality artifacts separate from `verdict.md`;
- execution verdict remains stable while quality gate communicates `pass|warn|fail`.

#### Slice W12-E2-S2 — harness quality phase integration (`done`)
Goal: run repo-local quality checks after live verification and make weak code or weak artifacts fail the quality gate.

Primary outputs:

- quality command transcripts
- harness-integrated quality scoring
- updated live E2E bundle completeness rules

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`
- `tests/cli/`

Dependencies:

- `W12-E2-S1`

Local tasks:

- `W12-E2-S2-T1` (done) Run `quality.commands` after verification, capture `quality-transcript.json`, and feed the results into the live quality scorer.
- `W12-E2-S2-T2` (done) Require full-stage validated outputs plus quality artifacts before a live run is considered clean, and add regression coverage for weak code or weak artifacts escaping execution pass.

Exit evidence:

- no live run reports clean output without both full-flow stage artifacts and quality artifacts;
- quality checks can downgrade or fail a run even when execution technically completed.

Sync notes:

- `2026-04-24` Wave 12 opened via `W8-E3-S1` queue-restoration policy for full-flow live E2E and quality-gate work.
- `2026-04-24` Wave 12 completed: live manifests now require curated issue pools and quality inputs, `aidd run` enforces workflow bounds, eval bundles include issue selection plus quality artifacts, and full regression checks passed.

## Wave 13 — scenario matrix and manual-only live audits (`done`)

### Epic W13-E1 — scenario taxonomy and loader contract (`done`)
Linked stories: `US-01`, `US-05`, `US-07`, `US-09`

#### Slice W13-E1-S1 — scenario metadata taxonomy (`done`)
Goal: add explicit scenario class, feature size, automation lane, and canonical runtime metadata to every scenario manifest and validate the combinations centrally.

Primary outputs:

- scenario metadata model
- loader validation for class/size/lane/runtime
- scenario-level contract tests

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`

Dependencies:

- `W12-E2-S2`

Local tasks:

- `W13-E1-S1-T1` (done) Define the scenario metadata model for `scenario_class`, `feature_size`, `automation_lane`, and `canonical_runtime` in the loader and scenario dataclass.
- `W13-E1-S1-T2` (done) Reject invalid class/size/lane/runtime combinations, including live-in-CI, large-in-CI, noncanonical runtimes, and invalid stage-scope pairings.

Exit evidence:

- every scenario manifest must declare explicit class, size, lane, and canonical runtime metadata;
- invalid live or deterministic combinations fail during scenario loading before execution begins.

#### Slice W13-E1-S2 — deterministic fixture seed support (`done`)
Goal: split deterministic and live feature selection paths so fixture-owned seeds drive deterministic scenarios while curated issue pools remain live-only.

Primary outputs:

- `fixture-seed` feature-source contract
- deterministic-scenario loader support
- migrated deterministic manifests

Touched areas:

- `src/aidd/harness/`
- `harness/scenarios/`
- `tests/harness/`

Dependencies:

- `W13-E1-S1`

Local tasks:

- `W13-E1-S2-T1` (done) Implement `feature_source.mode=fixture-seed` for deterministic scenarios and require `curated-issue-pool` only for live scenarios.
- `W13-E1-S2-T2` (done) Migrate existing deterministic and live manifests to the new taxonomy metadata and feature-source split.

Exit evidence:

- deterministic scenarios no longer depend on curated issue pools;
- live scenarios remain reproducible and deterministic through curated issue selection.

### Epic W13-E2 — representative matrix and manual automation split (`done`)
Linked stories: `US-05`, `US-07`, `US-09`, `US-10`

#### Slice W13-E2-S1 — representative scenario matrix (`done`)
Goal: classify the supported scenario set by class, size, and provider, and close any missing representative buckets without turning the matrix into a full cross-product.

Primary outputs:

- representative matrix source-of-truth doc
- classified scenario catalog
- deterministic large manual fixture workflow coverage

Touched areas:

- `docs/e2e/`
- `harness/scenarios/`
- `tests/`

Dependencies:

- `W13-E1-S2`

Local tasks:

- `W13-E2-S1-T1` (done) Write the representative scenario matrix and classify every maintained scenario by class, size, lane, provider, and canonical runtime.
- `W13-E2-S1-T2` (done) Add or migrate scenarios so the required small, medium, and large representative buckets exist without external live dependency in CI.

Exit evidence:

- the maintained scenario set covers the required representative buckets;
- provider and size expectations are visible in one repo-native source of truth.

#### Slice W13-E2-S2 — manual-only live automation (`done`)
Goal: keep CI and release automation deterministic while moving live external audits into a manual workflow-dispatch lane.

Primary outputs:

- manual live workflow
- release workflow without live E2E
- workflow regression tests

Touched areas:

- `.github/workflows/`
- `tests/`

Dependencies:

- `W13-E1-S2`

Local tasks:

- `W13-E2-S2-T1` (done) Remove live E2E from release automation and keep CI limited to deterministic project-code checks.
- `W13-E2-S2-T2` (done) Add a manual `workflow_dispatch` live workflow that filters scenarios by id, runtime, feature size, and scenario class and uploads eval bundle artifacts.

Exit evidence:

- branch and merge gates depend only on deterministic checks;
- live audits run only through an explicitly manual workflow path.

### Epic W13-E3 — docs, skills, and regression alignment (`done`)
Linked stories: `US-01`, `US-05`, `US-07`, `US-09`, `US-10`

#### Slice W13-E3-S1 — manual live documentation and skills (`done`)
Goal: align product docs and operator skills with the manual-only live lane and the deterministic-vs-live scenario split.

Primary outputs:

- updated README and architecture docs
- updated live and eval skills
- scenario-catalog wording aligned to manual-only live audits

Touched areas:

- `README.md`
- `docs/architecture/`
- `docs/e2e/`
- `.agents/skills/`

Dependencies:

- `W13-E2-S1`
- `W13-E2-S2`

Local tasks:

- `W13-E3-S1-T1` (done) Update README, eval architecture docs, and the live catalog to describe CI as deterministic-only and live E2E as a manual external audit system.
- `W13-E3-S1-T2` (done) Update the `live-e2e` and `aidd-eval` skills to explain scenario taxonomy, manual-only live execution, and `fixture-seed` versus `curated-issue-pool`.

Exit evidence:

- operator docs and skills no longer describe live E2E as a CI or release lane;
- deterministic and live scenario selection rules match the loader contract.

#### Slice W13-E3-S2 — regression and consistency coverage (`done`)
Goal: lock the new scenario taxonomy and workflow separation behind deterministic repo-local tests.

Primary outputs:

- loader regression tests
- docs/workflow consistency tests
- scenario coverage checks

Touched areas:

- `tests/`

Dependencies:

- `W13-E1-S1`
- `W13-E1-S2`
- `W13-E2-S1`
- `W13-E2-S2`
- `W13-E3-S1`

Local tasks:

- `W13-E3-S2-T1` (done) Add loader and workflow regressions for manual-only live rules, deterministic fixture seeds, and canonical runtime validation.
- `W13-E3-S2-T2` (done) Add docs and scenario consistency checks for representative matrix coverage, manual-only live scenarios, and deterministic CI eligibility.

Exit evidence:

- the scenario taxonomy, workflow split, and catalog coverage are enforced by repo-local deterministic tests;
- future live-lane regressions surface without requiring an external live run in CI.

Sync notes:

- `2026-04-24` Wave 13 was opened via `W8-E3-S1` queue-restoration policy to separate deterministic CI checks from manual-only live audits and to classify maintained scenarios by class, size, and provider.
- `2026-04-24` Initial Wave 13 queue restoration promotes `W13-E1-S1-T1` to `Next`, `W13-E1-S1-T2` and `W13-E1-S2-T1` to `Soon`, and `W13-E1-S2-T2`, `W13-E2-S1-T1`, `W13-E2-S1-T2`, `W13-E2-S2-T1`, `W13-E2-S2-T2`, `W13-E3-S1-T1`, `W13-E3-S1-T2`, `W13-E3-S2-T1`, and `W13-E3-S2-T2` to `Parking lot`.
- `2026-04-24` Wave 13 completed: scenario manifests now carry explicit class/size/lane/runtime taxonomy, deterministic lanes use `fixture-seed`, live lanes are manual-only, release automation no longer runs live E2E, and the representative matrix plus regression coverage are synchronized.

## Wave 14 — self-sufficient local live skill (`done`)

### Epic W14-E1 — local live operator skill usability (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W14-E1-S1 — standalone local live runbook (`done`)
Goal: turn the `live-e2e` skill into a self-sufficient local source-checkout playbook for prepared operators running manual live audits.

Primary outputs:

- rewritten `live-e2e` skill
- `aidd-eval` positioning note
- local-launch contract wording

Touched areas:

- `.agents/skills/`

Dependencies:

- `W13-E3-S1`
- `W13-E3-S2`

Local tasks:

- `W14-E1-S1-T1` (done) Rewrite the `live-e2e` skill as a standalone local operator runbook with prerequisites, env vars, preflight, launch steps, validations, artifacts, and first-triage guidance.
- `W14-E1-S1-T2` (done) Add a positioning note in `aidd-eval` that sends local live operators to `live-e2e` for launch guidance while keeping `aidd-eval` focused on generic eval and audit behavior.

Exit evidence:

- an operator can read `live-e2e` and understand what must already exist before a local live run will work;
- the skill no longer depends on external docs to explain the basic local live execution path.

#### Slice W14-E1-S2 — skill contract regression coverage (`done`)
Goal: lock the new local operator contract behind deterministic repo-local docs tests.

Primary outputs:

- docs consistency assertions for `live-e2e`
- skill split regression coverage

Touched areas:

- `tests/`

Dependencies:

- `W14-E1-S1`

Local tasks:

- `W14-E1-S2-T1` (done) Add docs consistency assertions that require `live-e2e` to document source-checkout prerequisites, runtime-command env vars, wrapper-command requirements, local launch examples, `idea -> qa` bounds, bundle location, and explicit non-provisioning limits.

Exit evidence:

- future edits cannot strip the local live operator contract out of `live-e2e` without failing repo-local tests.

Sync notes:

- `2026-04-24` Wave 14 was opened via `W8-E3-S1` queue-restoration policy to make the `live-e2e` skill self-sufficient for prepared local operator runs.
- `2026-04-24` Initial Wave 14 queue restoration promotes `W14-E1-S1-T1` to `Next`, `W14-E1-S1-T2` to `Soon`, and `W14-E1-S2-T1` to `Parking lot`.
- `2026-04-24` Wave 14 completed: `live-e2e` now documents local prerequisites, runtime-command setup, preflight, launch, validations, artifacts, and first-triage guidance directly in the skill; `aidd-eval` points local operators to it; and docs consistency tests lock the contract.

## Wave 15 — readiness recovery and verification hygiene (`done`)

### Epic W15-E0 — queue restoration governance (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W15-E0-S1 — reopen actionable queue (`done`)
Goal: reopen implementation work after the readiness audit found an all-done roadmap with no active backlog entries.

Primary outputs:

- Wave 15 roadmap lane
- restored short backlog queue
- dated sync note

Touched areas:

- `docs/backlog/`

Dependencies:

- `W8-E3-S1`
- `W14-E1-S2`

Local tasks:

- `W15-E0-S1-T1` (done) Define the Wave 15 roadmap lane and promote concrete local task IDs into `Next`, `Soon`, and `Parking lot` so implementation can resume from a valid queue.

Exit evidence:

- `docs/backlog/backlog.md` no longer has an empty actionable queue;
- every promoted backlog item exists as a local task in this Wave 15 roadmap section;
- the sync note records that the empty backlog plus all-done roadmap was the readiness blocker being corrected.

### Epic W15-E1 — deterministic local gate hygiene (`done`)
Linked stories: `US-10`

#### Slice W15-E1-S1 — lint gate recovery (`done`)
Goal: make the deterministic local lint gate pass again without changing product behavior.

Primary outputs:

- line-length-compliant docs consistency test

Touched areas:

- `tests/`

Dependencies:

- `W15-E0-S1`

Local tasks:

- `W15-E1-S1-T1` (done) Fix the long live-E2E docs consistency string literal without changing the asserted contract text.

Exit evidence:

- `uv run --extra dev ruff check .` passes;
- the live-E2E skill contract assertion still checks the same command text.

### Epic W15-E2 — roadmap evidence hygiene (`done`)
Linked stories: `US-10`

#### Slice W15-E2-S1 — historical done-marker normalization (`done`)
Goal: remove ambiguity in completed Wave 12 and Wave 13 local task evidence without changing their completed statuses.

Primary outputs:

- normalized local task done markers for Wave 12 and Wave 13

Touched areas:

- `docs/backlog/roadmap.md`

Dependencies:

- `W15-E1-S1`

Local tasks:

- `W15-E2-S1-T1` (done) Add explicit `(done)` markers to completed Wave 12 and Wave 13 local task bullets where parent slices and sync notes already mark the work complete.

Exit evidence:

- Wave 12 and Wave 13 local task bullets no longer depend only on parent slice status or sync notes for completion evidence;
- no roadmap status is changed from done to another state.

### Epic W15-E3 — external evidence lanes (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W15-E3-S1 — fresh manual live evidence (`done`)
Goal: collect one current manual live E2E bundle after local governance and deterministic gates are green.

Primary outputs:

- fresh manual live eval bundle
- captured runtime logs
- operator verification notes

Touched areas:

- `.aidd/reports/evals/`
- `reports/`

Dependencies:

- `W15-E1-S1`
- prepared runtime authentication and wrapper command outside this repository

Historical blocker:

- `2026-04-25` Local preflight found `AIDD_EVAL_CODEX_COMMAND` and `AIDD_EVAL_OPENCODE_COMMAND` unset, so no AIDD-compatible live runtime wrapper is available for a prepared manual live run in this environment.

Local tasks:

- `W15-E3-S1-T1` (done) Run one prepared manual live E2E scenario with a maintained runtime and preserve the eval artifacts for audit.

Closure evidence:

- `2026-05-06` Later live evidence superseded the original `2026-04-25` wrapper blocker: `eval-live-005-claude-code-20260506T074233Z` completed `AIDD-LIVE-005` with status `pass`, quality gate `warn`, first failure boundary `none`, and no stage timeouts.
- `2026-05-06` Additional maintained-runtime evidence exists for OpenCode: `eval-live-005-opencode-20260506T094747Z` completed `AIDD-LIVE-005` with status `pass` and first failure boundary `none`; the generated quality parser mismatch found during that run was fixed and locally reclassified as `warn` / `ready-with-risks`.
- `2026-05-07` W22 reconciliation preflight confirmed current `aidd doctor` and `aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime claude-code|opencode` both report execution readiness `pass`; no new manual live run was required for backlog reconciliation.

Exit evidence:

- a current `.aidd/reports/evals/<run_id>/` bundle exists for the selected live scenario;
- the report distinguishes runtime, model, document, adapter, and environment evidence.

#### Slice W15-E3-S2 — release-channel evidence capture (`done`)
Goal: prove package release channels on the next release candidate without making live E2E part of release gating.

Primary outputs:

- release-channel verification transcript
- package installation evidence
- historical container smoke evidence from the pre-no-container alpha policy

Touched areas:

- release artifacts
- `reports/`

Dependencies:

- release candidate tag and publishing credentials

Historical blocker:

- `2026-04-25` Local preflight found no release tag pointing at `HEAD`, and no local PyPI or GitHub publishing token environment variables were set for release-channel verification.

Local tasks:

- `W15-E3-S2-T1` (done) Capture PyPI or TestPyPI, `uv tool`, `pipx`, and then-required container smoke evidence for the next release candidate.

Closure evidence:

- `2026-05-06` Later release evidence superseded the original missing-tag/credential blocker: accepted tag `v0.1.0a2` on commit `92c893dbd830292ecab5b684a0a4044ef61a67d6` passed release workflow run `25448551936`.
- `2026-05-06` Accepted release jobs covered `build`, `publish-pypi`, `verify-pypi-install`, `verify-uv-tool-install`, `publish-container`, and `verify-ghcr-install`; installed `pipx`, `uv tool`, and containerized `aidd doctor` all reported `0.1.0a2`. Container evidence is historical only after the later alpha no-container policy.

Exit evidence:

- release verification artifacts show install and CLI smoke behavior from published channels;
- live E2E remains manual-only and outside release gating.

Sync notes:

- `2026-04-25` Wave 15 was opened via `W8-E3-S1` queue-restoration policy after readiness audit findings showed Wave 14 complete, no current `next` slice, and an empty backlog queue.
- `2026-04-25` Initial Wave 15 queue restoration completes `W15-E0-S1-T1`, promotes `W15-E1-S1-T1` to `Next`, `W15-E2-S1-T1` to `Soon`, and parks `W15-E3-S1-T1` plus `W15-E3-S2-T1` for external-evidence work.
- `2026-04-25` `W15-E1-S1-T1` completed: the live-E2E docs consistency assertion remains contract-equivalent while the deterministic lint gate passes; backlog advanced `W15-E2-S1-T1` to `Next`.
- `2026-04-25` `W15-E2-S1-T1` completed: Wave 12 and Wave 13 local task bullets now carry explicit `(done)` markers without changing their completed parent statuses; backlog advanced `W15-E3-S1-T1` to `Next`.
- `2026-04-25` `W15-E3-S1-T1` blocked: local preflight found maintained runtime binaries but no configured AIDD-compatible live runtime wrapper command in `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND`; backlog advanced `W15-E3-S2-T1` to `Next`.
- `2026-04-25` `W15-E3-S2-T1` blocked: no release candidate tag points at `HEAD`, and no local PyPI or GitHub publishing token environment variables were set; backlog queue is empty with both external evidence tasks blocked.
- `2026-05-07` W22 reconciliation closed the stale Wave 15 external-evidence blockers using later accepted evidence: live `AIDD-LIVE-005` bundles from `2026-05-06` satisfy `W15-E3-S1-T1`, and release tag `v0.1.0a2` satisfies `W15-E3-S2-T1`.

---

## Wave 16 — complexity reduction and legacy isolation (`done`)

### Epic W16-E1 — validator complexity reduction (`done`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-10`

#### Slice W16-E1-S1 — shared Markdown parsing (`done`)
Goal: remove duplicated Markdown heading and section parsing across core and validators.

Primary outputs:

- `MarkdownSectionIndex`
- shared contract section extraction helpers
- structural and semantic validator adoption

Touched areas:

- `src/aidd/core/`
- `src/aidd/validators/`

Dependencies:

- Wave 15 deterministic gates

Local tasks:

- `W16-E1-S1-T1` (done) Add shared Markdown section indexing and replace duplicated section extraction in stage registry and validators.

Exit evidence:

- structural and semantic validator tests pass;
- stage registry tests pass.

#### Slice W16-E1-S2 — semantic validator plumbing (`done`)
Goal: reduce public semantic validator plumbing while preserving import compatibility.

Primary outputs:

- semantic API facade
- `SemanticDocumentContext`
- common `ValidationFinding` helpers

Touched areas:

- `src/aidd/validators/`

Dependencies:

- `W16-E1-S1`

Local tasks:

- `W16-E1-S2-T1` (done) Move shared semantic document plumbing behind `validators.semantic_rules.common` and keep `validators.semantic` as the stable public facade.

Exit evidence:

- `tests/validators/test_semantic.py` passes without fixture changes.

#### Slice W16-E1-S3 — semantic stage rule modules (`done`)
Goal: split semantic validation rules by stage/document while preserving the public `validate_semantic_outputs(...)` API.

Primary outputs:

- `SemanticRule` registry keyed by `(stage, document_name)`
- stage-specific rule modules for `idea`, `research`, `plan`, `review-spec`, `tasklist`, `implement`, `review`, and `qa`

Touched areas:

- `src/aidd/validators/semantic_rules/`

Dependencies:

- `W16-E1-S2`

Local tasks:

- `W16-E1-S3-T1` (done) Delegate semantic validation through stage/document rule modules behind the stable facade.

Exit evidence:

- `tests/validators/test_semantic.py` passes without fixture changes.

### Epic W16-E2 — adapter duplication reduction (`done`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W16-E2-S1 — shared adapter probes (`done`)
Goal: remove duplicated runtime probe helpers while keeping runtime-specific capability reports.

Primary outputs:

- shared probe support helpers
- runtime probe modules as compatibility wrappers

Touched areas:

- `src/aidd/adapters/`

Dependencies:

- none

Local tasks:

- `W16-E2-S1-T1` (done) Deduplicate command discovery, version probing, help probing, and capability marker detection across runtime probes.

Exit evidence:

- adapter probe tests pass.

#### Slice W16-E2-S2 — shared subprocess streaming (`done`)
Goal: centralize stdout/stderr streaming, timeout, cancellation, and runtime-log assembly.

Primary outputs:

- shared streamed subprocess runner
- thin runtime-specific run result wrappers

Touched areas:

- `src/aidd/adapters/`

Dependencies:

- `W16-E2-S1`

Local tasks:

- `W16-E2-S2-T1` (done) Replace duplicated adapter streaming loops with a shared streaming helper while preserving runtime result types.

Exit evidence:

- adapter runner tests pass.

#### Slice W16-E2-S3 — adapter surface registry (`done`)
Goal: make CLI and harness dispatch runtime behavior through one adapter surface.

Primary outputs:

- `RuntimeAdapterSurface`
- CLI stage execution dispatch through the surface
- harness conformance lookup through the surface

Touched areas:

- `src/aidd/adapters/`
- `src/aidd/cli/`
- `src/aidd/harness/`

Dependencies:

- `W16-E2-S2`

Local tasks:

- `W16-E2-S3-T1` (done) Add runtime adapter surface registry and route CLI plus harness conformance through it.

Exit evidence:

- adapter and conformance tests pass.

#### Slice W16-E2-S4 — shared adapter path resolution (`done`)
Goal: remove duplicated adapter prompt-pack and stage-brief path resolution helpers.

Primary outputs:

- shared adapter execution path resolver
- native prompt and runtime runners using the shared resolver

Touched areas:

- `src/aidd/adapters/`

Dependencies:

- `W16-E2-S2`

Local tasks:

- `W16-E2-S4-T1` (done) Deduplicate adapter prompt-pack and stage-brief path resolution without changing runtime command shapes.

Exit evidence:

- adapter and conformance tests pass.

### Epic W16-E3 — configuration and CLI complexity (`done`)
Linked stories: `US-01`, `US-08`, `US-09`

#### Slice W16-E3-S1 — runtime config map (`done`)
Goal: make runtime-specific configuration addressable by runtime id while preserving old field access.

Primary outputs:

- `RuntimeConfig`
- `AiddConfig.runtime_configs`
- compatibility access through existing config fields

Touched areas:

- `src/aidd/config.py`
- `src/aidd/cli/`

Dependencies:

- `W16-E2-S3`

Local tasks:

- `W16-E3-S1-T1` (done) Add runtime config map lookup and switch CLI runtime helper functions to it.

Exit evidence:

- config tests and runtime timeout tests pass.

#### Slice W16-E3-S2 — CLI command module split (`done`)
Goal: reduce `cli/main.py` to app assembly and move command handlers into narrow modules.

Primary outputs:

- separate CLI command modules for doctor, run, stage, and eval

Touched areas:

- `src/aidd/cli/`

Dependencies:

- `W16-E3-S1`

Local tasks:

- `W16-E3-S2-T1` (done) Move command handlers out of `cli/main.py` while preserving Typer command names and callback behavior.

Exit evidence:

- CLI tests pass with unchanged command surfaces.

### Epic W16-E4 — eval runner decomposition (`done`)
Linked stories: `US-07`, `US-10`

#### Slice W16-E4-S1 — eval phase extraction (`done`)
Goal: split scenario evaluation into preparation, execution, classification, and persistence phases.

Primary outputs:

- typed phase helpers for the legacy scenario evaluator

Touched areas:

- legacy harness evaluator module

Dependencies:

- `W16-E2-S3`

Local tasks:

- `W16-E4-S1-T1` (done) Extract eval runner preparation, execution, classification, and artifact-writing phases without changing bundle layout.

Exit evidence:

- legacy harness evaluator tests pass.

#### Slice W16-E4-S2 — eval renderer cleanup (`done`)
Goal: simplify stage timing and live quality rendering helpers without changing output shape.

Primary outputs:

- smaller typed eval payload/render helpers

Touched areas:

- `src/aidd/evals/`

Dependencies:

- `W16-E4-S1`

Local tasks:

- `W16-E4-S2-T1` (done) Split stage timing and live quality renderer internals while preserving JSON and Markdown output.

Exit evidence:

- eval tests pass.

### Epic W16-E5 — compatibility shim isolation (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W16-E5-S1 — legacy shim inventory (`done`)
Goal: make retained legacy behavior explicit and removable only through compatibility policy.

Primary outputs:

- compatibility shim inventory
- config shim extraction
- artifact-index shim extraction

Touched areas:

- `src/aidd/`
- `docs/compatibility-policy.md`

Dependencies:

- none

Local tasks:

- `W16-E5-S1-T1` (done) Isolate raw provider command upgrade and missing prompt provenance fallback behind named compatibility helpers.

Exit evidence:

- config and run-store compatibility tests pass;
- compatibility policy lists retained shims.

#### Slice W16-E5-S2 — legacy removal window decision (`done`)
Goal: decide whether retained legacy shims are removed now or kept behind a documented deprecation path.

Primary outputs:

- explicit retained-shim decision in compatibility policy
- removal milestone rule for future compatibility-removal work

Touched areas:

- `docs/compatibility-policy.md`
- `docs/backlog/roadmap.md`

Dependencies:

- `W16-E5-S1`

Local tasks:

- `W16-E5-S2-T1` (done) Keep isolated legacy shims and document the future removal window instead of deleting compatibility behavior in this refactor.

Exit evidence:

- compatibility policy names the retained shims and the earliest removal path.

Sync notes:

- `2026-05-03` Wave 16 was opened after a complexity audit found monolithic validator, adapter, CLI, and eval-runner hotspots while Wave 15 external evidence lanes remained blocked.
- `2026-05-03` Wave 16 completed: semantic validation delegates through stage/document rule modules; adapter probe, streaming, and path-resolution helpers are shared; CLI handlers are split into command modules; eval runner phases and eval render helpers are extracted; retained legacy shims have an explicit future removal path.

---

## Wave 17 — complexity reduction pass 2 (`done`)

### Epic W17-E0 — developer loop determinism (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W17-E0-S1 — deterministic local checks (`done`)
Goal: make contributor checks run through the configured dev environment instead of relying on ambient Python state.

Primary outputs:

- deterministic Makefile check commands
- documented dev-extra check commands
- ignored incidental local lockfile artifact

Touched areas:

- root developer docs
- root tooling files

Dependencies:

- Wave 16 complexity baseline

Local tasks:

- `W17-E0-S1-T1` (done) Stabilize local check commands so lint, typecheck, and test use the dev-extra environment consistently.

Exit evidence:

- `uv run --extra dev ruff check .` passes;
- `uv run --extra dev python -m mypy src` passes;
- `uv run --extra dev pytest -q` passes.

### Epic W17-E1 — core and CLI orchestration reduction (`done`)
Linked stories: `US-01`, `US-03`, `US-04`, `US-05`, `US-06`, `US-10`

#### Slice W17-E1-S1 — stage-run CLI helper extraction (`done`)
Goal: keep the Typer command surface stable while moving runtime setup, adapter execution, repair retries, and reporting out of the command handler.

Primary outputs:

- internal stage-run options object
- internal stage-run executor
- thinner `cli/stage.py`

Touched areas:

- `src/aidd/cli/`

Dependencies:

- `W17-E0-S1`

Local tasks:

- `W17-E1-S1-T1` (done) Extract `aidd stage run` execution support into internal CLI helpers while preserving command behavior.

Exit evidence:

- CLI stage tests pass.

#### Slice W17-E1-S2 — repair-budget terminal helper extraction (`done`)
Goal: reduce `core/stage_runner.py` by moving terminal repair-budget result rewriting into a narrow helper without changing the public facade.

Primary outputs:

- focused repair budget terminal-output helper
- direct helper characterization tests
- stable public orchestration facade

Touched areas:

- `src/aidd/core/`

Dependencies:

- `W17-E1-S1`

Local tasks:

- `W17-E1-S2-T1` (done) Extract repair-budget terminal-result rewriting from stage orchestration into a focused core helper.

Exit evidence:

- core stage-runner and repair-flow tests pass.

#### Slice W17-E1-S3 — stage orchestration phase modules (`done`)
Goal: keep `run_single_stage_orchestration(...)` stable while moving preparation, invocation, output discovery, validation, repair-budget transitions, and interview routing into focused internal phase modules.

Primary outputs:

- stage preparation and invocation modules
- stage output discovery/publication module
- stage validation transition module
- stage interview-routing module
- shared stage orchestration model objects

Touched areas:

- `src/aidd/core/`

Dependencies:

- `W17-E1-S2`

Local tasks:

- `W17-E1-S3-T1` (done) Split stage orchestration phases out of `core/stage_runner.py` while preserving the public facade and compatibility aliases.

Exit evidence:

- core stage-runner, repair-flow, stage-terminal, and CLI stage tests pass.

### Epic W17-E2 — adapter surface cleanup (`done`)
Linked stories: `US-01`, `US-06`, `US-08`

#### Slice W17-E2-S1 — shared adapter command helpers (`done`)
Goal: remove remaining runtime-runner duplication while keeping runtime-specific command differences local.

Primary outputs:

- shared configured-command parsing
- shared AIDD execution environment builder
- shared runtime log persistence helper

Touched areas:

- `src/aidd/adapters/`

Dependencies:

- `W17-E0-S1`

Local tasks:

- `W17-E2-S1-T1` (done) Add shared adapter command, environment, and runtime-artifact helpers used by maintained runtime runners.

Exit evidence:

- adapter runner tests pass.

#### Slice W17-E2-S2 — adapter context validation boundary (`done`)
Goal: remove repeated command-context validation from runtime runners and keep reusable interview persistence behind an explicit core-owned adapter boundary.

Primary outputs:

- shared stage command-context validation helper
- explicit core adapter interview persistence boundary
- stable runtime-specific command construction in adapter modules

Touched areas:

- `src/aidd/adapters/`
- `src/aidd/core/`

Dependencies:

- `W17-E2-S1`

Local tasks:

- `W17-E2-S2-T1` (done) Consolidate adapter context validation and route reusable interview persistence through a core-owned adapter boundary.

Exit evidence:

- adapter tests pass.

### Epic W17-E3 — validator helper reduction (`done`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-10`

#### Slice W17-E3-S1 — semantic helper module split (`done`)
Goal: reduce the common semantic validator module by moving reusable parsing and placeholder helpers into focused internal modules.

Primary outputs:

- placeholder helper module
- Markdown block extraction helper module
- stable `validators.semantic` facade

Touched areas:

- `src/aidd/validators/semantic_rules/`

Dependencies:

- `W17-E0-S1`

Local tasks:

- `W17-E3-S1-T1` (done) Split common semantic placeholder and Markdown extraction helpers into focused internal modules.

Exit evidence:

- semantic validator tests pass.

#### Slice W17-E3-S2 — semantic rule helper and stage-rule split (`done`)
Goal: continue reducing common semantic-rule complexity by moving id extraction, evidence parsing, risk parsing, and finding factories into focused modules, then convert the largest stage validators into ordered small rule functions.

Primary outputs:

- task/citation/milestone id extraction helper module
- implementation evidence helper module
- risk and QA metadata helper module
- validation finding factory module
- ordered helper functions for implementation, tasklist, QA, and review validators

Touched areas:

- `src/aidd/validators/semantic_rules/`

Dependencies:

- `W17-E3-S1`

Local tasks:

- `W17-E3-S2-T1` (done) Split remaining common semantic helpers and decompose large stage validators without changing fixture formats or report shape.

Exit evidence:

- semantic validator tests pass.

### Epic W17-E4 — eval and harness reporting reduction (`done`)
Linked stories: `US-07`, `US-10`

#### Slice W17-E4-S1 — eval scoring helper extraction (`done`)
Goal: reduce branching in live quality and timing payload construction while preserving report output shape.

Primary outputs:

- live quality scoring helpers
- stage timing evidence model and step-evidence helper

Touched areas:

- `src/aidd/evals/`

Dependencies:

- `W17-E0-S1`

Local tasks:

- `W17-E4-S1-T1` (done) Extract eval quality scoring and timing step payload helpers without changing generated artifacts.

Exit evidence:

- eval quality and stage-timing tests pass.

#### Slice W17-E4-S2 — eval runner report context (`done`)
Goal: reduce high-arity eval report persistence by grouping stable report inputs into typed context objects.

Primary outputs:

- eval report persistence context
- runtime log source context

Touched areas:

- `src/aidd/harness/`

Dependencies:

- `W17-E4-S1`

Local tasks:

- `W17-E4-S2-T1` (done) Introduce typed eval report persistence context while preserving result bundle layout.

Exit evidence:

- harness eval-runner tests pass.

#### Slice W17-E4-S3 — eval runner phase modules (`done`)
Goal: keep the legacy evaluator result bundle shape stable while moving preparation, execution, classification, source-artifact rendering, report persistence, and grader payload construction into focused internal modules.

Primary outputs:

- eval run model objects
- eval preparation module
- eval execution module
- eval classification module
- eval report persistence and grader-payload module
- compatibility aliases for existing white-box tests and local debug scripts

Touched areas:

- `src/aidd/harness/`

Dependencies:

- `W17-E4-S2`

Local tasks:

- `W17-E4-S3-T1` (done) Decompose the legacy harness evaluator into phase modules while preserving behavior and artifact layout.

Exit evidence:

- harness eval-runner and eval scoring tests pass.

### Epic W17-E5 — retained compatibility cleanup (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W17-E5-S1 — config compatibility constructor isolation (`done`)
Goal: keep documented compatibility shims while reducing legacy constructor noise in configuration loading.

Primary outputs:

- named legacy runtime-config normalization helper
- stable read-only legacy config properties

Touched areas:

- `src/aidd/config.py`

Dependencies:

- `W17-E0-S1`

Local tasks:

- `W17-E5-S1-T1` (done) Move legacy `AiddConfig` constructor field normalization behind a named compatibility helper.

Exit evidence:

- config and run-store compatibility tests pass.

Sync notes:

- `2026-05-03` Wave 17 opened as a second complexity-reduction pass after the Wave 16 refactor left concentrated complexity in stage orchestration, CLI stage execution, adapter runners, semantic helpers, and eval reporting.
- `2026-05-03` Wave 17 completed with deterministic dev-extra checks, a thin CLI stage handler, shared adapter runner helpers, focused repair-budget terminal helpers, semantic placeholder/block helper modules, eval scoring/report contexts, and isolated config compatibility normalization.
- `2026-05-03` Wave 17 corrective audit completed the remaining planned decomposition: stage orchestration phase modules, shared adapter context validation, deeper semantic helper/stage-rule split, stage-timing evidence modeling, and eval runner phase modules.

---

## Wave 18 — architecture and documentation conformance closure (`done`)

### Epic W18-E1 — architecture truth baseline (`done`)
Linked stories: `US-01`, `US-02`, `US-03`, `US-04`, `US-05`, `US-06`, `US-07`, `US-08`, `US-09`, `US-10`

#### Slice W18-E1-S1 — implemented architecture alignment (`done`)
Goal: make architecture and contract documentation describe the implemented runtime, observability, interview, repair, and artifact-ownership boundaries without overstating incomplete target behavior.

Primary outputs:

- current-state architecture corrections
- adapter protocol/runtime matrix alignment
- artifact ownership clarifications

Touched areas:

- `docs/architecture/`
- `contracts/`
- `prompt-packs/stages/`

Dependencies:

- Wave 17 architecture and code decomposition baseline

Local tasks:

- `W18-E1-S1-T1` (done) Align architecture protocol docs with the implemented runtime request/result shape, runtime tiers, observability state, and failure taxonomy.
- `W18-E1-S1-T2` (done) Clarify stage contract and prompt-pack ownership wording for runtime-authored drafts and AIDD-owned final/control artifacts.

Exit evidence:

- architecture docs no longer describe `codex` or `opencode` as merely planned adapters;
- target architecture distinguishes implemented behavior from follow-up targets for normalized events, question loops, repair history, and stage timing;
- contract and prompt-pack wording consistently identifies `repair-brief.md` as AIDD-owned and `validator-report.md` as AIDD-canonical after validation.

### Epic W18-E2 — root and operator documentation refresh (`done`)
Linked stories: `US-01`, `US-06`, `US-07`, `US-09`, `US-10`

#### Slice W18-E2-S1 — current repository status refresh (`done`)
Goal: remove bootstrap-era wording from current operator-facing documents and mark historical inventory/report files so they cannot be mistaken for the present source of truth.

Primary outputs:

- refreshed README and operator docs
- historical markers for archival manifests/reports
- compatibility wording aligned with runtime tiers

Touched areas:

- `README.md`
- `docs/operator-*.md`
- `docs/compatibility-policy.md`
- `MANIFEST.md`
- `reports/repo-readiness/`
- `docs/backlog/rebuild-plan.md`

Dependencies:

- `W18-E1-S1`

Local tasks:

- `W18-E2-S1-T1` (done) Refresh README, operator support, troubleshooting, and compatibility docs to current CLI/runtime state.
- `W18-E2-S1-T2` (done) Mark stale generated manifests, readiness reports, and rebuild plan as historical snapshots when they are not maintained as live inventory.

Exit evidence:

- current docs do not describe the repo as a bootstrap skeleton or starter repository;
- historical files explicitly warn readers not to use their counts, Wave status, or test totals as current evidence.

### Epic W18-E3 — documentation drift regression checks (`done`)
Linked stories: `US-08`, `US-10`

#### Slice W18-E3-S1 — architecture documentation consistency tests (`done`)
Goal: keep the corrected architecture and README language from drifting back to stale bootstrap or planned-adapter claims.

Primary outputs:

- docs consistency regression tests

Touched areas:

- `tests/test_docs_consistency.py`

Dependencies:

- `W18-E1-S1`
- `W18-E2-S1`

Local tasks:

- `W18-E3-S1-T1` (done) Add docs consistency checks for stale bootstrap wording, runtime tier alignment, and artifact-ownership statements.

Exit evidence:

- targeted docs consistency tests fail when canonical docs reintroduce obsolete bootstrap/starter wording or planned-adapter claims for registered runtimes.

Sync notes:

- `2026-05-04` Wave 18 was opened via `W8-E3-S1` queue-restoration policy after an architecture/documentation audit found docs lagging behind the implemented runtime surface and Wave 16/17 refactors. Initial queue restoration promotes `W18-E1-S1-T1` to `Next`, `W18-E1-S1-T2` and `W18-E2-S1-T1` to `Soon`, and `W18-E2-S1-T2` plus `W18-E3-S1-T1` to `Parking lot`.
- `2026-05-04` Wave 18 completed: architecture docs now describe the implemented request/result adapter boundary, runtime tiers, observability state, question/repair limits, and failure taxonomy; contracts and prompt packs clarify artifact ownership; README/operator docs no longer describe the repo as bootstrap; historical snapshots are labeled archival; docs consistency tests cover the drift checks.

---

## Wave 19 — user-story implementation closure (`done`)

### Epic W19-E1 — runtime-native question and event closure (`done`)
Linked stories: `US-01`, `US-05`, `US-06`, `US-07`, `US-08`, `US-10`

#### Slice W19-E1-S1 — structured event and native question bridge (`done`)
Goal: map adapter-observed structured runtime events into durable attempt artifacts and route native question/pause events through the existing interview documents.

Primary outputs:

- runtime JSONL/event artifact persistence
- native question event bridge to `questions.md`
- CLI regression coverage for native-question blocking

Touched areas:

- `src/aidd/adapters/`
- `src/aidd/core/`
- `tests/cli/`

Dependencies:

- Wave 18 current-state architecture baseline

Local tasks:

- `W19-E1-S1-T1` (done) Wire adapter-detected question and pause events into the standard `questions.md` persistence path for structured-event-capable adapters.
- `W19-E1-S1-T2` (done) Persist emitted structured runtime events as optional attempt-level `runtime.jsonl` and `events.jsonl` artifacts.
- `W19-E1-S1-T3` (done) Add CLI regression coverage proving unresolved native questions block progression like document-authored blocking questions.

Exit evidence:

- adapter-emitted JSONL question events create durable `questions.md`;
- unresolved native questions produce a blocked stage transition;
- attempt artifact indexes include optional JSONL logs when those files exist.

### Epic W19-E2 — repair history and final artifact accountability (`done`)
Linked stories: `US-04`, `US-10`

#### Slice W19-E2-S1 — normal stage-run repair history finalization (`done`)
Goal: preserve repair attempts in stage metadata and the final `stage-result.md` during ordinary CLI stage runs.

Primary outputs:

- repair-history snapshot calls in the normal stage-run path
- final successful repair publication with repair attempts preserved
- exhausted-budget regression coverage

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/cli/`

Dependencies:

- `W19-E1-S1`

Local tasks:

- `W19-E2-S1-T1` (done) Make normal stage-run finalization write repair history into stage metadata and `stage-result.md` when repair is used.
- `W19-E2-S1-T2` (done) Add regression coverage for successful repair-after-invalid-output, exhausted repair budget, and no-repair happy path metadata.

Exit evidence:

- final published `stage-result.md` records initial failure and repair success when repair succeeds;
- exhausted repair budget records failed validation attempts in stage metadata;
- no-repair happy path leaves repair history empty.

### Epic W19-E3 — harness/eval artifact propagation (`done`)
Linked stories: `US-06`, `US-07`, `US-10`

#### Slice W19-E3-S1 — optional JSONL propagation into eval bundles (`done`)
Goal: include emitted structured runtime/event JSONL in durable eval bundles and failure-boundary analysis without changing existing bundle compatibility.

Primary outputs:

- eval bundle copying for optional `runtime.jsonl` and `events.jsonl`
- normalized-event failure-boundary input
- harness regression coverage

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`

Dependencies:

- `W19-E1-S1`

Local tasks:

- `W19-E3-S1-T1` (done) Copy emitted attempt-level `runtime.jsonl` and `events.jsonl` into eval result bundles when present.
- `W19-E3-S1-T2` (done) Extend eval regression coverage so emitted events can drive first-failure boundary selection and durable bundle metadata.

Exit evidence:

- eval bundles include optional JSONL artifacts only when source attempts emitted them;
- log analysis can select `events.jsonl` as the first decisive failure signal.

### Epic W19-E4 — release/install and compatibility evidence (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W19-E4-S1 — compatibility and install evidence alignment (`done`)
Goal: align automated compatibility checks with the documented Python support window and keep installed-operator evidence lanes explicit.

Primary outputs:

- Python 3.14 CI matrix coverage
- compatibility-policy alignment
- release/live evidence lane retained as manual or release-specific evidence

Touched areas:

- `.github/workflows/`
- `docs/compatibility-policy.md`
- `tests/`

Dependencies:

- Wave 18 operator documentation baseline

Local tasks:

- `W19-E4-S1-T1` (done) Align CI compatibility checks with the documented Python 3.12 through 3.14 support window.
- `W19-E4-S1-T2` (done) Preserve installed-package smoke proof coverage through existing release and release-live-proof tests without adding a live provider CI gate.
- `W19-E4-S2-T1` (done) Keep manual live E2E evidence separated from provider/env blockers through the existing manual live workflow and runtime preflight tests.

Exit evidence:

- CI matrix lists Python 3.12, 3.13, and 3.14;
- release installability tests cover the current supported `pipx` and `uv tool` workflow shape;
- manual live runtime preflight tests continue to classify missing provider/env setup before repository prep.

Sync notes:

- `2026-05-04` Wave 19 opened via `W8-E3-S1` queue-restoration policy after the user-story coverage audit found implementation gaps in native question/event routing, repair-history finalization, eval JSONL propagation, and compatibility evidence.
- `2026-05-04` Wave 19 completed: structured adapter JSONL is persisted as optional attempt artifacts; native question/pause events route into `questions.md`; normal repair runs preserve repair history in final `stage-result.md`; eval bundles copy optional JSONL artifacts and use `events.jsonl` in failure-boundary analysis; CI now covers Python 3.12 through 3.14.

---

## Wave 20 — gap intake and product-scope expansion (`done`)

### Epic W20-E1 — evidence closure (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W20-E1-S1 — live E2E evidence refresh (`done`)
Goal: produce a current live E2E readiness decision and either preserve a fresh audit bundle or document the exact provider/environment blocker.

Primary outputs:

- live E2E preflight decision
- manual live E2E audit bundle or explicit blocker note

Touched areas:

- `docs/e2e/`
- `harness/scenarios/live/`

Dependencies:

- Wave 19 compatibility and eval artifact baseline

Local tasks:

- `W20-E1-S1-T1` (done) Refresh the live E2E preflight and current evidence decision for one maintained runtime.
- `W20-E1-S1-T2` (done) Run one maintained-runtime manual live E2E and preserve the audit bundle, or document the explicit provider/env blocker if preflight fails.

Evidence:

- `2026-05-04` Local `uv run aidd doctor` reported `codex` and `opencode` provider and execution command readiness.
- `2026-05-04` `uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex` passed for `AIDD-LIVE-005` with default native Codex command `codex exec --full-auto --skip-git-repo-check --json -`.
- `2026-05-04` Fallback `opencode` run `eval-live-005-opencode-20260504T121644Z` produced a durable eval bundle at `.aidd/reports/evals/eval-live-005-opencode-20260504T121644Z` with status `fail`, quality gate `fail`, and first failure boundary `adapter` / `non_zero_exit` at the `idea` stage.
- `2026-05-04` Default `codex` attempt `eval-live-005-codex-20260504T120734Z` did not finalize beyond partial issue-selection evidence before it was stopped; do not use that partial bundle as a clean live audit.

Exit evidence:

- maintainers can tell whether fresh live E2E evidence exists for `US-07`;
- missing provider or environment setup is recorded as a blocker, not hidden as an implementation gap.

#### Slice W20-E1-S2 — release and install evidence refresh (`done`)
Goal: produce a current release/install evidence decision for the supported delivery channels without making live E2E a release gate.

Primary outputs:

- release/install prerequisite decision
- candidate install evidence or explicit release-channel blocker

Touched areas:

- `docs/release-checklist.md`
- `docs/architecture/distribution-and-development.md`

Dependencies:

- Wave 19 compatibility and release workflow baseline

Historical blockers:

- `2026-05-04` Local prerequisite refresh found no release candidate tag pointing at `HEAD` and no local PyPI/TestPyPI/GHCR token environment variables (`PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN`, `TWINE_USERNAME`, `TWINE_PASSWORD`, `GITHUB_TOKEN`, `GHCR_TOKEN`, `CR_PAT`) set for release-channel evidence capture.
- `2026-05-06` Tagged release attempt `v0.1.0a0` reached GitHub Actions but `publish-pypi` failed with PyPI Trusted Publishing `invalid-publisher`; package install verification did not run, so release/install evidence remains blocked until the PyPI trusted publisher is configured for repository `GrinRus/ai_driven_dev_v2`, workflow `.github/workflows/release.yml`, environment `pypi`, and package `ai-driven-dev-v2`.
- `2026-05-06` Tagged release attempt `v0.1.0a1` passed PyPI publish, `pipx`, `uv tool`, and container publish jobs, but `verify-ghcr-install` failed because the Docker pull reference used uppercase owner `GrinRus`; the same run exposed a stale CLI version source where installed package `0.1.0a1` reported `aidd 0.1.0a0`.

Local tasks:

- `W20-E1-S2-T1` (done) Refresh release/install evidence prerequisites for the next candidate across PyPI or TestPyPI, `pipx`, `uv tool`, and container paths.
- `W20-E1-S2-T2` (done) Capture PyPI or TestPyPI, `pipx`, `uv tool`, and then-required container smoke evidence for the next release candidate.
- `W20-E1-S2-T3` (done) Disable automatic GHCR `latest` image tagging for prerelease tags and cover the release-workflow tag policy with regression tests.

Evidence:

- `2026-05-06` PR `#13` was merged into `main` as `aa3655998227e6da2a979b06d2c87543adbf4734`; local `main` was fast-forwarded to `origin/main`, `pyproject.toml` version was confirmed as `0.1.0a0`, and `v0.1.0a0` did not exist locally or on `origin` before tagging.
- `2026-05-06` Pre-tag deterministic gate passed on `aa3655998227e6da2a979b06d2c87543adbf4734`: `uv run --extra dev ruff check .`, `uv run --extra dev python -m mypy src`, and `uv run --extra dev pytest -q` (`749 passed`).
- `2026-05-06` Annotated tag `v0.1.0a0` was pushed to `aa3655998227e6da2a979b06d2c87543adbf4734`; release workflow run `25437182363` (`https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25437182363`) completed with overall `failure`.
- `2026-05-06` Release jobs: `build` passed, `publish-container` passed, `publish-pypi` failed, `verify-pypi-install` skipped, `verify-uv-tool-install` skipped, and `verify-ghcr-install` skipped because the PyPI publish dependency failed.
- `2026-05-06` PyPI failure evidence: `publish-pypi` failed during Trusted Publishing token exchange with `invalid-publisher`; rendered claims included `sub=repo:GrinRus/ai_driven_dev_v2:environment:pypi`, `workflow_ref=GrinRus/ai_driven_dev_v2/.github/workflows/release.yml@refs/tags/v0.1.0a0`, and `environment=pypi`.
- `2026-05-06` Partial GHCR evidence: `publish-container` pushed `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a0`, `ghcr.io/grinrus/ai-driven-dev-v2:sha-aa36559`, and `ghcr.io/grinrus/ai-driven-dev-v2:latest` with digest `sha256:994a1134a2b10e6c68c7abccfc3c0a4e470e1ec51143979dd9c7e8a9ac408918`; this is not accepted install evidence because `verify-ghcr-install` was skipped.
- `2026-05-06` The release workflow now sets `docker/metadata-action` `flavor: latest=false` and keeps `latest` behind the explicit stable-tag raw-tag condition so future prerelease tags do not get `latest` from metadata-action defaults; `uv run --extra dev pytest tests/test_release_workflow.py -q` passed.
- `2026-05-06` Annotated tag `v0.1.0a1` was pushed to `a58edc0d0267a5ca528efab3f4caaf8e7b9854c6`; release workflow run `25446909468` (`https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25446909468`) completed with overall `failure`.
- `2026-05-06` `v0.1.0a1` job results: `build`, `publish-pypi`, `verify-pypi-install`, `verify-uv-tool-install`, and `publish-container` passed; `verify-ghcr-install` failed after 10 attempts because `docker pull ghcr.io/GrinRus/ai-driven-dev-v2:v0.1.0a1` is an invalid uppercase Docker repository reference.
- `2026-05-06` `v0.1.0a1` partial evidence: PyPI published `https://pypi.org/project/ai-driven-dev-v2/0.1.0a1/`; container publish produced `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a1` and `ghcr.io/grinrus/ai-driven-dev-v2:sha-a58edc0` without `latest`, digest `sha256:b4d8d247288a340801b80458db5fa1a3804a5d79fb939ae687d5f86bd507e32c`; evidence was rejected because GHCR verification failed and installed CLI output still reported `0.1.0a0`.
- `2026-05-06` PR `#16` fixed the GHCR verification reference by lowercasing the owner, moved CLI version reporting to package metadata with a source-tree fallback, added regressions, and bumped the next release candidate to `0.1.0a2`; CI passed for Python 3.12, 3.13, 3.14, adapter conformance, and build.
- `2026-05-06` Pre-tag deterministic gate passed on merged `main` commit `92c893dbd830292ecab5b684a0a4044ef61a67d6`: `uv run --extra dev ruff check .`, `uv run --extra dev python -m mypy src`, and `uv run --extra dev pytest -q` (`751 passed`).
- `2026-05-06` Annotated tag `v0.1.0a2` was pushed to `92c893dbd830292ecab5b684a0a4044ef61a67d6`; release workflow run `25448551936` (`https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25448551936`) completed with overall `success`.
- `2026-05-06` Accepted `v0.1.0a2` job results: `build`, `publish-pypi`, `verify-pypi-install`, `verify-uv-tool-install`, `publish-container`, and `verify-ghcr-install` all passed. PyPI version: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a2/`.
- `2026-05-06` `v0.1.0a2` install verification: `pipx` installed `ai-driven-dev-v2==0.1.0a2`, `aidd --version` returned `aidd 0.1.0a2`, and `aidd doctor` reported `Version 0.1.0a2`; `uv tool` produced the same version and doctor evidence.
- `2026-05-06` `v0.1.0a2` GHCR verification pulled `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2`, then containerized `aidd --version` and `aidd doctor` both reported `0.1.0a2`. Published GHCR tags were `v0.1.0a2` and `sha-92c893d`; no `latest` tag was produced for this prerelease. Container digest: `sha256:fc344386c4909d0dcfc74753583fc32c469621212e133f52fce2fbd39147d45d`.

Exit evidence:

- current `US-09` alpha install evidence exists for PyPI, `pipx`, and `uv tool`;
- GHCR/container evidence from earlier prerelease attempts is retained as historical traceability
  only and is no longer part of the supported alpha distribution contract;
- prior missing release candidate, trusted publisher, and GHCR verification issues are recorded as historical blockers.

#### Slice W20-E1-S3 — live eval failure triage (`done`)
Goal: turn the current failing live evidence into an owned fix or an explicit external blocker before requesting another live audit.

Primary outputs:

- live eval failure triage note
- focused regression for any AIDD-owned failure found during triage
- post-fix live rerun evidence or next explicit blocker

Touched areas:

- `docs/backlog/`
- `contracts/documents/`
- `src/aidd/core/`
- `src/aidd/adapters/opencode/`
- `tests/adapters/`
- `tests/core/`

Dependencies:

- `W20-E1-S1`

Historical blocker:

- `2026-05-04` Post-parser-fix OpenCode live rerun `eval-live-005-opencode-20260504T135544Z` reached the `idea` repair attempt and produced repaired documents, but the native OpenCode process hit the configured adapter timeout before AIDD could record a successful stage outcome. The run is blocked as runtime/provider timeout evidence, not a clean `US-07` live audit.

Local tasks:

- `W20-E1-S3-T1` (done) Triage the `AIDD-LIVE-005` OpenCode audit bundle and partial Codex bundle, recording the first owned failure boundary and reproduction command.
- `W20-E1-S3-T2` (done) Add a focused OpenCode native command regression for the AIDD-owned live failure.
- `W20-E1-S3-T3` (done) Rerun `AIDD-LIVE-005` after the OpenCode native command fix and preserve a clean audit bundle or updated blocker.
- `W20-E1-S3-T4` (done) Add a focused interview document parser regression and fix for the AIDD-owned plan-stage malformed `answers.md` failure found by the rerun.
- `W20-E1-S3-T5` (done) Rerun `AIDD-LIVE-005` after the interview document parser fix and preserve a clean audit bundle or updated blocker.

Evidence:

- `2026-05-04` Triage inspected `.aidd/reports/evals/eval-live-005-opencode-20260504T121644Z` and found an AIDD-owned OpenCode native command assembly defect: the operator message followed `--file`, and the current `opencode run` parser treated `Follow the attached AIDD stage request.` as a second file path.
- `2026-05-04` Reproduction used the then-current live evaluator command for `harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode`; the failing bundle records `adapter` / `non_zero_exit` at `idea`.
- `2026-05-04` The Codex run `eval-live-005-codex-20260504T120734Z` still has only partial issue-selection evidence and is not a clean audit.
- `2026-05-04` OpenCode preflight passed for `AIDD-LIVE-005` after the native command fix: `/opt/homebrew/bin/opencode`, version `1.4.10`, native execution command `opencode run --format json --dangerously-skip-permissions`.
- `2026-05-04` Fresh rerun `eval-live-005-opencode-20260504T130401Z` failed at validation, not adapter launch: runtime exited successfully through `idea`, `research`, and `plan` attempts, but `plan` attempt 3 ended `failed` with `INTERVIEW-MALFORMED-DOCUMENT` in `answers.md`.
- `2026-05-04` The first owned failure boundary is AIDD interview parsing: extra summary bullets outside the canonical `Answers` section were interpreted as answer entries. `src/aidd/core/interview.py` now parses only the canonical `Questions` or `Answers` section when present, with regression coverage in `tests/core/test_interview.py`.
- `2026-05-04` Post-parser-fix preflight passed with `uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode`.
- `2026-05-04` Post-parser-fix rerun `eval-live-005-opencode-20260504T135544Z` produced status `fail`, quality gate `fail`, first failure boundary `adapter`, first failure note `runtime.log: Adapter outcome: timeout`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260504T135544Z`.
- `2026-05-04` The failed rerun shows `idea` attempt 1 exited successfully but needed repair; `idea` attempt 2 timed out. The worktree artifacts show the repair attempt wrote a valid `stage-result.md` and `validator-report.md`, but the adapter recorded `timeout`/`-15`, so AIDD stopped before `research` and the live quality gate correctly failed.
- `2026-05-07` W22 reconciliation closed `W20-E1-S3-T5` as completed by its own preserved rerun evidence: the task required either a clean bundle or an updated blocker, and `eval-live-005-opencode-20260504T135544Z` recorded the updated timeout blocker later addressed by `W20-E1-S4`.

Exit evidence:

- the original OpenCode live failure has an AIDD-owned regression rather than an ambiguous provider blocker;
- the fresh rerun records a later AIDD-owned validation/parser boundary;
- the post-parser-fix rerun is preserved as explicit runtime/provider timeout evidence rather than a clean live audit.

#### Slice W20-E1-S4 — live timeout policy and clean evidence rerun (`done`)
Goal: make the live OpenCode timeout policy explicit, then attempt one clean `AIDD-LIVE-005` evidence rerun before falling back to the canonical Codex lane.

Primary outputs:

- generated OpenCode live stage-timeout profile
- post-timeout-profile OpenCode live rerun evidence
- optional Codex fallback rerun evidence if OpenCode remains provider/runtime blocked

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`
- `docs/backlog/`
- `harness/scenarios/live/`

Dependencies:

- `W20-E1-S3`

Historical blocker:

- `2026-05-04` Post-timeout-profile OpenCode rerun `eval-live-005-opencode-20260504T143938Z` no longer failed from adapter timeout, but the live audit still is not clean. The first failure boundary moved to `validation`: `idea` attempt 3 exited successfully from the runtime but failed validation with `SEM-INCOMPLETE-SECTION` because `Open questions` was not rendered as bullet items after the repair budget was exhausted.

Local tasks:

- `W20-E1-S4-T1` (done) Update generated live runtime config so OpenCode has an explicit timeout profile: `timeout_seconds = 1200`, `idea = 1500`, `research = 1500`, `plan = 1500`, `review-spec = 1500`, `tasklist = 1800`, `implement = 1800`, `review = 1800`, and `qa = 1800`.
- `W20-E1-S4-T2` (done) Rerun `AIDD-LIVE-005` on OpenCode after the timeout-profile fix and record run id, verdict, quality gate, first failure boundary, and bundle path.
- `W20-E1-S4-T3` (done; not applicable) Rerun `AIDD-LIVE-005` on canonical Codex only if OpenCode remains provider/runtime timeout blocked without an AIDD-owned defect.

Evidence:

- `2026-05-04` `uv run --extra dev pytest tests/harness/test_live_runtime_config.py -q` passed after adding the OpenCode live timeout profile to generated `aidd.example.toml`.
- `2026-05-04` OpenCode preflight passed with `/opt/homebrew/bin/opencode`, version `1.4.10`, native command `opencode run --format json --dangerously-skip-permissions`.
- `2026-05-04` The generated installed-live `aidd.example.toml` for `eval-live-005-opencode-20260504T143938Z` contains `runtime.opencode.timeout_seconds = 1200` and explicit stage timeouts for `idea`, `research`, `plan`, `review-spec`, `tasklist`, `implement`, `review`, and `qa`.
- `2026-05-04` Post-timeout-profile rerun `eval-live-005-opencode-20260504T143938Z` produced status `fail`, quality gate `fail`, first failure boundary `validation`, first failure note `stage-metadata: stage idea attempt 3 validator failed`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260504T143938Z`.
- `2026-05-04` The rerun proves the timeout-profile change removed the prior provider/runtime timeout symptom: all three `idea` attempts exited `success`/`0` with `Timeout = False`. The remaining blocker is model-output validation after repair exhaustion: `SEM-INCOMPLETE-SECTION` for non-bullet `Open questions` in `idea-brief.md`.
- `2026-05-04` Codex fallback `W20-E1-S4-T3` was not promoted because the decision rule allows fallback only for provider/runtime timeout, and this rerun failed at validation.
- `2026-05-06` Fresh OpenCode preflight for the fallback gate passed: `uv run aidd doctor` reported OpenCode `/opt/homebrew/bin/opencode`, version `1.14.30`, provider available `yes`, execution command available `yes`; `uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode` reported execution readiness `pass`.
- `2026-05-06` Fresh OpenCode gate run `eval-live-005-opencode-20260506T131037Z` completed with status `fail`, quality gate `fail`, first failure boundary `validation`, first failure note `stage qa attempt 3 validator failed`, final failure code `SEM-RISK-UNDERREPORT`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260506T131037Z`.
- `2026-05-06` The fresh gate is not a provider/runtime timeout: every stage attempt recorded runtime exit `success`/`0`, every timeout column was `False`, `log-analysis.md` reported `Timeout Stage/Budget: none`, and the harness run completed under the `14400s` run timeout.
- `2026-05-06` Codex fallback was not run. `W20-E1-S4-T3` is closed as not applicable because the fallback condition was false: OpenCode failed after QA validation repair exhaustion, not before validation at a provider/runtime timeout boundary.
- `2026-05-07` W22 reconciliation closed `W20-E1-S4-T2` as completed by preserved post-timeout-profile and fresh gate evidence. The current OpenCode live-quality caveat is model-output/scenario-quality evidence strength, not an unworked local code task.

Decision outcome:

- `W20-E1-S4-T2` did not prove a provider/runtime timeout after the timeout profile landed, so `W20-E1-S4-T3` stayed not applicable.
- The AIDD-owned validation follow-ups discovered by this lane were handled by later focused hardening slices `W20-E1-S6` and `W20-E1-S8`.
- Release/install evidence was closed separately by `W20-E1-S2-T2` with accepted `v0.1.0a2` publish and install evidence.
- Remaining OpenCode live-quality caveats are recorded as model-output or scenario-quality evidence strength, not as an active local implementation blocker.

Exit evidence:

- maintainers can tell the OpenCode timeout policy was no longer the decisive blocker after `W20-E1-S4`;
- maintainers can tell Codex fallback is reserved for provider/runtime timeout only and was deliberately skipped for validation-boundary failures;
- maintainers can distinguish completed live rerun evidence from the remaining optional desire for cleaner `pass` plus quality-gate evidence in a future manual audit.

#### Slice W20-E1-S5 — comparative live flow diagnosis and Claude control rerun (`done`)
Goal: decide whether the current `AIDD-LIVE-005` flow failure is AIDD-owned, runtime/model-output specific, scenario-quality owned, or environment/provider blocked by comparing preserved bundles with a fresh Claude control run.

Primary outputs:

- forensic matrix across recent OpenCode, Claude, and partial Codex live evidence
- fresh Claude control rerun evidence
- ownership decision for the current live flow blocker

Touched areas:

- `docs/backlog/`
- `.aidd/reports/evals/` local audit bundles, not committed

Dependencies:

- `W20-E1-S4`

Local tasks:

- `W20-E1-S5-T1` (done) Build a forensic matrix for the recent `AIDD-LIVE-005` OpenCode, Claude, and partial Codex bundles, recording first failure boundary, runtime exit, validation result, repair outcome, quality gate, and bundle path.
- `W20-E1-S5-T2` (done) Rerun `AIDD-LIVE-005` on `claude-code` as a control pass/fail lane after `W20-E1-S5-T1` establishes the existing evidence baseline.
- `W20-E1-S5-T3` (done) Compare the fresh Claude bundle with the latest OpenCode bundle and classify the remaining flow blocker as AIDD-owned, prompt/contract-hardening, provider/model-output, scenario-quality, or environment/provider blocked.

Evidence:

- `2026-05-04` Existing bundle `eval-live-005-claude-code-20260504T052321Z` passed execution with verification passed, quality gate `warn`, review `approved`, and QA `ready-with-risks`.
- `2026-05-04` Existing bundle `eval-live-005-opencode-20260504T143938Z` failed at `validation`, not timeout: all three `idea` attempts exited `success`/`0` with timeout `False`; the final validator finding was `SEM-INCOMPLETE-SECTION` for prose `Open questions` instead of bullet items or `- none`.
- `2026-05-04` Current preflight passes for both comparison runtimes: `claude-code` provider version `2.1.85 (Claude Code)` and `opencode` provider version `1.14.30`.
- `2026-05-04` Validator/config sanity checks passed for the relevant local behavior: `uv run --extra dev pytest tests/harness/test_live_runtime_config.py -q` and `uv run --extra dev pytest tests/validators/test_semantic.py -k "list_format or grounded_complete_content" -q`.
- `2026-05-04` Forensic matrix baseline:

| Bundle | Runtime | Verdict | Quality gate | First boundary | Decisive runtime/validation signal |
| --- | --- | --- | --- | --- | --- |
| `eval-live-005-opencode-20260504T121644Z` | `opencode` | `fail` | `fail` | `adapter` | `idea` attempt 1 exited `non_zero_exit`/`1`; OpenCode native command assembly was AIDD-owned and later fixed. |
| `eval-live-005-opencode-20260504T130401Z` | `opencode` | `fail` | `fail` | `validation` | `plan` attempt 3 exited `success`/`0` but failed `INTERVIEW-MALFORMED-DOCUMENT`; interview parsing was AIDD-owned and later fixed. |
| `eval-live-005-opencode-20260504T135544Z` | `opencode` | `fail` | `fail` | `adapter` | `idea` repair attempt hit `timeout`/`-15`; timeout profile was insufficient and later expanded. |
| `eval-live-005-opencode-20260504T143938Z` | `opencode` | `fail` | `fail` | `validation` | `idea` attempt 3 exited `success`/`0`, timeout `False`, but failed `SEM-INCOMPLETE-SECTION` because `Open questions` used prose instead of bullet items or `- none`. |
| `eval-live-005-claude-code-20260504T052321Z` | `claude-code` | `pass` | `warn` | `none` | Installed `idea -> qa` run completed; verification passed; review `approved`; QA `ready-with-risks`. |
| `eval-live-005-claude-code-20260504T152414Z` | `claude-code` | `fail` | `fail` | `adapter` | Control rerun timed out on `idea` attempt 1 with runtime exit `timeout`/`143`, validation `unknown`, and all later stages not reached. |
| `eval-live-005-codex-20260504T120734Z` | `codex` | `partial` | `n/a` | `n/a` | Bundle contains only `issue-selection.json`; no clean Codex audit evidence exists for this run id. |

- `2026-05-04` Claude control preflight passed: `uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime claude-code` reported provider version `2.1.85 (Claude Code)`, native command readiness, and execution readiness `pass`.
- `2026-05-04` Claude control rerun `eval-live-005-claude-code-20260504T152414Z` produced status `fail`, quality gate `fail`, first failure boundary `adapter`, first failure note `runtime.log: Adapter outcome: timeout`, and bundle path `.aidd/reports/evals/eval-live-005-claude-code-20260504T152414Z`.
- `2026-05-04` The fresh Claude run stopped before validation could compare with the OpenCode contract-formatting failure: `idea` attempt 1 exited `timeout`/`143`, validation result was `unknown`, and `research` through `qa` were not reached.
- `2026-05-04` Structured runtime evidence for the fresh Claude run shows the current Claude Code session used model `kimi-for-coding`, emitted an early `429` `rate_limit` retry, continued reading context files, and did not produce validated stage outputs before the stage timeout.
- `2026-05-04` Comparison decision: the fresh Claude control failure does not reproduce the latest OpenCode validation boundary. Current evidence does not prove an AIDD-owned core or validator regression. The latest OpenCode blocker remains model-output Markdown contract compliance or prompt/contract-hardening work; the fresh Claude lane is environment/provider/runtime blocked under the current model and rate-limit conditions.

Decision rules:

- If fresh Claude passes while OpenCode remains blocked only by Markdown contract formatting, record the blocker as runtime/model-output specific or prompt/contract-hardening work; do not add runtime-specific core logic.
- If fresh Claude fails on the same validation boundary, add a focused AIDD-owned regression or prompt/contract fix task before another live rerun.
- If fresh Claude is provider, auth, environment, or timeout blocked, record the blocker and do not infer core flow health from that run.
- If the comparison proves scenario-quality ownership, close the slice with explicit blocker evidence rather than repeating live reruns.

Exit evidence:

- maintainers can explain that the current live flow evidence is blocked by two different runtime-side symptoms rather than one confirmed core break: OpenCode reaches validation and fails strict Markdown list formatting, while the fresh Claude control lane times out before validation;
- no runtime-specific core logic is added from this diagnosis;
- the next action is either prompt/contract hardening for OpenCode-style Markdown compliance, or provider/runtime remediation for the current Claude lane, before another live rerun.

#### Slice W20-E1-S6 — OpenCode contract-compliance hardening (`done`)
Goal: make the current OpenCode live validation blocker actionable before another live rerun, without adding provider-specific core workflow logic.

Primary outputs:

- exact prompt, repair, and contract boundary for the `Open questions` list-format failure
- prompt or repair-guidance hardening for strict Markdown list output
- focused regression proving malformed list output remains blocked with actionable repair guidance
- deferred OpenCode rerun evidence after hardening

Touched areas:

- `docs/backlog/`
- `contracts/stages/`
- `prompt-packs/`
- `tests/validators/`
- `harness/scenarios/live/`

Dependencies:

- `W20-E1-S5`

Local tasks:

- `W20-E1-S6-T1` (done) Inspect `eval-live-005-opencode-20260504T143938Z` and record the exact prompt, repair, and contract boundary for the `Open questions` list-format failure.
- `W20-E1-S6-T2` (done) Harden the `idea` stage prompt and repair guidance so `Open questions` must render as bullet items or `- none`, without adding OpenCode-specific core logic.
- `W20-E1-S6-T3` (done) Add focused regression coverage proving malformed list-format output produces actionable repair guidance and remains blocked if not fixed.
- `W20-E1-S6-T4` (done) Rerun `AIDD-LIVE-005` on OpenCode after hardening and record run id, verdict, quality gate, first failure boundary, and bundle path.

Evidence:

- `2026-05-06` Forensic inspection of `eval-live-005-opencode-20260504T143938Z` found the exact old boundary: `contracts/stages/idea.md` and the semantic validator already required `Open questions` to use bullet items or `- none`, but `prompt-packs/stages/idea/run.md` and `repair.md` did not state strongly enough that prose such as `No open questions.` is invalid.
- `2026-05-06` The `idea` prompt and repair guidance now require `Constraints` and `Open questions` to render as top-level Markdown bullet items, or exactly `- none` when empty. The generated repair brief now adds an actionable generic hint for list-format `SEM-INCOMPLETE-SECTION` findings without adding OpenCode-specific core workflow logic.
- `2026-05-06` Focused local checks passed: `uv run --extra dev pytest tests/validators/test_semantic.py tests/core/test_repair.py tests/test_prompt_quality.py -q` reported `88 passed`.
- `2026-05-06` OpenCode preflight passed for `AIDD-LIVE-005`: provider `/opt/homebrew/bin/opencode`, version `1.14.30`, native execution command `opencode run --format json --dangerously-skip-permissions`.
- `2026-05-06` Post-hardening rerun `eval-live-005-opencode-20260506T054902Z` produced status `fail`, quality gate `fail`, first failure boundary `validation`, first failure note `stage-metadata: stage review attempt 3 validator failed`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260506T054902Z`.
- `2026-05-06` The rerun proves the old `idea` `Open questions` list-format blocker is closed for this live lane: `idea`, `research`, `plan`, `review-spec`, `tasklist`, and `implement` all reached `succeeded` with runtime exits `success`/`0` and no timeout. The new blocker is a later `review` model-output contract failure: final validator code `SEM-UNSUPPORTED-CLAIM` because a review finding lacked evidence reference to implementation output or acceptance criteria.

Exit evidence:

- maintainers can point to the exact contract and prompt boundary behind the current OpenCode blocker;
- OpenCode-specific behavior remains outside core workflow semantics;
- another OpenCode live rerun is attempted only after prompt or repair hardening has local regression evidence.

#### Slice W20-E1-S7 — Claude live timeout/profile diagnosis (`done`)
Goal: make Claude live timeout evidence explicit enough to distinguish provider/runtime blockage from AIDD workflow failure.

Primary outputs:

- explicit Claude `idea` live timeout coverage
- eval/log-analysis evidence for model profile, provider retry/rate-limit signals, timeout stage, and timeout budget
- deferred Claude control rerun after timeout/profile evidence is explicit

Touched areas:

- `src/aidd/harness/`
- `src/aidd/evals/`
- `tests/harness/`
- `tests/evals/`
- `docs/backlog/`

Dependencies:

- `W20-E1-S5`

Local tasks:

- `W20-E1-S7-T1` (done) Update generated Claude live runtime config to include explicit `idea` timeout coverage because the fresh control run timed out on `idea` before validation.
- `W20-E1-S7-T2` (done) Improve eval and log-analysis evidence for Claude runs so model profile, provider retry or rate-limit signals, timeout stage, and timeout budget are visible in the audit summary.
- `W20-E1-S7-T3` (done) Rerun `AIDD-LIVE-005` on Claude only after timeout/profile evidence is explicit; if it still fails before validation, close it as provider/runtime blocked.

Evidence:

- `2026-05-06` Generated Claude live config now includes `[runtime.claude_code.stage_timeouts].idea = 1500` alongside existing `research = 1500`, `tasklist = 1800`, `implement = 1800`, `review = 1800`, and `qa = 1800`.
- `2026-05-06` Eval `log-analysis.md` now includes a `Runtime Diagnostics` section with runtime id, model/profile evidence, retry signals, rate-limit signals, timeout stage/budget, default runtime timeout, stage timeout profile, harness run timeout, and timeout config source. The rate-limit signal extraction was tightened after inspection so long thinking text no longer masks the real `api_retry`/`rate_limit`/`429` event.
- `2026-05-06` Focused local checks passed: `uv run --extra dev pytest tests/harness/test_live_runtime_config.py tests/evals/test_log_analysis_runtime_log.py tests/evals/test_reporting_markdown_summary.py -q` reported `21 passed`.
- `2026-05-06` Claude preflight passed for `AIDD-LIVE-005`: provider `/Users/griogrii_riabov/.local/bin/claude`, version `2.1.85 (Claude Code)`, native execution command `claude -p --output-format stream-json --verbose --dangerously-skip-permissions`.
- `2026-05-06` Post-evidence Claude rerun `eval-live-005-claude-code-20260506T074233Z` produced status `pass`, quality gate `warn`, first failure boundary `none`, and bundle path `.aidd/reports/evals/eval-live-005-claude-code-20260506T074233Z`.
- `2026-05-06` The rerun proves the prior fresh Claude `idea` timeout did not reproduce under the explicit evidence path: every stage from `idea` through `qa` reached `succeeded`, every runtime exit was `success`/`0`, and every stage timeout column was `False`. The quality gate remains `warn` because review/QA artifacts are `ready-with-risks` and evidence references should be strengthened before treating the run as clean release evidence.
- `2026-05-06` Final local gates passed before commit: `uv run --extra dev ruff check .`, `uv run --extra dev python -m mypy src`, and `uv run --extra dev pytest -q` (`738 passed`).

Exit evidence:

- fresh Claude failures can be classified from audit artifacts without guessing whether the model, provider, timeout profile, or AIDD workflow boundary owned the stop;
- the old fresh Claude `idea` timeout blocker is closed by a successful full-flow rerun with explicit timeout/profile diagnostics;
- the remaining Claude lane quality risk is artifact evidence strength, not provider/runtime timeout.

#### Slice W20-E1-S8 — OpenCode review evidence-reference hardening (`done`)
Goal: make the new post-`W20-E1-S6` OpenCode review validation blocker actionable before any further OpenCode live rerun.

Primary outputs:

- exact prompt, repair, and contract boundary for review findings missing evidence references
- review prompt or repair-guidance hardening for evidence-backed findings
- focused regression proving malformed review findings produce actionable repair guidance and remain blocked if not fixed
- deferred OpenCode rerun evidence after review hardening

Touched areas:

- `docs/backlog/`
- `contracts/stages/`
- `prompt-packs/`
- `src/aidd/evals/`
- `tests/validators/`
- `tests/core/`
- `tests/evals/`
- `harness/scenarios/live/`

Dependencies:

- `W20-E1-S6`

Local tasks:

- `W20-E1-S8-T1` (done) Inspect `eval-live-005-opencode-20260506T054902Z` and record the exact prompt, repair, and contract boundary for the review finding evidence-reference failure.
- `W20-E1-S8-T2` (done) Harden the `review` stage prompt and repair guidance so every finding includes stable id, severity, disposition, rationale, and evidence reference to implementation output or acceptance criteria.
- `W20-E1-S8-T3` (done) Add focused regression coverage proving malformed review finding output produces actionable repair guidance and remains blocked if not fixed.
- `W20-E1-S8-T4` (done) Rerun `AIDD-LIVE-005` on OpenCode after review hardening and record run id, verdict, quality gate, first failure boundary, and bundle path.

Evidence:

- `2026-05-06` Forensic inspection of `eval-live-005-opencode-20260506T054902Z` found the exact boundary: the `review` validator already rejected findings without implementation-output or acceptance-criteria evidence, but the final repair brief only repeated the generic stable id/severity/disposition/rationale requirement. The failing `review-report.md` had `REV-*` findings with severity, disposition, and rationale, but no per-finding evidence references.
- `2026-05-06` `contracts/stages/review.md`, `prompt-packs/stages/review/run.md`, and `prompt-packs/stages/review/repair.md` now make `Evidence:` metadata or equivalent inline implementation/`AC-*` evidence explicit for every finding. The generated repair brief now adds an actionable `SEM-UNSUPPORTED-CLAIM` hint that tells the runtime to add `Evidence:` or remove/mark unsupported findings invalid.
- `2026-05-06` Focused local checks passed after hardening and quality-parser follow-up: `uv run --extra dev pytest tests/evals/test_quality.py tests/validators/test_semantic.py tests/core/test_repair.py tests/test_prompt_quality.py -q` reported `100 passed`.
- `2026-05-06` OpenCode preflight passed for `AIDD-LIVE-005`: provider `/opt/homebrew/bin/opencode`, version `1.14.30`, native execution command `opencode run --format json --dangerously-skip-permissions`.
- `2026-05-06` Post-hardening rerun `eval-live-005-opencode-20260506T094747Z` produced status `pass`, first failure boundary `none`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260506T094747Z`. The run reached `idea -> qa`, and `review` succeeded after one repair for a missing `Verdict` section; the previous `SEM-UNSUPPORTED-CLAIM` blocker did not recur.
- `2026-05-06` The generated live `quality-report.md` still recorded quality gate `fail` because the local quality evaluator only recognized backticked `Review status` lines and missed the contract-valid `## Verdict` / `**approved**` output. That AIDD-owned parser mismatch was fixed in `src/aidd/evals/quality.py`; recomputing the assessment against the same bundle now yields gate `warn`, verdict `ready-with-risks`, review status `approved`, QA verdict `ready-with-risks`, no blocking findings, and scores `flow_fidelity=3`, `artifact_quality=2`, `code_quality=1`. Generated `.aidd/` artifacts were not edited.

Exit evidence:

- maintainers can explain why the old idea-stage blocker and the later review evidence-reference blocker are both closed for OpenCode;
- review-stage contract compliance is hardened without provider-specific core logic;
- OpenCode live execution now reaches status `pass`; remaining quality caveat is a bounded `ready-with-risks` artifact/code-quality warning, not a runtime timeout or validation blocker.

### Epic W20-E2 — operator workflow frontend (`done`)
Linked stories: `US-05`, `US-06`, `US-10`, `US-11`

#### Slice W20-E2-S1 — frontend operator flow contract (`done`)
Goal: define the frontend workflow boundary before any UI implementation starts.

Primary outputs:

- frontend operator flow contract
- CLI parity and artifact visibility boundaries

Touched areas:

- `docs/product/`
- `docs/architecture/`

Dependencies:

- `US-11`

Local tasks:

- `W20-E2-S1-T1` (done) Define the frontend operator flow for stage execution, question answering, runner-log viewing, artifact browsing, and CLI parity boundaries.

Evidence:

- `docs/architecture/operator-frontend.md` defines frontend source-of-truth, required operator flows, question answering, runner-log viewing, artifact browsing, write boundaries, runtime/adapter boundaries, and the minimum implementation surface.

Exit evidence:

- frontend scope is documented as an operator surface over existing AIDD semantics;
- question, log, validation, repair, and artifact visibility expectations are reviewable before code starts.

#### Slice W20-E2-S2 — frontend foundation services (`done`)
Goal: expose frontend-ready read and answer-write services before adding a UI shell.

Primary outputs:

- reusable run, stage, log, artifact, and question read models
- standard `answers.md` write service for operator answers

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`

Dependencies:

- `W20-E2-S1`

Local tasks:

- `W20-E2-S2-T1` (done) Extract frontend-ready run, stage, log, artifact, and question read models into reusable core application services.
- `W20-E2-S2-T2` (done) Add an operator answer persistence service that writes resolved, partial, or deferred answers through the standard `answers.md` path.

Evidence:

- `src/aidd/core/run_inspection.py` now owns the run and stage inspection summaries previously used only by the CLI.
- `src/aidd/core/operator_frontend.py` exposes UI-neutral operator read models and answer persistence over existing AIDD artifacts.
- `tests/core/test_operator_frontend.py` covers run metadata, stage status, runtime log lookup, artifact lookup, question status, answer writes, partial-answer semantics, and unknown-question rejection.

Exit evidence:

- frontend code can consume AIDD state without parsing CLI output;
- operator answer writes preserve the existing question/answer document contract.

#### Slice W20-E2-S3 — first frontend implementation surface (`done`)
Goal: add the first frontend surface after the foundation services exist.

Primary outputs:

- reusable workflow orchestration service
- local `aidd ui` command and private JSON endpoints
- first frontend run-control surface
- frontend question, log, and artifact views

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W20-E2-S2`

Local tasks:

- `W20-E2-S3-T1` (done) Extract workflow run/start/resume orchestration from CLI callbacks into a reusable core application service; CLI delegates to it.
- `W20-E2-S3-T2` (done) Add the local-only `aidd ui` server command with private JSON endpoints over operator services.
- `W20-E2-S3-T3` (done) Render the first operator UI for work-item run status, stage status, questions/answers, runtime logs, artifacts, validation, and repair evidence.

Evidence:

- `src/aidd/core/workflow_service.py` owns workflow run orchestration without Typer dependency, while `aidd run` delegates stage selection, stage execution, and completion handling through that service.
- `src/aidd/cli/ui.py` adds `aidd ui --work-item <id> --root <path> --config <path> --host 127.0.0.1 --port 0`, serving a Python-packaged local UI with no Node/Vite dependency.
- Private UI endpoints cover `GET /api/run`, `GET /api/stage`, `GET /api/questions`, `POST /api/answers`, `GET /api/logs`, `GET /api/artifacts`, and `POST /api/workflow/run`.
- `tests/core/test_workflow_service.py` and `tests/cli/test_ui.py` cover workflow orchestration, UI read endpoints, answer POST, and CLI registration.

Exit evidence:

- the frontend can operate the documented minimum flow without bypassing CLI-equivalent provenance.

#### Slice W20-E2-S4 — frontend smoke and browser-safety hardening (`done`)
Goal: make the first local UI smoke-ready without expanding the frontend beyond the private operator surface.

Primary outputs:

- escaped rendering for dynamic UI text
- private workflow-run endpoint coverage through an internal seam
- local UI smoke evidence

Touched areas:

- `src/aidd/cli/`
- `tests/cli/`

Dependencies:

- `W20-E2-S3`

Local tasks:

- `W20-E2-S4-T1` (done) Escape all dynamic UI-rendered text from questions, stage metadata, artifact labels and paths, and runtime-derived values while preserving escaped log rendering.
- `W20-E2-S4-T2` (done) Add private `/api/workflow/run` endpoint coverage through an internal test seam, without invoking real runtimes or changing the public `aidd ui` command.
- `W20-E2-S4-T3` (done) Capture local UI smoke evidence for page load, blocking answer persistence, log and artifact rendering, and workflow-run service reachability.

Evidence:

- `src/aidd/cli/ui.py` now routes question text, stage labels, stage metadata, artifact labels and paths, runtime-derived values, and log text through escaped client-side rendering.
- `tests/cli/test_ui.py` covers the private workflow-run endpoint through an injected workflow service seam and asserts the operator script keeps dynamic markup escaped.
- `2026-05-04` Local UI smoke passed with page load, blocking answer persistence to `answers.md`, log and artifact reads, and workflow-run delegation through the internal service seam. The temporary smoke workspace was `/var/folders/0y/qkpd1n592qjgm3w3rcl_gs6m0000gn/T/aidd-ui-smoke-x5yvauzo/.aidd`; no `.aidd/` evidence was committed.

Exit evidence:

- the first frontend surface is smoke-ready for local operator use without direct artifact mutation or unescaped runtime/UI text.

#### Slice W20-E2-S5 — operator UI E2E evidence lane (`done`)
Goal: define and seed a separate operator-UI evidence lane for installed local-project behavior, without folding UI proof into public-repository live E2E.

Primary outputs:

- operator-UI E2E lane definition for installed local-project usage
- deterministic local-project UI scenario
- deferred manual installed UI smoke evidence
- deferred project-set UI evidence extension

Touched areas:

- `docs/e2e/`
- `harness/scenarios/`
- `tests/cli/`
- `tests/core/`
- `docs/backlog/`

Dependencies:

- `W20-E2-S4`
- `W20-E3-S4`

Local tasks:

- `W20-E2-S5-T1` (done) Define a separate operator-UI E2E lane in `docs/e2e/` that proves installed local-project UI behavior and stays separate from the public-repository live E2E lane.
- `W20-E2-S5-T2` (done) Add a deterministic local-project UI scenario covering page load, workflow-run request, blocking answer persistence, logs, artifacts, validation, and repair-history visibility.
- `W20-E2-S5-T3` (done) Add manual installed UI smoke evidence using local AIDD install against a local fixture project; record the summary in roadmap and do not commit `.aidd/`.
- `W20-E2-S5-T4` (done) Extend the UI scenario to include declared project-set roots so frontend evidence proves local monorepo and project-set visibility end to end.

Evidence:

- `docs/e2e/operator-ui-local-project.md` now defines the local-project operator UI E2E lane separately from the public-repository live E2E catalog. `docs/e2e/scenario-matrix.md` links the lane as service-level UI evidence rather than a new harness scenario class, and `docs/e2e/live-e2e-catalog.md` keeps public repositories scoped to live eval manifests.
- `tests/cli/test_ui.py` now includes a deterministic local-project UI lane over `OperatorUiService`: page load, workflow-run request delegation through the core service seam, blocking answer persistence, runtime logs, artifact paths, validator report visibility, validator pass/fail counts, and repair-brief path visibility.
- `tests/cli/test_ui.py` also proves declared project-set root visibility by exposing `workitems/WI-UI/context/project-set.md` through `/api/artifacts` and checking the local `api` / `web` roots in the context document.
- `2026-05-06` Focused local checks passed: `uv run --extra dev pytest tests/cli/test_ui.py tests/core/test_operator_frontend.py -q` reported `13 passed`.
- `2026-05-06` Manual installed UI smoke passed in disposable local fixture project `/tmp/aidd-ui-smoke-0hxJYa`: `uv tool run --from <repo> aidd init` created `.aidd/` inside the fixture project, `uv tool run --from <repo> aidd run --runtime generic-cli --from-stage idea --to-stage plan` completed three fixture-backed stages, `aidd ui` served `http://127.0.0.1:8765/`, and HTTP checks confirmed page load plus `/api/run`, `/api/stage?stage=plan`, `/api/artifacts?stage=plan`, and `/api/logs?stage=plan`. The fixture project declared `api` and `web` roots; `.aidd/workitems/WI-UI-SMOKE/context/project-set.md` preserved both. The temp project was removed and no `.aidd/` artifacts were committed.

Exit evidence:

- UI proof is based on the product's local-project operator path, not on GitHub issue intake;
- UI evidence stays separate from manual public-repository live E2E and can be reviewed without real runtime execution;
- installed local-project UI smoke evidence now covers page/API access against a disposable fixture project.

#### Slice W20-E2-S6 — frontend provider readiness visibility (`done`)
Goal: expose provider readiness to the frontend so operators can distinguish unavailable providers, ready providers, timeout/profile risk, and latest-run failure.

Primary outputs:

- frontend-ready runtime readiness read model
- private UI endpoint and panel for runtime readiness
- UI escaping and source-of-truth tests for readiness data

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`
- `tests/cli/`
- `docs/backlog/`

Dependencies:

- `W20-E2-S4`

Local tasks:

- `W20-E2-S6-T1` (done) Add a frontend-ready runtime readiness read model that exposes registered runtimes, command source, execution mode, provider availability, provider version, execution command availability, and configured timeout budgets.
- `W20-E2-S6-T2` (done) Add a private UI endpoint and UI panel for runtime readiness so operators can distinguish provider unavailable, provider ready, timeout/profile risk, and latest run failed.
- `W20-E2-S6-T3` (done) Add UI tests proving readiness data renders escaped and does not become workflow source of truth.

Evidence:

- `src/aidd/core/runtime_readiness.py` adds a UI-neutral runtime readiness read model built only from `AiddConfig`, runtime definitions, command-source metadata, and probe reports supplied by the caller. Core does not invoke adapter probes or execution-command discovery.
- `src/aidd/cli/ui.py` adds `GET /api/runtime-readiness` and a Readiness tab. The CLI/UI layer collects adapter provider probes and execution command availability, then passes those reports into the core read model.
- The readiness panel shows runtime id, support tier, command source (`default` or `config`), command, execution mode, provider availability, provider version, provider probe command, execution command availability, default timeout, and stage timeout profile. Latest-run failure remains visible through the existing run/stage read models, keeping readiness observational rather than workflow state.
- `tests/core/test_operator_frontend.py` covers read-model assembly from supplied probe reports and config timeouts. `tests/cli/test_ui.py` covers the private readiness endpoint, escaped rendering for readiness fields, and proves workflow runs continue to use the config snapshot rather than readiness probe output.
- `2026-05-06` Focused local checks passed: `uv run --extra dev pytest tests/core/test_operator_frontend.py tests/cli/test_ui.py -q` reported `16 passed`.

Exit evidence:

- the frontend can show runtime readiness without encoding provider-specific workflow semantics;
- readiness display remains observational and does not change canonical workflow state.

### Epic W20-E3 — project-set workflow scope (`done`)
Linked stories: `US-01`, `US-02`, `US-03`, `US-07`, `US-10`, `US-12`

#### Slice W20-E3-S1 — project-set workspace contract (`done`)
Goal: define how monorepo package roots and related local project roots are declared, bounded, and represented in AIDD artifacts.

Primary outputs:

- project-set workspace contract
- artifact ownership and cross-project link rules

Touched areas:

- `docs/product/`
- `docs/architecture/`

Dependencies:

- `US-12`

Local tasks:

- `W20-E3-S1-T1` (done) Define the project-set and monorepo workspace contract, including declared roots, artifact ownership, validation evidence, and execution bounds.

Evidence:

- `docs/architecture/project-set-workspace.md` defines the local-only project-set model, supported `[[project_set.projects]]` declaration shape, root bounds, artifact ownership, execution limits, and harness/eval expectations.

Exit evidence:

- maintainers can distinguish supported monorepo/project-set behavior from unsupported implicit multi-repository orchestration;
- downstream implementation can preserve document-first artifacts and validation evidence per declared project root.

#### Slice W20-E3-S2 — project-set config and resolver (`done`)
Goal: make declared local project roots parseable and resolvable before stage or harness integration.

Primary outputs:

- optional project-set config model
- bounded project-root resolver and preflight checks

Touched areas:

- `src/aidd/config.py`
- `src/aidd/core/`
- `tests/`

Dependencies:

- `W20-E3-S1`

Local tasks:

- `W20-E3-S2-T1` (done) Add optional `[[project_set.projects]]` config parsing with stable ids, repo-relative roots, and descriptive roles.
- `W20-E3-S2-T2` (done) Add project-set workspace resolution that rejects missing roots, absolute roots, parent escapes, symlink escapes, and duplicate resolved roots.

Evidence:

- `src/aidd/config.py` now parses optional project-set declarations while preserving empty project-set defaults.
- `src/aidd/core/project_set.py` resolves declared local roots and enforces repository-bound ownership.
- `tests/test_config.py` and `tests/core/test_project_set.py` cover valid declarations plus duplicate id/root, missing root, absolute root, `..` escape, and symlink escape cases.

Exit evidence:

- declared project roots are resolved deterministically;
- absent project-set config preserves the existing single-workspace behavior.

#### Slice W20-E3-S3 — project-set stage and harness integration (`done`)
Goal: propagate resolved project-set context into stage evidence and deterministic harness coverage.

Primary outputs:

- project-set context in work-item context, stage briefs, and attempt input bundles
- artifact summary visibility for project-set context
- deterministic monorepo/project-set harness coverage

Touched areas:

- `src/aidd/core/`
- `src/aidd/harness/`
- `harness/scenarios/`
- `docs/e2e/`
- `tests/`

Dependencies:

- `W20-E3-S2`

Local tasks:

- `W20-E3-S3-T1` (done) Persist resolved project-set context as `workitems/<id>/context/project-set.md` and include it in generated stage briefs when config declares projects.
- `W20-E3-S3-T2` (done) Ensure stage outputs and artifact summaries can cite project ids without changing adapter semantics.
- `W20-E3-S3-T3` (done) Add deterministic monorepo/project-set harness coverage with at least two declared roots.

Evidence:

- `src/aidd/core/project_set.py` renders and persists Markdown project-set context with stable project ids, repo-relative roots, roles, and explicit local-only rules.
- `src/aidd/core/stage_preparation.py` appends declared project-set context to stage briefs and attempt input bundles when config declares projects.
- `src/aidd/core/run_store.py` includes `project_set_context` in attempt artifact indexes when the work item has project-set context.
- `harness/scenarios/deterministic/project-set-plan-context.yaml` declares two local roots, `api` and `web`, and verifies that both ids remain visible in project-set context and stage-brief evidence.
- `tests/core/test_project_set.py`, `tests/core/test_stage_runner.py`, `tests/core/test_run_store_layout.py`, and `tests/harness/test_scenario_loader_model.py` cover context rendering, stage preparation, artifact summary visibility, and scenario coverage.

Exit evidence:

- harness coverage proves project ownership is preserved in artifacts and validation evidence.

#### Slice W20-E3-S4 — project-set artifact evidence tightening (`done`)
Goal: tighten deterministic and frontend-facing evidence so project-set context is visible beyond the generated Markdown document alone.

Primary outputs:

- deterministic scenario verification for artifact-index and input-bundle evidence
- operator artifact-view coverage for project-set context

Touched areas:

- `src/aidd/harness/`
- `harness/scenarios/`
- `docs/e2e/`
- `tests/`

Dependencies:

- `W20-E3-S3`

Local tasks:

- `W20-E3-S4-T1` (done) Extend the deterministic project-set scenario so verification checks artifact-index and input-bundle evidence for `project_set_context` and both project ids, not only `project-set.md` and `stage-brief.md`.
- `W20-E3-S4-T2` (done) Add operator artifact-view coverage proving frontend consumers can see `project_set_context` when a work item has declared project roots.

Evidence:

- `harness/scenarios/deterministic/project-set-plan-context.yaml` now runs as a deterministic workflow from `idea` through `plan`, declares `api` and `web` roots, and verifies `artifact-index.json` plus `input-bundle.md` preserve `project_set_context` and both project ids.
- `src/aidd/harness/repo_prep.py` can materialize local non-git fixture directories into temporary git repositories, which keeps deterministic fixture scenarios self-contained without committing nested fixture repositories.
- `harness/fixtures/minimal-python/aidd_fixture_runtime.py` provides the deterministic `generic-cli` fixture runtime used by the project-set scenario.
- `tests/harness/test_repo_prep.py` and `tests/harness/test_scenario_loader_model.py` cover local fixture materialization and the widened deterministic workflow scenario contract.
- `tests/core/test_operator_frontend.py` covers artifact view visibility for `project_set_context`.
- `2026-05-04` Deterministic project-set eval `eval-deterministic-003-generic-cli-20260504T141138Z` passed with quality gate `none`; bundle path `.aidd/reports/evals/eval-deterministic-003-generic-cli-20260504T141138Z`.

Exit evidence:

- deterministic and operator-facing evidence both expose project-set context for declared local project roots.

### Epic W20-E4 — local project operator adoption (`done`)
Linked stories: `US-09`, `US-11`, `US-12`

#### Slice W20-E4-S1 — local operator path documentation (`done`)
Goal: document the supported product path as local installation plus local project execution, while keeping public GitHub repositories limited to live E2E eval and support/reporting contexts.

Primary outputs:

- supported local operator path documentation
- explicit product-scope boundary excluding GitHub issue intake commands

Touched areas:

- `README.md`
- `docs/operator-handbook.md`
- `docs/e2e/`
- `docs/backlog/`

Dependencies:

- `US-09`
- `US-11`
- `US-12`

Local tasks:

- `W20-E4-S1-T1` (done) Document the supported local operator path: install AIDD locally, enter a local project root, run `aidd doctor`, initialize a work item, run CLI or `aidd ui`, inspect logs and artifacts, and keep `.aidd/` local to that project.
- `W20-E4-S1-T2` (done) Explicitly document that `aidd init --github-issue <url>` is out of product scope and public GitHub repositories are only live E2E eval targets.

Evidence:

- `README.md` now has a Supported Local Operator Path section showing installed and source-checkout command forms, `aidd doctor`, `aidd init --work-item ... --root .aidd`, `aidd run`, `aidd ui`, and CLI log/artifact inspection from a target local project root.
- `docs/operator-handbook.md` now makes local-project operation the product path, including local install/run, project-root entry, `doctor`, workspace initialization, CLI/UI execution, log/artifact inspection, and `.aidd/` ownership inside the local project.
- `docs/e2e/operator-ui-local-project.md` and `docs/e2e/live-e2e-catalog.md` now separate the local-project operator lane from public-repository live E2E. Public GitHub repositories are live E2E targets and support/reporting evidence sources only.
- `tests/test_docs_consistency.py` now asserts the local operator docs describe the local project path and explicitly mark `aidd init --github-issue <url>` as out of product scope.

Exit evidence:

- operators can identify the intended local-project adoption path without reading the roadmap;
- maintainers have an explicit scope guard against adding GitHub issue intake as a product feature.

#### Slice W20-E4-S2 — installed local-project smoke evidence (`done`)
Goal: add installed local-project smoke evidence that uses fixture projects rather than public GitHub issues.

Primary outputs:

- installed local-project smoke scenario using a fixture project
- source or GitHub-install smoke note that keeps the target project local

Touched areas:

- `harness/scenarios/`
- `harness/fixtures/`
- `docs/e2e/`
- `tests/harness/`
- `docs/backlog/`

Dependencies:

- `W20-E4-S1`
- `W20-E2-S5`

Local tasks:

- `W20-E4-S2-T1` (done) Add an installed local-project smoke scenario that uses a fixture project, not a public GitHub issue, and proves `aidd init`, `aidd run` or `aidd ui`, logs, artifacts, and answers work from a local project root.
- `W20-E4-S2-T2` (done) Add a source or GitHub-install smoke note or harness path for installing AIDD itself from repository source while keeping the target project local.

Evidence:

- `harness/scenarios/smoke/installed-local-project-fixture.yaml` adds `AIDD-INSTALLED-LOCAL-001`, a manual deterministic fixture smoke that uses `harness/fixtures/minimal-python` as the target local project and `uv tool run --from /path/to/ai_driven_dev_v2 aidd` as the source-install AIDD command form.
- The smoke path covers `aidd doctor`, `aidd init --work-item ... --root .aidd`, a bounded `generic-cli` workflow run from `idea` to `plan`, `aidd run show`, `aidd run logs`, `aidd run artifacts`, and standard `questions.md` / `answers.md` inspection through `aidd stage questions`.
- `docs/e2e/operator-ui-local-project.md` documents the source-install fixture smoke path and keeps the target project local. `docs/e2e/scenario-matrix.md` lists `AIDD-INSTALLED-LOCAL-001` as a manual fixture smoke, not a live public-repository manifest.
- `tests/harness/test_scenario_loader_model.py` covers the manifest source-install metadata, local fixture target, expected setup commands, evidence commands, and answer-inspection command. `tests/test_scenario_taxonomy.py` keeps the scenario matrix documentation synchronized.
- `2026-05-06` Manual source-installed local fixture smoke passed in disposable project `/tmp/aidd-source-local-smoke-V7bHSd`: `uv tool run --from <repo> aidd doctor`, `aidd init`, bounded `aidd run --from-stage idea --to-stage plan`, `aidd run show`, `aidd run logs`, `aidd run artifacts`, and `aidd stage questions` all succeeded; the temp project was removed and no `.aidd/` artifacts were committed.

Exit evidence:

- install-source evidence does not imply GitHub issue intake as a product path;
- local fixture smoke proves `.aidd/` remains rooted in the local target project.

Sync notes:

- `2026-05-04` Wave 20 opened via `W8-E3-S1` queue-restoration policy after the gap analysis found missing frontend and project-set product stories plus fresh live E2E and release/install evidence gaps. Initial queue restoration promotes `W20-E1-S1-T1` to `Next`; `W20-E1-S1-T2`, `W20-E1-S2-T1`, `W20-E2-S1-T1`, and `W20-E3-S1-T1` to `Soon`; and `W20-E1-S2-T2`, `W20-E2-S2-T1`, `W20-E2-S2-T2`, `W20-E3-S2-T1`, and `W20-E3-S2-T2` to `Parking lot`.
- `2026-05-04` W20 evidence-and-contract pass completed: live preflight is current, fallback live eval bundle `eval-live-005-opencode-20260504T121644Z` is preserved with failing adapter-boundary evidence, release-channel evidence capture is blocked by missing candidate tag and credentials, operator frontend and project-set contracts are documented, and implementation tasks remain parked until explicitly promoted.
- `2026-05-04` W20 foundation pass triaged the OpenCode live failure to an AIDD-owned native command assembly defect, added an OpenCode command regression, moved run inspection into reusable core services, added frontend-ready operator read/write services, and added optional project-set config plus bounded project-root resolution. Fresh clean live evidence and UI/project-set harness integration remain follow-up tasks.
- `2026-05-04` W20 implementation pass added project-set stage context and deterministic scenario coverage, extracted workflow orchestration into core, and added the first local `aidd ui` surface over reusable operator services. Release/install evidence remains blocked by missing release candidate tag and registry credentials.
- `2026-05-04` W20 closure-and-hardening pass completed frontend escaping, workflow-run endpoint seam coverage, local UI smoke evidence, project-set artifact-index/input-bundle verification, and operator project-set artifact visibility. Post-parser-fix OpenCode live rerun `eval-live-005-opencode-20260504T135544Z` remains blocked by runtime/provider timeout evidence, and release/install evidence remains blocked by missing release candidate tag and registry credentials.
- `2026-05-04` W20 timeout-profile pass added explicit OpenCode live stage timeouts and reran `AIDD-LIVE-005` as `eval-live-005-opencode-20260504T143938Z`. The timeout blocker moved to a validation/model-output blocker after repair budget exhaustion, so Codex fallback remains parked and unpromoted under the provider-timeout-only fallback rule.
- `2026-05-04` W20 comparative live-flow diagnosis completed: the fresh Claude control rerun `eval-live-005-claude-code-20260504T152414Z` failed at an `adapter` timeout on `idea` attempt 1, not at the OpenCode `SEM-INCOMPLETE-SECTION` validation boundary. The diagnosis does not prove an AIDD-owned core regression; clean live evidence remains blocked by runtime/model-output behavior.
- `2026-05-04` Remaining W20 gap intake added OpenCode contract-compliance hardening, Claude timeout/profile diagnosis, separate local-project operator UI evidence, frontend provider-readiness visibility, and local operator adoption documentation tasks. Public GitHub repositories remain live E2E eval targets only, while the product adoption path stays local installation plus local project execution.
- `2026-05-06` `W20-E4-S1` completed the local operator path documentation and GitHub issue-intake scope guard. The next actionable evidence task is `W20-E4-S2-T1`.
- `2026-05-06` `W20-E4-S2` completed the source-installed local fixture smoke path. The remaining Wave 20 queue contains only conditional parked items: release/install evidence (`W20-E1-S2-T2`) waiting on a release candidate tag and publishing credentials, and Codex fallback (`W20-E1-S4-T3`) reserved for a provider/runtime timeout blocker.
- `2026-05-06` Release candidate tag `v0.1.0a0` was pushed to merged `main` commit `aa3655998227e6da2a979b06d2c87543adbf4734`; release run `25437182363` built successfully and published the container, but PyPI Trusted Publishing failed with `invalid-publisher`, so `W20-E1-S2-T2` remains blocked. Discovered prerelease `latest` image tagging was fixed as `W20-E1-S2-T3`.
- `2026-05-06` Fresh OpenCode fallback gate `eval-live-005-opencode-20260506T131037Z` failed at validation (`qa` attempt 3 `SEM-RISK-UNDERREPORT`) with no timeout signals. Codex fallback was not run; `W20-E1-S4-T3` is closed as not applicable and removed from the backlog parking lot.

---

## Wave 21 — audit closure and production hardening (`done`)

Goal: close the full-audit findings by removing hidden operator runtime defaults, tightening project-set evidence, completing adapter/provenance/log ownership, and reducing the highest-risk module complexity without changing the public stage chain or `.aidd/` artifact layout.

### Epic W21-E1 — operator UI runtime and safety closure (`done`)
Linked stories: `US-01`, `US-06`, `US-09`, `US-11`

#### Slice W21-E1-S1 — explicit UI runtime launch contract (`done`)
Goal: make `aidd ui` workflow launches require an explicit operator-selected runtime while keeping readiness observational.

Primary outputs:

- UI runtime selector backed by `/api/runtime-readiness`
- `/api/workflow/run` required-runtime validation
- UI/API regression coverage for non-generic runtime payloads

Touched areas:

- `src/aidd/cli/`
- `tests/cli/`
- `docs/backlog/`

Dependencies:

- `W20-E2-S6`

Local tasks:

- `W21-E1-S1-T1` (done) Require explicit runtime selection for UI workflow launches and prove a non-generic runtime reaches `WorkflowRunRequest`.

Evidence:

- `src/aidd/cli/ui.py` requires `runtime` in `/api/workflow/run`; missing or empty runtime now returns `400` instead of defaulting to `generic-cli`.
- `src/aidd/cli/ui_assets.py` renders a runtime selector from `/api/runtime-readiness`, keeps `Run` disabled until selection, and posts the selected runtime.
- `tests/cli/test_ui.py` proves non-generic runtime propagation, missing-runtime rejection, disabled initial run state, and no hardcoded `generic-cli` workflow launch payload.

Exit evidence:

- UI launches no longer fall back to `generic-cli`;
- readiness display remains read-only and does not change workflow source of truth.

#### Slice W21-E1-S2 — warn-only UI request safety (`done`)
Goal: harden the private local UI request boundary without adding authentication in this wave.

Primary outputs:

- bounded JSON request body handling
- non-loopback local-only warning
- operator documentation for no-auth local UI behavior

Touched areas:

- `src/aidd/cli/`
- `docs/operator-handbook.md`
- `tests/cli/`

Dependencies:

- `W21-E1-S1`

Local tasks:

- `W21-E1-S2-T1` (done) Limit UI JSON request bodies and map invalid body shapes to deterministic HTTP errors.
- `W21-E1-S2-T2` (done) Warn when `aidd ui` binds outside loopback and document the no-auth local UI model.

Evidence:

- `src/aidd/cli/ui_http.py` owns UI JSON response/body helpers and caps request bodies at 64 KiB.
- `src/aidd/cli/ui.py` warns on non-loopback bind while preserving the existing public `aidd ui` options.
- `README.md`, `docs/operator-handbook.md`, and `docs/architecture/operator-frontend.md` document explicit runtime selection and warn-only no-auth local UI behavior.

Exit evidence:

- oversized UI POST bodies return `413`;
- malformed or non-object JSON returns `400`;
- non-loopback bind remains allowed but visibly warned as local-only/no-auth.

### Epic W21-E2 — project-set evidence closure (`done`)
Linked stories: `US-02`, `US-03`, `US-07`, `US-10`, `US-12`

#### Slice W21-E2-S1 — conditional project-set stage-result evidence (`done`)
Goal: make declared project ids and roots validator-visible in `stage-result.md` whenever a work item has project-set context.

Primary outputs:

- `stage-result.md` contract wording for conditional project-set evidence
- project-set-aware cross-document validator
- deterministic scenario evidence for project ids and roots in validated stage results

Touched areas:

- `contracts/documents/`
- `src/aidd/core/`
- `src/aidd/validators/`
- `harness/scenarios/deterministic/`
- `harness/fixtures/`
- `tests/validators/`

Dependencies:

- `W20-E3-S4`

Local tasks:

- `W21-E2-S1-T1` (done) Define conditional `Project-set evidence` rules in `stage-result.md` and stage brief guidance.
- `W21-E2-S1-T2` (done) Validate that project-set stage results cite every declared project id and root.
- `W21-E2-S1-T3` (done) Extend the deterministic project-set scenario and fixture runtime to prove validated per-project evidence.

Evidence:

- `contracts/documents/stage-result.md` now defines conditional `Project-set evidence` requirements when `workitems/<id>/context/project-set.md` exists.
- `src/aidd/core/stage_preparation.py` instructs runtime attempts to cite the project context path plus all declared project ids and roots in `stage-result.md`.
- `src/aidd/validators/cross_document.py` reports `CROSS-PROJECT-SET-EVIDENCE-MISSING` when project-set context exists but final stage evidence omits the section, context path, ids, or roots.
- `harness/fixtures/minimal-python/aidd_fixture_runtime.py` and `harness/scenarios/deterministic/project-set-plan-context.yaml` now prove validated per-project evidence in `stage-result.md`.
- `tests/validators/test_cross_document.py` covers passing and failing project-set evidence bundles.

Exit evidence:

- project-set context cannot be present while final stage evidence omits declared project ownership.

### Epic W21-E3 — adapter, provenance, and runtime-log ownership (`done`)
Linked stories: `US-01`, `US-06`, `US-08`, `US-10`

#### Slice W21-E3-S1 — registry-owned adapter dispatch (`done`)
Goal: move runtime execution dispatch from runtime-id branching to registered adapter surface callables.

Local tasks:

- `W21-E3-S1-T1` (done) Register per-runtime execution and conformance builders on `RuntimeAdapterSurface` without changing runtime ids or CLI behavior.

Evidence:

- `src/aidd/adapters/surface.py` now stores registered execution and conformance builder callables on `RuntimeAdapterSurface`; method bodies delegate to those callables instead of branching on runtime id.
- `tests/adapters/test_surface.py` proves maintained runtimes register execution and conformance callables and retain the same default execution modes.

#### Slice W21-E3-S2 — manifest provenance completion (`done`)
Goal: record explicit adapter id and resource revision in run manifests while preserving legacy manifest loading.

Local tasks:

- `W21-E3-S2-T1` (done) Add `adapter_id` and `resource_revision` to new run manifests and run-show summaries with backward-compatible defaults.

Evidence:

- `src/aidd/core/run_store.py` writes `adapter_id` and `resource_revision` for new run manifests while preserving existing manifest layout and legacy load behavior.
- `src/aidd/core/run_provenance.py` owns resource-source, Git SHA, packaged revision, and prompt-pack hash collection helpers.
- `src/aidd/core/run_inspection.py` and `src/aidd/cli/run.py` expose adapter and resource revision in run summaries.
- `tests/core/test_run_store_layout.py` covers repository and packaged-resource provenance.

#### Slice W21-E3-S3 — runtime-log schema ownership (`done`)
Goal: make `src/aidd/runtime_logs/` own normalized runtime event data structures and JSONL parsing helpers.

Local tasks:

- `W21-E3-S3-T1` (done) Move structured/normalized runtime event helpers into `runtime_logs` and keep adapters/evals as consumers.

Evidence:

- `src/aidd/runtime_logs/events.py` owns structured JSONL extraction, normalized event shaping, and runtime event artifact persistence.
- `src/aidd/adapters/runtime_events.py` re-exports the runtime-log helpers for adapter compatibility and keeps adapter question persistence local.
- `src/aidd/adapters/claude_code/runner.py` delegates normalized event parsing to `runtime_logs`.
- `tests/adapters/test_runtime_events.py` proves runtime-log-owned parsing semantics.

### Epic W21-E4 — maintainability closure (`done`)
Linked stories: `US-07`, `US-08`, `US-10`, `US-11`

#### Slice W21-E4-S1 — highest-risk module decomposition (`done`)
Goal: reduce module complexity in UI, run-store, eval reporting, and legacy eval runner seams without changing behavior or artifact filenames.

Local tasks:

- `W21-E4-S1-T1` (done) Split UI assets and HTTP helpers out of `src/aidd/cli/ui.py` while preserving the public `aidd ui` command.
- `W21-E4-S1-T2` (done) Extract run manifest/provenance/stage-status helpers from `run_store` while preserving `.aidd` layout.
- `W21-E4-S1-T3` (done) Extract eval report writer helpers while preserving result bundle filenames.
- `W21-E4-S1-T4` (done) Isolate legacy eval runner patch points behind an explicit compatibility module.

Evidence:

- `src/aidd/cli/ui_assets.py` and `src/aidd/cli/ui_http.py` split UI assets and HTTP helpers away from `OperatorUiService`.
- `src/aidd/core/run_provenance.py` removes provenance collection from `run_store` while preserving run manifest and artifact paths.
- `src/aidd/harness/eval_report_writers.py` owns eval source artifact writes behind the existing `write_source_artifacts` compatibility function.
- The legacy evaluator compatibility module owned module patch helpers before the black-box live E2E replacement.
- Focused checks passed: `uv run --extra dev pytest -q tests/cli/test_ui.py tests/core/test_operator_frontend.py tests/core/test_run_store_layout.py tests/adapters/test_surface.py tests/adapters/test_runtime_events.py tests/adapters/test_claude_code_runner.py tests/harness/test_result_bundle_persistence.py tests/validators/test_cross_document.py`.

## Wave 22 — backlog blocker reconciliation and delivery loop (`done`)

Goal: reconcile the empty active backlog with historical blocked local tasks, close stale blockers using accepted later evidence, and leave a repeatable slice-by-slice delivery loop for future backlog restoration.

### Epic W22-E0 — blocked-task reconciliation (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W22-E0-S1 — authoritative closure decision (`done`)
Goal: make the roadmap and short backlog agree about whether any open local task still requires implementation.

Primary outputs:

- authoritative closure decisions for the four historical blocked local tasks
- critical analytical note for the reconciliation slice
- empty synchronized active backlog after the slice closes

Touched areas:

- `docs/backlog/`
- `docs/analysis/`

Dependencies:

- `W8-E3-S1`
- `W21-E4-S1`

Per-slice work plan:

- Output: close or explicitly preserve each stale blocker with evidence-backed reasoning.
- Dominant touched area: planning and analysis documents only.
- Verification: `rg` checks prove no roadmap local task remains `blocked`, `active`, `planned`, `next`, or `later`; local gates remain green.
- Compatibility: no runtime ids, `.aidd` artifact layout, stage contracts, prompt packs, adapters, or public CLI behavior change.

Local tasks:

- `W22-E0-S1-T1` (done) Reconcile the empty active backlog with historical blocked local tasks and record authoritative closure decisions.

Evidence:

- `2026-05-07` Active `docs/backlog/backlog.md` had no task ids in `Next`, `Soon`, or `Parking lot`; roadmap search found exactly four stale blocked local tasks: `W15-E3-S1-T1`, `W15-E3-S2-T1`, `W20-E1-S3-T5`, and `W20-E1-S4-T2`.
- `2026-05-07` `W15-E3-S1-T1` is closed by later maintained-runtime live evidence: `eval-live-005-claude-code-20260506T074233Z` passed `AIDD-LIVE-005` with quality gate `warn`, first failure boundary `none`, and no stage timeouts.
- `2026-05-07` `W15-E3-S2-T1` is closed by accepted `v0.1.0a2` release/install evidence: release run `25448551936` passed PyPI publish, `pipx`, and `uv tool` verification; container/GHCR evidence from that run is historical only after the later alpha no-container policy.
- `2026-05-07` `W20-E1-S3-T5` is closed because its required rerun occurred as `eval-live-005-opencode-20260504T135544Z` and preserved an updated timeout blocker later addressed by `W20-E1-S4`.
- `2026-05-07` `W20-E1-S4-T2` is closed because post-timeout-profile rerun evidence was preserved, later hardening slices closed the AIDD-owned list-format and review-evidence blockers, and the remaining OpenCode caveat is live model-output/scenario-quality evidence strength rather than an unworked local implementation task.
- `2026-05-07` Preflight evidence was refreshed without running a manual live audit: `uv run aidd doctor`, `uv run aidd eval doctor harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime opencode`, and the same eval doctor command for `claude-code` all reported execution readiness `pass`.
- `docs/analysis/w22-e0-s1-critical-analysis.md` records the critical analytical review for this reconciliation slice and found no unresolved Critical or High defects.
- `2026-05-07` Final local gates passed: roadmap open-task searches returned no stale non-done local tasks or active/blocked headings; `uv run --extra dev ruff check .`, `uv run --extra dev python -m mypy src`, `uv run --extra dev pytest -q` (`781 passed`), and `uv run aidd doctor` all passed.

Exit evidence:

- no active backlog queue entries remain;
- no roadmap local task remains in a non-done status;
- external live/release evidence remains conditional for future audits, not a hidden code defect.

## Wave 23 — black-box live E2E evaluator (`done`)

Goal: replace report-first live E2E execution with a stepwise black-box evaluator
that drives installed AIDD through public operator surfaces and removes the legacy
product `eval run` command without backward compatibility.

### Epic W23-E1 — live E2E black-box execution (`done`)
Linked stories: `US-07`, `US-10`, `US-11`

#### Slice W23-E1-S1 — evaluator replacement and legacy removal (`done`)
Goal: make manual live E2E plan, execute, inspect, classify, and decide after each
flow step while deleting the legacy monolithic eval-run path.

Primary outputs:

- black-box live E2E evaluator module
- persisted `flow-state.json`, `flow-steps.json`, `flow-report.md`, and
  `operator-actions.jsonl`
- operator action request artifacts for blocking questions
- live manifest `live_flow` contract
- local skill entrypoint using the evaluator module
- removed product eval-run command and legacy runner compatibility path

Touched areas:

- `src/aidd/cli/`
- `src/aidd/harness/`
- `harness/scenarios/live/`
- `.github/workflows/`
- `.agents/skills/`
- `docs/`
- `tests/`

Local tasks:

- `W23-E1-S1-T1` (done) Replace legacy live eval-run execution with the black-box
  live E2E evaluator and remove backward-compatible eval-run surfaces.

Evidence:

- `src/aidd/harness/live_e2e_black_box.py` drives installed AIDD through
  `aidd stage run`, `aidd stage summary`, `aidd stage questions`, `aidd run show`,
  `aidd run logs`, and `aidd run artifacts`.
- `src/aidd/cli/main.py` no longer registers the legacy eval-run command; `aidd eval doctor`
  and `aidd eval summary` remain read-only support surfaces.
- Legacy eval runner, execution, classification, and compatibility
  patch modules were removed.
- Live manifests now declare `live_flow.driver: stepwise-black-box`,
  `checkpoint_policy: after-each-step`, and explicit answer policy.
- Local live documentation and skills invoke
  `uv run python -m aidd.harness.live_e2e_black_box`; GitHub Actions workflows no
  longer expose a live E2E entrypoint.
- Focused and full local gates passed on 2026-05-18:
  `uv run --extra dev ruff check .`,
  `uv run --extra dev python -m mypy src`,
  and `uv run --extra dev pytest -q` (`782 passed`).

Exit evidence:

- no live docs, skills, or manual workflow instruct operators to run the legacy eval-run command;
- live E2E remains manual-only and outside CI/release gates;
- final audit artifacts are derived from per-step black-box evidence.

## Wave 24 — beta readiness release preparation (`done`)

Goal: prepare AIDD for controlled operator-trial beta readiness without claiming unattended
production automation and without wiring live E2E into CI/CD or release workflows.

### Epic W24-E1 — source-of-truth and release guardrail closure (`done`)
Linked stories: `US-01`, `US-07`, `US-09`, `US-10`, `US-11`, `US-12`

#### Slice W24-E1-S1 — beta release-prep source audit (`done`)
Goal: prove README, user stories, target architecture, release process, and local smoke
evidence agree with the current code before release materials are prepared.

Primary outputs:

- beta-readiness source audit
- deterministic release workflow quality gate
- CI/CD guardrails that exclude live E2E
- source-installed local-project smoke verification
- release-readiness notes for latest accepted `0.1.0a6` evidence and source
  `0.1.0a7.dev0` state

Touched areas:

- `README.md`
- `docs/analysis/`
- `docs/architecture/`
- `docs/release-checklist.md`
- `.github/workflows/`
- `harness/scenarios/`
- `tests/`

Dependencies:

- `W23-E1-S1`

Local tasks:

- `W24-E1-S1-T1` (done) Audit README, user stories, and target architecture against the
  current CLI, package, workflow, runtime, and artifact behavior.
- `W24-E1-S1-T2` (done) Add deterministic release quality checks and locked local install
  commands while preserving the manual-only live E2E boundary.
- `W24-E1-S1-T3` (done) Verify the source-installed local-project smoke fixture runtime
  path and cover the workspace-relative command with scenario-loader regression checks.
- `W24-E1-S1-T4` (done) Prepare release-readiness notes for the accepted `0.1.0a6`
  evidence and post-release `0.1.0a7.dev0` source state without creating a tag or
  publishing artifacts.

Evidence:

- `docs/analysis/beta-readiness-source-audit.md` records the README, user-story, target
  architecture, workflow, runtime, and live-boundary audit.
- `.github/workflows/release.yml` now runs deterministic lint, typecheck, and tests on
  Python 3.12, 3.13, and 3.14 before package build and publish jobs.
- `Makefile install` now uses `uv sync --locked --extra dev`.
- `tests/test_release_workflow.py` and `tests/test_security_configuration.py` prevent live
  E2E commands, provider secrets, live manifests, and live evaluator invocation from
  entering CI/CD or release workflows.
- `harness/scenarios/smoke/installed-local-project-fixture.yaml` and the project-set
  deterministic scenario keep the `generic-cli` runtime command workspace-relative from
  `.aidd/` to the fixture root, and tests now lock that behavior.
- A source-installed local-project smoke passed on 2026-05-21 against a disposable
  `harness/fixtures/minimal-python` copy, covering `doctor`, `init`, bounded
  `run idea->plan`, `run show`, `run logs`, `run artifacts`, and `stage questions`.
- `docs/release-notes-v0.1.0a6-draft.md` and `docs/analysis/beta-readiness-source-audit.md`
  record the latest accepted `0.1.0a6` package-channel evidence and current
  `0.1.0a7.dev0` source development state; accepted package-channel evidence is recorded
  in `docs/release-checklist.md`.

Exit evidence:

- deterministic local gates pass;
- package build succeeds into a temp directory;
- live E2E remains manual-only and outside CI/CD/release workflows;
- release materials are prepared without changing the public alpha safety claim.

#### Slice W24-E1-S2 — manual live beta evidence refresh (`done`)
Goal: refresh maintained manual live E2E evidence for the beta-readiness provider matrix
outside CI/CD and release automation.

Primary outputs:

- uncommitted live stabilization ledger updates under `.aidd/reports/evals/`
- operator-authored overlays for terminal live runs
- explicit external blockers for provider/auth/network/setup failures

Touched areas:

- `.aidd/reports/evals/` local evidence only
- `src/`, `tests/`, `docs/`, `contracts/`, `prompt-packs/`, or `harness/scenarios/` only
  if a live run proves an AIDD-owned defect

Dependencies:

- `W24-E1-S1`

Local tasks:

- `W24-E1-S2-T1` (done) Refresh medium-plus manual live evidence for `codex`,
  `claude-code`, and `opencode` using maintained live manifests outside CI/CD.
- `W24-E1-S2-T2` (done) Classify structured `opencode` provider error payloads as
  runtime failures when the native CLI exits `0`, so orchestration stops explicitly
  instead of spending repair budget on missing documents.
- `W24-E1-S2-T3` (done) Make black-box live stage command timeouts terminal and visible
  in evidence without leaving inspected AIDD stage metadata in `executing`.

Evidence:

- `2026-05-26` refreshed manual live evidence from source revision
  `99864851129baaaf11bdc0fa883b35dff3966c57` using maintained live manifests.
- `eval-live-005-codex-20260526T160204Z` (`AIDD-LIVE-005`, `codex`) passed as a
  supplementary small smoke control: execution `pass`, quality gate `pass`, quality
  verdict `ready`, review `approved`, and QA `ready`.
- `eval-live-007-codex-20260526T163850Z` (`AIDD-LIVE-007`, `codex`) produced negative
  medium-plus evidence: stages reached `implement`, `plan` repaired successfully once,
  but the harness command timeout killed `aidd stage run implement` after `1200.000s`,
  leaving the stage metadata in `executing` and no runtime log visible through
  `aidd run logs`.
- `eval-live-007-claude-code-20260526T172838Z` (`AIDD-LIVE-007`, `claude-code`) is an
  explicit external provider blocker: the runtime log exposed through public CLI shows
  API 403 provider usage-limit/quota text before `idea` could produce stage documents.
- `eval-live-006-opencode-20260526T173043Z` (`AIDD-LIVE-006`, `opencode`) is negative
  large-scenario evidence: provider quota returned a structured API error payload with
  process exit `0`, so AIDD treated the runtime exit as success, spent repair budget on
  missing `idea-brief.md`, and stopped after validation failed three times.
- Operator-authored `operator-quality-analysis.md` overlays were written in each
  terminal bundle; `.aidd/reports/evals/` remains local evidence and is not committed.
- `2026-05-26` split the broad evidence-backed fix pass into two reviewable tasks:
  `W24-E1-S2-T2` owns the adapter/runtime error-payload classification issue proven by
  `eval-live-006-opencode-20260526T173043Z`, while `W24-E1-S2-T3` owns the live harness
  timeout lifecycle/evidence issue proven by `eval-live-007-codex-20260526T163850Z`.
- `2026-05-26` completed `W24-E1-S2-T2`: native OpenCode zero-exit structured
  provider API errors are classified as `provider_error`; raw logs and runtime exit
  metadata are preserved; CLI coverage proves the stage stops after one attempt instead
  of scheduling repair retries.
- `2026-05-26` completed `W24-E1-S2-T3`: black-box live stage command timeouts now
  write `stage-audits/<stage>-timeout-reconciliation.json`, reconcile non-terminal
  inspected stage metadata to `failed`, include the reconciliation payload in
  `flow-steps.json` and `flow-state.json`, skip the frontend checkpoint after a timed-out
  stage command, and derive stage audit state from reconciled metadata when the public
  stage-result document is missing. `tests/harness/test_live_e2e_black_box.py` covers the
  timeout lifecycle and evidence shape.

Exit evidence:

- counted clean manual live runs or explicit external blockers are recorded in the local
  operator ledger;
- evidence-backed AIDD-owned live harness defects discovered during the refresh were
  split, fixed, and covered by deterministic regressions;
- no live evidence artifact, target repository diff, provider log, or temp work root is
  committed.

## Wave 25 — local operator workflow hardening (`done`)

Goal: close non-security audit findings for the local alpha operator workflow: runtime
control, bounded log and artifact inspection, accessibility, mobile usability, UI
regression coverage, architecture boundaries, and maintainability. Authentication,
session tokens, Origin/CSRF guards, secret redaction, trusted harness sandboxing, and
dangerous provider default changes are explicitly out of scope for this wave.

### Epic W25-E1 — runtime control and observability (`done`)
Linked stories: `US-01`, `US-06`, `US-11`

#### Slice W25-E1-S1 — cancellable UI runtime jobs (`done`)
Goal: let operators cancel active local UI runtime jobs without stopping only the HTTP
server or losing runtime evidence.

Primary outputs:

- cancellable UI job registry
- `POST /api/jobs/<job_id>/cancel`
- cancelled job and runtime evidence states
- operator console cancel control

Touched areas:

- `src/aidd/cli/ui.py`
- `src/aidd/cli/ui_assets.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W21-E1-S1`
- `W21-E1-S2`

Local tasks:

- `W25-E1-S1-T1` (done) Add a cancellable UI job registry and
  `POST /api/jobs/<job_id>/cancel` endpoint for active stage, workflow, and intervention
  jobs.
  - Scope: `src/aidd/cli/ui.py` job lifecycle only.
  - Verification: `tests/cli/test_ui.py` proves active, cancelling, cancelled,
    completed, and already-finished job states.
- `W25-E1-S1-T2` (done) Propagate UI cancellation to the running stage execution so
  subprocess-backed runtimes terminate and persist a cancelled outcome.
  - Scope: UI-to-stage execution path using existing adapter and process cancellation
    behavior.
  - Verification: a fixture long-running `generic-cli` job cancels from the UI API and
    records cancelled runtime and stage evidence.
- `W25-E1-S1-T3` (done) Render a Cancel action and cancelled or terminating states in
  the operator console live job panel.
  - Scope: packaged UI assets only.
  - Verification: UI service or static tests prove button visibility, disabled terminal
    states, and live log preservation.

Evidence:

- `src/aidd/cli/ui.py` now exposes `POST /api/jobs/<job_id>/cancel`, records cancel
  request metadata in job views, returns deterministic already-finished payloads for
  completed jobs, and preserves live job logs.
- `tests/cli/test_ui.py` covers a running stage job moving through `running`,
  `cancelling`, and `cancelled`, plus completed jobs returning an already-finished
  cancel response.
- `src/aidd/cli/stage_run.py` and `src/aidd/adapters/runtime_execution.py` now carry
  a `cancel_requested` callback from UI job state into stage runtime requests, and
  `src/aidd/adapters/surface.py` passes it to the subprocess-backed `generic-cli`,
  Claude Code, Codex, OpenCode, and Qwen runners.
- `tests/cli/test_ui.py` covers cancel callback propagation for UI stage, workflow,
  and intervention jobs, plus a long-running `generic-cli` fixture cancelled via
  `POST /api/jobs/<job_id>/cancel` with `runtime-exit.json` recording
  `exit_classification: cancelled` and stage metadata recording a stopped stage.
- `2026-05-26` Focused checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.
- `2026-05-26` Focused W25-E1-S1-T2 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui.py src/aidd/cli/stage_run.py src/aidd/adapters/runtime_execution.py src/aidd/adapters/surface.py tests/cli/test_ui.py`,
  and `uv run --extra dev python -m mypy src`.
- `src/aidd/cli/ui_assets.py` now renders a live-job Cancel action in the log panel,
  shows `cancelling` and terminal `cancelled`/`completed`/`failed` disabled states,
  keeps `cancelling` in the active polling set, and preserves live log chunks after
  cancellation.
- `tests/cli/test_ui.py` statically covers the packaged Cancel action, `/api/jobs/.../cancel`
  call, `cancelling` polling state, terminal labels, and CSS status classes.
- `2026-05-26` Focused W25-E1-S1-T3 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  browser smoke of `uv run aidd ui --work-item WI-UI --root /tmp/.../.aidd --host 127.0.0.1 --port 8787`
  loaded the operator shell at `http://127.0.0.1:8787/`.

Exit evidence:

- active UI runtime jobs can be cancelled from API and UI;
- cancelled jobs persist a deterministic terminal state and do not keep a runtime
  subprocess alive;
- completed jobs cannot be cancelled retroactively.

#### Slice W25-E1-S2 — bounded logs and artifact previews (`done`)
Goal: keep local UI log and artifact inspection responsive on large runs while preserving
raw evidence availability through explicit bounded reads.

Primary outputs:

- tail/limit parameters for UI log reads
- capped default `/api/logs` responses
- capped artifact document previews
- visible truncation states in the operator console

Touched areas:

- `src/aidd/cli/ui.py`
- `src/aidd/cli/ui_assets.py`
- `src/aidd/core/operator_frontend.py`
- `tests/cli/test_ui.py`
- `tests/core/test_operator_frontend.py`

Dependencies:

- `W25-E1-S1`

Local tasks:

- `W25-E1-S2-T1` (done) Add tail or limit parameters to UI log reads and cap the
  default `/api/logs` response size.
  - Scope: UI API and operator frontend log view.
  - Verification: a high-volume runtime log test proves truncation metadata and no
    whole-file default response.
- `W25-E1-S2-T2` (done) Cap artifact document preview payloads while preserving
  explicit source inspection through bounded reads.
  - Scope: `/api/artifacts/document` and the UI artifact viewer.
  - Verification: a large Markdown artifact test proves preview truncation, byte counts,
    and source-mode bounds.
- `W25-E1-S2-T3` (done) Add operator console copy and states for truncated logs and
  artifacts.
  - Scope: packaged UI assets.
  - Verification: `tests/cli/test_ui.py` covers visible truncation indicators.

Exit evidence:

- `src/aidd/core/operator_frontend.py` now returns bounded operator log text with
  byte-size, byte-range, requested-size, max-size, and truncation metadata.
- `src/aidd/cli/ui.py` accepts `tail` or `limit` query parameters on `/api/logs`
  and no longer reads the whole runtime log by default.
- `tests/cli/test_ui.py` covers a high-volume runtime log where the default response
  is truncated to a tail window, and explicit `tail`/`limit` reads expose the expected
  byte ranges.
- `tests/core/test_operator_frontend.py` covers bounded head and tail read-model
  metadata.
- `2026-05-26` Focused W25-E1-S2-T1 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py tests/core/test_operator_frontend.py -q`,
  `uv run --extra dev ruff check src/aidd/core/operator_frontend.py src/aidd/cli/ui.py tests/cli/test_ui.py tests/core/test_operator_frontend.py`,
  and `uv run --extra dev python -m mypy src`.
- `src/aidd/core/operator_frontend.py` now returns bounded artifact document text with
  mode, byte-size, byte-range, requested-size, max-size, and truncation metadata; default
  preview reads are capped and source reads are explicitly bounded.
- `src/aidd/cli/ui.py` accepts `mode` and `limit` on `/api/artifacts/document`, and
  `src/aidd/cli/ui_assets.py` sends source-mode reads with the maximum bounded artifact
  limit instead of requesting an unbounded document.
- `tests/cli/test_ui.py` covers a large Markdown artifact where default preview and source
  reads are truncated with byte counts, and `tests/core/test_operator_frontend.py` covers
  the bounded artifact read model.
- `2026-05-26` Focused W25-E1-S2-T2 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py tests/core/test_operator_frontend.py -q`,
  `uv run --extra dev ruff check src/aidd/core/operator_frontend.py src/aidd/cli/ui.py src/aidd/cli/ui_assets.py tests/cli/test_ui.py tests/core/test_operator_frontend.py`,
  and `uv run --extra dev python -m mypy src`.
- `src/aidd/cli/ui_assets.py` now renders visible truncation notices for saved runtime
  logs and artifact document previews/source views, including byte range and full-file
  inspection guidance.
- `tests/cli/test_ui.py` statically covers the truncation notice copy, artifact/source
  state wiring, and packaged `.truncation-notice` style.
- `2026-05-26` Focused W25-E1-S2-T3 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.
- large logs and artifacts no longer require full-file UI responses by default;
- operators can see when a displayed log or artifact preview is truncated;
- raw evidence paths remain inspectable through existing artifact surfaces.

### Epic W25-E2 — operator UI usability and accessibility (`done`)
Linked stories: `US-05`, `US-06`, `US-11`

#### Slice W25-E2-S1 — accessibility baseline (`done`)
Goal: make the local operator console usable with keyboard and assistive technologies
without changing the visual information architecture.

Primary outputs:

- accessible question answer controls
- cockpit tab semantics
- active stage semantics
- named landmarks and visible focus styles

Touched areas:

- `src/aidd/cli/ui_assets.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W20-E2-S5`
- `W21-E1-S1`

Local tasks:

- `W25-E2-S1-T1` (done) Add accessible labels and relationships for dynamic question
  answer controls.
  - Scope: question card rendering.
  - Verification: DOM or static tests prove every generated textarea and select has a
    label or ARIA name.
- `W25-E2-S1-T2` (done) Add tablist, tab, and panel semantics to cockpit tabs and
  `aria-current` to the active stage.
  - Scope: UI HTML and JavaScript rendering only.
  - Verification: static UI tests prove roles, selected state, and active stage
    semantics.
- `W25-E2-S1-T3` (done) Add named landmarks and explicit focus-visible styling for
  keyboard users.
  - Scope: packaged HTML and CSS.
  - Verification: UI asset tests assert landmark labels, and a screenshot or manual
    checklist confirms visible focus.

Evidence:

- `src/aidd/cli/ui_assets.py` now gives each generated question textarea and resolution
  select a stable `id`, a screen-reader label, and an `aria-describedby` relationship to
  the rendered question text.
- `tests/cli/test_ui.py` statically covers the question control labels, described-by
  relationships, and packaged `.sr-only` helper style.
- `2026-05-26` Focused W25-E2-S1-T1 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.
- `src/aidd/cli/ui_assets.py` now exposes cockpit tabs as a `tablist` with `tab`
  buttons, updates `aria-selected` and the dynamic `tabpanel` label on activation, and
  marks the active stage rail item with `aria-current="step"`.
- `tests/cli/test_ui.py` statically covers the tablist, tab, panel, selected-state, and
  active-stage semantics.
- `2026-05-26` Focused W25-E2-S1-T2 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.
- `src/aidd/cli/ui_assets.py` now names the main operator landmarks and defines an
  explicit `:focus-visible` ring for buttons, selects, textareas, and focusable panels.
- `tests/cli/test_ui.py` statically covers the landmark labels and focus-visible CSS
  contract.
- `2026-05-26` Browser smoke loaded `http://127.0.0.1:8791/` and confirmed the rendered
  landmark labels: Operator controls, Operator workspace, Workflow navigation, Workflow
  stages, Stage cockpit, Run details, and Activity and recent artifacts.
- `2026-05-26` Focused W25-E2-S1-T3 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.

Exit evidence:

- question answer inputs are accessible by label;
- cockpit tabs and the active stage expose semantic state;
- keyboard focus is visible on critical operator controls.

#### Slice W25-E2-S2 — mobile and workflow clarity (`done`)
Goal: reduce local operator confusion during first launch, mobile inspection, and
question resolution flows.

Primary outputs:

- mobile active-stage rail visibility
- saved answer rendering in resolved question cards
- explicit loading and empty-run UI states

Touched areas:

- `src/aidd/cli/ui_assets.py`
- `src/aidd/core/operator_frontend.py`
- `tests/cli/test_ui.py`
- `tests/core/test_operator_frontend.py`

Dependencies:

- `W25-E2-S1`

Local tasks:

- `W25-E2-S2-T1` (done) Auto-scroll the active stage into view in the mobile
  horizontal stage rail.
  - Scope: UI JavaScript and CSS.
  - Verification: a mobile viewport browser or manual smoke confirms the selected stage
    is visible after load and stage switch.
- `W25-E2-S2-T2` (done) Render saved answer text for resolved questions.
  - Scope: operator frontend question read model and question card UI.
  - Verification: API and UI tests prove `answers.md` content appears in resolved
    question cards.
- `W25-E2-S2-T3` (done) Add explicit initial loading and empty-run states for first
  launch.
  - Scope: UI assets.
  - Verification: UI tests cover pre-fetch loading state and no-run state copy and
    actions.

Evidence:

- `src/aidd/cli/ui_assets.py` now gives the mobile stage rail scroll padding and calls
  `scrollIntoView({block: "nearest", inline: "center"})` for the active stage after each
  rail render, gated to the `max-width: 760px` mobile breakpoint.
- `tests/cli/test_ui.py` statically covers the mobile breakpoint gate, active-stage
  selector, `scrollIntoView` options, render hook, and CSS scroll padding.
- `2026-05-26` Manual implementation checklist confirmed the selected-stage scroll path
  runs after load and stage switch because both paths call `renderStageRail()`;
  in-app browser smoke loaded the operator console, but viewport control was unavailable.
- `2026-05-26` Focused W25-E2-S2-T1 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.
- `src/aidd/core/operator_frontend.py` now includes resolved answer text and answer
  resolution metadata in each operator question view.
- `src/aidd/cli/ui_assets.py` renders a read-only saved-answer block for resolved
  question cards without treating partial or deferred answers as resolved.
- `tests/core/test_operator_frontend.py` covers resolved and partial answer read-model
  behavior, and `tests/cli/test_ui.py` covers API payload fields plus saved-answer card
  markup.
- `2026-05-26` Focused W25-E2-S2-T2 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py tests/core/test_operator_frontend.py -q`,
  `uv run --extra dev ruff check src/aidd/core/operator_frontend.py src/aidd/cli/ui_assets.py tests/cli/test_ui.py tests/core/test_operator_frontend.py`,
  and `uv run --extra dev python -m mypy src`.
- `src/aidd/cli/ui_assets.py` now renders a pre-fetch loading state in the cockpit and a
  first-launch/no-run overview state with runtime readiness copy plus a runtime-gated Run
  workflow action.
- `tests/cli/test_ui.py` statically covers the loading markup, no-run copy, first-launch
  action wiring, and runtime-select re-render hook.
- `2026-05-26` Focused W25-E2-S2-T3 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py -q`,
  `uv run --extra dev ruff check src/aidd/cli/ui_assets.py tests/cli/test_ui.py`, and
  `uv run --extra dev python -m mypy src`.

Exit evidence:

- selected stage remains visible on mobile viewport checks;
- resolved question cards show the saved operator answer;
- first launch and no-run states present clear operator next actions.

### Epic W25-E3 — UI regression coverage (`done`)
Linked stories: `US-07`, `US-11`

#### Slice W25-E3-S1 — deterministic UI coverage without Node/Vite (`done`)
Goal: lock the operator console's critical DOM and service contracts with pytest-only
coverage that preserves the packaged static UI model.

Primary outputs:

- static DOM contract tests for packaged UI assets
- extended local-project UI E2E documentation
- service-level regressions for new UI hardening behavior

Touched areas:

- `src/aidd/cli/ui_assets.py`
- `docs/e2e/operator-ui-local-project.md`
- `tests/cli/test_ui.py`
- `tests/core/test_operator_frontend.py`

Dependencies:

- `W25-E1-S1`
- `W25-E1-S2`
- `W25-E2-S1`
- `W25-E2-S2`

Local tasks:

- `W25-E3-S1-T1` (done) Add static DOM contract tests for packaged UI
  accessibility-critical markup.
  - Scope: tests around `ui_assets.py`.
  - Verification: pytest-only checks pass with no Node or browser dependency.
- `W25-E3-S1-T2` (done) Extend operator UI local-project E2E documentation with
  manual browser checks for dashboard, tabs, logs, artifacts, questions, intervention,
  desktop, tablet, and mobile.
  - Scope: `docs/e2e/operator-ui-local-project.md`.
  - Verification: docs consistency or targeted Markdown assertions cover the checklist.
- `W25-E3-S1-T3` (done) Add service-level regressions for cancellation, bounded logs,
  saved-answer display, and truncation metadata.
  - Scope: `tests/cli/test_ui.py` and `tests/core/test_operator_frontend.py`.
  - Verification: the focused pytest suite passes.

Evidence:

- `tests/cli/test_ui_assets_contracts.py` now parses packaged `_INDEX_HTML` with the
  standard-library HTML parser and asserts named landmarks, runtime labeling, tab/panel
  semantics, and loading-state markup.
- The same pytest-only contract file statically covers dynamic UI accessibility contracts
  in `_OPERATOR_JS` and focus/screen-reader/truncation/saved-answer CSS hooks in
  `_OPERATOR_CSS`.
- `2026-05-26` Focused W25-E3-S1-T1 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py -q` and
  `uv run --extra dev ruff check tests/cli/test_ui_assets_contracts.py`.
- `docs/e2e/operator-ui-local-project.md` now includes a Manual Browser Checklist
  covering dashboard shell, cockpit tabs, live and saved logs, artifacts, questions,
  request-change/intervention flow, and desktop/tablet/mobile viewports.
- `tests/test_docs_consistency.py` asserts the checklist sections and viewport/focus
  coverage stay present.
- `2026-05-26` Focused W25-E3-S1-T2 checks passed:
  `uv run --extra dev pytest tests/test_docs_consistency.py -q` and
  `uv run --extra dev ruff check tests/test_docs_consistency.py`.
- `tests/cli/test_ui.py` now includes a service-level hardening regression that exercises
  already-finished cancellation, bounded log metadata, artifact truncation metadata, and
  saved-answer payload fields together.
- `2026-05-26` Focused W25-E3-S1-T3 checks passed:
  `uv run --extra dev pytest tests/cli/test_ui.py tests/core/test_operator_frontend.py -q`
  and `uv run --extra dev ruff check tests/cli/test_ui.py tests/core/test_operator_frontend.py`.

Exit evidence:

- critical UI semantics and new hardening states are covered without introducing a Node
  build pipeline;
- manual browser coverage remains documented for the local-project operator lane.

### Epic W25-E4 — non-security architecture and maintainability cleanup (`done`)
Linked stories: `US-01`, `US-07`, `US-08`, `US-11`

#### Slice W25-E4-S1 — runtime boundary cleanup (`done`)
Goal: remove non-security architecture boundary smells found during the audit without
changing public runtime behavior.

Primary outputs:

- neutral runtime catalog ownership
- protocol-owned Claude question metadata update path
- visible validator evidence for misplaced output promotion

Touched areas:

- `src/aidd/config.py`
- `src/aidd/core/`
- `src/aidd/adapters/`
- `src/aidd/validators/`
- `tests/`

Dependencies:

- `W21-E3-S3`

Local tasks:

- `W25-E4-S1-T1` (done) Move runtime readiness catalog data out of
  `aidd.adapters.runtime_registry` into a neutral runtime catalog module.
  - Scope: runtime metadata imports only; no behavior change.
  - Verification: an import-boundary grep plus existing doctor and readiness tests.
  - Evidence (`2026-05-26`): runtime catalog ownership moved to
    `src/aidd/runtime_catalog.py`; `src/aidd/adapters/runtime_registry.py` is now a
    compatibility re-export shim; core, CLI, harness, config, adapter, and test imports
    use the neutral catalog module.
  - Checks (`2026-05-26`): `rg -n "aidd\\.adapters\\.runtime_registry|runtime_registry import" src/aidd/core src/aidd/cli src/aidd/harness src/aidd/config.py`
    returned no matches; `uv run --extra dev pytest tests/adapters/test_runtime_registry.py tests/test_config.py tests/test_docs_consistency.py tests/cli/test_doctor.py tests/harness/test_live_runtime_config.py tests/harness/test_conformance_matrix.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`.
- `W25-E4-S1-T2` (done) Remove the Claude adapter's direct run-store metadata write by
  exposing a protocol-owned metadata hook or event.
  - Scope: Claude adapter boundary and core run metadata update path.
  - Verification: Claude question artifact tests still pass without importing
    `aidd.core.run_store` from adapters.
  - Evidence (`2026-05-26`): `src/aidd/core/adapter_interview.py` now exposes
    `persist_adapter_question_metadata`; Claude question persistence calls that hook
    instead of importing `aidd.core.run_store` or writing stage metadata directly.
  - Checks (`2026-05-26`): `rg -n "from aidd\\.core\\.run_store|import aidd\\.core\\.run_store" src/aidd/adapters -g '*.py'`
    returned no matches; `uv run --extra dev pytest tests/core/test_adapter_interview.py tests/adapters/test_claude_code_runner.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`.
- `W25-E4-S1-T3` (done) Record a validator or report warning when misplaced stage
  outputs are auto-promoted from `output/`.
  - Scope: stage output discovery and validation evidence.
  - Verification: a regression test proves promotion still works and warning evidence is
    visible.
  - Evidence (`2026-05-26`): stage output discovery now records promoted
    source/destination pairs and `validator-report.md` appends a non-blocking
    `STRUCT-OUTPUT-PROMOTED` warning section when misplaced `output/` documents are
    copied into canonical stage document locations.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/core/test_stage_runner.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`.

Exit evidence:

- core readiness models no longer import adapter-owned runtime registry data;
- Claude adapter no longer mutates run-store metadata through a core layout helper;
- output promotion remains compatible but becomes visible in validation evidence.

#### Slice W25-E4-S2 — module size reduction (`done`)
Goal: reduce the largest remaining UI, operator frontend, and live evaluator modules
without changing behavior, public CLI commands, or artifact filenames.

Primary outputs:

- static UI resource loader
- smaller operator frontend read-model modules
- split live E2E black-box evaluator modules

Touched areas:

- `src/aidd/cli/`
- `src/aidd/core/operator_frontend.py`
- `src/aidd/harness/live_e2e_black_box.py`
- `tests/`

Dependencies:

- `W25-E3-S1`

Local tasks:

- `W25-E4-S2-T1` (done) Split packaged UI assets into static resource files while
  preserving the no-Node and no-Vite packaging model.
  - Scope: `src/aidd/cli/static/` resources plus loader.
  - Verification: package resource tests and UI endpoint tests pass from source and built
    wheel.
  - Evidence (`2026-05-26`): HTML, CSS, and JS moved to
    `src/aidd/cli/static/`; `src/aidd/cli/ui_assets.py` now loads those package resources
    while preserving `_INDEX_HTML`, `_OPERATOR_CSS`, and `_OPERATOR_JS` imports.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/cli/test_ui_assets_contracts.py tests/cli/test_ui.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`;
    `uv build`; built wheel inspection confirmed `aidd/cli/static/{index.html,operator.css,operator.js}`;
    a wheel-import smoke verified `/`, `/operator.css`, and `/operator.js` responses.
- `W25-E4-S2-T2` (done) Split operator frontend read-model assembly into smaller
  modules for dashboard, artifacts, logs, and questions.
  - Scope: `src/aidd/core/operator_frontend.py` decomposition only.
  - Verification: existing operator frontend tests pass with no API shape change.
  - Evidence (`2026-05-26`): `src/aidd/core/operator_frontend.py` is now a
    compatibility facade; read-model implementation lives in
    `operator_frontend_models.py`, `operator_frontend_logs.py`,
    `operator_frontend_artifacts.py`, `operator_frontend_questions.py`, and
    `operator_frontend_dashboard.py`.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/core/test_operator_frontend.py tests/cli/test_ui.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`;
    facade import smoke confirmed the existing public functions remain exported.
- `W25-E4-S2-T3` (done) Split the live E2E black-box evaluator into orchestration,
  step execution, and report writing modules.
  - Scope: harness maintainability only.
  - Verification: live evaluator unit tests and result bundle tests pass.
  - Evidence (`2026-05-26`): `src/aidd/harness/live_e2e_black_box.py` is now a
    compatibility facade; orchestration moved to
    `src/aidd/harness/live_e2e_black_box_orchestration.py`, subprocess/command primitives
    moved to `src/aidd/harness/live_e2e_black_box_steps.py`, and JSON/report transcript
    helpers moved to `src/aidd/harness/live_e2e_black_box_reports.py`.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/harness/test_live_e2e_black_box.py tests/harness/test_result_bundle_layout.py tests/harness/test_result_bundle_persistence.py tests/harness/test_result_bundle_completeness.py tests/harness/test_result_bundle_artifacts.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`;
    `uv run --extra dev pytest tests/test_docs_consistency.py -q`; backlog sync check.

Exit evidence:

- large module responsibilities are split behind compatibility-preserving imports or
  public functions;
- existing UI, operator frontend, and live evaluator behavior remains unchanged.

#### Slice W25-E4-S3 — config and validation polish (`done`)
Goal: improve operator-facing diagnostics for config and repair loops without changing
stage contracts.

Primary outputs:

- friendly scalar config validation
- richer safe semantic finding collection during validation

Touched areas:

- `src/aidd/config.py`
- `src/aidd/core/stage_outputs.py`
- `src/aidd/validators/`
- `tests/`

Dependencies:

- `W25-E4-S1`

Local tasks:

- `W25-E4-S3-T1` (done) Add friendly validation for `repair.max_attempts` and invalid
  scalar config values.
  - Scope: `src/aidd/config.py`.
  - Verification: config tests cover non-integer, negative, and valid values.
  - Evidence (`2026-05-26`): `src/aidd/config.py` now validates config tables,
    string scalar fields, and non-negative integer `repair.max_attempts` with field-scoped
    `ValueError` messages instead of implicit coercion or attribute errors.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/test_config.py tests/test_docs_consistency.py -q`;
    `uv run --extra dev ruff check .`; `uv run --extra dev python -m mypy src`;
    backlog sync check.
- `W25-E4-S3-T2` (done) Collect independent semantic findings when structural
  validation is sufficient to continue checking.
  - Scope: validation flow only.
  - Verification: a validator regression proves mixed structural and semantic defects can
    surface together where safe.
  - Evidence (`2026-05-26`): `run_structural_validation_after_output_discovery` now
    preserves structural findings while also running semantic and cross-document checks
    when at least one output document is available for safe follow-on validation.
  - Checks (`2026-05-26`): `uv run --extra dev pytest tests/core/test_stage_runner.py tests/validators/test_structural.py tests/validators/test_semantic.py tests/validators/test_cross_document.py -q`.
    Final Wave 25 checks: `uv run --extra dev pytest -q` (`999 passed`, 2 existing
    tar extraction deprecation warnings); `uv run --extra dev ruff check .`;
    `uv run --extra dev python -m mypy src`; `uv run --extra dev pytest tests/test_docs_consistency.py -q`;
    backlog sync check.

Exit evidence:

- invalid scalar config values produce actionable errors;
- validation can surface independent semantic defects earlier without silently continuing
  past blocking structural failures.

## Wave 26 — completed-flow lineage operator experience (`done`)

Goal: implement the accepted Mission Control operator UI direction, including the
completed-run handoff that can launch a new work item, follow-up flow, cloned flow,
eval batch, or archive decision without mutating the completed source run.

Opening note:

- `2026-05-27` Wave 26 opened after the operator frontend design freeze. The accepted
  direction is documented in `docs/architecture/operator-frontend.md`; this wave turns
  that direction into reviewable core, UI, regression, and live E2E work.

### Epic W26-E0 — design freeze and planning handoff (`done`)
Linked stories: `US-07`, `US-10`, `US-11`

#### Slice W26-E0-S1 — accepted Mission Control UX contract (`done`)
Goal: freeze the chosen operator UI direction and reopen the backlog with reviewable
implementation tasks.

Primary outputs:

- accepted screen inventory
- completed-flow handoff contract
- reopened Wave 26 backlog queue

Touched areas:

- `docs/product/`
- `docs/architecture/`
- `docs/backlog/`
- `tests/`

Dependencies:

- `W25-E4-S3`

Local tasks:

- `W26-E0-S1-T1` (done) Document the accepted Mission Control UI direction, completed-run
  next-flow semantics, and implementation backlog.
  - Scope: product, architecture, and planning docs only.
  - Verification: docs consistency checks and backlog sync checks pass.

Exit evidence:

- `US-11` includes terminal-run next-flow handoff as a frontend success signal;
- `operator-frontend.md` records the 12 accepted screens and completed-run actions;
- `docs/architecture/assets/operator-ui-mission-control/` stores the accepted visual
  references, including active and completed command-center states;
- `target-architecture.md` records immutable completed runs and lineage-based next flows;
- Wave 26 local tasks are split and promoted into the short backlog queue.

### Epic W26-E1 — flow lineage core model and launch services (`done`)
Linked stories: `US-02`, `US-03`, `US-07`, `US-10`, `US-11`

#### Slice W26-E1-S1 — completed-run handoff read model (`done`)
Goal: expose terminal-run summaries, follow-up candidates, and lineage references through
runtime-agnostic operator frontend services.

Primary outputs:

- terminal run summary read model
- next-flow action recommendations
- source-run and baseline lineage references

Touched areas:

- `src/aidd/core/operator_frontend_models.py`
- `src/aidd/core/operator_frontend_dashboard.py`
- `src/aidd/core/run_store*.py`
- `tests/core/test_operator_frontend.py`

Dependencies:

- `W26-E0-S1`

Local tasks:

- `W26-E1-S1-T1` (done) Add a terminal-run handoff read model that exposes final QA status,
  final artifacts, blockers, repair counts, approval counts, questions answered, and
  recommended next-flow actions.
  - Scope: core operator frontend read models only.
  - Verification: `tests/core/test_operator_frontend.py` covers completed, failed, and
    completed-with-warning run summaries.
- `W26-E1-S1-T2` (done) Add lineage reference fields for source run, source work item, baseline,
  and child work item candidates without changing adapter semantics.
  - Scope: core run/work-item metadata read path.
  - Verification: core tests prove old runs still render and new lineage fields are
    optional, escaped, and source-of-truth derived.

Exit evidence:

- completed runs render actionable handoff data without JavaScript inferring workflow
  state;
- lineage references are core-owned and runtime-agnostic.

#### Slice W26-E1-S2 — next-flow draft and launch services (`done`)
Goal: create new work item or run drafts from completed-run context through core services
instead of direct UI document mutation.

Primary outputs:

- follow-up work item draft service
- clone flow draft service
- launch preflight service

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W26-E1-S1`

Local tasks:

- `W26-E1-S2-T1` (done) Implement a follow-up draft service that selects QA findings, review
  notes, failed evidence, or manual requests and produces a new work item request
  document with source-run references.
  - Scope: core work-item creation service.
  - Verification: core tests prove selected findings become durable Markdown context and
    source artifacts are referenced, not rewritten.
- `W26-E1-S2-T2` (done) Implement a clone-flow draft service that reuses runtime id, prompt pack,
  contracts path, branch or commit, and baseline references while assigning a new run or
  work item identity.
  - Scope: core launch draft service.
  - Verification: core tests prove cloned flow configuration is explicit and editable
    before launch.
- `W26-E1-S2-T3` (done) Add launch preflight validation for next-flow drafts, including writable
  workspace, valid runtime selection, contract availability, baseline availability, and
  source-run existence.
  - Scope: core preflight and CLI/API error payloads.
  - Verification: focused tests cover pass, warning, and blocking preflight outcomes.

Exit evidence:

- follow-up and cloned flows are independent units with durable source-run links;
- launch preflight blocks unsafe or ambiguous next-flow starts before runtime execution.

#### Slice W26-E1-S3 — workbench and evidence read models (`done`)
Goal: expose the non-handoff Mission Control screens through core-owned read models so the
static UI does not infer document, recovery, diagnostic, or provenance state in JavaScript.

Primary outputs:

- stage document workbench read model
- recovery and diagnostics read-model extensions
- evidence graph read model

Touched areas:

- `src/aidd/core/operator_frontend_models.py`
- `src/aidd/core/operator_frontend_artifacts.py`
- `src/aidd/core/operator_frontend_logs.py`
- `src/aidd/core/operator_frontend_questions.py`
- `src/aidd/core/operator_frontend_dashboard.py`
- `tests/core/test_operator_frontend.py`

Dependencies:

- `W26-E1-S1`

Local tasks:

- `W26-E1-S3-T1` (done) Add a stage document workbench read model for Markdown preview/source
  metadata, available diff inputs, contract requirements, validation results, references,
  and version or model-authored change history when present.
  - Scope: core operator frontend document/artifact read models only.
  - Verification: core tests cover present, missing, large/truncated, and invalid
    document states without editing runtime-authored artifacts.
- `W26-E1-S3-T2` (done) Add recovery and diagnostics read-model fields for blocking questions,
  validation/repair attempts, raw-log source summaries, runtime approval queues, and
  stage-scoped request-change context.
  - Scope: core operator frontend question, validation, log, and approval summaries.
  - Verification: core tests cover blocked, repair-available, stopped, approval-waiting,
    and log-truncated states.
- `W26-E1-S3-T3` (done) Add an evidence graph read model that derives nodes and edges from
  artifact indexes, stage outputs, validator reports, run events, approvals, and logs
  without creating a new canonical artifact format.
  - Scope: core artifact/provenance read model.
  - Verification: core tests prove graph nodes link back to existing artifacts and degrade
    to a flat artifact table when graph inputs are incomplete.

Exit evidence:

- workbench, recovery, diagnostics, and evidence screens consume typed core payloads;
- no visual graph or document state becomes a JavaScript-only source of truth.

### Epic W26-E2 — accepted operator UI screens (`done`)
Linked stories: `US-05`, `US-06`, `US-11`

#### Slice W26-E2-S0 — static UI refactoring foundation (`done`)
Goal: reduce the current packaged static UI monolith before adding the larger Mission
Control screen set, while preserving the no-Node and no-Vite packaging model.

Current-main analysis:

- `origin/main` is currently `36dc558`; rebasing `codex/operator-ui-mission-control-backlog`
  onto `origin/main` was a no-op.
- Main already split packaged assets into `src/aidd/cli/static/` and split operator
  frontend read models into smaller core modules.
- The remaining UI implementation is still concentrated in `operator.js` and
  `operator.css`; before adding the new screens, the static UI needs explicit
  module/resource boundaries so rendering, state, API, logs, artifacts, questions,
  approvals, and next-flow controls do not become one larger file.

Primary outputs:

- multi-resource static asset loader
- smaller browser JavaScript modules or equivalent packaged static boundaries
- CSS token, layout, and component boundaries
- targeted static UI contract tests

Touched areas:

- `src/aidd/cli/ui_assets.py`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/cli/test_ui_assets_contracts.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W25-E4-S2`
- `W26-E1-S1`

Local tasks:

- `W26-E2-S0-T1` (done) Add a packaged static asset manifest or loader that can serve multiple
  UI JavaScript and CSS resources while preserving the existing `/operator.js` and
  `/operator.css` compatibility routes.
  - Scope: static resource loader and UI HTTP serving only.
  - Verification: package resource tests and UI endpoint tests prove old routes still
    work and new static resources are included in source and wheel builds.
- `W26-E2-S0-T2` (done) Split `operator.js` into smaller packaged browser modules for API/state,
  shell rendering, stage cockpit rendering, artifacts/documents, logs/jobs, questions,
  approvals/interventions, and next-flow actions.
  - Scope: static JavaScript resources only.
  - Verification: existing UI tests pass and static contract tests assert each module owns
    its intended surface without removing escaping, accessibility, or runtime-selection
    safeguards.
- `W26-E2-S0-T3` (done) Split `operator.css` into token, layout, component, and responsive layers
  or equivalent clearly bounded sections before adding Mission Control-specific styles.
  - Scope: static CSS resources only.
  - Verification: CSS contract tests keep focus, screen-reader, truncation, saved-answer,
    mobile rail, and density rules present.
- `W26-E2-S0-T4` (done) Split monolithic script-string assertions in `tests/cli/test_ui.py` into
  targeted UI asset contract tests organized by surface.
  - Scope: UI tests only.
  - Verification: focused UI asset and UI endpoint tests pass with the same behavior
    checks but smaller failure surfaces.

Exit evidence:

- Mission Control UI work can add new screens without extending the current static
  JavaScript/CSS monoliths;
- existing local UI behavior, package resource loading, and no-Node packaging remain
  compatibility-preserved.

#### Slice W26-E2-S1 — Mission Control shell updates (`done`)
Goal: update the existing static operator console shell to match the accepted screen
inventory while preserving the no-Node packaging model.

Primary outputs:

- setup screen with previous-run context
- active and completed command center states
- run history lineage view

Touched areas:

- `src/aidd/cli/static/index.html`
- `src/aidd/cli/static/operator.css`
- `src/aidd/cli/static/operator.js`
- `src/aidd/cli/static/operator-*.css`
- `tests/cli/test_ui_assets_contracts.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W26-E1-S1`
- `W26-E2-S0`

Local tasks:

- `W26-E2-S1-T1` (done) Render the Project Setup mode selector with New Work Item,
  Follow-up Flow, Clone Previous Flow, Eval / Scenario Batch, and previous-run context.
  - Scope: packaged static UI shell and dashboard payload rendering.
  - Verification: UI endpoint and static DOM tests cover mode selection and inherited
    context rendering.
- `W26-E2-S1-T2` (done) Render Flow Complete in the command center with Start Next Flow actions
  and final artifact, blocker, evidence, approval, and safety summaries.
  - Scope: dashboard UI state for terminal runs.
  - Verification: static and service-level UI tests cover completed-run action visibility
    and no hidden generic runtime fallback.
- `W26-E2-S1-T3` (done) Render run history lineage with parent run, child work item, next-action
  badges, and actions for follow-up, clone, eval batch, and archive.
  - Scope: run-history UI and read model consumption.
  - Verification: UI tests prove lineage rows link to existing run/artifact data and
    escape dynamic labels.

Exit evidence:

- operators can see where the current run ended and what can safely happen next;
- setup and history screens can both start the next-flow path.

#### Slice W26-E2-S2 — Start Next Flow wizard (`done`)
Goal: provide a safe handoff wizard for selecting source findings, defining a new work
item, and confirming launch.

Primary outputs:

- source findings selection screen
- follow-up work item definition screen
- launch confirmation screen

Touched areas:

- `src/aidd/cli/static/`
- `src/aidd/cli/ui_http.py`
- `tests/cli/test_ui.py`
- `tests/cli/test_ui_assets_contracts.py`

Dependencies:

- `W26-E1-S2`
- `W26-E2-S1`

Local tasks:

- `W26-E2-S2-T1` (done) Render source findings selection grouped by QA findings, review notes,
  failed evidence, and manual request.
  - Scope: wizard UI and API payload rendering.
  - Verification: tests cover selection state, source artifact links, and required
    context counts.
- `W26-E2-S2-T2` (done) Render follow-up work item definition with generated acceptance
  criteria, required evidence, inherited context toggles, and first-stage input preview.
  - Scope: wizard UI and follow-up draft payload.
  - Verification: tests prove generated fields remain editable and source-run context is
    visible before launch.
- `W26-E2-S2-T3` (done) Render launch confirmation with preflight results, audit preview,
  source artifact links, and the Launch Flow Now action.
  - Scope: wizard UI and private launch preflight integration.
  - Verification: tests cover pass, warning, and blocked preflight states.

Exit evidence:

- the wizard makes it explicit that follow-up creates a new work item and run;
- launch cannot proceed without visible lineage and preflight evidence.

#### Slice W26-E2-S3 — workbench, recovery, diagnostics, and evidence screens (`done`)
Goal: update the remaining accepted Mission Control screens so the whole visual reference
set is implementable, not only setup, run history, and next-flow handoff.

Primary outputs:

- Stage Document Workbench screen
- Questions / Interview Loop screen
- Validation / Repair Center screen
- Runtime Logs / Live Console screen
- Artifacts / Evidence Graph screen
- Approvals / Request Change screen

Touched areas:

- `src/aidd/cli/static/index.html`
- `src/aidd/cli/static/operator.css`
- `src/aidd/cli/static/operator.js`
- `tests/cli/test_ui_assets_contracts.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W26-E1-S3`
- `W26-E2-S1`

Local tasks:

- `W26-E2-S3-T1` (done) Render the Stage Document Workbench with artifact tree, Markdown
  preview/source/diff controls, contract requirements, validation results, missing
  evidence, references, and version history.
  - Scope: packaged static UI document workbench.
  - Verification: static and endpoint tests cover document loading, source/preview state,
    truncation labels, and contract/validation sidebars.
- `W26-E2-S3-T2` (done) Render Questions / Interview Loop and Validation / Repair Center as
  first-class recovery screens with required answers, blocked stages, repair attempt
  timeline, Run Repair, Stop Run, and Request Change actions.
  - Scope: packaged static UI recovery surfaces.
  - Verification: UI tests cover unresolved, resolved, partial, deferred, repair-available,
    repair-exhausted, and explicit-stop states.
- `W26-E2-S3-T3` (done) Render Runtime Logs / Live Console and Approvals / Request Change with
  raw log source filters, bounded-log notices, approval queue, diff preview, intervention
  composer, and audit log.
  - Scope: packaged static UI diagnostics and human-control surfaces.
  - Verification: UI tests cover raw/saved logs, truncation visibility, approval decisions,
    request-change submission, and escaped dynamic runtime values.
- `W26-E2-S3-T4` (done) Render Artifacts / Evidence Graph with provenance nodes, edge selection,
  artifact inspector, flat table fallback, and open/download/copy-path actions.
  - Scope: packaged static UI evidence graph and artifact explorer.
  - Verification: UI tests cover complete graph, incomplete graph fallback, selected node
    inspector, artifact path escaping, and no mutation of source artifacts.

Exit evidence:

- all accepted visual references have an implementation task and verification path;
- recovery and diagnostic actions stay auditable and core-backed.

### Epic W26-E3 — API, safety, and regression coverage (`done`)
Linked stories: `US-03`, `US-06`, `US-10`, `US-11`

#### Slice W26-E3-S1 — private UI next-flow API (`done`)
Goal: expose next-flow draft, preflight, launch, and archive operations through local UI
endpoints backed by core services.

Primary outputs:

- private follow-up and clone draft endpoints
- launch endpoint
- archive decision endpoint

Touched areas:

- `src/aidd/cli/ui_http.py`
- `src/aidd/cli/ui.py`
- `src/aidd/core/`
- `tests/cli/test_ui.py`

Dependencies:

- `W26-E1-S2`

Local tasks:

- `W26-E3-S1-T1` (done) Add private UI endpoints for follow-up and clone draft creation with
  request-size limits, escaped response fields, and deterministic malformed-body errors.
  - Scope: local UI HTTP layer.
  - Verification: CLI UI tests cover success and invalid payloads without invoking real
    runtimes.
- `W26-E3-S1-T2` (done) Add a launch endpoint that creates the new independent work item or run,
  writes audit lineage, and dispatches normal workflow execution only after explicit
  runtime selection.
  - Scope: UI HTTP integration with core launch services.
  - Verification: tests prove launch delegates to core services and does not mutate the
    source run.
- `W26-E3-S1-T3` (done) Add an archive decision endpoint for completed runs that records local
  operator intent without deleting artifacts or blocking future read-only inspection.
  - Scope: UI HTTP and run metadata.
  - Verification: tests prove archive state is visible in dashboard/history and artifacts
    remain readable.

Exit evidence:

- every new UI write path has a narrow core-backed service boundary;
- completed source artifacts remain immutable after next-flow actions.

#### Slice W26-E3-S2 — deterministic UI and accessibility coverage (`done`)
Goal: prove the accepted design through tests and manual browser checklist updates without
introducing a Node build pipeline.

Primary outputs:

- static DOM contract coverage
- service-level next-flow regressions
- manual browser checklist update

Touched areas:

- `tests/cli/`
- `tests/core/`
- `docs/e2e/operator-ui-local-project.md`

Dependencies:

- `W26-E2-S1`
- `W26-E2-S2`
- `W26-E3-S1`

Local tasks:

- `W26-E3-S2-T1` (done) Add static DOM contract tests for the accepted screen landmarks, flow
  complete state, wizard controls, lineage labels, and focus-visible affordances.
  - Scope: `tests/cli/test_ui_assets_contracts.py`.
  - Verification: focused static UI asset tests pass.
- `W26-E3-S2-T2` (done) Add service-level UI regressions for completed-run next action,
  follow-up draft creation, clone draft creation, launch preflight, and archive decision.
  - Scope: `tests/cli/test_ui.py` and `tests/core/test_operator_frontend.py`.
  - Verification: focused UI/core pytest suite passes.
- `W26-E3-S2-T3` (done) Extend the manual browser checklist with Flow Complete, Start Next Flow,
  wizard, run-history lineage, desktop/tablet/mobile, and keyboard paths.
  - Scope: `docs/e2e/operator-ui-local-project.md`.
  - Verification: docs consistency tests assert the checklist sections remain present.

Exit evidence:

- accepted UI semantics are covered by deterministic tests;
- manual browser evidence can validate the completed-flow handoff in realistic viewports.

### Epic W26-E4 — live E2E and eval evidence integration (`done`)
Linked stories: `US-07`, `US-10`, `US-11`

#### Slice W26-E4-S1 — local-project UI E2E next-flow lane (`done`)
Goal: update the local-project operator UI evidence lane so it proves completed-run
handoff and lineage before public-repository live evidence is refreshed.

Primary outputs:

- local-project completed-run checklist
- deterministic fixture or service path for terminal run state
- manual smoke evidence instructions

Touched areas:

- `docs/e2e/operator-ui-local-project.md`
- `harness/scenarios/smoke/`
- `tests/cli/`

Dependencies:

- `W26-E3-S2`

Local tasks:

- `W26-E4-S1-T1` (done) Update the operator UI local-project E2E lane to require Flow Complete,
  Start Next Flow, follow-up draft, launch preflight, and run-history lineage checks.
  - Scope: E2E documentation only.
  - Verification: docs consistency test covers the new checklist sections.
- `W26-E4-S1-T2` (done) Add deterministic local fixture coverage that seeds a terminal run and
  proves the UI can create a follow-up draft without invoking a real provider runtime.
  - Scope: deterministic UI/service tests or smoke fixture data.
  - Verification: focused pytest proves source-run lineage and draft artifact references.
- `W26-E4-S1-T3` (done) Record a manual installed local-project smoke path for completed-run
  handoff, including expected evidence and cleanup rules for generated `.aidd/` state.
  - Scope: E2E docs and roadmap evidence.
  - Verification: manual smoke notes identify run id, source work item, child work item,
    browser, viewport, runtime id, and blockers.

Exit evidence:

- the local UI lane proves the new completed-flow behavior without depending on public
  repositories or provider credentials.

#### Slice W26-E4-S2 — public live E2E next-flow checkpoint logic (`done`)
Goal: update the black-box live E2E logic so final run evidence records completed-flow
handoff readiness and optional next-flow lineage without turning live E2E into a CI gate.

Primary outputs:

- live catalog next-flow checkpoint policy
- black-box evaluator final checkpoint evidence:
  `next-flow-checkpoint.json` and `next-flow-checkpoint.md`
- optional child-flow lineage evidence: `next-flow-lineage.json`
- result-bundle tests for next-flow evidence

Touched areas:

- `docs/e2e/live-e2e-catalog.md`
- `.agents/skills/live-e2e/`
- `src/aidd/harness/live_e2e_black_box*.py`
- `tests/harness/`

Dependencies:

- `W26-E4-S1`

Local tasks:

- `W26-E4-S2-T1` (done) Define the manual live E2E next-flow checkpoint policy: after terminal
  `qa`, inspect Flow Complete and record the operator's next-flow decision, but do not
  require launching a second public-repository flow by default.
  - Scope: live E2E docs and live-e2e skill guidance.
  - Verification: docs consistency tests cover the policy and keep live E2E manual-only.
- `W26-E4-S2-T2` (done) Extend the black-box live evaluator final checkpoint to capture
  completed-run next-action evidence, source-run summary, and optional lineage metadata in
  the result bundle.
  - Scope: live evaluator orchestration and report writer modules.
  - Verification: harness tests prove the final bundle contains
    `next-flow-checkpoint.json` and `next-flow-checkpoint.md` for completed, failed, and
    blocked terminal runs.
- `W26-E4-S2-T3` (done) Add an optional maintained-scenario follow-up proof path that creates a
  follow-up draft from QA findings when the operator explicitly enables it for a manual
  run.
  - Scope: live scenario policy and evaluator option handling.
  - Verification: unit tests prove the option is off by default, manual-only, and records
    `next-flow-lineage.json` with child work item lineage when enabled.

Exit evidence:

- public live E2E validates the new UX decision point without requiring nested live
  provider work by default;
- optional follow-up proof records lineage when a maintainer deliberately runs it.

### Epic W26-E5 — operator documentation and rollout clarity (`done`)
Linked stories: `US-09`, `US-11`

#### Slice W26-E5-S1 — completed-flow operator documentation (`done`)
Goal: document the completed-run handoff and lineage model for operators after the UI and
core services land.

Primary outputs:

- README operator UI summary update
- operator handbook next-flow section
- troubleshooting notes for blocked next-flow preflight

Touched areas:

- `README.md`
- `docs/operator-handbook.md`
- `docs/operator-troubleshooting.md`
- `tests/test_docs_consistency.py`

Dependencies:

- `W26-E3-S1`
- `W26-E4-S1`

Local tasks:

- `W26-E5-S1-T1` (done) Document completed-run handoff, follow-up flow creation, clone flow,
  eval batch handoff, archive behavior, and source-run lineage in operator-facing docs.
  - Scope: operator documentation only.
  - Verification: docs consistency tests assert the operator docs describe next-flow
    actions and keep local-project UI and live E2E boundaries distinct.

Exit evidence:

- operators can understand when to create a new work item, follow-up, clone, eval batch,
  or archive decision without reading implementation code;
- docs preserve the distinction between local-project UI proof and public-repository live
  E2E checkpoint evidence.

## Wave 27 — onboarding-first operator startup (`planned`)

Goal: make the first-run operator path UI-first while preserving the existing governed
workflow, project-local `.aidd/` ownership, explicit runner selection, and CLI-equivalent
provenance. Existing CLI subcommands and scripted flows remain compatible; onboarding
extends the UI surface instead of replacing CLI operation.

### Epic W27-E1 — onboarding UX and startup contract (`planned`)
Linked stories: `US-01`, `US-06`, `US-09`, `US-11`, `US-12`

#### Slice W27-E1-S1 — onboarding-first contract (`planned`)
Goal: define the UI-first startup flow before implementation changes the public command
surface or workspace setup behavior.

Primary outputs:

- onboarding-first operator frontend contract
- CLI compatibility and no-regression acceptance criteria
- project scope and multi-project boundary decision
- mandatory runner-selection decision
- operator-facing startup documentation plan

Touched areas:

- `docs/architecture/operator-frontend.md`
- `README.md`
- `docs/operator-handbook.md`
- `tests/test_docs_consistency.py`
- `docs/backlog/`

Dependencies:

- `W26-E5-S1`

Local tasks:

- `W27-E1-S1-T1` Define the onboarding-first operator UI contract covering preserved CLI
  behavior, no-work-item `aidd ui`, optional explicit onboarding launcher, project root
  selection, `.aidd` workspace ownership, work-item create/resume, runner selection, and
  multi-project isolation.
  - Scope: architecture and planning documents only.
  - Verification: docs consistency or `rg` checks prove the contract names CLI
    compatibility requirements, the startup entrypoint, project root rules,
    runner-selection requirement, and multi-project boundary.
- `W27-E1-S1-T2` Document the operator-facing UI-first startup path in README and the
  operator handbook without removing explicit CLI subcommand examples.
  - Scope: operator documentation only.
  - Verification: docs consistency tests prove README and handbook describe UI onboarding,
    explicit runner selection, project-local `.aidd/` ownership, and unchanged scripted CLI
    command examples.

Exit evidence:

- maintainers can implement onboarding without debating whether the UI owns workflow
  semantics;
- operators can see that the recommended first-run path starts in the UI, while scripted
  CLI paths keep their existing behavior and examples;
- unrelated projects stay isolated even if a launcher UI lists recent projects.

### Epic W27-E2 — onboarding launch shell and project setup (`planned`)
Linked stories: `US-09`, `US-11`, `US-12`

#### Slice W27-E2-S1 — rootless UI launch (`planned`)
Goal: let the operator start the local UI before a work item exists while preserving the
existing initialized-work-item command center path.

Primary outputs:

- no-work-item `aidd ui` setup mode
- explicit onboarding launcher decision without changing existing CLI behavior
- command compatibility coverage for explicit subcommands and help

Touched areas:

- `src/aidd/cli/main.py`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/cli/`

Dependencies:

- `W27-E1-S1`

Local tasks:

- `W27-E2-S1-T1` Allow `aidd ui` to start without `--work-item` and serve setup mode
  before a project/work-item context exists.
  - Scope: local UI command options, server options, and setup-mode routing.
  - Verification: CLI UI tests prove no-work-item launch serves setup mode and existing
    `--work-item` launch still opens the command center.
- `W27-E2-S1-T2` Add an explicit onboarding launcher only after the contract preserves bare
  `aidd`, `aidd --help`, and existing subcommand behavior.
  - Scope: Typer command entrypoint only.
  - Verification: CLI tests prove existing no-arg/help/subcommand behavior remains
    unchanged and the explicit onboarding launcher reaches setup mode.

Exit evidence:

- a new operator can run one command and reach the setup UI;
- existing CLI workflows and help behavior keep their current command behavior.

#### Slice W27-E2-S2 — project and work-item setup wizard (`planned`)
Goal: create or resume project-local AIDD work from the UI without writing workflow
artifacts outside the selected project root.

Primary outputs:

- UI-neutral onboarding project validation service
- project root entry and validation UI
- work-item create/resume UI backed by existing workspace bootstrap behavior

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W27-E2-S1`
- `W20-E4-S2`

Local tasks:

- `W27-E2-S2-T1` Add an onboarding service that validates a selected local project root,
  resolves the project-local `.aidd` workspace, discovers existing work items, and rejects
  path escapes.
  - Scope: UI-neutral core onboarding service.
  - Verification: core tests cover valid roots, missing roots, file paths, parent escapes,
    symlink escapes, existing `.aidd`, and empty-project initialization.
- `W27-E2-S2-T2` Render the Project Setup wizard for path entry, existing workspace
  detection, work-item create/resume, and request seeding.
  - Scope: packaged static UI setup screens and local UI endpoints.
  - Verification: UI tests cover setup rendering, validation errors, create/resume
    payloads, escaped paths, and no direct mutation of generated stage artifacts.
- `W27-E2-S2-T3` Route completed setup into the existing command center with the selected
  project root, work item, root, and config snapshot.
  - Scope: UI service context switching after setup completion.
  - Verification: UI tests prove the command center reads the selected `.aidd` workspace
    and workflow launches use the selected context.

Exit evidence:

- UI onboarding can initialize the same state as `aidd init`;
- existing `.aidd` work items can be resumed without creating duplicate workspaces;
- selected project context is explicit in subsequent run requests.

### Epic W27-E3 — runner selection during onboarding (`planned`)
Linked stories: `US-01`, `US-06`, `US-09`, `US-11`

#### Slice W27-E3-S1 — mandatory runner selection (`planned`)
Goal: make runner choice part of onboarding and every launch while keeping readiness
observational and runtime-specific behavior inside adapters.

Primary outputs:

- project-scoped runtime readiness query for onboarding
- runner selection cards with unavailable/setup states
- optional project-local runner preference that never replaces explicit launch payloads

Touched areas:

- `src/aidd/core/runtime_readiness.py`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W27-E2-S2`
- `W21-E1-S1`

Local tasks:

- `W27-E3-S1-T1` Expose runtime readiness for the selected project/config during
  onboarding before a work item run exists.
  - Scope: runtime readiness read model and local UI endpoint plumbing.
  - Verification: core/UI tests cover default and project config command sources,
    provider unavailable, execution command unavailable, and timeout profile display.
- `W27-E3-S1-T2` Render onboarding runner selection cards and disable launch until the
  operator explicitly selects a ready or intentionally degraded runner.
  - Scope: packaged static onboarding UI.
  - Verification: UI tests cover ready, unavailable, degraded, and missing-selection
    states without hardcoded `generic-cli` fallback.
- `W27-E3-S1-T3` Persist an optional project-local runner preference only as operator UI
  convenience while every workflow, stage, intervention, follow-up, and clone launch still
  sends an explicit runtime id.
  - Scope: UI preference storage and launch request construction.
  - Verification: tests prove saved preference preselects UI state but run manifests and
    API payloads still contain explicit operator-selected runtime ids.

Exit evidence:

- onboarding cannot start hidden-runtime work;
- readiness tells the operator what is installed/authenticated without becoming workflow
  source of truth;
- runner preference improves ergonomics without weakening run provenance.

### Epic W27-E4 — multi-project onboarding boundaries (`planned`)
Linked stories: `US-11`, `US-12`

#### Slice W27-E4-S1 — project-set setup and project switching (`planned`)
Goal: support multi-root local work as declared project sets while keeping unrelated
projects isolated from one another.

Primary outputs:

- project-set declaration UI for monorepo or related local roots
- noncanonical recent-project switcher for unrelated projects
- isolation tests for per-project `.aidd` state and active UI jobs

Touched areas:

- `src/aidd/core/project_set.py`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/core/`
- `tests/cli/`
- `docs/e2e/operator-ui-local-project.md`

Dependencies:

- `W27-E2-S2`
- `W27-E3-S1`
- `W20-E3-S4`

Local tasks:

- `W27-E4-S1-T1` Add a project-set declaration step for multiple roots inside the
  selected local project, using the existing bounded project-set resolver.
  - Scope: onboarding UI and project-set config/write path.
  - Verification: tests cover stable ids, duplicate ids, duplicate roots, missing roots,
    parent escapes, symlink escapes, and `project-set.md` context persistence.
- `W27-E4-S1-T2` Add a recent-project switcher as noncanonical UI cache while keeping
  each active workflow, job, and `.aidd` workspace scoped to one selected project.
  - Scope: local UI cache and context-switching guardrails.
  - Verification: UI tests prove switching projects does not mix work items, logs,
    runtime jobs, answers, or artifacts across project roots.

Exit evidence:

- one UI can help the operator choose among recent projects, but each flow remains
  scoped to exactly one project-local `.aidd` workspace;
- multiple roots inside one monorepo use project-set declarations rather than ad hoc
  cross-project state;
- concurrent unrelated-project execution remains separated unless a later design adds a
  multi-context job registry.

### Epic W27-E5 — onboarding evidence and rollout docs (`planned`)
Linked stories: `US-07`, `US-09`, `US-11`, `US-12`

#### Slice W27-E5-S1 — onboarding local-project evidence (`planned`)
Goal: prove the UI-first onboarding path with deterministic local fixtures and manual
installed smoke instructions before treating it as the default operator entrypoint.

Primary outputs:

- deterministic onboarding UI fixture coverage
- source-installed onboarding smoke path
- operator troubleshooting notes for setup and runner blockers

Touched areas:

- `tests/cli/`
- `tests/core/`
- `harness/scenarios/smoke/`
- `docs/e2e/operator-ui-local-project.md`
- `docs/operator-troubleshooting.md`

Dependencies:

- `W27-E4-S1`

Local tasks:

- `W27-E5-S1-T1` Add deterministic local UI onboarding coverage for project selection,
  work-item creation, runner readiness, bounded fixture execution, questions, logs, and
  artifacts.
  - Scope: service/static UI tests and fixture-backed smoke scenario updates.
  - Verification: focused pytest and scenario-loader tests prove the onboarding fixture
    path without provider credentials.
- `W27-E5-S1-T2` Record the source-installed manual onboarding smoke path and cleanup
  rules for generated `.aidd` state.
  - Scope: E2E/operator docs only.
  - Verification: docs consistency tests assert the smoke checklist names setup URL,
    selected project root, work item, runtime id, browser/viewport, evidence files, and
    cleanup rules.
- `W27-E5-S1-T3` Add troubleshooting notes for invalid project roots, missing runtime
  binaries, unauthenticated providers, unavailable execution commands, and stale UI
  project preferences.
  - Scope: operator troubleshooting docs only.
  - Verification: docs consistency tests cover the setup and runner blocker sections.

Exit evidence:

- UI-first onboarding is proven through local deterministic evidence before release docs
  present it as the default path;
- operators have recovery guidance for the likely first-run blockers.

Sync notes:

- `2026-06-02` Wave 27 opened from operator feedback that first-run AIDD should guide
  onboarding through the UI while existing CLI commands remain compatible.
  `W27-E1-S1-T1` is promoted to `Next`, `W27-E1-S1-T2` and `W27-E2-S1-T1` are promoted
  to `Soon`, and the remaining implementation/evidence tasks stay in `Parking lot` until
  the onboarding contract is accepted.
