# Provider-Free Packaged UI Browser Gate — 2026-07-27

This is the sanitized `provider-free-browser-pass-v1` record for the required
post-private-auth Wave 36 rerun. No product, fixture, or timeout change was made during
the gate.

## Candidate

- Source commit: `314aedf129521c5c19ec5efa3fa6e3853dea8594`
- Source tree: `9703b025f95f8cba81a4a2dd5b631916be06afec`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Viewports: `320x568`, `390x844`, `768x1024`, `1280x900`, `1440x900`
- Network boundary: provider-free disposable loopback UI only

The tracked worktree was clean throughout the gate. The only worktree entry was the
pre-existing excluded user snapshot
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`.

## Executions

1. The exact four historical race cases passed `4/4` in `106.58s`: intervention draft
   reconciliation at `320x568`, `1280x900`, and `1440x900`, plus terminal handoff at
   `1280x900`.
2. The complete intervention and terminal families passed `24/24` in `635.23s`
   (`14/14` intervention and `10/10` terminal).
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` discovered and
   executed the exact ordered registry `W36-E7-S1-T1..T12`. The discovered and executed
   lists were identical, `failed_ids=[]`, and all `79/79` tests passed. Historical
   intervention journey `W36-E7-S1-T10` passed `14/14`.
4. `uv run --extra dev pytest -q browser_tests` passed `188/188` in `3325.77s`.

All five viewports completed without a console, page, failed-request, overflow,
accessibility, or test-owned bounded process-cleanup failure. The runs created no tracked
or additional untracked source-tree residue.

## Result

- Overall result: `passed`
- Product or fixture changes during gate: none
- Failed journey IDs: none
- Next action: build and verify the exact tracked-archive candidate in
  `W36-E7-S4-T37`.
