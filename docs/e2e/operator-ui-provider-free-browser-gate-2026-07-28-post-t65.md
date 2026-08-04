# Provider-Free Packaged UI Browser Gate — 2026-07-28 Post-T65

This is the sanitized `provider-free-browser-pass-v1` record for the final post-T65
Wave 36 rerun. No product, fixture, timeout, or provider behavior changed during
the gate. No live provider or large scenario was invoked.

## Candidate

- Source commit: `b38dd4c4eb252e269d061d3618e6f06fbe23b0f9`
- Source tree: `8facd6ef24a93865161637cc05bd05f040d54a94`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Viewports: `320x568`, `390x844`, `768x1024`, `1280x900`, `1440x900`
- Network boundary: provider-free disposable loopback UI only

The tracked worktree was clean throughout the gate. The only worktree entry was
the pre-existing excluded user snapshot
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`.

## Executions

1. The exact four historical race cases passed `4/4` in `90.99s`.
2. The complete intervention and terminal families passed `24/24` in `332.59s`
   (`14/14` intervention and `10/10` terminal).
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` discovered
   and executed the exact ordered registry `W36-E7-S1-T1..T12`. The discovered
   and executed lists were identical, `failed_ids=[]`, and all `79/79` tests
   passed in `2185.87s`. Recovery journey `W36-E7-S1-T3` passed `9/9`;
   intervention journey `W36-E7-S1-T10` passed `14/14`.
4. `uv run --extra dev pytest -q browser_tests` passed `188/188` in `3274.98s`.

All five viewports completed without a console, page, failed-request, overflow,
accessibility, or bounded process-cleanup failure. The runs created no tracked or
additional untracked source-tree residue, and no test-owned process remained.

## Result

- Overall result: `passed`
- Product or fixture changes during gate: none
- Failed journey IDs: none
- Next action: build and verify the exact tracked-archive candidate in
  `W36-E7-S4-T37`.
