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
- release-readiness notes for latest accepted `0.1.0a18` package-channel evidence and
  `0.1.0a19` source development state

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
- `W24-E1-S1-T4` (done) Prepare release-readiness notes for the accepted `0.1.0a18`
  package-channel evidence and `0.1.0a19` source development state
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
- `docs/release-notes-v0.1.0a18-draft.md` and `docs/analysis/beta-readiness-source-audit.md`
  record the latest accepted `0.1.0a18` package-channel evidence and current
  `0.1.0a19` source development state; accepted package-channel evidence is recorded
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
- the historical Mission Control visual set recorded the accepted active and completed
  command-center states; Wave 42 replaces and removes those superseded image files;
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

- the historical integrated-operator-workbench concept, removed after the Wave 42 target set
  replaced it
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
5. the [Wave 42 target contract](../architecture/operator-frontend-target-ux.md) and
   [replacement prompt set](../architecture/assets/operator-ui-target-v2/generation-prompts.md)
   for visual hierarchy, density, and responsive intent only;
6. current core/UI read models, service contracts, and deterministic tests for compatibility;
7. analysis reports and the previous Mission Control assets as historical baseline evidence,
   never as normative target design.

Canonical design references:

- [accepted UX direction](../architecture/operator-frontend.md#8-accepted-next-generation-ux-direction);
- [UX validation checklist](../architecture/operator-frontend.md#9-ux-validation-checklist-for-the-accepted-direction);
- [Wave 42 target contract](../architecture/operator-frontend-target-ux.md) and
  [replacement prompt set](../architecture/assets/operator-ui-target-v2/generation-prompts.md);
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

The historical eight-screen crosswalk was removed with its superseded assets. Wave 42 owns the
current 13-screen crosswalk in
[Target Operator Experience](../architecture/operator-frontend-target-ux.md). Completed Wave 36
task and browser evidence remains valid as implementation-baseline history; it does not make the
removed images normative.

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

### Epic W36-E4 — progressive onboarding and truthful runtime context (`done`)
Linked stories: `US-01`, `US-09`, `US-11`, `US-12`

#### Slice W36-E4-S1 — branching setup flow (`done`)
Goal: make project, work-item, runtime, and launch decisions sequential and truthful
instead of six equally weighted setup panels.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- `W36-E3-S2`
- `W36-E6-S4-T1`

Local tasks:

- `W36-E4-S1-T1` (done) Add an explicit Project -> Work item -> Runtime -> Review/Launch
  onboarding state machine with deterministic Back and Continue transitions.
  - Scope: `operator-onboarding.js` state controller.
  - Verification: a transition table covers validation success/failure, create, resume,
    runtime selection, backward navigation, and launch readiness.
- `W36-E4-S1-T2` (done) Render Create and Resume as sibling work-item branches and allow
  inspection before runtime selection.
  - Scope: onboarding work-item step.
  - Verification: resume opens existing context without a runtime or launch request,
    while mutation actions remain runtime-gated.
- `W36-E4-S1-T3` (done) Move project-set and configuration details behind an Advanced
  disclosure.
  - Scope: onboarding project/work-item layout.
  - Verification: create or resume remains inside the first setup viewport at `390x844`
    and `1440x900`, while advanced project-set validation remains reachable.
- `W36-E4-S1-T4` (done) Remove no-run mode cards that do not change execution semantics and
  leave terminal follow-up, clone, eval, and archive presentation to `W36-E5-S9`.
  - Scope: Guided Setup presentation only; the legacy renderer remains available for rollback.
  - Verification: the setup action-to-service matrix proves each remaining selector has a
    distinct endpoint/outcome and no terminal disposition leaks into first-run setup.
- `W36-E4-S1-T5` (done) Add the Guided Delivery preference and contextual explanation card over
  the same selected context and service actions used by Studio.
  - Scope: Guided Delivery browser presentation only.
  - Verification: toggling Guided Delivery preserves project, work item, run, stage,
    runtime, request payload, and durable result for the same action.
- `W36-E4-S1-T6` (done) Bind the new Review & Launch control to the shared mutation dispatcher only
  after task-aware workflow entrypoint integrity is restored.
  - Dependencies: `W35-E2-S8`, `W36-E6-S4-T1`.
  - Scope: Guided Setup launch binding only.
  - Verification: Guided and legacy launch controls dispatch an identical task-aware request,
    duplicate input creates at most one job, and durable readback selects one result.
- `W36-E4-S1-T7` (done) Promote the verified Guided Setup candidate to `parity_closed` while retaining
  legacy setup for both missing/default and explicit rollback modes until cutover.
  - Dependencies: `W36-E4-S1-T6`, `W36-E7-S1-T1`.
  - Scope: Guided Setup parity-manifest entry only.
  - Verification: the required journey passes in the Studio renderer and explicit rollback
    reaches the legacy setup through the same service path.
- `W36-E4-S1-T8` (done) Restore runtime-readiness inspection before an onboarding work-item
  context exists.
  - Scope: onboarding/readiness boundary only; launch-history projection remains unchanged
    after a work item is selected.
  - Verification: project inspection and resume onboarding return readiness without requiring
    active context, while contextual readiness still includes canonical launch history.

Exit evidence:

- a first-time operator reaches create or resume before runtime details and optional
  project-set configuration;
- the UI contains no selectable execution mode that dispatches the same generic launch.

#### Slice W36-E4-S2 — dimensioned runtime readiness and safety (`done`)
Goal: show only runtime readiness and write-scope claims backed by observable evidence.

Dependencies:

- `W36-E1-S2`
- `W34-E4-S2-T1`
- `W34-E4-S3`
- `W34-E7-S1-T2`

Local tasks:

- `W36-E4-S2-T1` (done) Expose binary, execution-command, authentication, and capability
  readiness dimensions without inferring unavailable evidence.
  - Scope: core runtime readiness read model.
  - Verification: detected, unavailable, auth-verified, auth-failed, auth-unverified,
    and legacy fixtures produce typed dimensions with compatibility fields.
- `W36-E4-S2-T2` (done) Project the latest per-runtime launch outcome and timestamp from
  canonical attempt evidence.
  - Scope: core operator runtime-history read model.
  - Verification: no-history, success, failure, blocked, cancelled, and legacy attempts
    resolve deterministically without reading outside `.aidd/`.
- `W36-E4-S2-T3` (done) Render dimensioned readiness, protected write scope, and last-launch
  evidence in Guided Setup and the Studio launch context.
  - Scope: packaged runtime/safety UI.
  - Verification: truth-copy fixtures contain no undifferentiated authentication claim
    or `No upstream write` promise.

Exit evidence:

- `ready` no longer conflates executable discovery, authentication, capability, and
  previous launch outcome;
- the operator sees the actual protected-data/write boundary before execution.

### Epic W36-E5 — Document & Evidence Studio vertical migration (`done`)
Linked stories: `US-02`, `US-03`, `US-05`, `US-06`, `US-10`, `US-11`, `US-13`

#### Slice W36-E5-S0 — core operator decision foundations (`done`)
Goal: make terminal recommendation policy available to Inbox and Flow Complete before either
renderer binds a primary action.

Dependencies:

- `W36-E1-S2-T1`
- reuse the accepted terminal-run handoff read model and allowed-outcomes contract

Local tasks:

- `W36-E5-S0-T1` (done) Add one core-owned `recommended_outcome` and rationale to the terminal-run
  handoff read model without removing the complete allowed-outcomes list.
  - Scope: core terminal handoff recommendation policy only.
  - Verification: clean fresh terminal QA recommends Create New Work Item; fresh failed,
    blocked, or warning QA recommends Start Follow-up Flow; missing, stale, and nonterminal QA
    produce no Flow Complete recommendation.
- `W36-E5-S0-T2` (done) Expose the recommendation through the existing additive terminal-handoff API
  contract with explicit legacy fallback semantics.
  - Scope: local UI terminal-handoff response contract only.
  - Verification: endpoint fixtures preserve allowed outcomes and source identity while old
    payloads resolve to an explicit no-recommendation compatibility state.

Exit evidence:

- renderer code owns neither terminal eligibility nor recommendation priority;
- Inbox and Flow Complete consume one stable, backward-compatible decision contract.

#### Slice W36-E5-S1 — shared Studio hierarchy and progressive disclosure (`done`)
Goal: keep the current operator decision and primary document visible while demoting
zero-value and secondary evidence.

Dependencies:

- `W36-E1-S1`
- `W36-E1-S2`
- `W36-E3-S3`
- executable behavior verification builds on `W34-E5-S3-T5`

Local tasks:

- `W36-E5-S1-T1` (done) Add a visibility policy that hides a zero-value Evidence Inspector
  and keeps secondary Filmstrip/log evidence collapsed until requested.
  - Scope: shell rendering policy.
  - Verification: no-run, healthy running, blocked, terminal, and history fixtures show
    only panels with current operator value.
- `W36-E5-S1-T2` (done) Consolidate duplicate recovery summaries into one Recovery Summary
  inside the Studio Decision Bar with one Evidence link.
  - Scope: recovery rendering.
  - Verification: every blocker fixture exposes one recovery landmark, one primary
    action, and one supporting evidence path.
- `W36-E5-S1-T3` (done) Implement one policy-free primary-action slot for vertical surfaces to bind
  to their own core/service-provided decision and compact metadata.
  - Scope: shared Decision Bar slot composition only.
  - Verification: surface fixtures can bind one action or an explicit no-action state, while
    the shared layer contains no eligibility, priority, or terminal-recommendation policy.
- `W36-E5-S1-T4` (done) Move Refresh, Open `.aidd`, Stop server, and other maintenance commands
  into a labelled overflow surface.
  - Scope: shell maintenance controls.
  - Verification: service commands remain keyboard-accessible but no longer precede the
    primary operator task in focus or visual order.
- `W36-E5-S1-T5` (done) Establish one Studio content scroll owner so the inspector, drawers,
  and Filmstrip create no nested scroll traps on supported desktop viewports.
  - Scope: desktop shell layout.
  - Verification: `1280x900` and `1440x900` fixtures expose one primary vertical scroll
    path while sticky context and drill-down panels remain reachable.

Exit evidence:

- default, empty, and healthy states do not reserve equal visual weight for empty
  Blockers, Recovery, Activity, and Evidence panels;
- the first viewport communicates context, one decision, and the primary work surface.

#### Slice W36-E5-S2 — compact mobile operator shell (`done`)
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

- `W36-E5-S2-T1` (done) Replace the measured `275px` sticky mobile header with a compact
  context/status bar and maintenance overflow.
  - Scope: topbar markup and responsive CSS.
  - Verification: `320x568` and `390x844` fixtures meet the accepted header budget and
    never cover the mode tabs or primary action.
- `W36-E5-S2-T2` (done) Keep the current Decision Bar or Inbox action in the first mobile
  viewport and move dense evidence to explicit drill-down.
  - Scope: responsive workbench ordering.
  - Verification: no-run Inbox, post-stage, and active Studio fixtures expose the accepted
    primary decision without initial scrolling; vertical Recovery/History/terminal slices own
    their state-specific mobile parity.
- `W36-E5-S2-T3` (done) Replace repeated per-body-mode ordering selectors with one mobile
  priority layout contract: context -> decision -> document -> evidence/history drill-down.
  - Scope: responsive shell state classes.
  - Verification: every declared operator state maps to the same context -> decision ->
    document -> evidence/history drill-down ordering rule.
- `W36-E5-S2-T4` (done) Keep compact stage navigation and primary labels legible at `320px` and
  `390px` without rendering the desktop stage rail as a tiny grid.
  - Scope: responsive stage rail and label wrapping.
  - Verification: shared touch targets pass, no active stage or primary label clips,
    and document scroll width equals viewport width.

Exit evidence:

- mobile monitoring, answers, approvals, recovery, and next decisions are first-viewport
  tasks;
- dense diff, graph, and history views remain reachable through deliberate drill-downs.

#### Slice W36-E5-S3 — project-local Inbox (`done`)
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

- `W36-E5-S3-T1` (done) Implement a typed core-owned durable Inbox projection with Needs your
  decision, Ready to continue, and Flow complete sections.
  - Scope: core operator frontend read models only.
  - Verification: provider-free fixtures prove deterministic priority, exact work-item/run/stage
    references, one core-approved action, and no frontend-derived eligibility or live-job claim.
- `W36-E5-S3-T2` (done) Add typed work-item/run/stage correlation to bounded UI job summaries and
  compose the project-local Running now overlay without changing durable Inbox eligibility.
  - Dependencies: `W34-E3-S3-T1`.
  - Scope: CLI UI job summary and Inbox composition service only.
  - Verification: zero, one, concurrent, terminal, evicted, and legacy job fixtures produce a
    bounded Running now section whose references agree with durable run state.
- `W36-E5-S3-T3` (done) Expose the composed Inbox through an additive local UI read endpoint with
  bounded project-local data.
  - Scope: CLI UI read route and response contract only.
  - Verification: endpoint tests cover empty, blocking, running, ready, terminal, legacy, and
    malformed evidence without arbitrary path access.
- `W36-E5-S3-T4` (done) Render Inbox sections and route each item to the exact Studio context through
  the shared action/state seam.
  - Scope: packaged Inbox renderer only.
  - Verification: one browser fixture per section opens the expected work item, run, stage,
    artifact/evidence detail, and primary action.
- `W36-E5-S3-T5` (done) Promote the verified Inbox candidate to `parity_closed` while retaining legacy
  Project Home for both missing/default and explicit rollback modes until cutover.
  - Dependencies: `W36-E7-S1-T12`.
  - Scope: Inbox parity-manifest entry only.
  - Verification: `ui=studio` exposes no duplicate decision, while missing/default and
    `ui=legacy` preserve Project Home through the same read/action seam until cutover.

Exit evidence:

- the first actionable item and its primary action are visible without scrolling;
- Inbox is a rebuildable read model and cannot become a second workflow engine;
- blocking items cannot be hidden by presentation-only dismissal.

#### Slice W36-E5-S4 — active Document & Evidence Studio (`done`)
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

- `W36-E5-S4-T1` (done) Compose the active Studio view from shared mode navigation, compact context
  bar, canonical stage navigation, and Decision Bar slots.
  - Scope: packaged active-Studio markup and renderer only.
  - Verification: no-run, active, blocked, and terminal fixtures preserve context and expose
    exactly one primary action across supported desktop viewports.
- `W36-E5-S4-T2` (done) Render the read-only Document Canvas with Preview, Source, and Diff over the
  existing safe workbench/document endpoints.
  - Scope: packaged document renderer only.
  - Verification: Markdown, source, diff, missing, malformed, and truncated fixtures retain
    semantics, copyability, safe keys, and document-first visual priority.
- `W36-E5-S4-T3` (done) Render the conditional Evidence Inspector with finding, provenance, related
  artifact, and exact source-reference variants.
  - Scope: packaged evidence renderer only.
  - Verification: zero-value evidence hides the inspector while validator, provenance,
    implementation, and legacy fixtures show only retained evidence.
- `W36-E5-S4-T4` (done) Integrate live elapsed time, last-output age, real milestones, silence state,
  and Open live output into Studio without embedding raw logs in the default viewport.
  - Dependencies: `W36-E6-S3`.
  - Scope: active Studio observation renderer only.
  - Verification: running, silent, cancelling, completed, and externally completed jobs show no
    fake progress and agree with persisted runtime evidence.
- `W36-E5-S4-T5` (done) Promote the verified active-Studio candidate to `parity_closed` while retaining
  the legacy cockpit/sidebar renderer for missing/default and explicit rollback until cutover.
  - Dependencies: `W36-E7-S1-T2`, `W36-E7-S1-T7`.
  - Scope: active-Studio parity-manifest entry only.
  - Verification: `ui=studio` contains no duplicate workbench, while missing/default and
    `ui=legacy` retain artifact, question, recovery, and live-log reachability until cutover.

Exit evidence:

- the first desktop viewport contains context, one current decision, and the primary document;
- generated evidence remains read-only and corrections retain durable audited paths;
- stage progression and attempt history remain distinct concepts.

#### Slice W36-E5-S5 — human-decision Recovery Studio (`done`)
Goal: migrate questions, interventions, and runtime approvals into one contextual decision
surface without conflating their durable semantics.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S2`
- `W36-E6-S4`
- approval replacement depends on `W34-E3-S2`

Local tasks:

- `W36-E5-S5-T1` (done) Render blocking questions with exact QID, resolved/partial/deferred status,
  draft recovery, and answer-and-resume behavior.
  - Scope: question Recovery renderer only.
  - Verification: resolved unblocks, partial/deferred remain blocking when required, failed
    submit preserves the draft, and durable `answers.md` readback wins.
- `W36-E5-S5-T2` (done) Render Request Change and intervention context as durable stage-scoped input,
  including downstream-success rejection and remediation routing.
  - Scope: intervention Recovery renderer only.
  - Verification: allowed submit creates one operator-request document and blocked intervention
    creates none while preserving the selected stage/run.
- `W36-E5-S5-T3` (done) Render runtime approval scope, breadth, reason, risk, pending state, session
  confirmation, and durable winning decision separately from product questions.
  - Scope: approval Recovery renderer only.
  - Verification: allow/deny/cancel/conflict fixtures agree with the compare-and-set audit row and
    no broad approval posts before confirmation.
- `W36-E5-S5-T4` (done) Implement the decision-first mobile question and approval layouts with compact
  context, 44px controls, and evidence drill-down.
  - Dependencies: `W36-E5-S2`.
  - Scope: human-decision responsive presentation only.
  - Verification: `320x568` and `390x844` keyboard/touch journeys expose the full decision and
    primary submit without horizontal overflow or initial scroll.
- `W36-E5-S5-T5` (done) Promote the verified question candidate to `parity_closed` while retaining the
  legacy question renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T6`, `W36-E7-S1-T11`.
  - Scope: question parity-manifest entry only.
  - Verification: the question fixture closes independently and durable answer/resume behavior
    is equivalent in `ui=studio`, missing/default, and `ui=legacy` modes.
- `W36-E5-S5-T6` (done) Promote the verified intervention candidate to `parity_closed` while retaining
  the legacy intervention renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T10`, `W36-E5-S5-T5`.
  - Scope: intervention parity-manifest entry only.
  - Verification: allowed and blocked intervention fixtures close independently with identical
    durable request behavior.
- `W36-E5-S5-T7` (done) Promote the verified approval candidate to `parity_closed` while retaining the
  legacy approval renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T11`, `W36-E5-S5-T6`.
  - Scope: approval parity-manifest entry only.
  - Verification: allow, deny, cancel, session, and conflict fixtures close independently and
    preserve the same compare-and-set winner.

Exit evidence:

- question answers, runtime approvals, and intervention requests remain distinct durable paths;
- every human blocker exposes one decision, one evidence path, and truthful readback.

#### Slice W36-E5-S6 — runtime and validation Recovery Studio (`done`)
Goal: surface the first decisive runtime or validation failure with the one eligible recovery
action and exact retained evidence.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S3`
- `W34-E3-S3-T1`
- `W34-E4-S2`

Local tasks:

- `W36-E5-S6-T1` (done) Render runtime/provider failure, stopped state, last durable signal, and
  eligible retry without consuming or implying validation repair budget.
  - Dependencies: `W36-E5-S5-T7`.
  - Scope: runtime-failure Recovery renderer only.
  - Verification: unavailable executable, authentication, timeout, cancellation, no-progress,
    and legacy fixtures show the typed outcome and correct safe action.
- `W36-E5-S6-T2` (done) Render transient offline, reconnecting, recovered, expired-job, and manual
  Reconnect states while preserving durable log/artifact access.
  - Scope: connection Recovery renderer only.
  - Verification: cursor-preserving failure/recovery fixtures show no skipped or duplicated
    chunks and never claim runtime termination without server evidence.
- `W36-E5-S6-T3` (done) Render validation findings with exact document/line/rule/provenance and make
  Run Repair primary only when the backend reports repair available.
  - Scope: validation Recovery renderer only.
  - Verification: repair-available, repaired, exhausted, explicit-stop, stale-artifact, and
    malformed-report fixtures choose the correct action and evidence.
- `W36-E5-S6-T4` (done) Render Request Change as primary after repair exhaustion/explicit stop and keep
  raw logs/attempt history as secondary drill-down.
  - Scope: repair-exhaustion Recovery renderer only.
  - Verification: no exhausted state exposes an enabled Run Repair and the intervention request
    retains the selected run/stage context.
- `W36-E5-S6-T5` (done) Implement decision-first mobile runtime and validation Recovery layouts over
  the shared compact shell.
  - Dependencies: `W36-E5-S2`.
  - Scope: failure/recovery responsive presentation only.
  - Verification: `320x568` and `390x844` show the typed failure, one eligible recovery action,
    and evidence drill-down without horizontal overflow or initial decision scroll.
- `W36-E5-S6-T6` (done) Promote the verified runtime/validation candidates to `parity_closed` while
  retaining legacy failure cards for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T3`.
  - Scope: runtime/validation parity-manifest entries only.
  - Verification: both entries close and first-failure, repair-history, raw-log, and request
    paths remain equivalent in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- runtime failure, validation repair, and human correction remain truthful distinct paths;
- recovery never silently progresses or invents missing evidence.

#### Slice W36-E5-S7 — implement, Review, and QA quality gates (`done`)
Goal: migrate task execution, repository evidence, Review findings, QA verdict, remediation,
and stale downstream recovery without weakening task-aware eligibility.

Dependencies:

- `W35-E2-S8`
- `W36-E5-S4`
- `W36-E6-S2`
- `W36-E6-S4`

Local tasks:

- `W36-E5-S7-T1` (done) Render dependency-ready tasks, task attempts, blocked/failed recovery, and
  aggregate finalization inside Studio from the canonical task read model.
  - Scope: implement task workspace renderer only.
  - Verification: run/resume/fail/recover/finalize fixtures preserve successful tasks and never
    enable Review before successful aggregate finalization.
- `W36-E5-S7-T2` (done) Render the real repository diff, untracked/deleted files, `.aidd/` separation,
  scope status, and implementation-report claim mismatch in the Document Canvas.
  - Scope: implement evidence renderer only.
  - Verification: repository-diff fixtures match core evidence and use textual added/removed/
    changed meaning in addition to color.
- `W36-E5-S7-T3` (done) Render structured Review findings and QA verdict, residual risks, known issues,
  acceptance ids, and evidence links.
  - Scope: Review/QA quality-gate renderer only.
  - Verification: approval/rejection/not-ready/blocked/missing-evidence fixtures agree with the
    canonical reports and validators.
- `W36-E5-S7-T4` (done) Render selected remediation to `implement`, pending readback, and explicit
  downstream Review/QA stale rerun.
  - Scope: quality-gate remediation renderer only.
  - Verification: one durable remediation request is created, fresh downstream stages become
    stale, stale QA never becomes terminal, and rerun uses the selected runtime.
- `W36-E5-S7-T5` (done) Promote the verified implement/Review/QA candidates to `parity_closed` while
  retaining legacy surfaces for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T4`, `W36-E7-S1-T9`.
  - Scope: task/quality-gate parity-manifest entries only.
  - Verification: entries close while task ledger, finalization, diff, findings, remediation,
    stale-state, `ui=studio`, missing/default, and `ui=legacy` tests remain green.

Exit evidence:

- every Review/QA claim remains bound to task and repository evidence;
- no UI entrypoint bypasses the task ledger or aggregate finalization gate.

#### Slice W36-E5-S8 — History Filmstrip and retained evidence (`done`)
Goal: expose causal attempt/task history, comparison, lineage, and archive state using only
durably retained evidence.

Dependencies:

- `W36-E5-S4`
- `W36-E6-S1`
- `W34-E2-S2-T2`
- comparison/accountability consume `W34-E2-S3-T2`
- archive presentation consumes `W34-E2-S3-T1`

Local tasks:

- `W36-E5-S8-T1` (done) Implement a typed Filmstrip frame projection for stage attempts, task
  attempts, and aggregate finalization milestones with events as markers.
  - Scope: core operator timeline/read model only.
  - Verification: normal, repair, intervention, remediation, task, finalization, live, and
    legacy fixtures produce stable frame identity and retain the first decisive failure.
- `W36-E5-S8-T2` (done) Render the collapsed Studio Filmstrip and expanded History timeline with
  selected artifact/log evidence and Return to live behavior.
  - Scope: packaged Filmstrip/History renderer only.
  - Verification: frame selection, historical auto-follow pause, exact log range, missing
    snapshot, and current-live return behave deterministically.
- `W36-E5-S8-T3` (done) Render run comparison plus retained prompt, artifact, stage, and validator
  deltas.
  - Scope: History comparison renderer only.
  - Verification: Back/reload restores both runs and every displayed delta links to retained
    source evidence or an explicit unavailable-snapshot state.
- `W36-E5-S8-T4` (done) Render parent, source, and child run lineage without presenting lineage as
  mutable workflow state.
  - Scope: History lineage renderer only.
  - Verification: every routable relation resolves through canonical run identity and opening a
    relation leaves both source and target manifests byte-identical.
- `W36-E5-S8-T5` (done) Render archive state as the append-only overlay owned by `W34-E2-S3-T1`.
  - Scope: History archive-state renderer only.
  - Verification: archive inspection changes no completed-run bytes/hashes and all retained
    documents, logs, comparison, and lineage remain inspectable.
- `W36-E5-S8-T6` (done) Render Filmstrip as a vertical chronological mobile drill-down rather than a
  horizontal scroll trap.
  - Dependencies: `W36-E5-S2`.
  - Scope: History responsive presentation only.
  - Verification: `320x568` and `390x844` expose frame status, evidence action, and return path
    without page-level horizontal overflow.
- `W36-E5-S8-T7` (done) Promote the verified History candidate to `parity_closed` while retaining the
  legacy timeline/history renderer for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T5`.
  - Scope: History parity-manifest entry only.
  - Verification: the entry closes and timeline, comparison, lineage, archive, and raw evidence
    remain reachable in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- History never implies a document/repository snapshot that was not retained;
- stage progression, causal attempts, and run lineage remain distinguishable and routable.

#### Slice W36-E5-S9 — Flow Complete and independent next outcomes (`done`)
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

- `W36-E5-S9-T3` (done) Render immutable Flow Complete evidence, the core recommendation, and Other next
  actions only for fresh eligible terminal QA.
  - Dependencies: `W36-E5-S8-T7` as the direct queue predecessor.
  - Scope: terminal handoff renderer only.
  - Verification: clean, failed, blocked, and warning fresh terminal fixtures show the exact
    core recommendation; missing, stale, and nonterminal QA do not render Flow Complete.
- `W36-E5-S9-T4` (done) Render follow-up definition, inherited context, source evidence, preflight, and
  launch through the shared draft/mutation seams.
  - Dependencies: `W36-E5-S9-T3` as the direct queue predecessor.
  - Scope: follow-up next-flow renderer only.
  - Verification: Back/reload/failure/retry preserve the follow-up draft, successful launch
    creates one new work-item/run identity, and the source run remains byte-identical.
- `W36-E5-S9-T5` (done) Render clone definition, inherited context, source evidence, preflight, and
  launch through the shared draft/mutation seams.
  - Dependencies: `W36-E5-S9-T4` as the direct queue predecessor.
  - Scope: clone next-flow renderer only.
  - Verification: Back/reload/failure/retry preserve the clone draft, successful launch creates
    one independent identity, and the source run remains byte-identical.
- `W36-E5-S9-T6` (done) Render the existing Run Eval / Scenario Batch manual handoff as a non-repair
  comparison disposition under Other next actions.
  - Dependencies: `W36-E5-S9-T5` as the direct queue predecessor.
  - Scope: terminal eval handoff renderer only; no new mutation endpoint.
  - Verification: the action opens exact source/version/scenario context and operator commands,
    sends no workflow mutation request, and leaves source-run evidence unchanged.
- `W36-E5-S9-T7` (done) Render Archive Run as an append-only visibility disposition under Other next
  actions.
  - Dependencies: `W36-E5-S9-T6` as the direct queue predecessor.
  - Scope: terminal archive disposition renderer only.
  - Verification: archive writes only the owned overlay and completed documents, artifacts,
    logs, comparison, and lineage remain inspectable.
- `W36-E5-S9-T8` (done) Render the recommended next decision and Other next actions as a compact mobile
  drill-down over the shared responsive shell.
  - Dependencies: `W36-E5-S2`, with `W36-E5-S9-T7` as the direct queue predecessor.
  - Scope: Flow Complete responsive presentation only.
  - Verification: `320x568` and `390x844` show final status, one recommendation, and a reachable
    secondary-outcomes disclosure without horizontal overflow or initial decision scroll.
- `W36-E5-S9-T9` (done) Promote the verified Flow Complete candidate to `parity_closed` while retaining
  the equal-weight legacy action grid/wizard for missing/default and explicit rollback.
  - Dependencies: `W36-E7-S1-T8`.
  - Scope: terminal/next-flow parity-manifest entry only.
  - Verification: the parity entry closes and all accepted outcomes remain keyboard-reachable
    with distinct service semantics in `ui=studio`, missing/default, and `ui=legacy` modes.

Exit evidence:

- completed source runs remain immutable;
- one recommended outcome leads, while all accepted independent outcomes remain reachable.

#### Slice W36-E5-S10 — default cutover and legacy removal (`done`)
Goal: make Studio the only maintained renderer after a bounded rollback window and delete
presentation code that no longer owns a supported surface.

Dependencies:

- `W36-E4-S1-T7`
- `W36-E5-S3-T5`, `W36-E5-S4-T5`, `W36-E5-S5-T5..T7`, `W36-E5-S6-T6`,
  `W36-E5-S7-T5`, `W36-E5-S8-T7`, and `W36-E5-S9-T9`
- `W36-E7-S1-T1..T12`
- `W36-E7-S2-T1`

Local tasks:

- `W36-E5-S10-T1` (done) Switch the missing/default presentation selector to Studio after every
  per-surface parity entry is closed while retaining explicit `ui=legacy` rollback.
  - Dependencies: `W36-E7-S2-T1` as the direct queue predecessor.
  - Scope: packaged renderer default only.
  - Verification: the full provider-free browser command passes in default Studio mode and the
    explicit rollback renderer still dispatches identical service actions.
- `W36-E5-S10-T2` (done) Record one source-installed rollback-window pass while both presentation
  selectors remain supported.
  - Dependencies: `W36-E5-S10-T1` as the direct queue predecessor.
  - Scope: cutover evidence only.
  - Verification: isolated fixture copies prove equivalent endpoint/payload semantics and
    normalized outcomes in default and rollback modes; immutable source-run evidence remains
    byte-identical where the journey contract requires it.
- `W36-E5-S10-T3` (done) Remove the temporary legacy selector when no accepted journey requires it.
  - Dependencies: `W36-E5-S10-T2` as the direct queue predecessor.
  - Scope: browser bootstrap selector only.
  - Verification: missing, invalid, and former legacy selector values resolve to Studio without
    changing packaged URLs, service requests, or durable state.
- `W36-E5-S10-T4` (done) Remove unreferenced legacy render modules, selectors, body-mode ordering,
  package resources, and compatibility tests that no longer protect a supported contract.
  - Dependencies: `W36-E5-S10-T3` as the direct queue predecessor.
  - Scope: packaged frontend cleanup only.
  - Verification: exhaustive asset discovery, JavaScript syntax, package-resource, DOM, and
    browser suites pass with no legacy renderer references.
- `W36-E5-S10-T5` (done) Reconcile operator docs and screenshots to the Studio-only surface after
  implementation parity.
  - Dependencies: `W36-E5-S10-T4` as the direct queue predecessor.
  - Scope: README, handbook, local-project E2E, and architecture implementation-status text.
  - Verification: docs consistency finds no current-behavior claim or image that points to the
    removed renderer while historical assets remain clearly non-normative.

Exit evidence:

- `aidd ui` opens Studio through stable packaged assets and existing service semantics;
- no duplicate renderer, action dispatcher, or dead legacy selector remains;
- rollback evidence exists without retaining a permanent second frontend.

### Epic W36-E6 — durable navigation, drafts, reconnect, and action integrity (`done`)
Linked stories: `US-05`, `US-06`, `US-10`, `US-11`

#### Slice W36-E6-S1 — URL-backed work-item and run navigation (`done`)
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
- `W36-E6-S1-T3` (done) Define shared route intents for Inbox work-item, historical-run, parent, and
  child-lineage bindings without owning their vertical renderers.
  - Scope: URL/navigation intent controller only.
  - Verification: E5-owned Inbox and History fixtures bind each visible action to one distinct
    route outcome, and archived runs retain artifact/history inspection.

Exit evidence:

- operator location survives reload and browser navigation;
- Inbox and History no longer expose different labels for the same action.

#### Slice W36-E6-S2 — browser-session draft and dirty-state safety (`done`)
Goal: preserve unsaved operator input across UI navigation without treating drafts as
canonical workflow evidence.

Dependencies:

- `W36-E1-S1`
- `W36-E3-S2`
- next-flow adoption depends on `W34-E3-S4-T4`

Local tasks:

- `W36-E6-S2-T1` (done) Define the key, retention, and cleanup contract for noncanonical
  browser-session drafts.
  - Scope: operator frontend architecture only.
  - Verification: the contract isolates project, work item, run, stage, form, and source
    id and names exact submit/expiry cleanup behavior.
- `W36-E6-S2-T4` (done) Implement the scoped noncanonical browser-session draft store.
  - Dependencies: `W36-E6-S2-T1`.
  - Scope: shared packaged JavaScript state utility only.
  - Verification: contract fixtures isolate every key dimension and successful submit
    clears only the owning draft.
- `W36-E6-S2-T2` (done) Adopt draft restore and leave-warning behavior for question and
  intervention forms.
  - Dependencies: `W36-E6-S2-T4`.
  - Scope: question/intervention browser modules.
  - Verification: stage/tab switch, reload, failed submit, and successful submit preserve
    or clear the expected draft only.
- `W36-E6-S2-T3` (done) Adopt draft restore and leave-warning behavior for follow-up and clone
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

#### Slice W36-E6-S3 — reconnecting live observation (`done`)
Goal: recover live monitoring after transient API failure without losing log position or
misrepresenting the runtime as stopped.

Dependencies:

- `W34-E3-S3-T1`
- `W34-E5-S3-T5`
- `W36-E3-S3-T2`

Local tasks:

- `W36-E6-S3-T1` (done) Replace terminal-on-error interval polling with a cursor-preserving
  retry state machine and bounded exponential backoff.
  - Dependencies: `W36-E6-S2-T3`.
  - Scope: `operator-logs-jobs.js` polling controller.
  - Verification: failure -> retry -> recovery, repeated failure, cancellation, and
    terminal-job sequences produce no duplicate or skipped chunks.
- `W36-E6-S3-T2` (done) Render offline, reconnecting, recovered, expired-job, and manual
  Reconnect states.
  - Scope: live connection status surface.
  - Verification: each sequence names whether the runtime may still be running and
    offers the correct local recovery action.
- `W36-E6-S3-T3` (done) Reconcile active job, dashboard, logs, and selected stage after
  recovery or terminal-job eviction.
  - Scope: browser state reconciliation.
  - Verification: reconnect and eviction fixtures converge on the server-authoritative
    state while retaining durable log/artifact access.

Exit evidence:

- a transient local API failure cannot silently stop monitoring;
- reconnect and eviction states remain truthful about runtime ownership and durable
  evidence.

#### Slice W36-E6-S4 — client mutation and approval integrity (`done`)
Goal: give every mutating control an immediate pending state and reconcile conflicts to
the single durable server outcome.

Dependencies:

- `W34-E3-S1-T2` for keyed server admission and deterministic mutation conflicts;
- approval tasks depend on `W34-E3-S2`;
- next-flow adoption depends on `W34-E3-S4-T4`.

Local tasks:

- `W36-E6-S4-T1` (done) Add a shared keyed client mutation guard with pending lock, duplicate
  suppression, conflict readback, and retryable failure state.
  - Dependencies: `W36-E6-S3-T3`.
  - Scope: packaged API/state utility.
  - Verification: double-click and concurrent-control fixtures send one request per key
    and preserve a retry path after failure.
- `W36-E6-S4-T2` (done) Adopt the mutation guard for workflow, stage, and remediation launch
  controls.
  - Scope: run mutation controls.
  - Verification: pending, same-run conflict, different-run concurrency, failure, and
    success states match server admission.
- `W36-E6-S4-T3` (done) Adopt the mutation guard for answer and intervention writes.
  - Scope: question/intervention mutation controls.
  - Verification: failed writes retain drafts, successful writes clear drafts, and
    duplicate submissions create one durable artifact.
- `W36-E6-S4-T4` (done) Adopt the mutation guard for next-flow draft, preflight, and launch.
  - Dependencies: `W34-E3-S4-T4`.
  - Scope: next-flow browser controller.
  - Verification: repeated actions cannot create duplicate work items or runs and the
    source run remains unchanged after failure.
- `W36-E6-S4-T5` (done) Add approval reason capture and explicit confirmation for
  `allow_for_session` with controls disabled while submitting.
  - Dependencies: `W34-E3-S2`.
  - Scope: approval decision UI.
  - Verification: no session-wide approval POST occurs before confirmation and the
    submitted reason/breadth remain visible in the preview.
- `W36-E6-S4-T6` (done) Reconcile approval compare-and-set or terminal conflicts to the durable
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

#### Slice W36-E7-S1 — canonical operator browser journeys (`done`)
Goal: prove the critical operator jobs through provider-free rendered journeys rather
than isolated asset and endpoint assertions.

Dependencies:

- `W36-E2`
- `W36-E1-S2-T3`

Local tasks:

- `W36-E7-S1-T1` (done) Add the Guided Setup project validation, create/resume, runtime review,
  first launch, and resulting Inbox entry browser journey.
  - Dependencies: `W36-E4-S1-T1..T6`, `W36-E4-S2`, `W36-E5-S2`,
    `W36-E5-S3-T1..T4`.
  - Scope: onboarding browser scenario family.
  - Verification: every required viewport completes create or resume with one primary
    action, no geometry/accessibility failure, and no provider authentication.
- `W36-E7-S1-T2` (done) Add the active Studio running, silence, cancellation, transient
  reconnect, and return-to-live browser journey.
  - Dependencies: `W36-E5-S2`, `W36-E5-S4-T1..T4`, `W36-E6-S3`.
  - Scope: live Studio browser scenario family.
  - Verification: real milestones, last output, cursor recovery, cancel lifecycle, and
    durable logs pass without console/network ambiguity or fake progress.
- `W36-E7-S1-T3` (done) Add the Runtime/Validation Recovery Studio repair/exhaustion browser
  journey.
  - Dependencies: `W36-E5-S6-T1..T5`; direct queue predecessor `W36-E5-S6-T5`.
  - Scope: runtime/validation recovery scenario family.
  - Verification: each failure exposes the correct first evidence, one primary recovery
    action, and a truthful stopped/running state.
- `W36-E7-S1-T4` (done) Add the Review/QA quality-gate, remediation, and stale downstream
  browser journey.
  - Dependencies: `W35-E2-S8`, `W36-E5-S7-T2..T4`, `W36-E7-S1-T9` as the direct
    queue predecessor.
  - Scope: delivery-decision browser scenario family.
  - Verification: unsafe completion remains blocked, remediation/rerun is explicit, and stale
    QA keeps Flow Complete absent until a later fresh-QA journey proves terminal eligibility.
- `W36-E7-S1-T5` (done) Add the History Filmstrip, comparison, lineage, and archive browser
  journey.
  - Dependencies: `W36-E5-S8-T1..T6`, with `W36-E5-S8-T6` as the direct queue predecessor.
  - Scope: history and continuation browser scenario family.
  - Verification: Back/reload/deep links preserve run identity and completed source-run
    artifacts remain immutable and inspectable.
- `W36-E7-S1-T6` (done) Add the blocking-question answer/resume Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T1`, `W36-E5-S5-T4`.
  - Scope: product-question browser scenario family.
  - Verification: draft restore, resolved/partial/deferred state, failed/successful durable
    readback, answer/resume, and current run/stage context pass on desktop and mobile.
- `W36-E7-S1-T7` (done) Add the Document Canvas and Evidence Inspector browser journey.
  - Dependencies: `W36-E5-S4-T2..T3`.
  - Scope: document/evidence browser scenario family.
  - Verification: Preview/Source/Diff, safe artifact selection, validator provenance,
    missing evidence, zero-value hiding, and raw-log drill-down pass without arbitrary
    path reads.
- `W36-E7-S1-T8` (done) Add the Flow Complete, follow-up, clone, eval, and archive disposition
  browser journey.
  - Dependencies: `W36-E5-S0`, `W36-E5-S9-T3..T8`, with `W36-E5-S9-T8` as the direct
    queue predecessor.
  - Scope: terminal and next-outcome browser scenario family.
  - Verification: clean versus failed/blocked/warning fresh QA, stale/nonterminal exclusion,
    one core-recommended action, drafts/preflight, independent identities, truthful manual eval
    handoff, archive overlay, and byte-identical source-run evidence all pass.
- `W36-E7-S1-T9` (done) Add the implement task run/resume, failed-attempt recovery, repository
  evidence, and aggregate-finalization browser journey.
  - Dependencies: `W35-E2-S8`, `W36-E5-S7-T1..T4`, `W36-E5-S7-T4` as the direct
    queue predecessor.
  - Scope: task-aware implement browser scenario family.
  - Verification: dependency readiness, preserved successes, diff/scope evidence,
    finalization recovery, and Review eligibility agree with the canonical task ledger.
- `W36-E7-S1-T10` (done) Add the Request Change/intervention Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T2`, `W36-E5-S5-T4`, `W36-E7-S1-T6`.
  - Scope: intervention browser scenario family.
  - Verification: draft restore, allowed request, downstream-success rejection, one durable
    operator request, remediation routing, and current run/stage context pass.
- `W36-E7-S1-T11` (done) Add the runtime-approval Recovery Studio browser journey.
  - Dependencies: `W36-E5-S5-T3`, `W36-E5-S5-T4`, `W36-E7-S1-T10`.
  - Scope: runtime-approval browser scenario family.
  - Verification: allow, deny, cancel, session confirmation, pending state, compare-and-set
    conflict, durable winner, and current run/stage context pass on desktop and mobile.
- `W36-E7-S1-T12` (done) Add the project-local Inbox priority and routing browser journey.
  - Dependencies: `W36-E5-S0`, `W36-E5-S2`, `W36-E5-S3-T1..T4`.
  - Scope: Inbox browser scenario family.
  - Verification: Needs your decision, Running now, Ready to continue, and Flow complete
    fixtures preserve deterministic order, one core-approved action, exact Studio routing,
    first-viewport visibility, keyboard navigation, and blocking-item non-dismissal.

Exit evidence:

- every high-value operator job has an executable rendered journey across its supported
  viewports;
- browser scenarios prove task completion, not only page/API reachability.

#### Slice W36-E7-S2 — enforced packaged-UI gate (`done`)
Goal: make every declared browser journey executable in the maintained deterministic
quality lane.

Dependencies:

- `W36-E7-S1`
- `W34-E5-S3`

Local tasks:

- `W36-E7-S2-T1` (done) Add one command that discovers and executes every declared packaged-UI
  browser scenario.
  - Dependencies: `W36-E5-S9-T9` as the direct queue predecessor.
  - Scope: local/CI UI test entry point.
  - Verification: discovered scenario ids equal executed scenario ids exactly and live
    provider manifests are rejected.
- `W36-E7-S2-T2` (done) Add the packaged-UI browser command to CI.
  - Dependencies: `W36-E5-S10-T5` as the direct queue predecessor.
  - Dependencies: `W36-E7-S2-T1`.
  - Scope: deterministic CI integration only.
  - Verification: an intentional geometry, accessibility, console, or journey failure
    blocks CI while provider credentials remain unnecessary.
- `W36-E7-S2-T3` (done) Update the local-project UI evidence template for full browser passes.
  - Dependencies: `W36-E7-S2-T2` as the direct queue predecessor.
  - Dependencies: `W36-E7-S2-T1`.
  - Scope: operator E2E documentation only.
  - Verification: docs consistency and the evidence checklist record version, fixture,
    viewports, journeys, accessibility, console/network state, and cleanup.
- `W36-E7-S2-T4` (done) Add the packaged-UI browser command to release preflight.
  - Dependencies: `W36-E7-S2-T3` as the direct queue predecessor.
  - Dependencies: `W36-E7-S2-T2`.
  - Scope: deterministic release-preflight integration only.
  - Verification: an intentional browser journey failure blocks release preparation
    without provider credentials.
- `W36-E7-S2-T6` (done) Restore deterministic canonical-route coverage uncovered by the full
  packaged-UI pass.
  - Dependencies: `W36-E7-S2-T4` as the direct queue predecessor.
  - Scope: packaged browser journey contracts only.
  - Verification: Document/Evidence opens through canonical Studio route context and the
    intervention draft survives History/Back without a readiness-rerender race; the complete
    packaged-UI runner has no failed journey ids.
- `W36-E7-S2-T7` (done) Normalize packaged browser fixture source for the repository-wide lint
  gate after the full browser pass.
  - Dependencies: `W36-E7-S2-T5`.
  - Scope: browser-test source formatting only.
  - Verification: repository-wide Ruff and the affected History/Recovery browser fixtures pass
    without changing rendered DOM semantics.
- `W36-E7-S2-T8` (done) Reconcile repository-wide tests with the Studio-only asset ownership and
  deterministic process-fixture readiness exposed by final acceptance.
  - Dependencies: `W36-E7-S2-T7`.
  - Scope: test contracts and token-driven responsive control height only.
  - Verification: the process supervisor fixtures, UI asset ownership contracts, full pytest,
    Ruff, and mypy pass without changing public runtime or UI semantics.
- `W36-E7-S2-T5` (done) Record one source-installed full provider-free browser pass.
  - Dependencies: `W36-E7-S2-T6` as the direct queue predecessor.
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

- `W36-E7-S3-T1` (done) Write the observed operator task script and scoring template for
  Guided Setup, Inbox triage, active Studio monitoring, question recovery, runtime
  failure, QA remediation, History inspection, and terminal continuation.
  - Dependencies: `W36-E7-S2-T5` as the direct queue predecessor.
  - Scope: operator acceptance documentation.
  - Verification: every task records completion, elapsed time, wrong actions, assistance,
    confidence, and first decisive confusion.
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

Exit evidence:

- task success and operator confidence confirm the UI hierarchy instead of relying only
  on implementer-authored checks.

#### Slice W36-E7-S4 — isolated prod-like provider acceptance (`planned`)
Goal: prove the installed Studio and governed full flow against one pinned medium public-repository
task through both maintained native providers without coupling live-evaluation behavior to product
runtime semantics.

Dependencies:

- `W36-E7-S2`
- `W24-E1-S2`

Local tasks:

- `W36-E7-S4-T1` (done) Define the prod-like dual-provider execution and isolation contract for
  the canonical medium live scenario.
  - Scope: live E2E documentation and planning only.
  - Verification: docs consistency names the installed-wheel boundary, external evidence roots,
    pinned scenario/target, manual quality checkpoints, and forbidden cross-boundary state.
- `W36-E7-S4-T2` (done) Add executable preflight and architecture checks for source, target,
  provider-root, import, and scenario-specific isolation.
  - Dependencies: `W36-E7-S4-T1` as the direct queue predecessor.
  - Scope: provider-free harness and architecture tests.
  - Verification: conformance fixtures fail before live execution for overlapping roots, dirty
    tracked source, forbidden product imports, or live-scenario literals in runtime product code.
- `W36-E7-S4-T3` (done) Run `AIDD-LIVE-007` through Codex to a clean terminal result with
  manual stage-quality and rendered Studio evidence.
  - Dependencies: `W36-E7-S4-T92` as the direct replacement-candidate predecessor after the
    `W36-E7-S4-T91` dependency-direction fix and terminal post-T90 run;
    `W36-E7-S4-T88` as the prior replacement-candidate predecessor after the
    `W36-E7-S4-T87` shell-command-list evidence fix and terminal post-T86 run;
    `W36-E7-S4-T86` as the prior replacement-candidate predecessor after the
    `W36-E7-S4-T85` compound-command evidence fix and terminal post-T84 run;
    `W36-E7-S4-T84` as the prior replacement-candidate predecessor after the
    `W36-E7-S4-T83` QA-traceability fix and terminal post-T82 run, `W36-E7-S4-T82` as its prior
    candidate predecessor after `W36-E7-S4-T81`, and
    `W36-E7-S4-T37` as the exact-SHA candidate predecessor after the
    post-auth `W36-E7-S4-T60` and `W36-E7-S4-T36` gates; `W36-E7-S4-T33`, `W36-E7-S4-T32`, `W36-E7-S4-T31`, `W36-E7-S4-T30`, `W36-E7-S4-T29`, `W36-E7-S4-T28`, `W36-E7-S4-T27`, `W36-E7-S4-T26`, `W36-E7-S4-T25`, `W36-E7-S4-T24`, `W36-E7-S4-T23`, `W36-E7-S4-T22`, `W36-E7-S4-T21`, `W36-E7-S4-T20`, `W36-E7-S4-T19`, `W36-E7-S4-T18`, `W36-E7-S4-T17`, `W36-E7-S4-T16`, `W36-E7-S4-T15`, `W36-E7-S4-T14`, `W36-E7-S4-T13`, `W36-E7-S4-T2`, `W36-E7-S4-T6`, `W36-E7-S4-T10`,
    `W36-E7-S4-T11`, and `W36-E7-S4-T12` as live-discovered queue
    predecessors.
  - Scope: external Codex live execution and evidence only.
  - Verification: installed-wheel `idea -> qa`, target verification, complete audits, terminal
    reports, and bounded Chromium evidence pass from an external run root.
  - Post-T65 attempt: candidate `1dbe87a` passed public preflight and private Codex auth, then
    stopped in target setup before provider allocation because macOS Seatbelt denied the
    read-only LibreSSL configuration `/private/etc/ssl/openssl.cnf` used by HTTPS Git clone.
    The root is terminal and will not be resumed; `W36-E7-S4-T66` owns the provider-free
    isolation correction.
  - Post-T68 attempt: candidate `52bb49d` passed public preflight, private Codex auth, target
    clone, and wheel build without provider allocation, then stopped at installed-command
    discovery. The private XDG environment correctly placed the uv tool under provider-private
    data/bin while the harness expected the legacy `<install-home>/.local/bin/aidd` path.
    The terminal root will not be resumed; `W36-E7-S4-T69` owns the provider-free correction.
  - Post-T69 attempt: candidate `5cb58f3` passed public preflight, private Codex auth, target
    clone, run-owned wheel install, and public `aidd init` without provider allocation. The
    isolated `bun install` then installed packages but failed every selected lifecycle script
    with `CouldntReadCurrentDirectory`. A fresh provider-free Seatbelt reproduction has the
    same boundary; the terminal root will not be resumed and `W36-E7-S4-T71` owns the fix.
  - Post-T71 attempt: candidate `9d0bf59` passed isolated auth, target readiness, and manually
    audited `idea -> tasklist`. Implement completed task-scoped attempts T1 and T2 at the
    provider boundary, but the core canonical repair-history renderer dropped successful
    deferred attempt 1, rewrote the model-corrected `1,2,3` history to `2,3`, and then rejected
    its own non-1-based result with `SEM-INCOMPLETE-SECTION`. The root is terminal and will not
    be resumed; `W36-E7-S4-T72` owns the provider-free correction and invalidates this candidate.
  - Post-T72 attempt: candidate `44ba6d3` passed isolated auth, target readiness, exact-wheel
    identity, and strong manual audits for `idea` through `tasklist`. Implement preserved
    successful deferred attempt 1 and then selected T2, whose exact `node -e "..." -> pass`
    verification evidence was rejected because the runtime-agnostic command recognizer omits
    the standard Node.js executable. All three provider attempts exited `0`; the root is
    terminal and will not be resumed. `W36-E7-S4-T73` owns the provider-free validator fix and
    invalidates this candidate.
  - Post-T73 attempt: candidate `30e5f6a` passed isolated auth, target readiness, exact-wheel
    identity, and strong manual audits for `idea` through `tasklist`. Implement completed T1 and
    T2 provider work with passing focused Vitest and TypeScript checks, but semantic validation
    rejected the exact ``nl -ba ... | sed ...` -> pass`` inspection command as an outcome claim
    without executable evidence. Two repair attempts retained the truthful command and exhausted
    the budget. The root is terminal and will not be resumed; `W36-E7-S4-T74` owns the
    provider-free validator correction and invalidates this candidate.
  - Post-T75 attempt: candidate `9b9f504` passed isolated auth, target readiness, exact-wheel
    identity, and strong manual audits for `idea` through `tasklist`. Implement completed the
    four repository-change tasks and their focused Vitest/TypeScript checks, then rejected the
    successful verification-only T5 because its truthful task-local touched-file set was empty.
    The terminal root will not be resumed; `W36-E7-S4-T76` owns the provider-free contract fix
    and invalidates this candidate.
  - Post-T78 attempt: candidate `ead6dab` passed isolated auth, exact-wheel identity, target
    readiness, and strong manual audits through `tasklist`. Implement completed T1-T6, retained
    exactly the four allowed Hono paths, and passed its canonical validator, focused Vitest, and
    `tsc --noEmit`, but the live stage audit rejected the aggregate report because task-local
    executable evidence used `## Verification` while aggregate finalization copied only
    `## Verification notes`. The terminal root will not be resumed; `W36-E7-S4-T79` owns the
    runtime-agnostic finalization correction and invalidates this candidate.
  - Post-T80 attempt: candidate `4880ea4` passed private auth, target readiness, exact-wheel
    identity, manual quality audits through review, the exact four-file Hono implementation
    scope, focused Vitest `234/234`, and `tsc --noEmit`. QA exhausted its repair budget because
    rich-task semantic validation interpreted the contract-permitted evidence id `EV-11` as an
    additional task id. The terminal root is not resumed; `W36-E7-S4-T81` owns the provider-free
    correction and invalidates this candidate.
  - Completion evidence: fresh run `eval-live-007-codex-20260803T205243Z` used exact candidate
    `ae3131a`, tree `696633d`, wheel digest `2b3e481`, and pinned Hono revision `cf2d2b7`.
    All eight stages completed with manual stage-quality audits; the final four-file patch passed
    Vitest `236/236` and `tsc --noEmit`; terminal Chromium inspection found no console error or
    horizontal overflow. Execution, manual quality, source/session integrity, and provenance are
    independently clean. The sealed 469-file self-contained bundle has tree digest `a127580` and
    validates after the mutable work path is removed. Sanitized evidence is recorded in
    `docs/e2e/live-e2e-codex-acceptance-2026-08-03-post-t91.md`.
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
- `W36-E7-S4-T6` (done) Align active-Studio browser fixtures with the fresh terminal-handoff
  boundary exposed by the final acceptance run.
  - Dependencies: `W36-E7-S4-T2` as the discovery predecessor.
  - Scope: browser fixture expectations only; production Studio behavior is unchanged.
  - Verification: active context, Document Canvas, and Evidence Inspector use nonterminal stale
    evidence, while fresh terminal QA remains owned by Flow Complete; affected browser tests pass.
- `W36-E7-S4-T7` (done) Align generic provider-free fixture actions and markers with core-owned
  runtime selection and terminal recommendations.
  - Dependencies: `W36-E7-S4-T6` as the discovery predecessor.
  - Scope: browser fixture descriptors and next-flow test navigation only.
  - Verification: no-run selects a runtime, clean QA creates new work, warning/failed/blocked QA
    starts a follow-up, and secondary follow-up draft navigation remains durable.
- `W36-E7-S4-T8` (done) Restore the accepted 80-pixel mobile Studio header bound without reducing
  touch target size or changing desktop composition.
  - Dependencies: `W36-E7-S4-T7` as the direct queue predecessor.
  - Scope: token-driven mobile Studio layout only.
  - Verification: both mobile viewports keep a header at or below 80 pixels, 44-pixel controls,
    primary-before-maintenance order, and no horizontal overflow.
- `W36-E7-S4-T9` (done) Distinguish deliberate browser request cancellation from failed network
  requests during canonical Back/Forward/reload restoration.
  - Dependencies: `W36-E7-S4-T8` as the direct queue predecessor.
  - Scope: browser diagnostics and route-restoration tests only.
  - Verification: intentional `ERR_ABORTED` requests are recorded as cancellations while console,
    page, blocked-origin, HTTP, and real request failures remain gating.
- `W36-E7-S4-T10` (done) Allow public stepwise stage execution to continue canonically inside
  the same unbounded run without mutating its manifest identity.
  - Dependencies: `W36-E7-S4-T2` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: core run-manifest compatibility, CLI stage-run regression coverage, and planning
    reconciliation only; no scenario, provider, or target-specific branch.
  - Verification: an explicit run may advance `idea -> research -> plan` only after each prior
    stage succeeded, while skipped, failed, backward, runtime-mismatched, and config-mismatched
    reuse remains fail-closed and immutable manifest identity fields do not change.
- `W36-E7-S4-T11` (done) Route post-normalization `stage-result.md` findings through the normal
  repair budget instead of failing the stage with an orchestration exception.
  - Dependencies: `W36-E7-S4-T10` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-agnostic stage validation ordering plus core/CLI regression coverage only;
    validator codes, repair budgets, prompts, scenario manifests, and provider adapters stay
    unchanged.
  - Verification: duplicate/non-monotonic attempt history discovered after success normalization
    produces canonical validation evidence, a repair brief, and a successful bounded retry; a
    final invalid retry still exhausts the existing budget fail-closed.
- `W36-E7-S4-T12` (done) Make successful stage-result reconciliation idempotent and collapse
  duplicate canonical validator-verdict lines.
  - Dependencies: `W36-E7-S4-T11` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-agnostic stage terminal normalization and focused regression coverage only;
    validator grammar, provider adapters, prompts, and live scenario code do not change.
  - Verification: one or repeated reconciliation calls produce byte-stable Markdown with exactly
    one canonical `Validator verdict: pass` entry, including legacy input that already contains
    duplicate verdict lines.
- `W36-E7-S4-T13` (done) Materialize live allowed-write scope only from canonical
  repository-relative path prefixes declared by the authored scenario task.
  - Dependencies: `W36-E7-S4-T12` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral live scenario schema, workspace bootstrap, maintained Hono manifest,
    documentation, and provider-free harness regression coverage only; core scope semantics,
    provider adapters, prompts, and target-specific product code remain unchanged.
  - Verification: an explicit path list renders a scope accepted by `AllowedWriteScope`, invalid
    paths fail during manifest loading, and a legacy task without exact paths omits the optional
    scope document instead of creating malformed fail-closed evidence.
- `W36-E7-S4-T14` (done) Separate bounded installed-UI startup and API probe budgets for live
  frontend checkpoints.
  - Dependencies: `W36-E7-S4-T13` as the repeated live-discovery predecessor; blocks the active
    Codex acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral live harness checkpoint supervision and provider-free timeout tests
    only; UI endpoints, dashboard semantics, core orchestration, provider adapters, and scenario
    manifests remain unchanged.
  - Verification: a cold installed UI may use up to a bounded 30-second startup budget, each
    sequential API probe has a bounded 10-second response budget, slow fixtures beyond the legacy
    two-second probe boundary succeed, and true startup/probe hangs still fail with truthful
    timeout evidence and process cleanup.
- `W36-E7-S4-T15` (done) Align tasklist-plan milestone discovery with the canonical plan grammar
  accepted by production validation.
  - Dependencies: `W36-E7-S4-T14` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral cross-document milestone parsing, validator regression coverage, and
    planning reconciliation only; provider adapters, prompts, scenario manifests, and target
    product code remain unchanged.
  - Verification: list milestones written as either `- M1: description` or canonical
    `- M1 description` produce the same known milestone set, missing card references yield
    `CROSS-TASKLIST-PLAN-MILESTONE`, and dependency plus exact verification checks remain active.
- `W36-E7-S4-T16` (done) Make tasklist milestone authoring and repair guidance name the canonical
  mapping locations consumed by cross-document validation.
  - Dependencies: `W36-E7-S4-T15` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral tasklist prompt/brief guidance, cross-document finding text, repair
    evidence tests, and planning reconciliation only; the rich task grammar, provider adapters,
    scenario manifests, and target product code remain unchanged.
  - Verification: initial tasklist instructions and generated milestone repair briefs explicitly
    require M ids in `Outcome`, `Context`, acceptance criteria, or `Verification notes`; an ad hoc
    `Milestone` field remains unsupported, while a corrected canonical card validates.
- `W36-E7-S4-T17` (done) Preserve pending runtime-approval session confirmation across polling
  re-renders.
  - Dependencies: `W36-E7-S4-T16` as the full-browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: presentation-only approval confirmation state plus focused frontend/browser regression
    coverage; approval endpoints, durable decision CAS, runtime policy, and provider adapters
    remain unchanged.
  - Verification: opening `Allow session` creates no decision, a concurrent approval readback and
    `renderApprovals()` preserve the exact pending confirmation and reason, explicit confirm writes
    one durable decision, and cancel/terminal readback clears the ephemeral state.
- `W36-E7-S4-T18` (done) Reject task cards whose local `In scope` paths fall outside an authored
  canonical allowed-write scope before implementation begins.
  - Dependencies: `W36-E7-S4-T17` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral tasklist contract, cross-document validation, tasklist prompts, focused
    provider-free regression coverage, and planning reconciliation only; implementation task-diff
    enforcement, provider adapters, scenario manifests, and target product code remain unchanged.
  - Verification: a tasklist whose card scope includes any prefix outside
    `context/allowed-write-scope.md` produces an actionable `SEM-TASK-SCOPE-MISMATCH` and enters
    the normal tasklist repair budget, while exact files, permitted descendants, missing optional
    scope, malformed scope, and component boundaries remain fail-closed and deterministic.
- `W36-E7-S4-T19` (done) Keep the active Studio job identity live until terminal durable
  reconciliation and persisted-log rendering complete.
  - Dependencies: `W36-E7-S4-T18` as the full-browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: presentation-only active-job terminal reconciliation ordering plus focused frontend and
    browser regression coverage; job APIs, cancellation semantics, durable evidence, adapters,
    core orchestration, and live scenario code remain unchanged.
  - Verification: terminal polling does not clear `activeJobId` while dashboard, project-home, or
    Inbox durable readback is pending; after readback it atomically releases volatile state and
    renders persisted `runtime.log`, including the five-viewport active-Studio journey under the
    full browser lane.
- `W36-E7-S4-T20` (done) Make rich-task implementation reports describe only the current
  task-local repository diff while aggregate finalization owns cumulative touched-file evidence.
  - Dependencies: `W36-E7-S4-T19` as the live-discovery predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral Implement stage/document contracts, initial and repair prompts, focused
    provider-free prompt/contract regression coverage, and planning reconciliation only; task diff
    predicates, retry budgets, adapters, scenario manifests, and target product code remain
    unchanged.
  - Verification: in rich task mode, prerequisite files already modified before the current task
    are explicitly excluded from the task attempt's `Touched files`, current task baseline/final
    additions remain mandatory, cumulative paths appear only in aggregate finalization evidence,
    and `SEM-TASK-DIFF-MISMATCH` repair guidance removes prerequisite-only claims without reverting
    successful prior task outcomes.
- `W36-E7-S4-T21` (done) Make successful parent exit authoritative before inherited-pipe cleanup
  can cross the runtime deadline.
  - Dependencies: `W36-E7-S4-T20` as the exact-SHA full-suite discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral shared subprocess lifecycle ordering, provider-free characterization
    budgets, focused adapter regression coverage, and planning reconciliation only; provider
    adapters, runtime outcomes, scenario manifests, and target product code remain unchanged.
  - Verification: once the owned parent has exited normally, bounded descendant/pipe cleanup does
    not rewrite the result as timeout; real pre-exit timeout remains authoritative, large
    bidirectional I/O completes under a separate outer watchdog, and no descendants survive.
- `W36-E7-S4-T22` (done) Publish stage-scoped operator request Markdown atomically before readers
  can observe its canonical path.
  - Dependencies: `W36-E7-S4-T21` as the exact-SHA browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: core-owned operator intervention persistence, focused core/browser regression coverage,
    and planning reconciliation only; intervention endpoints, mutation payloads, eligibility,
    adapters, scenario manifests, and target product code remain unchanged.
  - Verification: a concurrent reader sees either no canonical `request-*.md` or the complete
    rendered document, never an empty/partial file; failed writes remove staging residue, preserve
    monotonic request identity, and create no duplicate intervention mutation.
- `W36-E7-S4-T23` (done) Parse each Implement `Touched files` list item through its canonical
  leading path token instead of treating backticked code identifiers in the change description as
  additional repository paths.
  - Dependencies: `W36-E7-S4-T22` as the Claude live-discovery predecessor; blocks the active
    provider acceptance tasks `W36-E7-S4-T3` and `W36-E7-S4-T4`.
  - Scope: runtime-neutral Implement semantic validation and focused provider-free regression
    coverage only; allowed-write policy, task-diff evidence, prompts, adapters, scenario manifests,
    and target product code remain unchanged.
  - Verification: a touched-file bullet such as ``- `src/app.py` - assign `context.error` `` checks
    only `src/app.py` against canonical scope, while malformed/missing paths and a genuinely
    out-of-scope leading path retain existing fail-closed findings.
- `W36-E7-S4-T24` (done) Keep rich-task repair history scoped to the task attempt whose global
  stage attempts it references, so a later task is not invalidated by an earlier successful task's
  retained repair evidence.
  - Dependencies: `W36-E7-S4-T23` as the direct live-discovery predecessor; blocks the active
    provider acceptance tasks `W36-E7-S4-T3` and `W36-E7-S4-T4`.
  - Scope: runtime-neutral task-attempt report/repair evidence reconciliation and focused core/
    validator regression coverage only; repair budgets, ledger schemas, provider adapters,
    scenario manifests, and target product code remain unchanged.
  - Verification: T1 may retain initial/repair references and succeed, then a clean T2 attempt
    validates without requiring a current T2 repair brief; a real current-task repair mention
    without corresponding retained evidence still fails closed.
- `W36-E7-S4-T25` (done) Replace the UI runtime-cancellation fixture's fixed one-second startup
  polling window with a bounded monotonic log synchronization helper.
  - Dependencies: `W36-E7-S4-T24` as the exact-SHA preflight discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free UI test synchronization only; UI jobs, runtime launch, cancellation,
    evidence persistence, provider adapters, and live scenario behavior remain unchanged.
  - Verification: delayed cold startup is observed within an explicit bounded deadline, missing
    startup still fails deterministically, cancellation evidence remains exact, and repeated
    isolated plus full-suite runs no longer depend on host scheduling within one second.
- `W36-E7-S4-T26` (done) Parse explicit plan milestone dependency clauses with their authored
  direction instead of treating the first milestone on a line as the dependent target.
  - Dependencies: `W36-E7-S4-T25` as the fresh Codex live-discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral tasklist/plan cross-document dependency parsing and focused validator
    regression coverage only; plan/tasklist contracts, prompts, adapters, scenario manifests, and
    provider outputs remain unchanged.
  - Verification: `M1 before M2 and M3`, `M2 and M3 after M1`, pronoun-backed `both before M4`,
    and `M4 depends on M2 and M3` produce prerequisite-to-target edges in the authored direction;
    the valid live-shaped task graph passes while a genuinely inverted task dependency fails.
- `W36-E7-S4-T27` (done) Replace the Inbox browser journey's global network-idle waits and short
  render polling with bounded server-authoritative surface synchronization.
  - Dependencies: `W36-E7-S4-T26` as the exact-SHA browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free Inbox browser journey synchronization only; Studio polling, routing,
    rendering, endpoints, service semantics, provider adapters, and live scenario behavior remain
    unchanged.
  - Verification: reload and navigation wait for DOM readiness plus the exact Inbox/Studio durable
    surface rather than global network silence; all five viewports pass repeatedly under the full
    browser lane while missing surface readback still times out deterministically.
- `W36-E7-S4-T28` (done) Recognize explicit shell-interpreter commands as executable Implement
  verification evidence instead of exhausting repair on truthful command results.
  - Dependencies: `W36-E7-S4-T27` as the fresh Codex live-discovery predecessor; blocks the active
    Codex acceptance task `W36-E7-S4-T3`.
  - Scope: runtime-neutral Implement semantic command recognition and focused provider-free
    regression coverage only; shell execution, prompts, adapters, scenario manifests, and target
    product code remain unchanged.
  - Verification: backticked `sh -c`, `bash -c`, and `zsh -c` commands with observed outcomes pass
    semantic validation, while prose-only shell names and result claims without executable
    evidence remain fail-closed.
- `W36-E7-S4-T29` (done) Use the Inbox journey's shared bounded surface budget when rendering the
  server-confirmed Running-now overlay under full-suite load.
  - Dependencies: `W36-E7-S4-T28` as the exact-SHA browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free Inbox browser journey synchronization only; job state, Inbox read model,
    polling, rendering, APIs, provider adapters, and live scenario behavior remain unchanged.
  - Verification: after the job API and Inbox read model both confirm the running identity, all
    five viewports wait through the same bounded 30-second durable-surface budget; the original
    `768x1024` case and the complete Inbox matrix pass without unbounded waits.
- `W36-E7-S4-T30` (done) Replace global network-idle navigation waits in intervention-draft and
  terminal-handoff browser journeys with bounded server-authoritative work-item surfaces.
  - Dependencies: `W36-E7-S4-T29` as the exact-SHA browser-gate discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: shared browser test synchronization plus the intervention-draft and terminal journey
    families only; Studio polling, product rendering, APIs, workflow mutations, adapters, and live
    scenario behavior remain unchanged.
  - Verification: navigation and reload wait for DOM readiness followed by the exact rendered
    work-item identity; intervention draft/submit and all five terminal viewports pass while a
    missing or wrong durable identity still times out within 30 seconds.
- `W36-E7-S4-T31` (done) Separate the live-artifact-heartbeat success fixture's scheduling budget
  from the one-second no-progress termination stress case.
  - Dependencies: `W36-E7-S4-T30` as the exact-SHA full-suite discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free live-harness test budgeting only; production lifecycle deadlines,
    no-progress classification, process supervision, scenario manifests, adapters, and provider
    behavior remain unchanged.
  - Verification: repeated heartbeat success fixtures tolerate bounded host startup jitter with a
    three-second no-progress and eight-second hard budget, while the adjacent one-second silent
    process fixture still terminates with truthful `provider-no-progress` evidence.
- `W36-E7-S4-T32` (done) Make the canonical Plan contract and prompt pack treat an authored
  `context/allowed-write-scope.md` as an exhaustive implementation-path boundary.
  - Dependencies: `W36-E7-S4-T31` as the repeated Codex live-discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: Plan-stage Markdown contract and prompt guidance plus provider-free prompt-quality
    regression only; tasklist scope validation, runtime adapters, core execution, scenario IDs,
    and target-specific paths or behavior remain unchanged.
  - Verification: initial and repair prompts require every proposed create/modify path to satisfy
    the canonical scope, forbid a new helper/module outside it, and direct the runtime to keep a
    tiny helper inside allowed files or raise a blocking question instead of broadening scope.
- `W36-E7-S4-T33` (done) Fail closed when Plan milestones or implementation strategy propose a
  repository write outside canonical `context/allowed-write-scope.md`.
  - Dependencies: `W36-E7-S4-T32` as the prompt-contract predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: Plan semantic validation, canonical validator protocol registration, repair guidance,
    and provider-free regressions only; no live IDs, target-specific paths, adapters, workflow
    execution, tasklist grammar, or allowed-scope source-of-truth changes.
  - Verification: proposed create/modify/move/delete paths in `Milestones` and `Implementation
    strategy` use the canonical component-boundary predicate; evidence paths and executable
    commands are ignored, malformed scope remains fail-closed, and a live-shaped out-of-scope
  helper produces stable `SEM-PLAN-SCOPE-MISMATCH` repair evidence.
- `W36-E7-S4-T34` (done) Record a normalized characterization of the four exact Chromium
  preflight failures before changing Studio or browser synchronization.
  - Dependencies: `W36-E7-S4-T33` as the exact-SHA preflight discovery predecessor; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free intervention and terminal browser diagnostics only; production UI,
    endpoints, mutation eligibility, provider adapters, and live scenario behavior remain
    unchanged.
  - Verification: isolated reruns identify for every failing viewport the rendered DOM revision,
    actual `/api/stage/interact` request URL/count, canonical operator-request files, archive
    decision/readback, and first decisive boundary, distinguishing a missing durable mutation
    from observer or re-render synchronization drift.
- `W36-E7-S4-T35` (done) Make Studio decision actions stable across polling re-renders through one
  shared server-authoritative mutation/render synchronization contract.
  - Dependencies: `W36-E7-S4-T34` as the characterization predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: shared Studio action dispatch/render coordination plus focused frontend and browser
    regression coverage only; viewport-specific delays, endpoint payloads, core eligibility,
    provider adapters, and live scenario branches are forbidden.
  - Verification: forced polling re-renders during intervention submit and Flow Complete archive
    produce exactly one durable mutation and stable winner readback without a detached/hidden
    action, while duplicate input remains guarded and the source run remains byte-identical.
- `W36-E7-S4-T38` (done) Characterize provider sibling-root visibility through the same
  process-launch boundary used by live acceptance.
  - Dependencies: `W36-E7-S4-T35` as the final Studio code-change predecessor; blocks the final
    Chromium candidate and active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: provider-free live-acceptance isolation fixtures and normalized diagnostics only;
    provider adapters, runtime semantics, and scenario behavior remain unchanged.
  - Verification: an executable canary proves which current source, target, provider, credential,
    and sibling-provider roots can be listed, read, or written, and unique pathnames alone never
    count as an isolation boundary.
- `W36-E7-S4-T39` (done) Enforce a provider-private filesystem and environment boundary for
  live acceptance execution.
  - Dependencies: `W36-E7-S4-T38` as the isolation characterization predecessor.
  - Scope: live-eval process launch, allowlisted environment construction, provider-private
    `HOME`/temporary/config/cache roots, and fail-closed platform capability checks only; no
    scenario-specific or target-specific product branches are allowed.
  - Verification: the T38 canary can use its authorized target and evidence roots but cannot list
    or read a sibling provider root, write the AIDD source, or observe another provider's
    credentials; a platform without an enforceable boundary reports a preflight blocker.
- `W36-E7-S4-T40` (done) Apply canonical identifier and containment checks to live run lookup
  and resume before reading flow state.
  - Dependencies: `W36-E7-S4-T39` as the provider-boundary predecessor.
  - Scope: live flow-state lookup and resume identity only; workflow semantics, provider adapters,
    and evidence schemas remain unchanged.
  - Verification: empty, absolute, separator, backslash, traversal, oversized, symlink-escape,
    scenario/runtime/work-item mismatch, and wrong-root run identities fail before any read or
    write, while a canonical interrupted run resumes with its existing lexical layout.
- `W36-E7-S4-T41` (done) Make source, target, and provider preflight/postflight integrity an
  obligatory live-acceptance session guard.
  - Dependencies: `W36-E7-S4-T40` as the contained-layout predecessor.
  - Scope: live-acceptance preflight lifecycle and source/target integrity snapshots only; build
    remains based on tracked `git archive` content and user-owned pre-existing untracked files are
    not modified.
  - Verification: provider layout is not allocated before preflight passes; tracked bytes, the
    baseline untracked set, target contamination, provider-root separation, and cleanup are read
    back after execution, and any new source file or harness payload fails closed.
- `W36-E7-S4-T42` (done) Route timeout and no-progress stage reconciliation through a public
  application boundary instead of direct harness-owned stage-status persistence.
  - Dependencies: `W36-E7-S4-T41` as the mandatory-session-guard predecessor.
  - Scope: one typed application/CLI terminal-reconciliation operation and its live-harness
    adapter only; the harness must not define an alternative stage grammar or import core status
    persistence directly.
  - Verification: an installed public surface terminalizes an abandoned executing stage with
    canonical identity and idempotent history, while a terminal or mismatched stage is not
    rewritten and the harness performs no direct stage-state write.
  - Completion: the typed compare-and-set operation now owns canonical identity validation,
    atomic `failed` persistence, and byte-stable `terminal-reconciliation.json`; the public
    `aidd stage reconcile-terminal` command exposes it to the installed target environment,
    and timeout/no-progress harness paths consume only that CLI JSON result. Application, CLI,
    adapter, architecture-boundary, timeout, and no-progress checks pass `18/18`, and the harness
    tree has no direct `persist_stage_status` import.
- `W36-E7-S4-T43` (done) Constrain manual and browser evidence imports to the authorized
  provider evidence root with symlink-safe atomic materialization.
  - Dependencies: `W36-E7-S4-T42` as the public-boundary predecessor.
  - Scope: live browser/manual evidence intake only; browser capture semantics, Studio behavior,
    and execution verdicts remain unchanged.
  - Verification: contained files and directories copy atomically, while sibling-provider paths,
    absolute escape, hard links, symlinks at every level, and partial-copy failures produce no
    trusted or partially published evidence.
  - Completion: `live_evidence_intake.py` now validates the provider `browser/` boundary with
    component-wise `lstat`, inventories only real directories and single-link regular files,
    copies through a sibling staging directory, verifies file sizes/SHA-256 and a tree digest,
    then performs one atomic publication. The positive/negative/digest/failure matrix passes
    `11/11`; both live-flow import integrations preserve their prior non-gating verdict behavior.
- `W36-E7-S4-T44` (done) Reconcile provisional running-stage frontend observations against the
  later durable stage state and post-stage checkpoint.
  - Dependencies: `W36-E7-S4-T43` as the safe-evidence predecessor.
  - Scope: live black-box frontend checkpoint classification only; Studio polling, endpoints,
    provider adapters, and the T35 mutation/render contract remain unchanged.
  - Verification: both historical `running probe fail -> stage success -> post-stage pass`
    sequences become superseded transition observations rather than provider failures, while a
    persistent frontend outage remains a truthful frontend failure.
  - Completion: the typed frontend reconciler records `provisional-pass`,
    `provisional-fail`, `superseded-transition`, and `confirmed-fail` independently from raw
    probe classifications. Durable stage status and the post-stage checkpoint now decide the
    effective frontend verdict; reconciliation is projected into JSON, Markdown, and flow-step
    details. The focused state/race/outage matrix passes `12/12`.
- `W36-E7-S4-T45` (done) Expose and reconcile stale-owner live flows without fabricating stage
  success.
  - Dependencies: `W36-E7-S4-T44` as the checkpoint-reconciliation predecessor.
  - Scope: live flow-state read model and atomic resume reconciliation only; provider completion
    events do not become stage verdicts.
  - Verification: a helper dying after provider completion but before flow-state commit is shown
    as stale, resumes idempotently as `interrupted-resumable`, retains its evidence, and never
    remains indefinitely `running` after its owner disappears.
  - Completion: `stale_owner_read_model` now projects dead-owner `running` state as
    `stale-owner` without writing, while explicit resume reloads under a directory lock, rechecks
    the complete run identity and owner, and atomically records one `interrupted-resumable`
    transition. Concurrent repeats are byte-stable; provider completion events and stage outputs
    are retained but never append completed-stage state. The full stale/resume matrix passes
    `32/32`.
- `W36-E7-S4-T46` (done) Accumulate live-flow duration across every resumed process segment.
  - Dependencies: `W36-E7-S4-T45` as the stale-flow predecessor.
  - Scope: live timing persistence and rendering only; stage execution and retry budgets remain
    unchanged.
  - Verification: a multi-resume fixture produces mutually consistent stage timing, run
    transcript duration, and retained step durations instead of resetting aggregate elapsed time
    when a new evaluator process starts.
  - Completion: `flow-state.json` schema v3 retains typed evaluator process segments with
    canonical start/finish timestamps, duration, owner PID, and termination reason. Every
    quality-review yield, interruption, stale-owner reconciliation, and terminal outcome closes
    its active segment; resume appends a new segment. Stage timing, synthetic run transcript, and
    eval summary now use the cumulative segment duration. The unit and multi-resume integration
    matrix passes `30/30`, including exact agreement across all four artifacts.
- `W36-E7-S4-T47` (done) Persist typed terminal evidence for every accepted remediation job.
  - Dependencies: `W36-E7-S4-T46` as the truthful-flow-evidence predecessor.
  - Scope: UI remediation job terminal evidence and harness readback only; Studio action
    synchronization remains owned by T35 and provider outcome semantics remain unchanged.
  - Verification: success, failure, cancellation, and operator wait retain work-item/run/stage/
    attempt identity, runtime-exit path, adapter outcome, typed first cause, and durable mutation
    winner; a retry cannot collapse to an untraceable generic `job failed` result.
  - Completion: `UiRunJobStore` now retains a typed `terminal_evidence` projection for
    completed, failed, cancelled, and waiting jobs. It includes canonical job identity,
    attempt/runtime-exit evidence, adapter outcome, durable stage-metadata winner, first
    decisive cause, and cancellation/operator-wait detail without losing an earlier request
    during cancellation. The live harness validates exact identity and schema before accepting
    remediation completion, persists typed evidence into the flow state, and carries the
    decisive cause instead of a generic failure string. The focused typed matrix passes `12/12`;
    the existing remediation, cancellation, and operator-decision compatibility matrix passes
    `35/35`.
- `W36-E7-S4-T48` (done) Preflight target installation and verification prerequisites before
  allocating a paid provider run.
  - Dependencies: `W36-E7-S4-T47` as the remediation-evidence predecessor.
  - Scope: provider-neutral target setup probes only; no Hono-, Rollup-, model-, or adapter-specific
    repair branch is allowed.
  - Verification: fresh-clone dependency installation, declared verification commands, and
    required generated/native artifacts pass a bounded smoke; the historical missing optional
    dependency shape is classified as `target-setup` before provider execution.
  - Completion: the live evaluator now completes bounded pinned-target Git preparation and
    dependency setup, then writes `target-readiness.json` before entering the stage loop. The
    typed readiness gate derives provider-free smoke commands from the selected authored task,
    defers only later `.aidd` stage/quality artifact checks, validates relative generated/native
    executables, and applies one bounded lifecycle budget. Missing prerequisites, optional
    dependencies, non-zero commands, and timeouts are classified `target-setup` with retained
    transcripts; the integration fixture proves no `run-stage` was emitted. The focused target
    matrix passes `26/26`. The completed T44–T48 lifecycle group passes repository Ruff, mypy
    across `221` modules, and all `2096` Python tests.
- `W36-E7-S4-T49` (done) Materialize canonical stage, validation, target-patch, final-report,
  and browser evidence inside a self-contained live bundle.
  - Dependencies: `W36-E7-S4-T48` as the target-readiness predecessor.
  - Scope: live result-bundle materialization and bundle-relative references only; legacy absolute
    references remain readable solely as explicitly degraded evidence.
  - Verification: deleting all mutable source/work/target roots still leaves every stage output,
    stage result, validator report, task/finalization record, target patch, final report, and
    browser artifact readable from the bundle; dangling or mismatched links fail closed.
  - Completion: terminal, blocked, and manual-quality-stop flows now invoke a separate typed
    `live_result_bundle` materializer. It copies the complete work-item stage tree and durable
    task/run evidence, final reports, audits, approval/remediation records, and browser artifacts
    into `canonical-evidence`, and records tracked plus non-ignored untracked product changes in
    `target.patch`. The published `live-result-index.json` contains only bundle-relative paths
    with size and SHA-256 readback; containment, symlink, dangling path, digest, and exact run
    identity checks fail closed. Absolute paths require an explicit `legacy-degraded` read mode.
    The source/work/target deletion matrix and terminal-flow compatibility suite pass `74/74`.
- `W36-E7-S4-T50` (done) Commit one atomic digest and provenance manifest for the complete live
  acceptance bundle.
  - Dependencies: `W36-E7-S4-T49` as the self-contained-materialization predecessor.
  - Scope: schema-v1 live bundle commit marker and readback validation only; raw evidence remains
    external and existing execution schemas stay compatible.
  - Verification: commit/tree/scenario/target identities plus SHA-256 and size for the source
    archive, wheel, stage evidence, target patch, reports, runtime evidence, and each browser file
    validate exactly; orphan browser files, wrong viewport/run identity, and digest mismatch fail.
  - Completion: a separate typed `live_bundle_manifest` sealer now materializes the exact tracked
    AIDD source archive and installed wheel into bundle provenance, records source commit/tree,
    pinned target revision, scenario/runtime/run/work-item identity, and size/SHA-256 for every
    regular bundle file, then atomically publishes `live-bundle-manifest.json` last. Its canonical
    tree digest is stable across repeat sealing. Readback revalidates the T49 index, every byte,
    the complete file inventory, and deterministic browser run/viewport identities; digest
    mutation, missing materialization, orphan browser files, and wrong browser identity all fail
    closed. The manifest, materialization, and terminal-flow matrix passes `79/79`.
- `W36-E7-S4-T51` (done) Finalize a truthful product-bundle summary after manual quality
  evidence is complete.
  - Dependencies: `W36-E7-S4-T50` as the digest-manifest predecessor.
  - Scope: product-evaluation summary writer/read model and legacy degraded-state handling only;
    the execution verdict is never rewritten retroactively.
  - Verification: pre-review, post-review, counted-clean, not-counted, and manual-quality-stop
    fixtures distinguish `execution_pass`, `quality_reviewed`, and `counted_clean`; an existing
    report cannot remain recorded as absent and no derived summary contradicts primary evidence.
  - Completion: product-evaluation summary schema v2 now independently derives
    `execution_pass`, `quality_reviewed`, `counted_clean`, `manual_quality_stop`, and
    `legacy_degraded`, with explicit not-clean reasons. Only the human-authored final decision in
    `quality-report.md` can supply counted-clean quality, while consistent flow/verdict/grader
    evidence supplies execution pass. Terminal resume is now a safe refresh operation: it updates
    the derived summary, rematerializes and reseals the bundle, but preserves `verdict.md` and
    `grader.json` bytes. The five-state unit matrix passes `5/5`, terminal pre/post-review refresh
    passes `2/2`, and all `41` live-document consistency checks pass.
- `W36-E7-S4-T52` (done) Bound ignored dependency and cache inventories in live repository
  snapshots without weakening exact product-change classification.
  - Dependencies: `W36-E7-S4-T51` as the truthful-summary predecessor.
  - Scope: live repository snapshot model only; tracked, untracked, modified, and deleted product
    paths remain exact.
  - Verification: a repository with tens of thousands of ignored files records counts, digests,
    grouping, a bounded sample, and truncation metadata within a fixed size budget while retaining
    exact product and contamination findings.
  - Completion: live workspace snapshots and classifications now persist ignored/cache paths as
    typed bounded inventories with total count, root/type group count, SHA-256 of the complete
    sorted set, a 50-path sample, and independent path/group truncation flags. Large ignored
    findings are likewise sampled with an aggregate truncation record, while tracked, modified,
    deleted, and non-ignored untracked product paths remain exact and legacy full-list snapshots
    still read. The 20,000-path fixture stays below fixed JSON budgets; the repository matrix
    passes `9/9`, the live setup-baseline flow passes, and all `41` doc checks pass.
- `W36-E7-S4-T53` (done) Read persisted runtime-log tails under an explicit byte and memory
  bound.
  - Dependencies: `W36-E7-S4-T52` as the bounded-repository-evidence predecessor.
  - Scope: canonical CLI runtime-log tail reader and its harness consumer only; full durable
    `runtime.log` persistence remains unchanged.
  - Verification: a large sparse log and one oversized JSON line return the correct bounded tail
    with explicit truncation and retained-byte metadata without loading the complete file.
  - Completion: `core/bounded_log_reader.py` now owns head/tail reads under a 256 KiB hard
    limit and reports file size, requested/retained bytes, exact start/end offsets, head/tail
    truncation, partial-line edges, and oversized-line status. Operator UI and read models use
    the shared result, `aidd run logs` no longer calls full-file `read_text()`, and live harness
    heartbeats inspect only a 4 KiB tail while durable `runtime.log` remains complete. The sparse
    64 MiB and oversized-line matrix plus CLI/read-model tests pass `12/12`, UI log API tests pass
    `5/5`, and all `41` doc checks pass.
- `W36-E7-S4-T54` (done) Normalize provider events into a bounded AIDD-owned lifecycle
  projection.
  - Dependencies: `W36-E7-S4-T53` as the bounded-log-reader predecessor.
  - Scope: runtime event normalization only; full provider-native payload remains canonical in
    `runtime.jsonl` and adapter result models remain compatible.
  - Verification: provider-free Codex, Claude, Qwen, and generic event fixtures retain lifecycle
    identity, timing, outcome, operator references, and evidence pointers without duplicating
    prompt/tool payload, under a fixed event-evidence size bound.
  - Completion: `runtime_logs/events.py` now projects provider JSON into canonical lifecycle
    rows containing only event kind, work-item/run/stage/attempt identity, available
    timestamp/duration/outcome, operator request/decision references, `runtime.jsonl` pointer,
    source, and full-payload SHA-256. Provider-native prompt/tool payload stays only in
    `runtime.jsonl`. Rows are capped at 1 KiB and the projection at 1 MiB/1,023 source events
    with a digest-backed truncation marker. Subprocess and Codex/Qwen live surfaces use the same
    projector; legacy normalized read models remain compatible. The provider/event matrix passes
    `15/15`, adapter suites `60/60`, downstream event/timeline tests `11/11`, and docs `41/41`.
- `W36-E7-S4-T55` (done) Reference canonical command evidence from live flow steps, grader, and
  aggregate transcript instead of embedding full stdout and stderr repeatedly.
  - Dependencies: `W36-E7-S4-T54` as the bounded-event-projection predecessor.
  - Scope: live report serialization and legacy readers only; public terminal outcomes and raw
    runtime-log contents remain unchanged.
  - Verification: a high-output fixture retains byte-equivalent access through canonical evidence
    pointers while bundle size grows linearly and no derived report contains another full copy of
    the runtime output.
  - Completion: `live_command_evidence.py` now persists each command result once as an atomic,
    content-addressed JSON record and emits bundle-relative pointer, SHA-256, size, exit/duration,
    timeout metadata, and 2 KiB stdout/stderr previews. Flow steps, lifecycle transcripts,
    operator requests, grader, run transcript, and aggregate runtime-log projection no longer
    embed complete streams; verified readers retain legacy inline compatibility. Canonical bundle
    materialization avoids copying the evidence owner a second time. The 1 MiB linear-growth,
    digest-tamper, legacy-read, successful-flow, timeout-flow, bounded-inventory, and module
    boundary matrix passes `12/12`; the closing `T49–T55` group gate passes Ruff, mypy over
    `src scripts`, and the complete Python suite `2125/2125`.
- `W36-E7-S4-T56` (done) Clear only the submitted intervention draft after its matching
  durable mutation wins across asynchronous Studio re-renders.
  - Dependencies: discovered by the failed `W36-E7-S4-T36` acceptance attempt after
    `W36-E7-S4-T55`; blocks the next `W36-E7-S4-T36` rerun.
  - Scope: shared intervention draft/mutation reconciliation and focused frontend/browser
    regressions only; endpoint payloads, core eligibility, provider adapters, and
    viewport-specific waits remain unchanged.
  - Verification: forced identity/render changes after an OK intervention response clear the
    immutable submitted draft exactly once while preserving newer or non-matching drafts; the
    complete five-viewport intervention family passes repeatedly with one durable request.
  - Completion: matching intervention readback and cleanup now both use the immutable draft
    identity captured by the submitted action, and cleanup happens immediately after the durable
    request winner is visible instead of waiting behind runtime-job polling. Deterministic route
    identity shift, duplicate, conflict, pre-existing-winner, and newer-draft cases pass in the
    full frontend suite `98/98`; the three historical viewports pass `3/3`, the complete
    intervention family passes `14/14`, and CLI/static contract coverage passes `60/60`.
- `W36-E7-S4-T57` (done) Replace History journey global network-idle navigation with the
  shared bounded server-authoritative work-item and History surface synchronization.
  - Dependencies: `W36-E7-S4-T56` as the direct queue predecessor; blocks the next
    `W36-E7-S4-T36` rerun.
  - Scope: History browser journey synchronization only; History product rendering, retained-run
    state, APIs, provider adapters, and timeout values remain unchanged.
  - Verification: all five History viewports pass repeatedly using DOM readiness plus exact
    durable work-item/History identity, while missing or wrong identity still times out within
    the shared 30-second surface budget.
  - Completion: initial History navigation, Back restoration, and reload now wait for
    `domcontentloaded`, the exact work-item chip, and the exact current lineage run under the
    shared bounded surface helper instead of global network idleness. The five-viewports plus
    wrong-run fail-closed matrix passes `6/6`; the historical `1440x900` case passes two
    additional independent reruns, and browser-harness/docs/planning checks pass `51/51`.
- `W36-E7-S4-T58` (done) Return the synchronously persisted intervention-request winner in the
  accepted UI job envelope and reconcile the submitted draft from that identity.
  - Dependencies: `W36-E7-S4-T56` and `W36-E7-S4-T57`; discovered by the second failed
    `W36-E7-S4-T36` attempt and blocks its next rerun.
  - Scope: public operator UI stage-interact acceptance boundary and focused CLI/frontend/browser
    regressions only; stage-interact CLI semantics, runtime execution, dashboard rendering,
    provider adapters, and viewport-specific timing remain unchanged.
  - Verification: the POST response contains the exact canonical request id/path/excerpt before
    the runtime job can hold later readback, one prepared request is reused by execution without
    duplication, and all five intervention viewports clear only the submitted draft while the
    runtime remains running.
  - Completion: the stage-interact acceptance boundary now validates and persists one typed
    intervention request before launching the background job, returns its canonical
    work-item/run/stage/id/path/excerpt envelope, and passes that same prepared request into
    execution without a second write. Frontend reconciliation validates the accepted envelope
    against the immutable submitted descriptor and clears only that draft before job polling,
    while retaining dashboard readback as a compatibility fallback. Focused CLI/frontend
    coverage passes `17/17`; the full intervention/browser/static selection passes `28/28`;
    and all five allowed viewports prove one request, an empty submitted draft, and a still-running
    runtime job.
- `W36-E7-S4-T36` (done) Re-run the complete provider-free Chromium acceptance matrix after the
  final provider-neutral hardening change.
  - Dependencies: `W36-E7-S4-T80` as the current direct queue predecessor;
    `W36-E7-S4-T79` as the preceding aggregate-evidence correction;
    `W36-E7-S4-T78` as the preceding fixture-cleanup correction;
    `W36-E7-S4-T77` as the preceding aggregate-finalization correction;
    `W36-E7-S4-T75` as the preceding browser synchronization predecessor;
    `W36-E7-S4-T74` as the preceding verification-evidence correction;
    `W36-E7-S4-T73` as the preceding verification-evidence correction;
    `W36-E7-S4-T72` as the preceding incremental-stage correction;
    `W36-E7-S4-T71` as the preceding isolation correction;
    `W36-E7-S4-T69` as the preceding run-owned install correction;
    `W36-E7-S4-T68` as the preceding terminal-projection correction;
    `W36-E7-S4-T67` as the preceding active-job ownership correction;
    `W36-E7-S4-T66` as the preceding isolation-backend correction;
    `W36-E7-S4-T65` as the preceding terminal-reconciliation correction;
    `W36-E7-S4-T64` as the preceding browser synchronization correction;
    `W36-E7-S4-T63` as the preceding intervention synchronization correction;
    `W36-E7-S4-T62` as the preceding isolation-backend correction;
    `W36-E7-S4-T61` as the preceding browser synchronization correction;
    `W36-E7-S4-T60`, `W36-E7-S4-T58`,
    `W36-E7-S4-T55`,
    `W36-E7-S4-T56`, and `W36-E7-S4-T57` as earlier code-change predecessors; blocks the
    active Codex acceptance task `W36-E7-S4-T3`.
  - Scope: browser acceptance evidence only; no product or fixture behavior changes.
  - Verification: the four discovered cases, both complete intervention/terminal journey
    families, and the full browser suite pass across all five viewports with clean console,
    page/request diagnostics and bounded process cleanup.
  - Failed attempt: source commit `5bbe2c9` and Chromium `149.0.7827.55` produced `3/4`
    historical cases, `24/24` complete intervention/terminal family cases, exact packaged
    discovery/execution for all 12 journeys with `W36-E7-S1-T10` at `13/14`, and the complete
    browser suite at `186/187`. The two independent first boundaries are post-success matching
    intervention-draft cleanup at `320x568`/`1440x900` and History's initial global
    `networkidle` wait at `1440x900`; sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-26.md`.
  - Second failed attempt: after `T56/T57`, source `cff519b` passed `2/4` historical cases but
    retained the submitted draft at `320x568` and `1280x900` despite an OK POST and one
    canonical request. Later layers were not run. The remaining boundary is the accepted job
    envelope, which does not expose the synchronously persisted request winner before runtime
    execution can delay dashboard readback; `W36-E7-S4-T58` owns that output.
  - Completion: the clean post-`T58` source `17213af` and tree `601aeb7` passed the exact
    historical matrix `4/4`, complete intervention/terminal families `24/24`, all twelve
    packaged registry journeys `79/79` with identical discovered/executed IDs and no failed ID,
    and the full Chromium suite `188/188` in `2617.84s`. All five viewports completed with clean
    console, page, request, overflow, accessibility, and bounded process-cleanup diagnostics;
    the sanitized evidence record is
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-26.md`.
  - Revalidation: `W36-E7-S4-T60` changed the tracked candidate after this completion evidence;
    rerun the same no-fixes Chromium matrix on the new clean source before another candidate is
    named.
  - Post-auth completion: clean source `314aedf`, tree `9703b02`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4`, complete
    intervention/terminal families `24/24`, all twelve packaged journeys `79/79` with identical
    discovered/executed IDs and no failed ID, and the full browser suite `188/188`. Every
    viewport completed without console, page, failed-request, overflow, accessibility, or
    test-owned process-cleanup failure. The sanitized evidence is
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-27.md`.
  - Post-merge revalidation attempt: clean source `bbed868` passed the historical matrix `4/4`
    in `84.44s`, complete intervention/terminal families `24/24` in `338.35s`, and all twelve
    packaged journeys `79/79` with exact discovered/executed ID parity and no failed ID. The
    complete browser suite stopped after its first failure at `108` passing tests: the
    `runtime-no-progress` Recovery fixture exceeded the 30-second global `networkidle` navigation
    wait before any durable product assertion. Isolated rerun passed `1/1` in `77.82s`, confirming
    a suite-order synchronization race. `W36-E7-S4-T61` owns the provider-free correction; this
    attempt is not accepted T36 evidence.
  - Post-T61 completion: clean source `21c12ed`, tree `7185fbd`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `80.71s`, complete
    intervention/terminal families `24/24` in `342.98s`, all twelve packaged journeys `79/79`
    with exact discovered/executed ID parity and no failed ID, and the full browser suite
    `188/188` in `2720.11s`. All five viewports completed without console, page, failed-request,
    overflow, accessibility, or test-owned process-cleanup failure. The sanitized evidence is
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28.md`.
  - Post-T64 completion: clean source `143cc1e`, tree `2efec8e`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `79.62s`, complete
    intervention/terminal families `24/24` in `351.27s`, all twelve packaged journeys
    `79/79` in `2099.53s` with exact discovered/executed ID parity and no failed ID, and the
    full browser suite `188/188` in `2662.12s`. All five viewports completed without console,
    page, failed-request, overflow, accessibility, or test-owned process-cleanup failure.
    Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28-post-t64.md`.
  - Post-T65 completion: clean source `b38dd4c`, tree `8facd6e`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `90.99s`, complete
    intervention/terminal families `24/24` in `332.59s`, all twelve packaged journeys `79/79`
    in `2185.87s` with exact discovered/executed ID parity and no failed ID, and the full browser
    suite `188/188` in `3274.98s`. All five viewports completed without console, page,
    failed-request, overflow, accessibility, or test-owned process-cleanup failure. Sanitized
    evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-28-post-t65.md`.
  - Post-T66 attempt: clean source `0e1aa84` passed historical cases `4/4` in `116.80s` and
    intervention/terminal families `24/24` in `365.04s`. The packaged registry then passed its
    first journey `5/5`, but active Studio reported `4/5`: tablet `768x1024` retained
    `activeJobId` beyond 15 seconds after recovered-log cancellation. The registry was stopped
    before the next journey and later layers did not run. `W36-E7-S4-T67` owns the remaining
    bounded nonterminal cancellation reconciliation race.
  - Post-T67 attempt: clean source `1a2b012`, tree `84bd68d`, passed historical cases `4/4`
    in `121.64s` and complete intervention/terminal families `24/24` in `518.19s`. After
    Guided Setup passed `5/5`, packaged active Studio reported `4/5`: desktop
    `1440x900` retained `activeJobId` beyond 15 seconds after a recovered-log cancellation.
    The registry was stopped before the next journey and the complete browser suite did not
    run. `W36-E7-S4-T68` owns the remaining delayed-cancellation terminal handoff.
  - Post-T68 completion: clean source `cb12e5b`, tree `6d26af7`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `156.57s`,
    complete intervention/terminal families `24/24` in `822.19s`, all twelve packaged
    journeys `79/79` in `2149.14s` with exact discovered/executed ID parity and no failed
    ID, and the full browser suite `188/188` in `2861.70s`. All five viewports completed
    without console, page, failed-request, overflow, accessibility, or test-owned
    process-cleanup failure. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-29-post-t68.md`.
  - Post-T69 completion: clean source `aa02a40`, tree `2905378`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `130.32s`,
    complete intervention/terminal families `24/24` in `652.53s`, all twelve packaged
    journeys `79/79` in summed `2415.26s` with exact discovered/executed ID parity and no
    failed ID, and the full browser suite `188/188` in `2841.88s`. All five viewports
    completed without console, page, failed-request, overflow, accessibility, or test-owned
    process-cleanup failure. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-07-29-post-t69.md`.
  - Post-T71 completion: clean source `ef38a3f`, tree `944906b`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `114.91s`, complete
    intervention/terminal families `24/24` in `585.43s`, all twelve packaged journeys `79/79`
    in summed `1834.28s` with exact discovered/executed ID parity and no failed ID, and the full
    browser suite `188/188` in `2422.40s`. All five viewports completed without console, page,
    failed-request, overflow, accessibility, or test-owned process-cleanup failure. Sanitized
    evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-01-post-t71.md`.
  - Post-T72 completion: clean source `bb465ea`, tree `6d43544`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `67.48s`, complete
    intervention/terminal families `24/24` in `297.36s`, all twelve packaged journeys `79/79`
    in summed `1451.49s` with exact discovered/executed ID parity and no failed ID, and the full
    browser suite `188/188` in `2457.28s`. All five viewports completed without console, page,
    failed-request, overflow, accessibility, or test-owned process-cleanup failure. Sanitized
    evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-01-post-t72.md`.
  - Post-T73 completion: clean source `edde5b7`, tree `65f52b5`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `209.69s`, complete
    intervention/terminal families `24/24` in `503.14s`, all twelve packaged journeys `79/79`
    in summed `2184.39s` with exact discovered/executed ID parity and no failed ID, and a fresh
    uninterrupted full browser suite `188/188` in `3264.76s`. All five viewports completed
    without console, page, failed-request, overflow, accessibility, or test-owned process-cleanup
    failure. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-02-post-t73.md`.
  - Post-T74 failed attempt: clean source `1882dc4`, tree `c6869ac`, passed the historical
    matrix `4/4` in `178.15s`, intervention/terminal families `24/24` in `324.26s`, and the
    packaged registry `79/79` with exact discovered/executed parity and `failed_ids=[]`. The
    fresh full suite then reported its first failure at Inbox
    `test_inbox_prioritizes_and_routes_durable_and_running_work[viewport3]` after `78` passing
    cases. That exact case passed once in isolation and once again at the same full-order
    position; the remaining test-only five-second provider-job/read-model polls are below the
    declared 30-second surface budget. `W36-E7-S4-T75` owns bounded phase diagnostics and
    synchronization before T36 restarts; no product or fixture fix was made inside this gate.
  - Post-T75 completion: clean source `5d37cae`, tree `374b94b`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `131.60s`, complete
    intervention/terminal families `24/24` in `408.31s`, all twelve packaged journeys `79/79`
    in summed `1813.28s` with exact discovered/executed ID parity and no failed ID, and a fresh
    uninterrupted full browser suite `188/188` in `1975.10s`. All five viewports completed
    without console, page, failed-request, overflow, accessibility, or test-owned process-cleanup
    failure. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-02-post-t75.md`.
  - Post-T76 completion: clean source `acd48ce`, tree `43c1e97`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the exact historical matrix `4/4` in `117.09s`, complete
    intervention/terminal families `24/24` in `496.55s`, all twelve packaged journeys `79/79`
    with identical discovered/executed IDs and `failed_ids=[]`, and one fresh uninterrupted full
    browser suite `188/188` in `2114.35s`. All five viewports completed without console, page,
    failed-request, overflow, accessibility, or test-owned process-cleanup failure. Sanitized
    evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-02-post-t76.md`.
  - Post-T77 failed attempt: after a clean process baseline, source `102366b` passed the exact
    historical matrix `4/4`, complete intervention/terminal families `24/24`, and all twelve
    packaged journeys `79/79` with exact discovered/executed ID parity and `failed_ids=[]`.
    Postflight then found one orphaned Inbox `browser_fixture_runtime.py` owned by the final
    `1440x900` case, so the full Chromium layer was not launched. `W36-E7-S4-T78` owns the
    provider-free fixture cleanup correction; no live provider ran.
  - Post-T78 completion: clean source `a05a58e`, tree `7b5ce6a`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the historical matrix `4/4` in `72.66s`, complete
    intervention/terminal families `24/24` in `289.46s`, all twelve packaged journeys `79/79`
    with exact discovered/executed ID parity and `failed_ids=[]`, and one fresh uninterrupted
    full browser suite `188/188` in `2054.64s`. All five viewports completed without console,
    page, failed-request, overflow, accessibility, or process-cleanup failure; explicit packaged
    and full-suite postflights were empty. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t78.md`.
  - Post-T79 completion: clean source `c040f0e`, tree `75fe019`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the historical matrix `4/4` in `68.84s`, complete
    intervention/terminal families `24/24` in `282.31s`, all twelve packaged journeys `79/79`
    in summed `1394.59s` with exact discovered/executed ID parity and `failed_ids=[]`, and one
    fresh uninterrupted full browser suite `188/188` in `2071.90s`. All five viewports completed
    without console, page, failed-request, overflow, accessibility, or process-cleanup failure;
    the final process postflight was empty. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t79.md`.
  - Post-T80 completion: clean source `403129a`, tree `fe3bd4c`, Playwright `1.61.0`, and
    Chromium `149.0.7827.55` passed the historical matrix `4/4` in `79.28s`, complete
    intervention/terminal families `24/24` in `313.57s`, all twelve packaged journeys `79/79`
    in summed `1506.17s` with exact discovered/executed ID parity and `failed_ids=[]`, and one
    fresh uninterrupted full browser suite `188/188` in `2164.92s`. All five viewports completed
    without console, page, failed-request, overflow, accessibility, or process-cleanup failure;
    the process preflight and postflight were empty. Sanitized evidence is in
    `docs/e2e/operator-ui-provider-free-browser-gate-2026-08-03-post-t80.md`.
- `W36-E7-S4-T37` (done) Prove the exact post-browser candidate is installable and ready for an
  isolated live-provider run.
  - Dependencies: `W36-E7-S4-T36` as the full-browser predecessor; blocks the active Codex
    acceptance task `W36-E7-S4-T3`.
  - Scope: candidate wheel, full static/Python/browser gates, doctor/eval-doctor, target readiness,
    source integrity, self-contained-bundle smoke, and executable provider-isolation evidence
    only; no production, scenario, provider, or target changes.
  - Verification: one wheel built from clean tracked `HEAD` is bound to its commit/tree/digest and
    loaded from an isolated install; full checks, `aidd doctor`, the selected provider's
    `aidd eval doctor`, target preflight, source tracked/untracked baseline, bundle finalization,
    and selected-provider isolation canary pass on that recorded SHA before a live layout is
    allocated. Deferred providers remain parked and are not covered by the candidate record.
  - Completion: clean candidate `43d740c`, tree `a780ce9`, source-archive digest
    `b416b44`, and wheel digest `b93257d` pass Ruff, mypy, Python `2126/2126`, Chromium
    `188/188`, isolated install/doctor, both provider eval-doctors, fresh pinned Hono setup and
    authored smoke, bundle seal/readback after target deletion, public preflight, dual
    `macos-seatbelt` canaries, and source-integrity postflight. The exact candidate and sanitized
    signals are recorded in `docs/e2e/candidate-readiness-2026-07-26.md`; later evidence commits
    do not replace or rebuild that wheel.
  - Revalidation: the `43d740c` record remains immutable historical evidence, but the
    post-`W36-E7-S4-T60` `T36` result must produce a new tracked-archive wheel, digest, private
    auth probes, and source postflight before provider acceptance resumes.
  - Current revalidation: source `c5747a0`, tree `2a946c5`, and tracked-index digest
    `bfce0b0` pass Ruff, mypy across `228` modules, and the complete Python suite
    `2145/2145`. The exact-SHA Chromium run was operator-stopped after `67` passing tests;
    it is incomplete evidence, not a browser failure. No tracked archive, wheel, candidate
    digest, installed doctor result, target readiness, bundle smoke, private-auth probe, or
    source postflight has been accepted yet. Resume `T37` by restarting the full Chromium
    suite on unchanged `c5747a0`, then complete the remaining readiness gates before naming a
    candidate.
  - Post-T61 completion: clean candidate `98d97c7`, tree `ebda9cd`, tracked-index digest
    `01f9da4`, tracked-archive digest `098d587`, and wheel digest `3b6b8cf` pass Ruff, mypy
    across `228` modules, Python `2145/2145`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight,
    dual private-auth `macos-seatbelt` canaries, and source-integrity postflight. The Claude
    probe uses the launcher's explicit single-key credential allowlist for the active
    `ANTHROPIC_AUTH_TOKEN`; no credential value or digest is recorded. The exact identities
    and sanitized signals are in `docs/e2e/candidate-readiness-2026-07-28.md`; this record
    commit does not replace or rebuild the candidate wheel.
  - Post-T64 attempt: exact source `3cee858` passes Ruff, mypy across `228` modules, and the
    complete Python suite `2146/2146`. Its exact-SHA Chromium gate reports `186/188`: both mobile
    active-Studio cases time out after a recovered live connection receives an immediate
    terminal cancellation response but retains the volatile active-job identity. The same pair
    passes `2/2` in isolation, identifying a suite-load-dependent terminal-reconciliation race
    owned by `W36-E7-S4-T65`. No archive, wheel, doctor, target, bundle, auth-probe, provider, or
    large-scenario gate ran after this browser failure.
  - Post-T65 completion: clean candidate `1dbe87a`, tree `075e9fa`, tracked-index digest
    `c11d307`, tracked-archive digest `0f7135d`, and wheel digest `3b38a55` pass Ruff, mypy
    across `228` modules, Python `2146/2146`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight,
    dual private-auth `macos-seatbelt` sessions, and source-integrity postflight. The Claude
    probe receives only the explicitly selected `ANTHROPIC_AUTH_TOKEN`; no credential value or
    digest is recorded. The exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-07-28-post-t65.md`; this record commit does not replace or
    rebuild the candidate wheel.
  - Post-T68 completion: clean candidate `52bb49d`, tree `b699659`, tracked-index digest
    `0f6d7ef`, tracked-archive digest `75105f0`, and wheel digest `90a4247` pass Ruff, mypy
    across `228` modules, Python `2146/2146`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight,
    dual private-auth `macos-seatbelt` sessions and visibility canaries, and source-integrity
    postflight. The Claude probe receives only the explicitly selected
    `ANTHROPIC_AUTH_TOKEN`; no credential value or digest is recorded. The exact identities
    and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-07-29-post-t68.md`; this record commit does not replace
    or rebuild the candidate wheel.
  - Post-T69 completion: clean candidate `5cb58f3`, tree `90953e1`, tracked-index digest
    `cfbf294`, tracked-archive digest `349fc3e`, and wheel digest `a7e72c1` pass Ruff, mypy
    across `228` modules, Python `2147/2147`, an uninterrupted exact-SHA Chromium
    `188/188`, isolated install/doctor, both provider eval-doctors, fresh pinned Hono setup
    with Vitest `233/233` and `tsc --noEmit`, bundle seal/readback after mutable-root
    deletion, public preflight, dual private-auth `macos-seatbelt` sessions and visibility
    canaries, and source-integrity postflight. One rejected host-saturation browser attempt
    is recorded without changing source or timeouts; the three exact cases, their 37-case
    predecessor, and the subsequent complete suite all pass. The exact identities and
    sanitized signals are in `docs/e2e/candidate-readiness-2026-07-29-post-t69.md`; this
    record commit does not replace or rebuild the candidate wheel.
  - Post-T71 completion: clean candidate `9d0bf59`, tree `8354d0a`, tracked-index digest
    `b89a31c`, tracked-archive digest `f4ef417`, and wheel digest `0964977` pass Ruff, mypy
    across `228` modules, Python `2149/2149`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight,
    dual private-auth `macos-seatbelt` sessions and visibility canaries, and source-integrity
    postflight. The Claude probe receives only the explicitly selected
    `ANTHROPIC_AUTH_TOKEN`; no credential value or digest is recorded. The exact identities
    and sanitized signals are in `docs/e2e/candidate-readiness-2026-08-01-post-t71.md`; this
    record commit does not replace or rebuild the candidate wheel.
  - Post-T72 completion: clean candidate `44ba6d3`, tree `f28f428`, tracked-index digest
    `8339ec6`, tracked-archive digest `bb7c0b0`, and wheel digest `1ea5b09` pass Ruff, mypy
    across `228` modules, Python `2150/2150`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight,
    dual private-auth `macos-seatbelt` sessions and visibility canaries, and source-integrity
    postflight. The Claude probe receives only the explicitly selected
    `ANTHROPIC_AUTH_TOKEN`; no credential value or digest is recorded. The exact identities
    and sanitized signals are in `docs/e2e/candidate-readiness-2026-08-01-post-t72.md`; this
    record commit does not replace or rebuild the candidate wheel.
  - Post-T73 completion: clean candidate `30e5f6a`, tree `a4bf5c4`, tracked-index digest
    `734b607`, tracked-archive digest `4c63a6e`, and wheel digest `472c771` pass Ruff, mypy
    across `228` modules, Python `2153/2153`, exact-SHA Chromium `188/188`, isolated
    install/doctor, both provider eval-doctors, fresh pinned Hono setup with Vitest `233/233`
    and `tsc --noEmit`, bundle seal/readback after mutable-root deletion, dual private-auth
    `macos-seatbelt` sessions and visibility canaries, and source-integrity postflight. The
    Claude probe receives only the explicitly selected `ANTHROPIC_AUTH_TOKEN`; no credential
    value or digest is recorded. Exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-08-02-post-t73.md`; this record commit does not replace
    or rebuild the candidate wheel.
  - Post-T75 Codex-scoped completion: clean candidate `9b9f504`, tree `9051118`, tracked-index
    digest `a98d253`, tracked-archive digest `75ff5a0`, and wheel digest `b74d5fc` pass Ruff,
    mypy across `228` modules, Python `2158/2158`, exact-SHA Chromium `188/188`, isolated
    install/doctor, Codex eval-doctor, fresh pinned Hono setup with Vitest `233/233` and
    `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight, Codex
    private-auth `macos-seatbelt` session and visibility canary, and source-integrity postflight.
    Exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-08-02-post-t75.md`; this record commit does not replace
    or rebuild the candidate wheel. Claude readiness and live execution remain unclaimed and
    parked under the current Codex-only scope.
  - Post-T76 Codex-scoped completion: clean candidate `c26820c`, tree `a46ed39`, tracked-index
    digest `e2acd4f`, tracked-archive digest `45f6174`, and wheel digest `469df0b` pass Ruff,
    mypy across `228` modules, Python `2165/2165`, exact-SHA Chromium `188/188`, isolated
    install/doctor, Codex eval-doctor, fresh pinned Hono setup with Vitest `233/233` and
    `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight, Codex
    private-auth `macos-seatbelt` session and visibility canary, and source-integrity postflight.
    Exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-08-02-post-t76.md`; this record commit does not replace
    or rebuild the candidate wheel. Claude readiness and live execution remain unclaimed and
    parked under the current Codex-only scope.
  - Post-T78 Codex-scoped completion: clean candidate `ead6dab`, tree `cfbc108`, tracked-index
    digest `4b373d3`, tracked-archive digest `9d87bfd`, and wheel digest `dc11248` pass Ruff,
    mypy across `228` modules, Python `2168/2168`, exact-SHA Chromium `188/188`, isolated
    install/doctor, Codex eval-doctor, fresh pinned Hono setup with Vitest `233/233` and
    `tsc --noEmit`, bundle seal/readback after mutable-root deletion, public preflight, Codex
    private-auth `macos-seatbelt` readiness, a standalone visibility canary, and source-integrity
    postflight. Exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-08-03-post-t78.md`; this record commit does not replace
    or rebuild the candidate wheel. Claude readiness and live execution remain unclaimed and
    parked under the current Codex-only scope.
  - Post-T79 Codex-scoped completion: clean candidate `abbc4d6`, tree `bc10c57`, tracked-index
    digest `42b9dca`, tracked-archive digest `93a46bc`, and wheel digest `78f4d11` pass Ruff,
    mypy across `228` modules, Python `2168/2168`, exact-SHA Chromium `188/188`, isolated
    install/doctor, Codex eval-doctor, fresh pinned Hono setup with Vitest `233/233` and
    `tsc --noEmit`, bundle seal/readback after mutable-root deletion, provider-private Codex auth
    readiness, a standalone `macos-seatbelt` capability canary, and source-integrity postflight.
    Exact identities and sanitized signals are in
    `docs/e2e/candidate-readiness-2026-08-03-post-t79.md`; this record commit does not replace or
    rebuild the candidate wheel. Claude readiness and live execution remain unclaimed and parked
    under the current Codex-only scope.
  - Post-T80 Codex-scoped completion: clean candidate `4880ea4`, tree `3ec3904`, tracked-index
    digest `bb9c0a0`, tracked-archive digest `cca520a`, and wheel digest `300bf16` pass Ruff,
    mypy across `228` modules, Python `2170/2170`, exact-SHA Chromium `188/188`, isolated
    install/doctor, Codex eval-doctor, fresh pinned Hono setup with Vitest `233/233` and
    `tsc --noEmit`, installed-candidate bundle deletion/readback, provider-private Codex auth,
    `macos-seatbelt` isolation, and source-integrity postflight. Exact identities and sanitized
    signals are in `docs/e2e/candidate-readiness-2026-08-03-post-t80.md`; this record commit does
    not replace or rebuild the candidate wheel. Claude readiness and live execution remain
    unclaimed and parked under the current Codex-only scope.
- `W36-E7-S4-T59` (done) Seed one allowlisted native-provider authentication snapshot into a
  fresh provider-private home without exposing the operator's remaining state.
  - Dependencies: the `W36-E7-S4-T3` private-home authentication discovery after
    `W36-E7-S4-T37`.
  - Scope: one typed live-harness auth-seed module and its focused provider-free tests only;
    launcher, session lifecycle, core, adapters, prompts, validators, and Studio remain unchanged.
  - Verification: opaque Codex `.codex/auth.json` and Claude Code `.claude.json` fixtures copy
    atomically to their exact relative destinations with private modes, while traversal,
    symlink, hard-link, oversized, and injected-copy-failure cases publish no partial credential
    file and expose no credential bytes, absolute source path, or digest in the result.
  - Completion: the typed seed operation derives the sole source and destination from a strict
    Codex/Claude Code runtime allowlist, validates every in-home component with `lstat`, rejects
    linked, non-regular, changed, existing, or larger-than-1-MiB credentials, and publishes a
    digest-verified staging copy with `0700/0600` modes. Its result exposes only runtime,
    relative destination, byte count, and `seeded` status; the positive and negative matrix
    passes `11/11`.
- `W36-E7-S4-T60` (done) Require provider-private authentication seeding and an isolated status
  probe before the live evaluator can start.
  - Dependencies: `W36-E7-S4-T59` as the typed snapshot predecessor; invalidates the recorded
    `W36-E7-S4-T36` and `W36-E7-S4-T37` candidate evidence when implementation changes land.
  - Scope: live isolation launcher, preflight/session evidence, prod-like runbook, and focused
    harness regressions only; core, adapters, prompts, validators, and Studio remain unchanged.
  - Verification: fake Codex and Claude Code binaries cross the real subprocess/isolation
    boundary, seeded private homes pass their status probe and launch an evaluator sentinel,
    unseeded homes return a `provider-auth` blocker without launching it, resume reuses existing
    private credentials, and reports remain credential-redacted with source read-only and sibling
    provider roots denied.
  - Completion: the launcher now requires `codex|claude-code`, permits the minimal T59 seed only
    for a fresh provider root, runs the runtime-specific status command inside the same OS
    boundary, and launches the evaluator only after a zero exit. Resume retains and reprobes the
    private credential without recopying. Preflight defers host auth with explicit
    `provider-private/pending-isolated-probe` state; session schema v2 records only runtime, seed
    mode, relative destination, probe status, and private-state cleanup. Both fake runtimes pass
    seeded and fail unseeded through real Seatbelt while operator HOME, sibling state, and source
    writes remain denied; focused launcher tests pass `17/17`, harness passes `378/378`, Ruff and
    mypy pass, and the complete Python suite passes `2145/2145`.
- `W36-E7-S4-T61` (done) Replace the runtime/validation Recovery browser journey's global
  navigation-idle waits with bounded work-item surface readiness.
  - Dependencies: discovered by the failed post-merge `W36-E7-S4-T36` revalidation after
    `W36-E7-S4-T60`; blocks the next `W36-E7-S4-T36` rerun.
  - Scope: `browser_tests/test_journey_runtime_validation_recovery.py` navigation synchronization
    only; production Studio, fixtures, timeout budgets, and recovery semantics remain unchanged.
  - Verification: the isolated `runtime-no-progress` case passes repeatedly, the complete
    runtime/validation Recovery family passes across all five viewports and parity selectors,
    diagnostics stay clean, and no global `networkidle` navigation remains in that journey.
  - Completion: all initial navigation and reload boundaries in the Recovery journey now wait
    for `domcontentloaded` followed by the exact work-item chip instead of global network idle.
    The isolated `runtime-no-progress` case passes `3/3`; the full runtime/validation Recovery
    file passes `9/9` across all viewports and parity selectors; Ruff passes and the file contains
    no remaining `networkidle` wait. Production Studio, fixture state, and timeout budgets are
    unchanged.
- `W36-E7-S4-T62` (done) Authorize the active macOS developer toolchain as a read-only live
  provider dependency so target Git setup can execute inside Seatbelt.
  - Dependencies: discovered by the first post-T37 Codex acceptance attempt before provider
    allocation; invalidates the `98d97c7` candidate and blocks its `T36 -> T37` replacement.
  - Scope: typed macOS isolation-backend tool-root discovery, focused harness regression, and
    prod-like runbook clarification only; core, adapters, prompts, validators, Studio, target
    setup semantics, and provider commands remain unchanged.
  - Verification: a real Seatbelt child executes `/usr/bin/git clone --no-local` through the
    same launcher boundary while the selected developer root and source remain read-only, the
    own provider root remains writable, and operator HOME plus sibling provider roots remain
    denied.
  - Completion: the macOS backend resolves `xcode-select --print-path` only when it names an
    existing developer directory below trusted `/Applications` or `/Library/Developer` roots,
    then includes that exact directory in the read-only tool roots used by Seatbelt. A real
    boundary regression executes `/usr/bin/git clone --no-local` into the own provider root,
    proving the previously blocked `libxcrun` path while the generated profile grants writes
    only below that provider. Focused isolation checks pass `3/3`, auth/session checks pass
    `41/41`, the complete harness passes `379/379`, Ruff and mypy pass, and the full Python
    run has `2145` passing tests; its sole initial failure was the corrected planning dependency
    edge from T62 to T36, whose planning/docs rerun passes `50/50`.
- `W36-E7-S4-T63` (done) Replace the downstream-blocked intervention journey's global
  navigation-idle wait with bounded exact work-item surface readiness.
  - Dependencies: discovered by the failed post-T62 `W36-E7-S4-T36` revalidation; blocks the
    next complete browser gate.
  - Scope: one initial navigation boundary in
    `browser_tests/test_journey_intervention_recovery.py`; production Studio, intervention
    semantics, fixtures, viewport coverage, and timeout budgets remain unchanged.
  - Verification: the isolated `390x844` case passes repeatedly, the complete intervention and
    terminal families pass `24/24`, diagnostics remain clean, and the downstream-blocked case no
    longer waits for global `networkidle`.
  - Completion: the downstream-blocked intervention case now waits for `domcontentloaded`
    followed by the exact fixture work-item chip before selecting the Plan surface. The
    `390x844` failure passes `3/3` in isolation, and the complete intervention/terminal families
    pass `24/24` in `599.24s` with clean diagnostics. Ruff and standard mypy pass; the full
    Python run has `2145` passing tests and only the subsequently corrected planning-status
    mismatch failed.
- `W36-E7-S4-T64` (done) Replace the Implement journey's global initial navigation-idle waits
  with bounded exact work-item and runtime surface readiness.
  - Dependencies: discovered by the failed post-T63 `W36-E7-S4-T36` complete browser suite;
    blocks the next complete browser gate.
  - Scope: initial navigation boundaries in `browser_tests/test_journey_implementation.py`;
    production Studio, implementation evidence, fixtures, viewport coverage, and timeout budgets
    remain unchanged.
  - Verification: the implementation-recovery case passes repeatedly, the complete Implement
    journey file passes, diagnostics remain clean, and no initial navigation in that journey
    waits for global `networkidle`.
  - Completion: both Implement journey entry points now wait for `domcontentloaded`, the exact
    fixture work-item chip, and selected-runtime readiness before rendering implementation
    evidence. The recovery case passes `3/3` across its five-viewport loop, the complete
    Implement file passes `2/2` in `64.58s`, and no `networkidle` wait remains in the file.
    Ruff and standard mypy pass; the full Python run has `2145` passing tests and only the
    subsequently corrected planning-status mismatch failed.
- `W36-E7-S4-T65` (done) Reconcile an immediate terminal cancellation response through the same
  durable active-job boundary used by terminal polling.
  - Dependencies: discovered by the failed post-T64 `W36-E7-S4-T37` exact-SHA Chromium gate;
    blocks the next complete `W36-E7-S4-T36` rerun.
  - Scope: active-Studio cancellation reconciliation and its provider-free frontend/browser
    regressions only; job persistence, runtime adapters, scenario fixtures, providers, and
    timeout budgets remain unchanged.
  - Verification: an immediate terminal cancel result preserves the active identity until
    dashboard, project, and inbox readback finish, then clears volatile job state; a
    nonterminal `cancelling` result continues polling, and a pre-cancel in-flight poll cannot
    overwrite either outcome. Both failed mobile active-Studio cases pass repeatedly with clean
  diagnostics. PR #414 (merge `2534cdef`) completed the compact header implementation; the remaining
  tablet shell ordering/density issue is tracked as T45.
  - Completion: cancellation captures the immutable job identity before mutation, sends immediate
    terminal responses through the existing durable dashboard/project/inbox reconciliation, and
    retains scheduled polling only for active statuses. Frontend tests pass `99/99`; the two
    failed mobile cases pass `3/3` repeated pairs; the complete active-Studio journey passes
    `5/5`; Ruff, mypy across `228` modules, planning integrity, and the complete Python suite
    `2146/2146` pass.
- `W36-E7-S4-T66` (done) Authorize the active macOS system TLS configuration as a read-only live
  provider dependency for HTTPS target setup.
  - Dependencies: discovered by the first post-T65 Codex acceptance attempt before provider
    allocation; invalidates candidate `1dbe87a` and blocks its `T36 -> T37` replacement.
  - Scope: typed macOS isolation-backend TLS-root discovery, focused real-Seatbelt regression,
    and prod-like runbook clarification only; Git target semantics, providers, core, adapters,
    prompts, validators, Studio, and scenario behavior remain unchanged.
  - Verification: a real Seatbelt child can read the exact trusted system TLS configuration
    required by `/usr/bin/git` while that root, the selected developer toolchain, and AIDD source
    remain read-only; own provider state remains writable and operator HOME plus sibling state
    remain denied. The regression must not require provider credentials or a public network.
  - Completion: the macOS backend includes the fixed real `/private/etc/ssl` directory only when
    it exists as a non-symlink system directory, then grants it through the same read-only tool
    roots used by Seatbelt. A real boundary regression reads `openssl.cnf`, retains the local Git
    clone proof, and asserts no TLS write rule; a separate provider-free production-like check
    completes the previously failing HTTPS Hono clone. Focused checks pass `2/2`, the complete
    isolation/auth/session selection passes `55/55`, Ruff and mypy pass, and full pytest passes
    `2146/2146`.
- `W36-E7-S4-T67` (done) Suppress stale dashboard recovery of an active-job identity after
  durable terminal reconciliation.
  - Dependencies: discovered by the failed post-T66 `W36-E7-S4-T36` packaged active-Studio
    journey; blocks the next complete browser gate.
  - Scope: active-Studio terminal identity ownership and provider-free frontend/browser
    regressions only;
    backend cancellation semantics, adapters, providers, fixtures, scenario behavior, and timeout
    budgets remain unchanged.
  - Verification: terminal dashboard/project/inbox readback records one browser-local tombstone
    for the immutable job id, so a concurrent stale `cancelling` dashboard payload cannot
    resurrect it; a genuinely new job clears the tombstone and retains normal polling. The
    active-Studio journey passes repeatedly across all five viewports after its packaged
    predecessor, without increasing the 15-second assertion budget.
  - Completion: terminal reconciliation now records the immutable active job id before clearing
    volatile state; dashboard recovery ignores that tombstoned id and a genuinely new launch
    clears the tombstone. The exact Guided Setup predecessor passes `5/5`, followed by three
    strict sequential active-Studio runs at `5/5` each; frontend passes `99/99`, Ruff and mypy
    pass, and the repeated complete Python suite passes `2146/2146`. One earlier unrelated
    100-millisecond process-start assertion missed its child PID under load, then passed `5/5`
    in isolation and in the complete rerun; no process code or timeout changed.
- `W36-E7-S4-T68` (done) Make a nonterminal cancellation request converge through one bounded
  terminal handoff even when the runtime stop and browser poll complete under suite load.
  - Dependencies: discovered by the failed post-T67 `W36-E7-S4-T36` packaged active-Studio
    journey; blocks the next complete browser gate.
  - Scope: UI job cancellation completion, active-Studio polling ownership, and focused
    provider-free regressions only; adapters, providers, scenario fixtures, and the existing
    15-second browser assertion budget remain unchanged.
  - Verification: a cancellation response that starts as `cancelling` cannot remain the volatile
    browser winner after the owned runtime process has stopped; terminal job evidence is
    reconciled once, stale polls cannot restore it, and the packaged Guided Setup predecessor
    followed by active Studio passes repeatedly across all five viewports.
  - Completion: terminal polling now accepts the typed terminal job plus dashboard active-job
    readback as the durable winner, clears the volatile identity, and renders terminal/log state
    before refreshing the heavier project-home and inbox projections behind a protected
    asynchronous boundary. Provider-free diagnostics proved that the runtime job and dashboard
    were already terminal while those derived projections could exceed the browser budget under
    load. Frontend tests pass `99/99`, static asset contracts pass `49/49`, three consecutive
    active-Studio matrices pass `5/5`, the exact Guided Setup predecessor followed by active
    Studio passes `10/10`, Ruff and mypy across `228` modules pass, and full pytest passes
    `2146/2146`; the 15-second browser assertion budget is unchanged.
- `W36-E7-S4-T69` (done) Keep local-wheel uv tool installation inside the selected live run when
  the process already has provider-private XDG roots.
  - Dependencies: discovered by the first post-T68 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `52bb49d` and blocks its `T36 -> T37` replacement.
  - Scope: provider-neutral harness install environment, focused install regression, and
    production-like no-provider smoke only; core, adapters, prompts, validators, Studio,
    scenario behavior, provider auth, and isolation policy remain unchanged.
  - Verification: the install helper explicitly owns both uv tool storage and bin roots below
    `<run>/install-home`, even when inherited `XDG_DATA_HOME` and related variables point at the
    provider-private session. The returned absolute `aidd` command exists under that run, the
    wheel digest remains the candidate digest, and no executable is published into shared
    provider-private data/bin state.
  - Completion: local-wheel installation now sets explicit run-owned `UV_TOOL_DIR` and
    `UV_TOOL_BIN_DIR` paths in addition to the existing run-owned HOME and cache. The focused
    inherited-private-XDG regression proves the returned command stays below install-home and
    shared provider-private bin remains absent. A real no-provider uv build/install smoke
    confirms the same boundary with a valid wheel and executable. Focused checks pass `16/16`,
    the complete harness regression passes `380/380`, Ruff and mypy across `228` modules pass,
    and full pytest passes `2147/2147`.
- `W36-E7-S4-T71` (done) Make macOS live isolation support dependency lifecycle subprocesses
  whose package manager resolves a transient working directory outside the selected target.
  - Dependencies: discovered by the first post-T69 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `5cb58f3` and blocks its `T36 -> T37` replacement.
  - Scope: typed macOS isolation dependency discovery, focused real-Seatbelt Bun lifecycle
    regression, and runbook clarification only; target commands, Bun package semantics,
    providers, core, adapters, prompts, validators, Studio, and scenario behavior remain
    unchanged.
  - Verification: a fresh Hono clone inside the own provider root completes `bun install`
    lifecycle scripts through the same Seatbelt boundary while AIDD source and any additional
    dependency roots stay read-only, own provider state remains writable, and operator HOME,
    sibling provider state, and credentials remain denied.
  - Completion: the macOS profile now grants `file-read*` only to exact `literal` ancestor
    directory objects required by package-manager environment discovery, never to their
    subtrees. Layouts below operator HOME fail before provider allocation. A real Seatbelt Bun
    lifecycle fixture and a fresh pinned Hono clone both complete through the production launch
    boundary; the post-install canary keeps source read-only and denies sibling provider,
    operator HOME, and credential access. Focused isolation tests pass `20/20`, the complete
    harness regression passes `382/382`, Ruff and mypy across `228` modules pass, and full pytest
    passes `2149/2149`.
- `W36-E7-S4-T72` (done) Preserve a successful deferred stage attempt before a later incremental
  implementation task enters validation or repair.
  - Dependencies: discovered by the failed post-T71 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `9d0bf59` and blocks its `T36 -> T37` replacement.
  - Scope: runtime-agnostic core stage-attempt persistence and focused provider-free regressions
    only; adapters, provider commands, live scenario behavior, prompts, validators, and Studio
    remain unchanged.
  - Verification: when task-scoped success defers stage publication to `pending`, canonical
    attempt evidence retains attempt 1 as `succeeded`; a later attempt and repair can therefore
    render a positive, unique, strictly increasing `1,2,3` history without canonical persistence
    deleting the first entry.
  - Completion: deferred successful validation now persists its attempt entry before the stage
    transitions to `pending`. The regression proves attempt 1 remains in metadata and canonical
    `stage-result.md`; focused stage-runner/repair/validator checks pass `150/150`, and the CLI
    plus incremental implementation lifecycle matrix passes `58/58`. Ruff and mypy across `228`
    modules pass, and the unchanged diff passes the complete Python suite `2150/2150`; two
    fake-runtime startup/barrier tests from the first host-loaded attempt pass `10/10` in five
    isolated repetitions before the clean complete rerun.
- `W36-E7-S4-T73` (done) Recognize the standard Node.js executable as concrete implementation
  verification command evidence.
  - Dependencies: discovered by the failed post-T72 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `44ba6d3` and blocks its `T36 -> T37` replacement.
  - Scope: runtime-agnostic implementation-verification command recognition and focused
    semantic-validator regressions only; stage contracts, prompts, providers, adapters, live
    scenario behavior, core orchestration, and Studio remain unchanged.
  - Verification: a backticked `node -e "..." -> pass` block is accepted as executable evidence,
    while bare prose and non-command Node-related artifacts remain rejected; the focused
    implement semantic matrix and planning integrity pass.
  - Completion: the runtime-agnostic command recognizer now treats `node` as an executable only
    in concrete command shapes, while bare Node.js prose remains non-evidence. The focused
    semantic matrix passes `47/47`, the saved live report revalidates with no findings, Ruff and
    mypy across `228` modules pass, planning integrity passes `9/9`, and the complete Python suite
    passes `2153/2153`.
- `W36-E7-S4-T74` (done) Recognize a concrete `nl`-based source-inspection pipeline as executable
  Implement verification evidence.
  - Dependencies: discovered by the failed post-T73 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `30e5f6a` and blocks its `T36 -> T37` replacement.
  - Scope: Implement Markdown contract clarification, runtime-agnostic verification-command
    recognition, the existing medium scenario audit rubric, and focused provider-free semantic
    regressions only; providers, adapters, core orchestration, target code, and Studio remain
    unchanged.
  - Verification: the saved live-shaped ``nl -ba src/hono-base.ts | sed -n ...` -> pass`` bullet
    validates as concrete command evidence, while bare `nl` prose, filenames, and outcome claims
    without an executable command remain fail-closed; focused validator and planning-integrity
    checks pass.
  - Completion: the Implement contract now explicitly accepts concrete read-only inspection
    pipelines, and the runtime-agnostic command recognizer treats `nl` as executable only in a
    command-shaped fragment with arguments. Bare prose and `.nl` filenames remain non-evidence;
    focused validator checks pass `51/51`, contract/scenario/planning checks pass `80/80`, the
    saved T2 live report revalidates with zero findings, Ruff and mypy across `228` modules pass,
    and the complete Python suite passes `2157/2157`.
- `W36-E7-S4-T75` (done) Use the Inbox journey's shared surface budget for provider-job and
  durable running-read-model preconditions with phase-specific timeout evidence.
  - Dependencies: discovered by the failed post-T74 `W36-E7-S4-T36` full Chromium run; blocks
    the next no-fixes T36 restart.
  - Scope: provider-free Inbox browser synchronization and focused browser regressions only;
    product UI/API behavior, provider execution, fixture semantics, viewport matrix, and timeout
    policy remain unchanged.
  - Verification: delayed provider-job and Inbox read-model convergence may use the existing
    bounded 30-second operator-surface budget, missing convergence still fails with the phase and
    last durable payload, and the complete Inbox family plus exact full-order prefix through
    `viewport3` pass without test-owned processes surviving.
  - Completion: both provider-job and Inbox running-read-model polls now use one typed bounded
    helper and the existing 30-second operator-surface budget; timeout evidence reports the exact
    phase and last durable payload. The fail-closed diagnostic unit passes `1/1`, the Inbox family
    passes `9/9`, and the canonical first-79 full-order prefix through the previously failing
    `1280x900` case passes `79/79`. Ruff and mypy across `228` modules pass, planning integrity
    passes `9/9`, and the clean complete Python rerun passes `2158/2158`.
- `W36-E7-S4-T76` (done) Distinguish verification-only rich implementation tasks from unsupported
  no-op repository-change attempts.
  - Dependencies: discovered by the failed post-T75 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `9b9f504` and blocks its `T36 -> T37` replacement.
  - Scope: Tasklist and Implement Markdown contracts, typed task-plan/selection evidence,
    runtime-agnostic Implement semantic validation, matching prompts, and focused provider-free
    regressions only; providers, adapters, live scenario literals, target code, and Studio remain
    unchanged.
  - Verification: an explicitly classified `verification-only` rich task with exact command
    outcomes and an empty task-local diff validates and reaches aggregate finalization, while an
    unclassified or repository-change no-op with completion claims remains rejected by the
    existing incomplete-summary and missing-diff findings.
  - Completion: Tasklist cards now carry typed `repository-change` or explicit
    `verification-only` execution mode into system-owned task selection and the task read model.
    Implement semantic validation accepts `- none` only for an explicitly selected
    verification-only rich task, while repository evidence rejects any actual task-local edit;
    ordinary unclassified no-op completion claims remain fail-closed. Focused task/validator
    checks pass `142/142`, the broader core/validator/task group passes `945/945`, Ruff and mypy
    across `228` modules pass, planning integrity passes `9/9`, and the clean complete Python
    rerun passes `2165/2165`.
- `W36-E7-S4-T77` (done) Validate mixed repository-change and verification-only aggregate
  implementation evidence with an explicit finalization mode.
  - Dependencies: discovered by the failed post-T76 Codex acceptance attempt after
    `W36-E7-S4-T37`; invalidates candidate `c26820c` and blocks its `T36 -> T37` replacement.
  - Scope: typed aggregate-finalization validation context, aggregate implementation-report
    rendering, and focused provider-free core/application/validator regressions only; task-local
    fail-closed validation, providers, adapters, prompts, contracts, scenario literals, target
    code, and Studio remain unchanged.
  - Verification: a mixed plan with repository-change tasks followed by an explicit
    verification-only task publishes one aggregate report containing the real changed files and
    no synthetic `- none` entry; its validator uses the system-owned aggregate execution mode,
    while a verification-only task-local report with any actual file entry remains rejected.
  - Completion: aggregate finalization derives one typed effective execution mode from the full
    task plan, filters task-local `- none` entries when real repository paths exist, and passes
    that system-owned mode to semantic validation without weakening selected-task checks. The
    saved post-T76 mixed live ledger now renders exactly the four real Hono paths without
    `- none`, and its saved aggregate report revalidates with zero findings; the task-local
    negative case remains rejected. Focused checks pass `33/33`, the broader implementation
    group passes `130/130`, Ruff and mypy across `228` modules pass, planning integrity passes
    `9/9`, and the complete Python suite passes `2168/2168`.
- `W36-E7-S4-T78` (done) Reconcile the Inbox browser fixture's running runtime before the UI
  harness exits.
  - Dependencies: discovered by the failed post-T77 `W36-E7-S4-T36` packaged-runner postflight;
    blocks the next complete `W36-E7-S4-T36` rerun.
  - Scope: provider-free Inbox browser fixture lifecycle and focused process-cleanup evidence
    only; production UI shutdown semantics, runtimes, adapters, providers, prompts, validators,
    scenario literals, and Studio behavior remain unchanged.
  - Verification: the Inbox running-now journey cancels its test-owned job through the public
    endpoint, observes a durable terminal status, and proves the fixture runtime PID has exited
    after every viewport, including `1440x900`; a focused postflight finds no UI or runtime
    orphan.
  - Completion: the Inbox fixture now publishes its test-owned runtime PID, cancels the job
    through the public endpoint in a fail-safe cleanup block, waits for durable `cancelled`, and
    proves the recorded process has exited before the viewport case completes. The formerly
    orphaning `1440x900` case passes `1/1`, the complete Inbox family passes `9/9` across all five
    viewports with an empty external process postflight, Ruff and mypy across `228` modules pass,
    and the complete Python suite passes `2168/2168`.
- `W36-E7-S4-T79` (done) Preserve task-local executable verification in aggregate Implement
  finalization evidence.
  - Dependencies: discovered by the failed post-T78 Codex acceptance attempt; invalidates
    candidate `ead6dab` and blocks its `T36 -> T37` replacement.
  - Scope: runtime-agnostic aggregate implementation-report rendering and focused provider-free
    finalization/audit regressions only; task-local validation, providers, adapters, prompts,
    contracts, scenario literals, target code, and Studio remain unchanged.
  - Verification: task reports using either canonical `## Verification` or legacy
    `## Verification notes` contribute executable command/outcome lines to the aggregate report;
    a realistic mixed Implement aggregate has nonzero backed evidence and passes the stage-audit
    policy, while reports with unbacked verification claims remain fail-closed.
  - Completion: aggregate finalization now prefers the canonical `Verification` section and
    falls back to legacy `Verification notes`, preserving executable task-local bullets before
    adding criterion pointers. Re-rendering the saved post-T78 six-task ledger changes the live
    audit shape from zero to `62` backed evidence lines with `48` outcome claims. Focused checks
    pass `3/3`, the broader implementation/harness regression passes `120/120`, Ruff and mypy
    across `228` modules pass, planning integrity passes `9/9`, and the complete Python suite
    passes `2168/2168` without weakening the existing evidence classifier.

- `W36-E7-S4-T80` (done) Parse only canonical leading attempt identities from Stage Result
  attempt-history entries.
  - Dependencies: discovered by the failed post-T79 Codex acceptance attempt; invalidates
    candidate `abbc4d6` and blocks its `T36 -> T37` replacement.
  - Scope: runtime-agnostic Stage Result semantic validation and focused provider-free
    regressions only; core orchestration, providers, adapters, prompts, contracts, scenario
    literals, target code, and Studio remain unchanged.
  - Verification: live-shaped attempt-history bullets may reference their own
    `attempt-000N/...` evidence paths without creating duplicate attempt identities, while
    duplicate, non-positive, and out-of-order leading attempt entries remain fail-closed.
  - Completion: Stage Result validation now extracts the canonical leading identity from each
    attempt-history bullet and ignores incidental attempt ids inside evidence paths. The
    live-shaped evidence-path regression passes while duplicate leading identities remain
    fail-closed; focused validator/core checks pass `393/393`, planning integrity passes `9/9`,
    Ruff and mypy across `228` modules pass, and the complete Python suite passes `2170/2170`.

- `W36-E7-S4-T81` (done) Do not interpret a structured QA evidence reference as an additional
  task identity.
  - Dependencies: discovered by the terminal post-T80 Codex acceptance attempt; invalidates
    candidate `4880ea4` and blocks its `T36 -> T37 -> T3` replacement.
  - Scope: runtime-agnostic rich-task evidence semantic validation and focused provider-free
    regressions only; core orchestration, providers, adapters, prompts, contracts, scenario
    literals, target code, and Studio remain unchanged.
  - Verification: a canonical task acceptance entry may cite a permitted `EV-N` reference or a
    task-scoped artifact path without either reference being counted as a second task id, while
    unknown and mismatched task/acceptance pairs remain fail-closed.
  - Completion: rich-task validation now derives task and acceptance identity only from the
    structured fields before `Evidence:`. The live-shaped regression contains both a task id and
    `EV-11` inside the evidence path and again in notes without creating a false second task;
    focused validator/cross-document checks pass `56/56`, planning integrity passes `9/9`, Ruff
    and mypy across `228` modules pass, and the complete Python suite passes `2170/2170`.

- `W36-E7-S4-T82` (done) Refresh the Codex-only exact-SHA candidate after T81.
  - Dependencies: `W36-E7-S4-T81` as the validator-fix predecessor; blocks the fresh
    `W36-E7-S4-T3` acceptance run.
  - Scope: provider-free full Chromium revalidation plus tracked-archive wheel, isolated install,
    doctor/eval-doctor, pinned Hono readiness, bundle smoke, private Codex auth/isolation probe,
    and source postflight; no Claude, Qwen, large, human, or product-code changes.
  - Verification: one immutable source SHA/tree and wheel digest passes the accepted T36/T37
    Codex-only readiness bar and becomes the sole artifact used by the next T3 run.
  - Completion: candidate `09b8d6a`, tree `8bba6dd`, tracked archive digest `9f10c8b`, and
    wheel digest `6db06bc` pass the Codex-only readiness bar. The exact-SHA Chromium suite passes
    `188/188`; bundle/manifest/isolation regressions pass `29/29`; isolated install, doctor,
    Codex eval-doctor, private-auth Seatbelt readiness, fresh pinned Hono setup, Vitest
    `233/233`, `tsc --noEmit`, and source postflight all pass. Sanitized evidence is recorded in
    `docs/e2e/candidate-readiness-2026-08-03-post-t81.md`; T3 is now the next task.

- `W36-E7-S4-T83` (done) Resolve QA-local evidence ids through their declared upstream
  artifact references.
  - Dependencies: discovered by the terminal post-T82 Codex acceptance attempt; invalidates
    candidate `09b8d6a` and blocks its `T36 -> T37 -> T3` replacement.
  - Scope: runtime-agnostic QA cross-document traceability and focused provider-free regressions
    only; core orchestration, providers, adapters, prompts, contracts, scenario literals, target
    code, and Studio remain unchanged.
  - Verification: an `EV-N` defined in the QA Evidence section is reusable from verification,
    readiness, acceptance, and task-acceptance entries only when its definition contains an
    existing full workspace-relative upstream/context artifact path; missing, basename-only, and
    circular local evidence remains fail-closed.
  - Completion: QA cross-document validation now derives reusable local evidence ids only from
    Evidence definitions backed by an existing full upstream/context artifact path. A focused
    positive and circular-negative matrix passes, the exact terminal live QA report revalidates
    with zero findings, the validator suite passes `296/296`, planning integrity passes `9/9`,
    Ruff and mypy across `228` modules pass, and the complete Python suite passes `2172/2172`.

- `W36-E7-S4-T84` (done) Refresh the Codex-only candidate after T83 without reopening deferred
  provider lanes.
  - Dependencies: `W36-E7-S4-T83`; blocks the next fresh `W36-E7-S4-T3` acceptance run.
  - Scope: exact-commit tracked archive/wheel, isolated install and doctor/eval-doctor, saved-QA
    regression, pinned Hono readiness, bundle smoke, private Codex auth/isolation probe, and
    source postflight. The already accepted post-T81 full Chromium evidence remains applicable
    because T83 changes only provider-free Markdown cross-document validation; no UI, harness,
    core, adapter, prompt, contract, Studio, or browser code changed.
  - Verification: one immutable source SHA/tree and wheel digest passes the Codex-only readiness
    checks affected by T83 and becomes the sole artifact used by the next T3 run.
  - Completion: candidate `912f444`, tree `5fb8486`, tracked archive digest `3260f35`, and wheel
    digest `4e1fe07` pass the affected Codex-only readiness bar. Ruff, mypy, Python `2172/2172`,
    validators `296/296`, saved terminal QA revalidation, bundle/manifest/isolation `29/29`,
    isolated install/doctor/eval-doctor, private-auth Seatbelt readiness, fresh pinned Hono setup,
    Vitest `233/233`, `tsc --noEmit`, and source postflight pass. The unchanged browser surfaces
    retain the accepted post-T81 Chromium `188/188` evidence. Sanitized evidence is recorded in
    `docs/e2e/candidate-readiness-2026-08-03-post-t83.md`; T3 is now next.

- `W36-E7-S4-T85` (done) Recognize complete shell compound checks as executable Implement
  verification evidence.
  - Dependencies: discovered by the terminal post-T84 Codex acceptance attempt; invalidates
    candidate `912f444` and blocks its replacement candidate and fresh `W36-E7-S4-T3` run.
  - Scope: the runtime-agnostic Implement evidence classifier, documented contract/prompt,
    focused validator regressions, and the maintained medium scenario rubric only; core,
    adapters, providers, target code, Studio, and browser behavior remain unchanged.
  - Verification: complete backticked `if ...; then ...; else ...; fi` checks containing a
    concrete executable are accepted with an observed outcome, while shell-like prose remains
    fail-closed.
  - Completion: the exact terminal T3 Implement report changes from one blocking
    `SEM-UNVERIFIABLE-CHECK-CLAIM` finding to zero without editing its evidence. Positive and
    negative compound-command regressions pass in the focused `31/31` suite; Ruff and mypy pass.

- `W36-E7-S4-T86` (done) Refresh the Codex-only candidate after T85.
  - Dependencies: `W36-E7-S4-T85`; blocks the next fresh `W36-E7-S4-T3` acceptance run.
  - Scope: provider-free repository gates, tracked-archive wheel, isolated install and doctor,
    pinned Hono readiness, bundle/isolation smoke, private Codex auth probe, and source postflight.
    Reuse the accepted post-T81 Chromium evidence because T85 changes only Markdown validation,
    its contract/prompt, tests, and scenario rubric; no UI, harness, Studio, or browser code changed.
  - Verification: one immutable source SHA/tree and wheel digest passes all Codex-only readiness
    checks affected by T85 and becomes the sole artifact used by the next T3 run.
  - Completion: candidate `4b2856f`, tree `9137bc3`, tracked archive digest `c8769e7`, and wheel
    digest `f9e9f98` pass the affected Codex-only readiness bar. Ruff, mypy, exact-candidate Python
    `2174/2174`, validators `298/298`, saved terminal Implement revalidation, bundle/manifest/
    isolation `29/29`, isolated install/doctor/eval-doctor, private-auth Seatbelt readiness,
    fresh pinned Hono setup, Vitest `233/233`, `tsc --noEmit`, and source postflight pass. The
    unchanged browser surfaces retain the accepted post-T81 Chromium `188/188` evidence.
    Sanitized evidence is recorded in `docs/e2e/candidate-readiness-2026-08-03-post-t85.md`;
    T3 is now next.

- `W36-E7-S4-T87` (done) Recognize a complete shell compound command when it is surrounded by
  command-list setup and trailing checks.
  - Dependencies: discovered by the terminal post-T86 Codex acceptance attempt; invalidates
    candidate `4b2856f` and blocks its replacement candidate and fresh `W36-E7-S4-T3` run.
  - Scope: runtime-agnostic Implement evidence classification, documented contract/prompt,
    focused regressions, and maintained medium scenario rubric only; core, adapters, providers,
    target code, Studio, and browser behavior remain unchanged.
  - Verification: a backticked command list shaped as `name=$(command); if ...; fi; check` is
    accepted only when the compound syntax closes and the list contains a concrete executable;
    shell-like prose remains fail-closed.
  - Completion: the exact terminal T3 T1 report changes from one blocking
    `SEM-UNVERIFIABLE-CHECK-CLAIM` finding to zero without editing its evidence. The focused
    positive/negative evidence matrix passes `32/32` and Ruff passes.

- `W36-E7-S4-T88` (done) Refresh the Codex-only candidate after T87.
  - Dependencies: `W36-E7-S4-T87`; blocks the next fresh `W36-E7-S4-T3` acceptance run.
  - Scope and verification: repeat the affected Codex-only exact-SHA readiness bar from T86,
    including repository gates, tracked-archive wheel, isolated install/doctor, saved-report
    regression, bundle/isolation smoke, pinned Hono readiness, private auth, and source postflight;
    retain the accepted unchanged-browser Chromium evidence explicitly.
  - Completion: candidate `7726023`, tree `1f89bd2`, tracked archive digest `9a9cf26`, and wheel
    digest `29b43f7` pass the affected Codex-only readiness bar. Ruff, mypy, exact-candidate Python
    `2175/2175`, validator/prompt/packaging/planning `382/382`, saved terminal Implement
    revalidation, bundle/manifest/isolation `29/29`, isolated install/doctor/eval-doctor,
    private-auth Seatbelt readiness, fresh pinned Hono setup, Vitest `233/233`, `tsc --noEmit`,
    and source postflight pass. Sanitized evidence is recorded in
    `docs/e2e/candidate-readiness-2026-08-03-post-t87.md`; T3 is now next.

- `W36-E7-S4-T89` (done) Accept bounded QA-local command evidence without weakening upstream
  traceability.
  - Dependencies: discovered by the terminal post-T88 Codex acceptance attempt; invalidates
    candidate `7726023` and blocks its replacement candidate and fresh `W36-E7-S4-T3` run.
  - Scope: align the runtime-agnostic QA contract, prompt, and cross-document validator so an
    `EV-N` definition may be grounded either in an existing exact upstream/context artifact or
    in a syntactically executable QA-local command with an explicit terminal outcome. Reuse the
    shared command-evidence classifier; do not add provider, scenario, target, core, adapter, or
    Studio branches.
  - Verification: the exact terminal QA report accepts post-QA status, ignored-residue, file,
    and artifact-presence commands while prose, circular ids, basename-only paths, commands
    without outcomes, and outcome claims without executable commands remain fail-closed.
  - Completion: QA cross-document validation reuses the shared executable-command classifier and
    requires an explicit terminal outcome before a QA-local `EV-N` becomes reusable. The exact
    terminal post-T88 QA report revalidates from eight blocking occurrences to zero without
    editing its evidence; focused validator/prompt/scenario/planning tests pass `432/432`, Ruff
    passes, mypy passes `228` modules, and the complete Python suite passes `2178/2178`.

- `W36-E7-S4-T90` (done) Refresh the Codex-only candidate after T89.
  - Dependencies: `W36-E7-S4-T89`; blocks the next fresh `W36-E7-S4-T3` acceptance run.
  - Scope and verification: repeat the affected provider-free repository, validator, prompt,
    packaging, tracked-archive wheel, isolated install/doctor, pinned Hono readiness,
    bundle/isolation, private Codex auth, and source-integrity gates; retain unchanged-browser
    evidence explicitly.
  - Completion: candidate `5a53614`, tree `b1877a8`, tracked archive digest `143e406`, and
    byte-repeatable wheel digest `e057790` pass the affected Codex-only readiness bar. Ruff,
    mypy, Python `2178/2178`, validator/prompt/scenario/planning `432/432`, exact terminal QA
    revalidation, bundle/manifest/session/isolation/auth `52/52`, isolated install/doctor/
    eval-doctor, private-auth Seatbelt readiness, fresh pinned Hono setup, Vitest `233/233`,
    `tsc --noEmit`, and source postflight pass. The unchanged browser surfaces retain the
    post-T81 Chromium `188/188` evidence. Sanitized evidence is recorded in
    `docs/e2e/candidate-readiness-2026-08-03-post-t89.md`; T3 is now next.

- `W36-E7-S4-T91` (done) Preserve dependency direction when one plan sentence contains
  more than one milestone relation.
  - Dependencies: discovered by the terminal post-T90 Codex acceptance attempt; invalidates
    candidate `5a53614` and blocks its replacement candidate and fresh `W36-E7-S4-T3` run.
  - Scope: runtime-agnostic tasklist/plan dependency parsing and focused cross-document
    regressions only; contracts, prompts, providers, target code, core, Studio, and browser
    behavior remain unchanged.
  - Verification: a sentence shaped as `M2 depends on M1 and is completed before M4` yields
    only `M2 -> M1` and `M4 -> M2`; it must not invent the reverse `M2 -> M4` edge. The exact
    terminal post-T90 plan/tasklist pair must no longer force a cyclic repair.
  - Completion: dependency objects are bounded by the next relation in the same clause, so the
    exact terminal plan now produces only `M2 -> M1`, `M3 -> M1`, `M4 -> M2/M3`, and
    `M5 -> M4`. Focused validator/planning tests pass `55/55`, Ruff and mypy pass, and the full
    Python suite passes `2179/2179`.

- `W36-E7-S4-T92` (done) Refresh the Codex-only candidate after T91.
  - Dependencies: `W36-E7-S4-T91`; blocks the next fresh `W36-E7-S4-T3` acceptance run.
  - Scope and verification: repeat the affected provider-free exact-SHA readiness bar,
    tracked-archive wheel, isolated install/doctor, pinned Hono readiness, bundle/isolation,
    private Codex auth, and source postflight; retain accepted unchanged-browser evidence.
  - Completion: candidate `ae3131a`, tree `696633d`, tracked archive digest `aecf4e4`, and
    byte-repeatable wheel digest `2b3e481` pass the affected Codex-only readiness bar. Ruff,
    mypy, Python `2179/2179`, focused validator/planning `55/55`, isolated install/doctor/
    eval-doctor, private-auth Seatbelt readiness, fresh pinned Hono setup, Vitest `233/233`,
    `tsc --noEmit`, clean target diff, and source postflight pass. The unchanged browser surfaces
    retain post-T81 Chromium `188/188` evidence. Sanitized evidence is recorded in
    `docs/e2e/candidate-readiness-2026-08-03-post-t91.md`; T3 is now next.

- `W36-E7-S4-T93` (done) Remove exponential backtracking from shell compound-evidence
  recognition before the `v0.1.0a16` release.
  - Dependencies: GitHub CodeQL high-severity alert on the accepted T3 branch; blocks release
    branch preparation but does not change provider execution or target-product behavior.
  - Scope: semantic command-evidence recognition and one adversarial validator regression.
  - Verification: command-substitution and plain assignment alternatives are disjoint and the
    assignment prefix is possessive; a 128-part scanner-shaped input terminates within the bounded
    validator test and is rejected as unverifiable, legitimate compound commands remain accepted,
    Ruff/mypy pass, and focused validator/planning tests pass `42/42`.

- `W36-E7-S4-T94` (done) Require material QA index claims to point to retained evidence.
  - Dependencies: `W36-E7-S4-T89` as the existing QA evidence-contract predecessor; discovered
    by the `AIDD-LIVE-005` Codex rerun after the Intent shell cleanup.
  - Scope: QA prompt/repair guidance, QA document contracts, cross-document validation, and
    focused regression coverage only; runtime adapters, stage progression, and target-work-item
    semantics remain unchanged.
  - Verification: every material `Verification summary` and `Readiness` bullet cites an `EV-N`
    defined in `Evidence` or an exact existing workspace-relative artifact path; a bare
    command/result bullet is rejected with `CROSS-QA-UPSTREAM-EVIDENCE`; prompt, validator,
    frontend, browser, Ruff, and mypy checks pass, and the Codex live lane reaches `qa` with
    status `pass`.
  - Completion: QA run/repair prompts and contracts now state the indexed-claim rule, the
    validator rejects an unindexed summary claim, and focused regression coverage passes.
    Provider-free UI/browser gates remain green; live run
    `eval-live-005-codex-20260810T104433Z` uses `gpt-5.6-luna` with `reasoning_effort=high`,
    completes all eight stages through `qa`, and reports `pass` with zero findings.

Exit evidence:

- Codex and Claude Code complete the same pinned medium task through installed public surfaces on
  one final AIDD revision and the exact same wheel bytes;
- raw worktrees, provider state, logs, screenshots, and target payload remain outside the AIDD
  checkout, while the tracked summary contains only sanitized identities, outcomes, and digests;
- each provider runs in an enforceable isolation domain that cannot read the other provider's
  roots or credentials, and each completed bundle remains independently auditable after mutable
  roots are removed;
- live-evaluation orchestration does not add scenario-specific behavior to core, adapters,
  validators, prompts, or Studio.

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
- one final clean AIDD revision has counted-clean `AIDD-LIVE-007` evidence for both Codex and
  Claude Code, including rendered Studio inspection and strict source/target/provider isolation;
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

---

## Wave 38 — typed runtime model and reasoning selection (`done`)

Goal: expose optional typed `model` and `reasoning_effort` selectors in runtime TOML,
map them only through adapter-owned capabilities, and preserve immutable selection
provenance across subprocess, brokered Codex, live E2E, and resume paths.

Non-goals:

- adding a UI model picker or one-off CLI selector flags;
- adding a static global model-id allowlist;
- changing native defaults when selectors are omitted;
- launching a provider-authenticated live scenario as an implementation gate.

### Epic W38-E1 — typed runtime selection boundary (`done`)
Linked stories: `US-01`, `US-07`, `US-08`, `US-10`

#### Slice W38-E1-S1 — typed selector configuration and capabilities (`done`)
Goal: parse optional runtime selectors, validate their types and adapter capabilities,
and reject unsupported or conflicting combinations before launch.

Dependencies:

- existing runtime catalog, config loader, and adapter surface;
- `W37-E1-S1` live Codex baseline.

Local tasks:

- `W38-E1-S1-T1` (done) Define typed runtime selector fields and capability metadata.
  - Scope: `src/aidd/config.py`, `src/aidd/runtime_catalog.py`, config tests.
  - Verification: omitted selectors preserve current native configuration; blank,
    non-string, unsupported-runtime, and unsupported-mode combinations fail closed.

- `W38-E1-S1-T2` (done) Validate selector conflicts before runtime allocation.
  - Scope: typed command/capability validation at the config-to-adapter boundary and
    focused negative tests.
  - Verification: raw custom commands remain compatible without typed selectors, while
    typed selectors conflicting with command-owned selectors fail closed before launch.

#### Slice W38-E1-S2 — Codex subprocess selector assembly (`done`)
Goal: inject typed selectors into Codex's native subprocess command without changing
other runtime commands or allowing command-owned selector conflicts.

Local tasks:

- `W38-E1-S2-T1` (done) Assemble Codex subprocess model and reasoning selectors at the adapter boundary.
  - Scope: `src/aidd/adapters/codex/runner.py`, runtime execution request, adapter tests.
  - Verification: empty configuration reproduces prior command tokens; Codex receives
    `--model` and `--config model_reasoning_effort=...`; other runtimes receive no Codex flags.

#### Slice W38-E1-S3 — Codex brokered selector payloads (`done`)
Goal: carry typed Codex selection through native app-server `thread/start` and `turn/start`
payloads while preserving command-owned conflict detection.

Local tasks:

- `W38-E1-S3-T1` (done) Map Codex selectors into brokered thread and turn start payloads.
  - Scope: `src/aidd/adapters/codex/live.py`, brokered adapter tests.
  - Verification: model appears only in `thread/start`, effort only in `turn/start`,
    and conflicting command-owned selectors fail before provider allocation.

#### Slice W38-E1-S4 — selection provenance and resume identity (`done`)
Goal: persist requested selectors, effective source, and runtime-default semantics in
run snapshots and make resumed runs immutable with respect to selection identity.

Local tasks:

- `W38-E1-S4-T1` (done) Persist typed selector provenance in stage and workflow run snapshots.
  - Scope: `src/aidd/cli/stage_run.py`, `src/aidd/cli/run.py`, manifest/resume tests.
  - Verification: requested selectors and source are readable in snapshots; omitted
    selectors say `runtime-default` without claiming a factual model; resume rejects drift.

#### Slice W38-E1-S5 — live E2E profile and operator documentation (`done`)
Goal: use the typed selector surface for the Codex live profile and document the operator
contract, runtime matrix, example TOML, and live E2E policy.

Local tasks:

- `W38-E1-S5-T1` (done) Generate the Luna/high Codex live profile and document typed selection behavior.
  - Scope: `src/aidd/harness/live_runtime_config.py`, `aidd.example.toml`, architecture,
    operator handbook, runtime matrix, and `docs/e2e`.
  - Verification: live config contains Codex `gpt-5.6-luna`/`high`, other runtimes retain
    native defaults, and docs checks plus focused harness tests pass.

Exit evidence:

- typed selectors validate before any runtime process is launched;
- empty runtime configuration preserves prior commands and native defaults;
- Codex subprocess and brokered app-server paths receive selectors at their native boundaries;
- non-Codex adapters receive no Codex-specific parameters;
- run snapshots and resume guards preserve immutable selection provenance;
- live E2E generated Codex profile uses `gpt-5.6-luna` with `high` effort without requiring
  a provider-authenticated scenario run.

Sync notes:

- `2026-08-04` Opened from the requested typed runtime-selection vertical slice. The work is
  split by dominant subsystem and verification signal so core, adapter, provenance, and harness
  changes remain reviewable independently. No historical Wave 37 entry is rewritten.
- `2026-08-04` Completed the typed selector vertical slice. Config, adapter, app-server,
  manifest/resume, live-profile, documentation, focused tests, full pytest (`2188 passed`),
  Ruff, and mypy checks pass. No provider-authenticated live scenario was launched.

---

## Wave 39 — operator runtime selector picker (`done`)

Goal: let operators choose optional typed model and reasoning-effort selectors in the
local UI launch flow while preserving adapter capability validation, native defaults,
and immutable run selection provenance.

Non-goals:

- adding a static global model-id allowlist;
- moving Codex flag or app-server mapping into the frontend or core;
- changing the existing CLI configuration contract.

### Epic W39-E1 — UI launch selection (`done`)
Linked stories: `US-01`, `US-10`, `US-11`

#### Slice W39-E1-S1 — typed UI launch selection (`done`)
Goal: carry operator-selected model and reasoning effort from the UI picker through
the shared launch path into runtime requests and run snapshots.

Dependencies:

- `W38-E1` typed runtime selector boundary;
- existing operator frontend launch service.

Local tasks:

- `W39-E1-S1-T1` (done) Propagate UI runtime selectors through stage/workflow launch requests and snapshots.
  - Scope: UI launch request models, stage/workflow execution handoff, and provenance tests.
  - Verification: a UI-selected Codex model/effort reaches the existing adapter request and
    manifest with `ui-selection` provenance; omitted values retain configured/native defaults.

- `W39-E1-S1-T2` (done) Render editable model and reasoning-effort controls for the selected runtime.
  - Scope: operator frontend Guided Setup and command-center assets.
  - Verification: browser-asset tests prove controls are visible, runtime changes reset stale
    selectors, and launch payloads include only non-empty typed values.

Exit evidence:

- UI can choose model and reasoning effort without editing TOML;
- blank selectors are omitted and native defaults remain intact;
- unsupported runtime selectors still fail closed at the existing adapter boundary;
- UI-created manifests preserve selector values, source, and resume identity.

Sync notes:

- `2026-08-04` Completed the UI picker vertical slice. The operator shell now exposes
  capability-gated model and reasoning-effort inputs, forwards non-empty values through
  UI stage/workflow launches, and records `ui-selection` provenance. Frontend, stage-run,
  Ruff, and mypy checks pass.
---

## Wave 40 — operator re-entry and task clarity (`done`)

Goal: make the local Operator UI understandable when a project already has AIDD state: open
the project-level decision queue on restart, make an independent work item visibly available,
and keep progress and the next safe action legible without changing workflow semantics.

### Epic W40-E1 — project-first operator orientation (`done`)
Linked stories: `US-02`, `US-03`, `US-05`, `US-06`, `US-11`, `US-13`

#### Slice W40-E1-S1 — existing-project re-entry (`done`)
Goal: route a bare local UI launch to the existing project's Inbox instead of repeating setup.

Primary outputs:

- project-only UI context for an existing `.aidd/` workspace;
- Inbox-first startup and restart behavior;
- deterministic API and browser coverage.

Touched areas:

- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/`
- `tests/cli/`, `tests/frontend/`, and browser journeys

Dependencies:

- `W36-E7-S2`

Local tasks:

- `W40-E1-S1-T1` (done) Open the existing project Inbox on bare `aidd ui`.
  - Scope: project-context startup and packaged UI bootstrap only.
  - Verification: a browser launch from a project containing `.aidd/` opens Inbox without
    setup, creates no artifacts, and resumes an exact selected work item only after an explicit
    operator action.

Exit evidence:

- restart distinguishes a missing project from an existing workspace without persisting a
  speculative last-work-item selection;
- a bare UI entry shows project-level decisions before stage-specific controls.

#### Slice W40-E1-S2 — independent work-item entry (`done`)
Goal: let an operator create a separate task while other work items remain active or inspectable.

Primary outputs:

- persistent project-level **New work item** entry;
- concise creation surface separate from runtime selection and launch.

Touched areas:

- `src/aidd/cli/static/`
- `tests/frontend/` and browser journeys

Dependencies:

- `W40-E1-S1`

Local tasks:

- `W40-E1-S2-T1` (done) Render and dispatch project-level independent work-item creation.
  - Scope: Inbox/Studio creation surface and existing onboarding service call only.
  - Verification: an operator can create a valid work item from an existing project without
    selecting a runtime, receives inline duplicate-id feedback, and lands on the new no-run
    Studio without mutating another run.

Exit evidence:

- creating work and launching work are visibly distinct choices;
- existing work items remain navigable after creation.

#### Slice W40-E1-S3 — decision-first progress density (`done`)
Goal: replace duplicated dashboard chrome with one readable workflow-progress and next-action
surface per current context.

Primary outputs:

- compact project/work-item progress summaries;
- contextual diagnostics and evidence disclosure instead of always-visible empty panels.

Touched areas:

- `src/aidd/cli/static/`
- `docs/architecture/operator-frontend.md`
- frontend and browser tests

Dependencies:

- `W40-E1-S1`

Local tasks:

- `W40-E1-S3-T1` (done) Consolidate the Inbox and Studio hierarchy around progress and one
  next action.
  - Scope: packaged Studio shell, styles, and documented UX acceptance only.
  - Verification: desktop and mobile browser checks show a compact progress state and one
    eligible action without simultaneous zero-value rails, sidebars, and activity surfaces;
    live state remains factual and never fabricates a percentage.

Exit evidence:

- operators can state which work item is current, which stage is next or blocked, and why,
  before opening diagnostics;
- document, evidence, history, and logs remain reachable as contextual drill-downs.

Sync notes:

- `2026-08-04` Completed the re-entry and clarity slice: a bare existing `.aidd/` workspace
  opens the project Inbox without choosing or persisting a speculative work item; explicit
  Studio links restore their requested item through the existing canonical endpoint. Operators
  can create an independent work item before choosing a runtime, and the Inbox/Studio surfaces
  now lead with factual progress and one next action. Focused CLI/frontend regressions and
  desktop/mobile browser checks passed.

#### Slice W40-E1-S4 — compact intent shell migration (`done`)
Goal: replace the compatibility cockpit composition with one intent-first workspace surface
without changing workflow, route, or runtime semantics.

Primary outputs:

- compact shell anchors with one primary workspace scroll owner;
- renderer/event rebinding for the new context, phase, decision, document, and technical-detail
  regions;
- removal of permanent stage rail, sidebar, dock, and duplicate cockpit chrome.

Touched areas:

- `src/aidd/cli/static/`
- `docs/architecture/operator-frontend.md`
- frontend, CLI contract, and browser tests

Dependencies:

- `W40-E1-S3`
- `W41-E1-S1`

Local tasks:

- `W40-E1-S4-T1` (done) Define compact shell anchors and scroll ownership in the packaged UI.
  - Scope: static shell markup and architecture acceptance only.
  - Verification: static contracts identify the new anchors and reject legacy shell containers.
- `W40-E1-S4-T2` (done) Rebind shell renderers and event handlers to the compact anchors.
  - Scope: browser-side renderers and focus/navigation wiring; preserve API and route contracts.
  - Verification: frontend and packaged browser journeys pass at all supported viewports.
- `W40-E1-S4-T3` (done) Keep live execution in the Intent workspace until durable artifacts exist.
  - Scope: browser-side job polling/render coordination only; runtime job, artifact, and route
    contracts remain unchanged.
  - Verification: starting an intervention or workflow does not request a not-yet-created
    artifact index, preserves the primary workspace while the job runs, and terminal
    reconciliation loads the durable artifact view; intervention recovery and frontend/static
    checks pass.

Exit evidence:

- legacy shell containers are absent from the base DOM;
- primary decision precedes technical details and maintenance in DOM and focus order;
- every intentional nested scroll region has an explicit owner.

Sync notes:

- `2026-08-10` Completed the compact intent shell migration. The packaged UI now has one
  `operatorWorkspace` scroll owner with Intent context, four delivery phases, one decision
  surface, a document canvas, and a technical-details disclosure. Legacy rail/sidebar/dock
  containers and their responsive layout rules were removed; dynamic form/action IDs, routes,
  API payloads, and workflow semantics remain unchanged. Live job polling now leaves the
  workspace visible without requesting a not-yet-created artifact index, then loads durable
  evidence after terminal reconciliation. Frontend/static contracts and focused browser geometry
  checks pass.

---

## Wave 41 — evidence-first document reading (`done`)

Goal: make the Document & Evidence Studio easy to read: lead with the selected document and
its decision value, then reveal clearly explained supporting evidence without changing the
workflow, artifact ownership, or source-of-truth rules.

### Epic W41-E1 — explainable operator reading (`done`)
Linked stories: `US-02`, `US-03`, `US-06`, `US-11`

#### Slice W41-E1-S1 — document-reader hierarchy (`done`)
Goal: turn the current Canvas and Evidence Inspector into one compact reading flow that explains
why every visible evidence group exists.

Primary outputs:

- document role and purpose brief for Canvas and Artifact Workbench readers;
- purpose-labelled, disclosure-based Evidence Inspector with useful empty, missing, and bounded
  states;
- desktop and mobile verification of document-first hierarchy.

Touched areas:

- `src/aidd/cli/static/operator-artifacts-documents.js`
- `src/aidd/cli/static/operator-components.css`
- `src/aidd/cli/static/operator-responsive.css`
- `docs/architecture/operator-frontend.md`
- `tests/frontend/`, `tests/cli/`, and operator UI acceptance docs

Dependencies:

- `W40-E1-S3`

Local tasks:

- `W41-E1-S1-T1` (done) Render an evidence-first document reader with purpose-labelled
  supporting disclosures.
  - Scope: packaged Canvas, Artifact Workbench, Evidence Inspector, and their reader-only
    styles; preserve existing workbench payloads and read-only ownership rules.
  - Verification: deterministic frontend tests prove document role/purpose and evidence-group
    explanations; desktop and 390px browser checks show the document before supporting
    evidence, usable native disclosures, no horizontal overflow, and no console errors.

Exit evidence:

- an operator can identify what the selected document is, why it matters, and which evidence
  group to open before inspecting raw paths or provenance;
- unresolved validation remains visible without turning unrelated evidence into equal-weight
  chrome;
- missing, bounded, unavailable-comparison, and graph-fallback states are explicit and do not
  fabricate durable evidence.

Sync notes:

- `2026-08-04` Completed the evidence-first reader slice. Studio and the Artifact Workbench now
  lead with a role, freshness, and decision-use brief; stale retained copies explicitly cannot
  masquerade as current proceed evidence. Supporting evidence is a compact disclosure stack with
  a group purpose and an item-level **Why** for validations, contract requirements, and retained
  versions. Read, Source, and Compare are bounded and truthful; Compare only presents retained
  copies side by side and never claims a generated diff. Related documents remain in Studio and
  persist in the canonical route across reload. Focused verification passed: frontend `107`, UI
  CLI `155`, focused browser `14`, Ruff, and mypy.

#### Slice W41-E1-S2 — intent vocabulary and technical disclosure (`done`)
Goal: make user-facing copy consistently intent-first while keeping canonical work-item identity
available only in technical lineage and contract fields.

Primary outputs:

- `Intent` copy across topbar, Inbox, onboarding, Studio, and next-flow actions;
- one non-duplicated Intent identity block in Active Studio;
- technical work-item/run/stage lineage behind a disclosure.

Touched areas:

- `src/aidd/cli/static/`
- `docs/architecture/operator-frontend.md`
- `docs/e2e/operator-ui-local-project.md`
- frontend and browser tests

Dependencies:

- `W41-E1-S1`

Local tasks:

- `W41-E1-S2-T1` (done) Replace visible Work item copy with Intent and remove duplicate identity.
  - Scope: user-facing labels, accessible names, and validation/error copy only.
  - Verification: copy-whitelist tests find no visible Work item outside technical disclosure.
- `W41-E1-S2-T2` (done) Move lineage and diagnostics into technical disclosures and document the
  vocabulary boundary.
  - Scope: next-flow/history/evidence presentation and UX contract documentation.
  - Verification: browser checks preserve source/target/run/stage auditability without exposing
  canonical identifiers as primary context.

Sync notes:

- `2026-08-10` Completed the intent vocabulary and technical disclosure follow-up. User-facing
  surfaces consistently say `Intent`; canonical `work_item`, run, stage, and lineage fields stay
  available in technical routes/disclosures. Active Studio no longer repeats the same identity,
  and copy-whitelist tests reject visible `Work item` labels outside technical context.

---

## Wave 42 — task-centered operator experience (`planned`)

Goal: replace the implemented document-first shell's ambiguous `Intent` vocabulary and weak task
affordances with one organic operator flow: create a Work Item, select an eligible Runner at the
point of execution, work dependency-ready Tasks, read or author Markdown through explicit
ownership boundaries, recover from exact failures, and finish with an immutable handoff.

This wave changes presentation, read models, and controlled frontend authoring only. It does not
change the eight-stage graph, adapter boundary, Markdown contracts, validation policy, durable
`.aidd/` ownership, or CLI behavior. Existing routes and payloads remain compatibility surfaces
until a slice explicitly migrates and verifies them.

Reference authority:

1. [Target Operator Experience](../architecture/operator-frontend-target-ux.md) for hierarchy,
   vocabulary, flows, Markdown ownership, states, responsive behavior, and acceptance;
2. [target visual set](../architecture/assets/operator-ui-target-v2/generation-prompts.md) for
   composition, density, and contextual action placement only;
3. [Operator Frontend Contract](../architecture/operator-frontend.md) for implemented service,
   endpoint, safety, and compatibility boundaries;
4. [task execution](../architecture/task-execution.md), document contracts, and existing core
   read models for canonical behavior.

Linked stories: `US-01`, `US-02`, `US-03`, `US-05`, `US-06`, `US-11`, `US-13`

### Epic W42-E1 — target contract and visual authority (`done`)

Goal: establish one written UX authority and one complete screen set before implementation.

#### Slice W42-E1-S1 — target interaction and Markdown contract (`done`)

Primary output: one normative target that names the product hierarchy, complete flow, screen
inventory, document ownership, controlled writes, task behavior, recovery states, and measurable
acceptance.

Touched areas:

- `docs/architecture/operator-frontend-target-ux.md`
- `docs/architecture/operator-frontend.md`

Dependencies: completed Wave 40 and Wave 41 implementation evidence.

Local tasks:

- `W42-E1-S1-T1` (done) Define the task-centered target operator contract.
  - Scope: architecture documentation only; retain existing workflow, runtime, and artifact
    ownership semantics.
  - Verification: the contract names all 13 surfaces, exact eight-stage order, Runner placement,
    task workspace behavior, Markdown ownership classes, failure states, viewport matrix, and
    provider-free acceptance.

#### Slice W42-E1-S2 — replacement visual set and stale-asset cleanup (`done`)

Primary output: one 13-screen reference set that covers the end-to-end desktop flow plus the
mobile blocking-decision path, with reproducible prompt notes and no competing old UI assets.

Touched areas:

- `docs/architecture/assets/operator-ui-target-v2/`
- `docs/architecture/operator-frontend.md`
- `docs/backlog/roadmap.md`
- `tests/test_docs_consistency.py`

Dependencies: `W42-E1-S1`.

Local tasks:

- `W42-E1-S2-T1` (done) Generate, register, and verify the replacement visual authority.
  - Scope: 13 target PNGs, prompt record, architecture and roadmap links, docs-consistency
    expectations, and deletion of the superseded Mission Control, Document & Evidence Studio,
    and exploratory image folders.
  - Verification: all 13 expected files exist, every filename is linked from architecture and
    planning docs, old asset paths have no remaining references, and docs consistency passes.

### Epic W42-E2 — literal navigation and contextual Runner (`planned`)

Goal: make project/work/task identity and execution choice visible where the operator acts,
without changing canonical ids or creating frontend-owned eligibility.

#### Slice W42-E2-S1 — Work Item shell and project work list (`planned`)

Primary output: a stable `Project -> Work Item` shell with literal vocabulary, grouped work, Work
Item tabs, and the exact stage strip.

Touched areas:

- `src/aidd/core/operator_inbox.py`
- `src/aidd/core/operator_frontend_models.py`
- `src/aidd/cli/static/index.html`
- `src/aidd/cli/static/operator-main.js`
- `src/aidd/cli/static/operator-inbox.js`
- `src/aidd/cli/static/operator-active-studio.js`
- `src/aidd/cli/static/operator-shell-rendering.js`
- `src/aidd/cli/static/operator-onboarding.js`
- `src/aidd/cli/static/operator-route-intents.js`
- `src/aidd/cli/static/operator-history.js`
- `src/aidd/cli/static/operator-next-flow-view.js`
- `src/aidd/cli/static/operator-next-flow-actions.js`
- `src/aidd/cli/static/operator-dashboard-actions.js`
- `src/aidd/cli/static/operator-components.css`
- `src/aidd/cli/static/operator-responsive.css`
- core, CLI, and frontend contract tests

Dependencies: `W42-E1`.

Local tasks:

- `W42-E2-S1-T1` (done) Replace primary `Intent` presentation with literal Work Item and Task
  vocabulary.
  - Scope: core-emitted and static visible labels, accessible names, headings, route titles, and
    copy assertions only; preserve `work_item` ids, request paths, API shapes, internal
    compatibility fields, and historical evidence text.
  - Verification: focused core/static copy tests reject `Intent` as a navigation noun while
    technical disclosures and canonical identifiers remain accessible.
- `W42-E2-S1-T2` (done) Publish core-owned Work Item attention groups and deterministic ordering.
  - Scope: extend the existing `OperatorInboxView` with Needs input, Running, Ready, and Complete,
    canonical-stage/Work-Item ordering, and one entry recommendation; failed/stale terminal state
    is not Complete and active `wait-for-stage` work is not omitted.
  - Verification: core/service tests prove exact membership, deterministic ordering, empty-project
    creation, and one recommendation without browser-owned priority.
- `W42-E2-S1-T4` (done) Render core-owned Work Item attention groups and selected context.
  - Scope: render the four server groups, preserve selected Work Item and deep-link context, show
    one contextual inspector and one primary action, and never mutate or re-sort server state.
  - Verification: provider-free frontend fixtures prove group order, selection persistence,
    empty groups, empty-project creation, and one primary action for the selected item.
  - Dependencies: `W42-E2-S1-T2` as the core-projection predecessor.
- `W42-E2-S1-T3` (done) Render the Work Item tabs and canonical stage strip.
  - Scope: Overview, Tasks, Documents, Runs tabs and the eight exact stages; retain current deep
    links, browser history, focus restoration, and stale/status semantics.
  - Verification: route and DOM tests cover all tabs, exact stage order, keyboard navigation,
    status text, and reload restoration without duplicate navigation landmarks.
  - Dependencies: `W42-E2-S1-T4` as the project-shell predecessor.

#### Slice W42-E2-S2 — launch readiness and contextual Runner (`planned`)

Primary output: one core-authoritative Runner readiness projection and one reusable picker placed
beside every action that launches workflow, stage, task, repair, or remediation work.

Touched areas:

- `src/aidd/core/operator_frontend_models.py`
- `src/aidd/core/operator_frontend_dashboard.py`
- `src/aidd/cli/ui.py`
- `src/aidd/cli/static/operator-api-state.js`
- `src/aidd/cli/static/operator-components.js`
- core, CLI, and frontend tests

Dependencies: `W42-E2-S1` and existing Wave 39 selector contracts.

Local tasks:

- `W42-E2-S2-T1` (done) Publish a core-owned launch-readiness projection.
  - Scope: selected runtime id, binary, command, auth, capabilities, permission policy, model,
    reasoning, config identity, probe observation timestamp, eligibility, and literal disabled
    reason; a stale snapshot or prior successful launch cannot authorize a mutation, and no
    adapter logic enters the core.
  - Verification: core and service tests cover ready, missing selection, stale evidence,
    verified/failed/unverified auth, unsupported capability, permission denial, config drift, and
    runtime-unavailable outcomes.
- `W42-E2-S2-T2` (done) Extract and place the contextual Runner control.
  - Scope: one frontend component reused beside workflow, stage, task, repair, and remediation
    launches; hide it from create, read-only history, completed handoff, and non-launch decisions.
  - Verification: fixture tests prove selected values reach the existing request path, disabled
    reasons mirror the core projection, and no surface exposes two Runner selectors or launch
    actions; service-side revalidation repeats the core readiness check before mutation.

### Epic W42-E3 — dependency-aware Task Workspace (`planned`)

Goal: make Task the default Deliver-stage unit, with truthful readiness, attempts, evidence, and
one mutually exclusive Run, Resume, or Finalize action.

#### Slice W42-E3-S1 — task workspace read boundary (`planned`)

Primary output: a reusable core/API projection for grouped tasks and a selected task.

Touched areas:

- `src/aidd/core/operator_frontend_models.py`
- `src/aidd/core/operator_frontend_dashboard.py`
- `src/aidd/core/task_execution.py`
- `src/aidd/cli/ui.py`
- core and CLI tests

Dependencies: `W42-E2-S2-T1` and existing Wave 35 task ledger.

Local tasks:

- `W42-E3-S1-T1` (done) Add the core Task Workspace read model.
  - Scope: Ready, Running, Blocked, Done groups; core next-ready and critical-path signals;
    dependencies, attempt counts, verification, last durable event, and preserved successes.
  - Verification: deterministic core tests cover mixed dependency graphs, no-ready work,
    interrupted attempts, partial success, finalization eligibility, and stale tasklists.
- `W42-E3-S1-T2` (done) Expose task workspace and selected-task detail through the UI service.
  - Scope: bounded list and detail payloads over existing ledger/evidence sources; preserve
    synchronous conflict and duplicate-suppression behavior.
  - Verification: CLI service tests prove stable ids, bounded reads, exact evidence links, missing
    task behavior, and post-mutation server-winner readback.
- `W42-E3-S1-T3` (done) Expose core-owned selected-task action eligibility in the bounded service
  payload.
  - Scope: publish Run, Resume, and Finalize action states with literal disabled consequences from
    the task ledger, dependency graph, stale-tasklist guard, finalization state, and Runner
    readiness; the browser must not infer action policy from status or group names.
  - Verification: core/service tests cover ready, running, blocked, done, stale, conflicted,
    unavailable-Runner, and finalization-retry states with one mutually exclusive recommended
    action and fail-closed disabled reasons. Completed in PR #313 (merge `fa2426a6`): the core
    projection now owns action semantics and the UI service gates selected-task mutations on the
    current run lease and Runner readiness; focused core/UI tests, planning/docs checks, Ruff,
    mypy, deterministic scenarios, adapter conformance, and packaged browser checks passed.

#### Slice W42-E3-S2 — task list, detail, and active run (`planned`)

Primary output: the target Tasks surface and its active-attempt observation state.

Touched areas:

- `src/aidd/cli/static/operator-main.js`
- `src/aidd/cli/static/operator-logs-jobs.js`
- `src/aidd/cli/static/operator-components.css`
- `src/aidd/cli/static/operator-responsive.css`
- frontend and browser tests

Dependencies: `W42-E3-S1` and `W42-E2-S2-T2`.

Local tasks:

- `W42-E3-S2-T1` (done) Render the grouped task list and deterministic selection.
  - Scope: Ready, Running, Blocked, Done sections, search/filter, dependency badges, next-ready
    marker, URL selection, empty/loading/error states, and keyboard list navigation.
  - Verification: fixture tests cover ordering, filters, deep links, reload, focus, empty groups,
    and no client-side status movement.
- `W42-E3-S2-T2` (done) Render selected-task detail and mutually exclusive actions.
  - Scope: outcome, scope, acceptance, dependencies, expected files, attempts, linked documents,
    blockers, Runner, and Run/Resume/Finalize; reuse existing mutation services.
  - Verification: tests prove action eligibility, pending duplicate suppression, conflict
    recovery, preserved successes, and literal disabled consequences.
- `W42-E3-S2-T3` (done) Render the active task attempt and live-output tray.
  - Scope: attempt identity, factual elapsed time, last-output age, durable milestone, cancel
    state, reconnect cursor, and collapsible raw output; never estimate percentage completion.
  - Verification: browser fixtures cover starting, streaming, quiet, cancellation-pending,
    failed, completed, reconnecting, and missing-log states without context loss.
- `W42-E3-S2-T4` (done) Render the selected-task contract and contextual Runner from core action
  projection.
  - Dependencies: `W42-E3-S1-T3`.
  - Scope: show scope, acceptance, expected files, verification, evidence, linked documents,
    blockers, attempts, and exactly one eligible Run/Resume/Finalize action with one contextual
    Runner beside it; preserve task ids, deep links, selection, and active-attempt context.
  - Verification: provider-free Task Workspace fixtures and browser checks prove bounded detail,
    literal disabled reasons, duplicate-action suppression, Runner payload propagation, reload,
    keyboard focus, and no client-side eligibility inference. Completed in PR #315 (merge
    `29c07782`): selected-task detail now consumes the core/service action projection, renders
    the bounded contract fields, propagates the selected Runner, and keeps the responsive action
    bar to one task mutation. Focused frontend, UI-contract, core/service, planning/docs, Ruff,
    mypy, and Task Workspace browser checks passed; full CI and packaged browser acceptance passed.

### Epic W42-E4 — Markdown Workspace and controlled authoring (`planned`)

Goal: make Markdown pleasant to read and safe to change by exposing document role, provenance,
freshness, retained versions, and explicit authoring boundaries.

#### Slice W42-E4-S1 — canonical Markdown reader (`planned`)

Primary output: a grouped document navigator and a read-only Markdown workspace that never
fabricates versions or implies generated output is editable.

Touched areas:

- `src/aidd/cli/static/operator-artifacts-documents.js`
- `src/aidd/cli/static/operator-components.css`
- `src/aidd/cli/static/operator-responsive.css`
- frontend and browser tests

Dependencies: `W42-E2-S1-T3` and current artifact/document read models.

Local tasks:

- `W42-E4-S1-T1` (done) Render role-grouped document navigation and the reading brief.
  - Scope: Output, Questions, Validation, Inputs, Evidence groups; filename, role, stage, attempt,
    freshness, bounded state, source of truth, rendered body, heading map, path/copy utilities.
  - Verification: fixtures cover current, stale, missing, malformed, truncated, permission-denied,
    and empty documents with one truthful next action.
- `W42-E4-S1-T2` (done) Add Source, retained Compare, and anchored finding context.
  - Scope: exact source rendering, comparison only for two named retained attempts, heading/line
    anchors, related evidence, and browser-history-preserving cross-document navigation.
  - Verification: tests reject synthetic history and editing controls; browser checks cover
    anchors, unavailable comparison, back/forward restoration, long Markdown, and overflow.

#### Slice W42-E4-S2 — operator-authored Markdown (`planned`)

Primary output: consistent Write/Preview workflows for each supported operator-owned document,
with draft, conflict, and durable destination semantics.

Touched areas:

- `src/aidd/cli/static/operator-onboarding.js`
- `src/aidd/cli/static/operator-questions.js`
- `src/aidd/cli/static/operator-approvals-interventions.js`
- `src/aidd/cli/static/operator-next-flow-actions.js`
- frontend and CLI tests

Dependencies: `W42-E4-S1` and existing write services.

Local tasks:

- `W42-E4-S2-T1` (done) Add operator-request Markdown Write/Preview with a consumed-input
  boundary.
  - Scope: new Work Item request and supported context inputs; edit before first consuming run,
    then route outcome changes to a revision/intervention instead of rewriting history.
  - Verification: tests cover preview, destination, validation, unsaved navigation, first write,
    pre-run edit, consumed-input refusal, and exact durable readback.
- `W42-E4-S2-T2` (done) Add the structured Markdown answer workflow.
  - Scope: question context, resolved/partial/deferred state, Write/Preview, evidence links,
    unblock consequence, draft persistence, and `answers.md` destination.
  - Verification: tests cover each resolution status, invalid/partial answers, failed submission,
    duplicate suppression, reconnect, conflict winner, and resulting workflow state.
- `W42-E4-S2-T3` (done) Unify intervention, remediation, follow-up, and clone Markdown drafts.
  - Scope: purpose-specific fields over one draft/preview state machine, source-evidence selection,
    exact destination, unsaved warning, and no mutation of runtime-generated documents.
  - Verification: frontend/service tests cover each purpose, draft isolation, destination,
    submission consequence, stale downstream stages, conflict, and reload recovery.

### Epic W42-E5 — decisions, recovery, and quality gates (`planned`)

Goal: give every blocking condition one bounded workbench, exact evidence, and one safe recovery
action without conflating questions, approvals, validation failure, or runtime failure.

#### Slice W42-E5-S1 — Decision Workbench and recovery (`planned`)

Primary output: shared decision composition with distinct schemas and truthful recovery semantics.

Touched areas:

- `src/aidd/cli/static/operator-questions.js`
- `src/aidd/cli/static/operator-approvals-interventions.js`
- `src/aidd/cli/static/operator-stage-cockpit.js`
- frontend and browser tests

Dependencies: `W42-E4-S2-T2` and `W42-E2-S2-T2`.

Local tasks:

- `W42-E5-S1-T1` (done) Render the shared Decision Workbench for questions and approvals.
  - Scope: decision type, reason, source snippets, consequence, schema-specific inputs, draft or
    approval evidence, and exactly one submit action; do not reduce approvals to answer forms.
  - Verification: fixtures cover question, approval, deferred answer, unavailable evidence,
    pending, conflict, permission denial, and mobile first-action visibility.
- `W42-E5-S1-T2` (done) Render validation and runtime recovery as distinct states.
  - Scope: validation document/rule/location/hint/budget/exact brief plus repair Runner; runtime
    first decisive failure/logs/retry/selection consequence without consuming repair budget.
  - Verification: tests prove repair exhaustion, request-change routing, runtime retry, cancel,
    stale evidence, no-budget mutation, and one primary action per state.

#### Slice W42-E5-S2 — implementation, Review, and QA gates (`planned`)

Primary output: repository-truth implementation review and selective Markdown remediation.

Touched areas:

- `src/aidd/cli/static/operator-stage-cockpit.js`
- `src/aidd/cli/static/operator-artifacts-documents.js`
- `src/aidd/cli/static/operator-approvals-interventions.js`
- frontend and browser tests

Dependencies: `W42-E3-S2` and `W42-E4-S2-T3`.

Local tasks:

- `W42-E5-S2-T1` (done) Render Implementation Review from real repository and verification
  evidence.
  - Scope: changed-file list, unified diff, completed task claims, actual commands/results, scope
    coverage, risk, Runner, and `Proceed to Review`; no stage-document editing.
  - Verification: fixtures cover clean, incomplete, changed-outside-scope, missing evidence,
    failed verification, large diff, and launch eligibility.
- `W42-E5-S2-T2` (done) Render selective Review/QA remediation and downstream staleness.
  - Scope: selectable findings/risks, exact source evidence, Markdown remediation Write/Preview,
    destination, Runner, and return to Implement through the existing service.
  - Verification: tests cover selection requirements, blocking/non-blocking findings, saved draft,
    conflict, stale Review/QA, preserved task successes, rerun, and fresh acceptance.

### Epic W42-E6 — run lineage and terminal handoff (`planned`)

Goal: make attempts and completion auditable without presenting inferred history or mutable final
state.

#### Slice W42-E6-S1 — Runs and Attempts workspace (`planned`)

Primary output: chronological run/attempt navigation with exact timeline, logs, artifacts, and
lineage.

Touched areas:

- `src/aidd/core/operator_timeline.py`
- `src/aidd/cli/static/operator-logs-jobs.js`
- `src/aidd/cli/static/operator-artifacts-documents.js`
- core, frontend, and browser tests

Dependencies: `W42-E2-S1-T3` and existing retained-attempt models.

Local tasks:

- `W42-E6-S1-T1` (done) Render the run list, retained attempts, exact timeline, and lineage.
  - Scope: filters, stable selection, run/attempt metadata, durable events, raw log, artifacts,
    input/output hashes, copy id, and compare only when both attempts are retained.
  - Verification: tests cover live, failed, repaired, completed, missing artifact, bounded log,
    unavailable comparison, reload, and no Runner selector on read-only history.

#### Slice W42-E6-S2 — immutable Flow Complete (`planned`)

Primary output: one final handoff that requires fresh QA and recommends one next outcome.

Touched areas:

- `src/aidd/cli/static/operator-next-flow-actions.js`
- `src/aidd/cli/static/operator-artifacts-documents.js`
- frontend and browser tests

Dependencies: `W42-E5-S2` and `W42-E6-S1`.

Local tasks:

- `W42-E6-S2-T1` (done) Render immutable handoff, final evidence, and next outcomes.
  - Scope: delivered scope, verification, known limitations, repository state, final documents,
    QA result, run ids, retained evidence, one core-recommended action, and quieter alternatives.
  - Verification: fixtures prove fresh-QA gating, stale/failed exclusion, source-run immutability,
    recommended outcome, follow-up lineage, clone/eval/archive semantics, and no Runner selector.

### Epic W42-E7 — executable UX acceptance (`planned`)

Goal: prevent another visual-only redesign by requiring deterministic surface fixtures, browser
behavior, accessibility, responsive geometry, and observed first-time use before cutover.

#### Slice W42-E7-S1 — provider-free surface fixtures and component states (`planned`)

Primary output: deterministic fixtures and contract tests for every target reference and shared
interaction state.

Touched areas:

- `tests/frontend/`
- `tests/cli/`
- operator UI fixture routes and documentation

Dependencies: each owning Wave 42 surface slice before its corresponding fixture closes.

Local tasks:

- `W42-E7-S1-T1` (done) Add provider-free routes for all 13 target surfaces.
  - Scope: canonical fixture payloads for project work, create, launch, tasks, active attempt,
    decision, validation repair, Markdown, implementation review, remediation, history,
    completion, and mobile decision.
  - Verification: one manifest test proves every target filename maps to a loadable fixture with
    no network, provider credentials, clock drift, or random ids.
- `W42-E7-S1-T2` (done) Add shared interaction-state and accessibility contracts.
  - Scope: loading, empty, partial, error, disabled, selected, pending, conflict, success, offline,
    reconnecting, permission denied, focus, keyboard, target size, and accessible names.
  - Verification: frontend tests exercise the applicable state matrix for every shared component
    and reject duplicate primary actions, color-only status, clipped names, and focus loss.

#### Slice W42-E7-S2 — responsive browser journeys and observed usability (`planned`)

Primary output: measured browser evidence and one observed novice journey that gates default
routing.

Touched areas:

- browser acceptance tests
- `docs/e2e/operator-ui-local-project.md`
- Wave 42 reconciliation notes

Dependencies: `W42-E2` through `W42-E7-S1`.

Local tasks:

- `W42-E7-S2-T1` (done) Run the target browser journey matrix at all supported viewports.
  - Scope: create -> runner -> launch, task run, question recovery, validation repair, Markdown
    change, review remediation, history, and completion at 320x568, 390x844, 768x1024, 1280x900,
    and 1440x900.
  - Verification: captured checks prove first-action visibility, focus order, target size, contrast,
    clipping, overflow, draft retention, reconnect, one primary action, and zero console errors.
- `W42-E7-S2-T2` (done) Observe and reconcile a first-time operator journey before cutover.
  - Scope: run the deterministic provider-free rehearsal for create -> choose Runner -> launch ->
    answer question -> resume session; keep its scripted observation mode distinct from human
    usability evidence and record comprehension signals as new roadmap tasks rather than silent
    polish.
  - Verification: the provider-free evidence records all five ordered steps, factual elapsed time,
    wrong actions, assistance, first decisive confusion, resulting tasks, accessibility/geometry
    checks, durable answer readback, and an explicit gated routing decision.
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
- `W42-E7-S2-T4` (done) Repair mobile recovery composition and first-viewport assertions.
  - Scope: keep one vertical scroll owner, render question recovery before secondary context on
    narrow viewports, remove recovery-panel minimum-width overflow, and measure the actual
    production primary-action selector before any scroll is requested.
  - Verification: the browser matrix proves question, validation, and review/remediation surfaces
    expose one visible primary action in the initial 320x568 and 390x844 viewports with no clipped
    action, horizontal overflow, focus loss, or console error; the assertion fails if a helper
    scrolls before measuring. PR #311 (`d7b13d48`) passed the full CI and packaged UI browser lane.

#### Slice W42-E7-S3 — installed task-centered live evidence (`planned`)

Primary output: one runner-owned live E2E checkpoint that proves the installed Implement flow
preserves canonical task-plan, ledger, attempt, finalization, and downstream-eligibility truth.

Touched areas:

- `src/aidd/harness/live_e2e_black_box_orchestration.py`
- live E2E report projections
- focused harness tests
- `docs/e2e/live-e2e-catalog.md`

Dependencies: `W42-E3-S1` and `W42-E7-S1`.

Local tasks:

- `W42-E7-S3-T1` (done) Add task-aware live E2E checkpoints for the installed Implement flow.
  - Scope: persist schema-v1 `task-flow-checkpoint.json` and `.md` after tasklist and Implement
    with run/revision identity, task ids/order/dependencies, the core-selected next task, statuses,
    attempts, evidence links, tasklist/ledger hashes, aggregate finalization, and Review
    eligibility; collect through installed public surfaces plus authorized durable artifacts,
    reuse `AIDD-LIVE-007`, and do not duplicate the responsive browser matrix or force synthetic
    provider failures.
  - Verification: focused harness tests accept a dependency-ordered finalized ledger and fail
    closed on identity or tasklist/ledger hash drift, missing task evidence, invalid next-ready
    selection, premature finalization, or Review eligibility that disagrees with the durable
    aggregate commit.
- `W42-E7-S3-T2` (done) Run and retain a fresh Codex task-aware `AIDD-LIVE-007` acceptance.
  - Dependencies: `W42-E7-S2-T3`, `W42-E7-S3-T1`, and `W42-E7-S3-T8` as the final Wave 42
    exit-evidence predecessors.
  - Scope: execute the installed current-`main` flow against the pinned Hono revision through
    Codex from `idea` to `qa`, retaining manual stage-quality audits, target verification, browser
    evidence, Flow Complete evidence, and task-aware checkpoints.
  - Verification: the run has install and provider readiness evidence, a complete `idea -> qa`
    execution, `task-flow-checkpoint.json/.md` snapshots with identity/dependency/attempt/hash/
    finalization/Review truth, final flow/code/quality reports, and no unclassified product diff;
    provider or runtime absence is explicitly environment-blocked.
  - Completion: `eval-live-007-codex-20260821T033606Z` ran from clean `main` revision `2db0e886`
    against Hono revision `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba` and completed all eight stages
    with execution verdict `pass`. The schema-v1 checkpoint is `pass` with matching tasklist/
    ledger hashes, four succeeded tasks, successful aggregate finalization, and Review eligibility.
    Retained bundle reports include flow, code, quality, target-workspace, browser/API checkpoint,
    runtime-log, and per-stage manual quality evidence. The uncoached human predecessor remains
    separately parked and is not claimed as pass; it gates only the later human-usability/default-
    renderer decision, not the Codex-only Wave 43 implementation lane.
- `W42-E7-S3-T3` (done) Stabilize the installed public Task Workspace read boundary used by
  the task-aware live checkpoint.
  - Dependencies: `W42-E7-S3-T1`; this remediation is required before a fresh `W42-E7-S3-T2`
    run can reconcile the task projection.
  - Scope: make the runner's short-lived `/api/tasks` probe resilient to transient UI startup or
    process-lifetime races, retain process/error diagnostics when the public boundary is
    unavailable, and prove that a valid installed task projection is read without relaxing
    fail-closed identity, dependency, hash, finalization, or Review-eligibility checks.
  - Verification: focused harness tests cover a successful public-task read, a transient probe
    retry, and a terminal unavailable boundary with retained diagnostics; existing checkpoint
    tests still fail closed on missing tasks or drift. The Codex live lane is rerun from clean
    `main` after this task merges.
- `W42-E7-S3-T4` (done) Keep the installed public Task Workspace server alive for the task-aware
  checkpoint after the UI root becomes ready.
  - Dependencies: `W42-E7-S3-T3`; this follow-up was discovered by the clean Codex rerun and is
    required before `W42-E7-S3-T2` can produce truthful live evidence.
  - Scope: make the checkpoint's UI process ownership explicit so a wrapper exit cannot orphan or
    terminate the `/api/tasks` server between root readiness and the task projection read; retain
    process-lifetime diagnostics and preserve bounded retry plus fail-closed identity, dependency,
    hash, finalization, and Review-eligibility checks.
  - Verification: focused harness tests cover a server that remains reachable after the launcher
    reports readiness, launcher exit before readiness, and terminal `/api/tasks` unavailability;
    the clean Codex `AIDD-LIVE-007` lane is rerun after this task merges.
- `W42-E7-S3-T5` (done) Make the installed Task Workspace checkpoint use a durable public UI
  server lifecycle rather than a probe-time process that can disappear after root readiness.
  - Dependencies: `W42-E7-S3-T4`; this follow-up is required because the next clean Codex rerun
    still received connection refusal from all bounded `/api/tasks` attempts even though direct
    verification of the same installed UI served the projection.
  - Scope: isolate and fix the remaining launcher/server lifetime boundary, retaining explicit
    server ownership, readiness, shutdown, and endpoint diagnostics without weakening the
    fail-closed task identity, dependency, hash, finalization, or Review-eligibility checks.
  - Verification: focused harness tests reproduce the observed root-ready then connection-refused
    sequence, prove a durable `/api/tasks` read through the installed public surface, and preserve
    terminal diagnostics; the clean Codex `AIDD-LIVE-007` lane is rerun after this task merges.
- `W42-E7-S3-T6` (done) Parse authored task dependencies from structured tasklist clauses without
  treating explanatory prose as task IDs.
  - Dependencies: `W42-E7-S3-T5`; this follow-up is required because the first clean rerun after
    T5 successfully read `/api/tasks` but the checkpoint parser reported dependency drift for every
    task after including the rest of each `Dependencies:` sentence as authored dependencies.
  - Scope: make tasklist dependency extraction preserve only declared task identifiers while
    retaining fail-closed behavior for malformed, missing, or ambiguous dependency clauses and
    preserving the public projection comparison.
  - Verification: focused checkpoint/parser tests cover concise clauses, explanatory prose,
    multiple dependencies, malformed clauses, and public-projection drift; the clean Codex
    `AIDD-LIVE-007` lane is rerun after this task merges.
- `W42-E7-S3-T7` (done) Normalize terminal punctuation in authored dependency identifiers.
  - Dependencies: `W42-E7-S3-T6`; this follow-up was discovered by the fresh Codex rerun after
    T6: the parser now isolates the dependency clause, but authored values such as `T1.` and
    `none.` still differ from the public projection and fail the checkpoint closed.
  - Scope: strip only unambiguous terminal punctuation from parsed task identifiers and the
    `none` sentinel, retain fail-closed behavior for malformed or ambiguous clauses, and keep
    public dependency comparison authoritative.
  - Verification: focused parser/checkpoint tests cover terminal punctuation, explanatory prose,
    concise and multiple dependencies, malformed clauses, and public-projection drift; the
    clean Codex `AIDD-LIVE-007` lane is rerun after this task merges.
- `W42-E7-S3-T8` (done) Isolate native Codex live execution from desktop MCP and plugin configuration.
  - Dependencies: `W42-E7-S3-T7`; this follow-up was discovered by the fresh post-T7 Codex lane,
    where provider startup remained alive without a runtime event until the no-progress boundary,
    while a bounded command with user plugins disabled completed the same research stage.
  - Scope: make the installed native Codex command used by manual live E2E opt out of unrelated
    desktop MCP/plugin startup while retaining authenticated Codex access, model/reasoning
    selectors, repository working directory, raw logs, and the existing fail-closed timeout
    classification. Keep provider-specific isolation in the Codex adapter/runtime command
    definition and do not change runtime-agnostic orchestration semantics.
  - Verification: command/config tests prove the live Codex command carries the isolated startup
    flags without dropping typed selectors; a focused installed-stage smoke reaches a terminal
    artifact with no desktop MCP children; the clean Codex `AIDD-LIVE-007` lane is rerun afterward.
  - Completion: PR #240 (merge `2db0e886`) added the live-only native startup isolation flags,
    preserved model/reasoning selectors, and passed focused tests, Ruff, mypy, and full CI. The
    fresh clean-main Codex lane `eval-live-007-codex-20260821T033606Z` completed `idea -> qa`
    with no provider no-progress boundary.

Wave 42 reconciliation notes:

- `2026-08-21` Codex-only alpha scope is now explicit: `W42-E7-S2-T3` is parked as deferred
  human-usability evidence, while the fresh Codex live checkpoint remains retained as execution
  evidence. Claude, dual-provider, and Wave 36 beta acceptance remain outside this lane. The
  Codex-only Wave 43 ownership foundation is therefore opened without marking the human gate as
  passed or switching the default renderer.

- `2026-08-21` The Codex live-evidence task `W42-E7-S3-T2` is complete. The fresh clean-main
  run `eval-live-007-codex-20260821T033606Z` passed `idea -> qa`, the target verification rerun,
  all manual stage audits, and the schema-v1 task-aware checkpoint. Its bundle retains
  `verdict.md`, `flow-quality-report.md`, `code-quality-report.md`, `quality-report.md`,
  `task-flow-checkpoint.json/.md`, target diff evidence, and frontend/API checkpoints. This
  closes the Codex execution evidence only; `W42-E7-S2-T3` remains `environment-blocked`, so the
  Wave 42 exit gate, default-renderer cutover, and Wave 43 promotion are not claimed.

- `2026-08-21` PR #240 (merge `2db0e886`) completed `W42-E7-S3-T8`. Native Codex live startup
  now opts out of unrelated desktop MCP/plugin configuration while preserving authenticated
  selectors and fail-closed timeout behavior. Focused tests, Ruff, mypy, and full CI passed;
  the clean-main rerun `eval-live-007-codex-20260821T033606Z` completed all eight stages and
  produced a passing task-aware checkpoint. The separate reconciliation of `W42-E7-S3-T2`
  records that live evidence; `W42-E7-S2-T3` remains environment-blocked.

- `2026-08-21` A fresh clean-main run `eval-live-007-codex-20260821T023047Z` passed `idea` with
  manual quality audit, but `research` remained without a first runtime event until the operator
  interrupted it. A disposable installed-stage probe with desktop plugins disabled completed
  `research`, so `W42-E7-S3-T8` is promoted to `Next`; no task-aware live pass or Wave 42 exit
  claim is made.

- `2026-08-21` PR #237 (merge `53208ce7`) completed T7: authored `none.`/`T1.` dependency
  values are normalized without weakening fail-closed handling, with 15 focused harness tests,
  Ruff, mypy, and full CI green. Fresh Codex run `eval-live-007-codex-20260821T013433Z` was
  retained as `infra-fail` after provider no-progress in `idea` at the 30-minute threshold;
  no task-aware live pass or Wave 42 exit claim is made. The genuine uncoached observation is
  still blocked, so `Next` and `Soon` remain empty and Wave 43 stays parked.

- `2026-08-21` PR #235 (merge `9ff76b3f`) made the installed `/api/tasks` projection reachable
  and isolated dependency clauses, but fresh Codex run `eval-live-007-codex-20260821T003332Z`
  still failed closed at the task-aware checkpoint because authored dependencies retained
  terminal punctuation (`T1.`, `none.`). T6 is complete; T7 is promoted as the next bounded
  parser remediation. No Wave 42 exit claim is made.

- `2026-08-20` The clean Codex run `eval-live-007-codex-20260820T233552Z` reached the installed
  `/api/tasks` public projection successfully after T5, with HTTP 200 and retained task identity,
  hash, and dependency data. Checkpoint reconciliation then failed closed on
  `dependency-drift:T1..T4`: authored dependency parsing included explanatory prose from each
  `Dependencies:` sentence, while the public graph contained the correct task IDs. T5 is complete
  in PR #233 (merge `fd6922b7`); `W42-E7-S3-T6` is added and promoted as the next bounded parser
  remediation. No Wave 42 exit claim is made.

- `2026-08-20` The clean Codex rerun `eval-live-007-codex-20260820T222927Z` passed install,
  `idea -> tasklist` stage validation, manual quality audits, target verification, and public UI
  root checkpoints, but the task-aware checkpoint again failed closed: all three `/api/tasks`
  attempts returned connection refused and the short-lived launcher was terminated with `-15`.
  Direct verification of the same installed UI served `/api/tasks`, so this is recorded as a new
  lifecycle-boundary remediation `W42-E7-S3-T5`; no live checkpoint or Wave 42 exit claim is made.

- `2026-08-20` `W42-E7-S3-T4` is complete in PR #230 (merge `afc127fc`). The task checkpoint now
  records bounded launcher attempts, relaunches an installed UI process that exits before root
  readiness, and continues bounded `/api/tasks` probes after a launcher exit so a surviving
  server is not mistaken for an unavailable boundary. Process state, return codes, launcher
  attempts, and captured output are retained on failure. Focused checkpoint/tasklist tests (11),
  the full live-E2E harness suite (64), docs/planning tests (50), Ruff, mypy, deterministic/
  adapter checks, security checks, and packaged UI browser CI passed. The clean Codex live lane
  must still be rerun from this merge; no Wave 42 exit claim is made.

- `2026-08-20` The clean Codex rerun `eval-live-007-codex-20260820T210403Z` passed install,
  `idea -> tasklist` stage validation, quality audits, target verification, and all public UI
  root checkpoints, but the task-aware checkpoint still failed closed on connection refusal at
  `/api/tasks` immediately after root readiness. The T3 bounded retry retained the unavailable
  boundary but did not solve the launcher/server lifetime race; `W42-E7-S3-T4` is added as a
  separate remediation before another live retry. No Wave 42 exit claim is made.

- `2026-08-20` `W42-E7-S3-T3` is complete in PR #227 (merge `9613b203`). The installed public
  `/api/tasks` probe now retries transient startup/process-lifetime failures within a bounded
  window and retains endpoint, attempt, process, and error diagnostics when the boundary remains
  unavailable. Focused checkpoint/probe tests, the full live-E2E harness suite, Ruff, mypy,
  deterministic/adapter checks, security checks, and packaged UI browser CI passed. The fresh
  Codex acceptance still must be rerun from this clean `main`; `W42-E7-S3-T2` remains blocked by
  the missing eligible human observation and no Wave 42 exit claim is made.

- `2026-08-20` Fresh Codex `AIDD-LIVE-007` attempts reached a valid tasklist but both stopped at
  the task-aware checkpoint because the installed short-lived `/api/tasks` public read boundary
  returned connection refused. Direct UI verification served the same endpoint, so the failure
  is classified as a repeatable harness/read-boundary race rather than a Hono target defect.
  `W42-E7-S3-T3` is added as a bounded remediation before retrying the live acceptance; no
  checkpoint pass or Wave 42 exit claim is made.

- `2026-08-20` `W42-E7-S2-T3` implementation contract is complete in PR #224 (merge `72aee00e`):
  real human observations require confidence, and the bounded blocker helper emits sanitized
  `environment-blocked` records that cannot claim completion. No eligible participant was
  available in this execution context, so the task remains `blocked` rather than being reported
  as passed. Its direct successor `W42-E7-S3-T2` is also `blocked`; the Wave 42 exit gate and
  default-renderer decision remain gated until a fresh anonymized human observation is supplied.

Wave 42 exit evidence:

- the target contract, code, fixtures, browser evidence, and backlog agree;
- every launch exposes one eligible Runner and one action, while non-launch surfaces hide it;
- Tasks is the default Deliver workspace and preserves core dependency/status truth;
- generated Markdown is read-only and every supported operator write previews Markdown, names its
  destination, survives failure, and reconciles to durable state;
- all 13 reference states are executable without provider credentials;
- maintained live product-evaluation evidence exposes task-plan, task-attempt, finalization, and
  downstream-eligibility truth instead of reducing Implement to one opaque stage result;
- the responsive matrix and observed first-time journey pass before the target shell becomes the
  default renderer.

---

## Wave 43 — validation and repair resilience (`planned`)

Goal: make the document-first workflow reliable across maintained and lower-capability runtimes
by separating runtime-authored content from AIDD-owned workflow records, preserving canonical
interview state, producing root-cause validation evidence, and providing one audited recovery
path after automatic repair exhaustion without weakening fail-closed progression.

This wave is runtime-neutral. It does not add provider-specific exceptions, accept missing
semantic content, reset repair history, permit generated Markdown to bypass validation, or add a
downstream rerun cascade. Safe Markdown-equivalent syntax may be normalized only when the same
required meaning is present. Runtime/provider differences remain adapter evidence and eval
variables rather than core branches.

Reference authority:

1. [Target architecture](../architecture/target-architecture.md) for lifecycle, document
   ownership, validation, repair, and adapter boundaries;
2. [Target Operator Experience](../architecture/operator-frontend-target-ux.md) for generated
   document ownership, Decision Workbench recovery, Runner placement, and attempt visibility;
3. document and stage contracts under `contracts/` for canonical Markdown grammar;
4. retained IUIT-1203 question, stage-result, tasklist, validator, repair, and runtime evidence
   after sanitization under the first Wave 43 task.

Linked stories: `US-01`, `US-02`, `US-03`, `US-04`, `US-05`, `US-06`, `US-07`, `US-10`,
`US-11`, `US-13`

Wave sequencing: Codex-only Wave 42 execution evidence is reconciled, while the genuine uncoached
human observation and default-renderer usability decision remain parked. The parked failure-corpus
task may prepare sanitized evidence, and Wave 43 functional changes may now proceed as the
Codex-only alpha lane; they remain separate from Wave 42 UI branches. Task-aware live checkpoint
schema v1 is the compatibility baseline for later resilience work; Wave 43 readers remain
compatible with retained pre-Wave-43 runs. The repair-extension UI continues to depend explicitly
on `W42-E5-S1`. Claude, dual-provider, and cross-runtime acceptance are deferred.

### Epic W43-E1 — artifact ownership and terminal records (`planned`)

Goal: make each stage request only runtime-authored content while AIDD owns validation and
terminal workflow records end to end.

#### Slice W43-E1-S1 — failure corpus and ownership contract (`planned`)

Primary output: reproducible failure fixtures plus one ownership matrix for runtime content,
workflow records, control documents, interview ledgers, and raw candidate evidence.

Touched areas:

- `docs/analysis/`
- `docs/architecture/target-architecture.md`
- `contracts/documents/`
- `contracts/stages/`

Dependencies: retained IUIT-1203 artifacts or sanitized equivalents supplied from the observed
Qwen run; contract work may begin from the already captured log/report evidence when the exact
documents are unavailable.

Local tasks:

- `W43-E1-S1-T1` (done) Record the validation and repair failure corpus.
  - Scope: sanitize and retain the malformed question resume, service-document placeholder,
    malformed rich-tasklist, cascade finding, and repair-exhaustion shapes; identify the first
    decisive boundary, runtime, stage, attempt mode, and automatic repair consumption for each.
  - Verification: every retained case is replayable through a provider-free parser, validator,
    or lifecycle fixture and distinguishes primary cause from related findings.
- `W43-E1-S1-T2` (done) Define the canonical stage-document ownership matrix.
  - Scope: classify every stage document exactly once as runtime content, AIDD workflow record,
    AIDD control document, interview ledger, or raw candidate evidence; name create, mutate,
    validate, publish, and UI-authoring permissions without changing the eight-stage graph.
  - Verification: contract-registry coverage proves every declared document has one owner and
    rejects conflicting runtime/AIDD ownership.
  - Completion: PR #244 (merge `a4d777c4`) added the canonical Markdown matrix, linked all eight
    stage contracts to it, and added coverage tests that fail on missing, duplicate, or conflicting
    ownership rows. Focused docs/planning tests (53), Ruff, mypy, and full CI passed.

#### Slice W43-E1-S2 — ownership-aware output registry and stage brief (`planned`)

Primary output: typed output categories used independently for runtime requests, system
generation, validation, and publication.

Touched areas:

- `src/aidd/core/stage_registry.py`
- `src/aidd/core/stage_preparation.py`
- core registry/preparation tests

Dependencies: `W43-E1-S1`.

Local tasks:

- `W43-E1-S2-T1` (done) Split stage output resolution by document owner.
  - Scope: expose runtime-authored, AIDD-generated, interview/control, and published document
    sets for all eight stages; retain a bounded compatibility reader only where existing callers
    require migration.
  - Verification: one table-driven core test asserts the exact four sets for every stage and
    proves `stage-result.md` and `validator-report.md` are absent from runtime completion targets.
  - Completion: PR #246 (merge `f9f74bf6`) added typed `StageOutputRegistry` projections for all
    eight stages and retained `resolve_expected_output_documents` as the complete compatibility
    reader. Focused registry/preparation/runner/workflow tests (116), docs/planning/ownership tests
    (53), Ruff, mypy, and full CI passed.
- `W43-E1-S2-T2` (done) Render ownership-aware stage briefs.
  - Scope: list runtime write targets, AIDD-generated records, read-only inputs, and stage-specific
    skeletons separately in installed and source-checkout briefs; remove instructions that ask the
    runtime to author canonical terminal records.
  - Verification: stage-brief snapshots for all stages and prompt-quality checks agree on write
    ownership and required content headings.
  - Completion: PR #248 (merge `4db5613e`) added owner-separated stage briefs, updated all eight
    stage run prompts, refreshed prompt-pack hashes, and passed 167 focused tests, 50 docs/planning
    tests, Ruff, mypy, full CI, packaged UI browser, and build checks.

#### Slice W43-E1-S3 — canonical validator and stage-result generation (`planned`)

Primary output: AIDD-generated validator and terminal records derived from canonical lifecycle
state rather than runtime-authored drafts.

Touched areas:

- `src/aidd/core/stage_outputs.py`
- `src/aidd/core/stage_terminal.py`
- `src/aidd/core/repair.py`
- focused core and validator tests

Dependencies: `W43-E1-S2`.

Local tasks:

- `W43-E1-S3-T1` (done) Generate canonical validator reports only after content validation.
  - Scope: validate runtime-content documents, retain an unexpected runtime validator draft only
    as attempt evidence, and write the canonical report from actual findings; do not require a
    model-authored validator file for output discovery.
  - Verification: missing and contradictory runtime drafts cannot create or suppress findings,
    while the final report exactly matches the current attempt's validator result.
- `W43-E1-S3-T2` (done) Render stage results from canonical lifecycle state.
  - Scope: derive stage id, attempt history, status, produced outputs, validation summary,
    blockers, next action, and terminal notes from AIDD state; preserve historical repair evidence
    and make repeated reconciliation byte-stable.
  - Verification: state-matrix tests cover succeeded, failed, blocked, repair-needed, exhausted,
    and resumed outcomes, including the exact `Terminal state notes: TODO` regression without
    consuming repair budget.
-  - Completion: PR #253 (merge `e2899537`) added a lifecycle-only stage-result projection and
    wired it into success, repair, blocked, exhausted, and adapter-stop paths. Canonical output
    preserves attempt/repair evidence, deterministic next actions, validator findings, repair
    budget notes, and durable project-set evidence; repeated reconciliation is byte-stable.
    Focused stage-terminal/repair/stage-runner tests (127), Ruff, mypy, full CI, deterministic
    scenarios, packaged UI browser, and build passed. `W43-E1-S3-T3` is now the next
    dependency-ready task.
- `W43-E1-S3-T3` (done) Enforce workflow-record ownership at every mutation boundary.
  - Scope: exclude AIDD records from misplaced runtime promotion and operator intervention
    targets, include canonical records during publication and indexing, and retain unexpected
    runtime copies only under attempt evidence.
  - Verification: discovery, publication, intervention, and artifact-index tests reject a runtime
    or operator overwrite while publishing the AIDD-owned records once.
  - Completion: PR #255 (merge `83e3a7ce`) made runtime completion targets and operator
    intervention targets runtime-owned only, retained unexpected stage-result, validator-report,
    and repair-brief drafts under attempt evidence, and classified those drafts as runtime
    evidence in the operator graph. Canonical records remain published and indexed exactly once.
    Focused ownership/stage-runner/intervention/frontend tests (209), docs/planning tests (50),
    Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.

#### Slice W43-E1-S4 — adapter document-completion alignment (`planned`)

Primary output: maintained adapters declare document completion from runtime-authored targets
only while preserving raw logs and canonical validation.

Touched areas:

- `src/aidd/adapters/`
- adapter conformance and runner tests

Dependencies: `W43-E1-S2`.

Local tasks:

- `W43-E1-S4-T1` (done) Align maintained adapter completion with runtime-authored outputs.
  - Scope: update generic CLI, Qwen, and OpenCode completion/settling behavior to wait only for
    runtime-content documents; retain adapter success as process evidence, not validation pass,
    and keep all provider-specific detection inside adapters.
  - Verification: adapter matrices prove a runtime may finish after writing only its content
    targets, raw stdout/stderr remain retained, and canonical validation still decides progression.
  - Completion: PR #257 (merge `6b87d863`) centralizes runtime-content completion settling for the
    maintained adapters, excludes AIDD workflow/interview/control records from completion targets,
    and preserves raw stdout/stderr as attempt evidence. Generic CLI now supports the same bounded
    document-complete stop reason; adapter surface tests prove canonical validation remains the
    progression authority. Adapter tests (270), core stage/registry/preparation tests (382),
    docs/planning/contract tests (51), Ruff, mypy, full CI, deterministic scenarios, packaged UI
    browser, and build passed.

### Epic W43-E2 — canonical interview resume (`planned`)

Goal: preserve operator answers and unresolved questions across attempts while accepting only
deterministically normalizable runtime question candidates.

#### Slice W43-E2-S1 — interview ledger and candidate ingestion (`planned`)

Primary output: one AIDD-owned question ledger fed by structured events or raw Markdown
candidates, with operator-owned answers protected from runtime mutation.

Touched areas:

- `contracts/documents/questions.md`
- `contracts/documents/answers.md`
- `src/aidd/core/interview.py`
- interview tests and examples

Dependencies: `W43-E1-S1-T2`.

Local tasks:

- `W43-E2-S1-T1` (done) Define canonical interview candidate and ledger semantics.
  - Scope: document QID merge rules, operator answer ownership, safe punctuation/list
    normalization, raw evidence retention, unresolved-question preservation, and explicit
    operator-attention behavior for ambiguous candidates.
  - Verification: contract examples cover canonical, safely normalizable, duplicate, omitted,
    and ambiguous question/answer cases without inventing decisions.
  - Completion: PR #259 (merge `0dd3e22e`) defined the canonical candidate/ledger boundary in
    both interview document contracts, added canonical/safe/duplicate/ambiguous/omitted worked
    examples, and added focused parser/persistence tests. Focused interview, contract, docs,
    planning, Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.
- `W43-E2-S1-T2` (done) Ingest structured and Markdown question candidates tolerantly.
  - Scope: normalize marker-adjacent colons, equivalent Markdown list markers, nested
    continuation text, and matching QIDs; preserve the raw candidate and reject semantic
    ambiguity without overwriting the ledger.
  - Verification: a table-driven parser matrix round-trips valid variants to canonical Markdown
    and leaves the prior ledger byte-identical for rejected candidates.
  - Completion: PR #261 (merge `75a14f59`) added tolerant question/answer candidate parsers,
    raw rejected-candidate details, safe continuation normalization, and persistence coverage;
    focused interview tests, Ruff, mypy, full CI, deterministic scenarios, packaged UI browser,
    and build passed.
- `W43-E2-S1-T3` (done) Merge interview state safely after every runtime attempt.
  - Scope: snapshot questions and answers before execution, merge valid candidates by QID,
    preserve omitted unresolved questions, restore operator answers, and expose rejected candidate
    evidence to the attempt index.
  - Verification: blocked -> answer -> resume -> malformed candidate retains valid canonical
    ledgers and either progresses or stops in explicit operator-attention state.
  - Completion: PR #263 (merge `a489b7c7`) implemented QID-preserving runtime merges, protected
    operator answers, raw candidate/disposition evidence in the attempt index, and a no-repair-budget
    operator-attention stop for rejected candidates. Focused core/adapter/validator tests (168),
    Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.

#### Slice W43-E2-S2 — resume accounting and operator recovery (`planned`)

Primary output: a distinct resume attempt identity plus an actionable rejected-candidate recovery
surface.

Touched areas:

- `src/aidd/core/models/run.py`
- `src/aidd/core/stage_invocation.py`
- `src/aidd/core/stage_validation.py`
- operator frontend read models and question UI

Dependencies: `W43-E2-S1`; frontend task additionally depends on `W42-E5-S1`.

Local tasks:

- `W43-E2-S2-T1` (done) Add `resume` as a non-repair attempt mode.
  - Scope: persist and render `initial`, `repair`, `resume`, and `intervention` distinctly; count
    only validation-triggered repair attempts against the automatic budget and read legacy
    manifests compatibly.
  - Verification: `initial -> repair -> blocked -> resume -> repair` records two repairs, one
    resume, monotonic attempt history, and the correct remaining budget.
  - Completion: PR #265 (merge `f774b9df`) persists and renders distinct `resume` attempt
    identity, counts only explicit `repair` modes against the budget, routes blocked-answer
    resumes through the core/CLI, and preserves legacy artifact-index fallback. Focused core,
    docs/planning, full Python suite (2323), Ruff, mypy, full CI, deterministic scenarios,
    packaged UI browser, and build passed.
- `W43-E2-S2-T2` (done) Expose rejected interview candidate diagnostics in the core UI model.
  - Scope: publish canonical question, protected answer, raw rejected fragment, source attempt,
    runtime, reason, and eligible recovery without making the frontend parse Markdown.
  - Verification: core/service tests cover absent, accepted, rejected, stale, and permission-
    unavailable candidate evidence with one deterministic next action.
  - Completion: PR #267 (merge `13ba2cd9`) projects bounded rejected, accepted, stale, absent, and
    permission-unavailable candidate diagnostics from retained evidence, preserves canonical QID
    answers, and exposes resume-only recovery guidance without frontend Markdown parsing. Focused
    core/docs/planning tests (122), full Python suite (2326), Ruff, mypy, full CI, deterministic
    scenarios, packaged UI browser, and build passed.
- `W43-E2-S2-T3` (done) Render bounded interview rejection recovery in the Decision Workbench.
  - Scope: show the rejected fragment and canonical state, preserve answer drafts, and offer only
    the eligible confirm/edit/resume or request-change action; do not schedule a repair merely to
    fix candidate punctuation.
  - Verification: provider-free browser flow covers answer, rejected resume candidate, evidence
    inspection, recovery, focus restoration, and unchanged repair budget.
  - Completion: PR #269 (merge `11d8e62d`) renders bounded rejected-candidate diagnostics in the
    Decision Workbench, keeps canonical answers and browser drafts authoritative, supports retained
    evidence inspection, preserves focus for edit/review, and routes resume without repair. Frontend
    tests (132), UI/docs/planning contracts (102), provider-free mobile/desktop browser recovery,
    full Python suite (2326), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser,
    and build passed.

### Epic W43-E3 — rich-tasklist authoring and diagnosis (`planned`)

Goal: make the strict executable tasklist grammar easier for weaker runtimes to produce and make
one formatting root cause yield one actionable repair rather than dozens of cascade findings.

#### Slice W43-E3-S1 — task-card grammar and embedded scaffold (`planned`)

Primary output: one documented rich-task grammar plus a complete installed-package scaffold.

Touched areas:

- `contracts/documents/tasklist.md`
- `contracts/stages/tasklist.md`
- `prompt-packs/stages/tasklist/`
- `src/aidd/core/stage_preparation.py`

Dependencies: `W43-E1-S2-T2`.

Local tasks:

- `W43-E3-S1-T1` (done) Separate required task semantics from safe Markdown presentation.
  - Scope: retain H3 task cards, outcome, dominant deliverable, bounded in-scope paths,
    task-local acceptance criteria, dependencies, and dedicated verification; document equivalent
    emphasis/list punctuation and continue rejecting compact or ambiguous table-like tasklists.
  - Verification: contract/example tests accept only meaning-preserving variants and reject any
    document missing executable task semantics.
  - Completion: PR #271 (merge `da566a09`) separated required task semantics from presentation-only
    Markdown changes in the document and stage contracts, added safe/invalid presentation fixtures,
    and retained fail-closed parser coverage for compact and table-like tasklists. Focused
    task-plan/prompt checks (30), docs/planning/semantic checks (56), full Python suite (2330),
    Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.
- `W43-E3-S1-T2` (done) Embed a complete rich-tasklist scaffold in the stage brief.
  - Scope: render one canonical H3 card, nested acceptance criterion, dependency entry, and
    verification entry in the installed brief; keep prompt text lean and ensure scaffold
    placeholders are prompt input rather than validated output.
  - Verification: stage-preparation snapshots and installed-package fixtures expose the same
    copyable grammar without requiring repository-local contract discovery.
  - Completion: PR #273 (merge `885deee2`) embeds a complete rich-tasklist card scaffold in
    generated stage briefs, including outcome, dominant deliverable, bounded in-scope paths,
    nested task-local acceptance, dependency, and verification entries. It works without
    repository-local contract discovery and declares itself prompt input rather than validated
    output. Focused stage-preparation/stage-runner tests (11), docs/prompt/planning checks (161),
    full Python suite (2331), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser,
    and build passed.

#### Slice W43-E3-S2 — tolerant task parsing and located issues (`planned`)

Primary output: one typed task plan from safe Markdown variants and structured parse issues for
content that remains invalid.

Touched areas:

- `src/aidd/core/task_plan.py`
- task-plan unit tests

Dependencies: `W43-E3-S1`.

Local tasks:

- `W43-E3-S2-T1` (done) Parse safe rich-task Markdown variants without semantic inference.
  - Scope: accept equivalent `-`/`*` markers, emphasized field labels, backticked/emphasized task
    ids, and supported heading separators; retain strict paths, acceptance ids, dependencies, and
    verification requirements.
  - Verification: canonical and safe-variant documents produce equivalent typed task plans while
    compact, table-like, unsafe, duplicate, and semantically incomplete cases remain invalid.
  - Completion: PR #275 (merge `190d1a51`) added presentation-only normalization for list markers,
    emphasis/backticks around syntactic labels and ids, and supported heading separators while
    preserving strict executable semantics. Focused parser/semantic tests (34), docs/planning
    checks (50), full Python suite (2332), Ruff, mypy, full CI, deterministic scenarios, packaged
    UI browser, and build passed.
- `W43-E3-S2-T2` (done) Return structured task parse issues with exact source locations.
  - Scope: replace string-only issues with kind, task id, heading/field line, missing fields, and
    root/related classification while retaining a compatibility error message for existing
    callers.
  - Verification: each malformed card points to its own source line and one missing field no
    longer produces an unrelated path or verification derivative.
  - Completion: PR #277 (merge `2b9bc9dd`) added typed parse issues with kind, task id, exact source
    line, field, missing-fields, and root/related metadata; semantic tasklist findings now retain
    precise locations while compatibility messages remain stable. Focused core/validator tests
    (105), task-plan regression tests (38), docs/planning checks (50), full Python suite (2336),
    Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed; the
    independent Python 3.12 UI-cancellation timing failure passed on rerun.

#### Slice W43-E3-S3 — root-cause tasklist validation and repair (`planned`)

Primary output: calibrated, grouped tasklist findings and one exact repair strategy.

Touched areas:

- `src/aidd/validators/semantic_rules/tasklist.py`
- `src/aidd/core/repair.py`
- tasklist validator and repair tests

Dependencies: `W43-E3-S2` and `W43-E4-S1` for final repair wording.

Local tasks:

- `W43-E3-S3-T1` (done) Collapse tasklist cascade issues into primary findings.
  - Scope: group a shared unrecognized card grammar across task ids, list affected ids and missing
    fields once, retain independent dependency/verification findings, and report the first exact
    offending line rather than the common `Ordered tasks` heading.
  - Verification: the retained eleven-card IUIT shape produces one grammar root finding plus only
    genuinely independent findings instead of six or seven messages per task.
- Completion: PR #304 (merge `59af3079`) groups repeated card-grammar failures by root cause,
    preserves independent dependency findings, and anchors the finding to the first offending
    source line. Focused semantic/repair tests (138), resilience/report checks (54), Ruff, mypy,
    docs/planning checks, and the full PR CI including deterministic scenarios, packaged UI
    browser, adapter conformance, and build passed.
- `W43-E3-S3-T2` (done) Calibrate tasklist finding severity to executability.
  - Scope: mark globally unreadable grammar and missing execution-critical card fields high,
    retain material verification gaps as medium repair-required findings, and omit findings for
    safely normalized presentation-only variants.
  - Verification: a severity matrix keeps incomplete tasklists fail-closed and prevents an
    unexecutable document from presenting a misleading no-blocker summary.
  - Completion: PR #306 (merge `3825b465`) classifies unreadable grammar and execution-critical
    card failures as `high`, dependency/verification gaps as `medium`, and keeps safe presentation
    variants finding-free. Focused tasklist/task-plan/repair/docs tests (152), resilience/report
    checks (54), Ruff, mypy, and full PR CI including deterministic scenarios, packaged UI
    browser, adapter conformance, and build passed.
- `W43-E3-S3-T3` (done) Render one tasklist-specific correction strategy.
  - Scope: preserve stable ids and valid cards, name the canonical card scaffold, repair only the
    affected section, and synchronize dependency and verification entries without asking the
    runtime to resolve every cascade message individually.
  - Verification: a deterministic repair fixes the retained malformed-tasklist shape in one
    attempt while unrelated valid sections remain byte-identical.
  - Completion: PR #308 (merge `52943ae2`) adds one tasklist-specific bounded correction strategy
    to the core repair brief: stable ids and valid cards are preserved, the canonical rich-task
    scaffold is named, only affected sections are patched, dependencies and verification entries
    are synchronized, and a complete re-parse is required. Focused repair/tasklist tests (153),
    resilience/report checks (54), Ruff, mypy, and full PR CI including deterministic scenarios,
    packaged UI browser, adapter conformance, and build passed.

### Epic W43-E4 — repair protocol and operator-authorized extension (`planned`)

Goal: make every progression-blocking correction explicit and permit one audited additional
repair after exhaustion without resetting automatic budget or conflating repair with Request
Change.

#### Slice W43-E4-S1 — progression-required repair semantics (`planned`)

Primary output: repair reports distinguish severity from progression impact and never label a
fail-causing correction optional.

Touched areas:

- `contracts/documents/validator-report.md`
- `contracts/documents/repair-brief.md`
- `src/aidd/core/repair.py`
- report and repair tests

Dependencies: `W43-E1-S1-T2`.

Local tasks:

- `W43-E4-S1-T1` (done) Define severity, progression, and advisory semantics explicitly.
  - Scope: preserve severity as impact, define every canonical fail finding as required for
    progression, reserve advisory observations for non-verdict evidence, and keep protocol-v1
    read compatibility where labels change.
  - Verification: contract/protocol tests reject `Verdict: fail` with only optional corrections
    and keep legacy reports readable.
  - Completion: PR #279 (merge `893300ce`) made every canonical fail finding progression-required,
    separated impact severity from repair eligibility, reserved advisory observations for
    non-verdict evidence, and retained protocol-v1 read compatibility. Focused repair/protocol/
    report tests (83), compatibility checks (96), docs/planning checks (50), full Python suite
    (2339), Ruff, mypy, and full CI including deterministic scenarios, adapter conformance,
    packaged UI browser, and build passed.
- `W43-E4-S1-T2` (done) Group repair briefs into primary, related, and advisory corrections.
  - Scope: replace high/critical mandatory versus medium/low optional grouping with progression-
    aware sections, retain exact evidence paths, and allow validator-specific bounded hints
    without runtime-specific branches.
  - Verification: a single medium fail finding renders under required corrections, duplicate or
    related findings collapse, and advisory-only evidence does not request a repair.
  - Completion: PR #281 (merge `ed3aa1ba`) added progression-aware primary, related, and advisory
    repair sections, explicit non-verdict advisory parsing, duplicate/related evidence collapse
    with exact paths, and bounded correction rendering. Focused repair/protocol/report tests (88),
    contract/stage/docs/planning checks (161), full Python suite (2344), Ruff, mypy, and full CI
    including deterministic scenarios, adapter conformance, packaged UI browser, and build passed.

#### Slice W43-E4-S2 — repair-extension contract and accounting (`planned`)

Primary output: a durable one-attempt operator grant plus separate automatic and manual repair
accounting.

Touched areas:

- architecture and repair document contracts
- `src/aidd/core/models/run.py`
- `src/aidd/core/repair.py`
- repair accounting tests

Dependencies: `W43-E2-S2-T1` and `W43-E4-S1`.

Local tasks:

- `W43-E4-S2-T1` (done) Define the operator-authorized repair-extension contract.
  - Scope: permit exactly one additional attempt only for the latest `repair-exhausted` stage,
    retain run/stage identity, validator and brief hashes, author/time/reason, same-run selection
    constraints, no succeeded downstream, and no validation bypass; keep Request Change and new
    run as separate actions.
  - Verification: allowed and rejected contract examples cover exhausted, generic failed, stale,
    already-extended, downstream-succeeded, intervention, and configuration-drift cases.
  - Completion: PR #283 (merge `b7485171`) added the durable `repair-extension.md` contract,
    immutable core grant evidence for run/stage, validator/brief hashes, configuration identity,
    author, timestamp, and reason, plus pure fail-closed eligibility checks for exhaustion-only,
    stale evidence, configuration drift, intervention, active jobs, prior grants, downstream
    success, identity mismatch, and validation bypass. Focused repair tests (41), harness/package
    fixture tests (48), docs/planning/packaging checks (51), Ruff, mypy, full Python matrix,
    deterministic scenarios, adapter conformance, packaged UI browser, and build passed.
- `W43-E4-S2-T2` (done) Account automatic repairs and manual extensions separately.
  - Scope: add `repair-extension` attempt/history identity, preserve the original automatic
    budget and exhaustion record, count one durable operator grant, and read older attempt indexes
    without the new mode.
  - Verification: `initial -> repair -> repair -> exhausted -> repair-extension` records two
    automatic repairs and one manual extension without resetting history or scheduling another
    automatic retry.
  - Completion: PR #285 (merge `14147d97`) added durable `repair-extension` metadata and attempt
    identity, preserved automatic repair budgets and exhaustion history, kept legacy attempt indexes
    readable, and rejected duplicate grants. Focused repair-flow tests (70), Ruff, mypy, full Python
    matrix, deterministic scenarios, adapter conformance, packaged UI browser, and build passed.
#### Slice W43-E4-S3 — guarded repair reopen and CLI (`planned`)

Primary output: one application service and CLI command that revalidates before issuing a single
repair extension.

Touched areas:

- application/core recovery service
- `src/aidd/cli/stage.py`
- `src/aidd/cli/stage_run.py`
- focused core and CLI tests

Dependencies: `W43-E1-S3`, `W43-E4-S2`, and the existing no-downstream-intervention guard.

Local tasks:

- `W43-E4-S3-T1` (done) Implement guarded repair-extension preflight and reopen.
  - Scope: verify failure reason, latest verdict, inactive job, downstream state, evidence hashes,
    and unused grant; revalidate current documents first, finalize without runtime when manual
    edits already pass, otherwise persist the grant and regenerate a fresh bounded repair brief.
  - Verification: only an eligible exhausted stage opens; generic failure, stale evidence,
    concurrent work, downstream success, and second grant stop before runtime execution.
  - Completion: PR #287 (merge `24d974a2`) added core-owned guarded preflight with fail-closed
    evidence, configuration, concurrency, downstream, identity, and duplicate-grant checks;
    manual-pass finalization writes a fresh pass report without runtime, while unresolved findings
    persist one grant, bounded `repair-extension` evidence, and reopen state without changing
    automatic repair accounting. Extension attempts consume the dedicated brief through stage
    invocation. Focused repair/stage tests (131), docs/planning checks (50), Ruff, mypy, full
    Python matrix, deterministic scenarios, adapter conformance, packaged UI browser, and build
    passed.
- `W43-E4-S3-T2` (done) Expose one explicit CLI repair-extension command.
  - Scope: select exact work item/run/stage/runtime, preview findings and budget, require operator
    confirmation or an explicit non-interactive flag, stream logs, and print grant, attempt, and
    validator evidence paths.
  - Verification: CLI tests cover prevalidation success, extension success/failure, cancellation,
    stale selection, non-interactive refusal, and no second extension.
  - Completion: PR #289 (merge `bf556dca`) added `aidd stage repair-extension` with exact
    run/stage/runtime selection, core preflight and configuration identity revalidation, findings
    and automatic-budget preview, explicit confirmation/non-interactive authorization, durable
    grant/attempt/evidence output, cancellation propagation, and a one-attempt fail-closed runtime
    path with no automatic retry loop. Focused CLI tests (35), core repair/stage tests (150),
    docs/planning checks (50), Ruff, mypy, full Python matrix, deterministic scenarios, adapter
    conformance, packaged UI browser, and build passed.

#### Slice W43-E4-S4 — repair-extension operator UI (`planned`)

Primary output: core-owned eligibility plus a Validation Recovery action that distinguishes one
more repair, Request Change, and a new run.

Touched areas:

- operator frontend recovery read models
- UI service mutation endpoint
- `src/aidd/cli/static/operator-stage-cockpit.js`
- frontend and browser tests

Dependencies: `W43-E3-S3`, `W43-E4-S3`, and `W42-E5-S1`.

Local tasks:

- `W43-E4-S4-T1` (done) Publish repair-extension eligibility and preview evidence.
  - Scope: expose primary cause, current findings, automatic budget, manual grant usage, exact
    validator/brief hashes, selected Runner, downstream restriction, and a literal disabled reason
    from core/service code.
  - Verification: service tests cover eligible, manually-fixed, stale, active, downstream-
    succeeded, already-used, and configuration-drift states without frontend inference.
  - Completion: PR #291 (merge `6456124f`) added the core-owned repair-extension preview projection,
    propagated configuration identity, selected Runner, active-job and downstream context through
    the service/dashboard read paths, and covered eligible, stale, active, manual-grant, downstream,
    manual-fix, and configuration-drift states. Focused repair/frontend/CLI tests (180), docs/
    planning checks (50), Ruff, mypy, full Python matrix, deterministic scenarios, adapter
    conformance, packaged UI browser, and build passed.
- `W43-E4-S4-T2` (done) Render `Run one more repair` as bounded recovery.
  - Scope: show one repair-extension primary action only when eligible, preview that history and
    budget are not reset, retain Request Change and Start new run as distinct alternatives, stream
    the exact attempt, and reconcile to canonical server state.
  - Verification: desktop/mobile browser fixtures cover extension success, extension failure,
    prevalidation success, disabled reasons, duplicate suppression, reconnect, and one primary
    action per recovery state.
  - Completion: PR #293 (merge `e4eb8a42`) added the bounded UI recovery action and loopback
    mutation endpoint backed by the existing core preflight/CLI command, with exact run/stage/
    runtime selection, service revalidation, streamed attempt logs, durable job readback, and
    separate Request Change/Start new run alternatives. Focused UI/CLI/core/frontend tests,
    docs/planning checks, Ruff, mypy, full Python matrix, deterministic scenarios, adapter
    conformance, packaged UI browser, and build passed; the browser contract was reconciled to
    the new eligible exhausted-state primary action.

### Epic W43-E5 — resilience regression and Codex-only evidence (`planned`)

Goal: prove the ownership, interview, tasklist, and repair-extension behavior deterministically,
then measure repeatability through a Codex-only live lane without claiming cross-provider readiness.

#### Slice W43-E5-S1 — provider-free resilience scenarios (`planned`)

Primary output: deterministic scenarios for every observed false-exhaustion and recovery path.

Touched areas:

- `src/aidd/evals/self_repair_probes.py`
- `harness/scenarios/deterministic/`
- validator, core, adapter, CLI, and browser fixtures selected by the scenario manifests

Dependencies: each owning Wave 43 functional slice; scenarios may land incrementally with their
owner and the slice closes after `W43-E4`.

Local tasks:

- `W43-E5-S1-T1` (done) Add ownership, interview, and tasklist resilience scenarios.
  - Scope: cover missing or contradictory runtime workflow drafts, service placeholder content,
    malformed question after resume, safe question/tasklist variants, eleven malformed cards,
    one malformed card, root-cause repair, and non-repair resume accounting.
  - Verification: each scenario asserts terminal state, attempt modes, budget, canonical ledgers,
    workflow records, root findings, raw evidence, and fail-closed semantic omissions.
- Completion: PR #295 (merge `17dfbdae`) added ten provider-free resilience scenarios backed by
  production interview/tasklist parsers and the retained failure corpus, a manual
  `AIDD-DETERMINISTIC-005` manifest, located malformed-card fixtures, lifecycle/evidence JSON
  reporting, and expanded self-repair probe coverage. Focused eval/failure-corpus/probe/stage-
  timing/harness tests (71), full Python suite (2387), Ruff, mypy, deterministic scenarios,
  adapter conformance, packaged UI browser, and build passed. `W43-E5-S1-T2` is now the next
  dependency-ready task; human usability, Claude, cross-runtime, and Wave 36 work remain parked.
- `W43-E5-S1-T2` (done) Add repair-extension eligibility and terminal scenarios.
  - Scope: cover extension success, repeated failure, manual-fix prevalidation, stale evidence,
    downstream success, second grant, Request Change separation, and immutable history.
  - Verification: provider-free runs assert exact grant content, attempt history, report lineage,
    no automatic loop, and unchanged downstream artifacts.
- Completion: PR #297 (merge `69e3f214`) added the production-backed repair-extension scenario
  runner, eight sanitized terminal-path fixtures, and the `AIDD-DETERMINISTIC-006` manifest.
  Reports retain exact grant content and hashes, distinct repair-extension attempt modes, budget
  and history accounting, report lineage, stale/downstream/second-grant guards, Request Change
  separation, and immutable source history. Focused repair/core/eval tests (62), scenario tests
  (10), docs/scenario/planning tests (113), Ruff, mypy, deterministic scenarios, adapter
  conformance, packaged UI browser, and build passed. `W43-E5-S2-T1` is now the next
  dependency-ready task; human usability, Claude, cross-runtime, and Wave 36 work remain parked.

#### Slice W43-E5-S2 — Codex stability lane (`planned`)

Primary output: a repeatable Codex profile that measures whether Wave 43 reduces false repair
exhaustion without weakening validation; cross-runtime comparison remains deferred.

Touched areas:

- eval profiles and reports
- sanitized retained runtime traces
- `docs/e2e/` or `docs/analysis/` comparison evidence

Dependencies: `W43-E5-S1`; Codex credentials and the pinned live environment are external
prerequisites and must be reported as explicit blockers when unavailable.

Local tasks:

- `W43-E5-S2-T1` (done) Define the Codex stability profile and metrics.
  - Scope: pin the representative work item, stage boundaries, prompt/runtime configuration,
    repetition count, initial-pass rate, first-repair recovery, exhaustion, findings per root
    cause, false budget consumption, interview resume, tasklist compliance, extension success,
    and intervention rate.
  - Verification: eval-doctor and profile tests prove the same scenario and evidence schema apply
    to every Codex repetition without provider-specific branches in core.
  - Completion: PR #299 (merge `fa75f0e7`) added the pinned AIDD-LIVE-007 Codex profile, canonical
    nine-metric vocabulary, required/conditional evidence inventory, fail-closed repetition
    validation, fixture-backed tests, and the stability-lane handoff. Ruff, mypy, focused eval/
    CLI tests (11), docs/planning/scenario checks (75), and full CI passed. Live repetitions remain
    the separate `W43-E5-S2-T2` task; human, Claude, and cross-runtime lanes remain parked.
- `W43-E5-S2-T2` (done) Run and report three fresh Codex repetitions.
  - Scope: execute at least three fresh Codex runs against one pinned scenario/profile after the
    provider-free gate, classify first decisive failures, and retain sanitized comparable artifacts.
  - Verification: every repetition has install/readiness evidence, runtime logs, stage audits,
    task-aware checkpoints, target verification, and per-metric verdicts; the aggregate report
    distinguishes stability, regression, and blocked-provider outcomes.
  - Completion: PR #301 (merge `3f4cf00e`) retained three fresh Codex run bundles and a
    profile-validated repetition fixture. All three repetitions are explicitly `infra-fail`: the
    first hit runaway repository-snapshot serialization during `implement`, and the next two
    produced no first Codex runtime event in `research`. Focused repetition/profile tests (11),
    eval/docs/planning checks (191), Ruff, mypy, full CI, adapter conformance, deterministic
    scenarios, packaged UI browser, and build passed. The aggregate result is indeterminate and
    does not claim Codex stability; human usability, Claude, cross-runtime, and Wave 36 lanes
    remain parked.
- `W43-E5-S2-T3` (parked) Run a future cross-runtime lower-capability comparison.
  - Scope: preserve the original lower-capability comparison objective for a later provider lane
    without changing Codex-only alpha acceptance or core/provider boundaries.
  - Verification: a future report compares the same profile across maintained and lower-capability
    runtimes and retains explicit environment-blocked verdicts when prerequisites are absent.

Wave 43 reconciliation notes:

- `2026-08-22` `W43-E5-S2-T2` is complete in PR #301 (merge `3f4cf00e`). Three fresh Codex
  repetitions were executed against the pinned AIDD-LIVE-007 profile and retained with install,
  runtime, stage-audit, checkpoint, verification, and verdict evidence. The runs are all
  `infra-fail` (one runaway snapshot serialization and two no-first-runtime-event stalls), so
  no stability or regression claim is made. The Codex-only lane is evidence-blocked pending a
  repeatable Codex service/harness environment; human usability, Claude, cross-runtime, and Wave
  36 work remain parked.

- `2026-08-22` `W43-E5-S2-T1` is complete in PR #299 (merge `fa75f0e7`). The Codex-only stability
  lane now has a pinned AIDD-LIVE-007 profile, native runtime/config identity, canonical nine
  metrics, required/conditional evidence inventory, and fail-closed repetition schema checks.
  Focused profile/eval-doctor tests, docs/planning/scenario checks, Ruff, mypy, and full CI passed.
  `W43-E5-S2-T2` is now the only dependency-ready task; human usability, Claude, cross-runtime,
  and Wave 36 work remain parked.

- `2026-08-22` `W43-E5-S1-T2` is complete in PR #297 (merge `69e3f214`). The provider-free
  repair-extension lane now covers successful and repeated-failure grants, manual-fix
  prevalidation, stale evidence, downstream-success and second-grant guards, Request Change
  separation, and immutable history. Every scenario retains exact grant hashes, attempt modes,
  automatic/manual accounting, report lineage, raw evidence, and no-loop assertions; fail-closed
  terminal reasons are checked explicitly. `W43-E5-S2-T1` is now the next dependency-ready task.
  Human usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-22` `W43-E5-S1-T1` is complete in PR #295 (merge `17dfbdae`). The provider-free
  resilience suite now covers missing/contradictory ownership drafts, service placeholders,
  malformed and safe interview candidates, safe tasklist presentation, eleven-card and single-
  card malformed tasklists, root/related finding retention, and non-repair resume accounting.
  Every result retains terminal state, attempt modes, repair budget, canonical/workflow records,
  located findings, and raw evidence; semantic omissions fail closed. `W43-E5-S1-T2` is now the
  next dependency-ready task. Human usability, Claude, cross-runtime, and Wave 36 work remain
  parked.

- `2026-08-21` `W43-E1-S4-T1` is complete in PR #257 (merge `6b87d863`). Maintained generic CLI,
  Qwen, and OpenCode adapters now settle only on substantive runtime-authored content; canonical
  stage-result, validator-report, repair-brief, interview, and answer records cannot end a process
  early. Raw runtime output remains retained, and adapter success still enters the existing
  canonical validation path. `W43-E2-S1-T1` is now Next and `W43-E2-S1-T2` is Soon; human
  usability, Claude, cross-runtime, and Wave 36 work remain parked.

- `2026-08-21` `W43-E1-S3-T3` is complete in PR #255 (merge `83e3a7ce`). Runtime completion
  and operator intervention now accept only substantive runtime-owned documents; AIDD-owned
  stage-result, validator-report, repair-brief, stage-brief, and publication records cannot be
  overwritten through those paths. Unexpected runtime drafts are retained under attempt evidence,
  indexed with stable keys, and shown as runtime evidence, while canonical records are published
  exactly once. Focused ownership/stage-runner/intervention/frontend tests (209), docs/planning
  tests (50), Ruff, mypy, full CI, deterministic scenarios, packaged UI browser, and build passed.
  `W43-E1-S4-T1` is now Next; human usability, Claude, cross-runtime, and Wave 36 work remain
  deferred.

- `2026-08-21` `W43-E1-S3-T2` is complete in PR #253 (merge `e2899537`). AIDD now renders
  stage-result records from canonical lifecycle state instead of trusting runtime drafts, with
  stable attempt history, explicit validator/blocker/next-action fields, exhausted-budget and
  resumed-state coverage, and durable project-set evidence. The exact `Terminal state notes: TODO`
  regression is removed and repeated reconciliation is byte-stable. Focused stage-terminal,
  repair, stage-runner, operator diagnostics, and deterministic project-set tests, Ruff, mypy,
  full CI, packaged UI browser, and build passed. `W43-E1-S3-T3` is now Next; human usability,
  Claude, cross-runtime, and Wave 36 work remain deferred.

- `2026-08-21` `W43-E1-S3-T1` is complete in PR #250 (merge `f198cb8b`). Runtime completion and
  discovery now use substantive stage documents only; canonical validator reports are rendered
  from the current structural, semantic, and cross-document findings. Missing or contradictory
  runtime validator drafts cannot affect the verdict, while an unexpected draft is retained as
  `runtime-validator-report.md` in attempt evidence and the artifact index. Focused core,
  validator, adapter-handshake, CLI, docs/planning tests (254), Ruff, mypy, full CI, packaged UI
  browser, and build passed. `W43-E1-S3-T2` is now Next and `W43-E1-S3-T3` is Soon. Human
  usability, Claude, cross-runtime, and Wave 36 work remain deferred.

- `2026-08-21` `W43-E1-S2-T2` is complete in PR #248 (merge `4db5613e`). Stage briefs now
  distinguish runtime write targets, AIDD-generated records, interview/control documents, and the
  published compatibility view; all eight run prompts prohibit runtime authoring of canonical
  terminal records. Focused ownership/prompt/stage-runner tests (167), docs/planning tests (50),
  Ruff, mypy, full CI, packaged UI browser, and build passed. `W43-E1-S3-T1` is now the next
  dependency-ready task and `W43-E1-S3-T2` is its direct successor in Soon. Human usability,
  Claude, cross-runtime, and Wave 36 work remain deferred.

- `2026-08-21` `W43-E1-S2-T1` is complete in PR #246 (merge `f9f74bf6`). Runtime-authored,
  AIDD-generated, interview/control, and published output projections are now typed and tested
  across all eight stages; terminal `stage-result.md` and `validator-report.md` are excluded from
  runtime targets while existing callers retain the complete published view. `W43-E1-S2-T2` is
  now the next dependency-ready task. Human usability, Claude, cross-runtime, and Wave 36 work
  remain deferred.

- `2026-08-21` `W43-E1-S1-T2` is complete in PR #244 (merge `a4d777c4`). The canonical ownership
  matrix covers every stage-declared document exactly once, separates runtime content from AIDD
  workflow/control/interview/raw-evidence records, and names mutation and UI-authoring boundaries.
  Coverage tests reject missing or conflicting rows; `W43-E1-S2-T1` is now the next dependency-ready
  task. Human usability, Claude, cross-runtime, and Wave 36 acceptance remain deferred.

Wave 43 exit evidence:

- every stage document has one enforced owner and maintained adapters wait only for runtime
  content;
- AIDD writes canonical validator and stage-result records, so service placeholders cannot spend
  repair budget;
- question/answer ledgers survive blocked resume and rejected candidates without operator-answer
  loss;
- resume and repair-extension attempts are distinct from automatic repairs in retained history;
- safe Markdown variants are accepted only when all required meaning is present;
- one malformed task grammar produces one actionable root cause rather than a wall of cascade
  findings;
- every fail-causing finding is a required repair correction, while advisory evidence does not
  force progression failure;
- one operator-authorized repair extension is auditable, revalidates first, never resets budget,
  never loops automatically, and is blocked after succeeded downstream work;
- provider-free scenarios pass before Codex repetition evidence, and Codex stability artifacts are
  retained; cross-runtime evidence is explicitly deferred to `W43-E5-S2-T3`.

## Wave 44 — Operator UI convergence (`done`)

Goal: iteratively bring the current Operator UI into conformance with the normative target
experience by fixing evidence-backed hierarchy, action, responsive, and accessibility gaps while
preserving workflow semantics, routes, API shapes, and durable evidence.

Reference authority:

1. [Target Operator Experience](../architecture/operator-frontend-target-ux.md) for the shell,
   vocabulary, action hierarchy, and responsive expectations;
2. [Main User Stories](../product/user-stories.md) for operator outcomes and runtime visibility;
3. provider-free browser fixtures and fresh rendered audits for observed behavior.

### Epic W44-E1 — action hierarchy and responsive shell (`done`)

Goal: make every visible primary action truthful for its current surface before broader visual
polish and shell composition work.

#### Slice W44-E1-S1 — contextual launch and primary-action policy (`planned`)

Primary output: one shared frontend visibility policy that keeps Runner and launch actions only on
launch surfaces, hides them from Inbox, create, history, generated-document, and Flow Complete
surfaces, and prevents duplicate competing primary actions.

Touched areas:

- `src/aidd/cli/static/operator-next-flow-actions.js`
- `src/aidd/cli/static/operator-next-flow-view.js`
- `src/aidd/cli/static/operator-shell-rendering.js`
- `browser_tests/`
- `tests/cli/`

Dependencies: existing Wave 42 Runner readiness and contextual action projections.

Local tasks:

- `W44-E1-S1-T1` (done) Enforce contextual launch-action visibility across Operator UI surfaces.
  - PR #318 (merge `0645856b`) now applies one shared surface policy to Runner and global launch
    controls, keeps terminal handoff recommendations read-only, and puts the mobile work-overview
    decision before the long stage strip. Provider-free browser coverage verifies Inbox, History,
    generated Documents, Flow Complete, and mobile first-viewport behavior without changing
    mutation routes or core eligibility.
  - Scope: centralize surface classification so Inbox/create, History/Runs, generated Markdown,
    and immutable Flow Complete never render a Runner selector or global workflow launch action;
    launch-capable workflow, stage, task, repair, and remediation surfaces retain exactly one
    contextual Runner and one primary launch action. Preserve existing mutation paths and route
    compatibility.
  - Verification: provider-free browser fixtures assert no Runner/global launch controls on
    read-only and create surfaces, no duplicate primary action on Flow Complete, and exactly one
    contextual Runner plus primary action on representative launch surfaces; console and overflow
    diagnostics remain clean.
- `W44-E1-S1-T2` (done) Recompose mobile Decision and recovery surfaces for first-viewport action
  visibility.
  - Scope: keep the decision summary, consequence, and one primary action in a single responsive
    composition for question, validation, runtime, and remediation states without changing core
    eligibility or recovery semantics.
  - Verification: mobile provider-free journeys at `320x568` and `390x844` prove the first action
    is visible, focusable, and not clipped or displaced below the initial viewport. PR #320 (merge
    `9792d8f5`) keeps the existing primary control in a safe-area-aware mobile action dock and
    reserves content space without adding a duplicate action or changing mutation semantics.

#### Slice W44-E1-S2 — target shell composition and visual hierarchy (`planned`)

Primary output: a responsive project/Work Item rail, tabs, grouped stage strip, central work
surface, contextual inspector, and collapsible live-output tray matching the target composition.

Dependencies: `W44-E1-S1`; existing Work Item tabs, stage navigation, Task Workspace, Documents,
and active-attempt read models.

Local tasks:

- `W44-E1-S2-T1` (done) Align the desktop shell with the target rail, tabs, stage strip, and
  central working surface.
  - PR #322 (merge `e3559b97`) adds the desktop navy project rail, Work Item context/tabs,
    stage-strip composition, central canvas, and contextual decision column while preserving
    existing navigation controls, routes, DOM ids, and mutation services. Read-only/completion
    surfaces reclaim the inspector column when it is empty so action cards retain usable hit
    targets.
  - Verification: provider-free desktop shell and Flow Complete geometry/hit-target coverage,
    focused Inbox and terminal journeys, Ruff, mypy, full Python matrix, frontend checks,
    deterministic scenarios, adapter conformance, packaged UI browser, security checks, and build
    all passed.
- `W44-E1-S2-T2` (done) Keep Documents and active-attempt evidence co-visible with the
  contextual inspector and live-output tray.
  - PR #324 (merge `69ce00df`) adds the target desktop composition for Documents and Tasks:
    Work Item context and the eight-stage strip remain present on Documents, the document
    navigator/reader/evidence inspector share one row, and selected task detail sits beside the
    authoritative task list with the attempt evidence tray spanning the workbench below. Existing
    routes, DOM ids, read models, and mutation services are unchanged.
  - Verification: provider-free Documents and active-attempt geometry/diagnostic coverage at
    `1280x900` and `1440x900`, focused shell/document/implementation journeys, frontend document
    and studio tests, UI asset contracts, docs/planning, Ruff, mypy, full Python matrix,
    deterministic scenarios, adapter conformance, packaged UI browser, security checks, and build
    all passed.
- `W44-E1-S2-T3` (done) Reconcile stage-strip density, typography, tokens, and overflow across
  desktop and mobile viewports.
  - PR #326 (merge `4e50e093`) keeps the canonical eight-stage strip readable on desktop and
    tablet, collapses the mobile strip behind a keyboard-accessible current-stage summary, and
    preserves the Work Item context and stage navigation when Task Workspace data is unavailable.
    The dashboard now exposes an existing canonical `tasklist.md` even before its stage attempt is
    selected, so the UI can distinguish a real published tasklist from a missing prerequisite
    without generating a failed request.
  - Verification: focused stage-strip browser checks across `320x568`, `390x844`, `768x1024`,
    `1280x900`, and `1440x900`; selected Documents/Tasks, mobile navigation, and route journeys;
    frontend Node suite (`135 passed`); full Python suite (`2430 passed`); docs/planning checks,
    Ruff, mypy, deterministic scenarios, adapter conformance, packaged UI browser, security
    checks, and build all passed. `W44-E1-S3-T1` is now the next dependency-ready task.

#### Slice W44-E1-S3 — rendered acceptance loop (`done`)

Primary output: a repeatable visual regression loop that captures target surfaces, checks hierarchy
and states, and records the next bounded UI task until the target contract is satisfied.

Dependencies: `W44-E1-S1` and `W44-E1-S2`.

Local tasks:

- `W44-E1-S3-T1` (done) Add initial-viewport, focus-order, console, and overflow assertions to
  the provider-free browser matrix.
  - PR #328 (merge `21c71156`) makes initial-viewport requirements explicit for launch, recovery,
    and completion journeys while retaining controlled scrolling for long Task and Markdown
    surfaces. The provider-free matrix continues to assert accessible focus order, diagnostics,
    duplicate-primary protection, rendered geometry, and horizontal overflow across
    `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`. It also fixes the mobile recovery
    action dock so a late workspace `width: 100%` rule cannot clip its fixed action at the
    `320px` boundary; routes, APIs, and mutation semantics are unchanged.
  - Verification: provider-free matrix (`9 passed`), geometry/accessibility/stage checks (`14
    passed`), UI contract/mobile checks (`68 passed`), frontend Node suite (`135 passed`),
    docs/planning (`50 passed`), Ruff, mypy, full Python suite (`2430 passed`), deterministic
    scenarios, adapter conformance, packaged UI browser (`14m27s`), security checks, and build
    all passed. `W44-E1-S3-T2` is now the next dependency-ready task.
- `W44-E1-S3-T2` (done) Produce a reconciled target-UX audit and split confirmed visual gaps into
  bounded follow-up tasks. The audit is retained in
  `docs/e2e/w44-e1-s3-t2-target-ux-audit.md`; technical browser checks remain green, but visual
  convergence stays open because the target shell, task-ready composition, decision surfaces,
  legacy create/history/completion compositions, and visual tokens still diverge.
  - Verification: fresh provider-free Playwright screenshots for all 13 target surfaces at
    `1280x900` plus Mobile Decision at `390x844`; route, console, failed-request, blocked-request,
    and viewport-width diagnostics clean. Screenshot evidence is retained locally under
    `/tmp/w44-audit-v1/`.
- `W44-E1-S3-T3` (done) Render the persistent target Project/Work Item rail and context shell on
  every Work Item surface. Reuse existing route intents, Work Item ids, core-owned Inbox data,
  tabs, and stage projections; add only frontend shell markup and styling. The rail exposes
  project identity, Work Item search/list, selected item, and the current Work Item id/title/stage
  on recovery, history, completion, and mobile decision surfaces. Desktop renders the persistent
  navy rail; mobile keeps the central Inbox route visible without a hidden duplicate route target.
  - PR #332 (merge `c7992051`) renders the project identity, deterministic Work Item list,
    selected state, canonical route-intent attributes, and accessible search filter. Shared shell
    synchronization now restores the Work Item identity and eight-stage strip on recovery, history,
    and terminal surfaces; Work Item context explicitly includes the durable id. Existing setup,
    mobile, route, API, and mutation semantics remain unchanged.
  - Verification: focused desktop rail and mobile guided-setup browser checks, active-studio and
    Inbox journeys, five-viewport provider-free browser matrix, frontend Node suite (`135 passed`),
    UI asset/composite/full UI plus docs/planning checks (`220 passed`), packaged JavaScript check,
    Ruff, mypy, deterministic scenarios, adapter conformance, packaged UI browser, security checks,
    and build all passed. `W44-E1-S3-T4` is now the next dependency-ready task.
- `W44-E1-S3-T4` (done) Render the target Ready-task Task Workspace composition using the
  authoritative task ledger. The provider-free Ready fixture now retains a selected TL-2 task,
  dependency rows, core readiness, one Run action, and the factual attempt tray without changing
  task status or eligibility ownership. PR #334 (merge `df6b3f56`) adds the target table
  composition, selected-task route/reload coverage, mobile layout, and provider-free matrix
  coverage. Verification: focused Ready-task browser checks (`2 passed`), task-run matrix,
  existing task/stage/action/accessibility/geometry checks, frontend Node suite (`135 passed`),
  docs/planning (`50 passed`), Ruff, mypy, packaged JavaScript, deterministic scenarios, adapter
  conformance, packaged UI browser, security, and build all passed.
- `W44-E1-S3-T5` (done) Render target Decision, Validation Repair, Review/QA Remediation, and
  Mobile Decision content above the shared recovery chrome. Preserve the actual question/finding,
  evidence, consequence, resolution state, Write/Preview/destination, and one primary action in
  the initial readable viewport. Verification: question, validation, remediation, and mobile
  provider-free journeys with focus, action visibility, and reconnect/disabled-state checks. PR
  #336 (merge `e088c50f`) promotes explicit recovery deep links to the authoritative question,
  validation, and Review finding surfaces, moves question content and durable destination ahead of
  generic decision chrome, and switches the remediation parity fixture to rejected Review evidence.
  Verification: focused Decision/Validation/Review browser checks on desktop/mobile (`4 passed`),
  Review/QA journey (`3 passed`), frontend Node suite (`135 passed`), provider-free/docs/planning/UI
  contracts (`104 passed`), Ruff, mypy, packaged JavaScript, deterministic scenarios, adapter
  conformance, packaged UI browser, security, and build all passed.
- `W44-E1-S3-T6` (done) Replace legacy Create Work Item, Runs/Attempts, and Flow Complete
  compositions with target task-centered layouts while retaining their existing routes, ids,
  history, lineage, and immutable handoff semantics. PR #338 (merge `99da14c9`) adds the target
  create editor/preview, selected-attempt history inspector, and Flow Complete handoff/evidence/
  completion compositions without changing mutation paths. Verification: create/history/completion
  rendered fixtures at desktop/mobile, route and reload compatibility, frontend/UI contracts,
  Ruff, mypy, deterministic, packaged-browser, security, and build checks passed in CI.
- `W44-E1-S3-T9` (done) Align the provider-free browser matrix with the authoritative decision and
  recovery surface selectors after the recovery content composition changed. PR #340 (merge
  `c90ede66`) replaces stale `.recovery-workbench` selectors with the current question,
  validation, and Review surface contracts and adds a registry guard against selector drift.
  Focused authoritative-surface and matrix-contract checks passed; the existing first-action,
  focus, diagnostics, and five-viewport assertions remain intact for the follow-up layout work.
- `W44-E1-S3-T10` (done) Recompose Validation Repair for first-viewport action visibility and
  responsive containment. PR #342 (merge `eeeb1f33`) moves the recovery action band ahead of the
  long validation evidence, makes its grid children shrink-safe, and stacks the action, Runner,
  and extension preview without fixed-width overflow. The finding, repair budget, readiness
  projection, and existing mutation paths remain unchanged. Verification: focused five-viewport
  Validation Repair geometry/accessibility test (`5 passed`), combined recovery/browser checks
  (`18 passed`), frontend suite (`135 passed`), UI contracts (`66 passed`), Ruff, mypy, and clean
  diff check; packaged UI browser CI also passed.
- `W44-E1-S3-T11` (done) Recompose the Question Decision surface so its authoritative answer action
  remains visible and focusable in the initial viewport while preserving the question evidence,
  durable draft, resolution state, and single primary-action contract. PR #344 (merge `f693db74`)
  adds a bounded desktop/tablet action dock that reuses the existing answer control; mobile behavior
  remains unchanged. Verification: one provider-free question-recovery regression over all five
  viewports (`1 passed`), selected durable-answer recovery, frontend suite (`135 passed`), UI
  contracts (`66 passed`), Ruff, mypy, and packaged UI browser CI.
- `W44-E1-S3-T12` (done) Align the Review-remediation browser journey with the authoritative Review
  quality-gate surface and its first-action contract instead of the generic recovery route. PR #346
  (merge `f1f51178`) switches the provider-free matrix to the rejected Review fixture and keeps the
  existing remediation launch control visible in a bounded action dock across all five viewports.
  Rejected-finding evidence, durable remediation launch semantics, and the one-primary-action
  contract remain unchanged. Verification: focused Review matrix (`1 passed` across five viewports),
  authoritative recovery and Review/QA journeys (`7 passed`), UI contracts (`59 passed`), frontend
  Node suite (`135 passed`), Ruff, mypy, packaged JavaScript, full CI, and build all passed.
- `W44-E1-S3-T13` (done) Recompose Flow Complete so the core-recommended outcome action is fully
  visible and focusable in the initial `320x568` viewport while preserving immutable handoff evidence,
  lineage overlays, and one primary-action semantics. PR #348 (merge `3193e39e`) extends the existing
  mobile single-primary action dock to the immutable Flow Complete handoff, keeping the core-recommended
  outcome action visible without changing lineage or mutation semantics. Verification: completion journey,
  full five-viewport provider-free matrix (`9 passed`), terminal journeys (`12 passed`), UI contracts
  (`59 passed`), frontend suite (`135 passed`), Ruff, mypy, packaged JavaScript, deterministic,
  adapter, build, and packaged UI browser CI all passed.
- `W44-E1-S3-T7` (done) Align shared Operator UI tokens and component density with the target
  visual language: warm canvas, deep navy rail, cobalt primary, mint success, amber warning,
  and at least 14px primary desktop reading text. PR #350 (merge `d486e9ae`) updates the shared
  semantic token layer and keeps legacy selector aliases/API behavior intact. Verification: target
  token contract, UI/readability/asset/semantic/density checks (`65 passed`), frontend Node suite
  (`135 passed`), full five-viewport provider-free matrix (`9 passed`), Ruff, mypy, packaged
  JavaScript, deterministic, adapter, build, and packaged UI browser CI all passed.
- `W44-E1-S3-T8` (done) Record a fresh rendered 13-surface parity audit and decompose any
  evidence-backed visual gaps into bounded follow-up tasks. PR #352 (merge `e1d77b01`) retains
  `docs/e2e/w44-e1-s3-t8-rendered-convergence-audit.md`. The provider-free matrix remains clean
  across all five viewports with no console errors, horizontal overflow, duplicate primary actions,
  or focus loss; the audit intentionally keeps Wave 44 open because Project Work selection/inspector,
  Active Task evidence, Markdown first-viewport reading, and Validation Repair hierarchy still diverge
  from the target composition.
- `W44-E1-S3-T14` (done) Render the target Project Work selected Work Item inspector and compact
  filter/table composition from the existing core-owned Inbox projection. PR #354 (merge `b3622bde`)
  makes Inbox rows selectable by click and keyboard, preserves selection in a bounded
  `inbox_work_item` deep-link, adds a server-owned filter/table composition, and keeps grouping,
  ordering, status, and mutation eligibility outside the browser. Verification: Inbox journey (`11
  passed`), selection/deep-link/reload journey (`1 passed`), full five-viewport matrix (`9 passed`),
  frontend Node suite (`135 passed`), UI contracts, Ruff, mypy, packaged JavaScript, full CI, and build.
- `W44-E1-S3-T15` (done) Render the target Active Task first-viewport attempt composition and
  live-output tray from the existing task-attempt evidence. PR #356 (merge `2e77fac5`) promotes the
  selected attempt into a first-viewport tray with factual identity, elapsed and output-age values,
  durable milestone, connection/reconnect cursor, one `Open live output` primary, guarded cancellation,
  and collapsible bounded raw output. Existing task actions, routes, API shapes, and mutation semantics
  remain unchanged. Verification: provider-free running/waiting/cancelling/failed/completed and
  offline/reconnecting states across desktop/mobile (`14` focused checks plus a final targeted rerun),
  frontend/UI contracts, Ruff, mypy, full Python/packaged-browser/adapter/deterministic/build CI.
- `W44-E1-S3-T16` (done) Recompose the Markdown Workspace so the selected read-only document,
  heading map, provenance, freshness, and finding anchors share the first viewport with the navigator.
  PR #358 (merge `f543ae51`) adds a compact read-only brief, co-locates the Markdown body and visible
  heading map, preserves Source/Compare/line-heading anchors and freshness semantics, and keeps
  generated documents read-only with existing routes/API shapes unchanged. Mobile heading-map links
  retain touch-sized targets; Compare stays explicitly disabled when no earlier retained attempt exists.
  Verification: current/stale/missing document fixtures, source/compare/anchor navigation, reload,
  focus, long-Markdown overflow, five-viewport geometry/accessibility checks, frontend suite, UI asset
  contracts, readability, docs/planning, Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed.
- `W44-E1-S3-T17` (done) Recompose Validation Repair into a responsive finding-to-action hierarchy
  that keeps the finding, literal repair consequence, readable Runner readiness, and one primary repair
  action ahead of long evidence. Preserve validation/readiness projections and mutation semantics. PR
  #360 (merge `a678418a`) adds the explicit repair consequence, keeps the finding and readable Runner
  readiness ahead of long extension evidence, and preserves the existing mutation selectors and
  readiness semantics. Verification: five-viewport validation fixtures, action visibility/focus,
  readable Runner state, evidence overflow, disabled/stale states, duplicate-primary protection,
  frontend/UI contracts, Ruff, mypy, and full CI including packaged UI browser passed.
- `W44-E1-S3-T18` (done) Correct the remaining eight-stage strip label clipping at the target desktop
  density, preserving stage order, active/current semantics, keyboard access, and the truthful mobile
  disclosure. PR #362 (merge `4e36bc6f`) adds a compact-width responsive override that reclaims inline
  space without changing the stage DOM, phase grouping, route semantics, or mobile disclosure. Verification:
  five-viewport stage-strip geometry/accessibility checks, no clipped labels or horizontal overflow,
  stable deep links/reload, frontend/UI contracts, Ruff, mypy, and full CI including packaged UI browser.
- `W44-E1-S3-T19` (done) Run a fresh rendered Wave 44 exit audit across all 13 target surfaces and
  reconcile the default task-centered routing decision. The audit is retained in
  `docs/e2e/w44-e1-s3-t19-rendered-exit-audit.md`. Provider-free browser and legacy-composition
  checks remain green, but the target shell and several first-viewport compositions still diverge;
  the audit therefore decomposes the next bounded UI tasks instead of claiming Wave 44 exit.
  - Verification: provider-free matrix (`9 passed`), target legacy compositions (`5 passed`), fresh
    desktop/mobile screenshots, target-asset comparison, responsive/accessibility review, and clean
    console/request/overflow diagnostics in the authoritative browser lanes.
- `W44-E1-S3-T20` (done) Recompose the selected Project Work view into a non-overlapping target
  table/list and right-side Work Item inspector. PR #366 (merge `82fb1d23`) constrains the
  server-owned list grid, compacts the table rows, and keeps the inspector in a separate desktop
  column or normal mobile flow without changing grouping, ordering, selection routes, or action
  services. Verification: selected Inbox fixture at `1280x900`, `1440x900`, `768x1024`, and
  mobile, geometry/accessibility, deep-link/reload, action-count, diagnostics, legacy/action
  browser checks (`14 passed`), frontend (`136 passed`), UI/docs/planning (`103 passed`), Ruff,
  mypy, and full CI including packaged UI browser.
- `W44-E1-S3-T21` (done) Recompose Work Item Overview/Launch so the contextual Runner readiness
  inspector and one launch action occupy the target hierarchy while the eight-stage strip remains
  readable at compact desktop widths. PR #368 (merge `2d450192`) adds a truthful request brief and
  launch scope, one contextual Runner readiness inspector, one primary launch action, and compact
  desktop/mobile geometry coverage while preserving runtime selection, readiness revalidation,
  route state, and no-Runner behavior on create/read-only surfaces. Verification: four-viewport
  launch composition, stage/action/legacy browser suites, frontend (`136`), UI asset contracts,
  docs/planning, Ruff, mypy, deterministic, adapter, build, security, and packaged UI browser CI.
- `W44-E1-S3-T22` (done) Recompose Tasks and Active Task into the target table/right-inspector/
  live-output hierarchy. PR #370 (merge `6e7b5c88`) moves the selected attempt into the right
  inspector, separates raw output into a full-width lower tray, keeps task groups/actions and
  factual attempt/reconnect/cancel state core-owned, and tightens table/inspector density without
  changing routes, ids, or mutation services. Verification: ready/running/waiting/cancelling/
  failed/completed task fixtures across desktop/mobile, target task/active-attempt geometry,
  accessibility and diagnostics (`34 passed`), frontend (`136 passed`), UI asset contracts,
  docs/planning, Ruff, mypy, deterministic, adapter, packaged UI browser, security, and build CI.
- `W44-E1-S3-T23` (done) Recompose Decision, Validation Repair, and Mobile Decision recovery
  content so rationale, evidence, resolution/consequence, destination, and the single contextual
  action retain the target hierarchy across desktop and mobile states. PR #372 (merge `a733341c`)
  now leads questions with decision context, rationale, retained evidence, answer/resolution controls,
  durable destination, and impact; Validation Repair now leads with a read-only document navigator,
  reader canvas, finding inspector, and one repair action. Mobile states keep the first decision or
  repair action visible without horizontal overflow. Focused decision/recovery browser checks (`4`),
  frontend (`28`), UI contracts, Ruff, mypy, deterministic, adapter, security, packaged UI browser,
  and build CI passed.
- `W44-E1-S3-T24` (done) Align Runs and Attempts with the target chronology, selected-attempt
  inspector, lineage, retained evidence, and read-only action hierarchy. PR #374 (merge
  `a85a9d03`) adds the compact Runs list, truthful attempt/view tabs, vertical chronology,
  selected-attempt evidence/lineage inspector, retained comparison action, and responsive
  desktop/mobile composition without changing history routes, selectors, lineage, archive, or
  read-only semantics. Verification: focused target/history browser suites (`16 passed`), frontend
  state/route tests (`41 passed`), five-viewport provider-free interaction/geometry/accessibility
  matrix, clean diagnostics with no horizontal overflow, CSS token contracts, planning integrity,
  Ruff, mypy, and full CI including packaged UI browser.
- `W44-E1-S3-T25` (done) Align Flow Complete with the target immutable handoff, evidence,
  completion inspector, and recommended-next-outcome composition without changing lineage semantics.
  PR #376 (merge `a8f15319`) now renders the target status hero, central handoff summary and final
  documents/evidence, plus a right-side Completion inspector with fresh-QA status, retained evidence,
  run IDs, the core recommendation, one primary outcome action, and disclosed secondary actions. The
  source run remains immutable and existing handoff/history routes, ids, lineage, and mutation
  semantics are preserved. Verification: focused frontend and Flow Complete/browser suites, five-
  viewport geometry/accessibility/diagnostic checks, UI contracts, planning integrity, Ruff, mypy,
  deterministic scenarios, adapter conformance, security, packaged UI browser, and build CI passed.
- `W44-E1-S3-T26` (done) Align Create Work Item with the target editor/preview shell, draft
  status, context sections, and one create action while preserving operator-authored Markdown rules.
  PR #378 (merge `9b97e908`) adds the target editor/preview composition, durable context and
  constraints preview, draft status, responsive action footer, and exactly one primary create action.
  Existing request persistence, Work Item ids, routes, runtime-independent creation, launch-time
  Runner selection, and operator-authored Markdown boundaries remain unchanged. The provider-free
  first-time journey now tolerates direct authoritative question recovery and avoids an unreliable
  `networkidle` boundary while the fixture is polling.
  - Verification: target Create Work Item browser checks across `1280x900`, `768x1024`, and
    `390x844`; guided setup and first-time recovery journey; frontend Node suite (`136 passed`),
    UI asset/accessibility/design-token contracts, docs/planning checks, Ruff, mypy, full Python
    matrix, deterministic scenarios, adapter conformance, packaged UI browser, security checks,
    and build CI all passed.
- `W44-E1-S3-T27` (done) Align Implementation Review and Review/QA Remediation with the target
  repository-truth, finding-evidence, and remediation action hierarchy. PR #380 (merge `737365c5`)
  adds the repository-truth summary/diff workspace, compact implementation ledger, explicit Review
  gate, finding-evidence table, retained source evidence, durable Write/Preview remediation request,
  downstream impact, and one contextual primary action for Review and QA. Existing routes, selectors,
  ledger/evidence projections, mutation services, and compatibility markup remain unchanged.
  Verification: focused implementation/review browser journeys (`6 passed`), frontend Node suite
  (`136 passed`), UI asset/readability/accessibility/design-token contracts, docs/planning checks,
  Ruff, mypy, full CI including Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance,
  packaged UI browser, security, and build all passed.
- `W44-E1-S3-T28` (done) Align Markdown Workspace reader, navigator, provenance, heading map,
  and evidence inspector spacing with the target document composition while keeping generated
  documents read-only. PR #382 (merge `5828f53b`) adds a compact role-grouped navigator,
  bounded document brief, target-style context/provenance inspector, source/path actions, a
  truthful Request change/Return to task action hierarchy, and route-scoped reader geometry
  without changing generated-document immutability, routes, ids, evidence contracts, or mutation
  services. Verification: focused Markdown Workspace browser/layout checks, document evidence
  journeys, frontend Node suites, UI asset/readability/accessibility/design-token contracts,
  Ruff, mypy, full Python matrix, deterministic scenarios, adapter conformance, packaged UI
  browser, security, and build all passed.
- `W44-E1-S3-T29` (done) Run a fresh rendered audit of all 13 provider-free target surfaces
  against the canonical target compositions after T28, record viewport geometry, first-action
  visibility, accessibility/diagnostic findings, and split each confirmed implementation gap into
  a bounded successor task before coding. PR #384 (merge `b30de404`) retains
  `docs/e2e/w44-e1-s3-t29-rendered-exit-audit.md`. The focused W44 suites passed (`71`), while the
  fresh responsive matrix recorded `6` passes and two first-viewport contract failures: launch at
  `320x568` and Flow Complete at `768x1024`. The audit also records target-density gaps in Project
  Work, Active Task, Decision/Mobile Decision, Review, Remediation, History, Flow Complete, and the
  shared path breadcrumb. Existing routes, ids, projections, mutation services, and generated
  document immutability are unchanged. Verification: fresh provider-free captures, focused W44
  browser suites, docs consistency, planning integrity, and full CI passed.
- `W44-E1-S3-T30` (done) Keep the Work Item Launch primary action visible and focusable in the
  initial `320x568` viewport while preserving the core-owned Runner readiness projection, one
  contextual Runner, fail-closed eligibility, and existing launch mutation path. PR #386 (merge
  `7c58edda`) adds a narrow-phone action dock using the existing launch button and hides only the
  duplicated empty readiness helper below `360px`; the Runner reason, readiness projection, routes,
  ids, and mutation service are unchanged. The five-viewport launch composition suite and the
  provider-free `create-runner-launch` matrix pass with focus, one-primary-action, diagnostics, and
  overflow checks green; UI contracts, planning/docs checks, Ruff, mypy, and full CI also pass.
- `W44-E1-S3-T31` (done) Keep the core-recommended Flow Complete action visible and focusable in
  the initial `768x1024` viewport while retaining immutable handoff/evidence, fresh-QA gating,
  lineage overlays, and secondary outcomes. PR #388 (merge `f7ab7364`) lifts the existing primary
  action into the bounded safe-area-aware dock for supported tablet/desktop widths and extends the
  target composition coverage to `768x1024`; handoff/evidence remain in document flow and source-run
  immutability, recommendation truth, and one-primary semantics are unchanged. Verification: five-
  viewport completion matrix, target legacy composition/mobile focus checks, UI contracts, docs/
  planning consistency, Ruff, mypy, full CI, packaged UI browser, deterministic, adapter, security,
  and build checks passed.
- `W44-E1-S3-T32` (done) Recompose Task Workspace and Active Task so the selected attempt
  inspector, factual attempt controls, task groups, and live-output tray share the target first
  viewport without changing task-ledger ownership or mutation services. PR #390 (merge `4fc916a7`)
  docks live output to a safe-area-aware desktop tray, bounds the task list and selected-task
  inspector for the first viewport, and removes nested shell scrolling while preserving core-owned
  ledger/status/eligibility, existing routes, ids, and mutation services. Verification: ready,
  running, waiting, cancelling, failed, and completed fixtures across desktop/mobile with tray
  visibility, reconnect/cancel semantics, one primary action, clean diagnostics, and no horizontal
  overflow; docs/planning checks, Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed.
- `W44-E1-S3-T33` (done) Recompose Decision and Mobile Decision so the decision context, evidence,
  resolution choices, durable destination, and one primary action remain in the target first-viewport
  hierarchy. PR #392 (merge `99ce2bca`) keeps question and approval context/evidence, resolution,
  editor/destination state, and one real primary action in the target first viewport across the five
  supported viewports. Question evidence opens when retained snippets exist; approval queues keep
  Allow once primary and other decisions secondary without changing routes, ids, mutation paths, or
  fail-closed recovery. Verification: focused browser/UI matrix (`20 passed`), UI asset contracts
  (`53 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build
  checks passed.
- `W44-E1-S3-T34` (done) Align Project Work with the target compact grouped table and selected Work Item
  inspector, removing duplicated setup/search chrome while preserving core-owned membership, ordering,
  progress truth, selection deep links, and one contextual action. PR #394 (merge `901b6bd0`) adds explicit
  Work Item, Stage, Progress, Runner, Last event, and Status columns with server-projected progress bars,
  responsive row geometry, selected inspector bounds, and selected-view banner suppression. Guided Setup
  resume keeps its direct Continue existing Work Item action visible. Existing routes, ids, membership,
  ordering, action services, keyboard selection, and deep-link/reload semantics remain unchanged.
  Verification: target Project Work browser matrix (`4 passed`), Inbox selection/routing smoke (`4 passed`),
  frontend Inbox tests (`8 passed`), UI contracts (`58 passed`), docs/planning (`108 passed`), Ruff, mypy,
  full CI, deterministic, adapter, packaged-browser, security, and build checks passed.
- `W44-E1-S3-T35` (done) Align Implementation Review with the target full-width diff, claims,
  verification, and Review inspector composition while preserving repository-truth evidence,
  launch readiness, and the explicit Review gate. PR #396 (merge `66af77e9`) adds a compact
  claims/verification overview, retains the canonical task ledger, and composes the repository diff
  beside a distinct Review inspector with responsive one-column fallback. Existing routes, ids,
  repository-truth evidence, read-only stage documents, readiness, and one primary action remain intact.
  Verification: focused browser composition (`3 passed`), frontend tests (`36 passed`), UI contracts,
  docs/planning (`108 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security,
  and build checks passed.
- `W44-E1-S3-T36` (done) Align Review/QA Remediation with the target findings/source-evidence/
  durable request composition while preserving selection semantics, downstream staleness, Runner
  readiness, conflict handling, and one remediation action. PR #398 (merge `da87abd7`) keeps findings,
  source paths, retained evidence, durable request state, downstream impact, Runner readiness, and one
  remediation action in the target two-region composition with responsive fallback. Exact finding ids,
  selection semantics, draft destinations, conflict/staleness behavior, routes, and mutation services
  remain unchanged. Verification: focused browser review/QA (`6 passed`), frontend tests (`28 passed`),
  UI contracts (`58 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security,
  and build checks passed.
- `W44-E1-S3-T37` (done) Align Runs and Attempts with the target compact retained-run list,
  chronology, selected-attempt inspector, lineage, and read-only actions without changing history
  routes or comparison semantics. PR #400 (merge `6d9f8287`) tightens the retained-run list and
  chronology spacing to match the target three-region composition while preserving selected-attempt
  evidence, lineage, comparison eligibility, read-only actions, routes, selectors, and historical
  semantics. Verification: focused history browser checks (`12 passed`, plus `2 passed` after final
  CSS refinement), frontend tests (`36 passed`), UI contracts/docs/planning (`108 passed`), Ruff, mypy,
  full CI, deterministic, adapter, packaged-browser, security, and build checks.
- `W44-E1-S3-T38` (done) Replace absolute filesystem paths in shared operator breadcrumbs with
  truthful project, Work Item, and current-stage labels while preserving copy/path utilities where
  they are explicitly part of document provenance. PR #402 (merge `924138cc`) now renders a truthful
  project label, Work Item, and current-stage label in the shared shell without exposing the absolute
  filesystem path. Existing provenance/path utilities, route/deep-link behavior, DOM ids, and setup/
  launch semantics remain unchanged. Verification: focused breadcrumb browser checks (`2 passed`),
  frontend tests (`36 passed`), Guided Setup/packaged smoke (`2 passed`), UI contracts/docs/planning
  (`105 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build.
- `W44-E1-S3-T39` (done) Recompose Validation Repair into the target finding-to-repair hierarchy
  so the finding, literal consequence, source document, repair budget, Runner readiness, and one
  repair action remain visible before long evidence. PR #404 (merge `a759b2af`) makes the inspector
  single-column and readable, moves the finding ahead of the document on mobile, keeps the desktop
  Runner/action group reachable, and preserves generated-document immutability, readiness
  revalidation, routes, ids, and mutation services. Verification: validation-repair viewport checks
  (`10 passed`), validation recovery journey including exhausted repair (`11 passed`), target legacy
  compositions (`17 passed`), frontend (`36 passed`), UI contracts (`55 passed`), docs/planning
  (`50 passed`), Ruff, mypy, full Python/packaged-browser CI, deterministic, adapter, security, and
  build checks passed.
- `W44-E1-S3-T40` (done) Recompose the desktop Validation Repair action group so Runner, the primary
  repair action, Request change, and raw evidence remain inline with the finding inspector instead
  of obscuring the consequence, repair brief, or extension evidence. PR #406 (merge `40632549`)
  removes the desktop fixed overlay, keeps the action group in normal inspector flow, and preserves
  readiness revalidation, action services, generated-document immutability, and the mobile safe-area
  dock. The provider-free matrix now keeps initial-viewport coverage on mobile and scrolls only the
  desktop inline action into view for geometry checks. Verification: validation-repair viewport
  checks (`10 passed`), recovery journey (`11 passed`), target legacy compositions (`17 passed`),
  five-viewport matrix (`1 passed`), frontend (`136 passed`), UI contracts (`63 passed`),
  docs/planning (`50 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed.
- `W44-E1-S3-T41` (done) Compact the desktop Validation Repair surface's vertical rhythm so the
  inline Runner and primary repair action are visible in the supported `1280x900` and `1440x900`
  initial viewports without restoring a fixed overlay or obscuring consequence, exact repair brief,
  or extension evidence. Keep the existing routes, readiness and mutation services, generated
  document read-only boundary, and mobile first-viewport dock. Verification: fresh screenshots and
  geometry/accessibility assertions at `1280x900`, `1440x900`, `768x1024`, `390x844`, and `320x568`
  prove inline action visibility, no overlap, one primary action, clean diagnostics, and no
  horizontal overflow. PR #408 (merge `d7994130`) compacts the desktop validation context,
  stage strip, finding inspector, and repair controls using existing UI tokens; mobile safe-area
  behavior, routes, ids, readiness, mutation services, and generated-document immutability remain
  unchanged. Focused viewport (`10`), validation matrix, recovery/legacy compositions (`28`),
  frontend (`136`), UI contracts (`53`), docs/planning (`50`), Ruff, mypy, and full CI passed.
- `W44-E1-S3-T42` (done) Split the Work Item detail shell into the target primary navigation rail
  and secondary Work Items navigator while keeping the project Inbox shell compact. On detail
  surfaces, preserve the existing Work Item list, selection/deep-link routes, navigation ids,
  keyboard behavior, and mobile collapse semantics, but expose the target two-level desktop
  hierarchy: icon navigation rail plus project Work Items rail. On the Inbox surface, retain the
  single target project navigation rail and do not duplicate Work Item controls. Verification:
  fresh target comparisons and geometry/accessibility checks at `1280x900`, `1440x900`,
  `768x1024`, `390x844`, and `320x568` prove route-scoped rail composition, stable selection and
  reload/deep links, one visible navigation state, no horizontal overflow, and clean diagnostics.
  PR #410 (merge `3ef38644`) adds the 84px primary rail and 236px Work Items rail on detail
  surfaces, retains the single 244px Inbox rail, and keeps the mobile rail collapsed. Existing
  navigation ids, route/deep-link selection, Work Item list ordering, and mutation semantics are
  unchanged. Verification: focused shell/legacy/inbox browser checks (`35 passed`), provider-free
  matrix (`9 passed`), frontend (`136 passed`), UI contracts/docs/planning (`110 passed`), Ruff,
  mypy, and full CI including packaged UI browser passed.
- `W44-E1-S3-T43` (done) Collapse the generic desktop breadcrumb/status topbar on Work Item detail
  surfaces so the target Work Item header, tabs, and stage strip begin in the initial viewport
  without a duplicated 64px chrome layer. Preserve top-level Inbox/Create/History routing,
  launch-time Runner controls, existing status/runtime semantics, keyboard focus, routes, ids,
  and mobile topbar behavior. Verification: fresh target comparisons and geometry checks at
  `1280x900`, `1440x900`, `768x1024`, `390x844`, and `320x568` prove title/header first-viewport
  position, one truthful context row, stable deep links/reload, no horizontal overflow, and clean
  diagnostics. PR #412 (merge `831be726`) completed the desktop detail chrome collapse; the
  remaining internal context-header density gap is tracked as T44.
- `W44-E1-S3-T44` (done) Compact the remaining Work Item detail context header so the target title,
  tabs, and stage strip retain their first-viewport hierarchy after the generic desktop topbar is
  collapsed. Replace the stacked `Work Item Workspace` eyebrow, phase/status line, and duplicate
  identity rows with one dense but truthful context row; preserve Work Item id, current status,
  stage semantics, launch/recovery controls, keyboard focus, routes, ids, and mobile behavior.
  Verification: fresh target comparisons and geometry/accessibility checks at
  `1280x900`, `1440x900`, `768x1024`, `390x844`, and `320x568` prove the title/tabs/stage strip
  align with the target hierarchy, status and identity remain discoverable, no horizontal overflow
  or diagnostic errors occur, and existing deep links/reload semantics remain stable.
- `W44-E1-S3-T45` (done) Align the tablet Work Item detail shell at `768x1024` with the target
  hierarchy: keep a compact top-level chrome, place the truthful Work Item context before tabs and
  the canonical stage strip, and preserve the existing desktop two-rail composition and mobile
  navigation behavior. Do not change route/API semantics, Work Item ids, stage ordering, status
  ownership, or launch/recovery controls. PR #416 (merge `efec5a79`) compacts the detail-only tablet
  topbar to one row, removes duplicated breadcrumb/status chrome, and restores context → tabs →
  stages ordering while leaving Inbox/setup and mobile navigation semantics unchanged. Verification:
  focused shell (`18 passed`), active-studio reconnect (`5 passed`), frontend (`136 passed`), UI
  contracts (`11 passed`), docs/planning (`50 passed`), Ruff, mypy, and full CI including packaged UI
  browser passed.
- `W44-E1-S3-T46` (done) Render the mobile Work Item detail identity in the target compact header.
  Keep the AIDD brand and a truncated current Work Item label discoverable beside the existing
  overflow/runtime control, preserve an accessible path back to Inbox, and leave recovery/question
  headers, routes, ids, status ownership, and launch controls unchanged. PR #418 (merge `f533b336`)
  adds the compact mobile detail header and preserves the existing Inbox arrow path, runtime
  disclosure, and route/DOM contracts. Fresh `390x844` and `320x568` captures show the AIDD brand,
  current Work Item id, Inbox/back path, and overflow control without clipping or horizontal
  overflow; recovery and mobile decision surfaces remain unchanged. Verification: shell (`20`),
  mobile studio header (`6`), focused mobile primary decision (`4`), frontend (`136`),
  docs/planning (`50`), Ruff, mypy, and full CI including packaged UI browser passed.
- `W44-E1-S3-T47` (done) Align the mobile recovery and Decision Workbench header with the target
  mobile decision composition. PR #421 (merge `722e38b0`) scopes the compact recovery-mode chrome
  to the AIDD brand, current Work Item identity, accessible Inbox/back path, and touch-safe
  overflow/runtime disclosure while preserving question, approval, validation, and runtime recovery
  content, routes, DOM ids, status ownership, and one primary action. Fresh question/recovery
  captures at `390x844` and `320x568` show the identity, arrow, and overflow affordances without
  horizontal overflow; overview, Inbox, and setup headers remain unchanged. Focused mobile route,
  recovery, and question checks, frontend Node suite (`136 passed`), UI contracts/docs/planning,
  Ruff, mypy, full Python matrix, deterministic scenarios, adapter conformance, packaged UI browser,
  security checks, and build all passed.

Wave 44 exit evidence:

- no global launch or Runner controls leak into non-launch surfaces;
- each launch surface has one contextual Runner and one primary action;
- the target shell hierarchy is visible without serial scrolling on supported desktop layouts;
- mobile decision and recovery actions are visible, focusable, and unclipped in the initial
  viewport;
- browser checks show no console errors, horizontal overflow, duplicate primary actions, or focus
  loss;
  - a fresh rendered audit confirms remaining gaps are absent or explicitly blocked. T19 is
    evidence-complete and T25-T47 are complete. The T47 audit confirms that mobile question and
    recovery headers expose AIDD, current Work Item identity, Inbox/back, and overflow controls
    without changing recovery content or introducing overflow. The task-centered renderer/default
    routing decision is accepted for the supported provider-free surfaces. Human, Claude/cross-runtime,
    and Wave 36 acceptance remain outside this rendered loop.

Wave 44 reconciliation:

- `2026-08-26` PR #421 (merge `722e38b0`) completed `W44-E1-S3-T47` and closes the rendered
  acceptance loop. Before T47, mobile question/recovery headers showed AIDD and Inbox but omitted
  the current Work Item identity. The scoped recovery-mode header now keeps AIDD, the current Work
  Item label, a real Inbox arrow path, and a 44px overflow/runtime control in the first viewport at
  `390x844` and `320x568`; question, approval, validation, and runtime recovery content and action
  semantics remain unchanged. Fresh captures and diagnostics are retained in
  `docs/e2e/w44-e1-s3-t47-rendered-audit.md`. Full PR CI passed, including Python 3.12/3.13/3.14,
  deterministic scenarios, adapter conformance, packaged UI browser, security checks, and build.
  The target-centered renderer/default routing is accepted for the provider-free surfaces; human,
  Claude/cross-runtime, and Wave 36 evidence remain parked.

## Wave 45 — live medium flow hardening (`planned`)

Goal: make the installed medium live flow terminate truthfully for both interview and
non-interview stages while retaining the target UI and historical evidence contracts.

### Epic W45-E1 — aggregate finalization compatibility (`planned`)

Goal: allow aggregate implementation finalization to publish the documents that actually exist for
the selected flow, without requiring conditional interview records on non-interview runs.

#### Slice W45-E1-S1 — non-interactive publication (`planned`)

Goal: keep canonical stage publication fail-closed for declared substantive and AIDD-owned records,
while treating `questions.md` and `answers.md` as optional control documents when no interview took
place.

Dependencies: Wave 44 rendered UI acceptance; existing stage-output ownership registry and
aggregate finalization service.

Local tasks:

- `W45-E1-S1-T1` (done) Permit non-interactive stage finalization to publish without `answers.md`.
  - PR #425 (merge `2878a851`) updates the runtime-agnostic stage-output publication boundary so
    conditional interview documents are copied when present, while their absence no longer turns a
    successful non-interview implementation into failed aggregate finalization. Substantive runtime
    outputs and canonical AIDD records retain strict existence checks; adapters, stage contracts,
    routes, and historical evidence are unchanged.
  - Verification: focused publication tests (`5 passed`), `tests/core/test_stage_runner.py` plus
    implementation-finalization tests (`92 passed`), Ruff, and mypy (`234 files`) passed; CI passed
    Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, packaged UI browser, CodeQL,
    dependency review, scorecard, and build.

- `W45-E1-S1-T2` (done) Normalize terminal status markers after repair and validation.
  - Output: make lifecycle-owned `stage-result.md` rendering and repair reconciliation emit exactly
    one terminal status in the `Status` section, so a valid Review/QA artifact cannot be rejected by
    a stale or duplicate compatibility marker. Preserve attempt history, validator evidence, and the
    existing public document contract.
  - Scope: `src/aidd/core/stage_terminal.py` and focused stage-result/orchestration tests only.
  - Verification: renderer and exhausted-repair regression tests must prove one canonical status for
    success and failure, idempotent reconciliation, preserved history, and no status drift in a fresh
    live medium flow.
  - PR #428 (merge `a184fe95`) canonicalizes success/failure status sections and preserves historical
    attempt evidence; focused core/repair tests, Ruff, mypy, and full CI passed.

- `W45-E1-S1-T3` (done) Accept valid compound shell verification commands in implementation evidence.
  - Output: extend the implementation verification evidence parser so commands containing shell
    assignments, command substitutions, pipelines, and `test` assertions are recognized as executable
    command evidence when the same verification bullet records the observed result. Preserve the
    existing fail-closed behavior for outcome claims without a command or artifact reference.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py`, focused semantic-rule/harness tests, and
    the live implementation evidence fixture only; no runtime adapters, stage contracts, or public
    document shape changes.
  - Verification: compound-command parser tests must pass for the exact `git status ... | awk ...; test
    -z` shape and equivalent safe shell forms, while malformed/non-executable snippets remain rejected;
    run the focused validator/harness suite, Ruff, and mypy.
  - PR #430 (merge `fa9a9674`) adds command-substitution recognition before shell-token evaluation and
    regression coverage for the exact compound `git status`/`awk`/`test` evidence shape. Focused
    implementation, semantic implement, and semantic QA checks pass (`72 passed`); CI passed.

#### Slice W45-E1-S2 — QA evidence traceability (`planned`)

Goal: make runtime-authored QA evidence resolve to the canonical upstream artifacts or valid
QA-local command evidence required by the cross-document validator, without weakening fail-closed
traceability.

Dependencies: W45-E1-S1; the QA report contract, QA prompt pack, and
`CROSS-QA-UPSTREAM-EVIDENCE` validator.

Local tasks:

- `W45-E1-S2-T1` (done) Require every QA evidence claim to cite a resolvable artifact or executable result.
  - Output: update the QA report authoring guidance and its deterministic fixture coverage so
    `Evidence`, `Verification summary`, `Readiness`, and task-acceptance bullets use exact existing
    workspace-relative artifact paths or stable `EV-N` definitions backed by those paths or by a
    syntactically executable command with an explicit terminal outcome. In particular, a bounded
    product-diff claim must include its executable `git diff --name-only ... -> pass` result (or an
    exact upstream artifact), rather than a prose-only `bounded product path check`.
  - Scope: `prompt-packs/stages/qa/`, `contracts/documents/qa-report.md`, and focused QA
    cross-document/semantic fixtures and tests; do not broaden artifact roots or permit source-only
    paths to bypass upstream evidence resolution.
  - Verification: deterministic QA fixtures reproduce the former `EV-4` false negative and pass
    with the corrected report shape; malformed evidence without a command/result or exact artifact
    path remains rejected. Run the focused QA validator/prompt/scenario tests, Ruff, and mypy.
  - PR #434 (merge `48f80f81`) adds explicit bounded-diff command evidence guidance, preserves
    fail-closed source-path handling, and adds accepted/rejected deterministic cross-document
    fixtures. Focused QA/semantic tests (`144 passed`), docs/planning checks (`50 passed`), Ruff,
    mypy, full CI, packaged UI browser, adapter, scenario, and build checks passed.

- `W45-E1-S2-T2` (done) Accept explicit negative terminal outcomes for implementation residue checks.
  - Output: align the implementation evidence parser and authoring guidance so an executable
    verification command with a concrete negative/clean result such as `-> no task-local cache`
    is accepted as an observed outcome, while prose-only claims, missing commands, and ambiguous
    status text remain rejected. Preserve the existing fail-closed requirement for command evidence,
    ignored-residue auditing, and exact outcome markers (`pass`, `fail`, `not-run`).
  - Scope: `src/aidd/validators/semantic_rules/evidence.py`,
    `prompt-packs/stages/implement/run.md`, and focused semantic/harness fixtures and tests only;
    do not change runtime adapters, stage contracts, or public UI behavior.
  - Verification: accepted executable residue/check bullets with `no ...` or equivalent concrete
    clean outcomes, rejected prose-only and commandless claims, existing `pass`/`fail`/`not-run`
    behavior, Ruff, mypy, focused semantic implement and live-evidence tests, and docs/planning
    consistency.

- `W45-E1-S2-T3` (done) Restrict implementation touched-file extraction to top-level entries.
  - Output: make task-diff evidence read only the top-level bullets in the `Touched files` section,
    so nested explanatory bullets containing code snippets, identifiers, or user-facing text are
    not misclassified as repository paths. Preserve reporting of every actual changed path and the
    fail-closed mismatch/scope findings for missing or unsupported top-level entries.
  - Scope: `src/aidd/core/task_repository_evidence.py` and focused
    `tests/core/test_task_repository_evidence.py` regression coverage only; do not broaden task
    scope rules, semantic document contracts, runtime adapters, or public UI behavior.
  - Verification: a report with nested backticked code examples and multiple top-level file entries
    produces only the canonical changed paths, while missing top-level paths and unsupported
    top-level paths continue to fail with `SEM-TASK-DIFF-MISMATCH`/scope findings. Run focused core
    repository-evidence tests, Ruff, mypy, and the planning consistency checks.

#### Slice W45-E1-S3 — selected-task execution scope fidelity (`planned`)

Goal: keep each implementation attempt bounded to the one dependency-ready task selected by the
ledger, so later task work cannot invalidate the current task's evidence or exhaust repair budget.

Dependencies: W45-E1-S2; task-local baseline/diff evidence and the implement prompt contract.

Local tasks:

- `W45-E1-S3-T1` (done) Enforce the selected implementation task as a hard execution boundary.
  - Output: strengthen the implement prompt and deterministic contract fixtures so the runtime must
    change and report only the selected task's `In scope` paths, stop before later tasklist cards,
    and leave later tests or deliverables for their own dependency-ready attempt. Preserve the
    existing global allowed-write scope, task-local baseline/diff evidence, fail-closed mismatch
    findings, and one-task-at-a-time ledger semantics.
  - Scope: `prompt-packs/stages/implement/run.md`, `prompt-packs/stages/implement/system.md`, and
    focused prompt/semantic/harness fixtures and tests only; do not weaken task-diff validation,
    change runtime adapters, or alter public UI behavior.
  - Verification: deterministic prompt/fixture checks prove selected-task-only guidance and later
    task isolation; an out-of-scope task diff remains rejected with
    `SEM-TASK-SCOPE-MISMATCH`; run focused implement/evidence tests, Ruff, mypy, and planning
    consistency checks.

- `2026-08-28` reconciliation after PR #442 (merge `21e75401`) marks `W45-E1-S3-T1` done. The
  implement run and system prompts now require one bounded attempt for exactly the selected task
  card and prohibit editing deliverables owned by later cards; prompt-pack hash fixtures and
  regression coverage were updated. Focused prompt/evidence tests (`138 passed`), Ruff, mypy,
  planning checks, and full CI including deterministic scenarios, adapter conformance, packaged UI
  browser, security, and build checks are green. The selected-task boundary fix is ready for a
  fresh Codex/Claude medium rerun from clean `main`.

- `2026-08-28` fresh Claude medium `eval-live-007-claude-code-20260827T223441Z` was rerun from
  clean `main` after the W45 evidence-contract fixes and completed `idea -> qa` with terminal
  `pass` and manual `counted-clean` quality evidence. All eight stage quality audits chose
  `continue`; the task-aware checkpoint reports matching tasklist/ledger hashes, successful
  aggregate finalization, and Review eligibility. The target Hono diff is bounded to the four
  intended files and its focused TypeScript/Vitest verification passed (237 tests). Together with
  the retained Codex medium pass and the Wave 42 UI target audit, this closes the current medium
  diagnose -> fix -> rerun loop without a confirmed product or UI defect; task-centered routing
  remains the default. The run bundle is retained at
  `.aidd/reports/evals/eval-live-007-claude-code-20260827T223441Z/`.

- `2026-08-28` reconciliation after PR #438 (merge `7b3bfff4`) marks `W45-E1-S2-T3` done. Task-diff
  evidence now reads only top-level `Touched files` bullets, so nested code explanations cannot be
  misclassified as changed paths; missing and unsupported top-level entries remain fail-closed.
  Focused repository-evidence/implementation-evidence tests (`32 passed`), Ruff, mypy, docs
  consistency, planning integrity (`50 passed`), full CI, deterministic scenarios, adapter
  conformance, packaged UI browser, and build checks are green. The failed Claude run remains
  retained as diagnostic evidence; the next action is a fresh Claude medium rerun from this clean
  `main`.

- `2026-08-27` reconciliation after PR #436 (merge `d12bea06`) marks `W45-E1-S2-T2` done. The
  implementation evidence parser now accepts concrete executable negative/clean outcomes such as
  `-> no task-local cache`, while ambiguous arrow text remains rejected. Prompt guidance, hash
  fixtures, focused semantic tests, docs/planning checks, Ruff, mypy, full CI, deterministic
  scenarios, adapter conformance, packaged UI browser, and build checks are green. The next
  action is a fresh Claude medium rerun from this clean `main`.

- `2026-08-27` reconciliation after PR #434 (`48f80f81`) marks `W45-E1-S2-T1` done. QA authoring
  now requires bounded product-diff claims to cite an executable command with an explicit outcome
  or an exact upstream artifact; deterministic fixtures preserve rejection of prose-only evidence.
  The fresh Codex medium run `eval-live-007-codex-20260827T145034Z` remains diagnostic until the
  lane is rerun from clean `main` with the merged guidance.

- `2026-08-27` reconciliation after PR #430 (`fa9a9674`) marks `W45-E1-S1-T3` done. The fresh
  Codex medium run `eval-live-007-codex-20260827T093650Z` completed `idea -> qa` with status `pass`,
  including task-aware checkpoint and target verification. A Claude rerun remains required to
  resolve the previously retained QA evidence-link outcome before claiming a clean two-runtime flow.

- `2026-08-27` Reconciled PR #428 (`a184fe95`) as `W45-E1-S1-T2` done. A fresh Codex medium run
  `eval-live-007-codex-20260827T082029Z` reached implementation with all four target Hono files and
  240 focused tests passing, but AIDD evidence validation rejected a valid compound `git status`/`awk`
  command as an unverifiable claim after repair budget exhaustion. No target product defect was found;
  `W45-E1-S1-T3` is promoted as the bounded parser hardening task before rerunning Codex and Claude.

- `2026-08-27` Codex medium rerun `eval-live-007-codex-20260827T064545Z` completed idea through
  implementation with target diff and focused verification passing, but stopped at Review after
  three validation attempts. The review report was complete and approved; the lifecycle result was
  rejected because the Status section retained duplicate terminal markers after repair. This is an
  AIDD-owned canonical-record defect, not a Hono target or UI defect. `W45-E1-S1-T2` is promoted as
  the next bounded fix before rerunning Codex and Claude medium lanes.

- `2026-08-26` PR #418 (merge `f533b336`) completed `W44-E1-S3-T46`. Mobile Work Item detail now
  keeps the AIDD brand, current Work Item identity, accessible Inbox/back path, and overflow/runtime
  control in one compact 64px header at `390x844` and `320x568`. Fresh captures across
  `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900` show the target shell hierarchy,
  truthful context, tabs/stages, and launch inspector without clipping or horizontal overflow;
  console/request diagnostics are clean. Focused shell (`20`), mobile header (`6`), primary decision
  launch (`4`), frontend (`136`), docs/planning (`50`), Ruff, mypy, and full CI including packaged
  UI browser passed. The rendered acceptance loop has no remaining bounded UI gap; deferred human,
  Claude/cross-runtime, and Wave 36 evidence remain parked.

- `2026-08-26` PR #416 (merge `efec5a79`) completed `W44-E1-S3-T45`. Tablet Work Item detail now
  keeps a compact 64px topbar, hides duplicate breadcrumb/status chrome, and restores the target
  context → tabs → stages order at `768x1024`; Inbox/setup and mobile navigation behavior remain
  unchanged. Fresh geometry is contained at `768x1024`, `390x844`, and `320x568`, with shell `18`
  passed, active-studio reconnect `5` passed, frontend `136` passed, UI contracts `11` passed,
  docs/planning `50` passed, Ruff, mypy, and full CI including packaged UI browser green. The next
  audit identifies a separate mobile detail-header identity gap; `T46` is promoted to `Next`.

- `2026-08-26` PR #414 (merge `2534cdef`) completed `W44-E1-S3-T44`. Work Item detail context now
  uses a compact target-style header: the title spans the available canvas, phase/status and durable
  Work Item identity remain discoverable in one dense metadata row, and the desktop tabs/stage strip
  follow without the removed eyebrow/duplicate identity stack. Tablet uses the same compact context
  treatment while retaining its established topbar; mobile remains unchanged. Focused desktop shell
  checks (`15 passed`), active-studio journey (`5 passed`), frontend (`136 passed`), UI contracts
  (`183 passed`), docs/planning (`50 passed`), Ruff, mypy, and full CI including packaged UI browser
  (`14m53s`) passed. Fresh comparison identifies the next bounded tablet gap: at `768x1024` the
  legacy topbar remains tall and tabs precede the context header; `T45` is now `Next`.

- `2026-08-26` PR #412 (merge `831be726`) completed `W44-E1-S3-T43`. Work Item detail surfaces now
  collapse the generic desktop breadcrumb/status row to zero-height chrome while keeping the real
  runtime settings control as a fixed launch/recovery disclosure. Inbox/setup topbars, routes, ids,
  status/runtime semantics, and mobile behavior remain unchanged; the Inbox browser helper now waits
  for the durable detail identity to be attached rather than requiring the intentionally hidden chip.
  Focused desktop shell checks (`12 passed`), frontend (`136 passed`), UI contracts (`183 passed`),
  docs/planning (`50 passed`), Ruff, mypy, targeted Inbox regressions, and full CI including packaged
  UI browser (`23m19s`) passed. Fresh comparison shows the next bounded gap: the internal detail context
  header still consumes a stacked eyebrow, phase/status line, and duplicate identity rows; `T44` is now
  `Next`.

- `2026-08-26` PR #410 (merge `3ef38644`) completed `W44-E1-S3-T42`. Work Item detail surfaces now
  use the target two-level desktop shell: an 84px primary navigation rail followed by a 236px
  project/Work Items rail; Inbox retains one 244px project rail and mobile collapses the secondary
  rail. Existing navigation ids, Work Item selection/deep links, ordering, and route semantics are
  preserved. Focused shell/legacy/inbox checks (`35`), the five-viewport provider-free matrix (`9`),
  frontend (`136`), UI contracts/docs/planning (`110`), Ruff, mypy, and full CI passed. Fresh capture
  shows the next target-equivalence gap: the generic desktop breadcrumb/status topbar still adds a
  duplicated 64px layer above the Work Item header; `W44-E1-S3-T43` is now `Next`.

- `2026-08-26` PR #408 (merge `d7994130`) completed `W44-E1-S3-T41`. Validation Repair now keeps
  the desktop Runner and primary repair action inline and visible in the initial `1280x900` and
  `1440x900` viewports through compact tokenized spacing, while the tablet remains scrollable and
  mobile retains its safe-area dock. Fresh screenshots and five-viewport geometry show no overlap,
  nested scroll, duplicate primary action, diagnostic error, or horizontal overflow; the next
  target-equivalence gap is the detail-shell split between the target icon rail and Work Items
  navigator, tracked as `W44-E1-S3-T42`.

- `2026-08-26` PR #406 (merge `40632549`) completed `W44-E1-S3-T40`. Validation Repair now keeps
  the desktop action group in normal inspector flow, so the Runner, primary repair, Request change,
  and raw evidence controls no longer cover the consequence, exact repair brief, or extension
  evidence. Mobile retains the initial-viewport safe-area dock. Fresh initial/action screenshots and
  the five-viewport matrix show no desktop overlap, while also exposing the next target-equivalence
  gap: the inline desktop action sits below the initial viewport on `1280x900`/`1440x900`. `T41` is
  now `Next` to reclaim that vertical rhythm without reintroducing an overlay.

- `2026-08-26` PR #402 (merge `924138cc`) completed `W44-E1-S3-T38`. Shared shell breadcrumbs now
  present a truthful project label, Work Item, and current-stage label without exposing the absolute
  filesystem path. Existing project-path provenance utilities, route/deep-link behavior, DOM ids,
  and setup/launch semantics remain unchanged. Focused breadcrumb browser checks (`2 passed`),
  frontend tests (`36 passed`), Guided Setup/packaged smoke (`2 passed`), UI contracts/docs/planning
  (`105 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build
  checks passed. `T39` was promoted and completed; `T40` is now `Next`.

- `2026-08-26` PR #400 (merge `6d9f8287`) completed `W44-E1-S3-T37`. Runs and Attempts now present a
  compact retained-run list and tighter chronology rhythm alongside the selected-attempt inspector,
  retained evidence, immutable lineage, and read-only actions. Routes, selectors, comparison
  eligibility, archive semantics, and historical evidence remain unchanged. Focused history browser
  checks (`12 passed`, plus `2 passed` after final CSS refinement), frontend tests (`36 passed`),
  UI contracts/docs/planning (`108 passed`), Ruff, mypy, full CI, deterministic, adapter,
  packaged-browser, security, and build checks passed. `T38` was promoted and completed; `T39` is now
  `Next`.

- `2026-08-26` PR #398 (merge `da87abd7`) completed `W44-E1-S3-T36`. Review/QA Remediation now keeps
  findings, source paths, retained evidence, durable request state, downstream impact, Runner readiness,
  and one remediation action in the target two-region composition with responsive fallback. Exact finding
  ids, selection semantics, draft destinations, conflict/staleness behavior, routes, and mutation services
  remain unchanged. Focused browser review/QA (`6 passed`), frontend tests (`28 passed`), UI contracts,
  docs/planning, Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build checks
  passed. `T37` and `T38` were promoted and completed; `T39` is now `Next`.

- `2026-08-26` PR #396 (merge `66af77e9`) completed `W44-E1-S3-T35`. Implementation Review now presents
  a compact claims/verification overview, retains the canonical task ledger, and places repository diff
  evidence beside a distinct Review inspector with responsive one-column fallback. Repository-truth
  evidence, launch readiness, read-only stage documents, routes, ids, and one primary Review action remain
  unchanged. Focused browser composition (`3 passed`), frontend tests (`36 passed`), UI contracts,
  docs/planning (`108 passed`), Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security,
  and build checks passed. `T35` was promoted as the next dependency-ready task and is now complete;
  `T36` was then completed and `T37` is now `Next` with `T38` as its direct `Soon` successor.

- `2026-08-26` PR #394 (merge `901b6bd0`) completed `W44-E1-S3-T34`. Project Work now presents a compact
  server-owned grouped table with explicit Work Item, Stage, Progress, Runner, Last event, and Status
  columns, truthful progress bars, bounded selected inspector, and responsive normal flow. The selected
  view suppresses the duplicated entry banner while Guided Setup resume retains its direct Continue
  existing Work Item action. Routes, ids, core-owned membership/order, deep links, keyboard selection,
  action services, and existing compatibility behavior remain unchanged. Target Project Work browser
  checks (`4 passed`), Inbox selection/routing (`4 passed`), frontend Inbox (`8 passed`), UI contracts,
  docs/planning, Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build all
  passed. `T35` was promoted as the next dependency-ready task and is now complete; `T36` is now `Next`
  and `T37` is its direct `Soon` successor.

- `2026-08-26` PR #392 (merge `99ce2bca`) completed `W44-E1-S3-T33`. Decision and Mobile Decision
  now preserve the target first-viewport hierarchy for context, retained evidence, resolution,
  editor/destination state, and one real primary action across question and approval fixtures at all
  five supported viewports. Read-only evidence opens when source snippets exist; approval queues keep
  Allow once as the sole primary while secondary decisions remain available. Routes, ids, mutation
  services, fail-closed recovery, and generated-document immutability remain unchanged. Focused
  browser/UI checks (`20 passed`), UI contracts (`53 passed`), docs/planning, Ruff, mypy, full CI,
  deterministic, adapter, packaged-browser, security, and build checks passed. `T34` was promoted as the
  next dependency-ready task and is now complete; `T35` is now `Next` and `T36` is its direct `Soon`
  successor.

- `2026-08-25` PR #390 (merge `4fc916a7`) completed `W44-E1-S3-T32`. Task Workspace and Active Task
  now keep the selected attempt inspector, factual attempt controls, task groups, and live-output
  tray in the target first-viewport desktop composition. The live tray is docked to the viewport,
  the list and inspector use bounded workbench scroll regions without nesting inside the shell
  scroller, and mobile retains its normal stacked flow. Core-owned task ledger/status/eligibility,
  routes, ids, mutation services, reconnect/cancel semantics, and one-primary behavior remain
  unchanged. Ready/running/waiting/cancelling/failed/completed browser fixtures passed across
  desktop/mobile, together with docs/planning, Ruff, mypy, full CI, deterministic, adapter,
  packaged-browser, security, and build checks. `W44-E1-S3-T33` is now the next dependency-ready
  task and `T34` is its direct Soon successor.

- `2026-08-25` PR #388 (merge `f7ab7364`) completed `W44-E1-S3-T31`. Flow Complete now keeps the
  existing core-recommended action visible and focusable across the supported bounded tablet/
  desktop widths, including the audited `768x1024` first viewport, via the established safe-area-
  aware action dock. Immutable handoff/evidence content remains in document flow; fresh-QA gating,
  source-run immutability, lineage overlays, recommendation truth, one-primary semantics, routes,
  ids, and mutation behavior are unchanged. The five-viewport completion matrix and target legacy
  composition/mobile focus checks passed, together with UI contracts, docs/planning consistency,
  Ruff, mypy, full CI, packaged UI browser, deterministic, adapter, security, and build checks.
  `W44-E1-S3-T32` is now the next dependency-ready task and `T33` is its direct successor.

- `2026-08-25` PR #386 (merge `7c58edda`) completed `W44-E1-S3-T30`. The Work Item Launch primary
  action is now visible and focusable at `320x568` in a touch-safe bottom dock, while the existing
  core-owned Runner readiness projection, literal disabled reason, one contextual Runner, routes,
  ids, and fail-closed launch mutation path remain unchanged. The five-viewport launch suite and
  provider-free create/Runner/launch matrix passed with one primary action, clean diagnostics, focus,
  and no horizontal overflow; T31 was promoted as its successor and is now complete, with T32 next.

- `2026-08-25` PR #384 (merge `b30de404`) completed `W44-E1-S3-T29`. The fresh rendered audit is
  retained in `docs/e2e/w44-e1-s3-t29-rendered-exit-audit.md`: focused W44 suites passed (`71`),
  while the five-viewport provider-free matrix recorded `6` passes and two first-viewport contract
  failures. Confirmed gaps were decomposed into T30-T39; T30 was promoted as the first convergence
  task and is now complete, with T31 promoted as the only dependency-ready successor. Human
  usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `2026-08-25` PR #382 (merge `5828f53b`) completed `W44-E1-S3-T28`. Markdown Workspace now
  uses the target compact navigator/reader/context composition with visible provenance, source
  and path utilities, heading-map anchors, one contextual primary action, and read-only generated
  document semantics preserved. Focused browser/layout checks, document evidence journeys,
  frontend/UI contracts, accessibility/readability/design-token checks, docs/planning, Ruff, mypy,
  full CI, deterministic, adapter, packaged-browser, security, and build checks passed. `T29` is
  now the only dependency-ready task for the next fresh 13-surface convergence audit; human
  usability, Claude/cross-runtime, and Wave 36 acceptance stay parked.

- `2026-08-25` PR #380 (merge `737365c5`) completed `W44-E1-S3-T27`. Implementation Review now
  leads with repository truth, changed-file/diff evidence, verification commands, scope and risk
  coverage, and an explicit Review gate. Review and QA remediation now use target finding tables,
  source/evidence anchors, durable Write/Preview requests, downstream impact, contextual Runner
  readiness, and one primary action while preserving existing routes, API shapes, ledger/evidence
  projections, selectors, and generated-document boundaries. Focused browser journeys (`6 passed`),
  frontend/UI contracts, readability/design-token/accessibility checks, docs/planning, Ruff, mypy,
  full CI, deterministic, adapter, packaged-browser, security, and build checks passed. `T28` is now
  the only dependency-ready task; human usability, Claude/cross-runtime, and Wave 36 acceptance stay
  parked.

- `2026-08-25` PR #378 (merge `9b97e908`) completed `W44-E1-S3-T26`. Create Work Item now uses the
  target editor/preview shell with durable context and constraints sections, visible draft status,
  responsive one-action footer, and no duplicate internal submit action. Existing request write,
  Work Item identity, route/API shapes, runtime-independent creation, launch-only Runner selection,
  and operator-authored Markdown semantics remain unchanged. Target Create Work Item, guided setup,
  first-time recovery, frontend, UI contracts, design-token inventory, docs/planning, Ruff, mypy,
  full Python matrix, deterministic, adapter, security, packaged UI browser, and build CI passed.
  `W44-E1-S3-T27` was the only dependency-ready task; T28 was planned, while human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #376 (merge `a8f15319`) completed `W44-E1-S3-T25`. Flow Complete now leads with a
  target-like completion status row, a central immutable handoff/evidence composition, and a bounded
  Completion inspector that exposes fresh-QA checks, retained evidence, run IDs, the core-recommended
  outcome, one primary action, and disclosed secondary outcomes. Existing routes, selectors, lineage,
  immutable source-run semantics, and handoff services remain unchanged. Focused Flow Complete/mobile/
  terminal/desktop browser checks, frontend suites, five-viewport geometry/accessibility/diagnostic
  checks, UI contracts, planning integrity, Ruff, mypy, deterministic, adapter, security, packaged UI
  browser, and build CI passed. `W44-E1-S3-T27` is now the only dependency-ready task; human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-25` PR #366 (merge `82fb1d23`) completed `W44-E1-S3-T20` from the T19-audited revision.
  The selected Project Work list now stays inside its server-owned grid column, the right-side
  Work Item inspector no longer overlaps rows, and mobile uses normal stacked flow. Four-viewport
  geometry/accessibility/deep-link coverage and full CI are green. `W44-E1-S3-T21` is now the only
  dependency-ready task; T22 is the direct Soon successor and T23-T28 remain planned. Wave 44 exit
  evidence and default task-centered routing remain open until the remaining target compositions
  are audited.

- `2026-08-25` completed `W44-E1-S3-T19` on revision `35ff0ace`. The fresh audit is retained in
  `docs/e2e/w44-e1-s3-t19-rendered-exit-audit.md`. The five-viewport provider-free matrix and
  target legacy-composition checks are green with clean diagnostics, but screenshot comparison
  confirmed remaining target-shell, inspector, recovery, history, completion, and editor-density
  gaps. `W44-E1-S3-T20` was the only dependency-ready task; T21-T28 were planned successors.

- `2026-08-24` PR #362 (merge `4e36bc6f`) completed `W44-E1-S3-T18`. The compact desktop/tablet
  stage strip now keeps all eight labels, including `Implement`, fully readable at `1280x900` while
  preserving canonical order, phase grouping, active/current semantics, keyboard access, and the mobile
  current-stage disclosure. Five-viewport stage-strip/accessibility journeys, related active-shell and
  mobile navigation checks (`12`), frontend Node suite (`136 passed`), UI/docs/planning checks (`103
  passed`), packaged JavaScript, Ruff, mypy, deterministic, adapter, security, build, and packaged-browser
  checks passed. `W44-E1-S3-T19` is now the only dependency-ready task for the fresh Wave 44 exit and
  default-routing audit; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #360 (merge `a678418a`) completed `W44-E1-S3-T17`. Validation Repair now leads with
  the finding, a literal repair consequence, readable Runner readiness, and one primary recovery action
  before long extension evidence across all five supported viewports. Existing readiness projections,
  mutation services, selectors, routes, and API shapes remain unchanged. Focused validation browser
  checks (`10`), recovery journeys (`13`), frontend/UI contracts, docs/planning, Ruff, mypy, packaged
  JavaScript, full CI, deterministic, adapter, security, build, and packaged-browser checks passed.
  `W44-E1-S3-T18` is now the only dependency-ready task for the remaining stage-strip clipping follow-up;
  Wave 44 exit/default-routing evidence remains open, while human usability, Claude/cross-runtime, and
  Wave 36 acceptance stay parked.

- `2026-08-24` PR #358 (merge `f543ae51`) completed `W44-E1-S3-T16`. Markdown Workspace now keeps a
  compact read-only reading brief, document body, and visible heading map together in the selected
  reader composition while preserving navigator provenance, freshness, Source/Compare behavior,
  stable line/heading anchors, existing routes/API shapes, and generated-document immutability. The
  five-viewport document evidence journey, desktop first-viewport geometry, mobile target-size checks,
  frontend/UI asset/readability contracts, Ruff, mypy, full CI, deterministic, adapter, packaged-browser,
  security, and build checks passed. `W44-E1-S3-T17` is now the only dependency-ready task; the independent
  stage-strip label clipping follow-up and Wave 44 exit/default-routing evidence remain open, while human
  usability, Claude/cross-runtime, and Wave 36 acceptance stay parked.

- `2026-08-24` PR #356 (merge `2e77fac5`) completed `W44-E1-S3-T15`. Active Task now leads with the
  selected task-attempt evidence: identity, factual elapsed and last-output ages, durable milestone,
  connection/reconnect cursor, one `Open live output` primary, guarded cancellation, and collapsible
  raw output. The browser keeps core-owned task membership/eligibility and existing mutation services;
  no fabricated progress or new API/route semantics were added. Active-attempt provider-free states,
  ready-task regression, desktop tray geometry, frontend/UI contracts, Ruff, mypy, deterministic,
  adapter, packaged-browser, build, and all required CI lanes passed. `W44-E1-S3-T16` is now the next
  dependency-ready task and T17 remains behind it; independent stage-strip label clipping at 1280px is
  retained as a separate follow-up, and Wave 44 exit/default-routing evidence remains open.

- `2026-08-24` PR #354 (merge `b3622bde`) completed `W44-E1-S3-T14`. Project Work now exposes a
  selectable, keyboard-accessible Work Item row with a retained inspector, compact search/filter,
  target-style stage/progress/Runner/last-event/status metadata, and reload-safe `inbox_work_item`
  selection state. The UI only filters/render-orders the existing core projection and keeps all
  route/API/DOM ids and primary mutation services intact. Inbox journey, selection/deep-link, full
  five-viewport matrix, frontend, UI contracts, Ruff, mypy, packaged JavaScript, deterministic,
  adapter, packaged-browser, and build checks passed. `W44-E1-S3-T15` is now Next; Markdown and
  Validation follow-ups remain planned. Human usability, Claude/cross-runtime, and Wave 36 acceptance
  remain parked.

- `2026-08-24` PR #352 (merge `e1d77b01`) completed `W44-E1-S3-T8` as a fresh rendered audit, not a
  Wave 44 exit claim. Provider-free Playwright captured all 13 target surfaces at desktop and mobile
  reference sizes; the authoritative five-viewport matrix remained clean for diagnostics, focus,
  target size, initial action visibility, and overflow. The audit retains four confirmed composition
  gaps: Project Work selected inspector/filter-table, Active Task live evidence, Markdown reader first
  viewport, and Validation Repair responsive hierarchy. Those are split into T14 (Next), T15 (Soon),
  T16, and T17; default task-centered routing remains provisional until these follow-ups are audited.
  Human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #350 (merge `d486e9ae`) completed `W44-E1-S3-T7`: shared Operator tokens now use
  a warm workspace canvas, deep navy context chrome, cobalt primary actions, mint success, amber
  warning, and a 14px body reading role; existing teal/green selector aliases continue to resolve
  through the new semantic roles. The target token contract, 65 focused UI/asset/semantic/density
  checks, frontend suite, five-viewport matrix, Ruff, mypy, packaged JavaScript, deterministic,
  adapter, build, and packaged-browser checks passed. `W44-E1-S3-T8` is now Next for a fresh 13-surface
  rendered parity audit; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #348 (merge `3193e39e`) completed `W44-E1-S3-T13`: the immutable Flow Complete
  handoff now reuses the responsive single-primary action dock, so the core-recommended outcome
  action is visible and focusable at `320x568` as well as the other four supported viewports. The
  completion journey, terminal journeys, full provider-free matrix, UI contracts, frontend suite,
  Ruff, mypy, packaged JavaScript, deterministic, adapter, build, and packaged-browser checks passed.
  `W44-E1-S3-T7` is now Next for the target palette and density alignment; `W44-E1-S3-T8` is its
  direct successor and is now Soon. Human usability, Claude/cross-runtime, and Wave 36 acceptance
  remain parked.

- `2026-08-24` PR #346 (merge `f1f51178`) completed `W44-E1-S3-T12`: the Review-remediation
  journey now uses the authoritative rejected Review quality gate and its existing durable
  `Send selected to implement` control remains visible in the initial viewport at all five
  supported sizes. Focused Review matrix, recovery, UI contract, frontend, Ruff, mypy, packaged
  JavaScript, packaged-browser, deterministic, adapter, security, and build checks passed. The
  same full matrix exposed an independent Flow Complete first-action gap at `320x568`; it is
  split into `W44-E1-S3-T13`, which is now Next. Token alignment `T7` remains Soon behind T13;
  human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `2026-08-24` PR #338 (merge `99da14c9`) completed `W44-E1-S3-T6`: Create Work Item now has a
  target request editor and Markdown preview, Runs/Attempts has a selected-attempt inspector,
  and Flow Complete exposes handoff, evidence, and completion tables while preserving routes,
  ids, lineage, and immutable history. CI passed including frontend, packaged UI browser,
  deterministic, security, and build checks. A fresh rendered audit then found an outdated
  question-recovery matrix selector and a fixed-width Validation Repair child that clips on
  mobile and pushes `Run Repair` below the first viewport. Those are split into `T9` and `T10`;
  `T9` is now Next and `T10` is Soon. Token alignment `T7` and final audit `T8` remain planned;
  human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `W44-E1-S3-T5` is complete in PR #336 (merge `e088c50f`). Explicit recovery routes now land on
  the server-selected question, validation, or Review finding surface instead of a generic
  summary. The Decision surface renders the real question form before shared decision chrome,
  retains evidence/consequence controls and durable `answers.md` destination, and hides the
  dashboard shell on mobile so the decision is the first readable content. Provider-free parity
  now uses the rejected Review fixture for remediation, with focused desktop/mobile browser
  coverage and clean frontend, docs/planning, Ruff, mypy, deterministic, adapter, packaged-browser,
  security, and build checks. `W44-E1-S3-T6` is now `Next`, `T7` is in `Soon`; human usability,
  Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `W44-E1-S3-T3` is complete in PR #332 (merge `c7992051`). The target desktop Project/Work Item
  rail now exposes project identity, a deterministic server-owned Work Item list, selected state,
  canonical route intents, and accessible filtering. Shared Work Item context and the eight-stage
  strip remain visible on recovery, history, completion, and mobile decision surfaces; mobile
  keeps the central Inbox route usable without a hidden duplicate rail target. Focused browser
  journeys, the five-viewport provider-free matrix, frontend Node suite, UI/docs/planning checks,
  Ruff, mypy, deterministic scenarios, adapter conformance, packaged UI browser, security checks,
  and build all passed. `W44-E1-S3-T4` is now `Next`, `T5` is its direct successor in `Soon`, and
  human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `W44-E1-S3-T4` is complete in PR #334 (merge `df6b3f56`). The Ready-task Task Workspace now
  renders core-owned groups as a dependency-aware table, keeps the selected task in the canonical
  route across reload, exposes one Run action with one contextual Runner, and retains factual
  attempt evidence. The deterministic Ready fixture and five-viewport task journey remain
  provider-free; focused browser/UI, full frontend, docs/planning, Ruff, mypy, deterministic,
  adapter, packaged-browser, security, and build checks passed. `W44-E1-S3-T5` is now `Next`,
  `T6` is in `Soon`; human usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `W44-E1-S3-T2` is complete in PR #330 (merge `834b7bfd`). The fresh rendered comparison is
  retained in `docs/e2e/w44-e1-s3-t2-target-ux-audit.md`: all captured routes are technically
  clean, while the persistent Work Item shell, Ready-task composition, decision content, legacy
  create/history/completion layouts, and target visual tokens remain open. `T3` is now the next
  bounded frontend fix; human usability, Claude/cross-runtime, and Wave 36 acceptance remain
  parked.

- `W44-E1-S3-T1` is complete in PR #328 (merge `21c71156`). The provider-free matrix now records
  which journeys require an initial-viewport first action, retains honest scroll behavior for
  long secondary surfaces, and keeps focus, diagnostics, geometry, duplicate-primary, and
  overflow assertions active across all five supported viewports. A fixed mobile recovery action
  no longer inherits full-workspace width and clips at `320px`. All focused, frontend, docs,
  Ruff, mypy, full Python, deterministic, adapter, packaged-browser, security, and build checks
  passed. `W44-E1-S3-T2` is now `Next`; human usability, Claude/cross-runtime, and Wave 36
  acceptance remain parked.

- `W44-E1-S2-T3` is complete in PR #326 (merge `4e50e093`). The stage strip now uses compact
  readable labels and bounded desktop/tablet density, while mobile exposes a truthful current
  stage summary with an explicit keyboard-accessible disclosure for the full eight-stage path.
  Missing Task Workspace data retains Work Item context and navigation, and published tasklist
  evidence is surfaced by the dashboard so the UI avoids false missing-tasklist errors. Focused
  stage-strip/mobile/route/document checks, frontend Node suite (`135 passed`), full Python suite
  (`2430 passed`), docs/planning, Ruff, mypy, deterministic scenarios, adapter conformance,
  packaged UI browser, security checks, and build passed. `W44-E1-S3-T1` is now `Next`; human
  usability, Claude/cross-runtime, and Wave 36 acceptance remain parked.

- `W44-E1-S2-T2` is complete in PR #324 (merge `69ce00df`). Documents now retain Work Item
  context and stage navigation while keeping the navigator, reader, and evidence inspector
  co-visible on desktop; selected Task Workspace detail sits beside the authoritative list and
  active-attempt evidence occupies a full-width tray below. Existing routes, DOM ids, read models,
  and mutation services remain unchanged. Focused provider-free geometry and diagnostics at
  `1280x900`/`1440x900`, shell/document/implementation journeys, frontend tests, UI contracts,
  docs/planning, Ruff, mypy, full Python matrix, deterministic scenarios, adapter conformance,
  packaged UI browser, security checks, and build passed. `W44-E1-S2-T3` is now the next
  dependency-ready task.

- `W44-E1-S2-T1` is complete in PR #322 (merge `e3559b97`). The desktop shell now follows the
  target rail/tabs/stage-strip/central-surface composition, keeps the decision inspector
  contextual, restores WCAG-safe rail and status-chip contrast, and expands completion/read-only
  canvases when no decision value exists so actions do not overlap. Provider-free desktop shell,
  Inbox, and terminal Flow Complete checks passed locally; the full Python matrix, frontend
  checks, deterministic scenarios, adapter conformance, packaged UI browser, security checks,
  and build passed in CI. `W44-E1-S2-T2` was the next dependency-ready task and is now complete;
  `T3` is the next task.

- `W44-E1-S1-T2` is complete in PR #320 (merge `9792d8f5`). Mobile question, intervention,
  approval, and recovery actions now stay visible on `320x568` and `390x844` through one existing
  DOM control in a safe-area-aware action dock; provider-free geometry checks cover focusability,
  target size, clipping, and horizontal overflow. Frontend tests, UI contracts, docs/planning,
  Ruff, mypy, packaged UI browser, deterministic scenarios, adapter conformance, and build passed.
  `W44-E1-S2-T1` was the next dependency-ready task and is now complete; `W44-E1-S2-T2` is the
  next dependency-ready task and `T3` remains its direct successor.

- `W44-E1-S1-T1` is complete in PR #318 (merge `0645856b`). Runner/global launch leakage is
  removed from non-launch surfaces, Flow Complete keeps only its core-recommended primary
  actions, and narrow work-overview surfaces expose the decision before the stage strip. Focused
  browser/contract tests, the full frontend suite, docs/planning checks, Ruff, mypy, packaged UI
  browser, deterministic scenarios, adapter conformance, and build passed; desktop shell
  composition remained planned.

#### Slice W45-E1-S4 — QA evidence entry shape (`planned`)

Goal: keep QA-local command evidence truthful and directly resolvable when a runtime author
records multiple verification commands, without weakening the fail-closed upstream traceability
contract.

Dependencies: W45-E1-S3; the QA report contract, prompt pack, shared executable-command classifier,
and `CROSS-QA-UPSTREAM-EVIDENCE` validator.

Local tasks:

- `W45-E1-S4-T1` (done) Harden QA evidence authoring for one-command-per-entry outcomes.
  - Output: update the QA prompt/contract guidance and deterministic regression fixtures so each
    `EV-N` definition contains one executable command (or one exact upstream artifact path) and an
    explicit terminal outcome such as `pass`, `fail`, `no output`, or `exit code 0`. Prohibit a
    parent evidence bullet with nested command bullets, require explicit `pass` for bounded diff
    claims, and preserve fail-closed rejection of prose-only, source-only, circular, basename-only,
    and command-without-outcome evidence. Do not broaden upstream artifact roots or change target
    runtime behavior.
  - Scope: `prompt-packs/stages/qa/`, `contracts/documents/qa-report.md`, and focused QA
    cross-document/prompt fixtures and tests only; no adapters, UI, scenario, or public API changes.
  - Verification: the Claude medium QA shape with bounded diff and post-QA residue commands
    revalidates from `CROSS-QA-UPSTREAM-EVIDENCE` findings to zero; malformed nested, omitted-outcome,
    and prose-only variants remain rejected. Run focused QA validator/prompt tests, Ruff, mypy, and
    planning consistency.
  - Completion: PR #445 (merge `72049686`) adds explicit one-command-per-entry guidance to the QA
    run and repair prompts and document contract, updates prompt hash fixtures, and adds a nested
    evidence regression. Focused cross-document/prompt tests (`136` and `138` passed), Ruff, mypy,
    full CI, deterministic scenarios, adapter conformance, packaged UI browser, security, and build
    all pass. The original failed Claude medium bundle remains retained; a fresh Claude rerun is
    required to confirm the runtime now authors the corrected shape.

#### Slice W45-E1-S5 — workspace-relative upstream evidence resolution (`planned`)

Goal: accept valid work-item-relative QA evidence references while preserving fail-closed
traceability for missing, basename-only, source-only, circular, or out-of-scope paths.

Dependencies: W45-E1-S4; canonical work-item workspace path policy and the stage-output ownership
registry.

Local tasks:

- `W45-E1-S5-T1` (done) Resolve work-item-relative QA evidence references.
  - Output: update the `CROSS-QA-UPSTREAM-EVIDENCE` path resolver so a backticked reference such as
    `context/workspace-baseline.md` resolves against the selected work item's canonical context
    root, while full `workitems/<id>/...` references keep working. Do not accept basename-only,
    source-only, missing, QA-local circular, or path-traversal references.
  - Scope: `src/aidd/validators/cross_document_rules/qa_upstream.py` and focused validator fixtures
    and tests only; do not change runtime adapters, stage contracts, prompts, or UI behavior.
  - Verification: a positive fixture with an existing work-item-relative context path passes;
    missing, basename-only, source-only, circular, and traversal variants remain rejected with
    `CROSS-QA-UPSTREAM-EVIDENCE`. Run the focused cross-document validator suite, Ruff, mypy, and
    planning consistency checks.
  - Completion: PR #448 (merge `63c08ab0`) accepts existing upstream artifacts through both full
    workspace-relative paths and paths relative to the selected work item. Traversal-shaped
    backtick references are excluded from QA-local command evidence, while basename-only,
    source-only, missing, and QA-local paths remain fail-closed. Cross-document tests (`59 passed`),
    Ruff, mypy, full CI, deterministic scenarios, adapter conformance, packaged UI browser, and
    build all pass.

#### Slice W45-E1-S6 — nested-backtick executable evidence (`planned`)

Goal: recognize truthful executable verification commands whose shell payload contains nested
Markdown/code backticks while preserving fail-closed evidence validation.

Dependencies: W45-E1-S5; the shared implementation evidence classifier and implementation-report
contract.

Local tasks:

- `W45-E1-S6-T1` (done) Parse executable evidence with nested code delimiters safely.
  - Output: update the shared implementation evidence parser so a command wrapped as Markdown
    inline code can contain JavaScript or other nested backticks (for example a `bun -e` command
    using a template literal) and still be recognized as executable evidence with its terminal
    outcome. Preserve rejection of prose-only claims, command-without-outcome, malformed or
    unclosed code, and existing QA-local circular/upstream path rules.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py` and focused implementation evidence
    validator tests only; do not change runtime adapters, stage contracts, prompts, UI, or target
    behavior.
  - Verification: positive nested-backtick `bun`/`node` commands with `-> pass` are accepted;
    ordinary commands remain accepted; malformed or unclosed nested code, prose-only claims, and
    command-without-outcome remain rejected. Run focused implementation evidence tests, Ruff,
    mypy, and planning consistency checks.
  - Completion: PR #451 (merge `809c67be`) teaches the shared classifier to use the terminal
    outcome marker as the right boundary for nested code payloads, requires balanced delimiters and
    a known executable prefix, and keeps malformed/prose evidence fail-closed. Focused evidence
    and semantic implement tests (`70 passed`), the full validator suite (`352 passed`), Ruff,
    mypy, planning/docs checks, packaged UI browser, deterministic scenarios, adapter conformance,
    security, and build all pass. The failed Codex medium bundle remains retained for a fresh
    provider rerun from this clean main.

- `W45-E1-S6-T2` (done) Implement multiline heredoc command evidence recognition.
  - Output: extend the shared implementation evidence classifier so a valid multiline heredoc
    command wrapped in a Markdown inline code span (for example `uv run --frozen python - <<'PY' ...
    PY` followed by `-> pass`) is recognized as executable evidence with its terminal outcome.
    Preserve fail-closed rejection of prose-only, malformed, unclosed, and command-without-outcome
    evidence, including the nested-backtick cases covered by T1.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py` and focused implementation evidence
    validator tests only; do not change runtime adapters, stage contracts, prompts, UI, or target
    behavior.
  - Dependencies: W45-E1-S6-T1.
  - Verification: positive multiline Python/heredoc and ordinary commands with `-> pass` are
    accepted; malformed/unclosed multiline spans, prose-only claims, and command-without-outcome
    remain rejected. Run focused implementation evidence/semantic tests, Ruff, mypy, and planning
    consistency checks.
  - Completion: PR #455 (merge `5dfed7d6`) recognizes closed multiline inline-code/heredoc command
    spans using the executable prefix while preserving fail-closed malformed/prose handling. Focused
    evidence/semantic tests (`76 passed`), the full validator suite (`358 passed`), Ruff, mypy, and
    planning/docs checks (`50 passed`) are green. A fresh Claude Large rerun is required from this
    clean main; the prior blocked run remains retained as diagnostic evidence.

#### Slice W45-E1-S7 — tasklist verification mapping (`planned`)

Goal: make tasklist authoring unambiguous for the required per-task verification mapping so
providers do not put the only concrete command evidence in nested bullets that the canonical
parser cannot associate with a task id.

Dependencies: W45-E1-S6; the tasklist rich-card contract and canonical task-plan parser.

Local tasks:

- `W45-E1-S7-T1` (done) Clarify same-line verification mapping in tasklist prompts and repair guidance.
  - Output: update the tasklist run and repair prompt packs with an explicit same-line
    `- <task-id>: <concrete check/result>` example for the `Verification notes` section and a
    prohibition on leaving the mapped value empty with commands only in nested bullets. Preserve
    the existing rich-card, dependency, execution-mode, and fail-closed validation contracts.
  - Scope: `prompt-packs/stages/tasklist/run.md`, `prompt-packs/stages/tasklist/repair.md`,
    `tests/test_prompt_quality.py`, and `tests/fixtures/active_prompt_pack_hashes.json` only;
    do not change the task-plan parser, stage contracts, runtime adapters, or UI behavior.
  - Verification: prompt-quality tests assert the explicit same-line syntax and nested-only
    prohibition; active prompt hashes are updated; focused prompt tests, Ruff, mypy, and planning
    consistency checks pass. A tasklist with an empty `- TL-N:` mapping remains fail-closed.
  - Completion: PR #458 (merge `f2fec5b3`) added same-line verification mapping examples and
    nested-only prohibition to the tasklist run/repair prompts. Prompt-quality, packaging,
    docs/planning, Ruff, mypy, and PR CI checks passed. The subsequent Claude Large run exposed
    a separate aggregate implementation-report formatting gap, now tracked in W45-E1-S8-T1.

#### Slice W45-E1-S8 — aggregate verification evidence preservation (`planned`)

Goal: preserve complete, executable verification evidence when AIDD aggregates per-task
implementation reports, including reports whose Markdown bullets wrap across lines.

Dependencies: W45-E1-S7; aggregate implementation finalization and the shared implementation
evidence validator.

Local tasks:

- `W45-E1-S8-T1` (done) Preserve wrapped verification commands in aggregate implementation reports.
  - Output: update aggregate implementation-report rendering to join continuation lines with their
    top-level verification bullet so executable commands and terminal outcomes remain on one
    canonical evidence item. Preserve task ids, touched-file extraction, fail-closed validation,
    and existing single-line report behavior.
  - Scope: `src/aidd/core/implementation_finalization.py` and focused finalization/semantic tests
    only; do not change runtime adapters, stage contracts, prompts, UI behavior, or target code.
  - Verification: a wrapped multi-line command/result source report renders as one aggregate
    evidence bullet recognized by `has_implementation_command_evidence`; existing aggregate,
    validator, Ruff, mypy, and planning checks remain green.
  - Completion: PR #460 (merge `95561400`) joins wrapped top-level verification bullets before
    aggregate semantic validation and adds regression coverage for command/result continuations.
    Focused finalization tests (`6 passed`), semantic/report tests (`84 passed`), docs/planning
    checks (`50 passed`), Ruff, mypy, and PR CI passed. A subsequent Claude Large quality audit
    found a separate target-test async-generator cleanup defect; it is tracked in W45-E1-S9-T1.

#### Slice W45-E1-S9 — Large target regression-test cleanup (`done`)

Goal: ensure provider-authored async regression tests in Large live runs cleanly release
resources across every supported AnyIO backend before target quality is accepted.

Dependencies: W45-E1-S8; Large live implementation quality review and provider-free verification.

Local tasks:

- `W45-E1-S9-T1` (done) Require deterministic async-generator cleanup in live-authored regression tests.
  - Output: update the implementation-stage authoring guidance and focused quality fixtures so
    async-generator-backed tests use explicit cleanup (for example `aclosing`) when a hard
    disconnect can interrupt iteration. Preserve direct-ASGI coverage rationale, bounded target
    scope, and fail-closed verification evidence.
  - Scope: `prompt-packs/stages/implement/`, the implementation quality contract/fixtures, and
    focused prompt or semantic tests only; do not change runtime adapters, target repositories,
    stage APIs, or UI behavior.
  - Verification: a fixture containing an interrupted async generator is accepted only with
    explicit cleanup evidence; the exact malformed/unclosed-generator pattern is rejected or
    flagged, existing implementation evidence remains valid, and focused prompt/semantic,
    Ruff, mypy, and planning checks pass.
  - Completion: PR #462 (merge `8e1727d8`) adds implementation-stage guidance requiring explicit
    cleanup for interrupted async generators, clean asyncio/Trio evidence, and fail-closed handling
    of `ResourceWarning`, `PytestUnraisableExceptionWarning`, and unclosed-generator fixtures.
    Prompt/packaging tests (`87 passed`), docs/planning checks (`50 passed`), Ruff, mypy, and full
    required CI including packaged UI browser, deterministic scenarios, adapter conformance, and
    build passed.

#### Slice W45-E1-S10 — authored verification command fidelity (`done`)

Goal: keep authored verification commands and their terminal outcomes as one exact, executable
evidence item in provider-written implementation reports, so semantic validation can prove the
selected task's checks without confusing Markdown formatting with a missing command.

Dependencies: W45-E1-S9; implementation-stage verification guidance and the semantic implementation
evidence contract.

Local tasks:

- `W45-E1-S10-T1` (done) Define exact authored-command evidence formatting for implementation reports.
  - Output: update implementation-stage authoring guidance and focused semantic/prompt fixtures so
    every authored verification command is reproduced byte-for-byte, including its terminal outcome
    marker (for example, `` `uv run --frozen pytest -q tests/test_responses.py -> pass` ``), without
    inserting a Markdown code-span boundary between the command and the outcome. Preserve the
    existing ignored-workspace audit, wrapped-command, heredoc, nested-backtick, and fail-closed
    evidence rules.
  - Scope: `prompt-packs/stages/implement/run.md`, `tests/test_prompt_quality.py`, and focused
    implementation semantic/evidence fixtures or tests only; do not change runtime adapters,
    stage contracts, target repositories, or UI behavior.
  - Verification: prompt and semantic tests accept a report that preserves the exact authored
    command/result span and reject a report that splits the command from its outcome or substitutes
    a count-only/normalized command; existing valid and malformed evidence tests remain green. Run
    focused implementation/prompt tests, Ruff, mypy, and planning consistency checks.
  - Diagnostic evidence: Claude Large run
    `eval-live-012-claude-code-20260829T202033Z` reached the target implementation and passed its
    target checks, but stopped fail-closed because the authored `uv run --frozen pytest -q
    tests/test_responses.py -> pass` command was split across Markdown code-span delimiters in the
    provider report. No target product or UI defect was found; the backend-only target has no visual
    design surface.
  - Completion: PR #465 (merge `f3e9abbf`) keeps authored command/result text in one exact Markdown
    code span, adds exact-versus-split semantic regression coverage, updates the active prompt hash,
    and passes focused prompt/semantic/evidence tests (`163`), docs/planning checks (`50`), Ruff,
    mypy, full CI, deterministic scenarios, adapter conformance, packaged UI browser, CodeQL,
    dependency review, scorecard, and build. A fresh Claude Large rerun from this clean main is
    required; the failed bundle remains retained as diagnostic evidence.

- `W45-E1-S10-T2` (done) Accept hyphenated negative verification outcomes as observed terminal results.
  - Output: extend the shared implementation evidence result matcher so an executable verification
    command followed by a concrete hyphenated negative/clean marker such as
    `` `git status --ignored --short --untracked-files=all` -> no-test-cache-residue `` is
    recognized as a terminal outcome without weakening command or evidence requirements.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py` and focused semantic implementation
    tests only; do not change runtime adapters, stage orchestration, target repositories, or UI.
  - Verification: a report containing a command with `-> no-test-cache-residue` (and equivalent
    hyphenated `no-*` clean markers) validates; ambiguous arrow prose and command-without-outcome
    evidence remain fail-closed; existing valid/malformed evidence, Ruff, mypy, and planning checks
    pass.
  - Diagnostic evidence: fresh Claude Large run
    `eval-live-012-claude-code-20260829T230612Z` produced the intended bounded Starlette patch and
    passing target checks, but implement validation exhausted its repair budget on
    `SEM-UNVERIFIABLE-CHECK-CLAIM` because the truthful residue-cleanup result
    `-> no-test-cache-residue` was not recognized. The target is backend-only with no product UI or
    design surface; AIDD operator UI/API checkpoints remained green.
  - Completion: PR #468 (merge `a7b84f67`) recognizes concrete hyphenated `no-*`, `without-*`,
    `clean-*`, and `clear-*` terminal markers while retaining fail-closed ambiguous-arrow handling.
    Focused semantic/prompt tests (`125 passed`), full validator suite (`360 passed`), docs/planning/
    evidence checks (`88 passed`), Ruff, mypy, full CI, deterministic scenarios, adapter conformance,
    packaged UI browser, CodeQL, dependency review, scorecard, and build passed. A fresh Claude Large
    rerun from this clean main is required to verify the original lane.

- `W45-E1-S10-T3` (done) Keep explanatory verification caveats executable or outside the
  `Verification` section.
  - Output: update implementation-stage authoring guidance and focused semantic/prompt fixtures so
    every bullet in `Verification` that contains an outcome claim also contains the exact command
    or assertion that produced it; move non-command caveats (for example, resolver warnings) to
    `Risks`/`Follow-up`, or mark them as observations without pass/fail language. Preserve strict
    fail-closed handling for command-free outcome claims and all existing command/result formats.
  - Scope: `prompt-packs/stages/implement/run.md`, `tests/test_prompt_quality.py`, and focused
    implementation semantic/evidence tests only; do not change runtime adapters, stage contracts,
    target repositories, or UI behavior.
  - Verification: a report with a command-free `Verification` caveat such as `neither command
    failed` remains rejected; a report that places the same caveat in `Risks` or pairs it with the
    exact command/result is accepted; existing valid/malformed, wrapped, heredoc, nested-backtick,
    and hyphenated-outcome evidence remains green. Run focused semantic/prompt tests, Ruff, mypy,
    and planning consistency checks.

  - Diagnostic evidence: fresh Codex Large run
    `eval-live-012-codex-20260830T005635Z` produced the intended bounded Starlette runtime fix and
    passing target checks (`213 passed, 2 xfailed`, Ruff green), but implement validation exhausted
    its repair budget on `SEM-UNVERIFIABLE-CHECK-CLAIM` because the provider report placed the
    explanatory `neither command failed because of it` outcome claim in `Verification` without an
    executable command on the same evidence item. No target product or UI/design defect was found;
    the backend-only target's AIDD operator UI/API checkpoints remained green.
  - Completion: PR #471 (merge `bbfd0a9e`) adds explicit implementation-stage guidance, prompt
    contract coverage, and semantic regressions for command-free verification caveats. Focused
    semantic/prompt/packaging tests (`128 passed`), docs/planning checks (`50 passed`), Ruff, mypy,
    deterministic scenarios, adapter conformance, packaged UI browser, security checks, and build
    passed. A fresh Codex and Claude Large rerun from this reconciled main is required to validate
    the original lane.

#### Slice W45-E1-S11 — Large target compatibility and bounded workspace (`done`)

Goal: prevent a Large provider patch from removing existing compatibility consumers or carrying
tool-generated dependency-lock churn into an otherwise bounded target change.

Dependencies: W45-E1-S10; Large implementation/review evidence from
`eval-live-012-codex-20260830T025946Z`.

Local tasks:

- `W45-E1-S11-T1` (done) Require compatibility-preserving target edits and clean bounded diffs.
  - Output: update implementation-stage authoring guidance and focused prompt/quality fixtures so
    providers must search all existing consumers before renaming/removing a shared helper, retain a
    compatibility symbol or migrate every consumer with coverage, run full target collection
    including unchanged consumers, and restore tool-generated `uv.lock` changes unless dependency
    updates are explicitly in scope. Preserve the selected Starlette exception-group fix and all
    existing command/result evidence rules.
  - Scope: `prompt-packs/stages/implement/run.md`, implementation quality/prompt fixtures, and
    focused semantic or review-contract tests only; do not change runtime adapters, stage APIs,
    target repositories, or UI behavior.
  - Verification: prompt/quality fixtures require consumer search, full collection evidence, and
    lockfile cleanup; reports that claim bounded scope while listing `uv.lock`, omit an unchanged
    consumer collection check after removing a symbol, or leave an import failure unresolved are
    rejected. Existing valid implementation evidence, nested/heredoc/wrapped command formats, and
    fail-closed outcome handling remain green. Run focused prompt/semantic tests, docs/planning,
    Ruff, and mypy.
  - Diagnostic evidence: Codex Large run
    `eval-live-012-codex-20260830T025946Z` produced the intended Starlette runtime behavior and
    focused checks (`213 passed, 2 xfailed`, dedicated matrix `12 passed`, Ruff green), but review
    rejected the workspace because removing `collapse_excgroups` broke the existing WSGI test
    import and the target diff included an unrelated `955`-addition/`685`-deletion `uv.lock`
    rewrite. AIDD operator UI/API checkpoints were green; the backend-only target has no product UI
    or visual design surface.
  - Acceptance: the guidance makes compatibility-consumer search and full collection a required
    implementation step, keeps `uv.lock` out of the bounded target diff by default, and adds
    regression fixtures for both review findings without weakening runtime-agnostic core behavior.
  - Completion: PR #474 (merge `365eb46a`) adds the implementation guidance, semantic guards, and
    prompt/quality regressions. Focused semantic/prompt/hash tests (`133 passed`), full validator
    tests (`366 passed`), docs/planning checks (`50 passed`), Ruff, mypy, deterministic scenarios,
    adapter conformance, packaged UI browser, and build all passed. Fresh Codex and Claude Large
    reruns remain required; no clean Large success is claimed by this task.

#### Slice W45-E1-S12 — explicit verification-only task mode (`done`)

Goal: prevent verification-only task cards from silently inheriting repository-change semantics,
so completed prerequisite checks can be recorded without triggering a false no-op failure during
implementation.

Dependencies: W45-E1-S11; rich task-plan parsing and implementation evidence validation.

Local tasks:

- `W45-E1-S12-T1` (done) Require an explicit execution mode for verification-only task cards.
  - Output: extend task-plan parsing and tasklist validation so a card that explicitly describes a
    verification-only task/output or an intentional absence of task-local repository edits must
    declare `Execution mode: verification-only`; otherwise emit a located, actionable grammar
    finding. Preserve the backward-compatible `repository-change` default for ordinary cards and
    do not infer evidence-only behavior from a title alone.
  - Scope: `src/aidd/core/task_plan.py`, `tests/core/test_task_plan.py`,
    `tests/validators/test_semantic_tasklist.py` only; do not change runtime adapters, stage APIs,
    implementation evidence rules, target repositories, or UI behavior.
  - Verification: explicit verification-only cards parse as `TaskExecutionMode.VERIFICATION_ONLY`;
    cards whose body says `verification-only task` or `no task-local repository edits` without the
    field fail with a located execution-mode finding; ordinary cards and explicit repository-change
    cards retain existing behavior. Run focused task-plan/tasklist tests, full validator tests,
    Ruff, mypy, and planning consistency checks.
  - Diagnostic evidence: Claude Large run
    `eval-live-012-claude-code-20260830T070220Z` generated TL-3/TL-4 verification-only cards
    without the explicit execution-mode field. The implementation stage then inherited
    `repository-change`, rejected truthful `- none` touched-files evidence as a no-op, exhausted
    bounded repairs, and stopped before review/QA. The target Starlette patch and focused checks
    passed; no target product or UI/design defect was found.
  - Completion: PR #477 (merge `c4fb1953`) makes task-plan parsing fail closed with a located,
    actionable missing-field finding when verification-only semantics appear without an explicit
    `Execution mode: verification-only`. Ordinary cards, title-only wording, and explicit
    `repository-change` cards retain their existing behavior. Focused task-plan/tasklist tests
    (`59 passed`), full validator tests (`367 passed`), docs/planning checks (`50 passed`), Ruff,
    `mypy src`, deterministic scenarios, adapter conformance, packaged UI browser, security, and
    build checks are green. Fresh Codex and Claude Large reruns remain required; no clean Large
    success is claimed by this task.

#### Slice W45-E1-S13 — wrapped executable verification commands (`done`)

Goal: keep implementation evidence fail-closed for prose while accepting valid standard command
wrappers used by provider-authored verification, including a `perl` timeout wrapper around an
`uv run` test command.

Dependencies: W45-E1-S12; fresh Codex Large diagnostic
`eval-live-012-codex-20260830T091915Z`.

Local tasks:

- `W45-E1-S13-T1` (done) Recognize supported command wrappers in implementation evidence.
  - Output: extend the shared implementation-evidence command matcher and focused fixtures so
    valid `perl -e ... -- <command>` wrappers with an observed result are accepted as executable
    evidence, while prose, malformed quoting, and unknown wrappers remain rejected. Preserve all
    existing command/result, heredoc, nested-backtick, negative-outcome, and fail-closed rules.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py`,
    `tests/validators/test_implementation_evidence.py`, and focused semantic implementation
    fixtures only; do not change runtime adapters, stage APIs, target repositories, or UI
    behavior.
  - Verification: a backticked `perl -e 'alarm 4; exec @ARGV' -- uv run ...` command with
    `-> fail (exit code 142)` is accepted; an unclosed/malformed wrapper and command-free outcome
    prose remain rejected. Run focused evidence/semantic tests, full validator tests, Ruff, mypy,
    and planning consistency checks.
  - Diagnostic evidence: Codex Large run
    `eval-live-012-codex-20260830T091915Z` added correct TL-1 red-regression coverage and
    recorded the bounded watchdog command, but the implementation validator rejected the report
    at `SEM-UNVERIFIABLE-CHECK-CLAIM` because `perl` was not recognized as a known executable.
    The target Starlette code was not changed and no target product/UI defect was found.
  - Acceptance: valid wrapped command evidence reaches semantic validation without weakening
    fail-closed handling of prose or malformed commands; the fresh Large lane can progress to
    the next authored target task.
  - Completion: PR #480 (merge `f61f414a`) adds `perl` to the shared executable matcher and
    implementation command pattern, with focused coverage for passing/failing watchdog wrappers
    and rejection of malformed or unknown wrappers. Evidence/implementation tests (`89 passed`),
    full validator tests (`372 passed`), planning/docs (`50 passed`), Ruff, mypy, deterministic
    scenarios, adapter conformance, packaged UI browser, and build checks are green. Fresh
    Codex and Claude Large reruns remain required; no clean Large success is claimed by this task.

#### Slice W45-E1-S14 — concrete tasklist verification commands (`done`)

Goal: fail early when provider-authored tasklists carry unresolved command placeholders, so
implementation evidence cannot inherit a command that cannot be executed or reproduced.

Dependencies: W45-E1-S13; tasklist semantic validation and implementation evidence validation.

Local tasks:

- `W45-E1-S14-T1` (done) Reject unresolved verification-command placeholders in tasklists.
  - Output: extend tasklist semantic validation and focused fixtures so inline verification
    commands containing unresolved angle-bracket placeholders such as `<test_name>` fail with a
    located, actionable finding. Preserve legitimate shell redirection/process-substitution syntax,
    authored command fidelity, and existing fail-closed checks for prose or malformed commands.
  - Scope: `src/aidd/validators/semantic_rules/tasklist.py`,
    `tests/validators/test_semantic_tasklist.py`, and tasklist contract guidance only; do not
    change runtime adapters, stage APIs, target repositories, or UI behavior.
  - Verification: a tasklist verification note containing `pytest tests/test_responses.py::<test_name>`
    is rejected before implementation with a concrete replacement message, while a concrete
    test command and shell forms such as `<(printf x)` remain accepted. Run focused tasklist
    semantic tests, full validator tests, Ruff, mypy, and planning consistency checks.
  - Diagnostic evidence: fresh Claude Large run
    `eval-live-012-claude-code-20260830T122148Z` authored a verification-only TL-3 note with
    `uv run --frozen pytest -q tests/test_responses.py::<test_name>`. The tasklist stage passed,
    but implement failed closed on `SEM-UNVERIFIABLE-CHECK-CLAIM` because the unresolved command
    placeholder could not be preserved as executable evidence. The target Starlette patch and
    focused tests passed; no target product or UI/design defect was found.
  - Acceptance: unresolved command placeholders are caught and repairable at tasklist, before
    implementation consumes repair budget; concrete commands and valid shell syntax remain
    backward compatible.
  - Completion: PR #482 (merge `683aff95`) adds the tasklist semantic guard and contract guidance;
    the focused tasklist suite (25 passed), full validator/docs/planning checks (424 passed), Ruff,
    mypy, CI, adapter conformance, deterministic scenarios, packaged UI browser, and build checks
    are green. The next action is a fresh Codex and Claude Large rerun from this clean main.

#### Slice W45-E1-S15 — dependency-aware implementation scope (`done`)

Goal: keep generated implementation cards reviewable when a regression task may legitimately
require a production correction, without weakening the task-local mutation boundary.

Dependencies: W45-E1-S14; tasklist decomposition, dependency ordering, and task-local diff
validation.

Local tasks:

- `W45-E1-S15-T1` (done) Implement tasklist guidance and coverage for coupled behavior-and-regression
  work.
  - Output: update the tasklist prompt/contract guidance and focused fixtures so a tasklist does
    not split a behavior fix from the tests needed to validate that fix when the test card could
    require production edits. The generated plan must either keep the coupled paths in one bounded
    card or make the production correction an explicit dependency-ready card before its tests.
  - Scope: tasklist prompt/contract guidance, deterministic tasklist fixtures, and focused
    decomposition tests only; preserve fail-closed implementation scope validation and do not
    change runtime adapters, stage APIs, target repositories, or UI behavior.
  - Verification: a coupled behavior-plus-regression fixture yields dependency-ordered cards whose
    implementation scopes can complete without a later tests-only card needing an unplanned
    production edit; an out-of-scope edit still fails closed with the existing scope finding.
  - Diagnostic evidence: fresh Codex Large run
    `eval-live-012-codex-20260830T141056Z` completed TL-1 and TL-2, then selected TL-3 (tests only)
    and added a required `starlette/responses.py` correction while writing regression tests. The
    implementation validator correctly stopped on `SEM-TASK-SCOPE-MISMATCH`; the target checks
    passed but the flow could not reach review/QA. This is a tasklist decomposition/authoring gap,
    not a target product or UI defect.
  - Acceptance: coupled tasklist output makes the production correction an explicit bounded task
    or includes the path in the same task; dependency order remains deterministic; scope validation
    remains fail-closed for genuinely unrelated paths.
  - Completion: PR #485 (merge `80e4212a`) keeps coupled behavior corrections and regression
    coverage in one bounded task or explicit dependency order. It adds the corresponding tasklist
    contract/prompt/repair guidance, a deterministic coupled-scope fixture, parser coverage, and
    prompt/hash checks. Focused tasklist/validator/docs/planning/packaging tests (`202 passed`),
    Ruff, mypy, full CI, adapter conformance, deterministic scenarios, packaged UI browser, and
    build checks are green. The next action is a fresh Codex and Claude Large rerun from this
    clean main; no target product or UI/design defect was found in the diagnostic run.

#### Slice W45-E1-S16 — inline compound-command verification evidence (`done`)

Goal: accept valid shell compound verification commands when a provider keeps the terminal
outcome marker inside the same Markdown code span, while continuing to reject prose and malformed
command evidence.

Dependencies: W45-E1-S15; shared implementation verification evidence matcher and Large live
quality validation.

Local tasks:

- `W45-E1-S16-T1` (done) Accept inline result markers on shell compound commands.
  - Output: update the shared implementation evidence matcher so a valid command such as
    `` `if git diff --name-only | rg -q ...; then exit 1; else exit 0; fi -> pass` `` is
    recognized as executable evidence when its outcome marker is inside the code span. Preserve
    exact command/result handling, nested and multiline command support, fail-closed malformed
    wrappers, and shell-like prose rejection.
  - Scope: `src/aidd/validators/semantic_rules/evidence.py`,
    `tests/validators/test_implementation_evidence.py`, and focused semantic implementation
    fixtures only; do not change runtime adapters, stage APIs, prompts, target repositories, or
    UI behavior.
  - Verification: focused evidence tests cover inline compound-command pass/fail markers,
    existing outside-span markers, malformed compounds, and prose; semantic implementation
    validation accepts the valid inline command and rejects non-command claims. Run focused
    validator tests, full validator tests, Ruff, mypy, and planning/docs consistency checks.
  - Diagnostic evidence: Codex Large run `eval-live-012-codex-20260830T165848Z` produced the
    intended bounded Starlette runtime change and all target checks passed (`205 passed, 2
    xfailed`, supplemental `25 passed`, Ruff green), but AIDD stopped at implementation TL-4
    because the valid compound command `if ...; then ...; fi -> pass` was placed inside one code
    span and the matcher did not recognize it as executable evidence. The target is backend-only;
    no product UI/design defect was found and AIDD operator UI/API checkpoints remained green.
  - Acceptance: valid inline shell compound commands are accepted with their observed outcome,
    malformed or prose lookalikes remain rejected, and the same Large flow can reach review/QA
    without weakening fail-closed verification semantics.
  - Completion: PR #488 (merge `c1eeaafa`) added a conservative terminal result-marker matcher
    used only when the command body is a valid shell compound expression. Focused evidence and
    semantic implementation tests (`92 passed`), full validator tests (`376 passed`), Ruff, mypy,
    full CI, adapter conformance, deterministic scenarios, packaged UI browser, and build checks
    are green. A fresh Codex+Claude Large rerun is required from this clean main; no clean
    two-provider Large success is claimed yet.

#### Slice W45-E1-S17 — tasklist dependency explanation parsing (`done`)

Goal: keep the core task dependency graph aligned with the machine-readable dependency clause in
provider-authored tasklists, so explanatory prose cannot introduce false dependencies or fail the
task-aware checkpoint.

Dependencies: W45-E1-S16; task-plan parsing, Task Workspace read model, and task-flow checkpoint
validation.

Local tasks:

- `W45-E1-S17-T1` (done) Implement dependency-clause parsing that ignores explanatory prose after the
  machine-readable dependency list while preserving explicit task ids, deterministic ordering,
  and fail-closed handling of malformed or unknown dependencies.
  - Output: update the core task-plan parser and focused parser/checkpoint tests so a line such as
    `TL-4: TL-2 — same dependency reasoning as TL-3` yields only `TL-2` in the canonical ledger,
    while `TL-4: TL-2, TL-3` retains both dependencies and unknown ids remain rejected.
  - Scope: `src/aidd/core/task_plan.py`, `src/aidd/harness/task_flow_checkpoint.py` only through
    focused tests; do not change runtime adapters, stage contracts, target repositories, or UI
    behavior.
  - Verification: parser, task read-model, and task-flow checkpoint tests cover em-dash and
    en-dash explanations, explicit multi-id clauses, punctuation, malformed clauses, and public
    dependency-drift prevention. Run focused core/harness tests, full validator/planning tests,
    Ruff, and mypy.
  - Diagnostic evidence: fresh Claude Large run
    `eval-live-012-claude-code-20260830T203136Z` generated a valid tasklist with `TL-4: TL-2 —
    same dependency reasoning as TL-3`, but the core parser included `TL-3` from the explanation;
    the installed public Task Workspace then disagreed with the checkpoint parser and stopped
    fail-closed on `dependency-drift:TL-4`. The target repository was not modified and has no
    product UI/design surface; AIDD operator UI/API checkpoints remained green.
  - Acceptance: machine-readable dependency clauses and checkpoint/public projections agree for
    explanatory tasklist prose; explicit dependencies remain intact, unknown/malformed clauses
    remain fail-closed, and no target runtime or UI behavior changes.
  - Completion evidence: PR #491 (merge `9faa84ae`) parses only the machine-readable clause before
    an em/en-dash rationale. Core, Task Workspace, and checkpoint regressions cover explanatory task
    ids, explicit multi-id dependencies, punctuation, and fail-closed unknown ids; focused tests,
    validator tests, Ruff, mypy, and full CI are green.
