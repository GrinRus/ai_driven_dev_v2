# Iterative Delivery Contract

Status: accepted target contract for `W57-E1-S1-T1`, recorded on **2026-10-01**.
The [nine accepted decisions](iterative-delivery-decisions.md) own the policy choices;
this document specifies their records, ownership, eligibility, and migration boundaries.
It does not claim that these services or formats are implemented in the current alpha.
The [roadmap](../backlog/roadmap.md) owns implementation and acceptance tasks.

## 1. Delivery and ownership

One Work Item represents an authorized delivery objective. One iterative policy selects
finite preparation routes, executes dependency-ready tasks, and corrects them within shared
limits. A changed plan creates a child run; an ordinary fix with an unchanged compatible
plan creates another attempt in the same run. Complete means current evidence supports
the required behavior and all terminal quality/publication gates have passed.

| Owner | Authoritative responsibility | Boundary |
| --- | --- | --- |
| Operator | Original request, explicit answers, scoped product decisions, authorized check registration, manual acceptance where needed. | Opening a document, permitting a runtime operation, and model sign-off do not authorize product changes. |
| Core | Source/decision eligibility, route and predecessor map, check selection, task dependencies, invalidation, budgets, lifecycle and completion policy. | No provider/model-specific progression logic or runtime process launch. |
| Application | Compose source, task, verification and assessment services; execute checks through an injected process port; persist/publish records; expose one CLI/UI projection. | No harness orchestration dependency and no second frontend controller. |
| Runtime through adapter | Substantive Markdown outputs, code changes, attributed observations/proposals; adapter retains raw runtime logs and observable runtime events. | Cannot write canonical authority, registration, receipt, assessment, validator or stage-result state. |
| Validators | Markdown structure, actual reference resolution, revision/identity checks, declared coverage and cross-document consistency. | Reference integrity is not a proof of natural-language meaning or complete product coverage. |
| Harness/evals | Independent scenario expectations, graders, comparisons and retained audit bundles. | An eval transcript cannot substitute for a product verification receipt. |
| CLI/UI | Read the shared projection; submit identified operator actions through application services; show exact retained evidence and raw logs. | No eligibility derived from prose, synthetic progress or client-local decisions. |

Runtime-authored stage outputs remain Markdown. AIDD-owned typed state may use current
JSON/JSONL storage; a readable Markdown projection does not become a second source of truth.
The current [document ownership matrix](../../contracts/documents/ownership-matrix.md)
continues to govern the current alpha until implementation replaces its affected rows.

## 2. Record contracts

Every persisted record has an immutable ID, explicit contract revision, Work Item/project
attribution, producing actor/event, timestamp and content digest. References bind the exact
record revision and digest, not a mutable latest filename. Updates create revisions/events;
they do not rewrite sealed predecessor records. Unknown or unavailable data is explicit.

| Record | Required content | Authoritative writer |
| --- | --- | --- |
| Source snapshot | `source_id`, revision, kind, full original bytes/digest, originating request/answer/authorized project configuration, actor/event, declared scope, exact fragment locators/digests and preserved surrounding context. | AIDD records operator input without rewriting it. |
| Criterion | `criterion_id`, revision, literal source wording, exact `source_refs`, constraints/non-goals, authority and decision refs, required flag, registered check refs and assessment policy. Interpretations, observable cases and negative examples are separately attributed proposals. | AIDD binds source-backed content or an explicit scoped decision; runtime can propose it. |
| Product decision | `decision_id`, QID when applicable, answer/source revision, affected criterion/task revisions, question/options, explicit choice and consequence, actor/event, authority scope, status and application refs. | Operator authorizes; AIDD records and projects it. |
| Task plan | Immutable plan revision/digest; Markdown task cards with stable task IDs, criterion refs, outcome/scope, dependencies, allowed changes, check refs and verification/assessment requirements. | Runtime authors Markdown; AIDD validates and binds eligible inputs. |
| Revision map | Parent/child plan and source revisions; criterion/task mapping as retained, changed, removed, new or ambiguous; input fingerprints; affected dependency closure; carry-forward and proof-refresh decisions with source attempt refs. | Core validates the mapping and its consequences. |
| Check definition | Check ID/revision/digest; authority source/registration event; exact argv or declared shell form; bounded parameters; cwd/project set; prerequisites; timeout; expected process outcome; applicability/mandatory rules; declared input manifest and environment/tool identity policy. | Authorized configuration, scenario or operator registration through AIDD. |
| Behavioral oracle | Oracle ID/revision/digest, literal expected behavior, independent source/owner, applicable criteria, evaluation method, fixtures/counterexamples, sealed-before-implementation event and independence qualification. | Authorized independent source or scoped operator assessment policy. |
| Check execution/receipt | Execution ID and process ownership; Work Item/run/stage/task/attempt refs; check revision, actual command/cwd, consumed source/criterion/oracle revisions, code/input/config/tool identity; start/end/duration; actual exit/timeout/cancel/unavailable result; stdout/stderr refs; sealing event/digest. | AIDD verification service, using observations from its injected executor. |
| Criterion assessment | Criterion/source/decision/oracle revisions, assessor and method, current receipt/change/observation refs, input fingerprint, confirmed/rejected/inconclusive/not-assessed status, rationale and timestamp. | AIDD applies an independent oracle or records a scoped operator observation. Model conclusions remain advisory. |
| Run identity | Work Item/run/parent/root IDs, stable creation key, sole policy and contract revision, route/reason, selected operations, predecessor input map, exact source/plan/config/runtime selectors, shared objective budget ref and publication state. | AIDD; pinned before execution. |
| Controller event | Stable action ID, run/task/attempt/execution refs, action/reason, decisive facts and fingerprint, budget reservation/debit, progress observation, resulting child/attempt/receipt refs. | Core policy through application persistence. |

Product authority has `authorized`, `proposed`, `conflicting` or `superseded` status.
Check execution has `not-run`, `running`, `passed`, `failed`, `timeout`, `cancelled`,
`unavailable` or `skipped` status. Proof freshness separately has `current`, `stale`,
`incompatible` or `unavailable` status. Behavioral assessment has `confirmed`, `rejected`,
`inconclusive` or `not-assessed` status. No dimension implies another.
Delivery completion requires a **current confirmed assessment for every required criterion**
and passed current required checks. Rejected, inconclusive or not-assessed required behavior
permits only a blocked, stopped or partial outcome, regardless of document consistency.

Decision application distinguishes recorded, resolved, applied, invalidated and conflicting.
Resolved means an identified answer was saved. Applied additionally requires the affected
input revisions to consume that answer and current behavioral assessment to support its
effect. A correct QID link with wrong behavior is not applied acceptance.

### Source coverage and authority

Preserve the entire request and answers, including context and constraints. A generated
paraphrase cannot replace literal criterion wording or gain authority by being copied to
another generated document. A material addition, conflict, omitted constraint or ambiguous
interpretation requires a scoped question/decision before affected implementation.
Technical decomposition within unchanged authorized scope does not need blanket plan approval.

Maintain a source-fragment inventory and explicit criterion/task dispositions so declared
requirements and constraints cannot disappear between stages. Deterministic validation
checks existence, bounds, digests, related IDs and declared coverage. It does not certify
that model-selected fragments capture every implication of free text. Retain that limitation
in assessments; use an independent expectation, counterexample or scoped human judgment
where meaning cannot be established objectively. An unknown material interpretation blocks
the affected work rather than becoming an automatically authorized proposal.

### Execution authority and independent expectations

Select applicable registered checks by declared project/path/criterion/task rules; the
required set is the union of mandatory project rules and applicable criterion/task rules.
Missing/ambiguous applicability blocks verification; a runtime cannot remove a mandatory
check. New or expanded commands, cwd, prerequisites or parameter bounds require registration.
Ordinary repeats of an unchanged registered definition do not require another approval.
This registry supplies execution authority, not a sandbox or a behavioral answer key.

An oracle is independent only when its expected behavior comes from an authorized source
outside the implementation-producing chain, such as an existing regression expectation,
scenario fixture or scoped operator choice. Sealing a model's own generated expectation
does not establish independence. A model may propose a test or help implement an oracle;
its expected values still need independent provenance. A check exit code supports only its
declared observation. It cannot confirm arbitrary natural-language or subjective behavior.

## 3. Identity and freshness

A receipt binds the actual consumed inputs: exact source/answer/criterion/check/oracle and
configuration revisions; selected parameters/cwd/project set; tool/lock/environment identity;
and repository content including committed, dirty and untracked files. The declared input
manifest also identifies relevant ignored/generated inputs and external service/data versions.
Secrets are redacted; use appropriate fingerprints rather than persisting secret values.

Distinguish verification byproducts from inputs. If a generated file influences behavior,
it is an input; classifying it as a disposable byproduct cannot hide its change. Unknown
external state or unpinned nondeterminism yields an explicit limitation or inconclusive
assessment, not reproducibility inferred from Git SHA alone.

Freshness compares these identities, not timestamps or a model's report. A changed input
makes dependent proof stale or incompatible. Preserve the original receipt; rerun checks
without rerunning implementation when only proof needs refresh. Required final checks
execute against the final tree after finalization mutations. Missing required inputs,
partial execution and all-skipped required checks cannot become a passing gate.

Manual acceptance binds the exact current behavior/source/tree observed by the operator.
Material changes invalidate it just as they invalidate automated assessment. Seal receipts
and assessments only after reconciliation; uncertain interrupted execution retains its
partial records and cannot publish a fabricated terminal result.

## 4. Finite preparation routes

The replacement has one iterative delivery policy, with no classic/iterative selector.
Persist selected operations, their predecessor references and the route rationale before
execution. Existing stage identifiers remain useful; verification is an AIDD service/gate,
not a model-authored successful stage.

Source eligibility means a pinned immutable full source snapshot and fragment inventory;
every declared required fragment has a criterion, an explicitly authorized non-goal/scope
disposition, or a blocking scoped decision. Supporting context remains attached. Missing
references, unresolved material ambiguity and unresolved requirement dispositions block
affected task preparation/implementation. Before tasklist can become executable, every
required criterion also has registered applicable checks and an independent-or-manual
assessment policy. These predicates apply to every route; a model's assertion of eligibility
cannot satisfy them. Structural coverage retains the meaning limits from section 2.

| Route | Required facts and selected preparation | Downstream gates |
| --- | --- | --- |
| Focused | The source-eligibility predicates above hold; ownership and checks/oracles are known; no material interface/design uncertainty. `idea → tasklist`. | Task implementation/checks, aggregate final-tree verification, review and QA. |
| Investigate | Repository/ownership/verification facts are missing but resolvable without authorizing an unresolved product decision. `idea → research → tasklist`; findings must satisfy the same source/check/assessment predicates before executable tasks; escalate to design when needed. | Same required implementation, verification, review and QA gates. |
| Design | Material interface/contract/dependency effects require a design. `idea → plan → review-spec → tasklist`, with research selected first when repository facts are missing. | Same gates plus validated design and review-spec inputs. |
| Correction | A child replan selects one of the above routes for the affected scope, reusing only explicitly eligible immutable prerequisites. | Re-execute affected tasks/dependents, refresh required proof and downstream quality gates. |

Selection uses explicit source/scope/ownership/check/oracle/interface/unknown facts. A model
observation is attributed input, not a confidence-based permission to shorten preparation.
Uncertain repository facts select investigation; unresolved product authority asks a durable
question; known material design effects select design. The operator can request more depth.
New material facts that change the plan/route create a child run with a revision map.

| Omitted current prerequisite | Explicit replacement |
| --- | --- |
| `research-notes.md` in a route without research | Source-bound known repository/ownership/check facts with exact references; unresolved material facts prevent omission. |
| `plan.md` in focused/investigate | Eligible criteria, source constraints and compact task cards expressing scope/dependencies/checks; no fabricated plan file. |
| `review-spec-report.md` without design | Deterministic source/reference/task eligibility and necessary scoped decisions; no synthetic model sign-off. |
| Previously executed preparation in correction | Exact parent run/input revisions plus compatible carry-forward validation; never mutable Work Item latest files. |

`not-selected` is an operation disposition, not `succeeded`. Direct-stage entrypoints use
the same route/input eligibility rules as a full run. Selected operation progress and
criterion assessment replace universal eight-stage completion; omitted preparation never
removes required terminal checks, review or QA.

## 5. Iteration and carry-forward

Plan changes create a child of the same Work Item. A new independent goal creates a new
Work Item; the existing next-flow concept is not the identity of a correction iteration.
Resolve every consumed artifact from the run's immutable input map. Parent failures can
supply only individually validated, explicitly eligible inputs; failed/blocked aggregate
state does not confer source authority or completed task status.

Retained work requires unchanged compatible source/criterion meaning, constraints, task
scope/dependencies and check authority, plus proof that the code/result remains present.
Revision maps retain the original attempt and change attribution. IDs or equal links alone
do not establish compatibility; ambiguous mappings ask/stop. Changed/new tasks and the
affected dependent closure execute again. Removed work requires an eligible scope decision
or technical decomposition mapping within the same authorized outcome.

Carried work is `reused`, not a newly executed successful attempt. Its stale receipts are
refreshed independently. Whole-tree receipts from a parent cannot prove a child's final
tree. If an affected change invalidates terminal review/QA, rerun the relevant gates.

There is one mutating checkout lease. Stop and reconcile predecessor executions before a
child can mutate that checkout. Publish child inputs via prepared, validated and committed
states; only committed complete input maps are executable. Bind a stable child creation key
to parent, decision/source evidence and policy revision. Replaying the transaction returns
the same child and one budget reservation/debit; it cannot create orphan duplicate children.

## 6. Bounded controller and recovery

The controller chooses from `continue`, `fix`, `verify`, `replan`, `ask`, `complete` and
`stop`. Document repair, runtime retry, answer continuation, task fix, check rerun and
child replan retain distinct attempt/action kinds. A failed attempt is retained and stops
that attempt; an explicit eligible correction action may follow without skipping to an
unrelated next task.

| Condition | Eligible next action |
| --- | --- |
| Cancellation, an action that would exceed its applicable count bound, exhausted active time, unsupported input or uncertain unreconciled process | Stop/reconcile the affected action; do not launch an over-budget or unreconciled execution. |
| Material unresolved product decision, check registration or required human assessment | Ask for the identified scope/evidence; continue only unaffected eligible work. |
| Valid implementation with missing/stale required proof | Verify through the registered executor, without a new implementation attempt. |
| Failed check or actionable review/QA finding, unchanged compatible plan, fix within scope | Fix the affected task, then verify and refresh invalidated gates. |
| Evidence requires a changed plan/route within authorized bounds | Replan into an idempotently created child with explicit invalidation. |
| Dependency-ready task with eligible inputs and available bounds | Continue that task. |
| All required tasks have valid executed/reused results, required final checks are current and passed, every required criterion has a current confirmed assessment, review/QA are validated, and the AIDD-owned internal immutable handoff is committed | Complete. This does not authorize external publication/release. |
| No eligible action or repeated equivalent failure without observed progress | Stop with retained decisive facts, or ask the specific unresolved question. |

Persist a Work Item objective budget with finite `max_execution_starts`,
`max_child_iterations` and `max_elapsed_seconds`, consumed counters, reservation IDs,
an optional enforceable cost cap and cost-telemetry availability. Every actual runtime
invocation or check process start consumes one execution start exactly once; retries,
repairs and fixes do not obtain free starts. A committed child creation consumes one
iteration exactly once. Time belongs to the root objective across children/resume.
As accepted on 2026-10-05, `max_elapsed_seconds` limits accumulated active automation time.
Exclude waiting for an operator answer or an explicit operator pause only after every
execution is confirmed stopped/terminal. Waiting while another task/check still runs
continues to consume time. Count overlapping active intervals once for the objective;
persist their boundaries and excluded waiting intervals. Resume and child creation retain
consumed time, and human waiting alone does not expire the objective. Unreconciled process
ownership or missing observations cannot fabricate a free pause. Process-specific timeouts
remain independent. See [baseline decision P01](iterative-delivery-decisions.md#p01-objective-time-accounting).

The accepted initial pilot limits are **40 execution starts, 3 child iterations and 7200
seconds (2 hours) of active time**, recorded on 2026-10-05 in
[P02](iterative-delivery-decisions.md#p02-pilot-automation-limits). The root run is not a child.
The last admitted execution/child is permitted; refuse actions needing another exhausted
count unit. An admitted child may continue within remaining execution/time capacity without
creating a further child. Reaching the time cap stops active work with partial evidence
retained. Quality gates remain required, and the controller cannot raise/reset limits or
remove checks to make the pilot pass. These starting values are unmeasured target settings,
not current runtime configuration or proof of an adequate budget.

Cost is attributed where available; unavailable is not zero. A mandatory unenforceable cost
cap blocks. Numeric defaults, the accepted time-accounting policy and no-progress thresholds are pinned
with the baseline protocol in `W57-E1-S1-T2` before evaluation, not tuned per failed trace.

Progress fingerprints bind the affected criterion/task/check, normalized failure/expected
observation, input identity and resulting evidence. Observable progress includes resolving
a named blocker, passing a previously failing applicable check, or an eligible task result.
A changed plan digest, renamed finding or model claim alone is not progress. Counters and
the failure chain persist across child creation.

As accepted on 2026-10-05 in [P03](iterative-delivery-decisions.md#p03-correction-loop-no-progress-threshold),
stop automatic correction for the same blocking problem after **two consecutive completed
correction-and-check cycles without confirmed improvement**. Initial defect discovery does
not count as a correction cycle. Problem lineage follows compatible criterion/task/check
or validator-finding revisions across children; a new code/input digest or unrelated task
success cannot reset it. Confirmed improvement addressing that blocker restarts only its
consecutive no-progress count, preserving all objective usage and earlier evidence.
Ambiguous progress/lineage asks/stops. At the threshold, surface retained attempts/evidence
for an explicit scoped operator action; no additional automatic correction or child can
bypass it. Independent process timeouts and immediate eligibility/authority stops remain.

Reserve an execution identity/budget before launch, retain process ownership and observations,
and reconcile exit/cancellation/timeout before sealing its result. After a crash, discover
whether the execution is running, terminal or unknowable before retry. Unknowable is an
explicit stop requiring resolution; never assume the command did not run. Cancellation
retains partial stdout/stderr, receipts and the first decisive failure. External effects
are not made exactly-once by an internal idempotency key.

CLI/UI show the same current action, reason, consumed/remaining limits, evidence gaps and
stop/cancel control. A saved product answer does not implicitly resume a paused run;
ordinary corrections in an already authorized active run may proceed within these limits.
Release, publication and other separately authorized external actions retain their boundary.

## 7. Direct breaking cutover

Ship one complete replacement candidate after acceptance. Internal tasks may be reviewed
separately, but the release must align core/application, current state, Markdown contracts,
prompts, validators, CLI/UI, harness, packaged resources and operator guidance. No public
opt-in coexistence lane, temporary classic default, compatibility reader, alias, converter
or in-engine rollback is part of this migration.

Current run/config/manifest/ledger formats identify the iterative format family and exact
supported contract revision. Preflight rejects missing/unsupported identity before workspace
or state mutation. An explicit recreation action creates current work from operator-selected
source content; it does not import old success/authority/receipt state or promise old resume.
Retain original Markdown/log/bundle bytes for direct/archive inspection. Reading those bytes
does not require interpreting the retired machine-state schema.

The baseline is the pinned earlier package/revision in its own checkout/environment and
compatible retained workspace. Compare that baseline with the new candidate using the same
tasks/independent oracle and declared runtime/model/environment controls; record intentional
AIDD/prompt differences. Rollback returns explicitly to that earlier version/workspace.
It never rewrites new runs to make them resumable by the earlier engine.

Candidate correctness, deterministic/browser/native behavior, real operator understanding,
runtime support tiers and installation gates remain required. No-go keeps the candidate
unaccepted. Final checks bind the exact final candidate after cutover/cleanup changes;
an earlier readiness report does not qualify a subsequently changed package for release.
`W59-E2-S1-T3` assesses implementation readiness before final packaging/cutover work;
`W59-E2-S2-T4` is the final release-readiness gate. Retained human observations require
explicit scope/impact/revision validation against final behavior; changes to observed
behavior or UI require new observations rather than re-labeling the earlier evidence.

As accepted on 2026-10-05 in [P04](iterative-delivery-decisions.md#p04-mandatory-acceptance-and-overhead-diagnostics),
correctness against independent expectations, truthful evidence and real operator understanding
are mandatory. Measure time/cost, operator reading/decision effort and document/prompt volume
without a mandatory 10% or 25% improvement gate for the first replacement. Pin comparison
definitions and report unavailable metrics honestly. These diagnostics cannot compensate for
quality failures or weaken recovery, runtime-tier, browser, installation or P01–P03 limits.
As accepted on 2026-10-06 in [P05](iterative-delivery-decisions.md#p05-first-replacement-operator-observation),
observe five eligible first-time operators from the target audience who did not implement
or review the UI. At least four must complete the predeclared key comprehension/decision/
recovery tasks without coaching. A serious interface-caused error in any session blocks
acceptance, including the participant outside that success threshold. Preserve every
session, assistance and failure; no scripted substitution or post-hoc selection of successes.
Exact tasks, severity/scoring rules, matched order and scenario/oracle definitions remain
baseline-protocol work; this choice is not completed observation or recruitment authority.
As accepted on 2026-10-06 in [P06](iterative-delivery-decisions.md#p06-native-comparison-repetitions),
compare four mandatory task classes with three independent repetitions per class/version:
twelve native scenario trials per version, twenty-four per declared runtime configuration.
Start from matched pinned original state, retain all outcomes and keep runtime/model/
reasoning/environment controls explicit. A scenario trial contains its own executions and
possible children; it is not one execution start. Runtime tiers and separate adversarial,
browser, installation and human lanes remain required.
As accepted on 2026-10-06 in [P07](iterative-delivery-decisions.md#p07-native-acceptance-and-external-failure-replacement),
each candidate case requires the expected outcome in all three counted repetitions.
After a diagnosed external failure and confirmed prerequisite recovery, replace only the
interrupted trial under matched controls, retaining the original attempt and compatible
observations. Unknown causes block acceptance; wrong behavior, poor model output and budget
exhaustion remain unsuccessful. Product fixes require new evidence on the changed candidate.
Reconcile scope/identity/freshness before retaining other results; runtime-tier release
consequences remain unchanged. Exact cases/oracles and baseline inventory remain protocol
work; no live runs are claimed or authorized.

This contract authorizes architecture/planning, not package publication or a beta claim.

## 8. Migration and story map

These are implementation obligations, not instructions to change active contracts during
this planning task. Each task updates its owning contract before code and includes its
direct regression; final scenarios integrate already verified changes.

| Surface and current owner | Replacement and owning tasks | Nearest existing checks to extend |
| --- | --- | --- |
| Protected request/questions/answers; `contracts/documents/ownership-matrix.md`; core interview; cross-document context | Source/criterion/decision state and readable projections; preserve originals; resolve actual anchors and answer application. `W57-E1-S2-T1/T2/T3`. | `tests/validators/test_cross_document.py`, `tests/validators/test_semantic_review_spec.py`, `tests/core/test_interview.py`. |
| `contracts/stages/tasklist.md`, `contracts/documents/tasklist.md`, `prompt-packs/stages/tasklist/system.md`, `src/aidd/core/stage_preparation.py` | Replace blanket “approved tasklist” assumptions with eligible validated decomposition of an authorized outcome; rich task cards and registered check refs. `W57-E1-S2-T1`, `W58-E1-S1-T2`, `W58-E2-S2-T3`. | `tests/core/test_stage_preparation.py`, `tests/core/test_task_plan.py`, `tests/test_contract_registry.py`. |
| Application implementation/finalizer, core task ledger/repository evidence and freshness; implementation/review/QA contracts | Check registry, injected verification, sealed receipts, independent assessment and final-tree gates. Retain authored command/outcome as attributed claims. `W57-E2-S1-T1/T2/T3`, `W57-E2-S2-T1/T2/T3`. | `tests/core/test_task_attempt_lifecycle.py`, `tests/core/test_task_repository_evidence.py`, `tests/validators/test_implementation_evidence.py`; add executor/assessment scenarios. |
| Core graph/registry/preparation/workflow service; config/run store; CLI run/stage entrypoints | Sole policy, finite routes, declared predecessor substitutions, pinned identity/budgets and direct-stage parity. `W58-E1-S1-T1/T2/T3`. | `tests/core/test_stage_graph.py`, `tests/core/test_workflow_service.py`, `tests/cli/test_run_workflow.py`, `tests/core/test_run_manifest_continuation.py`. |
| Task plan, run inputs, remediation/attempt lineage and reconciliation | Immutable revision maps, exact input resolver, addressed invalidation/carry-forward, bounded controller and crash/cancel transactions. `W58-E1-S2-T1/T2/T3`, `W58-E2-S1-T1/T2/T3`. | `tests/core/test_remediation.py`, `tests/core/test_task_attempt_evidence.py`, `tests/application/test_stage_reconciliation.py`. |
| All stage prompt packs and their contracts | Source-based task briefs; discovery/planning/implementation/review/QA prompts aligned one variable group at a time, existing runtime/model defaults pinned. `W58-E2-S2-T1` through `T5`. | Contract/preparation/semantic fixtures and representative trace/eval comparison per group. |
| Core frontend/Inbox/History read models; application projection; CLI/static UI | Outcome/criterion/change/receipt/assessment view, dynamic operations, scoped decisions and exact lineage, shared next action and limits. `W59-E1-S1-T1` through `T4`, `W59-E1-S2-T1/T2`. | `tests/cli/test_ui.py`, `tests/frontend/operator-decision-synchronization.test.mjs`, browser implementation/review/QA/recovery journeys. |
| Harness manifests/graders, packaged resources, guidance and compatibility policy | Target-route/recovery/unsupported-input scenarios; separate pinned baseline comparison, human observation, single replacement and no obsolete executable readers. `W57-E1-S1-T2`, `W58-E2-S3-T1`, `W59-E2-S1/S2`. | Packaging/planning/traceability checks, `make check`, `make test-browser`, declared native and install lanes on final candidate. |

| Story | Accepted target clarification |
| --- | --- |
| US-03 | Valid Markdown alone cannot advance through a required stale/missing/failing receipt or behavioral acceptance gate. |
| US-05 | Questions concern concrete missing authority; decisions have scope and observable application, distinct from permissions and model reviews. |
| US-07 | Independently pinned comparisons and real operator observations remain separate from deterministic/scripted evidence. |
| US-10 | Accountability includes source/criterion/check/oracle revisions, exact consumed inputs, iterations and final evidence identity. |
| US-11 | CLI/UI support selected finite routes and child history with shared action/reason/limits; unselected stages do not appear successful. |
| US-13 | Eligible tasklists decompose existing authority; fixes stay within the plan, replans create children, compatible work is reused with original attribution. |

US-01/02/04/06/08/09/12 retain portability, readable artifacts, repair, raw logs, extension,
installation and declared project-set guarantees. Existing evidence describes its captured
version; target contracts or synthetic design fixtures do not turn that evidence into proof
that the replacement is implemented.

## 9. Required adversarial acceptance

The owning implementation tasks must retain inspectable evidence for: internally consistent
documents/code/tests with wrong independent behavior; an omitted original constraint;
fabricated pass claims or all-skipped required checks; missing/unrelated/stale references;
an answered QID with unapplied behavior; permission/model sign-off used as product authority;
changed code/check/oracle/ignored input; subjective criteria without acceptance; failed parent
inputs; half-published or duplicate children; double-debited budgets; uncertain post-crash
processes; cancellation; stale project/run UI actions; and unsupported format before mutation.

Positive cases must show ordinary source-backed work without blanket specification approval,
a focused route without fake preparation outputs, actual registered checks, independent
assessment, addressed correction with retained work, refreshed final-tree proof, and a
complete result supported by all required gates. Documentation consistency checks validate
this planning output; they do not satisfy these future runtime acceptance cases.
