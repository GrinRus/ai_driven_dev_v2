# Provider-Free Packaged UI Browser Gate — 2026-08-03 Post-T79

This is the sanitized `provider-free-browser-pass-v1` record for the post-T79 Wave 36 rerun.
No product, fixture, timeout, or provider behavior changed during the gate. No live provider,
candidate-only, large, or xlarge scenario was invoked.

## Candidate

- Tested source commit: `c040f0e96457031b6a04d210c2e715c29ad76d55`
- Tested source tree: `75fe01904a5b12cdf5eb87009c99bd083a07ed0b`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Viewports: `320x568`, `390x844`, `768x1024`, `1280x900`, `1440x900`
- Network boundary: provider-free disposable loopback UI only

The tracked worktree was clean throughout the gate. The only worktree entry was the pre-existing
excluded user snapshot `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`.

## Executions

1. The exact four historical race cases passed `4/4` in `68.84s`: intervention draft
   reconciliation at `320x568`, `1280x900`, and `1440x900`, plus terminal handoff at `1280x900`.
2. The complete intervention and terminal families passed `24/24` in `282.31s` (`14/14`
   intervention and `10/10` terminal).
3. `uv run --extra dev python scripts/run_packaged_ui_scenarios.py` discovered and executed the
   exact ordered registry `W36-E7-S1-T1..T12`. The discovered and executed lists were identical,
   `failed_ids=[]`, and all `79/79` tests passed in summed `1394.59s`. Runtime/validation Recovery
   passed `9/9`, intervention passed `14/14`, and Inbox passed `9/9`.
4. One fresh uninterrupted canonical `uv run --extra dev pytest -q browser_tests` passed
   `188/188` in `2071.90s`.

All five viewports completed without a console, page, failed-request, overflow, accessibility, or
bounded process-cleanup failure. Explicit final postflight found no test-owned UI,
fixture-runtime, pytest, or packaged-runner process. The runs created no tracked or additional
untracked source-tree residue.

## Result

- Overall result: `passed`
- Product or fixture changes during gate: none
- Failed journey IDs: none
- Next action: build and verify the exact tracked-archive Codex candidate in `W36-E7-S4-T37`.
