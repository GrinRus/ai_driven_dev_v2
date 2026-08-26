# W44-E1-S3-T41 rendered audit

Date: 2026-08-26  
Revision: `d7994130` (`main` after PR #408)  
Capture lane: provider-free Playwright operator harness  
Comparison viewports: `1440x900`, `1280x900`, `768x1024`, `390x844`, `320x568`

## Result

The Validation Repair action hierarchy now matches the target ordering without using a fixed
overlay. On the supported desktop viewports, the finding context, consequence, exact repair brief,
Runner readiness, and the primary `Run repair` action are visible in the initial viewport. The
tablet keeps the same normal-flow composition and may scroll; mobile keeps its safe-area-aware
primary-action dock. Existing readiness revalidation, mutation services, routes, ids, and
generated-document read-only boundaries are unchanged.

Fresh captures show no overlap, nested shell scroll, duplicate primary action, console/page error,
failed same-origin request, or horizontal overflow. The compacting rules use existing semantic UI
tokens and do not alter the factual attempt or repair-budget content.

## Target comparison

The remaining clear target-equivalence gap is outside the Validation Repair content: detail surfaces
currently render the project navigation and Work Items list as one combined desktop rail, while the
target detail compositions use a narrow primary icon rail followed by a separate Work Items
navigator. The project Inbox target intentionally uses only the primary rail. This route-scoped shell
split is recorded as `W44-E1-S3-T42`; it must preserve all existing navigation ids and deep-link
semantics before Wave 44 can claim target-equivalent shell chrome.

## Verification

- `browser_tests/test_w44_validation_repair_viewport.py`: `10 passed`.
- `browser_tests/test_wave42_browser_matrix.py -k validation`: `1 passed` across five viewports.
- `browser_tests/test_journey_runtime_validation_recovery.py browser_tests/test_w44_target_legacy_compositions.py`: `28 passed`.
- Frontend Node suite: `136 passed`; UI contracts: `53 passed`; docs/planning: `50 passed`.
- Ruff, mypy, full CI, deterministic, adapter, packaged-browser, security, and build checks passed.
- Temporary fresh screenshots are outside the repository and are not product fixtures.
