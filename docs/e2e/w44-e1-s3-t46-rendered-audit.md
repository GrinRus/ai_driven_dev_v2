# W44-E1-S3-T46 rendered audit

Date: 2026-08-26  
Implementation merge: PR #418 (`f533b336`)  
Target references: `docs/architecture/assets/operator-ui-target-v2/03-work-item-launch.png` and
`docs/architecture/assets/operator-ui-target-v2/13-mobile-decision.png`

## Change under review

The mobile Work Item detail header now exposes the AIDD brand, current Work Item identity, an
accessible Inbox/back path, and the existing overflow/runtime control in one compact row. The
change is scoped to overview detail mode; setup, Inbox, recovery, question, routes, DOM ids, status
ownership, and launch semantics are unchanged.

## Fresh rendered evidence

The provider-free no-run fixture was captured after the merged implementation at:

- `/tmp/w44-post-t46-1280.png`;
- `/tmp/w44-post-t46-1440.png`;
- `/tmp/w44-post-t46-768.png`;
- `/tmp/w44-post-t46-390.png`;
- `/tmp/w44-post-t46-320.png`.

At `390x844` and `320x568`, the detail topbar is 64px high. It contains the visible `AIDD` brand,
the `WI-BROWSER` identity, the Inbox arrow button with the original accessible `Inbox` label, and
the overflow/runtime control. The detail context remains below the tabs and the current-stage
summary, decision inspector, and stage disclosure remain in normal document flow. At `768x1024`,
the compact tablet topbar remains 64px and context → tabs → stages ordering is preserved. At
`1280x900` and `1440x900`, the detail topbar remains collapsed, with the title/context → tabs →
stages → decision hierarchy starting in the first viewport. All five captures have
`document.documentElement.scrollWidth === innerWidth`.

## Target comparison and decision

The target mobile reference keeps product and Work Item identity in the dark header; T46 now does
so without duplicating the detail card's truthful status. The desktop references require the
two-level navy rail, Work Item tabs, grouped eight-stage strip, central surface, and contextual
launch inspector; the fresh desktop captures retain those elements and their existing route/state
semantics. The written target contract remains authoritative where illustrative reference content
differs from provider-free fixture copy.

The audit found no additional bounded target-equivalence gap in the supported shell surfaces. The
Wave 44 rendered acceptance loop is therefore complete through T46. Human usability sessions,
Claude/cross-runtime evidence, and Wave 36 acceptance remain explicitly parked and are not implied
by this UI decision.

## Verification

- `uv run --extra dev pytest -q browser_tests/test_w44_desktop_shell.py` — 20 passed.
- `uv run --extra dev pytest -q browser_tests/test_mobile_studio_header.py` — 6 passed.
- `uv run --extra dev pytest -q browser_tests/test_mobile_primary_decision.py -k globalNextActionButton` — 4 passed.
- `node --test tests/frontend/*.test.mjs` — 136 passed.
- `uv run --extra dev pytest -q tests/test_docs_consistency.py tests/test_planning_integrity.py` — 50 passed.
- Ruff and mypy — passed.
- PR CI — Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, packaged UI browser,
  build, CodeQL, dependency review, and scorecard all passed.

## Compatibility

Existing Work Item ids, route/API shapes, DOM compatibility ids, stage order, status ownership,
launch/recovery controls, Inbox/setup behavior, mobile decision behavior, and historical evidence
remain unchanged. T46 is complete and no T47 follow-up is opened.
