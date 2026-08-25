# W44-E1-S3-T29 rendered exit audit

Date: 2026-08-25
Revision: `08fcc3d9` (`main`)
Capture lane: provider-free Playwright operator harness
Primary comparison viewport: `1280x900`
Mobile comparison viewport: `390x844`

## Scope and method

This is the fresh rendered audit required after `W44-E1-S3-T28`. It re-runs the eight-journey
provider-free browser matrix at `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`,
then captures the full 13-surface target inventory from
[`operator-frontend-target-ux.md`](../architecture/operator-frontend-target-ux.md) at the
desktop comparison viewport and the Mobile Decision surface at `390x844`. Target references are
the `operator-ui-target-v2` images in the architecture assets directory.

The audit checks the written target hierarchy, first-action visibility, responsive containment,
accessible controls, duplicate primary actions, document overflow, console diagnostics, and
whether the current surface still exposes truthful core-owned state. It does not change routes,
API payloads, core projections, task eligibility, generated-document immutability, or mutation
services.

Temporary screenshot and measurement bundles from this run are retained locally at:

- `/var/folders/0y/qkpd1n592qjgm3w3rcl_gs6m0000gn/T/w44-t29-captures-ngsxubn7/`;
- `/tmp/w44-t29-matrix.XGxVLC/`.

They are evidence for this audit, not committed product fixtures.

## Technical baseline

The focused W44 browser suites remain green: `71 passed` in
`uv run pytest -q browser_tests/test_w44_*.py`. The fresh eight-journey responsive matrix is not
an exit pass: `6 passed, 2 failed` in `353.48s`.

The two failures are contract-level first-viewport gaps:

1. `create-runner-launch` at `320x568`: `#globalNextActionButton` starts at `y=541.4` with
   `height=44`, so its bottom is `17.4px` below the viewport.
2. `completion` at `768x1024`: the visible `[data-next-flow-action]` is rendered at `y=3165.9`
   in a `3229px` document, so the recommended terminal action is not in the initial viewport.

Other matrix journeys passed their technical assertions. The fresh captures also confirm that
the Markdown Workspace T28 composition is present, generated documents remain read-only, and the
document/context inspector, heading map, source actions, and one primary action are visible.

## Surface comparison

| Ref | Surface | Result | Confirmed remaining gap | Follow-up |
| --- | --- | --- | --- | --- |
| 01 | Project Work Items | Gap | The selected view still leads with a large returning-work banner and repeated search, while the target is a compact grouped table with progress bars, event/status columns, and a consistently sized right inspector. | `W44-E1-S3-T34` |
| 02 | Create Work Item | Partial | The target editor/preview hierarchy and one create action are present. The shared shell still exposes verbose legacy navigation/path context, but no create-specific first-action or overflow defect was found. | Shell follow-up only |
| 03 | Work Item Launch | Partial / mobile gap | Desktop has one contextual Runner inspector and one launch action. The fresh matrix shows the launch action falling below the `320x568` initial viewport. The target readiness list is also denser than the no-run state. | `W44-E1-S3-T30` |
| 04 | Task Workspace | Partial | Authoritative groups, next-ready selection, dependencies, and the selected-task inspector render. The table is substantially denser than before, but the target still keeps more rows and a more prominent next-ready card in the first viewport. | `W44-E1-S3-T32` |
| 05 | Active Task Run | Gap | The selected attempt inspector and factual controls render, but the live-output tray begins below the `900px` desktop viewport (`y≈1056`) instead of sharing the first viewport with the task table and inspector as in the target. | `W44-E1-S3-T32` |
| 06 | Decision Workbench | Partial / mobile gap | Desktop rationale, evidence, resolution semantics, and durable answer controls are truthful. On `390x844`, the resolution controls begin around `y=1142`; only the question and textarea/action dock are visible initially, unlike the target bounded decision composition. | `W44-E1-S3-T33` |
| 07 | Validation Repair | Partial | Finding, source document, heading map, repair consequence, Runner readiness, and one repair action are co-visible. The current reader/finding layout remains denser and less balanced than the target three-region recovery composition. | `W44-E1-S3-T39` |
| 08 | Markdown Workspace | Pass with residual shell gap | T28 now provides the compact navigator, reader, heading map, freshness/provenance, source/path utilities, read-only footer, and contextual Request change/Return to task actions. The surrounding shell still shows verbose path context compared with the target project/Work Item header. | Shell follow-up only |
| 09 | Implementation Review | Gap | Repository truth and one Review action are present, but the first viewport is a narrow summary/ledger stack with unused right-side space rather than the target full-width diff/claims/verification workspace and review inspector. | `W44-E1-S3-T35` |
| 10 | Review / QA Remediation | Gap | Findings, source evidence, durable Write/Preview, downstream staleness, and one remediation action are present, but the current central table/request split does not fill the target three-region composition or preserve its evidence density. | `W44-E1-S3-T36` |
| 11 | Runs and Attempts | Partial | Retained runs, selected attempt, chronology, lineage, raw-log/artifact views, and read-only actions are present. The current chronology remains vertically long and leaves more unused shell space than the target compact history composition. | `W44-E1-S3-T37` |
| 12 | Flow Complete | Partial / tablet gap | Immutable handoff, QA, retained evidence, recommendation, and lineage outcomes are truthful. The recommended action is below the initial `768x1024` viewport and the handoff/evidence tables remain more vertically stacked than the target compact completion composition. | `W44-E1-S3-T31` |
| 13 | Mobile Decision | Gap | The mobile question summary and fixed answer action are visible, but evidence, resolution choices, durable destination, and saved-state context are pushed below the first viewport. | `W44-E1-S3-T33` |

## Shared shell finding

Across the fresh captures, the top context bar renders an absolute temporary project path in the
breadcrumb. The target contract names the project, Work Item, and current stage without exposing a
filesystem path. This is a common composition/privacy mismatch rather than a route or data-model
issue and is recorded for a later bounded shell task (`W44-E1-S3-T38`).

## Confirmed invariants

The audit did not find regressions in the following contracts:

- existing Work Item ids, route intents, API shapes, DOM compatibility ids, and historical evidence
  remain intact;
- core-owned Inbox membership/order, task status, dependency eligibility, and Runner readiness
  remain outside browser-side inference;
- generated Markdown remains read-only and Source/Compare semantics are retained;
- launch and recovery mutations remain fail-closed with at most one contextual primary action;
- the focused W44 suites report no new accessibility, geometry, console, or horizontal-overflow
  failures in their covered states.

## Decision and next queue

`W44-E1-S3-T29` is complete as an evidence/decomposition task, but it is **not** a Wave 44 exit
pass. The two first-viewport failures are executable UI defects, and the surface comparison still
shows bounded target-composition gaps in Project Work, Active Task, Decision/Mobile Decision,
Implementation Review, Review/QA Remediation, History, and Flow Complete. The next implementation
cycle must start with the launch first-viewport correction, then re-run the same matrix before
promoting later surface work. Human usability, Claude/cross-runtime, and Wave 36 acceptance remain
parked.
