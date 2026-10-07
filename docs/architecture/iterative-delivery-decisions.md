# Iterative Delivery Architecture Decisions

This document records decisions for `W57-E1-S1-T1`: how AIDD will preserve the operator's
intended outcome, verify delivery, and support bounded iteration. It uses the accepted
[product positioning](../product/product-positioning.md),
[Operator UX direction](./iterative-operator-ux.md), and
[migration plan](../analysis/iterative-delivery-migration-plan-2026-10-01.md).

All nine policy decisions below are accepted. The
[unified target contract](iterative-delivery-contract.md) supplies their records, ownership,
route/lifecycle predicates and migration map. References to open contract design within
individual entries retain the state at decision time; the completion record below identifies
the resulting contract. These are migration targets. Current alpha contracts and workflow
remain in effect until the corresponding implementation tasks change them.

## ADR 001 Requirement authority

Status: **Accepted on 2026-10-01**. The operator explicitly selected option A in the
architecture discussion. This accepts the authority policy below; its persistence schema
and source-equivalence enforcement are still to be designed.

### Problem

A generated plan can be internally consistent while adding a product requirement that the
operator never requested. Requiring approval of the entire generated document also creates
a reading obligation without showing which decisions actually need attention.

### Decision

Explicit requirements in the original operator request and explicit subsequent answers
already have product authority. AIDD can proceed with an unambiguous extraction of those
requirements without asking the operator to approve the whole generated criterion list or
plan again.

A generated addition, ambiguous interpretation, conflicting requirement, or material change
to the authorized outcome requires a specific operator decision before affected work can
proceed. The question must explain the proposed behavior and its consequence, and both the
question and answer must be retained as documents. An answer grants authority within its
stated scope; it is not blanket approval for unrelated proposals.

Technical decomposition can proceed within the authorized outcome, constraints, and project
scope. A decomposition that changes product meaning follows the decision rule above.
Renaming a product choice as an implementation detail does not grant it authority.

### Source and decision boundaries

- Preserve the original request and consumed answer revisions. Generated documents reference
  those sources rather than replacing the operator's wording.
- Source links and digests establish provenance. They do not prove that a generated
  paraphrase preserves meaning. Ambiguous equivalence needs clarification or an explicit
  stop; a model's own sign-off cannot settle it.
- Opening a document, starting or resuming a run, approving a runtime permission, and a
  model review have their own consequences. None implicitly accepts a new product requirement.
- AIDD owns authority eligibility and the durable decision record. Runtimes propose content
  through Markdown contracts; CLI and UI expose the same scoped decision through shared
  application services.

The exact grounding checks, record format, and invalidation rules remain open design work
under this task. This decision does not claim that source links alone can enforce meaning.

### Example

The operator requests password reset by email with a token valid for 15 minutes. Both
requirements can enter the plan directly. Revoking all other sessions after a reset is a
new product policy and needs a separate question explaining that effect.

If the operator later changes the lifetime to 10 minutes, retain the earlier source and
record the new answer with its scope. The updated requirement does not make earlier
verification evidence current; evidence freshness is a separate architecture decision.

### Alternatives considered

| Option | Authority policy | Decision |
| --- | --- | --- |
| A | Explicit source requirements are authoritative; additions, ambiguity, and conflicts need scoped decisions. | Accepted. |
| B | Approve the entire short criterion list before execution; approve subsequent changes to meaning. | Not selected. Adds mandatory approval even for explicit requirements. |
| C | Delegate classes of product decisions through project policy. | Not selected. Requires a separate delegation and policy design. |

### Consequences and migration work

The main UX interaction is a concrete unresolved decision with its effect. The operator can
inspect supporting documents without having to approve every generated document.

For the target interpretation of `US-13`, an "approved tasklist" must mean an eligible,
validated decomposition of an authorized outcome with required product decisions resolved.
It must not introduce mandatory approval of the entire generated plan. The story wording,
ownership matrix, and stage-contract migration map will be reconciled when this architecture
task has its remaining decisions; current runtime acceptance behavior is unchanged here.

## ADR 002 Verification execution

Status: **Accepted on 2026-10-01**. The operator explicitly selected option A for the
executor: a dedicated AIDD verification service runs registered checks and retains their
execution evidence. This accepts the execution boundary. The acceptance policy is recorded
in ADR 003 and registration policy in ADR 004; the exact receipt schema remains open.

### Problem

A runtime-authored report saying that tests passed does not establish that the command ran,
what it returned, or which code it checked. Requiring native runtime tool events for all
verification also ties the product's evidence quality to each provider's capabilities.

### Decision

An application verification service owned by AIDD executes registered checks through an
injected, provider-independent execution port. The initial executor runs local processes.
The service retains the command, working directory, code/input identity, stdout/stderr,
timing, and actual exit, timeout, cancellation, or unavailable result.

Core policy determines which required checks are eligible and whether their evidence permits
progression. Application composition connects that policy to execution and persistence.
Provider-specific runtime launch and observation stay inside runtime adapters; neither the
core nor the verification service needs a particular agent's tool-event format to establish
that a registered local check ran.

The model may propose a check or cite an existing receipt. Writing a command or a passing
result into a tasklist or report does not register the command or create an execution
receipt. Check-registration authority follows ADR 004; its detailed contract remains to be
specified.

### Evidence and execution boundaries

- AIDD owns the execution lifecycle and canonical receipt. Runtime-authored Markdown reports
  remain attributed claims, with readable references to independently retained receipts.
- Evidence identifies the actual checked code, including relevant uncommitted inputs;
  a Git commit ID alone cannot identify a dirty working tree. The full identity and freshness
  policy will be specified with revision handling.
- Preserve failed, interrupted, timed-out, cancelled, skipped, and unavailable outcomes
  explicitly. Missing or unsuccessful required verification cannot silently become a pass.
- Process success records the observed execution result. Behavioral acceptance needs a
  separate assessment against expected behavior; a test written by the implementation
  agent is not automatically an independent answer key.
- CLI and UI consume the same retained facts through application services. Harness execution
  can share narrow process infrastructure, but an eval transcript cannot substitute for a
  product receipt.

This decision does not mandate a new serialized state format or define receipt reuse,
process recovery, or completion policy in detail. Those contracts remain open.

### Alternatives considered

| Option | Executor and evidence source | Decision |
| --- | --- | --- |
| A | AIDD runs registered checks and retains local process results and code identity. | Accepted. Fits local delivery without requiring provider tool-event support. |
| B | The agent executes checks; adapters supply confirmed execution events. | Not selected as the primary executor. Requires sufficient, compatible evidence from each runtime. |
| C | External CI executes mandatory checks; AIDD consumes results for the exact code version. | Not selected as the initial executor. Adds CI setup and feedback latency. |

The execution port can support an external executor later, under an accepted task with the
same evidence requirements. This decision does not require that extension now.

### Consequences and migration work

The Operator view can distinguish "the agent reports success" from "AIDD observed this check
on this code." A separate assessment then states whether that evidence confirms a criterion.

The existing `W57-E2-S1-T1` through `W57-E2-S1-T3` own registration, execution, and identity;
`W57-E2-S2-T1` and `W57-E2-S2-T2` own progression gates and behavioral assessment. This ADR
sets their target boundary without implementing them or completing `W57-E1-S1-T1`.

## ADR 003 Criterion acceptance

Status: **Accepted on 2026-10-01**. The operator explicitly selected option A: combine
automatic assessment against independent expected behavior with scoped human clarification
and manual assessment where needed.

### Problem

Code and tests produced from the same mistaken interpretation can agree while violating the
original request. Executing those tests independently establishes their actual result, but
does not by itself establish that the expected behavior was correct.

### Decision

Assess each required criterion against expected behavior whose authority comes from a source
independent of the implementation's own claims. Existing applicable contracts, independently
established examples, regression cases, or explicit operator decisions can supply that
expectation. Record its source, owner, version/digest, and sealing before implementation,
as required by the migration plan. Freezing a model-generated answer does not make it
independent merely because it was generated earlier.

When an independent expected result and suitable observed verification are available,
AIDD can confirm the criterion automatically under the declared assessment policy.
An ambiguous requirement needs a scoped clarification before affected implementation
proceeds, following ADR 001. A criterion that requires human judgment receives an explicit
manual assessment of the current result and its supporting evidence. Explicit source
requirements retain their authority; this policy does not require blanket approval of
criteria or a generated specification before every run.

An implementation agent's tests and a model review can identify defects and contribute
evidence. They do not automatically become an independent answer key or a confirmed
criterion assessment. Assessment must retain the expected-behavior source and the evidence
that supports its conclusion.

### Completion and evidence boundaries

- Keep product authority, observed check execution, and behavioral assessment distinct.
  A successful process does not automatically confirm every criterion it references.
- Record assessments as confirmed, rejected, inconclusive, or not assessed, with the
  criterion revision, expected-behavior source, assessor, and current evidence references.
- Retain a manual assessment with its actor, criterion scope, checked result identity,
  and supporting observation. It is distinct from granting authority to a new requirement.
- A mandatory criterion that is rejected, inconclusive, or not assessed prevents delivery
  completion. Report the unresolved criterion and a stopped/partial outcome explicitly;
  do not silently make it optional.
- Existing required check, review, and QA gates still apply. Criterion confirmation does
  not replace those gates, release evidence, or genuine operator usability observations.

The detailed assessment contract, oracle registration, revision identity, and invalidation
mechanisms remain work under `W57-E1-S1-T1` and the owning implementation tasks.

### Example

For a request that a reset token remain valid for 15 minutes, observable checks can exercise
acceptance at 14 minutes and rejection at 16 minutes against the original requirement.
Inspecting a generated constant or passing a test that encodes a different lifetime is
insufficient. These two examples illustrate the criterion; they do not claim complete
coverage of the password-reset behavior or resolve unspecified boundary conditions.

### Alternatives considered

| Option | Acceptance policy | Decision |
| --- | --- | --- |
| A | Automatically assess criteria with independent expected behavior and current evidence; clarify ambiguity and use manual assessment where necessary. | Accepted. Focuses human work on unresolved decisions and assessment gaps. |
| B | Require the operator to approve examples for every criterion before implementation. | Not selected. Adds preparation and reading for every run. |
| C | Require final human acceptance of every delivery in addition to automated checks. | Not selected. Makes the operator a mandatory participant in every completion. |

The existing `W57-E2-S2-T2` owns behavioral assessment and completion enforcement, with
independent baseline expectations in `W57-E1-S1-T2`. This decision does not implement them.

## ADR 004 Project check registry

Status: **Accepted on 2026-10-01**. The operator selected option A: a project registry of
checks with selection governed by AIDD policy, including declared parameter bounds.

### Problem

Independent execution needs an explicit definition of what AIDD is authorized to run.
A model-authored tasklist can suggest useful checks, but cannot grant itself command
registration authority, change required verification, or establish an independent oracle.

### Decision

Register project checks from authorized configuration, scenario definitions, or a scoped
operator action. Retain the authority source, registration event, definition version/digest,
command, working directory/project scope, prerequisites, timeout, expected execution result,
and declared inputs. Parameters may vary only within bounds declared in that definition.

AIDD selects applicable checks by declared rules using the task, criterion, project scope,
and available change evidence. Required checks come from that policy; an agent's suggestion
cannot remove them. Selection retains the policy/definition identities and rationale so
the CLI and UI can explain which checks are required and why.

Existing checks can repeat within their registered bounds without a new approval for each
execution. A new command, changed execution definition, or expanded parameter/project scope
requires separate registration under an authorized source. A runtime proposal remains a
proposal until that registration occurs. Registration is a scoped action on the concrete
definition, rather than approval of the entire generated plan.

### Authority and evidence boundaries

- Definition and parameter validation belong to AIDD policy. A model's confidence or its
  description of a command as harmless does not establish eligibility.
- Missing prerequisites, incompatible definitions, and parameters outside registered bounds
  produce an explicit blocker. Uncertain applicability must be resolved by the policy or
  surfaced as a gap; it cannot silently remove required verification.
- Registering a command authorizes its execution under the applicable execution policy.
  Independent expected behavior still needs its own source and assessment under ADR 003.
- Runtime permissions retain their attempt scope. They do not register a product check or
  confer product authority. Registry validation does not itself provide process isolation;
  preserve the existing distinction between full-access and brokered execution.
- Changed check definitions and inputs affect evidence identity. Previous receipts remain
  attributable to their original definitions; detailed freshness/reuse rules remain open.

### Alternatives considered

| Option | Check-set policy | Decision |
| --- | --- | --- |
| A | Register project checks and parameter bounds; select applicable checks by declared rules. | Accepted. Ordinary iterations reuse authority without repeated approval. |
| B | Require approval of the check set for each Work Item; repeat the unchanged approved set. | Not selected. Adds an operator action for each new Work Item. |
| C | Always execute the entire fixed project check set. | Not selected. Simpler selection, but unnecessary full-suite cost for bounded changes. |

`W57-E2-S1-T1` owns registry contracts, selection/execution policy, preflight, and fixtures.
`W57-E2-S1-T3` owns binding proof to the definition and declared inputs. The serialized
registry shape, exact selection predicates, oracle registration contract, and revision
handling still need contract design; this ADR does not implement them.

## ADR 005 Preparation depth and routing

Status: **Accepted on 2026-10-01**. The operator selected option A: AIDD automatically
chooses preparation depth from explicit evidence, with a visible route and rationale.

### Problem

Mandatory full preparation delays bounded work and produces documents that do not always
help the operator make a decision. Letting the model shorten preparation based on its own
confidence can instead omit needed investigation or design.

### Decision

Use a finite set of preparation routes selected by core policy. Select from declared
change scope, source/decision status, known ownership, available verification and expected
behavior, unresolved repository facts, and material interface/contract effects.

| Route | Selection basis | Preparation outcome |
| --- | --- | --- |
| Focused | Bounded known task, sufficient source authority, known ownership/checks, and no unresolved material decision. | Compact criteria and executable task cards without mandatory research or a full specification. |
| Investigate | Missing repository or verification facts that investigation can resolve. | Targeted research resolving the concrete uncertainty before executable task preparation. |
| Design | Material interface/contract effects that need explicit analysis and design decisions. | Necessary design and review of those decisions before executable task preparation. |

Uncertain classification escalates investigation or surfaces a durable question. Product
ambiguity follows ADR 001; selecting a deeper route does not grant authority to an unresolved
product proposal. A model can propose observations or a route, but its confidence score,
provider, or model name cannot determine reduced preparation eligibility.

Show the selected route and its reason in the CLI and UI without requiring a separate
operator planning mode for every task. The operator can request deeper preparation.
Requests for a shorter route must still satisfy the policy's mandatory prerequisites.

### Execution and contract boundaries

- Persist the route, policy/profile identity, selected operations, rationale, and predecessor
  input map before executing those operations. Later changes must respect run identity and
  the iteration identity in ADR 006, reuse policy in ADR 007, and controller policy in ADR 008.
- Reuse existing stage identifiers through explicit profile contracts. Each omitted
  preparation prerequisite needs a declared replacement; creating an empty specification
  or a fake successful skipped stage cannot satisfy the old contract.
- Progress reflects selected operations and criterion state. An unselected operation is
  distinct from a successful execution; a universal "8 of 8" projection is insufficient.
- Implementation, required verification, review, and QA retain their gates in every route.
  Short preparation does not imply weaker acceptance or unsupported source authority.
- The current alpha remains the supported behavior until a complete replacement candidate
  is accepted. ADR 009 subsequently fixed a direct breaking cutover: internal task slices
  do not create a supported mixed classic/iterative mode or a separate default transition.

### Alternatives considered

| Option | Preparation selection | Decision |
| --- | --- | --- |
| A | AIDD selects focused, investigate, or design from explicit evidence and exposes the rationale. | Accepted. Ordinary tasks start with sufficient preparation without another mandatory operator choice. |
| B | The operator selects depth for every new Work Item; AIDD checks prerequisites. | Not selected. Adds a route choice at each start. |
| C | Every Work Item starts with short research; design is added when findings require it. | Not selected. Gives a uniform initial investigation but adds research even for known bounded fixes. |

`W58-E1-S1-T1` through `W58-E1-S1-T3` own persisted profile identity, executable route
contracts, and evidence-based selection. The exact predicates, input substitutions, and
stage/profile migration map remain contract work under `W57-E1-S1-T1`; this ADR does not
implement them.

## ADR 006 Iteration identity and history

Status: **Accepted on 2026-10-01**. The operator selected option A: changed plans execute
in child runs of the same Work Item, preserving the predecessor and its evidence.

### Problem

Overwriting a plan inside an executing run makes historical inputs and results ambiguous.
A single long-lived run with repeated stage cycles would instead require changing the
existing stage lifecycle. A new independent Work Item for each correction would fragment
one delivery objective across unrelated work.

### Decision

Keep one Work Item for the same delivery objective. A changed plan/tasklist revision or
addressed replan creates a child run with a new run identity and an explicit parent link.
Preserve the previous run, its consumed inputs, plan, attempts, logs, and verification
evidence as immutable history. A child does not change a predecessor's recorded outcome.

Ordinary task fixes, check reruns, document repairs, retries, and resumes stay in the current
run when compatible with its unchanged pinned inputs and plan. Their attempts and results
remain attributable. A revised plan must not silently replace a running ledger.
A new independent objective uses the existing explicit new-work/follow-up semantics;
`next_flow` is not the same-Work-Item child-iteration mechanism.

Retain each child's parent, iteration number, reason/decision and evidence references,
consumed source identities, plan revision, tasklist identity, selected operations, and
profile/policy identity. Child creation links to the Work Item's objective-budget
accounting; concrete limits and controller behavior remain open design work.

### Activation and history boundaries

- Stop predecessor execution before activating its child. Preserve one mutating flow owner
  per checkout and a validated source snapshot across the ownership handoff. This decision
  does not introduce concurrent mutating iterations.
- Resolve consumed documents and evidence for an exact run. Shared active output paths are
  projections, not the authority for reconstructing an earlier run's inputs.
- Keep child output in run-local staging until a coherent validated bundle is committed.
  A blocked or incomplete child must not overwrite the committed parent projection.
- Publish lineage, plan revision, ledger, and active projection coherently, or retain an
  explicit recoverable incomplete state. Recovery must not combine different revisions.
- Failed or blocked predecessors can supply only specifically validated inputs/evidence;
  being a parent does not make all their output eligible for reuse.

In the CLI and UI, the Work Item remains one work context with its active iteration and
history. History identifies the plan, changes, checks, and assessments belonging to each
run; it does not present an old outcome as the child's current result.

### Alternatives considered

| Option | Iteration storage | Decision |
| --- | --- | --- |
| A | Child runs of one Work Item, with immutable predecessor history. | Accepted. Builds on the existing run model and keeps one delivery objective. |
| B | One long-lived run containing plan revisions and repeated stage cycles, with history retained. | Not selected. Requires deeper changes to stage lifecycle and completion rules. |

`W58-E1-S2-T1` and `W58-E1-S2-T2` own plan revisions and exact-run resolution/publication.
`W58-E2-S1-T1` owns child creation and lineage. Carry-forward and invalidation follow ADR 007.
Controller policy follows ADR 008. Exact limits, accounting, idempotency, and recovery contracts remain open;
this ADR accepts identity/history boundaries without implementing those services.

## ADR 007 Carry-forward and invalidation

Status: **Accepted on 2026-10-01**. The operator selected option A: rerun affected tasks
and their dependents, carry forward compatible retained work, and refresh stale verification.

### Problem

Repeating all implementation work after every replan wastes completed work. Carrying it
forward solely because task IDs match can instead retain behavior that no longer satisfies
the request, or report historical verification as evidence for changed code.

### Decision

Use explicit mappings between plan revisions for retained, changed, removed, and new tasks.
Compare task definitions, source-backed criterion meaning, constraints, authorized scope,
dependencies, and check definitions. Matching IDs or valid source links alone do not prove
equivalence. Unresolved product meaning follows the scoped question/stop rule in ADR 001;
a model cannot certify that its own reinterpretation preserves authority.

Map each finding or changed criterion/task to the affected task set and its dependency
closure. Re-execute changed tasks and affected dependents. Carry forward other work only
when its source evidence is valid, the relevant code changes remain present, and its
criteria, scope, and dependencies are compatible. Missing retained code, ambiguous revision
mapping, or invalid source evidence prevents automatic carry-forward.

Retain source-run, task, attempt, definition/digest, and evidence references for carried
work. Its ledger/read-model disposition is reused, with its original attribution; it is
not a newly executed successful attempt. A changed plan does not itself require blanket
product approval when the authorized outcome and constraints remain unchanged.

### Verification and completion boundaries

- Evaluate verification freshness separately from code/work compatibility. A compatible
  implementation can require new verification without another model implementation attempt.
- Receipt identity includes the checked code and relevant source, criterion, check,
  configuration, project/cwd, and declared-input identities. Keep old receipts attributable
  to their original identities; do not relabel them for the child.
- An earlier whole-tree receipt does not prove a changed final tree merely because the
  carried task appears unrelated. Stale or missing required verification runs again before
  its completion gate can be satisfied.
- Aggregate finalization runs required final checks on the actual final implementation
  tree, including after finalization changes. Carried work cannot bypass this gate.
- Assessments under ADR 003 must still apply to the current criterion and evidence. Reuse
  cannot turn a stale, rejected, or unassessed mandatory criterion into a confirmed one.

CLI and UI show reused work, the original attempt, the reason for compatibility, and any
pending re-verification. History retains earlier failures and successful receipts while
the current iteration exposes its actual evidence gaps.

### Alternatives considered

| Option | Re-execution policy | Decision |
| --- | --- | --- |
| A | Re-execute affected tasks/dependents; carry compatible retained work and refresh stale checks. | Accepted. Avoids unnecessary model work while retaining current proof requirements. |
| B | Repeat all tasks and checks in every iteration. | Not selected. Simpler carry-forward policy but more execution time and model calls. |
| C | Require human confirmation of every eligible carry-forward set. | Not selected. Adds reading and an action at each replan without replacing compatibility or freshness checks. |

`W58-E1-S2-T3` owns invalidation and carry-forward, with source/revision mapping in
`W57-E1-S2-T1`, `W57-E1-S2-T2`, and `W58-E1-S2-T1`. `W57-E2-S1-T3` owns proof identity/freshness, and
`W57-E2-S2-T1` owns completion gates. Exact record shapes, fingerprints, reference resolution,
and closure/eligibility predicates remain contract work; this ADR does not implement them.

## ADR 008 Bounded automatic control

Status: **Accepted on 2026-10-01**. The operator selected option A: automatic fixes,
verification, and replanning within authorized bounds and shared Work Item limits.

### Problem

Requiring an operator action for every ordinary correction interrupts delegated work.
Unbounded automatic retries can consume resources without progress or keep redefining the
plan until a failure appears to disappear. A new child run must not reset the objective's
limits or provide new product authority.

### Decision

Core policy chooses the next action from current retained evidence and eligible operations:
continue a ready task, repair/fix within the pinned plan, refresh verification, create an
eligible child replan, ask a scoped question, complete after all required gates, or stop.
The runtime may propose a diagnosis or plan, but does not grant itself progression or
completion merely by reporting success.

Ordinary corrections and replans within the authorized outcome, scope, check authority,
and compatible source meaning can proceed automatically. Unresolved product ambiguity,
material requirement/scope change, missing registration authority, or required manual
assessment follows the applicable operator question/decision rule. Automation retains
existing runtime-permission and external-action boundaries; this policy does not supply
permission for publication, release, or other separately authorized actions.

Apply finite attempt, iteration, and elapsed-time limits to the whole Work Item objective.
Children inherit remaining limits and consumed counters. Where cost telemetry is available,
retain attributed cost and apply any declared cost policy. Unavailable cost is explicit,
not zero; an unenforceable mandatory cost cap is a blocker rather than an assumed pass.
Exact defaults and per-action accounting will be declared in configuration and pinned for
the baseline protocol before evaluation, rather than tuned to rescue individual traces.

### Stop and recovery boundaries

- Exhausted limits, repeated equivalent failures without observed progress, incompatible
  evidence, or unresolved scope stop progression or surface a concrete question. A renamed
  finding, new plan digest, or model claim of progress cannot reset the limits.
- Distinguish document repair, runtime retry, answer continuation, implementation fix,
  check rerun, and plan iteration. Record the action, reason, evidence, attempts, and actual
  resource accounting; do not double-count the same execution on replay.
- Child creation binds a stable decision/idempotency identity to the parent, source evidence,
  and profile/policy revision. Retrying publication returns the same child or an explicit
  incomplete state, with one budget reservation/debit.
- Cancellation retains partial receipts, raw logs, process ownership, and the first decisive
  failure. Reconcile an existing execution and its outcome before starting a replacement;
  an uncertain post-crash state cannot silently trigger duplicate commands or children.
- Preserve the one-mutating-flow boundary and coherent publication from ADR 006. Required
  verification and assessment from ADR 002–ADR 004 and ADR 007 still gate completion.

CLI and UI expose the current action, its reason, consumed/remaining limits, evidence gaps,
and an explicit stop/cancel action through the shared service. Missing provider telemetry is
shown as unavailable. The UI does not invent a second controller or infer progress from prose.

### Alternatives considered

| Option | Correction autonomy | Decision |
| --- | --- | --- |
| A | Automatically fix, verify, and replan within shared limits and authorized bounds. | Accepted. Keeps routine delegated correction moving while retaining explicit stop and decision rules. |
| B | Automate fixes/checks, but require permission for each child replan. | Not selected. Adds a pause even when the authorized outcome is unchanged. |
| C | Stop after a check or review failure and let the operator choose continuation. | Not selected. Requires manual handling of ordinary correctable failures. |

`W58-E2-S1-T1` through `W58-E2-S1-T3` own control, recovery/accounting, and feedback routing.
`W58-E1-S1-T1` owns pinned objective limits. Exact counter schemas, action predicates,
progress fingerprints, process reconciliation, and numeric defaults remain contract/evaluation
work; this ADR does not implement the loop or enable it in the current classic workflow.

## ADR 009 Direct breaking replacement

Status: **Accepted on 2026-10-01**. The operator selected a direct migration of the whole
delivery process without backward compatibility, replacing the proposed staged coexistence.

### Decision

The replacement release contains one iterative delivery policy and its current formats.
Focused, investigate, design, and correction are routes of that policy, not separate classic
and iterative engines. Do not ship a period of dual-profile execution, an opt-in transition
mode, a classic selector, or an in-engine rollback to the retired process.

Update the core, application services, contracts, validators, prompts, CLI/UI, harness,
packaging, and operator guidance together before the replacement candidate is accepted.
Internal implementation tasks remain bounded and independently verifiable; they converge
on one complete replacement release rather than independently published mixed-format states.

Retire obsolete configuration/artifact/manifest/ledger inputs, aliases, and readers. Reject
an unsupported format before mutating the workspace; do not silently convert it, fill missing
provenance, or fall back to classic execution. Recreate work in the current format through an
explicit operator action. Preserve historical Markdown, logs, receipts, and raw bundles for
direct/archive inspection; preserving bytes does not promise old-run resumability or current
semantic interpretation of old machine state.

### Acceptance boundaries

- Retain correctness, native-runtime, real operator-understanding, browser, and installation
  gates for the exact replacement candidate. A breaking transition does not weaken these
  gates or establish beta readiness by itself.
- Compare against the pinned pre-migration release in a separate checkout/environment and
  retained baseline bundle. The new engine does not need classic execution or old-format
  readers to perform that evaluation. Pin intentional implementation/prompt differences
  and keep model/runtime/scenario/environment controls explicit.
- A failed candidate remains unaccepted; it does not create an ongoing public opt-in lane.
  Publishing or releasing remains a separately authorized action.
- If rollback is needed, return explicitly to the earlier package/revision and its compatible
  retained workspace. Do not rewrite a new run to make it resumable by the old engine.

### Alternatives considered

| Option | Release transition | Decision |
| --- | --- | --- |
| A | Temporary classic/iterative coexistence, then default switch and classic retirement. | Not selected. The operator explicitly removed the compatibility/coexistence requirement. |
| B | Direct replacement after candidate acceptance. | Accepted, with no backward compatibility or automatic workspace conversion. |
| C | Permanent support for both processes. | Not selected. Adds permanent dual-contract and regression maintenance. |

`W58-E1` implements the sole policy and immutable inputs. `W59-E2-S1` owns comparison and
candidate acceptance; `W59-E2-S2` owns installation, direct cutover, unsupported-input handling,
and final evidence. Existing task IDs are retained with revised outputs and dependencies.
The dated migration proposal is superseded on coexistence/default-switch/retirement details.
This ADR changes the accepted target, not the currently implemented alpha behavior.

## Baseline protocol decisions

These parameter decisions belong to `W57-E1-S1-T2`. They refine the accepted architecture
without reopening ADR 001–ADR 009 or changing current runtime behavior. A recorded choice
does not complete the baseline protocol or demonstrate that its limits are measured.

### P01 Objective time accounting

Status: **Accepted on 2026-10-05**. The operator selected option A.

The shared Work Item time limit counts active automation time across all runs/children.
Exclude operator-answer waiting and an explicit operator pause only when every execution
is confirmed stopped/terminal. A check or unaffected task still running consumes time even
if another task needs an answer. Count overlapping active intervals once, retain interval
boundaries and excluded waits, and preserve accumulated usage across pause/resume/children.
Missing observations or uncertain process ownership require reconciliation; they cannot
be treated as a verified pause. Separate execution timeouts remain enforced.

There is no additional objective-expiration deadline merely because the operator replies
later. Existing source/proof freshness and explicit resume rules still apply. P02 fixes
the pilot's numeric limits and P03 fixes the correction-loop no-progress threshold.

| Option | Time accounting | Decision |
| --- | --- | --- |
| A | Active automation time; exclude verified operator waiting/pauses. | Accepted. A delayed human answer does not consume the automation budget. |
| B | All elapsed time from first launch, including waiting/pauses. | Not selected. |
| C | Active time plus a separate expiration/reactivation deadline. | Not selected. |

### P02 Pilot automation limits

Status: **Accepted on 2026-10-05**. The operator selected option A as the initial pilot
settings. These values are not yet supported by runtime measurements or enabled in the
current implementation.

| Shared Work Item limit | Pilot value |
| --- | ---: |
| `max_execution_starts` | 40 |
| `max_child_iterations` | 3 |
| `max_elapsed_seconds` | 7200 seconds of active automation time under P01 |

Every actual runtime invocation or registered check command consumes one execution start,
including retries, document repairs, fixes and repeated verification. A committed child
creation consumes one child iteration; the root run does not. Counters are shared across
the objective and retained across pause/resume and child runs, with the existing exactly-once
reservation/debit and process-reconciliation rules.

The fortieth execution and third child are permitted. Refuse the next action that would
require a forty-first execution or fourth child; exhausted child capacity cannot create
another run, but does not cancel an already admitted child that can finish within its other
remaining bounds. Reaching the active-time cap stops active execution and retains partial
results. Completion still requires every quality gate; a numeric stop cannot convert partial
work into a passing result. Completing within the admitted work is allowed without another
execution when all required evidence is already present.

Pin these limits before pilot evaluation. An inadequate limit is an observed protocol/result
gap, not permission for the controller to raise it, omit required checks or reset counters.
Any later protocol revision is explicit and applies to a new declared comparison; preserve
the original capped result. P03 fixes the correction-loop no-progress threshold;
independent baseline expectations and the full protocol remain pending. P01/P02 do not
complete `W57-E1-S1-T2`.

| Option | Shared pilot limits | Decision |
| --- | --- | --- |
| A | 40 execution starts, 3 children, 2 hours active time. | Accepted as the initial evaluation setting. |
| B | 20 execution starts, 1 child, 45 minutes active time. | Not selected. |
| C | 80 execution starts, 5 children, 4 hours active time. | Not selected. |

### P03 Correction-loop no-progress threshold

Status: **Accepted on 2026-10-05**. The operator selected option A: stop automatic correction
after two consecutive completed correction-and-check cycles without confirmed improvement
on the same blocking problem. This is an initial evaluation setting, not measured runtime evidence.

The initial observation of the defect is the starting point, not a correction cycle.
A cycle contains an eligible correction and the resulting applicable verification/observation.
Compare retained facts for the affected criterion/task/check or validator finding. Progress
requires confirmed improvement addressing that blocker, such as a resolved finding or a
previously failing relevant check/case now passing under compatible independent expectations.
An unrelated task passing, a model's success claim, changed text/code/input digest, renamed
finding or new plan/child by itself cannot reset this failure chain.

Link the problem lineage across compatible revisions and child runs. Changed execution
input identities remain part of proof freshness, but do not alone create a new problem or
evidence of improvement. An ambiguous lineage/progress comparison asks/stops under existing
eligibility rules; the model cannot certify a reset. A confirmed improvement restarts the
consecutive no-progress count for that problem while the shared execution/iteration/time
counters remain consumed. Retain the earlier cycles and improvement evidence.

At the second completed cycle with no confirmed improvement, do not launch another automatic
correction for that blocker. Stop its correction chain and surface the blocker, attempts,
evidence and remaining limits for inspection or an explicit scoped operator action. Do not
mark incomplete required behavior complete, bypass dependent work or silently switch to a
new child to obtain more attempts. Process stalls, uncertain execution, required ambiguity,
permission denial and exhausted objective limits retain their separate immediate stop/ask
rules; this threshold is not permission to repeat an ineligible execution twice.

| Option | Consecutive completed correction cycles without confirmed progress | Decision |
| --- | ---: | --- |
| A | 2 | Accepted as the initial evaluation setting. |
| B | 1 | Not selected. |
| C | 3 | Not selected. |

### P04 Mandatory acceptance and overhead diagnostics

Status: **Accepted on 2026-10-05**. The operator selected option A: correctness, truthful
evidence and operator understanding are mandatory; speed, cost and reading volume are
measured diagnostics without a mandatory percentage improvement for the first replacement.

Evaluate behavior against the pinned independent expectations and original authorized
requirements. Retain the authority/freshness/assessment, recovery, deterministic/browser,
runtime-tier and installation gates from ADR 001–ADR 009. False completion, invented proof,
omitted mandatory requirements and misleading authority cannot be offset by faster execution
or shorter documents. A blocked negative scenario passes only when its predeclared expected
outcome is that explicit block; positive delivery scenarios must meet their completion gates.

Record active time, time to first independently verified change, operator reading/decision
time, prompt/document volume, latency, interventions and attributed cost where available.
Pin metric definitions, comparison checkpoints, matched fixtures and runtime/model/environment
controls before collecting comparison evidence. Missing cost/metric observations remain
unavailable rather than zero or an inferred improvement. These measurements diagnose costs
and remaining gaps; they do not establish population-wide improvements from a small pilot.

No mandatory 10% or 25% speed reduction is part of first-replacement acceptance. P01–P03
resource limits and stop rules remain binding; diagnostic performance does not make budgets
optional. Any configured mandatory cost cap retains its enforceability rule. An
explicit future protocol revision can propose quantitative performance gates with evidence
before a new comparison, preserving original results rather than redefining their pass status.

| Option | Additional comparative performance requirement | Decision |
| --- | --- | --- |
| A | No mandatory improvement percentage; retain all quality/understanding gates and measure overhead. | Accepted. |
| B | At least 25% lower median time to first independently verified change on matched bounded fixes. | Not selected. |
| C | At least 10% lower median time to first independently verified change on matched bounded fixes. | Not selected. |

P05 fixes the operator sample and core success rubric. Exact cases/oracles, baseline inventory
and the complete comparison protocol remain work in `W57-E1-S1-T2`; P04 does not claim observed UX or runtime
acceptance and does not authorize recruiting, live execution or publication.

### P05 First-replacement operator observation

Status: **Accepted on 2026-10-06**. The operator selected option A: five eligible participants,
at least four completing the key tasks without coaching, and no observed serious error
attributable to the interface. This is a pilot gate for that group, not a population-wide
usability guarantee or evidence that sessions have already happened.

Participants are developers/technical leads from the target audience who did not implement
or review the UI and are first-time users of the evaluated interface at study entry.
Predeclare the cohort, matched fixture tasks, old/new order, task time boxes and scoring
before observation. Counterbalance order across participants and retain the version,
fixture and session identity. Pin original expected behavior independently of generated
documents; use the existing [observation protocol](../e2e/operator-ui-observed-acceptance.md)
as the recording/privacy/facilitation baseline, adapting its task script to the replacement.

A successful participant completes every declared key task without hints or product
explanations: explain the goal and constraint; distinguish checked behavior from assumptions;
locate actual evidence and the next action; make the scoped decision where needed; and
recover from the declared failure/stale-proof case. Record task outcomes, elapsed time,
wrong actions, assistance and decisive confusion. Confidence ratings or document-open counts
cannot substitute for these outcomes. A hinted result is not unassisted success.

Any serious error caused by the interface blocks acceptance across the entire cohort,
including the participant outside the four-success threshold. Examples include treating
missing required proof as completion, mistaking runtime permission for product authority,
or applying a decision to the wrong project/run. Declare severity/attribution rules before
sessions; do not average away or retrospectively downgrade a decisive failure.

Retain every session/task row, including failures, assistance and abandonment. Do not select
the best five after observation. Missing participants, incomplete required sessions or a
threshold failure remain outstanding evidence/no-go. Refresh affected observations after
changes to observed behavior/UI, with explicit final-candidate impact/revision checks.
Browser, native-runtime and human lanes remain distinct. Existing parked observation/beta
tasks close only through exact candidate/protocol/scope reconciliation, not this parameter
choice. Recruiting or contacting participants is not authorized by recording the protocol.

| Option | Eligible participants / minimum unassisted successes | Decision |
| --- | --- | --- |
| A | 5 / 4 | Accepted, with no serious interface-caused error in any session. |
| B | 5 / 5 | Not selected. |
| C | 10 / 9 | Not selected. |

### P06 Native comparison repetitions

Status: **Accepted on 2026-10-06**. The operator selected option A: three independent
repetitions of each of the four mandatory task classes on both the baseline and candidate.

The classes are a bounded fix; clarification of an ambiguous requirement; an interface or
contract change; and a correction requiring replanning while retaining compatible completed
work. Pin the representative case, original source/answer script and independent expectations
for each class before execution. For one declared runtime/model/reasoning/environment
configuration, the comparison contains twelve scenario trials per version, twenty-four in
total. Additional declared configurations have their own matrix; this choice does not change
the existing runtime support tiers or authorize expanding the provider matrix.

A scenario trial is not a P02 execution start or child iteration. Each candidate trial has
its own Work Item, with the shared 40-start/3-child/2-hour active-time limits applying across
its internal execution and children. Do not relabel an exhausted or failed objective as an
unplanned independent trial to reset those limits. Record baseline settings and bounds
separately; an earlier engine is not assumed to implement the new controller or counters.

Start each repetition from the same pinned original target state in an isolated checkout/
workspace and the appropriate version's supported format. Do not carry solution code,
generated answers, agent context or proof from another repetition. Predeclared source answers
remain fixture inputs; compatible carry-forward within a trial remains part of the correction
case. Keep target commit, source/oracle, runtime/model/reasoning and environment controls
matched, and record intentional AIDD-version/prompt differences. The baseline runs in its
separate earlier-version environment, without a legacy reader in the replacement engine.

Predeclare trial IDs and retain every outcome, including failure, block, cancellation and
unavailable prerequisites. Do not select the best three after seeing results. Deterministic
adversarial cases, rendered browser journeys, installation and P05 operator observations
remain separate required lanes; twenty-four native trials cannot substitute for them.
Three repetitions are a bounded repeatability sample, not a population reliability estimate.
P07 fixes aggregation and external-failure handling. This sample-size choice does not
complete `W57-E1-S1-T2` or authorize live execution/publication.

| Option | Repetitions per class/version | Scenario trials per configuration, both versions | Decision |
| --- | ---: | ---: | --- |
| A | 3 | 24 | Accepted. |
| B | 1 | 8 | Not selected. |
| C | 5 | 40 | Not selected. |

### P07 Native acceptance and external-failure replacement

Status: **Accepted on 2026-10-06**. The operator selected option A: after resolving a
confirmed external failure, replace only the interrupted scenario trial under the same
declared conditions and retain other compatible observations.

For the candidate's native comparison matrix, each mandatory case requires the expected
outcome in all three counted repetitions. A positive delivery case must satisfy its
independent behavior and completion gates; an expected block counts only where the case
predeclares that outcome. Retain the baseline's actual results rather than requiring the
earlier version to implement replacement behavior or treating its failures as the candidate's
acceptance standard. Release consequences still follow the existing runtime support tiers:
a failed or unverified non-blocking lane remains a documented gap, never a passed matrix.
False completion, invented proof and hidden loss of required behavior retain their no-go rules.

An external-failure replacement requires retained evidence of the decisive external cause
that prevented observation, such as network or runtime unavailability, and confirmed restored
prerequisites. Use the existing execution/manual-quality taxonomy and raw evidence to make
that diagnosis. An unknown cause blocks acceptance. Wrong behavior, a poor model response,
exhausted execution/time/iteration limits or a product defect remain unsuccessful trials;
they cannot be reclassified as infrastructure merely to obtain three passing results.

Link the replacement attempt to its original predeclared trial slot, keep both identities,
outcomes, consumed resources, diagnosis and remediation, and start from the same pinned
original case state. The interrupted observation is not a pass. The replacement is an
explicitly recorded evaluation attempt, not a continuation that resets an existing Work
Item's counters or a hidden extra trial selected after seeing outputs. It does not authorize
automatic unbounded reruns. Reconfirm target/source/oracle, AIDD/runtime/model/reasoning and
environment identities; if the repair changes comparison controls, record the revision and
invalidate affected observations instead of assuming compatibility.

Unaffected results may remain only with explicit scope/identity/freshness reconciliation.
An AIDD defect requires a fix and new evidence on the changed candidate; repeating its
unchanged trial until success is not defect remediation. Preserve the unsuccessful earlier
candidate and rerun affected cases/checks under the accepted final-candidate rules. Missing
or unresolved required repetitions remain no-go, with no best-three selection or retrospective
threshold change. Browser, installation, human and adversarial gates remain separate.

| Option | Recheck after a confirmed external failure | Decision |
| --- | --- | --- |
| A | Replace only the interrupted trial after restoring prerequisites; retain compatible observations. | Accepted. |
| B | Repeat all six trials of the affected case, three per version. | Not selected. |
| C | Repeat all twenty-four trials of the runtime configuration. | Not selected. |

P01–P07 settle the discussed operational policies. Exact case/source/oracle definitions,
baseline package/revision and retained-bundle inventory, pinned comparison controls,
recording/scoring scripts and the complete protocol remain `W57-E1-S1-T2` work. This decision
records planning, not completed trials, authorization to run providers or publication.

## Contract completion

ADR 001–ADR 009 and the [unified target contract](iterative-delivery-contract.md) define the
accepted architecture. No further product-policy vote is required for the mechanics below.

| Topic | Contract result |
| --- | --- |
| Source and assessment | Contract sections 1–3 define exact sources, authority/registration/oracle/receipt/assessment ownership, record fields, freshness and honest validation limits. |
| Lifecycle | Sections 4–6 define finite routes, input substitutions, revision/carry-forward rules, action predicates, shared counters, progress and process/publication recovery. |
| Direct migration | Sections 7–9 define current-format replacement, old-input stops, source recreation, stage/prompt/code/check map, story effects and required adversarial acceptance. |

The ownership matrix and migration map live in that contract; user stories, traceability,
compatibility, UX direction and W57–W59 are reconciled with it. The roadmap records
`W57-E1-S1-T1` closure only after planning/document verification. P01 fixes time accounting,
P02 fixes initial pilot limits and P03 fixes the correction-loop no-progress threshold.
P04 separates mandatory quality/understanding gates from overhead diagnostics.
P05 fixes the five-participant/four-success operator gate and serious-error veto.
P06 fixes three native repetitions per task class/version, twenty-four trials per configuration.
P07 requires three expected candidate outcomes per case and permits a recorded replacement
only for the interrupted trial after a diagnosed external failure and prerequisite recovery.
Independent baseline expectations and the full evaluation/acceptance protocol remain work
in `W57-E1-S1-T2`. Serialized state, executors, validators, prompts and UI
remain implementation work; this completion record does not claim runtime acceptance.
