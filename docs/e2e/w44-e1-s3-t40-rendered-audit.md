# W44-E1-S3-T40 rendered follow-up audit

Date: 2026-08-26
Revision: `40632549` (`main` after PR #406)
Capture lane: provider-free Playwright operator harness
Comparison viewports: `1440x900`, `1280x900`, `768x1024`, `390x844`, `320x568`

## Result

The post-T40 Validation Repair hierarchy is present and truthful. The action group is now a normal
child of the right inspector, so the Runner, primary repair, Request change, raw evidence, and the
extension preview remain in order without covering consequence or exact repair-brief evidence. The
change is presentation-only; readiness, route, mutation, and generated-document ownership remain
unchanged.

One target-equivalence gap remains: because the action group is inline, its primary action is below the
initial `1280x900` and `1440x900` viewport on an unscrolled capture. The target asset keeps the full
right inspector and action group in the first desktop screen. The provider-free matrix therefore
retains initial-viewport enforcement on mobile and performs a bounded scroll only for desktop action
geometry; this is evidence for the next convergence task, not an exit pass.

Mobile ordering remains correct after T40: the finding inspector precedes the document stage, the
finding and consequence begin in the initial viewport, and the safe-area primary action remains
reachable.

## Evidence

- `browser_tests/test_w44_validation_repair_viewport.py`: `10 passed`.
- `browser_tests/test_journey_runtime_validation_recovery.py`: `11 passed`.
- `browser_tests/test_w44_target_legacy_compositions.py`: `17 passed`.
- `browser_tests/test_wave42_browser_matrix.py -k validation-repair`: `1 passed` across five viewports.
- Frontend Node suite: `136 passed`; UI contracts: `63 passed`; docs/planning: `50 passed`.
- Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build checks passed.
- Fresh initial and bounded-action screenshots were captured for desktop and mobile; temporary files
  are outside the repository and intentionally not product fixtures.

## Follow-up

`W44-E1-S3-T41` should reclaim only the desktop Validation Repair vertical rhythm needed to expose the
inline Runner and primary action in the supported initial viewport, without restoring a fixed overlay
or changing the mobile dock, action services, readiness semantics, routes, ids, or generated-document
boundaries.
