# Target Operator Experience

Status: normative target for Wave 42. Existing Operator UI routes and services remain the
compatibility baseline until their owning Wave 42 slices are implemented and browser-verified.

This document defines the task-centered Operator UI that replaces the previous visual reference
sets. It changes presentation and interaction hierarchy, not the canonical workflow, adapter
boundary, Markdown ownership, validation gates, or durable `.aidd/` state.

## 1. Product brief

- **Product type:** local developer tool and governed AI-delivery workbench.
- **Primary user:** an operator who creates work, selects a runner, resolves decisions, executes
  dependency-ready implementation tasks, and reviews durable evidence.
- **Primary job:** move one work item from a clear requested outcome to a reviewed, evidenced
  result without losing control of scope, runner choice, or validation state.
- **Platform:** responsive local web UI; desktop is the complete workbench, mobile is for
  monitoring and bounded human decisions.
- **Success signal:** a first-time operator can identify the current work item, current stage,
  selected runner, next action, and consequence without opening technical details.

The target supports `US-01`, `US-02`, `US-03`, `US-05`, `US-06`, `US-11`, and `US-13`. It is an
operator-UX correction inside existing product scope; `docs/product/user-stories.md` does not
need a new story.

## 2. Information architecture and vocabulary

The visible hierarchy is:

```text
Project -> Work Item -> Stage -> Task / Decision -> Run / Attempt -> Document / Evidence
```

Primary vocabulary is literal:

- **Work item** is the user-owned delivery outcome and durable workflow container.
- **Task** is one dependency-aware implementation unit created by `tasklist`.
- **Runner** is the operator-facing execution choice; its canonical runtime id remains visible
  in technical details and provenance.
- **Run** is one workflow execution identity; **attempt** is one stage or task execution attempt.
- **Document** is a Markdown input, stage output, or report. **Evidence** supports a decision but
  is not automatically the source of truth.

`Intent` may describe the request text, but it is not a navigation object, button label, or
replacement name for Work Item.

The desktop shell contains:

1. a compact project and Work Item rail;
2. Work Item tabs: **Overview**, **Tasks**, **Documents**, and **Runs**;
3. the canonical eight-stage strip, grouped visually as Understand, Decide, Deliver, and Prove;
4. one central working surface;
5. a contextual Runner / Decision inspector that is hidden when it adds no value;
6. a collapsible live-output tray tied to the exact active run or attempt.

The Runner selector is visible beside every launch action that requires it. Model, reasoning,
permission, authentication, and command details use progressive disclosure without hiding the
selected runner or action eligibility.

### 2.1 Runner launch-readiness contract

Runner launch readiness is a core-owned projection, not a frontend inference. For the selected
runtime and launch action it exposes the current config identity, probe observation timestamp,
binary and execution-command availability, authentication state, required capabilities,
permission compatibility, selected model/reasoning values, `eligible`, and one literal
`disabled_reason`.

- A prior successful launch is historical evidence only and never authorizes a new launch.
- A probe snapshot collected for a different config or runtime selection is stale. The UI may
  display it as history, but launch remains disabled until readiness is refreshed.
- The application service revalidates readiness before every mutation; a rendered eligible state
  is not an authorization token.
- `authentication=failed`, an unavailable command, a missing required capability, or an
  unsupported non-full permission policy blocks the affected action.
- `authentication=unverified` is a warning rather than a fabricated failure only when the adapter
  cannot provide a conclusive auth probe. The launch may proceed to normal adapter preflight.
- Blank model or reasoning values preserve runtime-native defaults and are omitted from the
  launch payload.

## 3. Main operator flow

1. Open a project and scan Work Items grouped by **Needs input**, **Running**, **Ready**, and
   **Complete**.
2. Create a Work Item by writing a short title, brief outcome, detailed context, constraints, and
   optional additional information; do not require a Runner yet.
3. Review the Work Item, select an eligible Runner, inspect scope and evidence destination, and
   launch the workflow.
4. Follow the eight canonical stages. Open generated Markdown when it matters to the current
   decision; do not force the operator through every document.
5. Resolve questions, approvals, validation failures, runtime failures, and repair exhaustion in
   one bounded Decision Workbench.
6. After `tasklist`, enter **Tasks** by default. Run or resume one dependency-ready task, inspect
   its attempt evidence, and preserve succeeded tasks.
7. Finalize implementation, review the real repository diff and claim evidence, then progress to
   Review and QA.
8. Send selected Review findings or QA risks back to Implement through a durable remediation
   request; rerun stale downstream stages.
9. On fresh terminal QA, inspect the immutable handoff and select one next outcome.

### 3.1 Work Item attention contract

The project list is one core-owned `OperatorInboxView` projection. The frontend renders its
groups and ordering without deriving priority or moving items between states.

| Group | Core-owned membership |
| --- | --- |
| **Needs input** | A question, approval, validation/runtime failure, repair exhaustion, or another explicit human decision owns the next action. |
| **Running** | A workflow, stage, task, finalization, remediation, or rerun job is durably active. |
| **Ready** | No job or blocker is active and the core exposes an allowed launch, resume, or continuation action. |
| **Complete** | Fresh terminal QA produced an immutable handoff. A failed or stale terminal state is not complete. |

Group order is **Needs input**, **Running**, **Ready**, then **Complete**. Within a group, the
core orders by canonical stage order and then stable Work Item id; the first item of the first
non-empty actionable group is the entry recommendation. Complete items are never auto-opened.

## 4. Screen inventory

| Reference | Surface | Primary job | Primary action |
| --- | --- | --- | --- |
| `01-project-work-items.png` | Project Work | Scan active work and select the item requiring attention | Open highest-priority Work Item |
| `02-create-work-item.png` | Create Work Item | Capture outcome, context, and safe identifier | Create Work Item |
| `03-work-item-launch.png` | Work Item Overview, no run | Review request, choose Runner, and confirm launch scope | Launch workflow |
| `04-task-workspace.png` | Implementation Tasks | Scan dependencies and run the next ready task | Run next task |
| `05-active-task-run.png` | Active Run | Monitor one task attempt and intervene only when necessary | Open live output |
| `06-decision-workbench.png` | Question / Approval | Make one bounded human decision with consequences visible | Submit decision |
| `07-validation-repair.png` | Validation Recovery | Understand the exact finding and choose repair or change | Run repair |
| `08-markdown-workspace.png` | Markdown Document Workspace | Read the canonical document and supporting findings | Request change or return to task |
| `09-implementation-review.png` | Implementation Review | Compare claimed work with the repository diff and verification | Proceed to Review |
| `10-review-qa-remediation.png` | Review / QA Gate | Select findings or risks and create a durable remediation | Send selected to Implement |
| `11-run-history.png` | Runs and Attempts | Inspect lineage, attempts, logs, and retained comparisons | Open selected attempt |
| `12-flow-complete.png` | Flow Complete | Review immutable handoff and choose the recommended next outcome | Create new Work Item or Start follow-up |
| `13-mobile-decision.png` | Mobile Decision | Answer, approve, retry, or monitor without dense evidence UI | Current bounded decision |

Generated labels in reference images are illustrative. This written contract and the existing
service semantics are authoritative.

## 5. Markdown interaction contract

Markdown remains the durable interoperability layer. The UI is a reader and controlled authoring
surface over Markdown; it is not a parallel database and not an unrestricted document editor.

### 5.1 Document ownership classes

#### Operator-authored inputs

- `context/user-request.md` follows the `Title`, `Brief`, `Context`, `Constraints`, and
  `Additional information` sections from the durable document contract. The UI shows Write and
  Preview modes, unsaved state, validation, and the exact destination.
- The Work Item header shows only the title and a bounded brief. Detailed context, constraints,
  and additional information remain in the document surface or an explicit details section.
- Existing unsectioned request files are rendered through a lossless compatibility projection and
  are not silently rewritten.
- Once a run has consumed an input revision, changing the requested outcome creates a new
  intervention, remediation, or follow-up input. It never silently rewrites consumed history.
- `answers.md` is authored through a question form with explicit `resolved`, `partial`, or
  `deferred` status. The UI previews the Markdown entry before submission and explains whether it
  unblocks progression.
- intervention, remediation, follow-up, and clone drafts use purpose-specific forms with a
  Markdown preview and source-evidence selector. Drafts are browser state until submitted.

#### Runtime-generated stage documents

- Idea, research, plan, review-spec, tasklist, implementation, review, and QA outputs are
  read-only in the UI.
- The operator changes them through **Request change**, **Run repair**, or the corresponding
  remediation path. The resulting request and new attempt remain durably linked.
- No pencil icon, editable code block, autosave, or ambiguous inline mutation is shown on a
  generated document.

#### Core-owned evidence and diagnostics

- stage results, validator reports, repair briefs, runtime exits, provenance, logs, manifests,
  task-attempt evidence, and archive overlays are read-only.
- Technical evidence can be copied or opened at its exact filesystem path, but this is secondary
  to the current operator decision.

### 5.2 Document Workspace anatomy

The Markdown Workspace contains:

1. a document navigator grouped by stage and role: **Output**, **Questions**, **Validation**,
   **Inputs**, and **Evidence**;
2. a header showing document name, role, stage, attempt, freshness, bounded-read state, and
   source-of-truth status;
3. **Read**, **Source**, and **Compare** views;
4. the Markdown body with a compact heading map;
5. an inspector that anchors unresolved findings to a section or retained line when available;
6. one contextual action such as **Answer question**, **Request change**, **Run repair**, or
   **Return to task**.

**Read** is the default. **Source** exposes exact retained Markdown without making it editable.
**Compare** appears only when two retained revisions exist and always names both attempts. The UI
does not synthesize a historical version or imply a diff when only the current file remains.

Cross-document references open the target document in the same Work Item and preserve the source
document in browser history. Missing, malformed, truncated, stale, and permission-denied states
name what is unavailable, why it matters, and the next safe action.

### 5.3 Authoring behavior

- Drafts survive supported navigation and failed submission, but are not canonical evidence.
- A draft is keyed by project, Work Item, run/stage/task context, purpose, and destination so one
  question, remediation, intervention, follow-up, or clone cannot overwrite another draft.
- Draft state remains browser-session state until submission. It is cleared only after the
  matching server write is durably read back; conflict, reconnect, or failed submission preserves
  the local draft and exposes the server winner separately.
- Back or route changes with an unsaved draft show a leave / keep editing decision.
- Submission enters a pending state, suppresses duplicates, and reconciles to the durable server
  winner after conflict or reconnect.
- A successful write shows the exact Markdown path, retained timestamp, and resulting workflow
  state. Undo is offered only when the underlying contract supports a compensating write.
- Keyboard order is Write -> Preview -> supporting evidence -> primary submit -> secondary cancel.

## 6. Task Workspace contract

After a valid tasklist exists, Tasks becomes the default work surface for Deliver. It shows:

- stable groups: **Ready**, **Running**, **Blocked**, and **Done**;
- task id, outcome-oriented title, dependency badges, attempt count, verification status, and
  last durable event;
- one selected task with scope, acceptance criteria, dependencies, expected files, attempts,
  documents, and blockers;
- a core-owned next-ready recommendation and critical-path marker;
- **Run**, **Resume**, or **Finalize implementation** as mutually exclusive primary actions;
- the selected Runner beside the primary action, with a literal disabled reason when ineligible.
- a dependency-blocked selection exposes the first safe prerequisite recovery target (for example,
  **Resume TL-2**) without enabling a mutation on the blocked task itself;

List is the default because dependency-aware execution is ordered work. A board may be added as a
view preference only after list behavior is complete; it must not permit manual movement that
contradicts canonical dependency or status state.

The groups describe actionability, while the persisted task status remains visible:

| Group | Task rule | Primary action |
| --- | --- | --- |
| **Ready** | Dependencies succeeded and a pending, failed, blocked, or interrupted task is currently actionable. | **Run** before the first attempt; otherwise **Resume**. |
| **Running** | The task ledger records `executing`. | Observe or cancel the exact attempt; no second launch. |
| **Blocked** | Dependencies, unresolved input, a stale tasklist hash, or another core blocker prevents execution. | No task launch; show the blocker and its safe recovery. |
| **Done** | The task ledger records `succeeded`. | Read-only evidence; succeeded tasks cannot rerun. |

When all authored tasks are succeeded and aggregate finalization is not, the task action is
replaced by **Finalize implementation**. A failed finalization becomes **Resume finalization** and
never moves succeeded tasks out of Done. A tasklist/ledger hash mismatch blocks the entire task
workspace and requires a continuation run.

The core-selected next-ready task is the first actionable task in authored order. The
critical-path marker is informational: it marks the unfinished task with the longest remaining
dependency path to a terminal task, with authored order as the tie-breaker. It never overrides
dependency eligibility or automatic authored-order execution; when the graph is stale or invalid,
the marker is omitted.

## 7. State and recovery rules

Every target surface defines loading, empty, partial, error, disabled, selected, pending,
conflict, success, offline, reconnecting, and permission-denied behavior where applicable.

- Empty Project Work exposes one **Create Work Item** action and does not ask for a Runner.
- Missing Runner keeps the launch action disabled beside an explicit **Choose Runner** control.
- Running work preserves the primary context, elapsed time, last output age, milestone, and
  cancel state without fabricated percentage progress.
- Questions and approvals remain distinct decision types even when they share the workbench.
- Validation failure shows document, rule, retained location, hint, repair budget, and the
  consequence of repair versus change.
- Runtime failure never consumes validation repair budget.
- Succeeded tasks remain visibly preserved when another task or aggregate finalization fails.
- A failed implementation task keeps the implementation stage in `failed`/repair-exhausted state;
  `blocked` is reserved for unresolved questions or runtime approvals. Live checkpoints verify this
  agreement across validator output, stage metadata, task ledger, and the recovery projection.
- Stale Review or QA never renders Flow Complete.
- Reconnect restores the exact Work Item, task, attempt, document, draft, and log cursor when the
  durable objects still exist.

## 8. Visual and interaction direction

- Quiet, fast, technical, and editorial; operational density is compact but not microscopic.
- Warm off-white canvas, deep navy navigation, cobalt primary action, mint success, amber warning,
  and red only for destructive or failed states.
- Alignment and whitespace establish hierarchy before borders. Nested cards are limited to true
  repeated objects such as tasks, attempts, or findings.
- Runner selection, current stage, current task or decision, and one primary action remain visible
  in the first desktop viewport.
- Desktop body text is at least 14 px for primary reading and 12 px only for bounded metadata.
- Status uses icon and text, never color alone. Focus is visible and follows visual order.
- Motion is limited to short state transitions, live insertion, and disclosure continuity; reduced
  motion is respected.

## 9. Acceptance criteria

- A first-time operator can create a Work Item and launch with an eligible Runner without opening
  technical settings or encountering duplicate primary actions.
- A returning operator can find the highest-priority decision or running item and open its exact
  context in two actions or fewer.
- After tasklist, the next dependency-ready task and its Runner are visible without scrolling at
  `1280x900` and `1440x900`.
- Generated Markdown cannot be edited in place; every supported write previews the resulting
  Markdown and names the durable destination.
- The document reader preserves role, freshness, attempt, validation, source, and comparison
  truth without fabricating versions.
- Question, approval, runtime failure, validation repair, task resume, implementation review,
  QA remediation, History, and Flow Complete each expose exactly one primary action.
- `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900` pass first-action visibility,
  focus order, target size, contrast, clipping, overflow, and reconnect checks.
- Provider-free browser fixtures cover every reference surface before default routing changes.
- An observed first-time operator completes create -> runner -> launch and question recovery
  without coaching; failures become roadmap tasks rather than undocumented polish requests.

## 10. Scope boundaries

This target does not add a workflow stage, a new adapter contract, direct editing of generated
stage outputs, multi-user cloud coordination, fabricated progress, or frontend-owned eligibility.
Runtime-specific details remain in adapters and core-owned read models remain authoritative.

Wave 42 changes visible vocabulary, composition, and read projections while preserving canonical
`work_item` ids, endpoint names, request shapes, durable paths, and historical evidence text.
Internal compatibility fields such as route `intent` values may remain until an owning task
explicitly migrates them; they must not leak back into user-facing navigation copy. Historical
runs remain read-only compatible and are never rewritten to match the new shell.

The task-centered renderer becomes the default only after its provider-free fixtures, responsive
browser matrix, and observed first-time journey pass. Rollback changes renderer/routing selection
only and never mutates durable workflow state.
