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

---

## Wave 0 — bootstrap artifacts and contributor ergonomics (`done`)

### Epic W0-E1 — root docs and architecture (`done`)
Linked stories: `US-01`, `US-02`, `US-07`, `US-09`, `US-10`

#### Slice W0-E1-S1 — root documentation set (`done`)
Goal: provide a clear project overview and contributor entrypoint.

Local tasks:

- `W0-E1-S1-T1` (done) Write `README.md`.
- `W0-E1-S1-T2` (done) Write lightweight root `AGENTS.md`.
- `W0-E1-S1-T3` (done) Add `CLAUDE.md` as a compatibility entrypoint.

#### Slice W0-E1-S2 — architecture baseline (`done`)
Goal: fix the initial architecture and protocol decisions.

Local tasks:

- `W0-E1-S2-T1` (done) Write target architecture.
- `W0-E1-S2-T2` (done) Write adapter protocol.
- `W0-E1-S2-T3` (done) Write document contract rules.
- `W0-E1-S2-T4` (done) Write eval/harness integration.
- `W0-E1-S2-T5` (done) Write runtime matrix and distribution notes.

### Epic W0-E2 — planning system and agent ergonomics (`done`)
Linked stories: `US-10`

#### Slice W0-E2-S1 — planning model (`done`)
Goal: make work selection explicit and hierarchical.

Local tasks:

- `W0-E2-S1-T1` (done) Define wave/epic/slice/local-task planning.
- `W0-E2-S1-T2` (done) Write the canonical roadmap.
- `W0-E2-S1-T3` (done) Write the short backlog queue.

#### Slice W0-E2-S2 — agent ergonomics (`done`)
Goal: reduce repeated prompting for coding agents.

Local tasks:

- `W0-E2-S2-T1` (done) Add nested `AGENTS.md` files.
- `W0-E2-S2-T2` (done) Move team skills into `.agents/skills/`.
- `W0-E2-S2-T3` (done) Add root skills for navigation, backlog work, story checks, live E2E, and log triage.

### Epic W0-E3 — live E2E discovery (`done`)
Linked stories: `US-07`

#### Slice W0-E3-S1 — repository selection (`done`)
Goal: define a first public-repo live E2E set.

Local tasks:

- `W0-E3-S1-T1` (done) Select public repositories.
- `W0-E3-S1-T2` (done) Define starter scenarios.
- `W0-E3-S1-T3` (done) Add starter scenario manifests.

---

## Wave 1 — package, local developer loop, and release scaffolding (`done`)

### Epic W1-E1 — package and CLI scaffold (`done`)
Linked stories: `US-09`

#### Slice W1-E1-S1 — installable Python package (`done`)
Goal: make the repo runnable from source with a real console entrypoint.

Local tasks:

- `W1-E1-S1-T1` (done) Add `pyproject.toml`.
- `W1-E1-S1-T2` (done) Add `src/aidd/__init__.py`.
- `W1-E1-S1-T3` (done) Add a working CLI scaffold.
- `W1-E1-S1-T4` (done) Add CLI smoke tests.

#### Slice W1-E1-S2 — local workspace bootstrap (`done`)
Goal: provide a minimal useful local command.

Local tasks:

- `W1-E1-S2-T1` (done) Implement `aidd doctor`.
- `W1-E1-S2-T2` (done) Implement `aidd init`.
- `W1-E1-S2-T3` (done) Add a sample config file.

### Epic W1-E2 — repository health files (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W1-E2-S1 — contribution and license docs (`done`)
Goal: make the repo ready for external contributors.

Local tasks:

- `W1-E2-S1-T1` (done) Write `CONTRIBUTING.md`.
- `W1-E2-S1-T2` (done) Add `LICENSE`.
- `W1-E2-S1-T3` (done) Add a PR template.

#### Slice W1-E2-S2 — CI and release scaffolding (`done`)
Goal: prepare standard automation for a Python CLI project.

Local tasks:

- `W1-E2-S2-T1` (done) Add CI workflow.
- `W1-E2-S2-T2` (done) Add release workflow.
- `W1-E2-S2-T3` (done) Add `Makefile` and `.gitignore`.

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

- `W2-E1-S5-T1` (done) Define the required `review-spec` inputs, especially the plan artifact and declared review inputs.
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
- `W7-E2-S3-T2` (done) Evidence: reference run `eval-live-005-opencode-20260422T142733Z` recorded `harness_pass`. Run OpenCode on the smoke lane and capture reference bundles.
- `W7-E2-S3-T3` (done) Evidence: reference run `eval-live-006-opencode-20260422T142812Z` recorded `harness_blocked`. Run OpenCode on at least one interview lane and capture reference bundles.
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
6. Replace the bounded current reconciliation note in backlog with the restoration event
   and first promoted task IDs; do not append a permanent queue-movement journal.
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
- `W10-E1-S1-T3` (done) Disposition: historical. Add a post-publish GHCR verification job to the `release` workflow that retries up to 10 times with 30-second backoff until the tagged image is pullable, then runs `aidd --version` and `aidd doctor` in the container.
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

- `W12-E2-S2-T1` (done) Disposition: legacy. Run the old live quality command block after verification, capture the legacy quality transcript artifact, and feed the results into the removed live quality scorer.
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
- `W19-E4-S1-T3` (done) Keep manual live E2E evidence separated from provider/env blockers through the existing manual live workflow and runtime preflight tests.

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
- `W20-E1-S4-T3` (done) Disposition: not applicable. Rerun `AIDD-LIVE-005` on canonical Codex only if OpenCode remains provider/runtime timeout blocked without an AIDD-owned defect.

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
- `2026-05-06` Focused local checks passed after hardening and the then-active legacy quality-parser follow-up: semantic, repair, prompt-quality, and legacy quality-evaluator regressions reported `100 passed`.
- `2026-05-06` OpenCode preflight passed for `AIDD-LIVE-005`: provider `/opt/homebrew/bin/opencode`, version `1.14.30`, native execution command `opencode run --format json --dangerously-skip-permissions`.
- `2026-05-06` Post-hardening rerun `eval-live-005-opencode-20260506T094747Z` produced status `pass`, first failure boundary `none`, and bundle path `.aidd/reports/evals/eval-live-005-opencode-20260506T094747Z`. The run reached `idea -> qa`, and `review` succeeded after one repair for a missing `Verdict` section; the previous `SEM-UNSUPPORTED-CLAIM` blocker did not recur.
- `2026-05-06` The generated live `quality-report.md` still recorded quality gate `fail` because the then-active local quality evaluator only recognized backticked `Review status` lines and missed the contract-valid `## Verdict` / `**approved**` output. That legacy parser mismatch was fixed at the time and later superseded by the execution-only live E2E model with manual post-run quality reports. Generated `.aidd/` artifacts were not edited.

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
- release-readiness notes for latest accepted `0.1.0a15` package-channel evidence and
  `0.1.0a16.dev0` source development state

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
- `W24-E1-S1-T4` (done) Prepare release-readiness notes for the accepted `0.1.0a15`
  package-channel evidence and `0.1.0a16.dev0` source development state
  without creating a tag or
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
- `docs/release-notes-v0.1.0a15-draft.md` and `docs/analysis/beta-readiness-source-audit.md`
  record the latest accepted `0.1.0a15` package-channel evidence and current
  `0.1.0a16.dev0` source development state; accepted package-channel evidence is recorded
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
- Operator-authored `manual quality-report.md` overlays were written in each
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

## Wave 27 — onboarding-first operator startup (`done`)

Goal: make the first-run operator path UI-first while preserving the existing governed
workflow, project-local `.aidd/` ownership, explicit runner selection, and CLI-equivalent
provenance. Existing CLI subcommands and scripted flows remain compatible; onboarding
extends the UI surface instead of replacing CLI operation.

### Epic W27-E1 — onboarding UX and startup contract (`done`)
Linked stories: `US-01`, `US-06`, `US-09`, `US-11`, `US-12`

#### Slice W27-E1-S1 — onboarding-first contract (`done`)
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

- `W27-E1-S1-T1` (done) Define the onboarding-first operator UI contract covering preserved CLI
  behavior, no-work-item `aidd ui`, optional explicit onboarding launcher, project root
  selection, `.aidd` workspace ownership, work-item create/resume, runner selection, and
  multi-project isolation.
  - Scope: architecture and planning documents only.
  - Verification: docs consistency or `rg` checks prove the contract names CLI
    compatibility requirements, the startup entrypoint, project root rules,
    runner-selection requirement, and multi-project boundary.
- `W27-E1-S1-T2` (done) Document the operator-facing UI-first startup path in README and the
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

### Epic W27-E2 — onboarding launch shell and project setup (`done`)
Linked stories: `US-09`, `US-11`, `US-12`

#### Slice W27-E2-S1 — rootless UI launch (`done`)
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

- `W27-E2-S1-T1` (done) Allow `aidd ui` to start without `--work-item` and serve setup mode
  before a project/work-item context exists.
  - Scope: local UI command options, server options, and setup-mode routing.
  - Verification: CLI UI tests prove no-work-item launch serves setup mode and existing
    `--work-item` launch still opens the command center.
- `W27-E2-S1-T2` (done) Disposition: superseded. Add an explicit onboarding launcher only after the contract preserves bare
  `aidd`, `aidd --help`, and existing subcommand behavior.
  - Decision: no separate launcher is needed for the accepted path. `aidd ui` without
    `--work-item` is the supported UI-first setup entrypoint, while bare `aidd` and
    `aidd --help` keep their existing behavior.

Exit evidence:

- a new operator can run one command and reach the setup UI;
- existing CLI workflows and help behavior keep their current command behavior.

#### Slice W27-E2-S2 — project and work-item setup wizard (`done`)
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

- `W27-E2-S2-T1` (done) Add an onboarding service that validates a selected local project root,
  resolves the project-local `.aidd` workspace, discovers existing work items, and rejects
  path escapes.
  - Scope: UI-neutral core onboarding service.
  - Verification: core tests cover valid roots, missing roots, file paths, parent escapes,
    symlink escapes, existing `.aidd`, and empty-project initialization.
- `W27-E2-S2-T2` (done) Render the Project Setup wizard for path entry, existing workspace
  detection, work-item create/resume, and request seeding.
  - Scope: packaged static UI setup screens and local UI endpoints.
  - Verification: UI tests cover setup rendering, validation errors, create/resume
    payloads, escaped paths, and no direct mutation of generated stage artifacts.
- `W27-E2-S2-T3` (done) Route completed setup into the existing command center with the selected
  project root, work item, root, and config snapshot.
  - Scope: UI service context switching after setup completion.
  - Verification: UI tests prove the command center reads the selected `.aidd` workspace
    and workflow launches use the selected context.

Exit evidence:

- UI onboarding can initialize the same state as `aidd init`;
- existing `.aidd` work items can be resumed without creating duplicate workspaces;
- selected project context is explicit in subsequent run requests.

### Epic W27-E3 — runner selection during onboarding (`done`)
Linked stories: `US-01`, `US-06`, `US-09`, `US-11`

#### Slice W27-E3-S1 — mandatory runner selection (`done`)
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

- `W27-E3-S1-T1` (done) Expose runtime readiness for the selected project/config during
  onboarding before a work item run exists.
  - Scope: runtime readiness read model and local UI endpoint plumbing.
  - Verification: core/UI tests cover default and project config command sources,
    provider unavailable, execution command unavailable, and timeout profile display.
- `W27-E3-S1-T2` (done) Render onboarding runner selection cards and disable launch until the
  operator explicitly selects a ready or intentionally degraded runner.
  - Scope: packaged static onboarding UI.
  - Verification: UI tests cover ready, unavailable, degraded, and missing-selection
    states without hardcoded `generic-cli` fallback.
- `W27-E3-S1-T3` (done) Persist an optional project-local runner preference only as operator UI
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

### Epic W27-E4 — multi-project onboarding boundaries (`done`)
Linked stories: `US-11`, `US-12`

#### Slice W27-E4-S1 — project-set setup and project switching (`done`)
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

- `W27-E4-S1-T1` (done) Add a project-set declaration step for multiple roots inside the
  selected local project, using the existing bounded project-set resolver.
  - Scope: onboarding UI and project-set config/write path.
  - Verification: tests cover stable ids, duplicate ids, duplicate roots, missing roots,
    parent escapes, symlink escapes, and `project-set.md` context persistence.
- `W27-E4-S1-T2` (done) Disposition: superseded. Add a recent-project switcher as noncanonical UI cache while keeping
  each active workflow, job, and `.aidd` workspace scoped to one selected project.
  - Decision: recent unrelated project switching remains deferred. The shipped UI keeps
    one active selected project/workspace per process and uses project-set declarations
    for related roots inside that selected project.

Exit evidence:

- one UI can help the operator choose among recent projects, but each flow remains
  scoped to exactly one project-local `.aidd` workspace;
- multiple roots inside one monorepo use project-set declarations rather than ad hoc
  cross-project state;
- concurrent unrelated-project execution remains separated unless a later design adds a
  multi-context job registry.

### Epic W27-E5 — onboarding evidence and rollout docs (`done`)
Linked stories: `US-07`, `US-09`, `US-11`, `US-12`

#### Slice W27-E5-S1 — onboarding local-project evidence (`done`)
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

- `W27-E5-S1-T1` (done) Add deterministic local UI onboarding coverage for project selection,
  work-item creation, runner readiness, bounded fixture execution, questions, logs, and
  artifacts.
  - Scope: service/static UI tests and fixture-backed smoke scenario updates.
  - Verification: focused pytest and scenario-loader tests prove the onboarding fixture
    path without provider credentials.
- `W27-E5-S1-T2` (done) Record the source-installed manual onboarding smoke path and cleanup
  rules for generated `.aidd` state.
  - Scope: E2E/operator docs only.
  - Verification: docs consistency tests assert the smoke checklist names setup URL,
    selected project root, work item, runtime id, browser/viewport, evidence files, and
    cleanup rules.
- `W27-E5-S1-T3` (done) Add troubleshooting notes for invalid project roots, missing runtime
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
- `2026-06-04` Wave 27 was reconciled after accepted `v0.1.0a7` and `v0.1.0a8`
  release evidence. The supported path is `aidd ui` without `--work-item`; the optional
  explicit launcher and unrelated recent-project switcher are superseded/deferred rather
  than active requirements. UI onboarding, explicit runner selection, command-center
  handoff, bounded selected-stage run, operator-control-center visibility, and rollout
  docs are shipped.

---

## Wave 28 — post-a8 operator hardening and release ergonomics (`done`)

Goal: keep the newly published UI-first operator path honest by auditing the installed
package, hardening the next source smoke lane, and tightening maintainer release
ergonomics without changing CLI compatibility or release immutability.

### Epic W28-E1 — post-release closure and evidence (`done`)
Linked stories: `US-07`, `US-09`, `US-11`

#### Slice W28-E1-S1 — accepted-release closure (`done`)
Goal: finish the post-`v0.1.0a8` release bookkeeping and prove `main` is ready for the
next development slice.

Primary outputs:

- release evidence PR merged into `main`
- local `main` synchronized to the accepted post-release version
- release branch/tag traceability retained

Touched areas:

- GitHub PR/release state
- `docs/release-checklist.md`
- `pyproject.toml`
- `uv.lock`

Dependencies:

- accepted `v0.1.0a8` GitHub Release and PyPI evidence

Local tasks:

- `W28-E1-S1-T1` (done) Merge the post-`v0.1.0a8` release evidence PR after CI is green.
  - Scope: GitHub release-follow-up PR only.
  - Verification: PR merge evidence shows green CI, `main` is at `0.1.0a9.dev0`, and
    `docs/release-checklist.md` records the accepted `v0.1.0a8` package evidence.
- `W28-E1-S1-T2` (done) Document PATH-safe GitHub CLI release operations for local maintainer
  shells where `gh` is installed outside the default `PATH`.
  - Scope: release documentation only.
  - Verification: docs checks prove the release checklist names `command -v gh`,
    explicit binary fallback, and no direct tag-push release trigger.

Exit evidence:

- release evidence is on `main`;
- maintainers can run release checks even when the GitHub CLI binary is not in the
  interactive shell `PATH`.

Sync notes:

- `2026-06-04` `W28-E1-S1` completed: PR #65 was merged into `main`, source development
  is back on `0.1.0a9.dev0`, accepted `v0.1.0a8` evidence remains recorded, and the
  release checklist now includes a PATH-safe GitHub CLI fallback for maintainer shells.

### Epic W28-E2 — published UI onboarding audit (`done`)
Linked stories: `US-07`, `US-09`, `US-11`

#### Slice W28-E2-S1 — installed package clean UI smoke (`done`)
Goal: verify the published package path, not the source checkout, can install and run
clean UI onboarding through the first bounded stages.

Primary outputs:

- disposable `/tmp` published-package audit transcript
- API/UI evidence for setup mode, runner selection, stage runs, logs, timeline, artifacts
- defect intake when published behavior differs from docs

Touched areas:

- manual audit evidence outside the source checkout
- `docs/e2e/operator-ui-local-project.md`
- `docs/backlog/`

Dependencies:

- `W28-E1-S1`
- accepted `ai-driven-dev-v2==0.1.0a8` on PyPI

Local tasks:

- `W28-E2-S1-T1` (done) Run a published `ai-driven-dev-v2==0.1.0a8` clean UI onboarding smoke
  from an isolated `uv tool`/`pipx` install.
  - Scope: disposable audit workspace outside the repo.
  - Verification: audit transcript records `aidd 0.1.0a8`, setup-required state,
    project-local work-item creation, explicit `generic-cli` selection, successful
    `idea` and `research` selected-stage jobs, logs, timeline, artifacts, and cleanup.
- `W28-E2-S1-T2` (done) Record any published-package UI defects as next-prerelease tasks without
  rewriting `v0.1.0a8`.
  - Scope: planning documents only.
  - Verification: each recorded defect has exact repro, expected/actual behavior,
    affected UI/API surface, and one reviewable fix task.

Exit evidence:

- the published package onboarding claim is revalidated after release;
- generated `.aidd` state remains outside the source repository;
- any defect found in the immutable release has a next-version fix path.

Sync notes:

- `2026-06-04` `W28-E2-S1` completed with disposable audit root
  `/tmp/aidd-a8-ui-audit-20260604T081222Z`. Isolated `uv tool` install and isolated
  `pipx run` both returned `aidd 0.1.0a8`; release tag clone resolved to
  `1b65dbded7ab55ddc8ef8ef8a823f5674f83c20a`; `aidd ui` served setup mode without
  `--work-item`; `/api/dashboard` blocked before setup; onboarding created
  `WI-A8-UI-SMOKE`; `/api/stage/run` without runtime returned `runtime is required.`;
  explicit `generic-cli` selected-stage runs completed `idea` and `research` in
  `run-20260604T081502Z`; stage rail reported both stages `succeeded`; live and
  persisted logs contained `fixture-runtime stage=idea` and
  `fixture-runtime stage=research`; timeline and Markdown artifact endpoints were
  readable. No published-package UI defect was found, so no next-prerelease defect task
  was added from this audit.

### Epic W28-E3 — source operator control smoke (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-11`

#### Slice W28-E3-S1 — source checkout control-center smoke (`done`)
Goal: verify the next development source keeps the operator-control-center surfaces usable
after onboarding and selected-stage execution.

Primary outputs:

- deterministic source checkout smoke for long-run visibility, implement diff review,
  structured review/QA, remediation, and stale downstream rerun
- focused regression fixes for any source-only defect found

Touched areas:

- `tests/cli/`
- `tests/core/`
- `src/aidd/cli/static/`
- `src/aidd/core/`
- `docs/e2e/operator-ui-local-project.md`

Dependencies:

- `W28-E2-S1`

Local tasks:

- `W28-E3-S1-T1` (done) Run a source checkout UI smoke that exercises Active Run, Timeline,
  Implement Review, Review Findings, QA Verdict, and remediation backflow on a disposable
  fixture project.
  - Scope: local manual/source smoke evidence only.
  - Verification: smoke notes show terminal job cleanup, real timeline milestones,
    source diff separated from `.aidd` artifacts, parsed review/QA summaries, stale
    downstream badges, and explicit rerun of `review -> qa`.
- `W28-E3-S1-T2` (done) Disposition: superseded. Fix the first confirmed source-only operator-control-center defect from
  the W28 smoke.
  - Decision: the W28 source smoke and focused deterministic checks found no source-only
    operator-control-center defect requiring a fix task.

Exit evidence:

- post-a8 source remains compatible with the published operator path;
- remediation and stale downstream behavior are checked through an operator-facing lane.

Sync notes:

- `2026-06-04` `W28-E3-S1` completed with disposable source smoke root
  `/tmp/aidd-a8-source-control-smoke-20260604T082001Z`. Source `aidd 0.1.0a9.dev0`
  served a seeded `WI-UI` command center; dashboard surfaced rejected review findings as
  next action; Implement diff showed tracked `app.py` plus untracked project files while
  keeping `.aidd` artifacts separate; implementation evidence parsed `TASK-1`; review
  findings parsed `RV-1`; QA verdict parsed `not-ready`; remediation request creation
  succeeded and remediation launch without runtime returned `runtime is required.` The
  focused source checks in `tests/cli/test_ui.py` for operator-control endpoints,
  remediation launch, stale downstream marking, QA-risk requests, and downstream rerun
  passed together with `tests/cli/test_ui_assets_contracts.py`. No source-only defect was
  found.

### Epic W28-E4 — next prerelease readiness (`done`)
Linked stories: `US-07`, `US-09`, `US-10`

#### Slice W28-E4-S1 — next alpha readiness checklist (`done`)
Goal: prepare the next prerelease decision with a clean list of verified fixes and open
operator risks.

Primary outputs:

- next-prerelease readiness note
- updated release checklist placeholders for the next candidate
- local deterministic check evidence

Touched areas:

- `docs/release-checklist.md`
- `CHANGELOG.md`
- `README.md`
- `docs/backlog/`

Dependencies:

- `W28-E3-S1`

Local tasks:

- `W28-E4-S1-T1` (done) Write the next-prerelease readiness note summarizing shipped post-a8
  fixes, remaining operator risks, and required release gates.
  - Scope: release-facing docs only.
  - Verification: docs consistency tests pass and the note keeps published release claims
    separate from source development version claims.

Exit evidence:

- maintainers have a bounded go/no-go input for the next prerelease;
- deterministic checks and manual operator evidence remain separate from publish gates.

Sync notes:

- `2026-06-04` `W28-E4-S1` completed: `CHANGELOG.md` records the unreleased
  roadmap/audit/release-ergonomics updates, and `docs/release-checklist.md` now has a
  next-prerelease readiness note for `0.1.0a9.dev0` with post-a8 evidence, remaining
  operator risks, and unchanged release gates. Wave 28 is closed.

---

## Wave 29 — real-provider operator beta hardening (`done`)

Goal: move the shipped UI-first operator path from deterministic local confidence to
real-provider, browser-verified, beta-readiness evidence while preserving CLI
compatibility, explicit runtime selection, project-local `.aidd/` ownership, and release
immutability.

### Epic W29-E1 — real-provider UI E2E evidence (`done`)
Linked stories: `US-01`, `US-06`, `US-07`, `US-11`

#### Slice W29-E1-S1 — provider UI acceptance contract (`done`)
Goal: define the real-provider UI-first E2E lane before running provider-authenticated
smokes.

Primary outputs:

- real-provider UI E2E acceptance matrix
- provider readiness and blocker taxonomy
- evidence capture checklist for authenticated local smokes

Touched areas:

- `docs/e2e/`
- `docs/operator-handbook.md`
- `docs/backlog/`

Dependencies:

- accepted `v0.1.0a8` package evidence
- Wave 28 published-package and source checkout UI smoke evidence

Local tasks:

- `W29-E1-S1-T1` (done) Define the real-provider UI E2E acceptance matrix for `codex`,
  `claude-code`, `opencode`, and optional `qwen` runs through clean UI onboarding.
  - Scope: E2E/operator documentation only.
  - Verification: docs checks and roadmap sync prove the matrix names provider auth
    prerequisites, `aidd ui` setup flow, explicit runtime selection, stage targets,
    expected artifacts, blocker classes, and cleanup rules.
- `W29-E1-S1-T2` (done) Add the provider readiness preflight checklist for UI-first
  smokes.
  - Scope: E2E/operator documentation only.
  - Verification: docs checks prove each maintained provider has binary, auth, command,
    timeout, runtime id, and evidence-location checks before launch.

Exit evidence:

- provider-authenticated UI smokes have a common contract before any runtime-specific
  defect is opened;
- environment blockers and AIDD-owned failures are classified consistently.

#### Slice W29-E1-S2 — provider-authenticated UI smokes (`done`)
Goal: run the UI-first flow against real provider runtimes and record exact evidence or
environment blockers.

Primary outputs:

- Codex UI smoke evidence or blocker note
- Claude Code UI smoke evidence or blocker note
- OpenCode UI smoke evidence or blocker note
- optional Qwen UI smoke evidence or blocker note

Touched areas:

- disposable audit workspaces outside the repository
- `docs/e2e/`
- `docs/backlog/`

Dependencies:

- `W29-E1-S1`
- local provider binaries and authentication where available

Local tasks:

- `W29-E1-S2-T1` (done) Run the Codex clean UI onboarding smoke through at least
  `idea -> research` and record evidence or a provider-auth blocker.
  - Scope: manual live evidence outside the repo.
  - Verification: evidence records install/source channel, UI URL, selected project root,
    selected `codex` runtime, job ids, logs, timeline, artifacts, terminal status, and
    cleanup.
- `W29-E1-S2-T2` (done) Run the Claude Code clean UI onboarding smoke through at
  least `idea -> research` and record evidence or a provider-auth blocker.
  - Scope: manual live evidence outside the repo.
  - Verification: evidence records install/source channel, UI URL, selected project root,
    selected `claude-code` runtime, job ids, logs, timeline, artifacts, terminal status,
    and cleanup.
- `W29-E1-S2-T3` (done) Run the OpenCode clean UI onboarding smoke through at least
  `idea -> research` and record evidence or a provider-auth blocker.
  - Scope: manual live evidence outside the repo.
  - Verification: evidence records install/source channel, UI URL, selected project root,
    selected `opencode` runtime, job ids, logs, timeline, artifacts, terminal status, and
    cleanup.
- `W29-E1-S2-T4` (done) Run the Qwen clean UI onboarding smoke through at least
  `idea -> research` when the experimental runtime is locally authenticated.
  - Scope: manual live evidence outside the repo.
  - Verification: evidence records install/source channel, UI URL, selected project root,
    selected `qwen` runtime, job ids, logs, timeline, artifacts, terminal status, and
    cleanup.
- `W29-E1-S2-T5` (done) Write a provider UI failure triage matrix from the completed
  smokes.
  - Scope: analysis/backlog documentation only.
  - Verification: each finding is classified as AIDD-owned, provider-auth/environment,
    model-output, adapter, documentation, or deferred product scope with exact evidence
    links.

Exit evidence:

- Codex, Claude Code, OpenCode, and optional Qwen authenticated UI-first paths are proven
  through `idea -> research`;
- provider lanes were not replaced by `generic-cli`;
- runtime-specific failures become targeted follow-up tasks instead of vague product
  risk.

Provider triage matrix:

- `codex`: `pass`; source checkout `aidd 0.1.0a9.dev0`; Codex CLI
  `codex-cli 0.133.0` from `/Applications/Codex.app/Contents/Resources/codex`;
  disposable audit root `/tmp/aidd-w29-codex-ui-smoke-20260604T101201Z`; UI
  onboarding created `WI-W29-CODEX-UI-SMOKE`; explicit `runtime=codex` selected;
  `/api/stage/run` without `runtime` returned `runtime is required`; run
  `run-20260604T101327Z` completed selected-stage `idea` and `research`; job ids
  `job-1d6a8ed5746541d895b4146792aea3f3` and
  `job-bd2ecfba5fa841c9a0e7803f5221757e` ended `completed` with exit code `0`;
  stage rail shows `idea` and `research` as `succeeded`; logs, timelines, and artifacts
  are available; `active_jobs=false` after terminal state. Provider emitted repeated
  plugin/skill manifest warnings and one Codex SSE `HTTP 504` warning during `idea`, but
  both stages completed successfully, so this is recorded as provider warning only.
- `claude-code`: `pass`; provider-auth rerun with login-shell PATH found
  `claude 2.1.85 (Claude Code)` at `/Users/griogrii_riabov/.local/bin/claude`;
  disposable audit root `/tmp/aidd-w29-provider-auth-rerun-20260604T113402Z`; UI
  onboarding created `WI-W29-CLAUDE-CODE-UI-SMOKE`; explicit `runtime=claude-code`
  selected; `/api/stage/run` without `runtime` returned `runtime is required`; run
  `run-20260604T113424Z` completed selected-stage `idea` and `research`; job ids
  `job-36edd1ecb6384e939afd6bfa85778b58` and
  `job-82d967f263284353911307797182aba7` ended `completed` with exit code `0`; stage
  rail shows `idea` and `research` as `succeeded`; logs, timelines, and artifacts are
  available.
- `opencode`: `pass`; provider-auth rerun with login-shell PATH found `opencode 1.14.30`
  at `/opt/homebrew/bin/opencode`; disposable audit root
  `/tmp/aidd-w29-provider-auth-rerun-20260604T113402Z`; UI onboarding created
  `WI-W29-OPENCODE-UI-SMOKE`; explicit `runtime=opencode` selected; missing-runtime
  launch returned `runtime is required`; run `run-20260604T113937Z` completed
  selected-stage `idea` and `research`; job ids `job-7c6c0f19d6d346829480d6623bec5113`
  and `job-2f76f77fc1c34ed69f3bb9a3f85f92ae` ended `completed` with exit code `0`;
  stage rail shows `idea` and `research` as `succeeded`; logs, timelines, and artifacts
  are available.
- `qwen`: `pass`; optional experimental provider-auth rerun with login-shell PATH found
  `qwen 0.17.0` at `/opt/homebrew/bin/qwen`; disposable audit root
  `/tmp/aidd-w29-provider-auth-rerun-20260604T113402Z`; UI onboarding created
  `WI-W29-QWEN-UI-SMOKE`; explicit `runtime=qwen` selected; missing-runtime launch
  returned `runtime is required`; run `run-20260604T114308Z` completed selected-stage
  `idea` and `research`; job ids `job-3c3746a152754807972d730234278cac` and
  `job-2566b84ea4804eab9264c47b1222de5b` ended `completed` with exit code `0`; stage
  rail shows `idea` and `research` as `succeeded`; logs, timelines, and artifacts are
  available.

### Epic W29-E2 — browser-verified operator UX (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-11`

#### Slice W29-E2-S1 — browser smoke contract and automation (`done`)
Goal: verify the operator UI in a browser, not only through API and static asset
contracts.

Primary outputs:

- browser smoke checklist for onboarding and command center surfaces
- automated or semi-automated browser smoke lane for disposable local projects
- screenshot and interaction evidence requirements

Touched areas:

- `docs/e2e/operator-ui-local-project.md`
- `tests/cli/`
- `src/aidd/cli/static/`

Dependencies:

- Wave 28 source checkout operator-control smoke

Local tasks:

- `W29-E2-S1-T1` (done) Define the browser-verified operator UI smoke checklist for
  onboarding, runner cards, selected-stage launch, Active Run, Timeline, Implement
  Review, Review Findings, QA Verdict, and remediation.
  - Scope: E2E documentation only.
  - Verification: docs checks prove required viewport, keyboard, screenshot, API snapshot,
    and cleanup fields are named.
- `W29-E2-S1-T2` (done) Add a browser-driven local UI smoke for clean onboarding and
  selected-stage launch against the deterministic fixture.
  - Scope: documented Manual+Browser smoke or static/API contracts; no Playwright or
    Selenium dev dependency.
  - Verification: the smoke creates a disposable project, completes onboarding, selects
    `generic-cli`, launches one selected stage, observes terminal cleanup, and leaves no
    `.aidd/` state in the repo.
- `W29-E2-S1-T3` (done) Capture browser screenshots for the primary operator control
  center states.
  - Scope: manual/browser evidence outside generated source artifacts.
  - Verification: evidence includes onboarding, command center, logs/timeline, artifacts,
    implement diff, review findings, QA verdict, remediation, and stale downstream states.
- `W29-E2-S1-T4` (done) Disposition: superseded. Convert the first repeatable browser UX defect into a targeted
  fix task after evidence exists.
  - Scope: planning documents only.
  - Verification: superseded for this evidence pass because the Manual+Browser smoke found
    no repeatable AIDD-owned UX defect; future browser defects should be added as fresh,
    focused roadmap tasks with repro, expected/actual behavior, and one verification path.

Exit evidence:

- operator UI quality is checked through actual browser interactions;
- visual and interaction regressions are separated from backend/API health.

### Epic W29-E3 — project-set and monorepo UX (`done`)
Linked stories: `US-11`, `US-12`

#### Slice W29-E3-S1 — project-set operator visibility (`done`)
Goal: make declared project-set roots understandable in the UI without mixing unrelated
repositories into one `.aidd` workspace.

Primary outputs:

- project-set UI behavior contract
- per-root artifact and diff grouping read model
- out-of-scope write warnings for operator review

Touched areas:

- `docs/architecture/project-set-workspace.md`
- `docs/architecture/operator-frontend.md`
- `src/aidd/core/`
- `src/aidd/cli/static/`

Dependencies:

- existing project-set resolver and onboarding root validation
- implement diff review service

Local tasks:

- `W29-E3-S1-T1` (done) Define the project-set UI behavior contract for declared
  roots, per-root ownership, and unrelated-project boundaries.
  - Scope: architecture documentation only.
  - Verification: docs checks prove the contract preserves one active project-local
    `.aidd/`, declared related roots, and no unrelated multi-project execution.
- `W29-E3-S1-T2` (done) Expose per-root artifact and source-diff grouping in the
  operator read model.
  - Scope: core read model/API only.
  - Verification: service tests prove changed files and artifacts are grouped by declared
    root and out-of-scope paths are reported without traversal escapes.
- `W29-E3-S1-T3` (done) Render project-set grouping and out-of-scope warnings in the
  operator UI.
  - Scope: packaged static UI assets only.
  - Verification: static UI contract tests prove root labels, grouping, and warning states
    render with escaped dynamic values.
- `W29-E3-S1-T4` (done) Add deterministic project-set UI regression coverage.
  - Scope: CLI/UI tests only.
  - Verification: fixture-backed tests prove duplicate roots, root escapes, per-root
    artifacts, and source diff grouping behave deterministically.

Exit evidence:

- monorepo operators can see which declared root owns each artifact or diff;
- unrelated repositories remain out of scope for one UI session.

### Epic W29-E4 — prompt and workflow accountability (`done`)
Linked stories: `US-07`, `US-10`, `US-11`

#### Slice W29-E4-S1 — run accountability read model (`done`)
Goal: make prompt/workflow inputs visible enough to compare runs and diagnose behavior
drift.

Primary outputs:

- prompt/workflow provenance UI contract
- run input and prompt hash read model
- run-to-run comparison surface for operator/evaluator use

Touched areas:

- `docs/architecture/operator-frontend.md`
- `src/aidd/core/`
- `src/aidd/cli/static/`
- `tests/core/`
- `tests/cli/`

Dependencies:

- existing run manifest provenance fields
- evidence graph read model

Local tasks:

- `W29-E4-S1-T1` (done) Define the prompt/workflow accountability contract for the
  operator UI.
  - Scope: architecture documentation only.
  - Verification: docs checks prove prompt paths, content hashes, Git SHA, config roots,
    runtime id, and stage graph inputs are named as read-only evidence.
- `W29-E4-S1-T2` (done) Expose prompt hash and workflow input provenance in a core
  run-accountability read model.
  - Scope: core read model only.
  - Verification: core tests prove prompt paths, hashes, config, runtime id, and run
    manifest references are returned without mutating artifacts.
- `W29-E4-S1-T3` (done) Render prompt/workflow provenance in the operator UI.
  - Scope: packaged static UI assets only.
  - Verification: static UI contract tests prove provenance cards and missing-evidence
    states render with escaped values.
- `W29-E4-S1-T4` (done) Add a bounded run-to-run comparison view for prompt and artifact
  drift.
  - Scope: core/UI read-only comparison only.
  - Verification: tests prove two runs can be compared by prompt hash, stage status,
    changed artifacts, and validator outcomes without reading outside `.aidd/`.

Exit evidence:

- maintainers can explain which prompt/workflow inputs produced a run;
- eval and operator reviews can detect prompt or configuration drift.

### Epic W29-E5 — runtime safety and approval UX (`done`)
Linked stories: `US-06`, `US-11`

#### Slice W29-E5-S1 — approval and safety control surfaces (`done`)
Goal: make runtime approval, denial, and sensitive-command decisions understandable in
the operator UI.

Primary outputs:

- approval state and policy UX contract
- sensitive command and denied request panels
- durable safety audit trail view

Touched areas:

- `docs/architecture/operator-frontend.md`
- `src/aidd/core/`
- `src/aidd/cli/static/`
- `tests/cli/`

Dependencies:

- existing runtime permission and approval queue surfaces

Local tasks:

- `W29-E5-S1-T1` (done) Define the runtime approval UX contract for pending,
  approved, denied, expired, and policy-blocked requests.
  - Scope: architecture/operator documentation only.
  - Verification: docs checks prove each approval state, operator action, and safety log
    field is named.
- `W29-E5-S1-T2` (done) Render sensitive command and denied request panels in the
  operator UI.
  - Scope: packaged static UI assets only.
  - Verification: static UI contract tests prove command summaries, policy reasons,
    runtime ids, timestamps, and operator actions render safely.
- `W29-E5-S1-T3` (done) Add approval audit trail API coverage for operator UI reads.
  - Scope: private UI API/tests only.
  - Verification: API tests prove approval history is readable, bounded, ordered, and not
    mixed across work items or runs.

Exit evidence:

- operators can understand runtime safety decisions without leaving the UI;
- approval history remains auditable and scoped to the active project/work item.

### Epic W29-E6 — release and install ergonomics v2 (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W29-E6-S1 — maintainer release preflight tooling (`done`)
Goal: reduce manual release friction without changing the GitHub Release published-event
release model.

Primary outputs:

- PATH-safe local release preflight command
- release evidence collector
- updated release checklist for next prerelease gates

Touched areas:

- `docs/release-checklist.md`
- `scripts/`
- `tests/`

Dependencies:

- accepted `v0.1.0a8` release flow
- PATH-safe `gh` documentation from Wave 28

Local tasks:

- `W29-E6-S1-T1` (done) Add a PATH-safe release preflight helper for `uv`, `gh`,
  source version, branch, tag absence, and PyPI version absence checks.
  - Scope: release helper script only.
  - Verification: unit tests or dry-run tests prove missing binaries, mismatched version,
    existing tag, and existing PyPI version produce explicit non-mutating failures.
- `W29-E6-S1-T2` (done) Add a release evidence collector for workflow, PyPI, `pipx`,
  and `uv tool` verification links.
  - Scope: release helper script/docs only.
  - Verification: tests prove evidence fields are bounded, required links are validated,
    and no release tag is created by the helper.
- `W29-E6-S1-T3` (done) Update the next prerelease checklist to use the preflight and
  evidence collector.
  - Scope: release documentation only.
  - Verification: docs checks prove the release flow still requires draft release,
    explicit publish approval, GitHub Release-created tag, PyPI verification, `pipx`, and
    `uv tool` smoke evidence.

Exit evidence:

- maintainers have a repeatable preflight before publishing the next prerelease;
- release helpers cannot bypass the accepted tag/publication model.

### Epic W29-E7 — beta-readiness acceptance matrix (`done`)
Linked stories: `US-01`, `US-07`, `US-09`, `US-10`, `US-11`, `US-12`

#### Slice W29-E7-S1 — beta gate definition (`done`)
Goal: define the product gate for a future beta-oriented release before claiming beta
readiness.

Primary outputs:

- beta acceptance matrix
- explicit non-goals and residual alpha risks
- go/no-go evidence checklist

Touched areas:

- `README.md`
- `docs/product/user-stories.md`
- `docs/architecture/target-architecture.md`
- `docs/release-checklist.md`

Dependencies:

- Wave 29 real-provider and browser evidence begins
- accepted alpha release evidence remains immutable

Local tasks:

- `W29-E7-S1-T1` (done) Define the beta-readiness acceptance matrix for install,
  clean UI onboarding, real provider execution, operator remediation, project-set
  boundaries, docs, security posture, and release evidence.
  - Scope: product/release documentation only.
  - Verification: docs checks prove beta readiness is described as a future gate, not a
    current production claim.
- `W29-E7-S1-T2` (done) Reconcile user stories and target architecture against the
  beta matrix.
  - Scope: product and architecture documentation only.
  - Verification: docs checks prove user story success signals and architecture
    non-goals match the beta gate wording.
- `W29-E7-S1-T3` (done) Prepare beta-oriented release note criteria after provider and
  browser evidence are available.
  - Scope: release documentation only.
  - Verification: the note criteria require fresh evidence links and do not describe an
    unpublished dev version as accepted.

Exit evidence:

- maintainers know exactly what remains before a beta-oriented claim;
- alpha/prerelease language remains honest until the gate is satisfied.

Sync notes:

- `2026-06-04` Wave 29 opened via `W8-E3-S1` queue-restoration policy after Wave 28
  closed with an empty active backlog. The wave groups the next product scopes into one
  large roadmap lane: real-provider UI E2E, browser-verified operator UX, project-set
  UX, prompt/workflow accountability, runtime safety, release ergonomics, and beta
  readiness. Initial queue restoration promotes `W29-E1-S1-T1` to `Next`,
  `W29-E1-S1-T2`, `W29-E2-S1-T1`, and `W29-E7-S1-T1` to `Soon`, with implementation
  and evidence follow-ups kept in `Parking lot` until the acceptance contract is written.
- `2026-06-04` Wave 29 contract/tooling pass completed the real-provider UI acceptance
  contract, browser smoke contract, project-set operator grouping, run accountability
  endpoint/UI cards, approval audit payload/UI rows, release preflight/evidence helpers,
  and beta-readiness matrix docs. Local provider preflight found Codex CLI
  `codex-cli 0.133.0` at `/Applications/Codex.app/Contents/Resources/codex`; Claude
  Code, OpenCode, and Qwen binaries were not present in the non-interactive Codex app
  shell `PATH`, so their smoke tasks were initially treated as `auth/env` blockers
  pending a login-shell preflight. Active queue advances to `W29-E1-S2-T1` for Codex
  smoke evidence and keeps browser/live evidence plus run-to-run comparison/release-note
  criteria as follow-up work.
- `2026-06-04` `W29-E1-S2-T1` and `W29-E1-S2-T5` completed in disposable audit root
  `/tmp/aidd-w29-codex-ui-smoke-20260604T101201Z`: source checkout `aidd 0.1.0a9.dev0`
  launched `aidd ui` clean onboarding, created `WI-W29-CODEX-UI-SMOKE`, explicitly
  selected Codex CLI `codex-cli 0.133.0`, verified `/api/stage/run` rejects missing
  `runtime`, and ran selected stages `idea` and `research` in
  `run-20260604T101327Z` to `succeeded`. The UI/API evidence shows no active jobs after
  terminal state and available logs, timelines, and artifacts. Updated local readiness
  also found OpenCode `1.14.30` and Qwen `0.17.0` binaries, but their auth/provider
  smokes were left pending until explicit authenticated lanes could be run through a
  login shell. Backlog advances to Browser evidence `W29-E2-S1-T2`.
- `2026-06-04` `W29-E2-S1-T2` and `W29-E2-S1-T3` completed through Manual+Browser
  evidence, without adding Playwright or Selenium dependencies. Session A used
  disposable root `/tmp/aidd-w29-browser-ui-smoke-pass-20260604T103044Z`, source
  checkout `aidd 0.1.0a9.dev0`, clean `aidd ui` onboarding, work item
  `WI-W29-BROWSER-SMOKE`, explicit `generic-cli`, and selected-stage launches for
  `idea` and `research` in `run-20260604T103202Z`; both jobs reached API status
  `completed`, stage status `succeeded`, terminal active-run cleanup, logs, timeline,
  and artifacts. Session B used seeded disposable root
  `/tmp/aidd-w29-browser-seeded-20260604T103356Z`, work item `WI-BROWSER-B`, and
  run `run-browser-b` to capture browser/API evidence for Implement Review, Review
  Findings, QA Verdict, remediation requests/status, stale downstream badges, blockers,
  and runtime readiness. No repeatable AIDD-owned browser UX defect was found, so
  `W29-E2-S1-T4` is superseded for this pass. Active queue advances to
  `W29-E4-S1-T4`; beta release-note criteria moves to `Soon` after comparison work.
- `2026-06-04` `W29-E4-S1-T4` completed a read-only run comparison surface:
  `GET /api/run/comparison?baseline_run_id=...&target_run_id=...` compares two run ids
  from the active work item by prompt hashes, stage statuses, bounded artifact hashes,
  and validator outcomes, returning warnings for missing legacy provenance or unsafe
  artifact paths instead of reading outside `.aidd/`. The Run History UI now renders a
  comparison panel with lineage-derived default baseline selection and manual baseline
  input. Active queue advances to beta-oriented release note criteria `W29-E7-S1-T3`.
- `2026-06-04` `W29-E7-S1-T3` completed beta-oriented release note criteria in
  `docs/release-checklist.md`: candidate notes must cite fresh provider, Browser,
  install, remediation, project-set, provenance/run-comparison, approval audit, security,
  and package-channel evidence before making any beta-oriented claim. The checklist also
  preserves the rule that `0.1.0a9.dev0` is a development line, not an accepted release.
  Wave 29 is closed with Codex provider evidence, Manual+Browser evidence, run
  comparison, and release-note criteria done. The active backlog queue is empty.
- `2026-06-04` Provider-auth rerun resolved the remaining W29 provider lanes after using
  a login-shell PATH instead of the narrower non-interactive Codex app shell PATH. The
  disposable audit root `/tmp/aidd-w29-provider-auth-rerun-20260604T113402Z` used source
  checkout `aidd 0.1.0a9.dev0`; preflight found `claude 2.1.85 (Claude Code)`,
  `opencode 1.14.30`, and `qwen 0.17.0`; and clean UI onboarding plus explicit runtime
  selection ran selected stages `idea` and `research` successfully for `claude-code`,
  `opencode`, and optional `qwen`. Each lane verified missing-runtime rejection, job API
  status `completed`, stage rail status `succeeded`, and available logs, timelines, and
  artifacts. W29 provider matrix is now all-pass for `codex`, `claude-code`, `opencode`,
  and optional `qwen`; future smokes should use a login shell or explicit PATH prefix
  when provider binaries live outside the Codex app's default non-interactive PATH.

---

## Wave 30 — security posture and `v0.1.0a9` release readiness (`done`)

Goal: close current default-branch dependency security alerts, then prepare an honest
go/no-go input for the next alpha prerelease without changing CLI/UI behavior or starting
publication before explicit approval.

### Epic W30-E1 — Dependabot security posture (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W30-E1-S1 — dependency alert triage and lock remediation (`done`)
Goal: inspect the open Dependabot alerts, classify reachable surface, and remediate
straightforward locked dependency updates before release candidate preparation.

Primary outputs:

- default-branch Dependabot alert triage table
- patched lockfile for simple dependency fixes
- security posture note for release readiness

Touched areas:

- `uv.lock`
- `docs/release-checklist.md`
- `docs/backlog/`

Dependencies:

- merged Wave 29 provider/browser evidence on `main`
- GitHub Dependabot alert read access through `gh`

Local tasks:

- `W30-E1-S1-T1` (done) Triage the four default-branch Dependabot alerts and fix
  simple lockfile remediations.
  - Scope: dependency lock plus release/backlog documentation only.
  - Verification: alert table names package, severity, dependency type, reachable
    surface, affected version, fixed version, action, and local deterministic gates pass.

Exit evidence:

- release readiness has no untriaged Dependabot alert from the current default branch;
- any remaining dependency risk is explicit rather than hidden.

### Epic W30-E2 — next alpha release readiness (`done`)
Linked stories: `US-01`, `US-07`, `US-09`, `US-10`, `US-11`

#### Slice W30-E2-S1 — `v0.1.0a9` source readiness evidence (`done`)
Goal: collect a fresh source-checkout operator smoke and summarize whether `main` is
ready for a release-candidate branch.

Primary outputs:

- fresh clean UI onboarding source smoke evidence
- README/release wording audit for unpublished `0.1.0a9.dev0`
- go/no-go summary for release candidate preparation

Touched areas:

- disposable `/tmp` smoke workspace
- `README.md`
- `docs/release-checklist.md`
- `docs/backlog/`

Dependencies:

- `W30-E1-S1`

Local tasks:

- `W30-E2-S1-T1` (done) Run a fresh source smoke from `main` through clean `aidd ui`
  onboarding, explicit runner selection, and selected-stage `idea -> research`.
  - Scope: manual deterministic source evidence outside the repository.
  - Verification: evidence records project root, work item, runtime id, run id, job ids,
    missing-runtime rejection, stage statuses, logs, timeline, artifacts, and cleanup.
- `W30-E2-S1-T2` (done) Write the `v0.1.0a9` release-readiness go/no-go summary.
  - Scope: release-facing documentation only.
  - Verification: docs keep `0.1.0a9.dev0` as development source, list security/test/UI
    smoke/provider evidence, and require explicit approval before release prep/publish.

Exit evidence:

- maintainers have a current release-candidate decision input;
- README and release docs do not imply that `0.1.0a9` is already published.

### Epic W30-E3 — approved release preparation (`done`)
Linked stories: `US-09`, `US-10`

#### Slice W30-E3-S1 — `v0.1.0a9` release branch and dry-runs (`done`)
Goal: reconcile the old approved-release-preparation blocker after accepted release
evidence made a new `v0.1.0a9` preparation invalid.

Primary outputs:

- accepted `v0.1.0a9` release/install evidence reference
- stale release-prep blocker closure decision
- synchronized roadmap/backlog status

Touched areas:

- `docs/backlog/`

Dependencies:

- completed `W30-E1-S1`
- completed `W30-E2-S1`
- accepted `v0.1.0a9` release/install evidence in `docs/release-checklist.md`
- later accepted `0.1.0a13` package evidence

Local tasks:

- `W30-E3-S1-T1` (done) Disposition: superseded by accepted release evidence. Close the stale
  `v0.1.0a9` release-prep blocker without creating a new release branch, tag, draft
  release, or PyPI publish.
  - Scope: planning documentation only.
  - Verification: `docs/release-checklist.md` records accepted `v0.1.0a9` evidence,
    origin has tag `v0.1.0a9`, latest accepted evidence is `0.1.0a14`, and the active
    backlog no longer parks the stale W30 task.

Exit evidence:

- the old release-prep blocker is closed because the immutable package version already
  exists and has accepted release/install evidence;
- no tag is pushed manually and no package is published from this reconciliation pass.

Sync notes:

- `2026-06-04` Wave 30 opened after PR #72 merged Wave 29 and local `main` was clean at
  `20e52df`. Initial queue restoration promoted `W30-E1-S1-T1` for Dependabot security
  triage, kept `W30-E2-S1-T1` and `W30-E2-S1-T2` behind security triage, and parked
  `W30-E3-S1-T1` behind a separate explicit release-prep approval.
- `2026-06-04` `W30-E1-S1-T1` completed: GitHub Dependabot reported four open alerts on
  default branch, all in `uv.lock` transitive docs-extra dependencies through
  `mkdocs-material`/`requests`, not AIDD runtime core or provider adapters. The lockfile
  was updated from `idna 3.13` to `3.18`, `pymdown-extensions 10.21.2` to `10.21.3`,
  and `urllib3 2.6.3` to `2.7.0`, covering the reported patched versions. The alerts are
  expected to close after this lock update reaches default branch and Dependabot
  re-evaluates the dependency graph.
- `2026-06-04` `W30-E2-S1-T1` and `W30-E2-S1-T2` completed with fresh source evidence in
  disposable audit root `/tmp/aidd-w30-release-readiness-smoke-20260604T121108Z`.
  Source checkout `aidd 0.1.0a9.dev0` started clean `aidd ui`, `GET /api/onboarding/state`
  returned `setup_required=true`, `GET /api/dashboard` before setup returned
  `Complete project setup before using this UI action.`, onboarding created
  `WI-W30-RELEASE-READINESS-SMOKE`, explicit `generic-cli` was selected, missing-runtime
  selected-stage launch returned `runtime is required.`, and run `run-20260604T121116Z`
  completed `idea` and `research` jobs `job-add2c133fdee4cff90c4232a20911b8c` and
  `job-52f8e71e3a564672becae1084bf27d71` with job status `completed`, stage rail status
  `succeeded`, fixture runtime logs, seven timeline events per stage, and expected
  Markdown artifacts. At that time, release prep stayed blocked on separate explicit
  approval.
- `2026-07-02` `W30-E3-S1-T1` closed by reconciliation rather than a new release action:
  `docs/release-checklist.md` records accepted `v0.1.0a9` release/install evidence, origin
  has tag `v0.1.0a9`, the release branch `release/v0.1.0a9` was already used for the
  accepted release, current source is `0.1.0a15.dev0`, and latest accepted package evidence
  is `0.1.0a14`. Re-preparing `v0.1.0a9` would conflict with immutable package-version
  rules, so no release branch, tag, draft GitHub Release, PyPI publish, or workflow publish
  trigger was created.

---

## Wave 31 — integrated operator workbench redesign (`done`)

Goal: redesign the local operator UI around the integrated workbench reference so project
selection, work-item navigation, run execution, Markdown artifacts, logs, diagnostics, and
recovery actions form one coherent operator path without changing core workflow semantics
or adapter boundaries.

### Epic W31-E1 — workbench UX contract and rollout plan (`done`)
Linked stories: `US-02`, `US-03`, `US-05`, `US-06`, `US-11`, `US-12`

#### Slice W31-E1-S1 — integrated workbench contract (`done`)
Goal: turn the saved workbench reference into implementation-ready UX rules before code
changes.

Primary outputs:

- operator workbench information architecture
- contextual navigation and state hierarchy rules
- browser validation checklist updates

Touched areas:

- `docs/architecture/operator-frontend.md`
- `docs/e2e/operator-ui-local-project.md`
- `docs/backlog/`

Dependencies:

- `docs/architecture/assets/operator-ui-mission-control/13-integrated-operator-workbench.png`
- completed Wave 29 browser evidence

Local tasks:

- `W31-E1-S1-T1` (done) Define the integrated operator workbench information architecture from
  `13-integrated-operator-workbench.png`.
  - Scope: architecture documentation only.
  - Verification: docs name the required hierarchy: project/work-item context, one
    run-global next action, document workbench, timeline/log diagnostics, and guided
    recovery cards.
- `W31-E1-S1-T2` (done) Update the local-project UI checklist for the redesigned workbench
  surfaces.
  - Scope: E2E documentation only.
  - Verification: checklist covers Project Home, Work Item Console, Document Workbench,
    Run Diagnostics, Recovery Assistant, contextual tabs, and compact viewport ordering.

Exit evidence:

- future UI implementation can be reviewed against one integrated UX contract;
- browser evidence expectations match the new workbench direction.

### Epic W31-E2 — project and work-item operating layer (`done`)
Linked stories: `US-11`, `US-12`

#### Slice W31-E2-S1 — project home read model (`done`)
Goal: expose a project/work-item home surface that lets operators select local projects
and resume work before entering stage internals.

Primary outputs:

- project home read model
- work-item status summary rows
- private UI endpoint coverage

Touched areas:

- `src/aidd/core/`
- `src/aidd/cli/ui.py`
- `tests/core/`
- `tests/cli/`

Dependencies:

- `W31-E1-S1`
- existing onboarding and run lookup services

Local tasks:

- `W31-E2-S1-T1` (done) Expose a project home read model for selected project root, `.aidd`
  root, discovered work items, latest run, stage progress, blockers, and terminal state.
  - Scope: core read model only.
  - Verification: core tests cover empty project, multiple work items, blocked run,
    completed run, and stale/missing run metadata.
- `W31-E2-S1-T2` (done) Add private UI endpoints for project home and work-item resume context.
  - Scope: CLI UI API only.
  - Verification: CLI tests prove endpoint payload shape, project scoping, missing
    workspace behavior, and no cross-project state mixing.

Exit evidence:

- the UI can open on project/work-item context instead of immediately entering a stage
  cockpit;
- project-set metadata remains visible without mixing unrelated repositories.

#### Slice W31-E2-S2 — project home UI shell (`done`)
Goal: render project and work-item navigation as the first operator layer.

Primary outputs:

- Project Home / Work Item Board shell
- structured project-set root editor
- resume/create work-item controls

Touched areas:

- `src/aidd/cli/static/`
- `tests/cli/test_ui_assets_contracts.py`

Dependencies:

- `W31-E2-S1`

Local tasks:

- `W31-E2-S2-T1` (done) Render the Project Home and Work Item Board shell from the project home
  endpoint.
  - Scope: packaged static UI assets only.
  - Verification: static UI tests prove work-item cards, status groups, latest run chips,
    resume actions, and empty states render with escaped dynamic values.
- `W31-E2-S2-T2` (done) Replace raw project-set JSON onboarding with a structured project-root
  editor.
  - Scope: packaged static UI assets only.
  - Verification: static UI tests prove add/remove root rows, id/root/role fields,
    validation status, duplicate-root warnings, and payload compatibility.

Exit evidence:

- operators can start from projects and work items before inspecting stage artifacts;
- monorepo roots are edited through UI controls rather than raw JSON.

### Epic W31-E3 — active run command center (`done`)
Linked stories: `US-03`, `US-06`, `US-11`

#### Slice W31-E3-S1 — run-global next action clarity (`done`)
Goal: make the next safe operator action the dominant control in every active-run state.

Primary outputs:

- fixed first-run next-action copy
- primary Next Action strip
- compact viewport action ordering

Touched areas:

- `src/aidd/cli/static/`
- `tests/cli/test_ui_assets_contracts.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W31-E1-S1`
- existing dashboard `next_action` payload

Local tasks:

- `W31-E3-S1-T1` (done) Fix first-run Next Action copy when a runtime is already selected and
  ready.
  - Scope: packaged static UI assets only.
  - Verification: static/UI tests prove selected-ready runtime shows runnable copy rather
    than `Choose a runtime before starting the workflow`.
- `W31-E3-S1-T2` (done) Render a primary run-global Next Action strip above the selected-stage
  workbench.
  - Scope: packaged static UI assets only.
  - Verification: static tests prove the strip renders one primary action, demotes
    duplicate run buttons, and preserves disabled/runtime-required states.
- `W31-E3-S1-T3` (done) Reorder the compact viewport so Next Action appears before logs,
  artifacts, and secondary evidence.
  - Scope: packaged static UI CSS/assets only.
  - Verification: static responsive tests and manual browser checklist prove primary
    action ordering on mobile/tablet widths.

Exit evidence:

- the operator can always identify the next safe action before reading logs or artifacts;
- active-run controls no longer contradict runtime readiness state.

### Epic W31-E4 — document and artifact workbench (`done`)
Linked stories: `US-02`, `US-03`, `US-10`, `US-11`

#### Slice W31-E4-S1 — artifact taxonomy read model (`done`)
Goal: make generated documents, runtime inputs, validation evidence, logs, project
evidence, and lineage distinguishable without path guessing.

Primary outputs:

- artifact category vocabulary
- latest/stale/canonical/attempt-local flags
- workbench-oriented artifact read model

Touched areas:

- `src/aidd/core/operator_frontend_artifacts.py`
- `src/aidd/core/operator_frontend_documents.py`
- `tests/core/`

Dependencies:

- `W31-E1-S1`
- existing artifact indexes and evidence graph read model

Local tasks:

- `W31-E4-S1-T1` (done) Define artifact categories for canonical stage documents, runtime
  inputs, validation evidence, runtime evidence, project evidence, and lineage evidence.
  - Scope: core artifact read model only.
  - Verification: core tests prove category, stage, attempt, canonical/latest, stale, and
    source/generated flags for representative artifacts.
- `W31-E4-S1-T2` (done) Expose workbench document metadata for preview/source/diff selection
  without arbitrary path reads.
  - Scope: core document workbench read model only.
  - Verification: core tests cover known document keys, missing documents, large
    truncation, invalid UTF-8, and previous-attempt diff candidates.

Exit evidence:

- UI consumers can organize artifacts by role rather than by raw path shape;
- document-first contracts remain Markdown files and do not become UI-authored schemas.

#### Slice W31-E4-S2 — central document workbench UI (`done`)
Goal: make Markdown artifacts the central work surface for active stage review.

Primary outputs:

- document tree grouped by artifact category
- Preview / Source / Diff mode controls
- contract and validation side inspector

Touched areas:

- `src/aidd/cli/static/`
- `tests/cli/test_ui_assets_contracts.py`

Dependencies:

- `W31-E4-S1`

Local tasks:

- `W31-E4-S2-T1` (done) Render the central Document Workbench with category tree and selected
  Markdown preview/source/diff.
  - Scope: packaged static UI assets only.
  - Verification: static tests prove category groups, selected document state, preview
    and source controls, diff mode, truncation notices, and empty states.
- `W31-E4-S2-T2` (done) Render document contract and validation context beside the selected
  artifact.
  - Scope: packaged static UI assets only.
  - Verification: static tests prove required document status, validator counts,
    missing evidence warnings, references, and version history render safely.

Exit evidence:

- operators can inspect source artifacts without leaving the active workbench;
- raw logs and evidence remain available as drill-down surfaces.

### Epic W31-E5 — diagnostics, logs, and recovery assistant (`done`)
Linked stories: `US-03`, `US-04`, `US-05`, `US-06`, `US-11`

#### Slice W31-E5-S1 — first failure and recovery read models (`done`)
Goal: surface the first decisive failure or blocking signal before raw log inspection.

Primary outputs:

- first-failure read model
- runtime/config failure blockers
- recovery action recommendations

Touched areas:

- `src/aidd/core/operator_frontend_dashboard.py`
- `src/aidd/core/operator_timeline.py`
- `tests/core/`

Dependencies:

- `W31-E1-S1`
- existing stage metadata, runtime exit metadata, validator reports, and question state

Local tasks:

- `W31-E5-S1-T1` (done) Expose the first decisive failure signal from runtime exit metadata,
  validator reports, blocking questions, repair exhaustion, and stopped events.
  - Scope: core dashboard/timeline read models only.
  - Verification: core tests cover runtime non-zero exit, timeout/provider error,
    validation failure, blocking questions, repair exhausted, and explicit stop.
- `W31-E5-S1-T2` (done) Convert runtime and configuration failures into visible blockers and
  recovery-oriented next actions.
  - Scope: core dashboard next-action/blocker read model only.
  - Verification: core tests prove failed runtime attempts do not show `Blockers 0` while
    asking the operator to inspect blockers.

Exit evidence:

- operators can diagnose failed runs from a summary before opening raw logs;
- validation and runtime failures route to repair or explicit stop, never silent
  continuation.

#### Slice W31-E5-S2 — diagnostics and recovery UI (`done`)
Goal: render logs, timeline, questions, repair, and intervention as guided recovery
surfaces instead of always-visible dense tabs.

Primary outputs:

- Run Diagnostics panel
- Summary / Timeline / Raw Logs layout
- Recovery Assistant cards

Touched areas:

- `src/aidd/cli/static/`
- `tests/cli/test_ui_assets_contracts.py`
- `tests/cli/test_ui.py`

Dependencies:

- `W31-E5-S1`

Local tasks:

- `W31-E5-S2-T1` (done) Render the Run Diagnostics panel with pipeline, attempts, repairs,
  question markers, and first-failure summary.
  - Scope: packaged static UI assets only.
  - Verification: static tests prove timeline nodes, attempt markers, repair markers,
    question markers, first-failure callout, and empty states render safely.
- `W31-E5-S2-T2` (done) Split logs into Summary, Timeline, and Raw Runtime Log views.
  - Scope: packaged static UI assets only.
  - Verification: static/UI tests prove raw stdout/stderr/system filters, truncation
    notices, saved-log fallback, and summary/timeline navigation.
- `W31-E5-S2-T3` (done) Render Recovery Assistant cards for questions, validation failures,
  repair, request change, and remediation.
  - Scope: packaged static UI assets only.
  - Verification: static/UI tests prove answer, rerun, request change, repair, and
    remediation actions stay gated by runtime and stage eligibility.

Exit evidence:

- recovery paths are visible as guided actions rather than hidden in separate tabs;
- raw runtime logs remain one click away and preserve native evidence.

### Epic W31-E6 — contextual navigation and verification (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-11`

#### Slice W31-E6-S1 — contextual navigation and regression coverage (`done`)
Goal: reduce always-visible UI clutter while preserving access to artifacts, logs,
questions, validation, and review/QA surfaces.

Primary outputs:

- contextual tab visibility rules
- static/service regressions for workbench hierarchy
- updated manual browser evidence path

Touched areas:

- `src/aidd/cli/static/`
- `tests/cli/`
- `docs/e2e/operator-ui-local-project.md`

Dependencies:

- `W31-E3-S1`
- `W31-E4-S2`
- `W31-E5-S2`

Local tasks:

- `W31-E6-S1-T1` (done) Render contextual navigation rules for stage-specific tabs and
  secondary evidence surfaces.
  - Scope: packaged static UI assets only.
  - Verification: static tests prove implement/review/QA tabs appear only when relevant
    while Documents, Logs, Timeline, and Recovery remain reachable.
- `W31-E6-S1-T2` (done) Add service and static regression coverage for the integrated workbench
  hierarchy.
  - Scope: UI tests only.
  - Verification: tests prove Project Home, Next Action strip, Document Workbench,
    Run Diagnostics, Recovery Assistant, and Evidence/Logs drill-down render from seeded
    workspaces.
- `W31-E6-S1-T3` (done) Record a deterministic browser smoke for the redesigned workbench.
  - Scope: manual browser evidence outside the repository plus checklist note.
  - Verification: evidence records clean onboarding, project/work-item selection,
    selected-stage run, document workbench, diagnostics, recovery, raw logs, compact
    viewport ordering, and cleanup.

Exit evidence:

- the redesigned workbench is proven through static, service, and browser evidence;
- reduced navigation clutter does not hide required logs, artifacts, validation, or
  questions.

Sync notes:

- `2026-06-09` Wave 31 was opened from the integrated UI concept review. The wave uses
  `13-integrated-operator-workbench.png` as the visual reference and decomposes the
  redesign into contract, project/work-item layer, active-run next action, document
  workbench, diagnostics/recovery, and contextual navigation evidence tasks. Initial
  queue promotion sets `W31-E1-S1-T1` as `Next`, keeps the checklist and first read-model
  tasks in `Soon`, and parks the broader UI rollout until the contract lands.
- `2026-06-09` Wave 31 was completed as one integrated local implementation pass:
  Project Home, work-item resume APIs, run-global Next Action, artifact taxonomy,
  Document Workbench, first-failure/recovery read models, Diagnostics/Recovery UI,
  contextual tabs, and responsive ordering are covered by core/API/static regressions.
  Verification passed with the focused operator/docs suite (`174 passed`), the full
  suite (`1159 passed`), and an in-app browser smoke recorded outside the repository at
  `/tmp/aidd-w31-smoke-CZ2xso/w31-smoke-evidence.txt`.
- `2026-06-10` Wave 31 UI audit found two Artifacts-tab UX issues and fixed them:
  Stage Document Workbench now renders before evidence graph/table, and the default
  selected document uses preferred artifact priority instead of alphabetic order. Fresh
  evidence was recorded outside the repository at
  `/tmp/aidd-w31-audit-X1WAMg/w31-ui-audit-evidence.txt`.

---

## Wave 32 — installed CLI log visibility (`done`)

Goal: close the public CLI raw-log rendering defect found by the exact-PyPI
`AIDD-LIVE-011` run without changing runtime adapter behavior.

### Epic W32-E1 — raw runtime log CLI safety (`done`)
Linked stories: `US-06`, `US-07`, `US-09`

#### Slice W32-E1-S1 — persisted run log rendering (`done`)
Goal: make saved runtime logs printable through `aidd run logs` even when raw log text
contains Rich-markup-like bracket sequences.

Primary outputs:

- safe literal output for `aidd run logs`
- regression coverage for bracketed path-like runtime log text
- post-fix live rerun evidence for `AIDD-LIVE-011`

Touched areas:

- `src/aidd/cli/run.py`
- `tests/cli/test_run_logs.py`
- `docs/backlog/`

Dependencies:

- exact-PyPI `AIDD-LIVE-011` failure evidence:
  `eval-live-011-opencode-20260622T130824Z`
- existing `opencode` live provider readiness

Local tasks:

- `W32-E1-S1-T1` (done) Fix `aidd run logs` so persisted raw runtime logs are printed
  literally when they contain Rich-markup-like bracket text.
  - Scope: CLI log rendering only.
  - Verification: focused CLI regression passes and `AIDD-LIVE-011` source-checkout
    live rerun gets past the `research` public log-inspection boundary.

Exit evidence:

- `aidd run logs` no longer crashes on raw log content like
  `[/, /a, /a/b, /a/b/c.py]`;
- live evidence distinguishes fixed source-checkout proof from the immutable
  failed `0.1.0a11` exact-PyPI package proof.

Sync notes:

- `2026-06-22` Completed `W32-E1-S1-T1`: `src/aidd/cli/run.py` now renders raw
  persisted runtime logs with Rich markup/highlighting disabled, focused CLI/harness
  checks passed, and source/local-wheel live rerun
  `eval-live-011-opencode-20260622T133433Z` passed all stages including the prior
  `research` public log-inspection boundary. Exact PyPI proof is deferred until a
  fixed prerelease can be published because `ai-driven-dev-v2==0.1.0a11` is
  immutable.

## Wave 33 — live E2E product-evaluation follow-up (`done`)

Goal: turn the new black-box product-evaluation protocol into a repeatable maintained
matrix practice without making live E2E a CI/CD or release gate.

### Epic W33-E1 — maintained matrix evidence closure (`done`)
Linked stories: `US-07`, `US-10`

#### Slice W33-E1-S1 — canonical maintained matrix evidence (`done`)
Goal: publish one current maintained-matrix evidence table that separates clean lanes,
not-counted lanes, provider blockers, and follow-up defects.

Primary outputs:

- maintained live E2E matrix evidence table
- PR or issue comment with lane outcomes and bundle ids
- missing-lane follow-up list

Touched areas:

- `.aidd/reports/evals/` local evidence only
- PR or issue comments
- `docs/e2e/` only if the maintained matrix definition changes

Dependencies:

- PR #93 live protocol branch merged or rebased onto its intended base
- canonical runtime auth for `codex` and `opencode`

Local tasks:

- `W33-E1-S1-T1` (done) Build a maintained-matrix evidence table from the latest local and PR
  bundle evidence, marking each lane `counted-clean`, `not-counted`, `blocked-provider`,
  `blocked-product-defect`, or `missing`.
  - Scope: evidence review and reporting only.
  - Verification: every maintained matrix lane has a row with scenario id, runtime, run
    id or blocker, execution verdict, manual decision, and final report paths.
- `W33-E1-S1-T2` (done) Run the missing or stale maintained lanes from a clean tracked checkout
  and publish updated evidence without substituting runtimes.
  - Scope: manual live execution only.
  - Verification: each newly run product-evaluation lane has per-stage-run audits,
    final `flow-quality-report.md`, `code-quality-report.md`, `quality-report.md`,
    and a terminal execution verdict or explicit blocker.

Exit evidence:

- maintainers can tell whether the current maintained matrix is clean, partially clean,
  or blocked without reading individual bundles first;
- live evidence remains manual-only and outside CI/CD/release automation.

### Epic W33-E2 — operator evidence ergonomics (`done`)
Linked stories: `US-07`, `US-11`

#### Slice W33-E2-S1 — product-evaluation bundle summary (`done`)
Goal: reduce manual counted-clean review load by generating a read-only summary of
stage-run audits, remediation cycles, untracked product files, and final report presence.

Primary outputs:

- read-only product-evaluation bundle summary artifact
- deterministic fixture coverage for summary generation

Touched areas:

- `src/aidd/harness/`
- `tests/harness/`
- `docs/e2e/`

Dependencies:

- Wave 33 canonical matrix evidence table identifies the most useful summary fields

Local tasks:

- `W33-E2-S1-T1` (done) Add a read-only product-evaluation bundle summary that lists stage-run
  audit decisions, remediation source ids, untracked product files, final report
  presence, and terminal flow-state freshness.
  - Scope: harness reporting only.
  - Verification: fixture-based harness test proves the summary preserves manual-only
    quality semantics and does not change execution verdicts.
- `W33-E2-S1-T2` (done) Document how operators use the bundle summary while still reading
  stage evidence before assigning counted-clean.
  - Scope: live E2E docs and skill guidance only.
  - Verification: docs consistency test proves the summary is described as evidence
    navigation, not runner-owned quality scoring.

Exit evidence:

- product-evaluation bundles are faster to audit without weakening the black-box manual
  quality model;
- runner still does not parse or score subjective product quality.

Sync notes:

- `2026-06-30` Completed `W33-E1-S1-T1` with local evidence report
  `.aidd/reports/evals/maintained-matrix-20260630.md`: all six canonical maintained
  lanes have terminal `pass`, final manual reports, complete stage-quality audit
  coverage, and no unresolved unexpected product residue.
- `2026-06-30` Closed `W33-E1-S1-T2` without launching new live runs because the
  maintained matrix has no missing or stale canonical lane.
- `2026-06-30` Completed `W33-E2-S1-T1` and `W33-E2-S1-T2`: terminal
  product-evaluation bundles now get read-only `product-evaluation-bundle-summary.*`
  navigation artifacts, and live E2E docs/skill guidance state that the summary is
  not runner-owned quality scoring and does not replace manual `quality-report.md`.

### Epic W33-E3 — product-evaluation matrix expansion (`done`)
Linked stories: `US-07`, `US-10`

#### Slice W33-E3-S1 — new repository setup audits (`done`)
Goal: decide which additional public repositories are safe candidates for future
product-evaluation lanes before adding maintained scenarios.

Primary outputs:

- setup-audit notes for Pydantic, FastAPI, Rich, and Ruff candidates
- candidate decision table
- candidate-only Rich product-evaluation draft manifest

Touched areas:

- local setup-audit notes
- `docs/e2e/` candidate documentation
- `harness/scenarios/live/`

Dependencies:

- current maintained matrix evidence is understood well enough to avoid expanding a
  broken protocol

Local tasks:

- `W33-E3-S1-T1` (done) Run non-mutating setup audits for Pydantic, FastAPI, Rich, and Ruff
  candidates, recording clone pin, setup command, focused baseline verification, hidden
  prompts, and blocker status.
  - Scope: setup audit evidence only.
  - Verification: each candidate has a decision row of `candidate`, `blocked`, or
    `reject`, with exact revision and baseline command outcome.
- `W33-E3-S1-T2` (done) Draft one next product-evaluation scenario from the best passing setup
  audit without adding it to the maintained matrix yet.
  - Scope: scenario draft only.
  - Verification: scenario loader doctor passes for the draft and docs mark it as
    candidate, not maintained coverage.

Exit evidence:

- matrix expansion is based on setup proof rather than speculative repo popularity;
- maintained coverage is not expanded until the candidate protocol is proven usable.

Sync notes:

- `2026-07-02` Completed `W33-E3-S1-T1`: disposable setup audits for Pydantic,
  FastAPI, Rich, and Ruff were recorded in
  `docs/e2e/live-e2e-candidate-setup-audits.md` with exact pins, setup commands,
  focused baseline outcomes, candidate task ideas, and decision rows.
- `2026-07-02` Completed `W33-E3-S1-T2`: `AIDD-LIVE-013` was drafted as a
  candidate-only Rich product-evaluation manifest for literal bracketed markup
  rendering. The catalog marks it as a candidate draft, not maintained coverage;
  `docs/e2e/scenario-matrix.md` was intentionally not expanded.

---

## Wave 34 — codebase audit remediation (`done`)

Goal: remediate the confirmed correctness, reliability, compatibility, testability,
maintainability, and defensive-boundary findings in
`docs/analysis/codebase-audit-2026-07-10.md` without changing the eight-stage workflow,
weakening document-first validation, or using provider-authenticated live E2E as an
implementation gate.

Delivery order:

1. restore validation trust and transactional publication;
2. serialize local mutations and bound runtime lifecycle/evidence;
3. make deterministic automation and release checks executable;
4. reduce the measured hotspots and remove confirmed dead surfaces;
5. apply defensive hardening that remains relevant for local CLI, adapter, harness,
   workspace, and persisted-evidence paths.

Scope decision:

- `SEC-01`, `SEC-03`, and `SEC-04` remain in scope as defensive hardening because
  their invariants govern local CLI, adapter, harness, workspace, and persisted-evidence
  paths, not only the browser frontend.
- `SEC-02` is not an implementation target in this wave. The supported frontend remains
  a private, single-operator local UI with a loopback default, a visible warning for
  non-loopback binds, and explicit opt-in for remote approval writes.
- Reopen `SEC-02` before non-loopback operation becomes a supported or recommended
  deployment mode, before the UI is shared across users or hosts, or before an external
  service embeds the mutation API.

Non-goals:

- frontend authentication, session tokens, Origin/CSRF/Host enforcement, or remote
  multi-user deployment;
- provider-authenticated live E2E, penetration testing, or performance certification;
- promotion of audit hypotheses or raw static-analysis signals into accepted work;
- public API, CLI, contract, or persisted-schema changes during planning. Any
  implementation-time compatibility change must be explicit in its local task.

### Epic W34-E1 — validation and contract trust (`planned`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-10`, `US-12`

#### Slice W34-E1-S1 — canonical stage-result gate (`done`)
Goal: prevent an invalid common stage checkpoint from being normalized, published, or
used for downstream progression.

Dependencies:

- none

Local tasks:

- `W34-E1-S1-T1` (done) Add canonical `stage-result.md` semantic rules and a final
  post-normalization publication invariant. [`BUG-01`]
  - Scope: common-document validation and the final stage publication gate.
  - Verification: an eight-stage matrix rejects wrong stage, missing declared output,
    incoherent status/history, blocker mismatch, and skipped next stage.

Exit evidence:

- no stage can publish success when its canonical result contradicts stage identity,
  outputs, attempt history, blockers, or next-stage order.

#### Slice W34-E1-S2 — stage-specific cross-document evidence (`planned`)
Goal: bind authored stage claims to the primary and upstream evidence that gives those
claims meaning.

Dependencies:

- `W34-E1-S1-T1`
- `W35-E1-S1`
- `W35-E1-S2`
- `W35-E2-S7`

Local tasks:

- `W34-E1-S2-T1` (done) Add a typed evidence context and bind implementation output to the
  selected task, changed paths, allowed scope, and authored checks. [`ARCH-01`]
  - Scope: implement-stage cross-document rules.
  - Verification: wrong-task, missing-path, out-of-scope, and skipped-authored-check
    fixtures fail with stable findings.
- `W34-E1-S2-T2` (done) Bind rich task-card outcomes, acceptance IDs, dependency
  obligations, and authored verification to plan milestones, dependencies, and
  verification notes. [`ARCH-01`]
  - Scope: tasklist cross-document rules.
  - Verification: missing and mismatched plan obligations fail without reimplementing
    task-plan parsing or changing valid rich-tasklist behavior.
- `W34-E1-S2-T3` (done) Bind non-task review findings, changed paths, and artifact/evidence
  references to implementation artifacts. [`ARCH-01`]
  - Dependencies: `W34-E1-S2-T2`.
  - Scope: review cross-document rules.
  - Verification: nonexistent finding, evidence, and changed-path references fail while
    exact task/acceptance coverage remains owned by `W35-E2-S7`.
- `W34-E1-S2-T4` (done) Bind non-task QA risks, checks, and verdict relationships to review and
  implementation evidence. [`ARCH-01`]
  - Scope: QA cross-document rules.
  - Verification: unsupported risk, check, and cross-stage verdict relationships fail
    without duplicating the exact task/acceptance gate from `W35-E2-S7`.

Exit evidence:

- tasklist, implement, review, and QA outputs cannot pass by satisfying local shape
  while contradicting their authored context.

#### Slice W34-E1-S3 — validator report protocol and examples (`done`)
Goal: make renderer, contract, prompts, consumers, and examples use one versioned
validator vocabulary.

Dependencies:

- `W34-E1-S1-T1`

Local tasks:

- `W34-E1-S3-T1` (done) Define the canonical versioned validator field/code registry.
  [`COMPAT-01`]
  - Scope: validator-report protocol registry only.
  - Verification: every normative field/code and retained legacy alias has one
    registry entry and schema test.
- `W34-E1-S3-T2` (done) Normalize all eight success examples and exact invalid/repair
  expectations against the canonical protocol. [`COMPAT-02`]
  - Dependencies: `W34-E1-S3-T3`, `W34-E1-S3-T4`, `W34-E1-S3-T5`,
    `W34-E1-S3-T6`, `W34-E1-S3-T7`.
  - Scope: contract examples and full-stack validator fixtures.
  - Verification: every success example passes, while invalid and repair examples emit
    their exact expected codes.
- `W34-E1-S3-T3` (done) Make the validator report renderer emit registry-owned vocabulary.
  [`COMPAT-01`]
  - Dependencies: `W34-E1-S3-T1`.
  - Scope: validator report rendering only.
  - Verification: renderer output is exhausted by the registry-driven protocol matrix.
- `W34-E1-S3-T4` (done) Align the validator-report Markdown contract with the registry.
  [`COMPAT-01`]
  - Dependencies: `W34-E1-S3-T1`.
  - Scope: durable validator-report contract only.
  - Verification: contract examples and registry fields/codes agree exactly.
- `W34-E1-S3-T5` (done) Align validation repair prompts with the registry vocabulary.
  [`COMPAT-01`]
  - Dependencies: `W34-E1-S3-T1`.
  - Scope: validator repair prompt packs only.
  - Verification: prompt-quality checks reject unknown fields/codes and retain declared
    legacy aliases only.
- `W34-E1-S3-T6` (done) Adopt the registry in dual-read validator-report consumers.
  [`COMPAT-01`]
  - Dependencies: `W34-E1-S3-T1`.
  - Scope: validator-report readers only.
  - Verification: canonical and declared legacy fixtures read equivalently while
    undeclared aliases fail.
- `W34-E1-S3-T7` (done) Render the prompt-facing validator-report skeleton from the canonical
  registry.
  - Dependencies: `W34-E1-S3-T1`, `W34-E1-S3-T4`.
  - Scope: common stage-brief validator skeleton only.
  - Verification: prepared stage briefs use exactly the canonical registered fields and
    do not preserve a second handwritten validator-report vocabulary.

Exit evidence:

- examples teach the behavior production validators enforce;
- legacy validator-report consumers have a documented dual-read window.

#### Slice W34-E1-S4 — item- and section-scoped semantic rules (`done`)
Goal: close parser false passes and false failures caused by whole-document or
whole-section matching.

Dependencies:

- `W34-E1-S2`

Local tasks:

- `W34-E1-S4-T1` (done) Reuse the canonical section-aware interview parser in
  cross-validation. [`BUG-02`]
  - Scope: interview cross-document rule.
  - Verification: question-shaped prose outside the authoritative Questions section is
    ignored while real unanswered questions still block.
- `W34-E1-S4-T2` (done) Validate mitigation and owner metadata inside each QA risk item.
  [`BUG-03`]
  - Scope: QA semantic rule.
  - Verification: a neighboring-risk isolation test reports the exact untreated risk.
- `W34-E1-S4-T3` (done) Preserve independent mixed-ID and missing-coverage findings through
  the canonical Wave 35 task-plan parser. [`BUG-04`]
  - Scope: tasklist semantic regression coverage only.
  - Verification: a mixed-style tasklist with missing dependency/verification coverage
    emits both stable findings without introducing a second task grammar.
- `W34-E1-S4-T4` (done) Require command- or artifact-shaped executable evidence instead of
  prose tool names. [`BUG-05`]
  - Scope: implementation evidence grammar.
  - Verification: a table covers accepted commands/artifacts and rejected prose-only
    claims.

Exit evidence:

- evidence is evaluated inside its authoritative item/section rather than borrowed from
  unrelated prose.

#### Slice W34-E1-S5 — validator change isolation (`done`)
Goal: reduce contract synchronization cost after correctness behavior is characterized.

Dependencies:

- `W34-E1-S2`
- `W34-E1-S3`
- `W34-E1-S4`

Local tasks:

- `W34-E1-S5-T1` (done) Add one production-equivalent full-stack contract fixture runner.
  [`REF-04`]
  - Scope: validator test infrastructure.
  - Verification: every stage example uses the same runner and production registry.
- `W34-E1-S5-T2` (done) Split cross-document rules by invariant and stage behind the current
  public facade. [`REF-04`]
  - Scope: validator implementation modules.
  - Verification: the public finding protocol and focused stage matrices remain
    unchanged.
- `W34-E1-S5-T3` (done) Partition the monolithic semantic test module by stage and shared
  invariant. [`REF-04`]
  - Scope: validator tests only.
  - Verification: the same regression cases are collected with no duplicate fixture
    ownership.
- `W34-E1-S5-T4` (done) Remove unreachable validator scaffolds and unused constants after a
  public-import compatibility check. [`DEAD-02`]
  - Scope: validator dead surface only.
  - Verification: the pre-Wave-35 tasklist semantic pipeline and other unreachable
    surfaces are absent; import inventory and the complete validator suite pass.
- `W34-E1-S5-T5` (done) Remove the unused packaged `common/run-rules.md` fragment without
  changing active prompt composition. [`DEAD-02`]
  - Scope: packaged prompt resources.
  - Verification: wheel inventory passes and active prompt hashes remain unchanged.

Exit evidence:

- contract changes have one full-stack test path and stage-local ownership;
- confirmed unreachable validator and prompt-pack surface is absent.

### Epic W34-E2 — transactional state and immutable evidence (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-10`, `US-11`

#### Slice W34-E2-S1 — atomic stage publication (`done`)
Goal: make durable success observable only after canonical output publication commits.

Dependencies:

- `W34-E1-S1-T1` for the final semantic gate

Local tasks:

- `W34-E2-S1-T1` (done) Publish outputs through staged-directory verification and atomic
  replace. [`REL-02`]
  - Scope: stage output publisher.
  - Verification: injected create, copy, verify, and replace failures expose neither a
    partial mirror nor a committed destination.
- `W34-E2-S1-T2` (done) Persist `succeeded` only after reconciliation and publication commit.
  [`REL-02`]
  - Scope: stage runner success transition.
  - Verification: every injected publication failure leaves a truthful non-success
    state.
- `W34-E2-S1-T3` (done) Terminalize raised adapter exceptions with failed state and diagnostic
  evidence. [`REL-07`]
  - Scope: stage runner exception boundary.
  - Verification: an injected adapter exception proves `executing -> failed` and
    preserves owned document restoration.

Exit evidence:

- a succeeded stage always has complete canonical outputs;
- a raised adapter failure never leaves a durable executing stage.

#### Slice W34-E2-S2 — canonical run identity and continuation (`done`)
Goal: make resume, latest-run selection, and manifest reuse agree on one authoritative
run identity.

Dependencies:

- none for `T1` and `T2`
- `W34-E2-S2-T3` depends on `T1` and `T2`

Local tasks:

- `W34-E2-S2-T1` (done) Validate immutable runtime, target, and configuration fields when an
  existing run manifest is reused. [`COMPAT-03`]
  - Scope: run manifest creation/reuse.
  - Verification: identical resume succeeds and every immutable-field mismatch is
    rejected explicitly.
- `W34-E2-S2-T2` (done) Use one latest-run resolver with sub-second identity and a shared tie
  policy. [`BUG-07`]
  - Scope: run lookup, inspection, and resume resolution.
  - Verification: two same-second manifests resolve identically through every public
    consumer.
- `W34-E2-S2-T3` (done) Add explicit `--run-id` workflow continuation for non-first
  `--from-stage` starts. [`BUG-06`]
  - Scope: CLI workflow selection and core continuation service.
  - Verification: every non-first starting stage continues the requested run and
    validates its upstream prerequisites.

Exit evidence:

- the CLI can resume any valid non-first stage without allocating a contradictory run;
- every consumer chooses the same latest run.

#### Slice W34-E2-S3 — immutable completed-run overlays and accountability (`done`)
Goal: preserve completed-run bytes while exposing truthful operator state and all prompts
actually used.

Dependencies:

- `W34-E2-S2-T1`

Local tasks:

- `W34-E2-S3-T1` (done) Move archive decisions to a separate append-only operator
  overlay/index. [`ARCH-03`]
  - Scope: archive write/read model.
  - Verification: source manifest bytes and hash are identical before and after archive.
- `W34-E2-S3-T2` (done) Aggregate immutable per-attempt prompt provenance across executed
  stages. [`ARCH-02`]
  - Scope: run accountability read model.
  - Verification: an idea-to-QA fixture exposes every executed prompt set and attempt
    mode.

Exit evidence:

- completed-run source evidence is immutable;
- full-flow accountability lists prompts actually used at every executed stage.

### Epic W34-E3 — local operator concurrency and bounded UI state (`done`)
Linked stories: `US-03`, `US-06`, `US-10`, `US-11`

#### Slice W34-E3-S1 — serialized run mutation (`done`)
Goal: admit only one conflicting mutation for a run while allocating durable identities
atomically across CLI and UI processes.

Dependencies:

- none

Local tasks:

- `W34-E3-S1-T1` (done) Add a filesystem-backed run-mutation lease and atomic run/attempt
  allocation. [`REL-01`, `REF-02`]
  - Scope: core run store and identity allocation.
  - Verification: concurrent CLI/UI allocation yields unique IDs and one mutation owner.
- `W34-E3-S1-T2` (done) Route stage, workflow, and remediation UI mutations through keyed
  admission with deterministic conflict responses. [`REL-01`, `REF-02`]
  - Scope: UI application service.
  - Verification: overlapping same-run requests admit one job and reject the others
    without creating attempts.

Exit evidence:

- same-run mutations cannot race metadata, attempts, or publication;
- non-conflicting runs remain independently executable.

#### Slice W34-E3-S2 — terminal-safe operator decisions (`done`)
Goal: keep runtime decisions immutable and make cancellation terminate all waiters.

Dependencies:

- `W34-E3-S1-T1`

Local tasks:

- `W34-E3-S2-T1` (done) Resolve each approval exactly once with compare-and-set semantics.
  [`REL-09`, `REF-02`]
  - Scope: approval decision service.
  - Verification: concurrent opposite decisions yield one durable winner shared by the
    runtime and audit ledger.
- `W34-E3-S2-T2` (done) Wake decision waiters on cancellation and reject decisions for
  terminal jobs. [`REL-08`, `REF-02`]
  - Scope: job/approval lifecycle.
  - Verification: the waiter exits within a bound and no post-cancel continuation is
    possible.

Exit evidence:

- runtime behavior and durable approval history cannot disagree;
- cancelled jobs retain no live decision-wait thread.

#### Slice W34-E3-S3 — bounded local UI retention (`done`)
Goal: keep a long-lived local server within explicit memory and response budgets.

Dependencies:

- `W34-E3-S1-T2`

Local tasks:

- `W34-E3-S3-T1` (done) Store live chunks in a byte-bounded ring, cap responses, and evict
  terminal jobs by TTL/count. [`PERF-01`]
  - Scope: UI job registry.
  - Verification: a high-volume stress fixture stays within fixed memory and response
    budgets while durable logs remain available.

Exit evidence:

- local UI memory no longer grows without bound with job count or log volume.

#### Slice W34-E3-S4 — UI service change isolation (`done`)
Goal: separate routing, job/approval state, dashboard reduction, and next-flow rendering
after their corrected behavior is characterized.

Dependencies:

- `W34-E3-S1`
- `W34-E3-S2`
- `W34-E3-S3`
- executable frontend tests from `W34-E5-S3`

Local tasks:

- `W34-E3-S4-T1` (done) Add characterization fixtures for corrected routes, jobs, approvals,
  and dashboard states. [`REF-02`]
  - Scope: UI tests.
  - Verification: API/state snapshots cover mutation conflicts, decisions,
    cancellation, retention, and terminal views.
- `W34-E3-S4-T2` (done) Extract thin HTTP route handlers from `cli/ui.py`. [`REF-02`]
  - Scope: UI routing only.
  - Verification: endpoint contract fixtures remain unchanged.
- `W34-E3-S4-T3` (done) Extract pure dashboard reducers and evidence collectors. [`REF-02`]
  - Scope: core dashboard read model.
  - Verification: deterministic state-to-view fixtures remain equivalent.
- `W34-E3-S4-T4` (done) Split the next-flow browser hotspot into controller and view modules.
  [`REF-02`]
  - Scope: packaged JavaScript.
  - Verification: DOM-state and packaged-asset tests preserve behavior and module
    loading.

Exit evidence:

- UI routing, mutation ownership, read-model reduction, and browser next-flow behavior
  can change independently.

### Epic W34-E4 — bounded adapter lifecycle and truthful runtime evidence (`done`)
Linked stories: `US-01`, `US-06`, `US-08`, `US-10`

#### Slice W34-E4-S1 — bounded process supervision (`done`)
Goal: make every transport start supervision before blocking I/O and own its complete
process lifecycle.

Dependencies:

- none for characterization and timeout validation
- integration tasks depend on the shared supervisor task

Local tasks:

- `W34-E4-S1-T1` (done) Add provider-free adapter lifecycle characterization fixtures.
  [`REF-03`]
  - Scope: cross-adapter tests only.
  - Verification: a startup, bidirectional-I/O, timeout, cancellation, parent-exit, and
    descendant-exit matrix runs without provider authentication.
- `W34-E4-S1-T2` (done) Reject non-finite runtime budgets at configuration and execution
  boundaries. [`BUG-08`]
  - Scope: timeout contract.
  - Verification: parameterized tests cover non-finite values, booleans, zero,
    negatives, and valid finite values.
- `W34-E4-S1-T3` (done) Start readers, deadline, and cancellation supervision before managed
  stdin delivery. [`REL-03`]
  - Scope: shared streaming and Qwen prompt startup.
  - Verification: a large bidirectional fake runtime terminates under both timeout and
    explicit cancellation.
- `W34-E4-S1-T4` (done) Add a shared owned-process-group supervisor with bounded drain and
  termination. [`REF-03`]
  - Scope: adapter lifecycle primitive.
  - Verification: a disposable parent/child process-tree test proves bounded group
    shutdown.
- `W34-E4-S1-T5` (done) Adopt the owned-process supervisor in shared streamed execution.
  [`REL-05`, `REL-10`]
  - Dependencies: `W34-E4-S1-T4`.
  - Scope: shared streamed transport lifecycle only.
  - Verification: descendants exit after timeout, cancellation, parent exit, and
    inherited-pipe drain expiry.
- `W34-E4-S1-T6` (done) Propagate cancellation through Codex live startup, active turn, and
  approval wait. [`REL-04`]
  - Scope: Codex live transport.
  - Verification: three-state cancellation tests persist a cancelled outcome.
- `W34-E4-S1-T7` (done) Propagate cancellation through Qwen live startup, active turn, and
  approval wait. [`REL-04`]
  - Scope: Qwen live transport.
  - Verification: three-state cancellation tests persist a cancelled outcome.
- `W34-E4-S1-T8` (done) Preserve incomplete trailing Qwen JSONL frames until a complete record
  arrives. [`REL-06`]
  - Scope: Qwen event reader.
  - Verification: a representative event is split at every byte boundary; malformed
    complete lines and duplicate IDs remain deterministic.
- `W34-E4-S1-T9` (done) Adopt the owned-process supervisor in Codex-live execution.
  [`REL-05`, `REL-10`]
  - Dependencies: `W34-E4-S1-T4`, `W34-E4-S1-T5`.
  - Scope: Codex-live lifecycle integration only.
  - Verification: Codex descendants exit after timeout, denial, cancellation, parent
    exit, and bounded drain expiry.
- `W34-E4-S1-T10` (done) Adopt the owned-process supervisor in Qwen-live execution.
  [`REL-05`, `REL-10`]
  - Dependencies: `W34-E4-S1-T4`, `W34-E4-S1-T5`.
  - Scope: Qwen-live lifecycle integration only.
  - Verification: Qwen descendants exit after timeout, denial, cancellation, parent
    exit, and bounded drain expiry.

Exit evidence:

- configured timeout and cancellation cover prompt delivery, active execution, approval
  waits, pipe drain, and descendant shutdown.

#### Slice W34-E4-S2 — runtime outcome and evidence truth (`done`)
Goal: make every blocked, failed, cancelled, or early-stopped runtime attempt leave one
normalized and comparable evidence envelope.

Dependencies:

- `W34-E4-S1`

Local tasks:

- `W34-E4-S2-T1` (done) Define typed stop reasons and one runtime-evidence commit contract.
  [`REF-03`]
  - Scope: shared adapter result model.
  - Verification: a cross-adapter outcome table covers success, failure, timeout,
    cancellation, denial, blocked, and launch failure.
- `W34-E4-S2-T2` (done) Persist truthful Codex early-stop and blocked outcomes through the
  shared contract. [`BUG-09`, `REL-11`]
  - Scope: Codex live path.
  - Verification: denial, startup-timeout, and blocked branches agree between outer
    status, raw log, and `runtime-exit.json`.
- `W34-E4-S2-T3` (done) Persist canonical Qwen blocked outcomes through the shared contract.
  [`REL-11`]
  - Scope: Qwen live path.
  - Verification: a blocked attempt retains stdout/stderr, raw log, and blocked exit
    evidence.
- `W34-E4-S2-T4` (done) Normalize executable-launch failures for every registered runtime.
  [`REL-12`]
  - Scope: adapter surface.
  - Verification: a missing-executable conformance matrix produces equivalent durable
    evidence for every maintained runtime.
- `W34-E4-S2-T5` (done) Add a disk-backed runtime-log sink with bounded in-memory tails and
  counters. [`PERF-02`]
  - Scope: shared runtime capture layer.
  - Verification: a high-volume fake runtime preserves the complete disk log within a
    fixed resident-memory budget.

Exit evidence:

- runtime status, raw logs, and exit metadata agree for every terminal and blocked path;
- verbose runtimes cannot force unbounded in-memory capture.

#### Slice W34-E4-S3 — adapter context and capability compatibility (`done`)
Goal: make advertised capabilities and configured execution context match what each
adapter actually runs.

Dependencies:

- `W34-E4-S1-T1`
- `W34-E4-S2-T1`

Local tasks:

- `W34-E4-S3-T1` (done) Propagate Qwen intervention mode and operator-request metadata.
  [`COMPAT-04`]
  - Scope: Qwen context, environment, and native prompt assembly.
  - Verification: native and adapter-flags intervention fixtures preserve both fields.
- `W34-E4-S3-T2` (done) Align Claude capability reporting with executable registered
  transports. [`COMPAT-05`]
  - Scope: Claude probe and adapter surface.
  - Verification: probe-to-execution conformance covers every claimed live path.
- `W34-E4-S3-T3` (done) Preserve supported Codex live arguments and reject unsupported options
  explicitly. [`COMPAT-06`]
  - Scope: Codex live command/thread mapping.
  - Verification: one supported option is preserved and one unsupported option is
    rejected before launch.

Exit evidence:

- permission mode does not silently drop configured behavior;
- doctor/capability output never promises an unimplemented execution path.

### Epic W34-E5 — executable automation, durable bundles, and release checks (`done`)
Linked stories: `US-07`, `US-09`, `US-10`, `US-11`

#### Slice W34-E5-S1 — deterministic CI scenario lane (`done`)
Goal: turn `automation_lane: ci` into an executable local-only contract without adding
provider-live work to CI/CD.

Dependencies:

- the P1 validation gate in `W34-E1-S1` before the lane becomes required

Local tasks:

- `W34-E5-S1-T1` (done) Repair stale CI-labelled smoke manifests and fixtures. [`BUG-11`]
  - Scope: deterministic scenarios and local fixtures.
  - Verification: each manifest passes from a freshly materialized fixture.
- `W34-E5-S1-T2` (done) Expose a deterministic local-only `aidd eval execute` entry point
  over the existing pipeline without restoring the removed legacy live-run command.
  [`TEST-01`, `DEAD-01`]
  - Scope: CLI and harness entry point.
  - Verification: one smoke covers prepare, execute, verify, teardown, and bundle
    persistence while rejecting live/provider-auth manifests.
- `W34-E5-S1-T3` (done) Execute every discovered CI-lane manifest in CI. [`TEST-01`]
  - Scope: CI workflow integration.
  - Verification: discovered manifest IDs equal executed manifest IDs exactly.

Exit evidence:

- every CI-labelled scenario is executable and actually executed;
- the deterministic pipeline has a supported product entry point.

#### Slice W34-E5-S2 — bounded harness lifecycle and immutable bundles (`done`)
Goal: bound the complete deterministic lifecycle and freeze completed evidence by value.

Dependencies:

- `W34-E5-S1-T1`

Local tasks:

- `W34-E5-S2-T1` (done) Apply one lifecycle budget and owned process groups to setup, run,
  verify, and teardown. [`REL-13`, `REF-01`]
  - Scope: deterministic harness runner.
  - Verification: timeout and descendant-exit tests cover every phase.
- `W34-E5-S2-T2` (done) Materialize result bundles by copy, hash, and atomic replace instead
  of hard links. [`REL-14`]
  - Scope: result bundle writer.
  - Verification: later source mutation cannot alter the destination and injected copy
    failure leaves no partial bundle.
- `W34-E5-S2-T3` (done) Make the running-stage frontend checkpoint transition-aware.
  [`TEST-03`, `REF-01`]
  - Scope: black-box checkpoint probe.
  - Verification: a barrier test completes the stage during probing and routes to the
    normal post-stage checkpoint without a false failure.

Exit evidence:

- setup, run, verify, and teardown share one bounded lifecycle;
- completed bundles and checkpoint decisions remain stable under source mutation and
  concurrent stage transitions.

#### Slice W34-E5-S3 — classification, release, and packaged-UI gates (`done`)
Goal: make automated classifications and release/package evidence reject ambiguous or
non-executable claims.

Dependencies:

- none for classifier and release tasks
- JavaScript DOM tests build on the syntax gate

Local tasks:

- `W34-E5-S3-T1` (done) Replace divergent eval classifiers with one typed earliest-failure
  classifier. [`BUG-10`]
  - Scope: eval log analysis.
  - Verification: structured/text fixture tables cover assertions, HTTP errors, missing
    executables/files, DNS, and timeout, and both public APIs agree.
- `W34-E5-S3-T2` (done) Bound release preflight subprocess and network failures. [`REL-15`]
  - Scope: release preflight script.
  - Verification: timeout, transport, TLS/DNS, registry, and server failures still emit
    valid structured blocker output.
- `W34-E5-S3-T3` (done) Validate release evidence by exact host, path, semantic version, and
  exit status. [`BUG-12`]
  - Scope: release evidence collector.
  - Verification: unrelated hosts, prefix versions, and error-bearing transcripts fail.
- `W34-E5-S3-T4` (done) Run `node --check` for every packaged JavaScript asset in CI.
  [`TEST-02`]
  - Scope: package and CI syntax gate.
  - Verification: asset discovery is exhaustive and an intentional syntax error fails.
- `W34-E5-S3-T5` (done) Add lightweight DOM-state tests for module ordering, stale responses,
  cancellation, and error rendering. [`TEST-02`]
  - Scope: packaged frontend behavior tests.
  - Verification: out-of-order and rejected mocked responses exercise deterministic
    state recovery.
- `W34-E5-S3-T6` (done) Make the built-wheel resource smoke offline-deterministic and bounded.
  [`TEST-05`]
  - Scope: package resource smoke test only.
  - Verification: `UV_OFFLINE=1` package-resource tests pass using the built wheel and
    every subprocess has an explicit timeout.
- `W34-E5-S3-T7` (done) Include release scripts in the strict mypy gate and fix their typed
  boundary returns. [`TEST-06`]
  - Scope: release-script typing plus configured mypy commands.
  - Verification: `python -m mypy src scripts` passes through local, CI, and release
    commands.

Exit evidence:

- failure taxonomy, release evidence, and packaged browser behavior have executable
  negative-path gates.

#### Slice W34-E5-S4 — live orchestration change isolation (`done`)
Goal: split the measured 8.6k-line live orchestration hotspot behind characterized typed
boundaries after lifecycle and classification behavior is corrected.

Dependencies:

- `W34-E5-S4-T5` has no prerequisite
- decomposition tasks `W34-E5-S4-T1..T4` depend on `W34-E5-S2` and
  `W34-E5-S3-T1`

Local tasks:

- `W34-E5-S4-T1` (done) Extract durable flow-state and resume coordination from live
  orchestration. [`REF-01`]
  - Scope: harness flow-state service.
  - Verification: deterministic resume and idempotency suites preserve bundle behavior.
- `W34-E5-S4-T2` (done) Consolidate process/checkpoint coordination and
  `BlackBoxCommandResult` behind the existing steps module. [`REF-01`, `REF-05`]
  - Scope: live process, result-model, and checkpoint services.
  - Verification: facade and orchestration expose one result type, duplicate process
    helpers are absent, and lifecycle/monkeypatch fixtures preserve decisions.
- `W34-E5-S4-T3` (done) Extract pure quality-policy evaluation from orchestration.
  [`REF-01`]
  - Scope: quality policy only.
  - Verification: existing fixture verdicts remain equivalent.
- `W34-E5-S4-T4` (done) Make the existing reports module authoritative for atomic report,
  transcript, and bundle rendering. [`REF-01`, `REF-05`]
  - Scope: live report writers only.
  - Verification: duplicate orchestration helpers are absent and golden JSON/Markdown
    bundles remain byte-stable.
- `W34-E5-S4-T5` (done) Replace the fake runtime's unconditional stage delay with an opt-in
  transition barrier for checkpoint tests. [`TEST-04`]
  - Scope: live black-box test fixture only.
  - Verification: the same flow cases pass without fixed sleep outside explicit
    running-stage/checkpoint scenarios.

Exit evidence:

- process lifecycle, durable flow state, checkpoints, quality policy, and report writing
  can evolve independently;
- extracted report/step modules have production consumers and ordinary provider-free
  flows no longer pay a real-time checkpoint delay.

### Epic W34-E6 — remaining confirmed dead surfaces (`done`)
Linked stories: `US-01`, `US-08`, `US-09`, `US-10`

#### Slice W34-E6-S1 — compatibility-checked removal (`done`)
Goal: remove production and dependency surface that has no supported runtime,
compatibility, registry, or resource entry point.

Dependencies:

- `W34-E6-S1-T4` and `W34-E6-S1-T5` have no prerequisite
- compatibility-code and runtime-dependency removal follows the adjacent
  correctness/reliability slices in `W34-E1` and `W34-E4`

Local tasks:

- `W34-E6-S1-T1` (done) Remove superseded Claude question/resume code and
  implementation-only tests after a public-import compatibility review. [`DEAD-03`]
  - Scope: Claude adapter legacy surface.
  - Verification: registered adapter integration tests cover the retained shared path.
- `W34-E6-S1-T6` (done) Remove dead adapter-local prompt-read shims after confirming
  `aidd.adapters.native_prompt` as the canonical owner. [`DEAD-03`]
  - Scope: Claude, Codex, and OpenCode runner prompt helpers only.
  - Verification: native prompt fixtures remain equivalent and an architecture test
    excludes adapter-local prompt readers.
- `W34-E6-S1-T2` (done) Remove the unreferenced core interview capability helper after a
  public-import check. [`DEAD-04`]
  - Scope: core interview surface.
  - Verification: import inventory and the interview suite pass.
- `W34-E6-S1-T3` (done) Remove the three unused direct runtime dependencies and regenerate the
  lock. [`DEAD-05`]
  - Scope: project dependencies and lock only.
  - Verification: locked sync, wheel build/install, and package/validator tests pass.
- `W34-E6-S1-T4` (done) Remove the obsolete raw repository inventory `manifest.txt`.
  [`DEAD-06`]
  - Scope: generated root inventory only.
  - Verification: tracked files contain no cache, bytecode, or removed-file inventory;
    the explicitly historical `MANIFEST.md` remains available.
- `W34-E6-S1-T5` (done) Remove the dormant MkDocs documentation extra and its lock/config
  surface. [`DEAD-07`]
  - Scope: project optional dependencies, lock, and Dependabot grouping only.
  - Verification: locked sync, wheel build, and documentation consistency pass without
    a MkDocs dependency subtree.

Exit evidence:

- every removed symbol/resource/dependency has a recorded compatibility exclusion and
  retained integration coverage.

#### Slice W34-E6-S2 — dependency maintenance queue reconciliation (`done`)
Goal: retire obsolete update proposals and refresh only dependency surfaces still owned
by the repository after dead packages are removed.

Dependencies:

- `W34-E6-S1-T3`
- `W34-E6-S1-T5`

Local tasks:

- `W34-E6-S2-T1` (done) Close or supersede dependency update proposals that target removed
  packages. [`DEAD-05`, `DEAD-07`]
  - Scope: obsolete dependency-update pull requests only.
  - Verification: no open update proposal references a dependency absent from the
    canonical project configuration.
- `W34-E6-S2-T2` (done) Rebase and apply compatible updates for retained Python runtime and
  development dependencies. [`MAINT-01`]
  - Scope: retained Python dependency declarations and lock only.
  - Verification: locked sync, lint, strict typing, full tests, and wheel smoke pass.
- `W34-E6-S2-T3` (done) Rebase and apply compatible pinned GitHub Actions updates.
  [`MAINT-01`]
  - Scope: maintained workflow action pins only.
  - Verification: workflow validation and all required GitHub checks pass.

Exit evidence:

- the automated dependency queue contains only maintained surfaces and its compatible
  updates have current verification evidence.

### Epic W34-E7 — defensive local trust boundaries (`done`)
Linked stories: `US-01`, `US-03`, `US-07`, `US-08`, `US-10`, `US-12`

#### Slice W34-E7-S1 — typed runtime operator policy (`done`)
Goal: replace permissive lexical decisions with explicit local capability policy.

Dependencies:

- none for the typed policy model
- enforcement follows characterization of current runtime operator decisions

Local tasks:

- `W34-E7-S1-T1` (done) Define typed capability rules for runtime operator requests.
  [`SEC-01`]
  - Scope: runtime operator policy model.
  - Verification: a defensive decision table covers known capabilities, unknown
    requests, and policy-blocked operations without executing provider-live commands.
- `W34-E7-S1-T2` (done) Apply protected-data and core-evidence boundaries consistently to
  reads, writes, and destructive operations, and fail closed when no verifiable
  boundary exists. [`SEC-01`]
  - Dependencies: `W34-E7-S1-T1`.
  - Scope: runtime operator policy enforcement.
  - Verification: disposable local fixtures prove protected evidence is never
    auto-approved and ordinary bounded project operations retain intended behavior.

Exit evidence:

- broadly capable or unknown operations cannot receive permissive approval from lexical
  inference alone.

#### Slice W34-E7-S2 — shared identifier containment (`done`)
Goal: make every user-controlled identifier resolve to one contained component before
the first write.

Dependencies:

- reuse existing project-root containment primitives where they satisfy the new shared
  identifier contract

Local tasks:

- `W34-E7-S2-T1` (done) Add shared typed identifier validation and resolve-and-contain
  primitives. [`SEC-03`]
  - Scope: common identifier/path boundary.
  - Verification: defensive fixtures cover valid components, invalid components, root
    escape, and unsafe ancestor resolution without recording sensitive paths.
- `W34-E7-S2-T2` (done) Adopt the shared boundary for workspace and work-item paths.
  [`SEC-03`]
  - Scope: core workspace/work-item persisted paths only.
  - Verification: every workspace/work-item write-path family passes the shared
    containment matrix.
- `W34-E7-S2-T3` (done) Adopt the shared boundary for scenario, eval-run, and result-bundle
  paths. [`SEC-03`]
  - Scope: harness and eval persisted paths.
  - Verification: every harness/bundle write-path family passes the same containment
    matrix.
- `W34-E7-S2-T4` (done) Adopt the shared boundary for run and attempt paths. [`SEC-03`]
  - Dependencies: `W34-E7-S2-T2`.
  - Scope: core run/attempt persisted paths only.
  - Verification: every run/attempt write-path family passes the shared containment
    matrix.
- `W34-E7-S2-T5` (done) Adopt the shared boundary for operator-overlay and CLI-created paths.
  [`SEC-03`]
  - Dependencies: `W34-E7-S2-T2`, `W34-E7-S2-T4`.
  - Scope: operator overlay and CLI persisted paths only.
  - Verification: every overlay/CLI write-path family passes the shared containment
    matrix.

Exit evidence:

- core and harness identifiers share one fail-closed containment contract.

#### Slice W34-E7-S3 — fail-closed safety configuration (`done`)
Goal: reject ambiguous or unknown safety-sensitive configuration before runtime
execution.

Dependencies:

- `W34-E4-S1-T2` for the shared runtime budget contract

Local tasks:

- `W34-E7-S3-T1` (done) Distinguish missing from blank values, validate known safety keys, and
  reject unknown or malformed safety fields. [`SEC-04`]
  - Scope: configuration loading and validation.
  - Verification: a defensive config matrix covers absent defaults, blank values,
    unknown keys, malformed safety fields, and valid explicit settings.

Exit evidence:

- malformed safety configuration cannot silently fall back to permissive behavior.

#### Slice W34-E7-S4 — canonical allowed-write-scope boundary (`done`)
Goal: make validation, task execution, and Implement Review resolve one authoritative
scope document with identical path-prefix semantics.

Dependencies:

- `W34-E7-S2-T1`

Local tasks:

- `W34-E7-S4-T1` (done) Add a typed canonical `AllowedWriteScope` parser, resolver,
  and safe prefix predicate. [`BUG-13`, `ARCH-06`]
  - Scope: core allowed-write-scope model only.
  - Verification: a parity table covers files, top-level/nested directories, missing
    scope, malformed values, escapes, and platform separators.
- `W34-E7-S4-T2` (done) Migrate semantic validation to the canonical allowed-write-scope
  boundary. [`BUG-13`, `ARCH-06`]
  - Dependencies: `W34-E7-S4-T1`.
  - Scope: semantic validator scope consumer only.
  - Verification: validator fixtures classify the canonical parity table exactly.
- `W34-E7-S4-T3` (done) Migrate task diff/scope gates to the canonical allowed-write-scope
  boundary. [`BUG-13`, `ARCH-06`]
  - Dependencies: `W34-E7-S4-T1`.
  - Scope: task execution scope consumer only.
  - Verification: task diff fixtures classify the canonical parity table exactly and
    retain fail-closed repair behavior.
- `W34-E7-S4-T4` (done) Migrate repository diff and Implement Review reads to the canonical
  allowed-write-scope boundary. [`BUG-13`, `ARCH-06`]
  - Dependencies: `W34-E7-S4-T1`.
  - Scope: repository diff/read-model consumer only.
  - Verification: the canonical `workitems/<id>/context/allowed-write-scope.md` fixture
    drives Implement Review and matches the parity table.

Exit evidence:

- validator, task execution, and Implement Review classify the same canonical parity
  table; no supported consumer reads a stage-local shadow scope or private path grammar.

### Epic W34-E8 — planning and architecture source-of-truth hygiene (`done`)
Linked stories: `US-06`, `US-10`, `US-11`, `US-12`

#### Slice W34-E8-S1 — bounded canonical planning queue (`done`)
Goal: keep roadmap status authoritative and backlog limited to current execution intent.

Dependencies:

- none

Local tasks:

- `W34-E8-S1-T1` (done) Remove the historical backlog journal and make queue
  reconciliation notes bounded instead of append-only. [`PLAN-01`]
  - Scope: backlog queue and restoration policy only.
  - Verification: the active queue is preserved, every queued ID resolves in roadmap,
    and backlog contains one current reconciliation note.
- `W34-E8-S1-T2` (done) Normalize inherited local-task status and historical disposition
  semantics across roadmap and backlog placement. [`PLAN-01`]
  - Scope: planning status model only.
  - Verification: `Next` tasks are explicitly `next`, queued tasks are non-terminal,
    and every marker follows the documented vocabulary.
- `W34-E8-S1-T3` (done) Replace wave-specific backlog assertions with generic roadmap/backlog
  integrity checks. [`PLAN-02`]
  - Scope: planning documentation tests only.
  - Verification: synthetic orphan, duplicate, queued-done, non-local, status-mismatch,
    and invalid-Soon-dependency fixtures fail deterministically.

Exit evidence:

- backlog is a bounded execution queue rather than a second historical source;
- generic checks enforce ID, status, and dependency invariants for future waves.

#### Slice W34-E8-S2 — stable target-architecture wording (`done`)
Goal: describe implemented ownership and supported behavior without completed-wave or
unimplemented-mode claims.

Dependencies:

- none

Local tasks:

- `W34-E8-S2-T1` (done) Replace stale planned frontend/project-set and completed-wave wording
  with stable implemented ownership boundaries. [`ARCH-07`]
  - Scope: target architecture and matching documentation assertions only.
  - Verification: architecture docs describe current ownership without Wave 29 policy
    text or contradicting the planned browser-driver decision.
- `W34-E8-S2-T2` (done) Reconcile the CLI runtime-log contract with `US-06` and current CLI
  behavior. [`ARCH-07`]
  - Scope: product/architecture documentation decision only.
  - Verification: docs consistently specify raw logs and structured evidence; any new
    user-selectable log mode is deferred to a separate product slice.

Exit evidence:

- target architecture describes current supported behavior and no longer embeds a
  completed implementation wave as permanent policy.

Wave 34 exit evidence:

- every confirmed audit finding is mapped to a roadmap local task or, for `SEC-02`, an
  explicit deployment-boundary deferral with reopen triggers;
- all P1 non-security findings have deterministic regressions and no remaining accepted
  P1 state/evidence invariant gap;
- CI executes every declared deterministic CI scenario and every packaged JavaScript
  file has an executable syntax gate;
- provider-authenticated live E2E remains outside the implementation gate;
- full configured lint, type, test, build, wheel-smoke, and documentation consistency
  checks pass before the wave is closed.

Sync notes:

- `2026-07-14` The incremental cleanup/refactoring review in
  `docs/analysis/repository-cleanup-audit-2026-07-14.md` reopened Wave 35 for the
  task-aware implementation-entrypoint invariant, added the canonical
  allowed-write-scope boundary, reconciled incomplete harness extraction and
  deterministic-gate cleanup with existing Wave 34 ownership, and created `W34-E8` for
  planning/architecture source-of-truth hygiene.
- `2026-07-10` Wave 34 was opened from
  `docs/analysis/codebase-audit-2026-07-10.md`. The first promoted task restores the
  canonical `stage-result.md` gate; independent transactional publication, local
  mutation serialization, adapter characterization, runtime policy, and identifier
  boundary foundations are queued behind it or alongside it according to their explicit
  dependencies. Frontend session/origin hardening is intentionally not queued while the
  supported UI remains private, local, and single-operator.

---

## Wave 35 — implementation-ready tasks and incremental execution (`done`)

Goal: turn the approved tasklist into complete task cards and execute them incrementally without
changing the canonical eight-stage workflow.

Dependencies:

- `W34-E1-S1-T1`, `W34-E1-S2-T1`
- `W34-E2-S1-T1`, `W34-E2-S1-T2`, `W34-E2-S2-T1`
- `W34-E3-S1-T1`, `W34-E3-S1-T2`
- `W34-E7-S2-T1`

### Epic W35-E1 — implementation-ready task cards (`done`)
Linked stories: `US-02`, `US-03`, `US-04`, `US-10`, `US-13`

#### Slice W35-E1-S1 — rich task-card contract (`done`)
Goal: require every task to carry enough bounded intent and acceptance evidence for execution.

Local tasks:

- `W35-E1-S1-T1` (done) Define the rich Markdown task-card contract and canonical example.
  - Scope: tasklist contracts and examples.
  - Verification: contract registry and example checks pass.
- `W35-E1-S1-T2` (done) Parse and validate task cards, acceptance ids, and dependency graphs.
  - Scope: typed task plan and semantic validator.
  - Verification: valid/invalid fixture matrix passes.
- `W35-E1-S1-T3` (done) Align tasklist, implement, review, and QA prompt packs with task-card evidence.
  - Scope: stage prompt packs.
  - Verification: prompt quality checks pass.
- `W35-E1-S1-T4` (done) Add a deterministic rich-tasklist workflow scenario.
  - Scope: provider-free harness fixtures.
  - Verification: valid output passes and incomplete output repairs or stops.

#### Slice W35-E1-S2 — deterministic task boundaries (`done`)
Goal: make task scope and ordering mechanically enforceable before implementation starts.

Dependencies: `W35-E1-S1`.

Local tasks:

- `W35-E1-S2-T1` (done) Define safe repository-relative path prefixes for `In scope`.
  - Scope: tasklist contracts and canonical examples.
  - Verification: contract registry and example checks pass.
- `W35-E1-S2-T2` (done) Reject unsafe scope paths and forward dependency references.
  - Scope: typed task-plan parser and semantic tasklist validation.
  - Verification: validator fixture matrix passes.
- `W35-E1-S2-T3` (done) Align tasklist run and repair prompts with deterministic boundaries.
  - Scope: tasklist prompt pack.
  - Verification: prompt-quality checks pass.
- `W35-E1-S2-T4` (done) Add provider-free invalid boundary fixtures.
  - Scope: deterministic tasklist scenario inputs.
  - Verification: missing scope paths, escapes, forward dependencies, and scope conflicts stop or repair.

### Epic W35-E2 — durable per-task execution (`done`)
Linked stories: `US-03`, `US-04`, `US-06`, `US-10`, `US-11`, `US-13`

#### Slice W35-E2-S1 — task plan and ledger (`done`)
Goal: derive safe dependency order and mutable execution state from immutable tasklist Markdown.

Local tasks:

- `W35-E2-S1-T1` (done) Document task source-of-truth, persistence, and compatibility decisions.
- `W35-E2-S1-T2` (done) Implement the typed task plan and dependency resolver.
- `W35-E2-S1-T3` (done) Implement the atomic source-hashed task ledger and state transitions.

#### Slice W35-E2-S2 — task-scoped implementation (`done`)
Goal: execute and repair one dependency-ready task at a time, then publish aggregate evidence.

Local tasks:

- `W35-E2-S2-T1` (done) Capture task-scoped repository baselines and attempt evidence.
- `W35-E2-S2-T2` (done) Bind implementation validation to task scope and acceptance ids.
- `W35-E2-S2-T3` (done) Run the automatic fail-fast dependency loop with manual resume.
- `W35-E2-S2-T4` (done) Aggregate task reports and commit implement success after publication.

#### Slice W35-E2-S3 — operator task controls (`done`)
Goal: expose the same task state and safe mutations through CLI and the local frontend.

Local tasks:

- `W35-E2-S3-T1` (done) Add `aidd task list`, `show`, and `run` commands.
- `W35-E2-S3-T2` (done) Add UI-neutral task reads and run-scoped mutation API.
- `W35-E2-S3-T3` (done) Render task progress and Run/Resume controls in the operator UI.

#### Slice W35-E2-S4 — aggregate gates and deterministic evidence (`done`)
Goal: prove every task and acceptance criterion before review/QA progression.

Local tasks:

- `W35-E2-S4-T1` (done) Bind review and QA evidence to every completed task and acceptance id.
- `W35-E2-S4-T2` (done) Add provider-free failure, repair, resume, and aggregate full-flow coverage.

#### Slice W35-E2-S5 — crash-safe task lifecycle (`done`)
Goal: make task attempts, interview resume, diff repair, and aggregate finalization recoverable.

Dependencies: `W35-E2-S1`, `W35-E2-S2`, `W34-E3-S1`.

Local tasks:

- `W35-E2-S5-T1` (done) Add dead-owner recovery and transferable run mutation leases.
- `W35-E2-S5-T2` (done) Add ledger schema v2 finalization state and transitions.
- `W35-E2-S5-T3` (done) Allocate task attempts atomically and reconcile abandoned execution.
- `W35-E2-S5-T4` (done) Preserve task-owned questions and answers across blocked resume.
- `W35-E2-S5-T5` (done) Run task diff and scope validation inside the implement repair loop.
- `W35-E2-S5-T6` (done) Persist independent aggregate finalization attempts.
- `W35-E2-S5-T7` (done) Retry aggregate validation and atomic publication without rerunning tasks.

#### Slice W35-E2-S6 — operator recovery parity (`done`)
Goal: expose complete task state and conflict-safe task/finalization mutations through CLI and UI.

Dependencies: `W35-E2-S5`.

Local tasks:

- `W35-E2-S6-T1` (done) Add a shared task read model with attempts and finalization state.
- `W35-E2-S6-T2` (done) Complete task CLI detail, manifest preflight, and `task finalize`.
- `W35-E2-S6-T3` (done) Add synchronous UI admission and task finalization API.
- `W35-E2-S6-T4` (done) Render attempt history and finalization recovery in the operator UI.

#### Slice W35-E2-S7 — structured aggregate acceptance evidence (`done`)
Goal: require review and QA to record one evidence-backed result per task acceptance criterion.

Dependencies: `W35-E1-S2`, `W35-E2-S5`, `W35-E2-S6`.

Local tasks:

- `W35-E2-S7-T1` (done) Define structured review and QA task-acceptance evidence.
- `W35-E2-S7-T2` (done) Validate exact task/acceptance evidence coverage and verdict alignment.
- `W35-E2-S7-T3` (done) Align review and QA prompts with structured aggregate evidence.
- `W35-E2-S7-T4` (done) Extend the provider-free task execution recovery scenario.

#### Slice W35-E2-S8 — task-aware implementation entrypoint integrity (`done`)
Goal: make every public implementation entrypoint preserve dependency order, task-local
evidence, aggregate finalization, and remediation truth.

Dependencies:

- `W35-E1-S1`
- `W35-E1-S2`
- `W35-E2-S5`
- `W35-E2-S6`
- `W35-E2-S7`

Local tasks:

- `W35-E2-S8-T1` (done) Define the task-aware semantics and failure behavior for
  workflow, stage run/interact, task run/finalize, UI stage controls, and remediation.
  [`CORR-01`]
  - Scope: task-execution architecture and entrypoint contract only.
  - Verification: one matrix names task selection, ledger/finalization transitions,
    publication eligibility, and fail-closed behavior for every entrypoint.
- `W35-E2-S8-T2` (done) Move implementation execution/finalization policy into one typed core
  service with domain results and errors. [`CORR-01`, `ARCH-04`]
  - Dependencies: `W35-E2-S8-T1`.
  - Scope: core implementation execution boundary only.
  - Verification: core tests preserve task-loop behavior and the service imports no
    CLI or Typer modules.
- `W35-E2-S8-T3` (done) Route workflow, stage, interact, and task CLI commands through the
  core implementation service. [`CORR-01`, `ARCH-04`]
  - Dependencies: `W35-E2-S8-T2`.
  - Scope: CLI adapters only.
  - Verification: CLI entrypoint fixtures cannot invoke or publish raw one-shot
    `implement` outside the task-aware contract.
- `W35-E2-S8-T4` (done) Route UI stage, task, interact, and remediation mutations through the
  core implementation service. [`CORR-01`, `ARCH-04`]
  - Dependencies: `W35-E2-S8-T2`.
  - Scope: private operator API/application adapters only.
  - Verification: remediation rebuilds task/finalization evidence before downstream
    stages become stale or eligible, and UI imports no CLI business service.
- `W35-E2-S8-T5` (done) Require a complete successful task ledger and aggregate finalization
  before review or QA eligibility. [`CORR-01`]
  - Dependencies: `W35-E2-S8-T2`.
  - Scope: stage progression and cross-stage validation defense only.
  - Verification: forged generic implement success cannot unlock review/QA without
    matching task and finalization evidence.
- `W35-E2-S8-T6` (done) Add a provider-free implementation-entrypoint conformance matrix and
  extend the deterministic task-execution scenario. [`CORR-01`, `TEST-07`]
  - Dependencies: `W35-E2-S8-T3`, `W35-E2-S8-T4`, `W35-E2-S8-T5`.
  - Scope: CLI/API/workflow/remediation regression coverage only.
  - Verification: every entrypoint records task attempts/diffs, respects dependencies,
    fails closed without ready context, and publishes only after aggregate success.

Exit evidence:

- there is no public path from raw `implement` execution to canonical success;
- CLI, UI, workflow, remediation, review, and QA observe the same task ledger and
  finalization policy.

#### Slice W35-E2-S9 — task-execution change isolation (`done`)
Goal: reduce change coupling after all entrypoints use the same characterized core
service.

Dependencies:

- `W35-E2-S8`

Local tasks:

- `W35-E2-S9-T1` (done) Extract task attempt, recovery, and interview-evidence lifecycle from
  the task-execution hotspot. [`REF-06`]
  - Scope: core task attempt lifecycle only.
  - Verification: blocked/resumed/crashed attempt fixtures remain equivalent.
- `W35-E2-S9-T2` (done) Extract typed repository baseline, diff, and scope evidence helpers.
  [`REF-06`]
  - Dependencies: `W34-E7-S4`.
  - Scope: core task repository evidence only; reuse `AllowedWriteScope` without a new
    scope grammar.
  - Verification: tracked, untracked, deleted, symlink, and out-of-scope fixtures retain
    exact findings.
- `W35-E2-S9-T3` (done) Extract aggregate report, validation, publication, and finalization
  coordination. [`REF-06`]
  - Scope: core implementation finalization only.
  - Verification: retry, publication failure, and successful aggregate fixtures retain
    ledger/status equivalence.
- `W35-E2-S9-T4` (done) Partition task execution tests by plan, attempt, repository evidence,
  and finalization ownership. [`REF-06`]
  - Dependencies: `W35-E2-S9-T1`, `W35-E2-S9-T2`, `W35-E2-S9-T3`.
  - Scope: task execution tests and import-boundary assertion only.
  - Verification: the same cases are collected and an architecture test rejects core
    task semantics owned or re-exported by CLI/UI modules.

Exit evidence:

- task attempts, repository evidence, and aggregate finalization can evolve behind one
  stable application boundary.

#### Slice W35-E2-S10 — bounded task repository evidence (`done`)
Goal: avoid repeated full-repository hashing and duplicate attempt payloads while
preserving immutable task evidence.

Dependencies:

- `W35-E2-S9-T1`
- `W35-E2-S9-T2`
- `W35-E2-S9-T3`

Local tasks:

- `W35-E2-S10-T1` (done) Capture one immutable `RepositorySnapshot` per checkpoint and reuse
  it across validation and task completion. [`PERF-03`]
  - Scope: task repository scan lifecycle only.
  - Verification: a synthetic large-repository fixture asserts one scan per checkpoint
    while preserving exact diff/scope findings.
- `W35-E2-S10-T2` (done) Define the canonical task-attempt evidence layout, reference,
  retention, and compatibility contract. [`PERF-03`]
  - Scope: task attempt evidence architecture only.
  - Verification: the decision selects one copy/reference model, forbids hard links,
    and names integrity, cleanup, resume, and read-model behavior.
- `W35-E2-S10-T3` (done) Migrate duplicated global-attempt payloads to the canonical task
  evidence contract. [`PERF-03`]
  - Dependencies: `W35-E2-S10-T2`.
  - Scope: task attempt evidence materialization only.
  - Verification: bundle-size, integrity, cleanup, resume, and read-model fixtures pass
    without hard links or duplicated evidence payloads.

Exit evidence:

- successful and repaired tasks have bounded repository scans and one contract-owned
  immutable representation for each evidence payload.

Wave 35 exit evidence:

- compact legacy tasklists fail without fallback;
- task execution is dependency-ordered, task-scoped, resumable, and fail-fast;
- implement success is published only after every task succeeds;
- CLI and UI expose consistent task state;
- deterministic checks cover repair, conflicts, hash mismatch, aggregation, review, and QA;
- every implementation entrypoint is task-aware and task evidence is bounded.

Corrective audit:

- `2026-07-12` Wave 35 was reopened after failure-path review found lost interview answers,
  unrecoverable `executing` tasks, non-repeatable aggregate publication, late diff validation,
  weak aggregate evidence matching, and asynchronous UI mutation conflicts. Existing completed
  tasks remain historical implementation evidence; corrective slices close these gaps before the
  wave can be marked done again.
- `2026-07-12` Corrective slices completed deterministic task-scope/order validation,
  crash-safe leases and attempts, blocked Q/A resume, in-loop diff repair, ledger-v2 aggregate
  finalization, `aidd task finalize`, synchronous UI conflicts, full task reads, and structured
  review/QA acceptance evidence. Ruff, mypy, `1358` pytest tests, package build/smoke, scenario
  loading, generic-cli eval doctor, and diff checks passed.
- `2026-07-14` Wave 35 was reopened after repository review proved that generic CLI/UI
  stage and remediation entrypoints can still publish one-shot `implement` success
  outside the task ledger. Corrective slice `W35-E2-S8` restores one core task-aware
  execution boundary before further task-execution refactoring or optimization.

---

## Wave 36 — Document & Evidence Studio migration (`planned`)

Goal: migrate the capability-rich packaged Operator UI to the accepted Document & Evidence
Studio experience through bounded vertical slices across Guided Setup, Inbox, Studio,
Recovery, History, and Flow Complete without changing the canonical stage graph, mutation
semantics, artifact ownership, or `aidd ui` entrypoint.

The migration is a strangler rollout, not a big-bang rewrite. Legacy and Studio renderers may
temporarily consume the same server-authoritative payloads, but they must share action dispatch
and mutation services. A temporary browser-only presentation selector may change the renderer;
it must never select a different endpoint, runtime, eligibility rule, or workflow path. Rollback
changes presentation only and never rewrites canonical `.aidd/` state.

### Wave 36 reference authority

When references disagree, use this order:

1. [Operator Frontend Contract](../architecture/operator-frontend.md) sections 8 and 9 for the target information
   architecture, four-mode concept, state matrix, component contract, references, and UX
   acceptance criteria;
2. sections 1 through 7 of the same document for workflow invariants, write boundaries,
   current endpoints/read models, and compatibility behavior; their Mission Control,
   cockpit, right-rail, bottom-dock, and Work / Recovery / Evidence / History presentation
   terms are implemented-baseline evidence, not target design;
3. [target architecture](../architecture/target-architecture.md),
   [task execution](../architecture/task-execution.md), and
   [project-set workspace](../architecture/project-set-workspace.md) for workflow, task,
   completed-run, and project-root ownership;
4. [user stories](../product/user-stories.md) for product outcomes and scope;
5. the [reference-screen prompt set](../architecture/assets/operator-ui-document-evidence-studio/generation-prompts.md)
   and linked images for visual hierarchy, density, and responsive intent only;
6. current core/UI read models, service contracts, and deterministic tests for compatibility;
7. analysis reports and the previous Mission Control assets as historical baseline evidence,
   never as normative target design.

Canonical design references:

- [accepted UX direction](../architecture/operator-frontend.md#8-accepted-next-generation-ux-direction);
- [UX validation checklist](../architecture/operator-frontend.md#9-ux-validation-checklist-for-the-accepted-direction);
- [reference-screen prompt set](../architecture/assets/operator-ui-document-evidence-studio/generation-prompts.md);
- [document contracts](../architecture/document-contracts.md) and
  [runtime matrix](../architecture/runtime-matrix.md);
- [local-project Operator UI E2E lane](../e2e/operator-ui-local-project.md) for the current
  executable baseline and evidence schema; its legacy route names remain baseline-only until
  `W36-E1-S1-T3` replaces them with the accepted state/route matrix.

Compatibility and acceptance references:

- core read-model ownership: [models](../../src/aidd/core/operator_frontend_models.py),
  [dashboard](../../src/aidd/core/operator_frontend_dashboard.py),
  [project home](../../src/aidd/core/operator_frontend_project_home.py),
  [artifacts](../../src/aidd/core/operator_frontend_artifacts.py), and
  [timeline](../../src/aidd/core/operator_timeline.py);
- local service/package boundary: [UI service](../../src/aidd/cli/ui.py),
  [HTTP layer](../../src/aidd/cli/ui_http.py), and
  [asset manifest](../../src/aidd/cli/ui_assets.py);
- shared browser seam: [packaged entry](../../src/aidd/cli/static/index.html),
  [bootstrap](../../src/aidd/cli/static/operator.js),
  [API/state](../../src/aidd/cli/static/operator-api-state.js), and
  [main composition](../../src/aidd/cli/static/operator-main.js);
- current surface owners to strangle, not fork: [cockpit](../../src/aidd/cli/static/operator-stage-cockpit.js),
  [documents/evidence](../../src/aidd/cli/static/operator-artifacts-documents.js),
  [questions](../../src/aidd/cli/static/operator-questions.js),
  [approvals/interventions](../../src/aidd/cli/static/operator-approvals-interventions.js),
  [next flow](../../src/aidd/cli/static/operator-next-flow-actions.js),
  [logs/jobs](../../src/aidd/cli/static/operator-logs-jobs.js), and
  [onboarding](../../src/aidd/cli/static/operator-onboarding.js);
- visual-system baseline: [tokens](../../src/aidd/cli/static/operator-tokens.css),
  [base](../../src/aidd/cli/static/operator-base.css),
  [layout](../../src/aidd/cli/static/operator-layout.css),
  [components](../../src/aidd/cli/static/operator-components.css), and
  [responsive rules](../../src/aidd/cli/static/operator-responsive.css);
- service/package compatibility: [UI service tests](../../tests/cli/test_ui.py),
  [asset contracts](../../tests/cli/test_ui_assets_contracts.py), and
  [package resources](../../tests/test_packaging_resources.py);
- canonical behavior evidence: [operator frontend](../../tests/core/test_operator_frontend.py),
  [timeline](../../tests/core/test_operator_timeline.py),
  [task execution](../../tests/core/test_task_execution.py),
  [remediation](../../tests/core/test_remediation.py),
  [run comparison](../../tests/core/test_run_comparison.py), and
  [runtime operator](../../tests/core/test_runtime_operator.py);
- [docs consistency](../../tests/test_docs_consistency.py) for architecture, queue, and
  visual-reference synchronization.

Historical planning evidence:

- [UX/UI audit 2026-07-08](../analysis/ux-ui-audit-2026-07-08.md) records browser-backed
  happy-path and failure-state iterations for the current UI;
- [codebase audit 2026-07-10](../analysis/codebase-audit-2026-07-10.md) records Wave 34 backend
  and test foundations;
- the `2026-07-11` Chrome review measured a `275.2px` sticky header at `390x844`, a
  first-launch primary action below the first viewport, a `2802px` mobile onboarding page,
  twenty controls below `44px`, two borderline contrast failures, and accessible-name
  mismatches on all eight stage buttons.

External pattern references are non-normative and may inform interaction checks only:

- [Linear Inbox](https://linear.app/docs/inbox) for keyboard-friendly attention queue and
  list-to-detail navigation; AIDD blocking items remain core-prioritized and cannot be snoozed
  or dismissed;
- [GOV.UK Check answers](https://design-system.service.gov.uk/patterns/check-answers/) and
  [Complete multiple tasks](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/)
  for Guided Setup review, status, Back, and input-preservation behavior;
- [GitHub Actions workflow-run logs](https://docs.github.com/en/actions/how-tos/monitor-workflows/use-workflow-run-logs)
  and [previous run attempts](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)
  for run/job/step hierarchy, exact failure evidence, retained logs/artifacts, and explicit
  attempt selection;
- [Sentry Issue Details](https://docs.sentry.io/product/issues/issue-details/) for a decisive
  problem summary followed by stack/breadcrumb evidence and contextual drill-down;
- [Prefect Artifacts](https://docs.prefect.io/v3/concepts/artifacts) for human-readable artifacts
  tied to exact flow/task runs and retained versions.

These references do not authorize copying product visuals, hiding missing evidence, inventing
progress, or changing AIDD workflow semantics. The local authority order above always wins.

### Reference-screen crosswalk

| Reference | Target surface | Owning slice | Supporting contract | Executable journey | Primary acceptance |
| --- | --- | --- | --- | --- | --- |
| [01-inbox-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/01-inbox-desktop.png) | Project-local decision queue | `W36-E5-S3` | `W36-E5-S0` and `W36-E5-S1` | `W36-E7-S1-T12` | First core-approved decision and action are visible without scrolling. |
| [02-guided-setup-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/02-guided-setup-desktop.png) | Four-step Guided Setup | `W36-E4-S1` | `W36-E3-S2` and `W36-E3-S3` | `W36-E7-S1-T1` | Create/Resume and explicit runtime selection complete through one service path. |
| [03-active-studio-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/03-active-studio-desktop.png) | Live document-centered Studio | `W36-E5-S4` | `W36-E5-S1` | `W36-E7-S1-T2` and `W36-E7-S1-T7` | Context, Decision Bar, primary document, and live evidence share the first desktop viewport. |
| [04-validation-repair-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/04-validation-repair-desktop.png) | Validation recovery | `W36-E5-S6` | `W36-E6-S3` | `W36-E7-S1-T3` | Exact finding and `Run Repair` versus `Request Change` semantics remain truthful. |
| [05-quality-gate-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/05-quality-gate-desktop.png) | Implement/Review/QA quality gate | `W36-E5-S7` | `W35-E2-S8` | `W36-E7-S1-T4` and `W36-E7-S1-T9` | Real diff, claim evidence, remediation selection, and stale downstream state agree. |
| [06-history-filmstrip-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/06-history-filmstrip-desktop.png) | Attempt History Filmstrip | `W36-E5-S8` | `W36-E6-S1` | `W36-E7-S1-T5` | Only durable attempts, events, artifacts, and lineage are selectable. |
| [07-flow-complete-desktop.png](../architecture/assets/operator-ui-document-evidence-studio/07-flow-complete-desktop.png) | Immutable terminal handoff | `W36-E5-S9` | `W36-E6-S2` and `W36-E6-S4` | `W36-E7-S1-T8` | Fresh QA exposes one core-recommended outcome and never mutates the source run. |
| [08-question-mobile.png](../architecture/assets/operator-ui-document-evidence-studio/08-question-mobile.png) | First-viewport mobile question | `W36-E5-S5` | `W36-E5-S2` | `W36-E7-S1-T6` | Question, resolution status, and submit action fit the decision-first mobile contract. |

Generated text is not normative. The written architecture contract and service semantics win
when a reference image differs from executable behavior.

### Migration phases

1. **Contract freeze** — finish the route/action/quality matrices in `W36-E1`; the accepted
   concept and viewport contract are already recorded by `W36-E1-S1-T1..T2`.
2. **Executable baseline** — land the provider-free packaged-browser harness and reproduce
   current geometry, accessibility, console, and network state before restructuring.
3. **Additive foundations** — add the core terminal recommendation, semantic tokens, shared
   controls/state surfaces, URL state, scoped drafts, reconnect, and mutation guards without
   changing the default renderer.
4. **Guided Setup** — migrate Project -> Work Item -> Runtime -> Review & Launch and prove the
   first-launch journey before closing its parity entry; physical legacy removal waits for the
   cutover phase.
5. **Inbox and active Studio** — add the project-local attention projection, mode shell,
   Decision Bar, Document Canvas, Evidence Inspector, and live observation.
6. **Recovery and quality gates** — migrate questions/interventions, approvals,
   runtime/validation/repair, task finalization, Review, QA, remediation, and stale reruns one
   state family at a time.
7. **History and handoff** — migrate Filmstrip, comparison, lineage, Flow Complete, and all
   next-flow outcomes while preserving source-run immutability.
8. **Cutover and cleanup** — promote Studio only after per-surface parity, retain a bounded
   presentation-only rollback window, then remove legacy renderers and selectors separately.
9. **Acceptance** — enforce all discovered browser journeys in CI/release preflight and record
   first-time-operator evidence.

Each migrated state family must land its own browser journey before its parity entry closes.
All legacy renderers remain available through the bounded rollback window and are removed only
in the cutover phase. The final acceptance epic aggregates already-executable journeys; it is
not the first time they are tested.

### Hard dependency gates

| Gate | Blocks |
| --- | --- |
| `W36-E1-S1..S2` | Broad visual restructuring or route removal. |
| `W34-E5-S3-T4..T5` and `W36-E2` | Default-shell, responsive, and renderer-parity claims. |
| `W35-E2-S8` | Full-flow launch redesign, implement task controls, remediation, Review/QA eligibility, and default cutover. |
| `W34-E2-S2-T2` | Resume, History, Lineage, and durable deep-link sign-off. |
| `W34-E2-S3-T1..T2` | Archive and prompt-accountability presentation. |
| `W34-E3-S2` | Approval renderer replacement and session-breadth confirmation. |
| `W34-E3-S3-T1` | Long-running/reconnect sign-off. |
| `W34-E4-S2` and `W34-E4-S3` | Runtime-failure vocabulary and dimensioned readiness. |
| `W34-E7-S1` | Capability and protected-data/write-scope claims. |
| `W34-E3-S4-T4` | Follow-up/clone draft and next-flow renderer cutover. |
| Per-surface browser parity | Default routing for that surface and eventual legacy removal. |

Scope decisions:

- mobile is monitoring, question answering, approval, recovery, and next-decision first;
  dense diff, evidence graph, comparison, and lineage remain desktop-first drill-downs;
- Wave 36 owns operator-facing semantics, packaged browser behavior, design-system
  primitives, responsive hierarchy, navigation, renderer migration, and rendered evidence;
- Wave 34 remains authoritative for server-side mutation leases, approval compare-and-set,
  bounded retention, runtime outcome/evidence truth, capability policy, run identity, archive
  overlays, lightweight DOM foundations, and next-flow module splitting;
- Wave 35 remains authoritative for task-aware implement entrypoint and finalization integrity;
- the frontend remains private, local, single-operator, and loopback-first.

Non-goals:

- a new stage, workflow engine, adapter, artifact authority, provider-specific UI semantics,
  or unaudited inline editing of generated evidence;
- remote multi-user deployment, frontend authentication, or cross-project Inbox aggregation;
- marketing-page styling, decorative motion, or unreadable mobile parity for dense evidence;
- provider-authenticated live E2E as an implementation gate;
- deleting legacy renderers in the same task that first introduces their replacement.

Story check:

- the wave strengthens `US-02`, `US-03`, `US-05`, `US-06`, `US-09`, `US-10`, `US-11`,
  `US-12`, and `US-13` while preserving runtime portability from `US-01`;
- this is implementation and acceptance detail inside existing product scope, so
  `docs/product/user-stories.md` does not require a scope update.

### Epic W36-E1 — accepted UX contract and measurable hierarchy (`done`)
Linked stories: `US-05`, `US-06`, `US-09`, `US-11`, `US-12`

#### Slice W36-E1-S1 — operator coherence contract (`done`)
Goal: lock Inbox, Studio, History, and Guided Delivery semantics plus one primary-decision
rule before changing the rendered shell.

Dependencies:

- none

Local tasks:

- `W36-E1-S1-T1` (done) Lock Inbox / Studio / History destinations, Guided Delivery
  presentation, contextual Recovery/Evidence, and the one-primary-action contract.
  - Scope: `docs/architecture/operator-frontend.md` only.
  - Verification: a docs consistency matrix names the primary job, primary action,
    supporting evidence, and recovery path for every top-level state.
- `W36-E1-S1-T2` (done) Define the mobile operator job boundary and viewport ordering/budgets
  for `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`.
  - Scope: operator frontend architecture only.
  - Verification: the contract names the first-viewport action, maximum compact-header
    footprint, drill-down behavior, and required mobile jobs at every breakpoint.
- `W36-E1-S1-T3` (done) Replace checklist-only navigation wording with a canonical operator
  state/route matrix.
  - Scope: `docs/e2e/operator-ui-local-project.md` only.
  - Verification: Guided Setup, Inbox, active Studio, reconnecting, Question/Approval
    Recovery, Validation Recovery, Quality Gate, Flow Complete, and History each map to
    an explicit route, context key, and expected decision surface.

Exit evidence:

- every supported state has one primary operator job and a bounded supporting-evidence
  path;
- mobile behavior is a deliberate product contract rather than an accumulation of
  state-specific CSS ordering rules.

#### Slice W36-E1-S2 — truthful control and quality contract (`done`)
Goal: make visible controls and quality claims correspond to distinct behavior and
measurable evidence.

Dependencies:

- `W36-E1-S1`

Local tasks:

- `W36-E1-S2-T1` (done) Define an action-to-service semantics table for setup, create,
  resume, follow-up, clone, eval, archive, workflow, and stage actions.
  - Scope: operator frontend architecture only.
  - Verification: every visible selectable action has a distinct outcome and service
    path, or is explicitly removed.
- `W36-E1-S2-T2` (done) Define truthful UI vocabulary for runtime readiness, authentication
  evidence, safety/write scope, approval breadth, connectivity, and mutation state.
  - Scope: operator UX vocabulary in architecture docs.
  - Verification: ambiguous normative claims such as undifferentiated `ready` or
    `safe` are absent from the accepted vocabulary.
- `W36-E1-S2-T3` (done) Define measurable operator UX thresholds and evidence fields.
  - Scope: local-project UI E2E acceptance docs.
  - Verification: the template records first-action visibility, header footprint,
    touch targets, focus entry, contrast, overflow, reconnect outcome, task completion,
    wrong actions, elapsed time, and operator confidence.

Exit evidence:

- controls cannot promise behavior that the selected service call does not perform;
- UI quality is evaluated by rendered and task-completion evidence rather than asset
  string presence alone.

### Epic W36-E2 — executable rendered-browser foundation (`done`)
Linked stories: `US-07`, `US-09`, `US-11`

#### Slice W36-E2-S1 — deterministic packaged-UI browser harness (`done`)
Goal: execute the packaged local UI in a real browser against provider-free states with
deterministic cleanup.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2-T3`
- `W34-E5-S3-T4`
- `W34-E5-S3-T5`

Local tasks:

- `W36-E2-S1-T1` (done) Select and document the maintained provider-free browser driver and
  packaging policy for served UI checks.
  - Dependencies: `W36-E1-S2-T3`.
  - Scope: browser-test architecture and documentation policy only.
  - Verification: the decision preserves the no-Node/Vite product runtime, names the
    executable test command, and replaces the blanket no-browser-driver wording in the
    local-project lane.
- `W36-E2-S1-T4` (done) Add the selected browser driver as a development-only dependency and
  lock its executable smoke command.
  - Dependencies: `W36-E2-S1-T1`.
  - Scope: development dependency, lock, and browser smoke command only.
  - Verification: locked sync and one provider-free packaged-UI launch pass without
    changing runtime package dependencies.
- `W36-E2-S1-T2` (done) Add a disposable seeded-project launcher and executable browser harness
  for packaged UI assets.
  - Dependencies: `W36-E2-S1-T4`.
  - Scope: UI browser test infrastructure.
  - Verification: one command serves a temporary project, opens every required viewport,
    records console/network state, and removes project-local `.aidd/` state on exit.
- `W36-E2-S1-T3` (done) Add provider-free fixture builders for setup, no-run, running,
  question, runtime-failure, approval, QA, remediation, and terminal states.
  - Dependencies: `W36-E2-S1-T2`.
  - Scope: deterministic UI fixtures only.
  - Verification: every declared fixture opens through the public local UI without
    provider authentication or arbitrary path reads.

Exit evidence:

- packaged browser behavior is executable and repeatable without a provider runtime;
- fixture state and screenshots never leak into the repository worktree.

#### Slice W36-E2-S2 — rendered geometry and accessibility assertions (`done`)
Goal: fail deterministically when the rendered UI loses first-viewport priority,
accessibility semantics, or viewport containment.

Dependencies:

- `W36-E2-S1`
- `W36-E1-S2-T3`

Local tasks:

- `W36-E2-S2-T1` (done) Add executable accessible-name, label, focus-order, contrast,
  target-size, and reduced-motion assertions.
  - Dependencies: `W36-E2-S1-T3`.
  - Scope: browser assertion helpers.
  - Verification: one intentionally invalid fixture fails each accessibility rule with
    the owning selector and measured value.
- `W36-E2-S2-T2` (done) Add executable sticky-header, primary-action, clipping, overlap,
  nested-scroll, and horizontal-overflow assertions.
  - Dependencies: `W36-E2-S2-T1`.
  - Scope: browser geometry assertions.
  - Verification: intentionally bad header, offscreen CTA, clipped label, scroll-trap,
    and overflow fixtures fail at the expected viewport.
- `W36-E2-S2-T3` (done) Add deterministic screenshot and DOM-measure evidence output.
  - Scope: browser evidence writer.
  - Verification: each run produces bounded viewport metadata, screenshot paths,
    console/network summaries, accessibility results, and cleanup status.

Exit evidence:

- the defects measured in the `2026-07-11` review are executable regressions rather
  than manual observations only.

#### Slice W36-E2-S3 — presentation-only migration seam (`done`)
Goal: migrate one rendered surface at a time while preserving one API client, one action
dispatcher, stable package assets, and a bounded renderer rollback path.

Dependencies:

- `W36-E1-S1-T3`
- `W36-E2-S1`
- `W34-E5-S3-T5`

Local tasks:

- `W36-E2-S3-T1` (done) Extract shared non-next-flow dashboard loading, context selection, and
  mutation dispatch from legacy render ownership; next-flow splitting remains owned by
  `W34-E3-S4-T4` until that task closes.
  - Scope: packaged browser state/action seam only.
  - Verification: legacy fixtures produce equivalent requests and durable readback through
    the shared seam before any Studio renderer is enabled.
- `W36-E2-S3-T2` (done) Add a temporary browser-only `ui=studio|legacy` presentation selector while
  keeping `/`, packaged asset URLs, `aidd ui`, and action endpoints stable.
  - Scope: browser bootstrap and renderer selection only.
  - Verification: an executable truth table covers `missing | studio | legacy` against
    `legacy_only | candidate | parity_closed`: before cutover missing uses legacy; `studio`
    renders candidate or closed Studio surfaces and falls back only for `legacy_only`; `legacy`
    forces every retained rollback renderer; invalid follows the current missing-value rule.
- `W36-E2-S3-T3` (done) Add a per-surface parity manifest with owning slice, rollout state
  (`legacy_only | candidate | parity_closed`), rollback renderer, required fixture, browser
  journey, and legacy-removal gate.
  - Scope: packaged-browser migration metadata and tests.
  - Verification: every declared surface has exactly one owner and no surface can switch
    default before its required journey passes.
- `W36-E2-S3-T4` (done) Make the parity manifest drive per-surface renderer resolution so migrated
  Studio surfaces and unmigrated legacy fallbacks can coexist inside either bootstrap mode.
  - Scope: browser renderer resolver only.
  - Verification: mixed-state fixtures implement the selector/parity truth table, retain one
    shared state/action seam, and fall back deterministically without changing service requests;
    browser journeys can exercise a `candidate` before closure, while missing/default and
    `ui=legacy` never expose candidates during the rollback window.

Exit evidence:

- renderer selection cannot change workflow or mutation semantics;
- rollback is presentation-only and does not alter canonical `.aidd/` state;
- retained legacy renderers remain reachable through missing/default and `ui=legacy` even after
  parity closes, until the bounded cutover task removes the rollback path;
- the migration can cut over one surface without requiring all other surfaces to be ready.

### Epic W36-E3 — semantic design system and accessibility (`done`)
Linked stories: `US-02`, `US-05`, `US-06`, `US-11`

#### Slice W36-E3-S1 — semantic tokens and density (`done`)
Goal: make repeated visual decisions come from one semantic token contract.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- rendered verification uses `W36-E2-S2`

Local tasks:

- `W36-E3-S1-T1` (done) Add semantic typography, spacing, radius, elevation, control-size,
  status, focus, and motion tokens.
  - Scope: `operator-tokens.css` only.
  - Verification: token inventory tests cover every accepted role and enforce a bounded
    raw-value budget outside the token layer.
- `W36-E3-S1-T2` (done) Replace duplicate status and surface palettes with semantic color
  roles.
  - Scope: packaged CSS color consumption.
  - Verification: computed-style fixtures preserve state meaning and meet accepted
    contrast thresholds.
- `W36-E3-S1-T3` (done) Define compact desktop and touch mobile density modes from shared
  control tokens.
  - Scope: token and responsive density rules.
  - Verification: measured controls meet the compact desktop contract and the `44px`
    mobile target without per-component magic values.

Exit evidence:

- type, spacing, radius, color, focus, motion, and control size have one source of truth;
- responsive density does not depend on ad hoc component overrides.

#### Slice W36-E3-S2 — complete form and interaction controls (`done`)
Goal: make every input and clickable surface visually consistent and state-complete.

Dependencies:

- `W36-E3-S1`
- `W36-E2-S2`

Local tasks:

- `W36-E3-S2-T1` (done) Normalize button, text-input, select, textarea, and checkbox anatomy
  and typography.
  - Scope: base control CSS.
  - Verification: onboarding, question, intervention, comparison, and next-flow forms
    share computed height, font, border, radius, and focus roles.
- `W36-E3-S2-T2` (done) Add shared hover, active, focus-visible, disabled, invalid, pending,
  selected, and loading states.
  - Scope: interactive control states.
  - Verification: one browser fixture exercises every state with pointer, keyboard,
    and touch-density assertions.
- `W36-E3-S2-T3` (done) Normalize segmented filters, radio-like selectors, clickable rows,
  and pressed/selected ARIA state.
  - Scope: composite browser controls.
  - Verification: log filters, viewer modes, runtime cards, artifact rows, and evidence
    selections expose equivalent visual and accessibility state.

Exit evidence:

- native text inputs no longer fall outside the product control system;
- pointer, keyboard, and assistive-technology state agree for every control family.

#### Slice W36-E3-S3 — reusable decision and state surfaces (`done`)
Goal: replace locally duplicated card variants with a small shared product-surface
anatomy.

Dependencies:

- `W36-E3-S1`
- `W36-E3-S2`

Local tasks:

- `W36-E3-S3-T1` (done) Implement the shared Decision Bar and Status Marker anatomy.
  - Scope: packaged decision-surface primitives only.
  - Verification: action, pending, blocked, complete, stale, and no-action fixtures retain one
    primary slot plus non-color status text without owning surface-specific policy.
- `W36-E3-S3-T2` (done) Consolidate empty, loading, error, reconnecting, and unavailable
  surfaces with local recovery actions.
  - Scope: packaged state-surface primitives.
  - Verification: every state exposes a title, consequence, recovery action when
    possible, and correct live-region or busy semantics.
- `W36-E3-S3-T3` (done) Establish the editorial hierarchy for Document Canvas, conditional
  Evidence Inspector, and History without an equal-weight card wall.
  - Scope: panel/card layout classes.
  - Verification: rendered fixtures keep one framed primary surface per hierarchy level
    and preserve clear primary/supporting visual weight.
- `W36-E3-S3-T4` (done) Implement the shared Inbox Item anatomy without eligibility or priority
  logic in the browser.
  - Scope: packaged Inbox item primitive only.
  - Verification: blocking, running, ready, terminal, and malformed fixtures render the
    core/service-provided route and action without recomputing either.
- `W36-E3-S3-T5` (done) Implement the shared Guided Step anatomy.
  - Scope: packaged Guided Delivery primitive only.
  - Verification: current, complete, invalid, optional, and disabled step fixtures retain one
    explanation, input group, primary action, Back action, and advanced disclosure.
- `W36-E3-S3-T6` (done) Implement the shared Recovery Summary anatomy.
  - Scope: packaged Recovery primitive only.
  - Verification: question, approval, runtime, validation, intervention, and quality-gate
    fixtures retain one decisive failure, one evidence path, and one primary recovery slot.

Exit evidence:

- decision and state treatment can change once instead of across duplicated local
  spotlight families;
- default work screens no longer give every metadata group equal card weight.

#### Slice W36-E3-S4 — keyboard and readable semantics (`done`)
Goal: close the measured accessible-name, focus-entry, contrast, and numerical scanning
gaps.

Dependencies:

- `W36-E3-S2`
- `W36-E2-S2-T1`

Local tasks:

- `W36-E3-S4-T1` (done) Add a skip-to-current-decision path and deterministic focus entry/return for
  top-level modes and detail surfaces.
  - Scope: shell markup and focus controller.
  - Verification: keyboard-only traversal reaches the primary action before maintenance
    controls and returns focus after dialogs, drill-downs, and recovery actions.
- `W36-E3-S4-T2` (done) Fix stage accessible names and dynamic onboarding/form label
  associations.
  - Scope: rendered accessibility markup.
  - Verification: all eight stage buttons pass label-content-name matching and every
    generated form field has a stable id, name, and associated label.
- `W36-E3-S4-T3` (done) Raise borderline contrast, readable minimums, and tabular numeric
  treatment.
  - Scope: typography and color CSS.
  - Verification: automated contrast checks pass and timers, attempts, counts, and
    status metrics retain stable column width.

Exit evidence:

- the rendered accessibility gate passes without the known Lighthouse contrast and
  stage-label failures;
- keyboard users can enter the operator job without traversing the complete service
  toolbar first.

### Epic W36-E4 — progressive onboarding and truthful runtime context (`planned`)
Linked stories: `US-01`, `US-09`, `US-11`, `US-12`

#### Slice W36-E4-S1 — branching setup flow (`planned`)
Goal: make project, work-item, runtime, and launch decisions sequential and truthful
instead of six equally weighted setup panels.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- `W36-E3-S2`
- `W36-E6-S4-T1`

Local tasks:

- `W36-E4-S1-T1` (parked) Add an explicit Project -> Work item -> Runtime -> Review/Launch
  onboarding state machine with deterministic Back and Continue transitions.
  - Scope: `operator-onboarding.js` state controller.
  - Verification: a transition table covers validation success/failure, create, resume,
    runtime selection, backward navigation, and launch readiness.
- `W36-E4-S1-T2` (planned) Render Create and Resume as sibling work-item branches and allow
  inspection before runtime selection.
  - Scope: onboarding work-item step.
  - Verification: resume opens existing context without a runtime or launch request,
    while mutation actions remain runtime-gated.
- `W36-E4-S1-T3` (planned) Move project-set and configuration details behind an Advanced
  disclosure.
  - Scope: onboarding project/work-item layout.
  - Verification: create or resume remains inside the first setup viewport at `390x844`
    and `1440x900`, while advanced project-set validation remains reachable.
- `W36-E4-S1-T4` (planned) Remove no-run mode cards that do not change execution semantics and
  leave terminal follow-up, clone, eval, and archive presentation to `W36-E5-S9`.
  - Scope: Guided Setup presentation only; the legacy renderer remains available for rollback.
  - Verification: the setup action-to-service matrix proves each remaining selector has a
    distinct endpoint/outcome and no terminal disposition leaks into first-run setup.
- `W36-E4-S1-T5` (planned) Add the Guided Delivery preference and contextual explanation card over
  the same selected context and service actions used by Studio.
  - Scope: Guided Delivery browser presentation only.
  - Verification: toggling Guided Delivery preserves project, work item, run, stage,
    runtime, request payload, and durable result for the same action.
- `W36-E4-S1-T6` (planned) Bind the new Review & Launch control to the shared mutation dispatcher only
  after task-aware workflow entrypoint integrity is restored.
  - Dependencies: `W35-E2-S8`, `W36-E6-S4-T1`.
  - Scope: Guided Setup launch binding only.
  - Verification: Guided and legacy launch controls dispatch an identical task-aware request,
    duplicate input creates at most one job, and durable readback selects one result.
- `W36-E4-S1-T7` (planned) Promote the verified Guided Setup candidate to `parity_closed` while retaining
  legacy setup for both missing/default and explicit rollback modes until cutover.
  - Dependencies: `W36-E4-S1-T6`, `W36-E7-S1-T1`.
  - Scope: Guided Setup parity-manifest entry only.
  - Verification: the required journey passes in the Studio renderer and explicit rollback
    reaches the legacy setup through the same service path.

Exit evidence:

- a first-time operator reaches create or resume before runtime details and optional
  project-set configuration;
- the UI contains no selectable execution mode that dispatches the same generic launch.

#### Slice W36-E4-S2 — dimensioned runtime readiness and safety (`planned`)
Goal: show only runtime readiness and write-scope claims backed by observable evidence.

Dependencies:

- `W36-E1-S2`
- `W34-E4-S2-T1`
- `W34-E4-S3`
- `W34-E7-S1-T2`

Local tasks:

- `W36-E4-S2-T1` (planned) Expose binary, execution-command, authentication, and capability
  readiness dimensions without inferring unavailable evidence.
  - Scope: core runtime readiness read model.
  - Verification: detected, unavailable, auth-verified, auth-failed, auth-unverified,
    and legacy fixtures produce typed dimensions with compatibility fields.
- `W36-E4-S2-T2` (planned) Project the latest per-runtime launch outcome and timestamp from
  canonical attempt evidence.
  - Scope: core operator runtime-history read model.
  - Verification: no-history, success, failure, blocked, cancelled, and legacy attempts
    resolve deterministically without reading outside `.aidd/`.
- `W36-E4-S2-T3` (planned) Render dimensioned readiness, protected write scope, and last-launch
  evidence in Guided Setup and the Studio launch context.
  - Scope: packaged runtime/safety UI.
  - Verification: truth-copy fixtures contain no undifferentiated authentication claim
    or `No upstream write` promise.

Exit evidence:

- `ready` no longer conflates executable discovery, authentication, capability, and
  previous launch outcome;
- the operator sees the actual protected-data/write boundary before execution.

### Epic W36-E5 — Document & Evidence Studio vertical migration (`planned`)
Linked stories: `US-02`, `US-03`, `US-05`, `US-06`, `US-10`, `US-11`, `US-13`

#### Slice W36-E5-S0 — core operator decision foundations (`planned`)
Goal: make terminal recommendation policy available to Inbox and Flow Complete before either
renderer binds a primary action.

Dependencies:

- `W36-E1-S2-T1`
- reuse the accepted terminal-run handoff read model and allowed-outcomes contract

Local tasks:

- `W36-E5-S0-T1` (parked) Add one core-owned `recommended_outcome` and rationale to the terminal-run
  handoff read model without removing the complete allowed-outcomes list.
  - Scope: core terminal handoff recommendation policy only.
  - Verification: clean fresh terminal QA recommends Create New Work Item; fresh failed,
    blocked, or warning QA recommends Start Follow-up Flow; missing, stale, and nonterminal QA
    produce no Flow Complete recommendation.
- `W36-E5-S0-T2` (planned) Expose the recommendation through the existing additive terminal-handoff API
  contract with explicit legacy fallback semantics.
  - Scope: local UI terminal-handoff response contract only.
  - Verification: endpoint fixtures preserve allowed outcomes and source identity while old
    payloads resolve to an explicit no-recommendation compatibility state.

Exit evidence:

- renderer code owns neither terminal eligibility nor recommendation priority;
- Inbox and Flow Complete consume one stable, backward-compatible decision contract.

#### Slice W36-E5-S1 — shared Studio hierarchy and progressive disclosure (`planned`)
Goal: keep the current operator decision and primary document visible while demoting
zero-value and secondary evidence.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- `W36-E3-S3`
- executable behavior verification builds on `W34-E5-S3-T5`

Local tasks:

- `W36-E5-S1-T1` (parked) Add a visibility policy that hides a zero-value Evidence Inspector
  and keeps secondary Filmstrip/log evidence collapsed until requested.
  - Scope: shell rendering policy.
  - Verification: no-run, healthy running, blocked, terminal, and history fixtures show
    only panels with current operator value.
- `W36-E5-S1-T2` (planned) Consolidate duplicate recovery summaries into one Recovery Summary
  inside the Studio Decision Bar with one Evidence link.
  - Scope: recovery rendering.
  - Verification: every blocker fixture exposes one recovery landmark, one primary
    action, and one supporting evidence path.
- `W36-E5-S1-T3` (planned) Implement one policy-free primary-action slot for vertical surfaces to bind
  to their own core/service-provided decision and compact metadata.
  - Scope: shared Decision Bar slot composition only.
  - Verification: surface fixtures can bind one action or an explicit no-action state, while
    the shared layer contains no eligibility, priority, or terminal-recommendation policy.
- `W36-E5-S1-T4` (planned) Move Refresh, Open `.aidd`, Stop server, and other maintenance commands
  into a labelled overflow surface.
  - Scope: shell maintenance controls.
  - Verification: service commands remain keyboard-accessible but no longer precede the
    primary operator task in focus or visual order.
- `W36-E5-S1-T5` (planned) Establish one Studio content scroll owner so the inspector, drawers,
  and Filmstrip create no nested scroll traps on supported desktop viewports.
  - Scope: desktop shell layout.
  - Verification: `1280x900` and `1440x900` fixtures expose one primary vertical scroll
    path while sticky context and drill-down panels remain reachable.

Exit evidence:

- default, empty, and healthy states do not reserve equal visual weight for empty
  Blockers, Recovery, Activity, and Evidence panels;
- the first viewport communicates context, one decision, and the primary work surface.

#### Slice W36-E5-S2 — compact mobile operator shell (`planned`)
Goal: keep the current decision visible on narrow viewports without pretending dense
desktop evidence is a mobile-first surface.

Dependencies:

- `W36-E5-S1`
- `W36-E5-S3-T1..T4`
- `W36-E5-S4-T1..T4`
- `W36-E3-S1`
- `W36-E3-S2`
- `W36-E3-S4`

Local tasks:

- `W36-E5-S2-T1` (parked) Replace the measured `275px` sticky mobile header with a compact
  context/status bar and maintenance overflow.
  - Scope: topbar markup and responsive CSS.
  - Verification: `320x568` and `390x844` fixtures meet the accepted header budget and
    never cover the mode tabs or primary action.
- `W36-E5-S2-T2` (planned) Keep the current Decision Bar or Inbox action in the first mobile
  viewport and move dense evidence to explicit drill-down.
  - Scope: responsive workbench ordering.
  - Verification: no-run Inbox, post-stage, and active Studio fixtures expose the accepted
    primary decision without initial scrolling; vertical Recovery/History/terminal slices own
    their state-specific mobile parity.
- `W36-E5-S2-T3` (planned) Replace repeated per-body-mode ordering selectors with one mobile
  priority layout contract: context -> decision -> document -> evidence/history drill-down.
  - Scope: responsive shell state classes.
  - Verification: every declared operator state maps to the same context -> decision ->
    document -> evidence/history drill-down ordering rule.
- `W36-E5-S2-T4` (planned) Keep compact stage navigation and primary labels legible at `320px` and
  `390px` without rendering the desktop stage rail as a tiny grid.
  - Scope: responsive stage rail and label wrapping.
  - Verification: shared touch targets pass, no active stage or primary label clips,
    and document scroll width equals viewport width.

Exit evidence:

- mobile monitoring, answers, approvals, recovery, and next decisions are first-viewport
  tasks;
- dense diff, graph, and history views remain reachable through deliberate drill-downs.

#### Slice W36-E5-S3 — project-local Inbox (`planned`)
Goal: replace Project Home/dashboard scanning with a core-owned, bounded decision queue for
the selected project root.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- `W36-E2-S3`
- `W36-E3-S3`
- `W36-E5-S0`
- Inbox routing consumes `W36-E6-S1-T1..T2`
- reuse the accepted Wave 31 project-home, next-action, blocker, and first-failure read models

Local tasks:

- `W36-E5-S3-T1` (parked) Implement a typed core-owned durable Inbox projection with Needs your
  decision, Ready to continue, and Flow complete sections.
  - Scope: core operator frontend read models only.
  - Verification: provider-free fixtures prove deterministic priority, exact work-item/run/stage
    references, one core-approved action, and no frontend-derived eligibility or live-job claim.
- `W36-E5-S3-T2` (planned) Add typed work-item/run/stage correlation to bounded UI job summaries and
  compose the project-local Running now overlay without changing durable Inbox eligibility.
  - Dependencies: `W34-E3-S3-T1`.
  - Scope: CLI UI job summary and Inbox composition service only.
  - Verification: zero, one, concurrent, terminal, evicted, and legacy job fixtures produce a
    bounded Running now section whose references agree with durable run state.
- `W36-E5-S3-T3` (planned) Expose the composed Inbox through an additive local UI read endpoint with
  bounded project-local data.
  - Scope: CLI UI read route and response contract only.
  - Verification: endpoint tests cover empty, blocking, running, ready, terminal, legacy, and
    malformed evidence without arbitrary path access.
- `W36-E5-S3-T4` (planned) Render Inbox sections and route each item to the exact Studio context through
  the shared action/state seam.
  - Scope: packaged Inbox renderer only.
  - Verification: one browser fixture per section opens the expected work item, run, stage,
    artifact/evidence detail, and primary action.
- `W36-E5-S3-T5` (planned) Promote the verified Inbox candidate to `parity_closed` while retaining legacy
  Project Home for both missing/default and explicit rollback modes until cutover.
  - Dependencies: `W36-E7-S1-T12`.
  - Scope: Inbox parity-manifest entry only.
  - Verification: `ui=studio` exposes no duplicate decision, while missing/default and
    `ui=legacy` preserve Project Home through the same read/action seam until cutover.

Exit evidence:

- the first actionable item and its primary action are visible without scrolling;
- Inbox is a rebuildable read model and cannot become a second workflow engine;
- blocking items cannot be hidden by presentation-only dismissal.

#### Slice W36-E5-S4 — active Document & Evidence Studio (`planned`)
Goal: make context, one Decision Bar, the selected Markdown document, and bounded evidence the
default active-run workspace.

Dependencies:

- `W36-E1-S2`
- `W36-E2-S3`
- `W36-E3`
- `W36-E5-S1`
- `W36-E6-S1-T1..T2`
- `W36-E6-S4-T1`
- `W34-E5-S3-T5`

Local tasks:

- `W36-E5-S4-T1` (parked) Compose the active Studio view from shared mode navigation, compact context
  bar, canonical stage navigation, and Decision Bar slots.
  - Scope: packaged active-Studio markup and renderer only.
  - Verification: no-run, active, blocked, and terminal fixtures preserve context and expose
    exactly one primary action across supported desktop viewports.
- `W36-E5-S4-T2` (planned) Render the read-only Document Canvas with Preview, Source, and Diff over the
  existing safe workbench/document endpoints.
  - Scope: packaged document renderer only.
  - Verification: Markdown, source, diff, missing, malformed, and truncated fixtures retain
    semantics, copyability, safe keys, and document-first visual priority.
- `W36-E5-S4-T3` (planned) Render the conditional Evidence Inspector with finding, provenance, related
  artifact, and exact source-reference variants.
  - Scope: packaged evidence renderer only.
  - Verification: zero-value evidence hides the inspector while validator, provenance,
    implementation, and legacy fixtures show only retained evidence.
- `W36-E5-S4-T4` (planned) Integrate live elapsed time, last-output age, real milestones, silence state,
  and Open live output into Studio without embedding raw logs in the default viewport.
  - Dependencies: `W36-E6-S3`.
  - Scope: active Studio observation renderer only.
  - Verification: running, silent, cancelling, completed, and externally completed jobs show no
    fake progress and agree with persisted runtime evidence.
- `W36-E5-S4-T5` (planned) Promote the verified active-Studio candidate to `parity_closed` while retaining
  the legacy cockpit/sidebar renderer for missing/default and explicit rollback until cutover.
  - Dependencies: `W36-E7-S1-T2`, `W36-E7-S1-T7`.
  - Scope: active-Studio parity-manifest entry only.
  - Verification: `ui=studio` contains no duplicate workbench, while missing/default and
    `ui=legacy` retain artifact, question, recovery, and live-log reachability until cutover.

Exit evidence:

- the first desktop viewport contains context, one current decision, and the primary document;
- generated evidence remains read-only and corrections retain durable audited paths;
- stage progression and attempt history remain distinct concepts.

#### Slice W36-E5-S5 — human-decision Recovery Studio (`planned`)
Goal: migrate questions, interventions, and runtime approvals into one contextual decision
surface without conflating their durable semantics.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S2`
- `W36-E6-S4`
- approval replacement depends on `W34-E3-S2`

Local tasks:

- `W36-E5-S5-T1` (parked) Render blocking questions with exact QID, resolved/partial/deferred status,
  draft recovery, and answer-and-resume behavior.
  - Scope: question Recovery renderer only.
  - Verification: resolved unblocks, partial/deferred remain blocking when required, failed
    submit preserves the draft, and durable `answers.md` readback wins.
- `W36-E5-S5-T2` (planned) Render Request Change and intervention context as durable stage-scoped input,
  including downstream-success rejection and remediation routing.
  - Scope: intervention Recovery renderer only.
  - Verification: allowed submit creates one operator-request document and blocked intervention
    creates none while preserving the selected stage/run.
- `W36-E5-S5-T3` (planned) Render runtime approval scope, breadth, reason, risk, pending state, session
  confirmation, and durable winning decision separately from product questions.
  - Scope: approval Recovery renderer only.
  - Verification: allow/deny/cancel/conflict fixtures agree with the compare-and-set audit row and
    no broad approval posts before confirmation.
- `W36-E5-S5-T4` (planned) Implement the decision-first mobile question and approval layouts with compact
  context, 44px controls, and evidence drill-down.
  - Dependencies: `W36-E5-S2`.
  - Scope: human-decision responsive presentation only.
  - Verification: `320x568` and `390x844` keyboard/touch journeys expose the full decision and
    primary submit without horizontal overflow or initial scroll.
- `W36-E5-S5-T5` (planned) Promote the verified question candidate to `parity_closed` while retaining the
  legacy question renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T6`.
  - Scope: question parity-manifest entry only.
  - Verification: the question fixture closes independently and durable answer/resume behavior
    is equivalent in `ui=studio`, missing/default, and `ui=legacy` modes.
- `W36-E5-S5-T6` (planned) Promote the verified intervention candidate to `parity_closed` while retaining
  the legacy intervention renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T10`.
  - Scope: intervention parity-manifest entry only.
  - Verification: allowed and blocked intervention fixtures close independently with identical
    durable request behavior.
- `W36-E5-S5-T7` (planned) Promote the verified approval candidate to `parity_closed` while retaining the
  legacy approval renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T11`.
  - Scope: approval parity-manifest entry only.
  - Verification: allow, deny, cancel, session, and conflict fixtures close independently and
    preserve the same compare-and-set winner.

Exit evidence:

- question answers, runtime approvals, and intervention requests remain distinct durable paths;
- every human blocker exposes one decision, one evidence path, and truthful readback.

#### Slice W36-E5-S6 — runtime and validation Recovery Studio (`planned`)
Goal: surface the first decisive runtime or validation failure with the one eligible recovery
action and exact retained evidence.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S3`
- `W34-E3-S3-T1`
- `W34-E4-S2`

Local tasks:

- `W36-E5-S6-T1` (parked) Render runtime/provider failure, stopped state, last durable signal, and
  eligible retry without consuming or implying validation repair budget.
  - Scope: runtime-failure Recovery renderer only.
  - Verification: unavailable executable, authentication, timeout, cancellation, no-progress,
    and legacy fixtures show the typed outcome and correct safe action.
- `W36-E5-S6-T2` (planned) Render transient offline, reconnecting, recovered, expired-job, and manual
  Reconnect states while preserving durable log/artifact access.
  - Scope: connection Recovery renderer only.
  - Verification: cursor-preserving failure/recovery fixtures show no skipped or duplicated
    chunks and never claim runtime termination without server evidence.
- `W36-E5-S6-T3` (planned) Render validation findings with exact document/line/rule/provenance and make
  Run Repair primary only when the backend reports repair available.
  - Scope: validation Recovery renderer only.
  - Verification: repair-available, repaired, exhausted, explicit-stop, stale-artifact, and
    malformed-report fixtures choose the correct action and evidence.
- `W36-E5-S6-T4` (planned) Render Request Change as primary after repair exhaustion/explicit stop and keep
  raw logs/attempt history as secondary drill-down.
  - Scope: repair-exhaustion Recovery renderer only.
  - Verification: no exhausted state exposes an enabled Run Repair and the intervention request
    retains the selected run/stage context.
- `W36-E5-S6-T5` (planned) Implement decision-first mobile runtime and validation Recovery layouts over
  the shared compact shell.
  - Dependencies: `W36-E5-S2`.
  - Scope: failure/recovery responsive presentation only.
  - Verification: `320x568` and `390x844` show the typed failure, one eligible recovery action,
    and evidence drill-down without horizontal overflow or initial decision scroll.
- `W36-E5-S6-T6` (planned) Promote the verified runtime/validation candidates to `parity_closed` while
  retaining legacy failure cards for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T3`.
  - Scope: runtime/validation parity-manifest entries only.
  - Verification: both entries close and first-failure, repair-history, raw-log, and request
    paths remain equivalent in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- runtime failure, validation repair, and human correction remain truthful distinct paths;
- recovery never silently progresses or invents missing evidence.

#### Slice W36-E5-S7 — implement, Review, and QA quality gates (`planned`)
Goal: migrate task execution, repository evidence, Review findings, QA verdict, remediation,
and stale downstream recovery without weakening task-aware eligibility.

Dependencies:

- `W35-E2-S8`
- `W36-E5-S4`
- `W36-E6-S2`
- `W36-E6-S4`

Local tasks:

- `W36-E5-S7-T1` (parked) Render dependency-ready tasks, task attempts, blocked/failed recovery, and
  aggregate finalization inside Studio from the canonical task read model.
  - Scope: implement task workspace renderer only.
  - Verification: run/resume/fail/recover/finalize fixtures preserve successful tasks and never
    enable Review before successful aggregate finalization.
- `W36-E5-S7-T2` (planned) Render the real repository diff, untracked/deleted files, `.aidd/` separation,
  scope status, and implementation-report claim mismatch in the Document Canvas.
  - Scope: implement evidence renderer only.
  - Verification: repository-diff fixtures match core evidence and use textual added/removed/
    changed meaning in addition to color.
- `W36-E5-S7-T3` (planned) Render structured Review findings and QA verdict, residual risks, known issues,
  acceptance ids, and evidence links.
  - Scope: Review/QA quality-gate renderer only.
  - Verification: approval/rejection/not-ready/blocked/missing-evidence fixtures agree with the
    canonical reports and validators.
- `W36-E5-S7-T4` (planned) Render selected remediation to `implement`, pending readback, and explicit
  downstream Review/QA stale rerun.
  - Scope: quality-gate remediation renderer only.
  - Verification: one durable remediation request is created, fresh downstream stages become
    stale, stale QA never becomes terminal, and rerun uses the selected runtime.
- `W36-E5-S7-T5` (planned) Promote the verified implement/Review/QA candidates to `parity_closed` while
  retaining legacy surfaces for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T4`, `W36-E7-S1-T9`.
  - Scope: task/quality-gate parity-manifest entries only.
  - Verification: entries close while task ledger, finalization, diff, findings, remediation,
    stale-state, `ui=studio`, missing/default, and `ui=legacy` tests remain green.

Exit evidence:

- every Review/QA claim remains bound to task and repository evidence;
- no UI entrypoint bypasses the task ledger or aggregate finalization gate.

#### Slice W36-E5-S8 — History Filmstrip and retained evidence (`planned`)
Goal: expose causal attempt/task history, comparison, lineage, and archive state using only
durably retained evidence.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S1`
- `W34-E2-S2-T2`
- comparison/accountability consume `W34-E2-S3-T2`
- archive presentation consumes `W34-E2-S3-T1`

Local tasks:

- `W36-E5-S8-T1` (parked) Implement a typed Filmstrip frame projection for stage attempts, task
  attempts, and aggregate finalization milestones with events as markers.
  - Scope: core operator timeline/read model only.
  - Verification: normal, repair, intervention, remediation, task, finalization, live, and
    legacy fixtures produce stable frame identity and retain the first decisive failure.
- `W36-E5-S8-T2` (planned) Render the collapsed Studio Filmstrip and expanded History timeline with
  selected artifact/log evidence and Return to live behavior.
  - Scope: packaged Filmstrip/History renderer only.
  - Verification: frame selection, historical auto-follow pause, exact log range, missing
    snapshot, and current-live return behave deterministically.
- `W36-E5-S8-T3` (planned) Render run comparison plus retained prompt, artifact, stage, and validator
  deltas.
  - Scope: History comparison renderer only.
  - Verification: Back/reload restores both runs and every displayed delta links to retained
    source evidence or an explicit unavailable-snapshot state.
- `W36-E5-S8-T4` (planned) Render parent, source, and child run lineage without presenting lineage as
  mutable workflow state.
  - Scope: History lineage renderer only.
  - Verification: every routable relation resolves through canonical run identity and opening a
    relation leaves both source and target manifests byte-identical.
- `W36-E5-S8-T5` (planned) Render archive state as the append-only overlay owned by `W34-E2-S3-T1`.
  - Scope: History archive-state renderer only.
  - Verification: archive inspection changes no completed-run bytes/hashes and all retained
    documents, logs, comparison, and lineage remain inspectable.
- `W36-E5-S8-T6` (planned) Render Filmstrip as a vertical chronological mobile drill-down rather than a
  horizontal scroll trap.
  - Dependencies: `W36-E5-S2`.
  - Scope: History responsive presentation only.
  - Verification: `320x568` and `390x844` expose frame status, evidence action, and return path
    without page-level horizontal overflow.
- `W36-E5-S8-T7` (planned) Promote the verified History candidate to `parity_closed` while retaining the
  legacy timeline/history renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T5`.
  - Scope: History parity-manifest entry only.
  - Verification: the entry closes and timeline, comparison, lineage, archive, and raw evidence
    remain reachable in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- History never implies a document/repository snapshot that was not retained;
- stage progression, causal attempts, and run lineage remain distinguishable and routable.

#### Slice W36-E5-S9 — Flow Complete and independent next outcomes (`planned`)
Goal: make fresh terminal QA produce an immutable handoff with one recommended disposition and
all secondary outcomes behind progressive disclosure.

Dependencies:

- `W36-E5-S0`
- `W36-E5-S7`
- `W36-E5-S8`
- `W36-E6-S2`
- `W36-E6-S4`
- `W34-E2-S3-T1`
- `W34-E3-S4-T4`

Local tasks:

- `W36-E5-S9-T3` (planned) Render immutable Flow Complete evidence, the core recommendation, and Other next
  actions only for fresh eligible terminal QA.
  - Scope: terminal handoff renderer only.
  - Verification: clean, failed, blocked, and warning fresh terminal fixtures show the exact
    core recommendation; missing, stale, and nonterminal QA do not render Flow Complete.
- `W36-E5-S9-T4` (planned) Render follow-up definition, inherited context, source evidence, preflight, and
  launch through the shared draft/mutation seams.
  - Scope: follow-up next-flow renderer only.
  - Verification: Back/reload/failure/retry preserve the follow-up draft, successful launch
    creates one new work-item/run identity, and the source run remains byte-identical.
- `W36-E5-S9-T5` (planned) Render clone definition, inherited context, source evidence, preflight, and
  launch through the shared draft/mutation seams.
  - Scope: clone next-flow renderer only.
  - Verification: Back/reload/failure/retry preserve the clone draft, successful launch creates
    one independent identity, and the source run remains byte-identical.
- `W36-E5-S9-T6` (planned) Render the existing Run Eval / Scenario Batch manual handoff as a non-repair
  comparison disposition under Other next actions.
  - Scope: terminal eval handoff renderer only; no new mutation endpoint.
  - Verification: the action opens exact source/version/scenario context and operator commands,
    sends no workflow mutation request, and leaves source-run evidence unchanged.
- `W36-E5-S9-T7` (planned) Render Archive Run as an append-only visibility disposition under Other next
  actions.
  - Scope: terminal archive disposition renderer only.
  - Verification: archive writes only the owned overlay and completed documents, artifacts,
    logs, comparison, and lineage remain inspectable.
- `W36-E5-S9-T8` (planned) Render the recommended next decision and Other next actions as a compact mobile
  drill-down over the shared responsive shell.
  - Dependencies: `W36-E5-S2`.
  - Scope: Flow Complete responsive presentation only.
  - Verification: `320x568` and `390x844` show final status, one recommendation, and a reachable
    secondary-outcomes disclosure without horizontal overflow or initial decision scroll.
- `W36-E5-S9-T9` (planned) Promote the verified Flow Complete candidate to `parity_closed` while retaining
  the equal-weight legacy action grid/wizard for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T8`.
  - Scope: terminal/next-flow parity-manifest entry only.
  - Verification: the parity entry closes and all accepted outcomes remain keyboard-reachable
    with distinct service semantics in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- completed source runs remain immutable;
- one recommended outcome leads, while all accepted independent outcomes remain reachable.

#### Slice W36-E5-S10 — default cutover and legacy removal (`planned`)
Goal: make Studio the only maintained renderer after a bounded rollback window and delete
presentation code that no longer owns a supported surface.

Dependencies:

- `W36-E4-S1-T7`
- `W36-E5-S3-T5`, `W36-E5-S4-T5`, `W36-E5-S5-T5..T7`, `W36-E5-S6-T6`,
  `W36-E5-S7-T5`, `W36-E5-S8-T7`, and `W36-E5-S9-T9`
- `W36-E7-S1-T1..T12`
- `W36-E7-S2-T1`

Local tasks:

- `W36-E5-S10-T1` (parked) Switch the missing/default presentation selector to Studio after every
  per-surface parity entry is closed while retaining explicit `ui=legacy` rollback.
  - Scope: packaged renderer default only.
  - Verification: the full provider-free browser command passes in default Studio mode and the
    explicit rollback renderer still dispatches identical service actions.
- `W36-E5-S10-T2` (planned) Record one source-installed rollback-window pass while both presentation
  selectors remain supported.
  - Scope: cutover evidence only.
  - Verification: isolated fixture copies prove equivalent endpoint/payload semantics and
    normalized outcomes in default and rollback modes; immutable source-run evidence remains
    byte-identical where the journey contract requires it.
- `W36-E5-S10-T3` (planned) Remove the temporary legacy selector when no accepted journey requires it.
  - Scope: browser bootstrap selector only.
  - Verification: missing, invalid, and former legacy selector values resolve to Studio without
    changing packaged URLs, service requests, or durable state.
- `W36-E5-S10-T4` (planned) Remove unreferenced legacy render modules, selectors, body-mode ordering,
  package resources, and compatibility tests that no longer protect a supported contract.
  - Scope: packaged frontend cleanup only.
  - Verification: exhaustive asset discovery, JavaScript syntax, package-resource, DOM, and
    browser suites pass with no legacy renderer references.
- `W36-E5-S10-T5` (planned) Reconcile operator docs and screenshots to the Studio-only surface after
  implementation parity.
  - Scope: README, handbook, local-project E2E, and architecture implementation-status text.
  - Verification: docs consistency finds no current-behavior claim or image that points to the
    removed renderer while historical assets remain clearly non-normative.

Exit evidence:

- `aidd ui` opens Studio through stable packaged assets and existing service semantics;
- no duplicate renderer, action dispatcher, or dead legacy selector remains;
- rollback evidence exists without retaining a permanent second frontend.

### Epic W36-E6 — durable navigation, drafts, reconnect, and action integrity (`planned`)
Linked stories: `US-05`, `US-06`, `US-10`, `US-11`

#### Slice W36-E6-S1 — URL-backed work-item and run navigation (`planned`)
Goal: make reload, Browser Back, deep links, and lineage navigation preserve the selected
operator context.

Dependencies:

- `W36-E1-S1-T3`
- `W34-E2-S2-T2`
- archive navigation consumes `W34-E2-S3-T1`

Local tasks:

- `W36-E6-S1-T1` (done) Add a URL-state codec for Inbox / Studio / History mode, work item,
  run, stage, attempt or task-attempt detail, and artifact selection.
  - Scope: packaged browser state module.
  - Verification: round-trip, missing, legacy, stale, and invalid-value cases resolve to
    safe deterministic state.
- `W36-E6-S1-T2` (done) Wire push, replace, popstate, and reload restoration through the URL
  codec across Inbox, Studio, History, and contextual drawers.
  - Scope: shell navigation controller.
  - Verification: a browser history sequence preserves Logs versus Artifacts, selected
    stage, selected run, and artifact drill-down across Back, Forward, and reload.
- `W36-E6-S1-T3` (next) Define shared route intents for Inbox work-item, historical-run, parent, and
  child-lineage bindings without owning their vertical renderers.
  - Scope: URL/navigation intent controller only.
  - Verification: E5-owned Inbox and History fixtures bind each visible action to one distinct
    route outcome, and archived runs retain artifact/history inspection.

Exit evidence:

- operator location survives reload and browser navigation;
- Inbox and History no longer expose different labels for the same action.

#### Slice W36-E6-S2 — browser-session draft and dirty-state safety (`planned`)
Goal: preserve unsaved operator input across UI navigation without treating drafts as
canonical workflow evidence.

Dependencies:

- `W36-E1-S1`
- `W36-E3-S2`
- next-flow adoption depends on `W34-E3-S4-T4`

Local tasks:

- `W36-E6-S2-T1` (soon) Define the key, retention, and cleanup contract for noncanonical
  browser-session drafts.
  - Scope: operator frontend architecture only.
  - Verification: the contract isolates project, work item, run, stage, form, and source
    id and names exact submit/expiry cleanup behavior.
- `W36-E6-S2-T4` (planned) Implement the scoped noncanonical browser-session draft store.
  - Dependencies: `W36-E6-S2-T1`.
  - Scope: shared packaged JavaScript state utility only.
  - Verification: contract fixtures isolate every key dimension and successful submit
    clears only the owning draft.
- `W36-E6-S2-T2` (planned) Adopt draft restore and leave-warning behavior for question and
  intervention forms.
  - Dependencies: `W36-E6-S2-T4`.
  - Scope: question/intervention browser modules.
  - Verification: stage/tab switch, reload, failed submit, and successful submit preserve
    or clear the expected draft only.
- `W36-E6-S2-T3` (planned) Adopt draft restore and leave-warning behavior for follow-up and clone
  definition forms.
  - Dependencies: `W36-E6-S2-T4`.
  - Scope: next-flow browser controller.
  - Verification: wizard Back, reload, preflight failure, retry, and successful launch
    preserve or clear the expected draft.

Exit evidence:

- changing stage, mode, run, or wizard step cannot silently discard unsaved operator
  text;
- draft state never becomes canonical `answers.md`, intervention, or next-flow evidence
  before explicit submission.

#### Slice W36-E6-S3 — reconnecting live observation (`planned`)
Goal: recover live monitoring after transient API failure without losing log position or
misrepresenting the runtime as stopped.

Dependencies:

- `W34-E3-S3-T1`
- `W34-E5-S3-T5`
- `W36-E3-S3-T2`

Local tasks:

- `W36-E6-S3-T1` (parked) Replace terminal-on-error interval polling with a cursor-preserving
  retry state machine and bounded exponential backoff.
  - Scope: `operator-logs-jobs.js` polling controller.
  - Verification: failure -> retry -> recovery, repeated failure, cancellation, and
    terminal-job sequences produce no duplicate or skipped chunks.
- `W36-E6-S3-T2` (planned) Render offline, reconnecting, recovered, expired-job, and manual
  Reconnect states.
  - Scope: live connection status surface.
  - Verification: each sequence names whether the runtime may still be running and
    offers the correct local recovery action.
- `W36-E6-S3-T3` (planned) Reconcile active job, dashboard, logs, and selected stage after
  recovery or terminal-job eviction.
  - Scope: browser state reconciliation.
  - Verification: reconnect and eviction fixtures converge on the server-authoritative
    state while retaining durable log/artifact access.

Exit evidence:

- a transient local API failure cannot silently stop monitoring;
- reconnect and eviction states remain truthful about runtime ownership and durable
  evidence.

#### Slice W36-E6-S4 — client mutation and approval integrity (`planned`)
Goal: give every mutating control an immediate pending state and reconcile conflicts to
the single durable server outcome.

Dependencies:

- `W34-E3-S1-T2` for keyed server admission and deterministic mutation conflicts;
- approval tasks depend on `W34-E3-S2`;
- next-flow adoption depends on `W34-E3-S4-T4`.

Local tasks:

- `W36-E6-S4-T1` (parked) Add a shared keyed client mutation guard with pending lock, duplicate
  suppression, conflict readback, and retryable failure state.
  - Scope: packaged API/state utility.
  - Verification: double-click and concurrent-control fixtures send one request per key
    and preserve a retry path after failure.
- `W36-E6-S4-T2` (planned) Adopt the mutation guard for workflow, stage, and remediation launch
  controls.
  - Scope: run mutation controls.
  - Verification: pending, same-run conflict, different-run concurrency, failure, and
    success states match server admission.
- `W36-E6-S4-T3` (planned) Adopt the mutation guard for answer and intervention writes.
  - Scope: question/intervention mutation controls.
  - Verification: failed writes retain drafts, successful writes clear drafts, and
    duplicate submissions create one durable artifact.
- `W36-E6-S4-T4` (planned) Adopt the mutation guard for next-flow draft, preflight, and launch.
  - Dependencies: `W34-E3-S4-T4`.
  - Scope: next-flow browser controller.
  - Verification: repeated actions cannot create duplicate work items or runs and the
    source run remains unchanged after failure.
- `W36-E6-S4-T5` (planned) Add approval reason capture and explicit confirmation for
  `allow_for_session` with controls disabled while submitting.
  - Dependencies: `W34-E3-S2`.
  - Scope: approval decision UI.
  - Verification: no session-wide approval POST occurs before confirmation and the
    submitted reason/breadth remain visible in the preview.
- `W36-E6-S4-T6` (planned) Reconcile approval compare-and-set or terminal conflicts to the durable
  winning decision and audit row.
  - Dependencies: `W34-E3-S2`.
  - Scope: approval conflict UI.
  - Verification: concurrent opposite decisions display one server-authoritative winner
    and no stale pending controls.

Exit evidence:

- UI controls cannot create duplicate local mutations through repeated input;
- runtime approval breadth is explicit and the UI/audit view agrees with the durable
  compare-and-set winner.

### Epic W36-E7 — executable UX acceptance and rollout evidence (`planned`)
Linked stories: `US-07`, `US-09`, `US-11`, `US-12`, `US-13`

#### Slice W36-E7-S1 — canonical operator browser journeys (`planned`)
Goal: prove the critical operator jobs through provider-free rendered journeys rather
than isolated asset and endpoint assertions.

Dependencies:

- `W36-E2`
- `W36-E1-S2-T3`

Local tasks:

- `W36-E7-S1-T1` (parked) Add the Guided Setup project validation, create/resume, runtime review,
  first launch, and resulting Inbox entry browser journey.
  - Dependencies: `W36-E4-S1-T1..T6`, `W36-E4-S2`, `W36-E5-S2`,
    `W36-E5-S3-T1..T4`.
  - Scope: onboarding browser scenario family.
  - Verification: every required viewport completes create or resume with one primary
    action, no geometry/accessibility failure, and no provider authentication.
- `W36-E7-S1-T2` (planned) Add the active Studio running, silence, cancellation, transient
  reconnect, and return-to-live browser journey.
  - Dependencies: `W36-E5-S2`, `W36-E5-S4-T1..T4`, `W36-E6-S3`.
  - Scope: live Studio browser scenario family.
  - Verification: real milestones, last output, cursor recovery, cancel lifecycle, and
    durable logs pass without console/network ambiguity or fake progress.
- `W36-E7-S1-T3` (planned) Add the Runtime/Validation Recovery Studio repair/exhaustion browser
  journey.
  - Dependencies: `W36-E5-S6-T1..T5`.
  - Scope: runtime/validation recovery scenario family.
  - Verification: each failure exposes the correct first evidence, one primary recovery
    action, and a truthful stopped/running state.
- `W36-E7-S1-T4` (planned) Add the Review/QA quality-gate, remediation, and stale downstream
  browser journey.
  - Dependencies: `W35-E2-S8`, `W36-E5-S7-T2..T4`.
  - Scope: delivery-decision browser scenario family.
  - Verification: unsafe completion remains blocked, remediation/rerun is explicit, and stale
    QA keeps Flow Complete absent until a later fresh-QA journey proves terminal eligibility.
- `W36-E7-S1-T5` (planned) Add the History Filmstrip, comparison, lineage, and archive browser
  journey.
  - Dependencies: `W36-E5-S8-T1..T6`.
  - Scope: history and continuation browser scenario family.
  - Verification: Back/reload/deep links preserve run identity and completed source-run
    artifacts remain immutable and inspectable.
- `W36-E7-S1-T6` (planned) Add the blocking-question answer/resume Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T1`, `W36-E5-S5-T4`.
  - Scope: product-question browser scenario family.
  - Verification: draft restore, resolved/partial/deferred state, failed/successful durable
    readback, answer/resume, and current run/stage context pass on desktop and mobile.
- `W36-E7-S1-T7` (planned) Add the Document Canvas and Evidence Inspector browser journey.
  - Dependencies: `W36-E5-S4-T2..T3`.
  - Scope: document/evidence browser scenario family.
  - Verification: Preview/Source/Diff, safe artifact selection, validator provenance,
    missing evidence, zero-value hiding, and raw-log drill-down pass without arbitrary
    path reads.
- `W36-E7-S1-T8` (planned) Add the Flow Complete, follow-up, clone, eval, and archive disposition
  browser journey.
  - Dependencies: `W36-E5-S0`, `W36-E5-S9-T3..T8`.
  - Scope: terminal and next-outcome browser scenario family.
  - Verification: clean versus failed/blocked/warning fresh QA, stale/nonterminal exclusion,
    one core-recommended action, drafts/preflight, independent identities, truthful manual eval
    handoff, archive overlay, and byte-identical source-run evidence all pass.
- `W36-E7-S1-T9` (planned) Add the implement task run/resume, failed-attempt recovery, repository
  evidence, and aggregate-finalization browser journey.
  - Dependencies: `W35-E2-S8`, `W36-E5-S7-T1..T4`.
  - Scope: task-aware implement browser scenario family.
  - Verification: dependency readiness, preserved successes, diff/scope evidence,
    finalization recovery, and Review eligibility agree with the canonical task ledger.
- `W36-E7-S1-T10` (planned) Add the Request Change/intervention Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T2`, `W36-E5-S5-T4`.
  - Scope: intervention browser scenario family.
  - Verification: draft restore, allowed request, downstream-success rejection, one durable
    operator request, remediation routing, and current run/stage context pass.
- `W36-E7-S1-T11` (planned) Add the runtime-approval Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T3`, `W36-E5-S5-T4`.
  - Scope: runtime-approval browser scenario family.
  - Verification: allow, deny, cancel, session confirmation, pending state, compare-and-set
    conflict, durable winner, and current run/stage context pass on desktop and mobile.
- `W36-E7-S1-T12` (planned) Add the project-local Inbox priority and routing browser journey.
  - Dependencies: `W36-E5-S0`, `W36-E5-S2`, `W36-E5-S3-T1..T4`.
  - Scope: Inbox browser scenario family.
  - Verification: Needs your decision, Running now, Ready to continue, and Flow complete
    fixtures preserve deterministic order, one core-approved action, exact Studio routing,
    first-viewport visibility, keyboard navigation, and blocking-item non-dismissal.

Exit evidence:

- every high-value operator job has an executable rendered journey across its supported
  viewports;
- browser scenarios prove task completion, not only page/API reachability.

#### Slice W36-E7-S2 — enforced packaged-UI gate (`planned`)
Goal: make every declared browser journey executable in the maintained deterministic
quality lane.

Dependencies:

- `W36-E7-S1`
- `W34-E5-S3`

Local tasks:

- `W36-E7-S2-T1` (planned) Add one command that discovers and executes every declared packaged-UI
  browser scenario.
  - Scope: local/CI UI test entry point.
  - Verification: discovered scenario ids equal executed scenario ids exactly and live
    provider manifests are rejected.
- `W36-E7-S2-T2` (planned) Add the packaged-UI browser command to CI.
  - Dependencies: `W36-E7-S2-T1`.
  - Scope: deterministic CI integration only.
  - Verification: an intentional geometry, accessibility, console, or journey failure
    blocks CI while provider credentials remain unnecessary.
- `W36-E7-S2-T3` (planned) Update the local-project UI evidence template for full browser passes.
  - Dependencies: `W36-E7-S2-T1`.
  - Scope: operator E2E documentation only.
  - Verification: docs consistency and the evidence checklist record version, fixture,
    viewports, journeys, accessibility, console/network state, and cleanup.
- `W36-E7-S2-T4` (planned) Add the packaged-UI browser command to release preflight.
  - Dependencies: `W36-E7-S2-T2`.
  - Scope: deterministic release-preflight integration only.
  - Verification: an intentional browser journey failure blocks release preparation
    without provider credentials.
- `W36-E7-S2-T5` (planned) Record one source-installed full provider-free browser pass.
  - Dependencies: `W36-E7-S2-T1`, `W36-E7-S2-T3`.
  - Scope: manual operator browser evidence only.
  - Verification: one completed template records version, fixtures, viewports, journeys,
    accessibility, console/network state, and cleanup.

Exit evidence:

- packaged UI regressions cannot pass through static string contracts alone;
- release evidence includes one complete provider-free rendered operator pass.

#### Slice W36-E7-S3 — observed first-time-operator acceptance (`planned`)
Goal: verify that the simplified UI is understandable to operators who did not implement
it.

Dependencies:

- `W36-E7-S2`
- `W36-E1-S2-T3`

Local tasks:

- `W36-E7-S3-T1` (planned) Write the observed operator task script and scoring template for
  Guided Setup, Inbox triage, active Studio monitoring, question recovery, runtime
  failure, QA remediation, History inspection, and terminal continuation.
  - Scope: operator acceptance documentation.
  - Verification: every task records completion, elapsed time, wrong actions, assistance,
    confidence, and first decisive confusion.
- `W36-E7-S3-T2` (planned) Record five first-time-operator sessions against the source-installed
  packaged UI.
  - Scope: manual operator acceptance evidence.
  - Verification: one anonymized report contains all required task metrics, browser and
    viewport context, blockers, and no sensitive project/runtime evidence.
- `W36-E7-S3-T3` (planned) Reconcile accepted session findings into roadmap tasks and beta-readiness
  evidence.
  - Scope: planning and product-readiness docs.
  - Verification: every reportable finding is closed, deferred with rationale, or mapped
    to a reviewable roadmap task before beta UX is claimed.

Exit evidence:

- task success and operator confidence confirm the UI hierarchy instead of relying only
  on implementer-authored checks.

Wave 36 exit evidence:

- Guided Setup, Inbox, active Studio, contextual Recovery/Evidence, History, and Flow
  Complete each expose one primary decision and bounded supporting evidence;
- all eight accepted reference screens map to an implemented surface and executable
  journey, with the written architecture contract winning over generated text;
- the Studio renderer is the only maintained default and no duplicate legacy renderer,
  action dispatcher, or dead selector remains after the bounded rollback window;
- no selectable control promises behavior that its service call does not perform;
- runtime readiness, authentication evidence, write scope, connectivity, and approval
  breadth are truthfully distinguished;
- transient polling failures recover without losing log position or silently abandoning
  monitoring;
- unsaved operator input survives supported navigation and never becomes canonical
  evidence before submission;
- `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900` browser journeys pass
  geometry, interaction, console/network, and accessibility assertions;
- five observed first-time-operator sessions meet the accepted completion/confidence bar
  or leave explicit follow-up tasks before beta UX is claimed;
- no Wave 34 backend responsibility is duplicated inside Wave 36.

Sync notes:

- `2026-07-13` The unstarted operator UX plan was renumbered from Wave 35 to Wave 36
  when the incremental-task Wave 35 was integrated. The accepted-contract entry task
  was initially visible in `Soon`; selected browser-foundation, design-system,
  onboarding, responsive-shell, navigation, draft, reconnect, mutation/approval, and
  acceptance entry tasks were placed in `Parking lot`. Server-side mutation, approval,
  retention, runtime-evidence, run-identity, archive, DOM-test, and next-flow-split
  foundations remain owned by Wave 34 and are consumed through explicit dependencies.
- `2026-07-14` Queue reconciliation deliberately moved `W36-E1-S1-T1` to `Parking lot`
  while Wave 35 entrypoint integrity and the ready Wave 34 foundations remain the active
  correction path.
- `2026-07-14` The accepted Document & Evidence Studio contract and eight reference screens
  replaced Mission Control as the target design. `W36-E1-S1-T1` and `W36-E1-S1-T2` are now
  complete; Wave 36 retains its id and becomes the canonical migration wave rather than
  duplicating the work in a new wave. The plan adds a presentation-only strangler seam,
  vertical Inbox/Studio/Recovery/History/Flow Complete slices, per-surface browser parity,
  and bounded legacy cutover while keeping Wave 34/35 integrity gates authoritative.

---

## Wave 37 — reproducible live-provider model baselines (`done`)

Goal: make the Codex model and reasoning configuration used by manual live E2E explicit
and repeatable without changing product-runtime defaults or overriding the native defaults
of the other providers.

Non-goals:

- changing the runtime catalog or normal operator-run defaults;
- pinning a Qwen, Claude Code, or OpenCode model;
- executing a provider-authenticated live scenario as an implementation gate.

### Epic W37-E1 — live runtime baseline configuration (`done`)
Linked stories: `US-01`, `US-07`, `US-08`, `US-10`

#### Slice W37-E1-S1 — Codex live model pin (`done`)
Goal: generate a native Codex live-E2E command that explicitly selects `gpt-5.5` and
`xhigh` reasoning while retaining provider-supplied native commands for the other runtimes.

Dependencies:

- the existing native live-runtime command resolver and generated live config.

Local tasks:

- `W37-E1-S1-T1` (done) Configure the default live Codex command with `gpt-5.5` and
  `xhigh` reasoning.
  - Scope: `src/aidd/harness/live_runtime_config.py`, focused harness tests, and the
    live-E2E runbook.
  - Verification: focused runtime-config tests prove the generated Codex command carries
    both overrides while Claude Code and Qwen preserve their runtime-catalog defaults.

Exit evidence:

- generated live config records the selected Codex model and reasoning effort;
- provider-command overrides still take precedence, and unoverridden Qwen and Claude Code
  commands remain native provider defaults.

Sync notes:

- `2026-07-13` Opened from the requested live-E2E reproducibility change; it is an
  isolated harness configuration task and does not alter product runtime defaults.
- `2026-07-13` Completed `W37-E1-S1-T1`: generated live Codex config now uses
  `gpt-5.5` with `model_reasoning_effort="xhigh"`; Claude Code and Qwen retain their
  catalog defaults, and focused harness, eval-doctor, static, and documentation checks
  pass.
