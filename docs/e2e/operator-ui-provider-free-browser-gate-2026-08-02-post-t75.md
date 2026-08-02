# Provider-Free Packaged UI Browser Gate — 2026-08-02 Post-T75

This is the sanitized `provider-free-browser-pass-v1` record for the post-T75
Wave 36 rerun. No product, fixture, timeout, or provider behavior changed during
the gate. No live provider, candidate-only, large, or xlarge scenario was invoked.

## Candidate

- Source commit: `5d37caeb9b4d8348b795470fe04b03bd700b051a`
- Source tree: `374b94bb5d95d469b516bcda66a700f9a96a827d`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Viewports: `320x568`, `390x844`, `768x1024`, `1280x900`, `1440x900`
- Network boundary: provider-free disposable loopback UI only

The tracked worktree was clean throughout the gate. The only worktree entry was
the pre-existing excluded user snapshot
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`.

## Executions

1. The exact four historical race cases passed `4/4` in `131.60s`.
2. The complete intervention and terminal families passed `24/24` in `408.31s`
   (`14/14` intervention and `10/10` terminal).
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` discovered
   and executed the exact ordered registry `W36-E7-S1-T1..T12`. The discovered
   and executed lists were identical, `failed_ids=[]`, and all `79/79` tests
   passed in summed `1813.28s`. Runtime/validation Recovery passed `9/9`,
   intervention passed `14/14`, and the final Inbox journey passed `9/9`.
4. After two discarded infrastructure-only attempts were externally terminated
   with no test failure while another workspace's quality pipeline was active, a
   fresh uninterrupted canonical `uv run --extra dev pytest -q browser_tests`
   passed `188/188` in `1975.10s` once the host was free. The discarded attempts
   did not change source and are not acceptance evidence.

All five viewports completed without a console, page, failed-request, overflow,
accessibility, or bounded process-cleanup failure. Postflight found no test-owned
UI, fixture-runtime, pytest, or packaged-runner process. The runs created no
tracked or additional untracked source-tree residue.

## Result

- Overall result: `passed`
- Product or fixture changes during gate: none
- Failed journey IDs: none
- Next action: build and verify the exact tracked-archive candidate in
  `W36-E7-S4-T37`.
