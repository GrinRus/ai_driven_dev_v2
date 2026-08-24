# W44-E1-S3-T2 Target UX audit

Date: 2026-08-24  
Revision: `14ca9232` (`main`)  
Capture lane: provider-free Playwright operator harness  
Viewport set: `1280x900` for desktop surfaces and `390x844` for Mobile Decision

## Scope and method

The audit compares the rendered Operator UI with the normative target in
[`operator-frontend-target-ux.md`](../architecture/operator-frontend-target-ux.md) and the
13 target references in `docs/architecture/assets/operator-ui-target-v2/`.

1. Load each provider-free route from the shared surface manifest.
2. Capture the settled rendered surface with the local operator browser harness.
3. Inspect the saved screenshot against the matching target reference.
4. Check route response status, console/page diagnostics, failed or blocked requests, and
   document width at the captured viewport.
5. Separate technical browser acceptance from visual and information-architecture parity.

Current captures are retained locally at `/tmp/w44-audit-v1/` as `01` through `13` PNG files.
They are local audit evidence, not product fixtures or release artifacts.

## Technical baseline

The captured routes returned HTTP 200, emitted no console or page errors, had no failed or
blocked requests, and did not exceed the viewport width. The existing five-viewport browser
matrix remains the authoritative check for clipping, focus order, target size, duplicate
primary actions, and overflow. These checks prove that the current UI is stable; they do not
prove visual equality with the target references.

## Surface findings

| Ref | Surface | Result | Confirmed gap |
| --- | --- | --- | --- |
| 01 | Project Work | Partial | Inbox groups and selected inspector exist, but the target project selector, Work Item search/list rail, dense rows, filters, and table columns are absent. |
| 02 | Create Work Item | Fails target parity | The screen is the legacy Guided Setup flow with project/runtime steps; the target starts with a direct Work Item outcome form and defers Runner selection until launch. |
| 03 | Work Item Launch | Partial | Work Item tabs, stage strip, and contextual action exist, but the project/work-item rail, cobalt action treatment, and compact readiness inspector are missing. |
| 04 | Task Workspace | Fails target parity | The fixture renders only Done tasks as large teal cards, so the target Ready row, selected task inspector, dependency columns, Runner readiness, and live tray are not represented. |
| 05 | Active Task Run | Partial | Work Item context and stage path exist, but the target active-attempt composition and persistent work-item rail are not present in the first viewport. |
| 06 | Decision Workbench | Fails target parity | The Work Item identity and stage strip disappear; a generic validation-recovery block precedes the question instead of the target decision context, evidence, consequence, and answer form. |
| 07 | Validation Repair | Fails target parity | Recovery is rendered as a broad stacked card layout without the persistent Work Item/stage shell or the target finding-to-repair hierarchy. |
| 08 | Markdown Workspace | Closest | Navigator, bounded reader, Source/Compare affordances, and evidence inspector are present; the persistent rail, palette, and target editorial density still differ. |
| 09 | Implementation Review | Partial | Repository review surface and contextual action exist, but the target shell and target diff/verification hierarchy are not represented in the captured composition. |
| 10 | Review/QA Remediation | Fails target parity | The surface falls back to generic validation recovery and loses the Work Item/stage context required to explain remediation and downstream staleness. |
| 11 | Runs and Attempts | Fails target parity | History has filters and chronology, but only the tabs remain visible; the target Work Item shell, lineage context, and selected-attempt inspector are absent. |
| 12 | Flow Complete | Fails target parity | The handoff is rendered as large green cards without the target Work Item header, eight-stage strip, handoff summary table, evidence table, and completion inspector. |
| 13 | Mobile Decision | Fails target parity | The header says `AIDD / Inbox`; Work Item title, current stage summary, actual question context, answer states, destination, and durable save form are not visible. |

## Cross-surface findings

### P0 — persistent shell identity is incomplete

The target hierarchy is `Project → Work Item → Stage → Task / Decision → Run / Attempt →
Document / Evidence`. The current UI has a fixed navigation rail, but it is only a set of
top-level buttons. Recovery, history, completion, and mobile decision surfaces do not retain a
visible Work Item title and current stage. This makes the operator lose context exactly where
the consequence of an action is highest.

### P0 — primary task path is not visually exercised

The Task Workspace implementation has core-owned groups and selected-task data, but the
provider-free fixture used for the audit contains only succeeded tasks. The target's primary
path is a Ready task with dependencies, Runner readiness, one Run action, and a live-output
tray. The fixture and rendered composition therefore cannot establish target parity for the
main delivery job.

### P0 — decision surfaces show recovery chrome instead of the decision

Desktop and mobile decision states expose a generic recovery summary before the actual
question or repair form. The target requires the question/finding, why it matters, evidence,
resolution state, destination, draft state, and one consequence-bearing primary action in the
first readable surface.

### P1 — create, history, and completion still use legacy compositions

Create is still a guided setup wizard, History is a chronology canvas without the target shell,
and Flow Complete uses large status cards instead of the target handoff/evidence tables. These
are distinct surfaces and should not be hidden behind a token-only polish pass.

### P1 — visual language is not aligned

The target calls for warm off-white canvas, deep navy navigation, cobalt primary actions,
mint success, amber warning, and at least 14px primary desktop reading text. The current token
set still uses teal as the primary action and `--type-body-size: 13px`; many component rules also
use hard-coded 13px values.

## Accessibility and evidence limits

The existing browser assertions cover rendered geometry, overflow, focus order, accessible
names, target sizes, duplicate primary actions, and diagnostics. Screenshot inspection alone
cannot prove keyboard traversal, contrast ratios, screen-reader announcements, or reconnect
behavior for every state. Those remain test obligations for each follow-up task.

## Convergence decision

Wave 44 visual convergence is **open**. The current default renderer must not be declared
target-complete. The confirmed gaps are actionable frontend work, not environment blockers.

The next bounded task is to render the persistent target Project/Work Item rail and context shell
without changing routes, API shapes, core projections, or mutation semantics. Subsequent tasks
must separately cover the Ready-task composition, decision/recovery content, legacy create flow,
History/Flow Complete composition, and target tokens.

