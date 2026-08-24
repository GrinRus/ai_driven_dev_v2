# W44-E1-S3-T19 rendered exit audit

Date: 2026-08-25  
Revision: `35ff0ace` (`main`)  
Capture lane: provider-free Playwright operator harness  
Desktop comparison viewport: `1280x900`  
Mobile decision viewport: `390x844`

## Scope and method

This audit repeats the 13-surface target inventory from
[`operator-frontend-target-ux.md`](../architecture/operator-frontend-target-ux.md) after
`W44-E1-S3-T18`. The target reference images are the `operator-ui-target-v2` assets in the same
architecture directory. Fresh screenshots were captured locally under
`/tmp/w44-t19-audit-20260825/`; they are audit evidence, not product fixtures.

The evidence set combines:

- the provider-free browser matrix over all five supported viewports;
- the target legacy-composition checks for Create Work Item, Runs/Attempts, and Flow Complete;
- fresh desktop captures for the selected Project Work inspector, launch, Tasks, Active Task,
  Decision, Validation Repair, Markdown, Review, History, and Flow Complete surfaces;
- a fresh `390x844` Mobile Decision capture with the primary action visible.

The audit checks target hierarchy, contextual actions, state vocabulary, responsive containment,
accessible controls, initial action visibility, duplicate primary actions, horizontal overflow,
console errors, and failed requests. It does not change routes, API payloads, core ownership, task
ledger semantics, or mutation services.

## Technical baseline

The authoritative provider-free matrix passed `9` tests across
`320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`. The target legacy-composition suite
passed `5` tests. Those checks reported no console errors, failed requests, blocked requests,
horizontal overflow, duplicate primary actions, or focus/target-size violations in their covered
states. The existing stage-strip and accessibility suites remain green.

This is a technical pass only. A clean browser diagnostic does not prove visual convergence with
the target composition.

## Surface comparison

| Ref | Surface | Result | Confirmed visual gap | Follow-up |
| --- | --- | --- | --- | --- |
| 01 | Project Work Items | Gap | Selected inspector and table rows share the same width; the selected action can be visually crowded by the inspector instead of occupying the target right column. | `W44-E1-S3-T20` |
| 02 | Create Work Item | Partial | The editor and preview exist, but the current Guided Setup/top navigation and lower project context do not match the focused target editor/preview shell. | `W44-E1-S3-T26` |
| 03 | Work Item Launch | Partial | The no-run view exposes a truthful runtime choice, but the target launch inspector hierarchy and full stage-label presentation are not consistently visible in the initial desktop composition. | `W44-E1-S3-T21` |
| 04 | Task Workspace | Partial | The authoritative groups, selected task, dependencies, and Run action render, but the target right-side task inspector and table density are not reproduced consistently. | `W44-E1-S3-T22` |
| 05 | Active Task Run | Gap | The current active-attempt tray is a separate block above the task workspace; the target keeps the selected attempt inspector on the right and live output in a dedicated lower tray. | `W44-E1-S3-T22` |
| 06 | Decision Workbench | Partial | The question and durable answer controls are truthful, but supporting rationale, evidence, resolution state, and consequence are not arranged with the target hierarchy on every viewport. | `W44-E1-S3-T23` |
| 07 | Validation Repair | Partial | Finding, consequence, Runner, and repair action are present, while the target compact finding-to-action hierarchy still differs in density and responsive composition. | `W44-E1-S3-T23` |
| 08 | Markdown Workspace | Partial | Navigator, read-only body, heading map, freshness, and evidence are present, but the target reader/inspector shell and spacing remain visually different. | `W44-E1-S3-T28` |
| 09 | Implementation Review | Partial | Repository evidence and quality-gate data render, but the target first viewport is a dedicated diff/claims/verification workspace rather than the current summary-plus-gate stack. | `W44-E1-S3-T27` |
| 10 | Review/QA Remediation | Partial | Findings and source evidence are actionable, but the target scope/evidence/remediation density and action hierarchy are not matched. | `W44-E1-S3-T27` |
| 11 | Runs and Attempts | Partial | Retained runs, chronology, lineage, and inspector exist, but the target chronology/inspector composition is denser and keeps the selected attempt hierarchy clearer. | `W44-E1-S3-T24` |
| 12 | Flow Complete | Partial | Immutable handoff and recommendation are correct, but handoff, evidence, completion, and next-outcome blocks do not yet match the target compact composition. | `W44-E1-S3-T25` |
| 13 | Mobile Decision | Gap | The primary answer action is visible and focusable, but the target mobile decision context (why it matters, evidence, resolution choices, destination, and saved state) is not retained in the same readable hierarchy. | `W44-E1-S3-T23` |

## Confirmed invariants

The following are not gaps in this audit:

- existing Work Item ids, route intents, API shapes, DOM compatibility ids, and historical
  evidence remain intact;
- core-owned Inbox membership/order, task status, dependency eligibility, and Runner readiness
  remain outside browser-side inference;
- generated Markdown remains read-only;
- launch and recovery controls remain fail-closed and preserve one-primary-action rules;
- supported viewports do not exhibit horizontal document overflow in the authoritative matrix.

## Decision and next queue

`W44-E1-S3-T19` is complete as an evidence and decomposition task, but it is **not** a Wave 44
exit pass. The target shell and several first-viewport compositions still diverge from the
normative target. Default task-centered routing remains provisional until the bounded follow-ups
are implemented and a fresh rendered audit confirms the gaps are gone.

The next dependency-ready task is `W44-E1-S3-T20`. Human usability, Claude/cross-runtime, and
Wave 36 acceptance remain parked and are not prerequisites for this UI convergence loop.
