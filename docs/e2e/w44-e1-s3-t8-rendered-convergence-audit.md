# W44-E1-S3-T8 rendered convergence audit

Date: 2026-08-24  
Revision: `c03d66c6` (`main`)  
Capture lane: provider-free Playwright operator harness  
Desktop viewport: `1280x900`  
Mobile viewport: `390x844` for Mobile Decision  

## Scope and method

This audit reruns the 13 target surfaces from
[`operator-frontend-target-ux.md`](../architecture/operator-frontend-target-ux.md) after
`W44-E1-S3-T7` token alignment. The capture set is retained locally at
`/tmp/w44-audit-v2-new/`; those PNGs are audit evidence, not product fixtures.

The provider-free journeys were opened through the existing public routes and durable fixture
states. Where a surface requires an interaction to expose its target composition, the audit used
the existing route/action contract (for example, the empty-project create surface and the
implementation quality-gate entry). No API shape, route intent, task ledger, or mutation service
was changed for the audit.

## Technical baseline

All 13 captures returned HTTP 200. The captured document width was equal to or below the viewport
width. The authoritative five-viewport provider-free matrix on the same revision remained green
(`9 passed`) with clean diagnostics, focus, target-size, initial-action, and overflow assertions.

The T7 palette is visible in the captures: the workspace is warm off-white, the context rail is
deep navy, launch controls are cobalt, and success/warning states use mint/amber semantic roles.
The shared body reading role is 14px. This fixes the previous global visual-token mismatch but does
not by itself make every target composition present in the first viewport.

## Surface results

| Ref | Surface | Result | Fresh finding |
| --- | --- | --- | --- |
| 01 | Project Work Items | Partial | Core groups, search, Work Item rows, and one durable action render. The project route has no target-style selected Work Item inspector and no target filter/table header composition. |
| 02 | Create Work Item | Partial | The direct operator-request editor and Read/Preview destination are present. Guided Setup/project setup and saved-item context still share the first composition instead of the focused target form. |
| 03 | Work Item Launch | Partial | Tabs, eight-stage strip, and one launch action are present. The no-run state correctly asks for runtime selection, but the selected Runner readiness inspector is not visible until a runtime is chosen. |
| 04 | Task Workspace | Partial | Ready/Running/Blocked/Done groups, selected task detail, dependency badge, core next-ready marker, and Run action render. The initial composition does not show a live tray, and the action dock compresses the lower selected-task/Runner area. |
| 05 | Active Task Run | Gap | The current provider-free running-stage capture does not expose a selected task attempt with factual elapsed time, last-output age, milestone, reconnect cursor, and collapsible raw output in the first viewport. |
| 06 | Decision Workbench | Partial | Question context, evidence/consequence inputs, durable destination, stage shell, and one answer action are present. Resolution/destination details fall below the desktop first viewport; mobile keeps the primary action visible but the lower answer context is still condensed. |
| 07 | Validation Repair | Partial | Finding, location, repair brief, budget, Runner, Request Change, and Run Repair are present. The three-column evidence/action composition compresses Runner copy and gives the long evidence card equal visual weight with the first repair decision. |
| 08 | Markdown Workspace | Gap | The role/provenance document list and stale evidence are available, but the selected Markdown reader/heading map is below the first viewport behind the document list and stale rerun panel. |
| 09 | Implementation Review | Partial | Repository summary, changed-file/verification claims, task identity, and quality-gate evidence render. The target review composition is not a dedicated first-viewport diff/claims/verification workspace yet. |
| 10 | Review/QA Remediation | Partial | Rejected finding, source evidence, related paths, selection, downstream consequence, and the existing single remediation action render correctly. The target compact review shell and evidence/action density are not fully matched. |
| 11 | Runs and Attempts | Partial | Filters, retained frames, selected attempt, lineage, and read-only history are visible. The target chronology/inspector density and first-viewport handoff hierarchy still differ. |
| 12 | Flow Complete | Partial | Immutable handoff, QA result, retained evidence, completion inspector, and core recommendation are visible. The lower handoff/evidence rows continue below the first viewport rather than using the target compact table composition. |
| 13 | Mobile Decision | Partial | Work Item, run, stage strip, question, answer destination, and pinned single primary action remain truthful and unclipped. Resolution-state and supporting-consequence context require additional scroll on the 390px capture. |

## Confirmed follow-up slices

The following are bounded product gaps, not environment blockers:

- Project Work needs a target-aligned selected Work Item inspector and filter/table composition.
- Active Task Run needs a provider-free running-attempt fixture and the target live-output tray.
- Markdown Workspace needs the selected reader and heading/finding context in the first readable
  viewport.
- Validation Repair needs a responsive finding-to-action hierarchy that keeps Runner identity and
  the primary repair decision readable before long evidence.

These findings are split into `W44-E1-S3-T14` through `T17` in the reconciliation that follows this
audit. Wave 44 remains open until those slices and a later fresh audit satisfy the target contract.

## Decision

`W44-E1-S3-T8` is complete as a fresh rendered audit and gap decomposition. It is **not** a Wave 44
exit pass: the target renderer must not be declared complete, and the default task-centered routing
decision remains provisional until the follow-up slices are merged and re-audited.
