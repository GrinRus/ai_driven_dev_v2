# Operator UI Studio rollback-window evidence — 2026-07-18

> Historical, non-normative evidence: the selector and rollback renderer described here were
> removed after this bounded check passed. Current installations expose Studio only.

This record captures the bounded source-installed rollback check required before removing the
temporary Operator UI presentation selector. It is automated presentation-parity evidence, not a
substitute for the first-time-operator sessions required by `W36-E7-S3`.

## Tested boundary

- Source revision: `a26a1db` (`feat(ui): make Studio the default renderer`).
- Browser: Playwright Python sync API with Chromium `149.0.7827.55`.
- Fixture: canonical provider-free `terminal-handoff` workspace built through production
  persistence helpers.
- Viewport: `1280x900`.
- Presentations: missing selector (default Studio) and explicit `ui=legacy` rollback.
- Command:

  ```bash
  uv run --extra dev pytest -q browser_tests/test_studio_legacy_rollback_window.py
  ```

## Result

The check passed with one test in 14.18 seconds. Both presentations:

- read byte-for-byte equivalent JSON values from `/api/dashboard` and `/api/run/timeline` for the
  same work item, run, stage, and terminal QA state;
- exposed the same guarded service actions: Create New Work Item, Start Follow-up Flow, Clone Flow,
  Run Eval / Scenario Batch, and Archive Run;
- produced no console errors, page errors, failed requests, or cleanup failures; and
- left the completed source run manifest unchanged by SHA-256.

This result accepts the temporary rollback window for selector removal. It does not authorize a
second workflow implementation: both renderers remain presentations over the same API, mutation,
and durable readback services until the legacy presentation is removed.
