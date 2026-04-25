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
- GHCR verification
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
- `W10-E1-S1-T3` (done) Add a post-publish GHCR verification job to the `release` workflow that retries up to 10 times with 30-second backoff until the tagged image is pullable, then runs `aidd --version` and `aidd doctor` in the container.
- `W10-E1-S1-T4` (done) Update release documentation so the three verification jobs are required release evidence for tagged builds.

Sync notes:

- `2026-04-23` `W10-E1-S1-T1` completed: release workflow now includes a post-publish PyPI verification job with bounded retries and explicit `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T2` completed: release workflow now includes a post-publish `uv tool install` verification job with bounded retries and explicit `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T3` completed: release workflow now includes a post-publish GHCR verification job with bounded pull retries and containerized `aidd --version`/`aidd doctor` checks.
- `2026-04-23` `W10-E1-S1-T4` completed: release checklist now names the three post-publish verification jobs as required tagged-release evidence.

Exit evidence:

- a tagged release produces visible pass/fail evidence for `pipx`, `uv tool install`, and GHCR install paths.

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

## Wave 15 — readiness recovery and verification hygiene (`next`)

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

- `uv run ruff check .` passes;
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

### Epic W15-E3 — external evidence lanes (`next`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W15-E3-S1 — fresh manual live evidence (`next`)
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

Local tasks:

- `W15-E3-S1-T1` Run one prepared manual live E2E scenario with a maintained runtime and preserve the eval artifacts for audit.

Exit evidence:

- a current `.aidd/reports/evals/<run_id>/` bundle exists for the selected live scenario;
- the report distinguishes runtime, model, document, adapter, and environment evidence.

#### Slice W15-E3-S2 — release-channel evidence capture (`later`)
Goal: prove package release channels on the next release candidate without making live E2E part of release gating.

Primary outputs:

- release-channel verification transcript
- package installation evidence
- container smoke evidence

Touched areas:

- release artifacts
- `reports/`

Dependencies:

- release candidate tag and publishing credentials

Local tasks:

- `W15-E3-S2-T1` Capture PyPI or TestPyPI, `uv tool`, `pipx`, and container smoke evidence for the next release candidate.

Exit evidence:

- release verification artifacts show install and CLI smoke behavior from published channels;
- live E2E remains manual-only and outside release gating.

Sync notes:

- `2026-04-25` Wave 15 was opened via `W8-E3-S1` queue-restoration policy after readiness audit findings showed Wave 14 complete, no current `next` slice, and an empty backlog queue.
- `2026-04-25` Initial Wave 15 queue restoration completes `W15-E0-S1-T1`, promotes `W15-E1-S1-T1` to `Next`, `W15-E2-S1-T1` to `Soon`, and parks `W15-E3-S1-T1` plus `W15-E3-S2-T1` for external-evidence work.
- `2026-04-25` `W15-E1-S1-T1` completed: the live-E2E docs consistency assertion remains contract-equivalent while the deterministic lint gate passes; backlog advanced `W15-E2-S1-T1` to `Next`.
- `2026-04-25` `W15-E2-S1-T1` completed: Wave 12 and Wave 13 local task bullets now carry explicit `(done)` markers without changing their completed parent statuses; backlog advanced `W15-E3-S1-T1` to `Next`.
