# Project quality remediation plan — 2026-09-05

## Status

This is the **accepted audit-remediation plan**, but its local tasks are not yet part of the
canonical roadmap or active backlog. Candidate IDs become authoritative only when each slice is
promoted through the repository's backlog workflow.

This revision starts at W48 because the adjacent UI task owns the candidate
`Wave 47 — Focus Canvas production rollout`. The remediation plan must integrate that work after
merge, not compete for its IDs or edit its UI surface in parallel.

Source assessment:
[`project-quality-flow-audit-2026-09-05.md`](project-quality-flow-audit-2026-09-05.md).

## Parent outcome decomposed

Parent outcome: close the 2026-09-05 quality-audit findings and produce trustworthy beta-candidate
evidence without replacing AIDD's architecture or weakening existing behavior.

The parent is too broad for one task or one wave because it contains independent outputs in:

- adapter process capture;
- core stage and task lifecycle;
- document contracts and prompt packs;
- harness/eval evidence;
- product boundaries and architecture;
- code-structure and planning hygiene;
- release, browser, provider, and human acceptance.

The work is therefore split into three waves:

| Wave | Outcome | Findings | Estimated effort | Beta criticality |
| --- | --- | --- | ---: | --- |
| W48 | Lifecycle and evidence truth | F-01 through F-10 | 38.5 engineer-days | Required |
| W49 | Product boundaries and sustainable maintenance | F-11 through F-14, F-16, F-17 | 42.75 engineer-days | E1 and E3 required; other slices may be accepted debt |
| W50 | Current, retrievable beta acceptance | F-15 and all prior gates | 8 engineer-days plus external sessions | Required |

The minimum beta-critical baseline is **64.75 engineer-days**: all of W48, W49-E1 and W49-E3,
and all newly proposed W50 tasks. It excludes any W49-E2 work found necessary to maintain the W48
changes and the effort already represented by reused provider/human acceptance tasks. Full closure
of all newly proposed tasks is **89.25 engineer-days**, plus those external sessions. With three
coordinated owners, the beta-critical calendar path is roughly **6–9 weeks** because several gates
are sequential and provider/participant availability is external. These are coarse planning point
estimates, not delivery commitments.

## Finding-to-work traceability

| Finding | Primary remediation | Closure evidence |
| --- | --- | --- |
| F-01 | W48-E1-S1 byte-authoritative capture | Invalid and split UTF-8 bytes remain exact; reader failure cannot return adapter success. |
| F-02 | W48-E1-S2 document-read and terminal safety | Every read/parse failpoint reaches `repair-needed` or `failed`; no abandoned `validating`. |
| F-03 | W48-E1-S3 monotonic task failure | Original executor cause and terminal task ledger survive corrupt enrichment evidence. |
| F-04 | W48-E2 executable document authority | Contracts, prompts, registry, and all-stage ownership tests agree. |
| F-05 | W48-E3-S1 lineage plus W48-E4-S1 assertions | Clean task attempts report zero repairs; only executed probes can be observed. |
| F-06 | W48-E4-S1 typed assertions/interview | Required claims gate PASS, including a real `blocked → answer → resume` sequence. |
| F-07 | W48-E3-S3 self-contained bundle v2 | Sealed PASS survives deletion of mutable harness/product state and verifies every reference. |
| F-08 | W48-E3-S2 failure-cause model | Setup failure remains infrastructure/setup through every report projection. |
| F-09 | W48-E4-S2 source/wheel portability | Every maintained scenario runs in both artifact modes without an implicit `python` command. |
| F-10 | W48-E4-S3 behavioral conformance | Required vectors observe bytes, events, question, exit, timeout, cancellation, cwd, and env. |
| F-11 | W49-E1-S1 project-set policy/gate | Product wording is mode-specific; an outside-set change blocks aggregate finalization. |
| F-12 | W49-E1-S2 adapter-owned metadata | A fake runtime extends via adapter-local descriptor without provider edits in core. |
| F-13 | W49-E2 hotspot reduction | Characterized behavior is preserved and no new E/F complexity block is admitted. |
| F-14 | W49-E3-S1 planning hygiene | Active planning is bounded and parent status is mechanically rolled up. |
| F-15 | W50 exact-candidate acceptance | Same-revision source/wheel/browser/provider/human evidence is current and retrievable. |
| F-16 | W49-E3-S2 story traceability | Generated US-01…US-13 view has live contracts, code, tests, scenarios, and evidence links. |
| F-17 | W49-E4 assurance ratchets | Formatter, critical-module coverage, and Python/JavaScript analysis are required gates. |

## Concurrent UI work boundary

At the time of this revision, the adjacent `Улучшить UI и UX` task is implementing W47 in the main
checkout. Until its PR merges, it has exclusive ownership of:

- `src/aidd/cli/static/**`;
- `tests/frontend/**` and UI-focused `browser_tests/**`;
- `docs/architecture/operator-frontend*.md`;
- packaged-UI registries/runners, UI-specific live manifests, `docs/e2e/**`, and retained UI
  acceptance evidence;
- W47 UI planning and acceptance evidence in `roadmap.md` and `backlog.md`.

`src/aidd/cli/ui.py`, public UI payloads, core operator read models, packaged UI scenarios, and
shared planning files are integration seams. They may be changed by this plan only after inspecting
the current UI diff/PR and establishing one owner for the exact file. The operating rules are:

1. W48 core, adapter, validator, harness, and eval tasks may run in parallel only when their diff
   does not touch the UI-owned paths or change a payload consumed by W47.
2. W49-E2-S2 is held until the W47 UI PR is merged and a post-merge compatibility baseline is
   green. If W47 already produces one of its outputs, close or reslice the residual work instead of
   reimplementing it.
3. W50 UI/browser/provider/human acceptance runs only against a revision containing both W47 and
   all beta-critical remediation changes.
4. Integration happens through merged `origin/main`; do not copy uncommitted UI files between
   worktrees or resolve overlap by overwriting the adjacent checkout.
5. Before selecting every local task, refresh the adjacent task/PR status and compare its touched
   paths with the candidate task. An overlap means sequence or transfer ownership, never parallel
   editing.

## Planning rules for execution

1. Promote one local task at a time through `roadmap.md` and `backlog.md`.
2. Every task below has one concrete output, one dominant touched area, and one main verification
   signal.
3. Contract changes precede code that implements them.
4. Behavior fixes and behavior-preserving refactors must not share a task or commit.
5. No new live-provider evidence is counted until W48's deterministic exit gate passes.
6. A code, contract, prompt, validator, or harness change after candidate freeze invalidates W50
   acceptance and returns it to the freeze step.
7. Existing parked acceptance tasks are reused; this plan does not create duplicate human,
   cross-runtime, or browser tasks.

## Per-task delivery loop

Repeat this loop until the W50 exit gate is met:

1. Fetch `origin`, inspect the adjacent UI task/PR, and select the first dependency-ready,
   non-overlapping local task from the accepted order.
2. Read the nearest `AGENTS.md`, owning contracts, relevant architecture/product documents, current
   implementation, tests, and prior evidence for that task.
3. Write a focused implementation plan containing the one output, allowed scope, acceptance signal,
   dependencies, and rollback/recovery concern.
4. Create `codex/<task-id>-<short-slug>` from current `origin/main` in an isolated worktree; never
   implement in a stale or dirty shared checkout.
5. Implement the smallest vertical change, run the task's focused verification and owning
   neighborhood checks, then make a task-scoped commit.
6. Review the full diff for correctness, architecture/runtime neutrality, regression risk, evidence
   truth, and UI-thread overlap. Fix findings and add a follow-up commit when needed.
7. Push the branch, open a PR, wait for required checks, address review/CI findings, and merge only
   when the task acceptance signal is evidenced.
8. Fetch the merge and fast-forward the clean main checkout. If the adjacent UI task still owns a
   dirty main checkout, do not touch it; verify `origin/main` and start the next isolated branch from
   that commit after coordination.
9. Reconcile task status/evidence, then return to step 1.

## Recommended queue decision

The adjacent UI task currently owns `W47-E1-S1-T4`, while the existing browser task
`W46-E1-S2-T4` remains separately queued. Neither result should be treated as final beta evidence
before lifecycle and evidence semantics stabilize. Recommended remediation order:

1. keep W47 implementation and its branch/PR under the adjacent UI owner;
2. promote no W48 task until the W47 planning changes in `roadmap.md`/`backlog.md` are merged or the
   adjacent owner formally hands those files back;
3. make `W48-E1-S1-T1` the first remediation task only after the overlap check confirms its branch
   can be based on current `origin/main` without touching UI-owned paths;
4. retain `W46-E1-S2-T4` and `W46-E2-S2-T4` for the W50 candidate matrix rather than deleting or
   duplicating them;
5. promote only a direct successor into `Soon` after the current task is accepted;
6. keep provider/human acceptance parked until exact candidate freeze.

No queue or roadmap file is changed by this analysis-plan commit.

# Wave 48 — lifecycle and evidence truth

## Goal

Make every execution path terminal, every eval claim evidence-backed, every scenario gate
executable, and every PASS bundle independently auditable.

Linked stories: `US-01`, `US-02`, `US-03`, `US-04`, `US-05`, `US-06`, `US-07`, `US-08`,
`US-09`, `US-10`, `US-13`.

## Epic W48-E1 — exception-safe execution lifecycle

### Slice W48-E1-S1 — byte-authoritative runtime capture

Primary output: exact raw subprocess bytes plus a separately defined tolerant text view.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E1-S1-T1` | Define raw-byte authority and UTF-8 presentation/error policy. | Adapter protocol | Docs test distinguishes raw evidence from display text. | 0.5d |
| `W48-E1-S1-T2` | Launch stdout/stderr as binary pipes. | `process_supervisor.py` | Invalid-byte child reaches the stream layer byte-exactly. | 0.5d |
| `W48-E1-S1-T3` | Persist raw chunks before incremental display decoding. | `runtime_log_capture.py` | Split multibyte/invalid-byte matrix preserves exact bytes and counters. | 0.75d |
| `W48-E1-S1-T4` | Replace EOF-overloaded queue messages with typed `chunk/eof/error` events. | `subprocess_streaming.py` | Injected reader error is distinguishable from clean EOF. | 0.75d |
| `W48-E1-S1-T5` | Reconcile reader outcomes before returning adapter success. | Shared subprocess runner | Exit zero plus reader failure returns capture failure with partial evidence. | 0.75d |

Dependencies: T1 → T2/T3 → T4/T5.

Exit signal: `b"before\n\xffafter\n"` is preserved in durable evidence, produces no daemon-thread
traceback or hang, and cannot result in successful empty capture.

### Slice W48-E1-S2 — document-read and stage-terminal safety

Primary output: malformed/unreadable Markdown produces a legal repair or failed terminal state,
never an abandoned `validating` state.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E1-S2-T1` | Define canonical failure kinds/codes for non-file, unreadable, invalid UTF-8, and malformed frontmatter. | Validator protocol/contracts | Contract and protocol registry remain equivalent. | 0.5d |
| `W48-E1-S2-T2` | Add one typed Markdown readability probe. | `document_loader.py` | Parameterized path/UTF-8/frontmatter matrix returns typed outcomes only. | 0.75d |
| `W48-E1-S2-T3` | Map repairable runtime-output read failures to located structural findings. | `structural.py` | Directory, invalid UTF-8, and malformed frontmatter each yield one repair verdict. | 0.75d |
| `W48-E1-S2-T4` | Treat only regular readable Markdown as discovered output. | `stage_outputs.py` | A directory named `plan.md` is not a valid discovered document. | 0.5d |
| `W48-E1-S2-T5` | Use the same core readiness predicate in eligibility and preflight. | Stage graph/preparation | Core eligibility cannot mark an input runnable when preflight will reject it. | 0.5d |
| `W48-E1-S2-T6` | Add exception-safe terminalization around post-execution discovery/interview/validation. | `stage_runner.py` | Failpoint matrix always persists `repair-needed` or `failed` with the primary cause. | 1d |
| `W48-E1-S2-T7` | Extend public reconciliation to abandoned `validating` stages. | Core terminal reconciliation | Stale state converges idempotently; a live owner is not rewritten. | 0.75d |

Dependencies: T1 → T2 → T3/T4 → T5/T6 → T7.

Coordination: T5 is limited to the core readiness predicate and does not change public UI payloads.
Any UI projection is a separate post-W47 task and must run the merged W47 frontend/browser
regression suite.

Exit signal: all F-02 reproductions are automated; a stopped owner leaves no stage in
`executing`/`validating`, and canonical answers survive malformed runtime candidates.

### Slice W48-E1-S3 — monotonic task failure

Primary output: task failure is durable before optional evidence enrichment begins.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E1-S3-T1` | Persist the primary executor failure and terminal task state first. | Task attempt lifecycle | Executor error plus corrupt report leaves task `failed` with original cause. | 0.75d |
| `W48-E1-S3-T2` | Move report/interview/snapshot/diff collection to best-effort enrichment. | Implementation evidence | Secondary collection failures cannot replace the executor error. | 0.75d |
| `W48-E1-S3-T3` | Reconcile task ledger and implement-stage projection across crash windows. | Implementation service | Failpoint matrix converges to task/stage `failed` without deleting evidence. | 0.75d |

Dependencies: T1 → T2 → T3. This slice can run in parallel with S1 and S2 after its focused
contract is approved.

Exit signal: the exact F-03 reproduction is covered, `ImplementationPortError.__cause__` remains
the executor exception, and no failed task remains `executing`.

## Epic W48-E2 — executable document authority

### Slice W48-E2-S1 — one ownership narrative

Primary output: architecture and contracts unanimously declare AIDD ownership of
`stage-result.md` and `validator-report.md`.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E2-S1-T1` | Remove runtime-draft wording from architecture, document contract, and all eight stage contracts. | Contracts/docs | Contradictory ownership phrases are absent and all eight contracts match the matrix. | 0.75d |

### Slice W48-E2-S2 — ownership-safe prompts

Primary output: repair and intervention mutate only runtime-owned stage content.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E2-S2-T1` | Rewrite all repair prompts to treat workflow records as read-only evidence. | Repair prompt packs | Per-stage write-target table contains only runtime content. | 0.75d |
| `W48-E2-S2-T2` | Rewrite all intervention prompts with the same protected-record boundary. | Intervention prompt packs | Mutation verbs paired with protected documents fail the prompt test. | 0.5d |
| `W48-E2-S2-T3` | Replace contradiction-preserving assertions and refresh prompt hashes. | Prompt/docs tests | Reintroducing `update stage-result` fails CI; packaged/source hashes agree. | 0.75d |

Dependencies: E2-S1-T1 → T1/T2 → T3.

### Slice W48-E2-S3 — ownership-derived output registry

Primary output: one typed ownership registry drives runtime/AIDD/interview/publication projections.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E2-S3-T1` | Parse the canonical matrix into a fail-closed typed registry. | New core ownership registry | Missing, duplicate, unknown, and conflicting rows fail before execution. | 1d |
| `W48-E2-S3-T2` | Build stage output projections from that registry and remove independent filename authorities. | `stage_registry.py` | A synthetic new document receives only its declared owner. | 0.75d |
| `W48-E2-S3-T3` | Prove protected runtime candidates never become completion targets. | Ownership integration tests | All-eight-stage discovery/repair/intervention/publication table passes. | 0.5d |

Dependencies: E2-S1-T1 → T1 → T2 → T3.

## Epic W48-E3 — truthful eval evidence

### Slice W48-E3-S1 — explicit attempt lineage

Primary output: attempt classification comes from persisted lifecycle lineage, never ordinal count.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E3-S1-T1` | Define versioned stage/task/finalization attempt lineage with legacy reads. | Core evidence contract | Round-trip fixtures distinguish initial, repair, resume, intervention, task, and finalization. | 0.5d |
| `W48-E3-S1-T2` | Persist lineage from each owning lifecycle service. | Core lifecycle evidence | Three clean task attempts create no repair edge. | 1.5d |
| `W48-E3-S1-T3` | Derive timing, repair history, and repair matrix only from lineage. | `stage_timing.py` | DET-004 reports zero repairs; one injected repair reports exactly one. | 1d |

Dependencies: T1 → T2 → T3; T2 follows W48-E1 terminalization.

### Slice W48-E3-S2 — one failure-cause model

Primary output: execution verdict and first decisive cause are compatible across every report.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E3-S2-T1` | Define typed failure cause, phase, source, reason, evidence link, and legacy mapping. | Eval contracts | Table rejects contradictory verdict/cause combinations. | 0.5d |
| `W48-E3-S2-T2` | Preserve partial phase transcripts and the failing command. | Harness runner | Failure on command two records commands one and two plus primary cause. | 1d |
| `W48-E3-S2-T3` | Propagate the cause through log analysis, grader, verdict, and summary. | Eval reporting | DET-002 is infrastructure/setup, while malformed Markdown remains validation. | 1.5d |

Dependencies: T1 → T2 → T3.

### Slice W48-E3-S3 — self-contained bundle v2

Primary output: a PASS bundle remains fully auditable after harness cache deletion.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E3-S3-T1` | Define conditional bundle inventory, separate eval/product IDs, relative references, and legacy policy. | Result-bundle contract | Fixtures reject dangling links and ambiguous identity. | 0.75d |
| `W48-E3-S3-T2` | Persist actual product run ID, feature selection, and phase metadata. | Eval reports | Successful run has distinct IDs and an existing feature-selection record. | 1d |
| `W48-E3-S3-T3` | Materialize raw attempt logs/exits/events, stage validators, task ledger, and finalization evidence. | Bundle materializer | All references survive deletion of product/harness `.aidd` roots. | 2d |
| `W48-E3-S3-T4` | Atomically seal and validate inventory, digests, sizes, and identities before PASS. | Bundle finalization | Missing/mutated/orphan evidence converts candidate PASS to bundle-integrity failure. | 1d |

Dependencies: E3-S1-T1 + E3-S2-T1 → T1 → T2/T3 → T4.

## Epic W48-E4 — executable scenarios and behavioral conformance

### Slice W48-E4-S1 — typed assertions and a real interview flow

Primary output: every scenario success claim is an executable assertion with exact evidence.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E4-S1-T1` | Add typed `assertions` and explicitly non-gating `notes` to the scenario model. | `scenarios.py` | Unknown assertions fail loading; prose is never inferred as a gate. | 0.75d |
| `W48-E4-S1-T2` | Evaluate assertions into `scenario-assertions.json/md`. | Harness assertion evaluator | Each assertion reports pass/fail/not-observed and one evidence reference. | 1.5d |
| `W48-E4-S1-T3` | Gate deterministic verdicts and bundle sealing on required assertions. | Deterministic eval | Successful commands with missing task/finalization evidence cannot PASS. | 0.75d |
| `W48-E4-S1-T4` | Add a non-browser deterministic answer-and-resume driver and interview scenario. | Deterministic fixture/harness | Persisted assertions observe exact `blocked → answer → resume → continued` with unchanged repair budget. | 1.5d |
| `W48-E4-S1-T5` | Migrate maintained manifests and correct DET-004/scenario-matrix claims. | Scenario manifests/docs | Every retained claim maps to a passing assertion or is labelled a note. | 0.75d |

Dependencies: T1 → T2 → T3; T4 depends on W48-E1 and the merged W47 decision-lifecycle contract;
T5 follows T2/T4 and W48-E3-S3-T4. T4 does not touch `src/aidd/cli/static/**`,
`tests/frontend/**`, or the W47 UI browser journey.

### Slice W48-E4-S2 — source/wheel scenario portability

Primary output: every maintained deterministic lane runs through an explicit toolchain.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E4-S2-T1` | Define source/wheel artifact mode and explicit AIDD/Python commands. | Harness execution model | Both commands remain executable with `python` removed from PATH. | 0.5d |
| `W48-E4-S2-T2` | Repair DET-002 config/setup and migrate implicit interpreter commands. | Deterministic manifests/fixture | DET-002/005/006 run from freshly materialized fixtures. | 1d |
| `W48-E4-S2-T3` | Add discovery-driven maintained-scenario matrix for source and built wheel. | Harness matrix/candidate CI | Discovered scenario IDs × artifact modes exactly equal executed pairs. | 1.5d |

Dependencies: T1 → T2 → T3; T3 follows E4-S1 migration.

### Slice W48-E4-S3 — behavioral adapter conformance

Primary output: conformance proves observable adapter behavior rather than metadata shape.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W48-E4-S3-T1` | Separate declared capabilities from observed conformance results. | Adapter conformance model | A boolean or enum member alone cannot produce behavioral PASS. | 0.5d |
| `W48-E4-S3-T2` | Add fixture vectors for bytes, JSONL, question, exit, timeout, cancellation, cwd, and env. | Adapter fixture | Fixture self-tests reproduce every vector and leave no child process. | 1d |
| `W48-E4-S3-T3` | Preserve generic-cli structured evidence through common finalization. | Generic adapter finalizer | Structured output commits `runtime.jsonl/events.jsonl` and returns paths. | 0.75d |
| `W48-E4-S3-T4` | Execute maintained adapter surfaces against required behavior vectors. | Conformance runner | Breaking log/question/timeout persistence fails the observed dimension. | 1.5d |
| `W48-E4-S3-T5` | Make behavioral conformance required while retaining schema conformance separately. | CI workflow | A deliberate adapter persistence mutation fails the required lane. | 0.5d |

Dependencies: T1 → T2/T3 → T4 → T5; stream vectors depend on W48-E1.

## Wave 48 exit gate

- F-01 through F-10 have focused regression, contract, scenario, or conformance enforcement and
  all required checks are green.
- No stopped execution owner leaves stage/task state `executing` or `validating`.
- Raw bytes remain authoritative; all text views have an explicit decode policy.
- Contracts, run/repair/intervention prompts, and runtime registry share one ownership model.
- DET-004 contains zero false repairs; an injected repair contains exactly one.
- A required interview proves `blocked → answer → resume` rather than file presence.
- A PASS bundle is self-contained, contains distinct eval/product identity, and has no dangling or
  unverifiable claim.
- Ruff, strict mypy, full default pytest, focused browser checks, maintained source/wheel scenarios,
  and behavioral adapter conformance pass.

# Wave 49 — product boundaries and sustainable maintenance

## Goal

Make public promises match supported security modes, reduce extension and change risk, and prevent
planning/document/assurance drift from recurring.

Linked stories: `US-01`, `US-07`, `US-08`, `US-10`, `US-11`, `US-12`.

## Epic W49-E1 — truthful product and provider boundaries

### Slice W49-E1-S1 — project-set policy and implement gate

Recommended product decision: full access promises declaration, attribution, detection, and
fail-closed progression after an outside-root change; preventive containment is promised only for
brokered/isolated modes.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E1-S1-T1` | Publish a mode-specific project-set capability matrix in US-12 and architecture. | Product/docs | Docs gate rejects unconditional containment wording. | 0.5d |
| `W49-E1-S1-T2` | Block aggregate finalization when repository evidence contains outside-set changes. | Core implementation gate | Outside-root change prevents Review/QA and preserves exact path evidence. | 1.5d |
| `W49-E1-S1-T3` | Add two-root positive and outside-root negative implement scenarios. | Deterministic scenarios | Positive run changes both roots; negative run stops progression. | 2d |
| `W49-E1-S1-T4` | Align UI copy with detected/rejected versus preventively contained modes. | Frontend presentation | DOM/browser fixtures distinguish full-access warning from enforced containment. | 0.5d |

Dependencies: T1 → T2/T4 → T3, plus `W47-E1-S4-T2` → T4. T4 must reuse the merged Focus Canvas
components and terminology rather than introducing a parallel presentation pattern.

### Slice W49-E1-S2 — adapter-owned provider metadata

Primary output: adding a runtime does not require provider literals or credential filenames in
runtime-neutral core.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E1-S2-T1` | Define adapter security/capability descriptor. | Adapter protocol | Descriptor contract covers protected paths, credentials, config, and capabilities. | 0.75d |
| `W49-E1-S2-T2` | Implement descriptors for built-in runtimes. | Adapter packages | Table test resolves every maintained runtime descriptor. | 1.5d |
| `W49-E1-S2-T3` | Consume protected-path metadata and remove provider literals from core. | Runtime policy | Existing security matrix passes; provider literals are absent from core. | 1.5d |
| `W49-E1-S2-T4` | Drive built-in registration/config compatibility from descriptors. | Adapter registry/config | Existing TOML/runtime IDs remain compatible without central provider branches. | 2d |
| `W49-E1-S2-T5` | Prove clean extension with an allowlisted fake external descriptor. | Architecture/conformance test | Fake runtime needs adapter-local code and matrix row, not a core edit. | 1d |

Dependencies: T1 → T2 → T3/T4 → T5.

## Epic W49-E2 — behavior-preserving hotspot reduction

### Slice W49-E2-S1 — live harness decomposition

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S1-T1` | Characterize public live-facade artifact and event ordering. | Harness tests | Current and extracted paths produce equivalent normalized artifacts. | 1d |
| `W49-E2-S1-T2` | Remove the unreachable 14-function `_legacy_*` process island. | Live orchestrator | No legacy implementation remains; characterization stays green. | 0.5d |
| `W49-E2-S1-T3` | Extract stage execution/inspection. | Harness stage module | Stage terminal/blocked fixtures remain equivalent. | 1.5d |
| `W49-E2-S1-T4` | Extract frontend probes and semantic-failure classification. | Harness probe module | Probe state matrix preserves every decision. | 1.5d |
| `W49-E2-S1-T5` | Extract bundle/report coordination behind the facade. | Harness report module | Success/blocked/manual-stop bundles remain equivalent. | 1.5d |

Dependencies: T1 → T2 → T3 → T4/T5. Begin only after W48 evidence semantics are stable and
`W47-E1-S4-T2` has reconciled the final Focus Canvas journeys; otherwise the frontend-probe
characterization would be stale before extraction starts.

### Slice W49-E2-S2 — post-Focus-Canvas service-boundary stabilization

Primary output: server-side UI orchestration is decomposed without revisiting W47 presentation or
changing its public behavior.

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S2-T1` | Extract UI job registry/lifecycle from `cli/ui.py`. | CLI application service | Two-project job lifecycle tests preserve isolation. | 1.5d |
| `W49-E2-S2-T2` | Extract HTTP payload codecs/controller dispatch. | CLI transport | Endpoint contract suite preserves status/body shapes. | 2d |
| `W49-E2-S2-T3` | Replace dashboard `_next_action` branching with ordered typed rules. | Core dashboard evidence | Full state matrix yields exactly one deterministic action. | 1d |

Dependencies: merged W47 UI PR and a green post-merge CLI/frontend/browser compatibility baseline.
Before promoting each task, compare it with the final W47 diff. If W47 already produced the output,
record that evidence and reslice only the remaining hotspot; do not repeat the refactor.

### Slice W49-E2-S3 — complexity-tail ratchet

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E2-S3-T1` | Add a reviewed complexity baseline and no-new-E/F ratchet. | Quality tooling | Synthetic new E/F block fails the check. | 1d |
| `W49-E2-S3-T2` | Decompose `build_task_flow_checkpoint`. | Task checkpoint | Complexity is C or lower and checkpoint fixtures are byte-equivalent. | 2d |
| `W49-E2-S3-T3` | Decompose `_validate_scenario_contract`. | Scenario validation | Complexity is C or lower and invalid-manifest matrix is unchanged. | 1.5d |
| `W49-E2-S3-T4` | Decompose `run_single_stage_orchestration` after W48. | Core stage lifecycle | Transition matrix remains green and complexity is C or lower. | 2d |
| `W49-E2-S3-T5` | Decompose the Codex live transport. | Codex adapter | The Codex adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |
| `W49-E2-S3-T6` | Decompose the Qwen live transport. | Qwen adapter | The Qwen adapter passes the bytes/events/timeout/cancel matrix. | 1.25d |

Dependencies: T1 first; every remaining task is independent and behavior-preserving.

## Epic W49-E3 — planning and documentation truth

### Slice W49-E3-S1 — executable planning hygiene

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E3-S1-T1` | Define parent-status algebra, including parked-child semantics and archive authority. | Planning contract | Examples for done/planned/parked/blocked are unambiguous. | 0.5d |
| `W49-E3-S1-T2` | Archive 509 historical reconciliation bullets, leaving one current note. | Backlog/history docs | All IDs remain discoverable and active backlog is bounded. | 1d |
| `W49-E3-S1-T3` | Add bounded-note and parent-status roll-up validation. | Planning integrity tests | Second note and stale completed parent fail; parked child follows explicit rule. | 1.5d |
| `W49-E3-S1-T4` | Reconcile current wave/epic/slice statuses mechanically. | Roadmap | Roll-up checker reports no mismatch. | 1d |

Dependencies: T1 → T2/T3 → T4.

### Slice W49-E3-S2 — executable user-story traceability

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E3-S2-T1` | Correct optional-frontmatter and superseded beta-audit wording. | Architecture/analysis docs | Docs agree with product contract and current US-13 set. | 0.5d |
| `W49-E3-S2-T2` | Define a structured US-01…US-13 registry linking contracts, code boundaries, tests, scenarios, and evidence. | Product traceability data | Every reference exists and story IDs are unique. | 1d |
| `W49-E3-S2-T3` | Generate and validate a byte-stable traceability view in CI. | Docs tooling | Removing a required test/scenario reference fails generation. | 1.5d |

Dependencies: T1/T2 → T3.

## Epic W49-E4 — assurance ratchets

### Slice W49-E4-S1 — formatter baseline

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E4-S1-T1` | Decide formatter scope/exclusions and apply one isolated mechanical baseline. | Python formatting | Ruff/mypy/tests pass and no semantic AST change is introduced. | 1.5d |
| `W49-E4-S1-T2` | Add `ruff format --check .` to CI. | CI | Intentional format drift fails the required check. | 0.5d |

Run this after hotspot refactors to avoid permanent merge conflicts.

### Slice W49-E4-S2 — critical-module coverage

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E4-S2-T1` | Record line/branch coverage for lifecycle, evidence, adapters, and scenario gates. | Coverage tooling | JSON baseline is tied to SHA and exact command. | 1d |
| `W49-E4-S2-T2` | Add non-decreasing per-module thresholds in one CI job. | CI coverage gate | Synthetic critical-module regression fails without chasing a global vanity number. | 1.5d |

### Slice W49-E4-S3 — browser JavaScript security analysis

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W49-E4-S3-T1` | Add JavaScript/TypeScript CodeQL analysis for packaged frontend source. | Security workflow | Python and JS analysis results are both uploaded. | 0.5d |

New CodeQL findings become separate triage/fix tasks; they are not fixed inside the workflow task.

## Wave 49 exit gate

- US-12 wording and behavior agree for full-access versus brokered/isolated modes.
- Outside-project-set changes cannot silently qualify aggregate finalization.
- A new adapter does not require provider literals in runtime-neutral core.
- W48 behavior remains unchanged after hotspot decomposition.
- No new E/F complexity block is admitted.
- Active backlog is bounded and status roll-up is machine-checked.
- Story traceability is generated and complete.
- Formatter, critical-module coverage, and Python/JavaScript security gates have reviewed baselines.

Required before beta: E1, E3, and any E2 item needed to safely maintain W48 code. Remaining E2/E4
tasks may be accepted as explicit P2/P3 debt if they do not contradict a public beta signal.

# Wave 50 — current and retrievable beta acceptance

## Goal

Produce one exact-candidate decision whose deterministic, browser, install, provider, and human
evidence is current, immutable, and retrievable.

## Epic W50-E1 — evidence freshness and retention

### Slice W50-E1-S1 — freshness model

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W50-E1-S1-T1` | Define `current/stale/incompatible/unavailable` from SHA, schema, target pin, and locator. | Evidence contract | Historical `adbc73f…` bundle is stale on a different candidate SHA. | 0.5d |
| `W50-E1-S1-T2` | Project freshness consistently into reports and UI. | Evidence read model | Service/DOM fixtures show state and reason without changing verdict history. | 1d |

Dependencies: T1 → T2; the UI projection in T2 additionally depends on merged W47 and must preserve
the Focus Canvas information hierarchy.

### Slice W50-E1-S2 — immutable sanitized bundle export

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W50-E1-S2-T1` | Define retention locator, digest, size, revision, target pin, and redaction contract. | Evidence archive contract | Contract rejects a locator without integrity/provenance metadata. | 0.5d |
| `W50-E1-S2-T2` | Export and read back a sanitized immutable archive. | Bundle exporter/verifier | Fresh checkout verifies the archive after mutable `.aidd` deletion. | 1.5d |

Dependencies: E1-S1 and W48 bundle v2 precede archive export.

## Epic W50-E2 — exact artifact candidate gate

### Slice W50-E2-S1 — freeze and local acceptance

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W50-E2-S1-T1` | Freeze candidate SHA, source tree, wheel digest, scenario inventory, and test commands. | Candidate manifest | Record is complete and worktree is clean. | 0.5d |
| `W50-E2-S1-T2` | Run full static/unit/integration/browser/security/build gates, including the W47 Focus Canvas packaged-browser journey, on the frozen candidate. | Candidate CI | One signed/hashed readiness record links every required result. | 1d |
| `W50-E2-S1-T3` | Run installed deterministic happy/failure/repair/interview/task/project-set/bundle matrix. | Candidate eval | Exact wheel passes every typed assertion with self-contained bundles. | 1d |
| `W50-E2-S1-T4` | Verify `pipx` and `uv tool` clean install and upgrade for the exact wheel. | Release verification | Installed version and wheel digest match candidate manifest. | 0.5d |

Any behavior or evidence-schema change invalidates T1–T4.
Earlier W47 UI evidence is historical after W48/W49 changes and cannot substitute for the T2
frozen-candidate rerun.

## Epic W50-E3 — provider and human acceptance

### Reuse existing tasks instead of creating duplicates

| Existing task | Required outcome in this plan |
| --- | --- |
| `W46-E1-S2-T4` | Two-project navigation/isolation browser evidence on the candidate. |
| `W46-E2-S2-T4` | Responsive long request/task content evidence. |
| `W42-E7-S2-T3` | One genuine uncoached first-time operator observation. |
| `W36-E7-S3-T2` | Five first-time operator sessions; W42 observation counts only if both protocols match. |
| `W36-E7-S3-T3` | Reconcile observed usability findings before a decision. |
| `W36-E7-S4-T4` | Claude run on the exact candidate SHA and target pin. |
| `W36-E7-S4-T5` | Final same-revision Codex/Claude acceptance report. |
| `W43-E5-S2-T3` | Lower-capability comparison or explicit environment-blocked result. |

One new Codex candidate-run task should be added under the existing `W36-E7-S4` provider
acceptance slice using the next verified free task ID; do not overwrite historical T3 evidence.

### Slice W50-E3-S1 — final decision pack

| Task | Output | Dominant area | Main verification | Effort |
| --- | --- | --- | --- | ---: |
| `W50-E3-S1-T1` | Validate that every reused acceptance task targets the same candidate identity. | Acceptance coordinator | SHA, wheel, target, schema, and scenario mismatch blocks synthesis. | 0.5d |
| `W50-E3-S1-T2` | Publish one beta-readiness decision with accepted residual P2/P3 debt. | Release/analysis report | Every claim links to a retrievable verified bundle; blockers cannot render as PASS. | 1d |

Dependencies: all W50-E1/E2 tasks and the reused acceptance tasks.

## Wave 50 exit gate

- exact candidate SHA/tree/wheel identity is frozen and consistent everywhere;
- all required local and installed-artifact gates pass;
- Codex and Claude evidence is same-revision and retrievable;
- lower-capability and human evidence is complete or explicitly environment-blocked where the
  product gate permits that outcome;
- uncoached findings are reconciled rather than silently ignored;
- every PASS claim resolves to a sanitized immutable bundle with verified digests;
- zero audit P1 remains open;
- residual P2/P3 items have explicit owner, rationale, and acceptance decision.

## Cross-wave dependency path

```text
adjacent W47 Focus Canvas merge
  -> post-merge UI compatibility baseline -------------------------\
W48-E1 terminal safety
  -> W48-E3 lineage/taxonomy/bundle
  -> W48-E4 executable scenarios/conformance
  -> W48 exit gate
  -> W49-E1 product-boundary truth + W49-E3 planning/docs truth
  -------------------------------------------------------> W50 candidate freeze
  -> deterministic/browser/install gates
  -> provider and human tasks
  -> immutable archive
  -> beta-readiness decision
```

W49-E2 refactors and W49-E4 assurance work can proceed after W48 in independent branches, but
must merge before candidate freeze if they are included in the beta scope.

## Existing-roadmap relationship

| Audit area | Related predecessor or concurrent work | Why this plan is not a duplicate |
| --- | --- | --- |
| Operator UI | Active adjacent W47 Focus Canvas rollout | W47 owns presentation and UI acceptance; this plan only integrates its merged result and sequences server-side hotspot work afterward. |
| Stage exception safety | `W34-E2-S1-T3`, `W36-E7-S4-T42` | Prior work covers adapter exception/abandoned execution, not the full post-`validating` boundary. |
| Task recovery | `W35-E2-S5-T3`, `W46-E3-S1-T1`, `W46-E3-S3-T1` | New acceptance covers corrupt evidence during synchronous executor-failure recovery. |
| Ownership | `W43-E1-*` | Registry/core protection landed; repair/intervention wording and bidirectional authority remain inconsistent. |
| Repair evidence | `W43-E2-S2-T1`, `W36-E7-S4-T24`, `W43-E5-S1-T1` | Lifecycle semantics exist; eval projection still infers repair from attempt ordinal. |
| Scenario coverage | `W35-E2-S4-T2`, `W43-E5-S1-*`, `W46-E3-S3-T1` | Existing fixtures do not make all manifest claims executable or perform a true deterministic interview. |
| Bundle integrity | `W34-E5-S2-T2`, `W36-E7-S4-T49/T50` | Live patterns exist; deterministic PASS bundles do not yet inherit the same self-contained guarantees. |
| Project-set | `W20-E3-*`, `W21-E2-S1`, `W29-E3-S1` | Declaration/evidence/UI exists; mode-specific promise and implement-level outside-root gate are missing. |
| Planning hygiene | `W15-E2`, `W34-E8-S1` | The bounded backlog outcome regressed; automated roll-up/current-note checks prevent recurrence. |
| Browser/provider/human acceptance | W36/W42/W43/W46 parked tasks | Existing IDs are dependencies, not recreated work. |

Do not reopen completed tasks or rewrite their historical status. Add the proposed tasks as explicit
follow-up work with the new regression signal.

## Verification ladder for every implementation task

1. Run the smallest focused test named in the task.
2. Run the owning package/module test neighborhood.
3. Run Ruff and strict mypy when Python changes.
4. Run docs/planning/prompt consistency when contracts or prompts change.
5. Run deterministic scenario assertions when lifecycle/evidence semantics change.
6. Run the full default Python suite before slice completion.
7. Run source/wheel, browser, security, and build gates before wave completion.
8. Run real providers only after the deterministic wave gate is green.

## Definition of done for the remediation program

- code, contracts, prompts, validators, scenarios, and reports express the same semantics;
- every completed process has a terminal stage/task state;
- every scenario claim is executable or explicitly non-gating;
- every PASS bundle is self-contained, provenance-correct, and retrievable;
- all 13 user stories have current traceability and an evidence freshness state;
- planning sources are bounded and machine-consistent;
- no public beta claim exceeds the behavior proven for the exact candidate artifact.
