# Project quality and workflow-conformance audit — 2026-09-05

Implementation follow-up:
[`project-quality-remediation-plan-2026-09-05.md`](project-quality-remediation-plan-2026-09-05.md).

## Executive decision

At revision `f2819535fa3142002a173fdd31fd5e0d6ab69763`, AIDD is a **strong alpha with a
sound product architecture, but it is not beta-ready**. The core eight-stage happy path and the
incremental task-execution vertical slice work on the current revision. The main readiness risk is
not the absence of engineering controls; it is that several controls and eval reports currently
overstate what they have actually observed.

The judgment-based score is **73/100 (confidence: medium-high)**:

| Plane | Score | Decision summary |
| --- | ---: | --- |
| Code-base quality | **74/100** | Strong typing, linting, CI, tests, and core lifecycle design; three reproduced exception-safety failures and concentrated complexity prevent a higher score. |
| Alignment with product goals | **80/100** | Eight of thirteen user stories have strong implementation evidence; five are materially partial. |
| Conformance to the declared workflow | **64/100** | The current eight-stage/task happy path passes, but repair, interview, provenance, and failure-classification evidence is not yet trustworthy enough for a beta claim. |
| Weighted overall (`40% / 30% / 30%`) | **73/100** | Continue incremental hardening; do not rewrite the system, and do not promote it to beta until the P1 gates below are closed. |

The score is an audit judgment, not an ISO certification. It is deliberately capped by observed
failure behavior: a large green suite does not compensate for a stage that can remain stranded in
`validating` until explicit recovery/reconciliation, a task ledger that can remain `executing`, or
a PASS bundle that contains false repair claims and dangling provenance references.

Finding distribution: **0 P0, 7 P1, 8 P2, and 2 P3**.

## Recommended product decision

1. Keep the architecture and the document-first direction. A rewrite is not justified.
2. Treat evidence truth and exception-safe terminalization as beta blockers; reconcile artifact
   ownership before further contract or prompt expansion.
3. Continue calling the current line alpha. This agrees with `README.md` and the future beta gate in
   `docs/product/user-stories.md`.
4. Fix the smallest vertical reliability slices first; only then spend effort on broad module
   decomposition and additional live-provider runs.

## Scope and baseline

The audit covered:

- the product statement, all `US-01` through `US-13`, the target architecture, and the declared
  `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa` flow;
- core orchestration, validators, maintained adapters, CLI/operator UI, harness, evals, contracts,
  prompt packs, deterministic scenarios, CI, release, and security automation;
- current source behavior through static checks, focused negative-path reproduction, focused test
  lanes, one fresh deterministic full-flow execution, and inspection of retained historical live
  reports;
- maintainability indicators across 227 Python source files and 83,881 physical source lines;
  219 files/76,054 lines under the default `tests/` suite plus 71 files/10,036 lines under
  `browser_tests/` (290 files/86,090 lines total); and 25 packaged JavaScript files with 15,562
  lines.

Audit runtime:

- repository revision: `f2819535fa3142002a173fdd31fd5e0d6ab69763`;
- host: Darwin arm64;
- Python `3.13.7`, Node `25.9.0`, uv `0.8.22`;
- worktree was clean before the report was added;
- the default Python suite was executed, but the separate `browser_tests/` Chromium lane was not
  rerun in this audit; its CI definition and retained reports were inspected;
- no current real-provider run was launched, because that would require external credentials and
  would not be a read-only assessment. Existing Codex/Claude evidence was assessed for content,
  revision freshness, and retrievability.

## Assessment method

The quality model is adapted from the product-quality framing in
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html), which defines nine product-quality
characteristics for specification and evaluation. Secure-delivery checks use the high-level
practice model in [NIST SP 800-218 SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final).
Repository-specific criteria were added because AIDD's primary promise is orchestration evidence,
not merely a callable Python API.

The dimensions below guide the ordinal judgment; they are not presented as independently measured
subscores. The only arithmetic aggregation is the visible plane formula:
`74 * 0.40 + 80 * 0.30 + 64 * 0.30 = 72.8`, rounded to 73.

### Scoring dimensions

| Dimension | Weight within code/flow judgment | What was assessed |
| --- | ---: | --- |
| Functional correctness and reliability | 20% | Terminal-state safety, failure preservation, validation behavior, repair, resume, and task execution. |
| Architecture and flexibility | 15% | Runtime-neutral core, adapter boundaries, ownership model, extensibility, and coupling. |
| Maintainability | 15% | Complexity, file/function size, dead compatibility code, cohesion, and planning-source hygiene. |
| Verification and testability | 15% | Negative paths, executable contracts, CI lanes, scenario assertions, and false-positive resistance. |
| Declared-flow conformance | 20% | Evidence for every stage and control loop, rather than only a happy-path exit code. |
| Observability and auditability | 10% | Raw logs, identifiers, provenance, bundle completeness, immutable evidence, and classifications. |
| Security and delivery safety | 5% | Dependency checks, static security checks, permissions, pinned CI actions, package/release gates. |

### Evidence levels

- **E4 — observed now:** reproduced or executed on the audited revision with inspectable artifacts.
- **E3 — source-confirmed/executable:** current-revision implementation or contradiction is
  directly visible in source; focused automated tests or CI definitions are included where
  applicable.
- **E2 — retained claim:** a tracked report or indirect test exists, but raw evidence is absent or
  belongs to another revision.
- **E1 — declared:** documentation or capability metadata only.
- **E0 — contradicted:** the observed result conflicts with the declared behavior.

### Priority meanings

- **P0:** immediate catastrophic security, data-loss, or system-wide correctness failure.
- **P1:** blocks a beta/readiness claim or can silently corrupt lifecycle/evidence truth.
- **P2:** significant reliability, extensibility, or maintainability debt that should be scheduled
  before broad adoption.
- **P3:** documentation, governance, or defense-in-depth improvement with a bounded present impact.

## What is already strong

### The product architecture is coherent

- The canonical stage graph is compact and runtime-neutral in `src/aidd/core/stages.py`.
- Direct imports from `aidd.core` to `aidd.adapters` were not found. Adapter requests and outcomes
  are expressed through shared domain types.
- Markdown contracts are not presentation-only. The registry and structural/semantic validators
  consume them, and the output publication path uses ownership-aware discovery and an atomic
  staging/swap operation.
- Validation and repair transitions are predominantly fail-closed. Adapter failure, unresolved
  questions, invalid documents, and exhausted repair budget normally prevent downstream
  progression.

### Incremental implementation is the strongest vertical slice

`US-13` has a durable task plan, dependency validation, ledger, per-task attempts, repository
baseline/diff evidence, fail-fast behavior, resume support, aggregate finalization, and review/QA
eligibility checks. A fresh deterministic run on this revision executed `TL-1`, `TL-2`, and `TL-3`
once each in dependency order, finalized the implementation, then completed review and QA.

### Engineering discipline is above a typical alpha baseline

- Ruff and strict mypy pass; nearly all source functions are annotated.
- The CI matrix covers Python 3.12 through 3.14, JavaScript syntax/tests, Python tests, adapter
  conformance, deterministic scenarios, packaged-browser tests, and build gating.
- GitHub Actions are SHA-pinned. Separate dependency review, CodeQL, and OpenSSF Scorecard jobs
  exist.
- Release automation builds, publishes, and verifies `pipx` and `uv tool` installation.
- Core accountability records prompt/resource/repository hashes, configuration, runtime identity,
  attempt artifacts, and comparisons.

### Product scope is generally honest

`README.md` calls the project prerelease alpha, warns about broad working-tree access, and excludes
production-ready unattended multi-user automation. This honesty materially reduces product-risk
even where implementation and evidence remain partial.

## Prioritized findings

| ID | Priority | Finding | Primary impact |
| --- | --- | --- | --- |
| F-01 | P1 | Invalid stream bytes can kill a reader thread while the adapter returns success with an empty log. | Reliability, US-06, diagnosis |
| F-02 | P1 | Document read/parse failures can strand a stage in `validating` until explicit recovery; eligibility can report the same input as runnable. | Lifecycle truth, US-03/04 |
| F-03 | P1 | Task failure finalization can mask the primary executor error and leave the task ledger `executing`. | US-13 recovery |
| F-04 | P2 | Canonical ownership rules contradict stage contracts and repair/intervention prompts. | Document-first authority |
| F-05 | P1 | Eval reporting mistakes independent task attempts for self-repair and labels unexecuted probes as observed. | Evidence integrity, US-07/10 |
| F-06 | P1 | Deterministic scenario declarations are not executable acceptance rules; required interview/resume can be absent in a PASS. | Workflow proof, US-04/05/07 |
| F-07 | P1 | PASS bundles have incorrect/dangling provenance and omit evidence needed to re-audit the verdict. | Accountability and reproducibility |
| F-08 | P1 | Setup infrastructure failure is reclassified as a synthetic validation finding. | Failure triage and eval truth |
| F-09 | P2 | A maintained large deterministic lane is broken, and two resilience lanes depend on an implicit `python` executable. | Portability and release evidence |
| F-10 | P2 | Adapter conformance checks declarations, not behavior; generic-cli discards captured structured JSONL. | US-01/07/08/10 |
| F-11 | P2 | US-12's unconditional bounded-execution wording conflicts with documented full-access behavior; current scenarios prove mainly traceability. | US-12 product claim |
| F-12 | P2 | Provider-specific policy/configuration remains in core/central registries. | Runtime neutrality and extension cost |
| F-13 | P2 | Complexity and responsibility are concentrated in a few modules, including an unreachable legacy process-execution island. | Maintainability and change risk |
| F-14 | P2 | The canonical planning sources are too large and do not roll up parent status from local tasks. | Planning truth and reviewability |
| F-15 | P2 | Current live and UX acceptance evidence is incomplete or revision-stale for changed workflow paths. | Beta decision confidence |
| F-16 | P3 | Architecture wording and smaller audit documents have drifted from current contracts/product stories. | Documentation consistency |
| F-17 | P3 | Assurance breadth is not governed by a coverage threshold, formatter gate, or JavaScript CodeQL lane. | Consistency and defense in depth |

## Detailed findings

### F-01 — stream decoding can silently lose evidence and still succeed (`P1`, E4)

`src/aidd/adapters/process_supervisor.py:27-38` launches subprocess pipes in text mode without an
explicit encoding or error policy. `src/aidd/adapters/subprocess_streaming.py:41-57` always places
an end-of-stream sentinel in `finally`, but it does not send a reader exception to the main loop.
The main loop at `:159-237` therefore cannot distinguish clean EOF from a decoder failure.

Reproduction: a child wrote `before\n`, byte `0xff`, `after\n`, and exited with code zero. The daemon
reader raised `UnicodeDecodeError`; the returned adapter result still indicated success/zero, and
stdout, `runtime.log`, and its raw source were empty.

This directly violates the requirement that raw runtime logs remain available. The correct design
is binary capture as the authority, an explicit incremental decoding policy for display, and a
reader-error event that the supervisor must reconcile before returning success.

### F-02 — validation exceptions can strand lifecycle state (`P1`, E4)

`validate_required_document_existence` in `src/aidd/validators/structural.py:128-157` treats
`Path.exists()` as sufficient. The next layer reads the path as UTF-8 Markdown and can raise for a
directory, unreadable file, invalid UTF-8, or malformed frontmatter
(`src/aidd/validators/document_loader.py:108-188`). These failures are not normalized into
validation findings by `src/aidd/core/stage_outputs.py:274-332`.

The stage runner persists `validating` before discovery/interview/validation at
`src/aidd/core/stage_runner.py:868-948`, but this region has no exception-safe terminalization.
Two reproductions were observed:

- an adapter created `plan.md` as a directory;
- a successful adapter outcome left invalid UTF-8 in `answers.md`.

Both raised out of orchestration after the transition, leaving durable status `validating`; the
first case had no canonical validator report or repair transition. Relatedly,
`src/aidd/core/stage_graph.py:186-195` can declare an input eligible using `exists()` before
preflight rejects it as unreadable/non-file.

Every input/output read failure must become either a located validation finding with a legal
repair transition or a durable failed terminal state with exception evidence. No exception after a
persisted transition may leave a non-running process in `executing` or `validating`.

### F-03 — task recovery is not exception-safe (`P1`, E4)

`ImplementationExecutionService.run_task` catches an executor exception, but its recovery calls
`_complete_task_execution` before it can mark the ledger failed
(`src/aidd/core/implementation_service.py:326-346`). That helper reads and copies the current
implementation report before the terminal ledger update (`:159-198`, with terminalization later at
`:235-260`).

Reproduction: the executor wrote invalid UTF-8 to `implementation-report.md` and raised a
`RuntimeError`. Recovery then raised `UnicodeDecodeError`, masked the primary exception, and left
the ledger entry `executing`.

Terminalization must be best-effort and monotonic: preserve the original exception as the primary
cause, quarantine malformed candidate evidence, persist a failed attempt and ledger state, and add
secondary collection errors without replacing the cause.

### F-04 — document ownership is internally contradictory (`P2`, E3)

The canonical matrix in `contracts/documents/ownership-matrix.md` and the target architecture at
`docs/architecture/target-architecture.md:370-387` say that `stage-result.md` and
`validator-report.md` are AIDD-owned workflow records. The current run prompts agree and explicitly
tell the runtime not to write them.

The following sources say the opposite:

- `docs/architecture/document-contracts.md:58-65` says the runtime writes a stage-result draft;
- `contracts/documents/stage-result.md:8-10` says the runtime writes it;
- all eight `contracts/stages/*.md` call it a runtime-authored summary draft;
- repair prompts still instruct the model to repair/update both workflow records, for example
  `prompt-packs/stages/plan/repair.md:10-31,62-105`;
- intervention prompts instruct the runtime to update `stage-result.md`, for example
  `prompt-packs/stages/plan/intervention.md:9-16`.

`tests/test_docs_consistency.py:185-218` asserts both sides, so the green test preserves the
contradiction rather than detecting it. Core output protection mitigates canonical corruption, but
the contradictory prompts still waste runtime work, create unexpected protected candidates, and
make repair behavior less predictable.

Choose one rule — the implemented AIDD-owned rule is the coherent choice — and update the
architecture, document/stage contracts, repair/intervention prompts, prompt hashes, and semantic
consistency tests together. The runtime registry should also derive from, or be exhaustively
checked against, the canonical ownership model rather than relying on filename sets hard-coded in
`src/aidd/core/stage_registry.py:27-28`.

### F-05 — task attempts are reported as self-repair (`P1`, E4)

`src/aidd/evals/stage_timing.py:574-592` treats attempts after attempt one as repair attempts.
At `:702-783`, a successful multi-attempt stage becomes a successful repair and the catalog's
probes are projected as observed.

In the fresh `AIDD-DETERMINISTIC-004` run, the implement stage has three global attempts because
three independent tasks ran. Every task has one attempt, no repair reason, and no resume. The eval
bundle nevertheless reports:

- two repair-history rows with repair reason `n/a`;
- `repair_success: true`;
- 24 deterministic probes with `evaluation_source: run-artifact-observation`;
- a successful `implement-resume-non-repair-accounting` probe even though no resume occurred.

Introduce a durable `attempt_kind` such as `initial`, `repair`, `resume`, `task`, and
`finalization`. Repair reports must be derived from actual repair lineage and executed fault
injections, never from ordinal attempt count or a probe catalog.

### F-06 — deterministic scenario semantics are not enforced as executable gates (`P1`, E4)

`harness/scenarios/deterministic/minimal-python-task-execution.yaml:53-54` declares
`interview.required: true`. The fresh PASS run contains `- none` in every questions/answers file;
the fixture constants at `harness/fixtures/minimal-python/aidd_fixture_runtime.py:28-29` guarantee
that result. `src/aidd/harness/deterministic_eval.py:222-323` does not enforce a
`blocked -> answer -> resume` sequence.

The same scenario's `verify.pass_conditions` are not represented by the scenario model and are not
executed. Commands check mostly for file existence, while those conditions additionally promise
dependency order, task-local attempts/diffs, aggregate finalization, and review/QA evidence.
Separately, the scenario matrix at `docs/e2e/scenario-matrix.md:150-152` overclaims repair,
blocking interview resume, and fail-fast coverage for this lane.

Convert scenario acceptance into typed, executable assertions with durable evidence. When
`interview.required` is true, PASS must require a blocking question, persisted answer, distinct
resume attempt, unchanged repair budget, and successful continuation. Conditions that are not
executable should be labelled notes, not gates.

### F-07 — eval PASS bundles are not provenance-complete (`P1`, E4)

The fresh DET-004 bundle demonstrates the first three related integrity failures below; static
inspection of error persistence shows the fourth:

1. `harness-metadata.json` references `feature-selection.json`, but the file is absent.
2. `aidd_run_id` is set to the eval ID; the actual product run is
   `run-20260905T061853Z`.
3. top-level `runtime.log` is harness/AIDD command output. Raw per-attempt runtime logs, canonical
   per-stage validator reports, and task/finalization evidence remain only in the mutable
   harness-cache working copy.
4. error paths discard partial setup/verify transcripts even though the runner attaches completed
   commands to the exception.

Relevant construction and persistence paths include
`src/aidd/harness/eval_reports.py:183-249`,
`src/aidd/harness/eval_reports.py:653-670`,
`src/aidd/harness/eval_reports.py:761`,
`src/aidd/harness/eval_reports.py:790`,
`src/aidd/harness/eval_reports.py:803-810`,
`src/aidd/harness/eval_reports.py:886`,
`src/aidd/harness/runner.py:44-54`,
`src/aidd/harness/runner.py:100-149`, and
`src/aidd/harness/result_bundle.py:360-361`.

Make a bundle integrity validator part of verdict finalization. PASS must fail closed on a dangling
reference, ambiguous eval/product identity, missing required raw evidence, digest mismatch, or
missing scenario-specific report. The self-contained bundle should remain sufficient after the
harness cache is deleted.

### F-08 — infrastructure failure is labelled validation failure (`P1`, E4)

`src/aidd/harness/eval_reports.py:298-310` transforms setup/install/teardown failures into a
synthetic `STRUCT-MISSING-REQUIRED-DOCUMENT` validator finding. The observed DET-002 result has
execution status `infra-fail`, but its first failure is category `validation`, sourced from the
synthetic validator report. The real first failure is `uv sync --extra dev` rejecting an undefined
fixture extra.

Verdict and cause must be separate but compatible fields. Setup/install/teardown failures belong
to environment/infrastructure, adapter process failures to adapter/runtime, invalid Markdown to
validation, and acceptance mismatches to scenario verification. Do not manufacture document
findings for infrastructure errors.

### F-09 — maintained deterministic lanes are not invocation-portable (`P2`, E4)

The maintained large `AIDD-DETERMINISTIC-002` manifest runs `uv sync --extra dev`, but the fixture
has no `dev` extra. It then lacks the `aidd.example.toml` required by the deterministic executor.
The resilience scenarios DET-005/006 pass under `uv run`, but direct installed-CLI invocation fails
because their commands assume `python` is on `PATH`.

These lanes are not the primary CI/release gate, so this is P2 rather than P1. Repair the fixture
setup and use a harness-owned interpreter or an explicit scenario interpreter. Test each maintained
manifest through the installed entry point, not only a source/uv environment.

### F-10 — adapter conformance is structural rather than behavioral (`P2`, E3/E4)

The conformance matrix requires log, failure, question, timeout, and workspace behavior. However,
`src/aidd/harness/adapter_conformance.py:92-138` passes raw-log/question dimensions when a field is
merely a boolean (including `False`), and passes failure/timeout when enum members exist. The CI
test asserts that this declaration inspection yields no failed dimensions.

This missed an observed generic-cli gap: `src/aidd/adapters/surface.py:527-554` persists the plain
runtime log but deletes the structured capture sources and returns no `runtime_jsonl` or
`events_jsonl`, although `DiskBackedRuntimeLogSink` had parsed the JSONL.

Split `declared capability` from `observed conformance`. A fixture adapter test must execute bytes,
JSON events, questions, non-zero exit, timeout, cancellation, and cwd/env cases and compare the
durable adapter outcome and files.

### F-11 — project-set bounding is conditional, not universal (`P2`, E3)

Project-set declarations, context injection, root grouping, and post-run diff flags are substantial.
The current deterministic scenario, however, stops at plan and mainly proves textual traceability.
It does not prove cross-root implementation, per-root evidence, or progression rejection for an
out-of-root write.

The documented `full-access` policy returns ALLOW immediately at
`src/aidd/core/runtime_operator.py:518-535`; project-root checks occur only in stricter brokered
paths. The behavior itself is disclosed in `README.md`. The mismatch is that the unconditional
`US-12` phrase “execution stays bounded” reads as enforcement in every supported mode, while the
full-access mode provides declaration, attribution, and post-factum detection instead.

Make a product choice: either enforce declared roots even in the supported broad mode, or change
the user story and UI wording to “declared, attributed, and detected.” In either case, add a
two-root implement scenario with an intentional outside-root write and explicit expected outcome.

### F-12 — provider details leak across the extension boundary (`P2`, E3)

The core has no direct adapter imports, which is good, but `src/aidd/core/runtime_operator.py:48-94`
hard-codes `.claude`, `.codex`, `.opencode`, `.qwen`, and provider credential filenames.
`src/aidd/adapters/surface.py` is a central provider registry over 1,100 lines, and
`src/aidd/config.py` contains provider-specific legacy fields/accessors.

Move protected runtime paths and credential descriptors into security/capability metadata supplied
by each adapter. Move adapter registration toward data/entry-point discovery while retaining an
explicit allowlist. Add an architecture test for provider names/imports in runtime-neutral core.

### F-13 — complexity is concentrated in high-risk boundaries (`P2`, E4)

Radon scored 3,066 blocks with average complexity 4.41: 2,334 A, 469 B, 194 C, 46 D, 15 E,
and 8 F. The average is healthy, but the tail is concentrated exactly where orchestration truth is
assembled:

- `src/aidd/harness/task_flow_checkpoint.py:250` — complexity 82;
- `src/aidd/harness/scenarios.py:502` — 50;
- `src/aidd/harness/live_e2e_black_box_orchestration.py:7448` — 49;
- `src/aidd/adapters/codex/live.py:407` and `src/aidd/adapters/qwen/live.py:58` — 42;
- `src/aidd/core/stage_runner.py:596` — 36;
- `src/aidd/core/run_store.py:919` — 38;
- `src/aidd/core/operator_frontend_dashboard_evidence.py:1171` — 37.

The largest modules are `live_e2e_black_box_orchestration.py` (9,482 lines), `cli/ui.py` (5,013),
and `operator_frontend_dashboard_evidence.py` (2,477). The live orchestrator still contains a
14-function `_legacy_*` process-execution island at roughly lines 425-1003, while line 1010 binds
the canonical implementation imported from the extracted steps module; direct search found no
caller for the legacy entry.

Use characterization tests and extract by responsibility. Do not combine this with product
semantics changes. First remove the dead legacy island, then split lifecycle/setup, command
execution, frontend probes, evidence assembly, and reporting behind the current facade. Split UI
transport/routing from job, decision, and workflow services.

### F-14 — planning documents no longer satisfy their own operating model (`P2`, E4)

`docs/backlog/backlog.md` calls itself a short actionable queue and says to keep one bounded current
reconciliation note. It is 3,713 lines and contains 509 dated reconciliation bullets. The canonical
roadmap is 17,330 lines and has very high churn.

Parent status is not rolled up. In Wave 43, for example, `W43-E1` and its slices remain `planned`
while all their local tasks are `done`; similar mismatches exist across the wave. The parked
cross-runtime task legitimately prevents the entire wave from being done, but it does not justify
completed child containers remaining planned. `tests/planning_integrity.py` validates syntax,
vocabulary, placement, and queue synchronization, not parent/child roll-up or the bounded-note
rule.

Archive reconciliation history into dated analysis/history files, keep one current note in the
active backlog, and add deterministic roll-up validation. A canonical plan whose aggregate status
cannot be trusted weakens the repository's document-first claim.

### F-15 — live and UX acceptance is not current enough for beta (`P2`, E2)

The tracked 2026-08-31 report records successful Codex and Claude full flows against a pinned
Starlette revision. The raw `.aidd/reports/evals/...` bundles referenced by that report are absent
from this checkout because `.aidd/` is ignored, so only the reconciliation summary is auditable
here. The report was produced on AIDD revision `adbc73f...`; 20 relevant contract/core/CLI/harness
files changed before the audited `f281953...`, including task recovery, finalization, timeline,
checkpoint, and live orchestration paths.

The operator UX contract also requires genuine uncoached first-time observation before the target
renderer is considered accepted, while that task remains parked. The most recent large run used
API/UI checkpoints and supplied no new browser screenshots.

Keep these reports as valuable historical evidence, but display evidence revision/freshness and do
not use them as current-SHA beta acceptance. Preserve future sanitized bundles in an immutable,
retrievable location with digests.

### F-16 — smaller documentation drift remains (`P3`, E3)

- `docs/architecture/document-contracts.md:19-29,123-133` and the target architecture describe
  frontmatter as required, while the product story and loader intentionally make it optional.
- `docs/analysis/beta-readiness-source-audit.md` discusses coverage through `US-12`, while the
  current product source includes `US-13`.
- User-story IDs are checked when the roadmap mentions them, but there is no executable
  story-to-contract-to-test-to-scenario traceability requirement.

Reconcile the wording and add a small generated traceability table. Do not solve this with more
free-form narrative.

### F-17 — assurance breadth has a few ungoverned edges (`P3`, E4)

The default Python suite under `tests/` is large and passed in full, so this is not a claim that
test volume is weak. However:

- no coverage threshold makes regression in exercised surface measurable at the merge gate;
- `uv run --extra dev ruff format --check .` reports 328 files that would be reformatted and 199
  already formatted, while CI runs lint but no formatter check;
- CodeQL covers Python but not the 15,562-line packaged browser JavaScript surface.

Decide on one formatter baseline in a dedicated mechanical change, then gate only new drift. Add a
measured coverage baseline with critical-module thresholds rather than chasing a repository-wide
percentage. Extend browser-code security analysis or add a suitable JS static/dataflow lane. These
are hardening improvements, not evidence of a current vulnerability.

## Product-goal alignment

Status meanings: **implemented** means the product path exists with strong code/test evidence;
**partial** means the main path exists but a material success signal or acceptance boundary is not
demonstrated.

| Story | Status | Evidence and remaining gap |
| --- | --- | --- |
| US-01 Runtime portability | **Partial** | Shared stage graph/request/outcome model and old Codex+Claude full-flow evidence exist. Current-SHA parity and lower-capability evidence are absent; provider policy leaks into core. |
| US-02 Document-first artifacts | **Implemented, inconsistent authority** | Markdown contracts drive registry and validators. F-04 must be fixed so repair/intervention has one owner model. |
| US-03 Validate before progression | **Implemented, reliability gap** | Transition logic is fail-closed in normal cases; F-02 shows parser/I/O exceptions can bypass terminalization. |
| US-04 Self-repair | **Implemented in core/tests** | Budgets, briefs, reruns, and exhaustion are implemented. The full-flow eval evidence currently misreports task attempts as repair. |
| US-05 User interview | **Implemented in core/tests** | QID parsing, ledger, block/answer/resume, CLI and UI paths exist. DET-004 does not exercise the sequence it claims. |
| US-06 Native runtime visibility | **Implemented, reliability gap** | Concurrent streaming and disk-backed raw capture exist. F-01 weakens the guarantee; generic-cli structured JSONL is an architecture/eval gap, not a breach of this story's raw-log requirement. |
| US-07 Harness and eval | **Partial** | Scenario loading, durable results, graders, and live orchestration are substantial. F-05 through F-10 make some verdict evidence non-authoritative. |
| US-08 Clean adapter extension | **Partial** | A typed protocol and runtime matrix exist. Central registries/config, provider details in core, and non-behavioral conformance increase extension cost and risk. |
| US-09 Installable operator experience | **Implemented** | Package resources, CLI, multi-Python CI, release build, and pipx/uv-tool verification are present. The audited source is correctly labelled unreleased alpha. |
| US-10 Change accountability | **Implemented in core; partial in eval bundles** | Prompt/config/repo/resource hashes and comparisons are strong. Eval/product IDs and dangling/missing bundle evidence must be corrected. |
| US-11 Operator frontend | **Partial** | It reuses core services and has extensive provider-free/browser evidence. The uncoached observation and current Wave 46 multi-context/responsive gates remain open. |
| US-12 Project-set workflow | **Partial** | Root declarations, context, diff grouping, and cross-document checks exist. Universal enforcement and two-root implementation evidence do not. |
| US-13 Incremental task execution | **Implemented, strongest slice** | Dependency order, task-local attempts, ledger, resume, finalization, and review/QA eligibility have code, tests, deterministic, and historical live evidence. F-03 is the remaining high-impact recovery defect. |

Summary: **8 implemented, 5 partial** (`US-01`, `US-07`, `US-08`, `US-11`, `US-12`). The
implemented group still carries the cross-cutting P1 exception/evidence defects above; “implemented”
does not mean beta-accepted.

## Declared-flow conformance

| Flow capability | Evidence level | Assessment |
| --- | --- | --- |
| Eight-stage order | E4 | Fresh DET-004 completed all eight stages in order. |
| Valid Markdown happy path | E4 | All stage outputs validated and published in the fresh fixture run. |
| Validation failure stops progression | E3 | Focused core/CLI tests pass; parser/I/O exceptions expose F-02. |
| Automatic repair and exhaustion | E3 | Core tests and dedicated provider-free scenarios pass; DET-004 is not repair evidence despite its report. |
| Interview/block/answer/resume | E3 | Core and UI tests pass; no E4 full-flow sequence in DET-004 despite `required: true`. |
| One-task-at-a-time implementation | E4 | Three tasks ran once each in dependency order; finalization preceded review/QA. |
| Failure recovery and resume | E3/E0 | Normal tests pass; the malformed-report reproduction can strand the ledger. |
| Raw logs and event evidence | E3/E0 | Most adapters persist attempt logs; invalid bytes and generic-cli structured logs expose gaps. |
| Self-contained eval verdict | E0 | Fresh PASS bundle contains false repair claims, dangling provenance, and cache-only required evidence. |
| Cross-runtime full flow | E2 | Tracked Codex/Claude report exists on an older revision; raw bundles are not retrievable here. |
| Project-set implementation | E2/E3 | Plan-level deterministic traceability and core diff tests exist; multi-root implement enforcement is not demonstrated. |
| Operator UX acceptance | E2/E3 | Extensive scripted/browser evidence exists; required uncoached observation and current multi-context gates remain open. |

The flow itself is materially real. The 64/100 score reflects that the project's own promise
includes repair, interview, classification, provenance, and auditable evidence, not only a
successful stage sequence.

## Verification performed

### Current-revision checks

| Check | Result |
| --- | --- |
| `uv run --extra dev ruff check .` | PASS |
| `uv run --extra dev python -m mypy src scripts` | PASS, 234 files |
| Packaged JavaScript syntax check | PASS, 25 assets |
| `node --test tests/frontend/*.test.mjs` | PASS, 140 tests |
| Focused docs/planning/ownership tests | PASS, 55 tests |
| Focused user-story/core/adapter/scenario lanes | PASS, 129 tests |
| Adapter/validator negative-path neighborhoods | PASS, 81 tests |
| Core lifecycle/readiness neighborhood | PASS, 40 tests |
| Selected stage-runner tests | PASS, 4 tests |
| Adapter conformance lane | PASS, 4 tests; F-10 explains why this is insufficient |
| CI scenario fixture integration | PASS, 5 manifests |
| Focused repair/interview tests | PASS, 7 tests |
| Verdict/log-analysis tests | PASS, 27 tests |
| `uv run --extra dev pytest -q` | PASS, 2,519 tests in 1,275.58 seconds |
| `uv run --extra dev ruff format --check .` | FAIL, 328 files would be reformatted; no formatter gate currently exists (F-17) |

### Fresh flow execution

- `AIDD-DETERMINISTIC-004`: PASS in about 25 seconds; eight stages, three ordered task attempts,
  aggregate finalization, review, QA, and six verify commands.
- `AIDD-DETERMINISTIC-005`: 10/10 cases pass when launched through `uv run`.
- `AIDD-DETERMINISTIC-006`: 8/8 cases pass when launched through `uv run`.
- `AIDD-DETERMINISTIC-002`: `infra-fail` during setup; see F-08/F-09.
- Direct installed-CLI launch for DET-005/006: fails on missing `python`; see F-09.

Fresh audit evidence was retained temporarily outside the checkout at
`/tmp/aidd-flow-audit.2LEzko`. The decisive values are recorded in this report because `/tmp` is
not a durable product evidence store.

### Static and supply-chain probes

- Radon results are recorded in F-13.
- Vulture at 90% confidence reported only the conventional `format` argument in an overridden
  HTTP handler; this was assessed as a false positive.
- Bandit medium/high scan reported two `urlopen` sites in the live harness. Both are reached with a
  locally allocated `127.0.0.1` UI URL in the inspected call paths; no confirmed high-severity
  finding was identified.
- An exact-pin `pip-audit --no-deps --disable-pip` scan reported no known vulnerabilities. This is
  a point-in-time advisory-database check, not proof of absence, and the no-deps mode was required
  after the isolated resolver environment failed to bootstrap pip.

## Remediation plan

The phases below are sequencing recommendations, not new canonical roadmap tasks. Before
implementation, use the repository's backlog/task-slicing workflow to create accepted local tasks
with one dominant touched area and one verification signal.

The task-level estimates and IDs are authoritative in the linked remediation plan: W48–W50 contain
64.75 beta-critical engineer-days and 89.25 engineer-days for full closure, plus external sessions.
The adjacent W47 Focus Canvas UI rollout owns presentation work; remediation integrates its merged
result rather than duplicating it.

### Phase 0 — restore lifecycle and evidence truth (`P1` plus foundational `P2`)

#### 0A. Exception-safe stream and lifecycle boundaries

1. Capture subprocess output as bytes; preserve raw bytes before decoding.
2. Add an explicit reader error/result channel and reconcile it before success.
3. Normalize non-file, unreadable, invalid-UTF-8, and malformed-frontmatter outputs into located
   findings where repairable.
4. Add a top-level terminalization guard around every post-transition stage-runner operation.
5. Make task-attempt terminalization monotonic and secondary-evidence collection best-effort.
6. Add deterministic reconciliation for already abandoned `executing`/`validating` states.

Acceptance:

- the three F-01/F-02/F-03 reproductions become automated regression tests;
- no completed process can leave stage/task state `executing` or `validating`;
- the primary exception is never replaced by evidence-copy/parse cleanup;
- invalid bytes remain available in raw evidence with a documented display decoding policy.

#### 0B. Make ownership one executable contract

1. Adopt AIDD ownership for `stage-result.md` and `validator-report.md` everywhere.
2. Remove runtime mutation instructions from all repair and intervention prompts.
3. Update architecture, document contracts, all eight stage contracts, prompt hashes, and tests in
   the same slice.
4. Derive the runtime output registry from one typed ownership model or validate exact bidirectional
   equivalence with the Markdown matrix.

Acceptance:

- a semantic consistency test rejects any prompt/contract that asks the runtime to mutate an
  AIDD-owned record;
- runtime writes to protected records remain diagnostic evidence and never completion targets;
- adding a document owner cannot silently fall through a filename default.

#### 0C. Repair eval provenance and classification

1. Persist explicit attempt kinds and real lineage.
2. Store the actual product run ID separately from the eval run ID.
3. Write feature selection or omit the reference; copy raw attempt logs, canonical validator
   reports, task ledger/finalization, and scenario-specific reports into the bundle.
4. Preserve partial command transcripts on every failure.
5. Replace synthetic validation findings for infrastructure failures with a unified cause model.
6. Run bundle integrity validation before the verdict can be PASS.

Acceptance:

- DET-004 reports zero repairs unless a fault is actually injected and repaired;
- every `evaluation_source=run-artifact-observation` points to an artifact proving that exact probe;
- deleting `harness-cache` does not make a PASS bundle unauditable;
- every referenced file exists and matches its digest;
- execution status and first-failure category cannot contradict each other.

### Phase 1 — make scenario and adapter claims executable (`P1/P2`)

1. Add typed scenario assertions for stage sequence, task order, finalization eligibility, failures,
   and evidence fields.
2. Implement a real deterministic `blocked -> answer -> resume` full-flow lane and make
   `interview.required` enforce it.
3. Restore DET-002 setup/config and make every maintained manifest runnable from an installed
   artifact with an explicit interpreter.
4. Replace declaration-only adapter conformance with behavior fixtures for bytes, JSONL, questions,
   exit mapping, timeout, cancellation, cwd, and environment.
5. Persist generic-cli structured events instead of deleting them.
6. Unify canonical verdict, first-failure cause, and reporting classes into one typed taxonomy with
   compatibility mapping for older bundles.

Acceptance:

- all maintained deterministic scenarios pass through both source and installed-package entry
  points;
- changing a capability boolean or enum without matching behavior fails conformance;
- scenario prose is either an executable assertion or explicitly non-gating documentation;
- one schema carries cause category consistently through log analysis, grader, summary, and UI.

### Phase 2 — close product-boundary and maintainability debt (`P2/P3`)

1. Decide whether project-set means enforced containment or attributed/detected scope, update the
   story/architecture/UI, and add a two-root implement negative-path scenario.
2. Move provider credential/path descriptors from core to adapter capability/security metadata.
3. Remove the dead live-harness compatibility island, then extract the remaining harness by
   lifecycle, command execution, probes, evidence, and reporting.
4. After the adjacent W47 UI rollout merges, split `cli/ui.py` transport/routing from application
   services and payload codecs without revisiting its presentation behavior.
5. Refactor F/E-complexity functions using characterization tests; avoid semantic changes in the
   same commits.
6. Archive backlog reconciliation history, add parent-status roll-up checks, and generate a compact
   US-to-contract/test/scenario traceability view.
7. Reconcile optional-frontmatter and US-13 wording drift.
8. Establish a formatter baseline, critical-module coverage thresholds, and browser-JavaScript
   security analysis without mixing the mechanical reformat with behavior changes.

Acceptance:

- no unused `_legacy_*` process implementation remains;
- no new E/F-complexity block is introduced; modified lifecycle/evidence functions are C or lower;
- the active backlog contains one bounded current reconciliation note;
- completed child tasks deterministically roll up their slice/epic status, with explicit handling
  for parked tasks;
- provider names in runtime-neutral core are absent or justified by a reviewed security abstraction.

### Phase 3 — produce beta-grade acceptance evidence (plus external sessions)

1. Run the repaired deterministic happy, validation-failure, repair, interview, task-failure,
   project-set, and bundle-integrity lanes on the exact candidate SHA.
2. Build the wheel and verify `pipx` and `uv tool` install/upgrade from that artifact.
3. Run same-revision Codex and Claude medium/large flows, plus one maintained lower-capability
   runtime or record an explicit external blocker.
4. Perform the required genuine uncoached first-time operator observation and current Wave 46
   two-context/responsive browser journeys.
5. Store sanitized immutable bundles outside ignored local `.aidd/`, with revision, target pin,
   digests, and retrievable locations.

Beta acceptance gate:

- zero open P1 findings from this audit;
- full static/unit/integration/browser/release checks pass on the candidate SHA;
- every maintained scenario has an executable assertion set and self-contained bundle;
- real-provider evidence is same-revision and its raw sanitized bundle is retrievable;
- remaining P2 items have explicit accepted scope and do not contradict a public success signal.

## Suggested execution order and ownership boundaries

| Workstream | Dominant owner | Must not be combined with |
| --- | --- | --- |
| Stream bytes/error propagation | adapters/process supervision | broad adapter API redesign |
| Stage terminalization | core orchestration/validators | prompt rewrite or UI redesign |
| Task terminalization | implementation lifecycle | task grammar changes |
| Ownership reconciliation | contracts/prompts/core registry | unrelated validator tuning |
| Attempt lineage and bundle integrity | harness/evals | live-provider reruns before the fix |
| Scenario assertions/interview lane | harness fixtures | production core semantics changes |
| Adapter behavioral conformance | adapter protocol/harness | adding a new provider |
| Project-set semantics | product/architecture/core policy | UI cosmetic work |
| Harness/UI decomposition | maintainability-only | new behavior |
| Beta evidence | release/eval | any unmerged behavior change |

## Residual risks after the plan

Even after these changes, AIDD will remain an orchestration layer around third-party runtimes. It
cannot guarantee model quality, provider availability, or safe arbitrary execution under full
access. The correct product promise is deterministic orchestration policy, bounded and truthful
evidence, explicit operator decisions, and honest classification of what was not observed.

Performance/load behavior, multi-process concurrency under sustained operator use, fuzzing of all
Markdown grammars, Windows-specific process-tree behavior, and a full JavaScript security/dataflow
review were outside this audit. They should be assessed before a production rather than beta claim.

## Final conclusion

AIDD is not a low-quality project. It has unusually substantial contracts, lifecycle modeling,
tests, provenance, release automation, and a real end-to-end task execution path for an alpha.
Its current weakness is more specific and more fixable: **the evidence and terminal-state
boundaries are less reliable than the architecture and happy path**.

The highest-value move is therefore not more features and not a rewrite. It is to make every
failure terminal, every scenario claim executable, and every PASS bundle self-contained and
truthful. After those changes and same-revision live acceptance, the project can credibly move from
“strong alpha” toward beta.
