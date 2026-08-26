# W44-E1-S3-T40 rendered follow-up audit

Date: 2026-08-26
Revision: `a759b2af` (`main` after PR #404)
Capture lane: provider-free Playwright operator harness
Comparison viewports: `1440x900`, `390x844`

## Result

The post-T39 Validation Repair hierarchy is present and truthful. The five-viewport validation
journey and target legacy compositions are green, and the retained screenshots show the finding,
document, consequence, repair budget, Runner readiness, and one primary action in the intended order.

One desktop-only visual defect remains: the fixed `.repair-actions` dock sits over the lower part of
the right finding inspector. At `1440x900` it can obscure the consequence's secondary copy and the
exact repair-brief area, while the target composition keeps the action group inside the inspector
flow below the finding facts. This is a presentation overlap, not a readiness, route, mutation, or
generated-document ownership defect.

Mobile ordering is correct after T39: the finding inspector precedes the document stage, the finding
and consequence begin in the initial viewport, and the safe-area primary action remains reachable.

## Evidence

- `browser_tests/test_w44_validation_repair_viewport.py`: `10 passed`.
- `browser_tests/test_journey_runtime_validation_recovery.py`: `11 passed`.
- `browser_tests/test_w44_target_legacy_compositions.py`: `17 passed`.
- Fresh provider-free screenshots were captured for all five supported viewports; temporary files are
  outside the repository and are intentionally not product fixtures.

## Follow-up

`W44-E1-S3-T40` removes the desktop action/inspector overlap while preserving the mobile dock and all
existing action services, readiness semantics, routes, ids, and generated-document boundaries.
