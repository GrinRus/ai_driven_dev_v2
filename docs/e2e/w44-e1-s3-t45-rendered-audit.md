# W44-E1-S3-T45 rendered audit

Date: 2026-08-26  
Implementation merge: PR #416 (`efec5a79`)  
Target reference: `docs/architecture/assets/operator-ui-target-v2/03-work-item-launch.png` and
`13-mobile-decision.png`

## Change under review

The tablet Work Item detail shell now uses one compact top-level row at `768x1024`. The duplicated
breadcrumb/status chrome is hidden on detail views, and the Work Item context card is explicitly
ordered before tabs and the canonical stage strip. Inbox and setup keep their established topbars;
mobile navigation and decision/recovery behavior are unchanged.

## Fresh rendered evidence

The provider-free no-run fixture was captured after the implementation at:

- `/tmp/w44-post-t45-1280.png`;
- `/tmp/w44-post-t45-1440.png`;
- `/tmp/w44-post-t45-768.png`;
- `/tmp/w44-post-t45-390.png`;
- `/tmp/w44-post-t45-320.png`.

At `768x1024`, the compact topbar is 64px high, context begins at y=76, tabs at y=158.6, and the
stage strip at y=213.6. The decision inspector follows at y=442.6, with no horizontal overflow.
The title, truthful Work Item id/status, tabs, and stage strip are therefore available in the
target order without the former 227px legacy topbar.

Desktop remains stable: at `1280x900`, the collapsed detail topbar is zero-height, context begins at
y=4, tabs at y=90.9, and stages at y=145.9. At `1440x900`, the same hierarchy begins at y=4/92.2/147.2.

## Remaining bounded gap

The mobile overview captures are technically contained and keep the existing decision and stage
summary, but their topbar hides the product brand and current Work Item identity, leaving only the
Inbox entry and overflow/runtime control. The target mobile header keeps the AIDD brand and a
truncated Work Item label visible. This is a separate responsive identity task, `W44-E1-S3-T46`,
and is not folded into the tablet shell change.

## Verification

- `uv run --extra dev pytest -q browser_tests/test_w44_desktop_shell.py` — 18 passed.
- `uv run --extra dev pytest -q browser_tests/test_journey_active_studio.py -k reconnects_cancels` — 5 passed.
- `node --test tests/frontend/*.test.mjs` — 136 passed.
- `uv run --extra dev pytest -q tests/test_provider_free_routes.py tests/test_packaged_ui_scenarios.py tests/test_w43_ownership_matrix.py` — 11 passed.
- `uv run --extra dev pytest -q tests/test_docs_consistency.py tests/test_planning_integrity.py` — 50 passed.
- Ruff and mypy — passed.
- PR CI — Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, packaged UI browser,
  build, CodeQL, dependency review, and scorecard all passed.

## Compatibility and decision

Existing Work Item ids, route/API shapes, DOM compatibility ids, stage order, status ownership,
launch/recovery controls, Inbox/setup behavior, mobile navigation semantics, and historical evidence
remain unchanged. T45 is complete. Target convergence remains open only for the mobile detail
identity gap tracked as T46; default task-centered routing remains provisional until that task is
reviewed or explicitly accepted as a bounded responsive exception.
