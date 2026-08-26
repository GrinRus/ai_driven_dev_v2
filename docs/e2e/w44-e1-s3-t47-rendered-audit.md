# W44-E1-S3-T47 rendered audit

Date: 2026-08-26<br>
Implementation merge: PR #421 (`722e38b0`)<br>
Target reference: `docs/architecture/assets/operator-ui-target-v2/13-mobile-decision.png`

## Change under review

The recovery-mode mobile header now keeps the same target identity hierarchy as the mobile Decision
composition: the AIDD brand, current Work Item identity, an accessible Inbox/back path, and the
existing overflow/runtime disclosure. The CSS is scoped to `body.recovery-mode`; overview, Inbox,
and Guided Setup headers retain their existing compositions. Question, approval, validation, and
runtime-recovery content, routes, DOM ids, status ownership, and one-primary-action behavior are
unchanged.

## Fresh rendered evidence

The provider-free recovery/question captures were taken from the PR head (`5d4d04c6`, the exact
implementation commit included in merge `722e38b0`) at:

- `/tmp/w44-t47-audit/question-390-final.png`;
- `/tmp/w44-t47-audit/question-390.png`;
- `/tmp/w44-t47-audit/question-320.png`;
- `/tmp/w44-t47-audit/runtime-390.png`;
- `/tmp/w44-t47-audit/validation-320.png`.

The final mobile question capture shows `AIDD`, the truncated `WI-BROWSER` Work Item identity, the
Inbox arrow, and the vertical-dots overflow control in one compact dark header. Route assertions
at both supported mobile widths verify a 66px header, visible Work Item context, Inbox and overflow
controls at least 44px wide, literal `←` and `⋮` affordances, and
`document.documentElement.scrollWidth <= window.innerWidth`. The recovery and question content
remains below the header and keeps its existing primary action and decision semantics.

The capture is retained as local evidence only; no credentials, provider calls, or sensitive
operator data are included.

## Target comparison and decision

The target reference requires current Work Item identity and a bounded way back to the Work Item
context before the decision content. T47 closes the only gap found by the post-T46 five-viewport
audit. The desktop two-rail shell, Work Item tabs, eight-stage strip, contextual launch inspector,
and mobile decision surface remain covered by the earlier rendered audits and provider-free matrix.
Fixture copy density may differ from the illustrative reference image; the written target contract
remains authoritative for behavior and hierarchy.

The Wave 44 rendered acceptance loop is complete through T47. The task-centered renderer/default
routing decision is accepted for the supported provider-free surfaces. Human usability sessions,
Claude/cross-runtime comparison, and Wave 36 acceptance remain parked and are not implied by this
UI decision.

## Verification

- `uv run --extra dev pytest -q browser_tests/test_mobile_studio_header.py::test_mobile_recovery_route_exposes_current_work_item_identity` — 4 passed.
- `uv run --extra dev pytest -q browser_tests/test_mobile_studio_header.py::test_mobile_recovery_header_keeps_identity_and_decision_surface` — 4 passed.
- `uv run --extra dev pytest -q browser_tests/test_w44_decision_recovery_target.py::test_question_recovery_renders_the_decision_before_shared_chrome ...::test_question_workbench_keeps_target_hierarchy_at_supported_viewports` — 7 passed.
- `node --test tests/frontend/*.test.mjs` — 136 passed.
- `uv run --extra dev pytest -q tests/cli/test_ui_assets_contracts.py tests/cli/test_ui_focus_contract.py tests/test_docs_consistency.py tests/test_planning_integrity.py` — 105 passed.
- Ruff and mypy — passed.
- PR #421 CI — Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, packaged UI browser, build, CodeQL, dependency review, and Scorecard all passed.

## Compatibility

Existing Work Item ids, route/API shapes, DOM compatibility ids, stage order, status ownership,
recovery/question actions, overview/Inbox/setup behavior, and historical evidence remain unchanged.
