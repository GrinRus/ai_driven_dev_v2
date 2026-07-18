# Provider-Free Packaged UI Browser Pass — 2026-07-18

This is the accepted `provider-free-browser-pass-v1` record for the source-installed
Document & Evidence Studio. It contains no provider credentials, project paths, runtime logs,
generated `.aidd/` state, or human-observation metrics.

- Evidence schema: `provider-free-browser-pass-v1`
- AIDD version: `0.1.0a16.dev0`
- Source commit: `28f8e26bf07e3dc4a1340bc9541e3e93ce2b6405`
- Execution command: `uv run --extra dev python scripts/run_packaged_ui_scenarios.py`
- Browser: `Chromium 149.0.7827.55`
- Fixture family: `browser_tests.state_fixtures` at the source commit above
- Viewports: `320x568, 390x844, 768x1024, 1280x900, 1440x900`
- Journey ids: `W36-E7-S1-T1..T12`
- Discovered journey ids: `T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12`
- Executed journey ids: `T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12`
- Journey results: all 12 passed; `failed_ids: []`
- Accessibility: passed accessible-name, label, focus-order, contrast, touch-size, and
  reduced-motion assertions owned by the journey fixtures
- Geometry: passed header footprint, first-viewport primary action, clipping, overlap,
  single-scroll-owner, and horizontal-overflow assertions
- Console/page errors: none reported by browser diagnostics
- Failed requests: none unexplained; intentional negative-boundary requests returned their
  asserted fail-closed status
- Network boundary: loopback-only passed
- Cleanup: pages, contexts, and browsers closed; UI process groups stopped; temporary fixture
  projects and generated `.aidd/` workspaces removed by the bounded harness
- Overall result: `passed`
- Blocker: `none`

The runner reported exact discovered/executed identity in canonical journey order. This record
is automated rendered-browser evidence only. Human elapsed time, wrong actions, assistance,
confidence, and first decisive confusion remain owned by the observed acceptance lane
`W36-E7-S3`.
