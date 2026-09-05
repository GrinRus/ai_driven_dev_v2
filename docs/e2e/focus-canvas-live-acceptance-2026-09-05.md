# Focus Canvas live acceptance — 2026-09-05

## Scope

This is the live local-project acceptance record for Wave 47 Focus Canvas. The app was started
from the current source tree with `aidd ui` through `operator_browser_harness`; the browser drove
the loopback HTTP server and a disposable `.aidd/` project fixture. This is live production UI/API
evidence, not a standalone prototype and not a claim of external-provider acceptance.

- Source revision: `f2819535` plus the working-tree Focus Canvas changes.
- Browser: Playwright `1.61.0`, Chromium `149.0.7827.55`.
- Fixture: `blocking-question`, Work Item `WI-BROWSER`, run `run-browser`, stage `idea`.
- Captures: `/tmp/aidd-focus-canvas-live-desktop.png` and
  `/tmp/aidd-focus-canvas-live-mobile.png`.
- Network boundary: loopback UI/API only; no provider or credential was used.

## Live flow evidence

The following checks were run against the started project and passed:

1. Inbox routing: `test_inbox_prioritizes_and_routes_durable_and_running_work` passed at
   `390x844` and `1280x900`. The test opens the prioritized **Needs input** item, posts the
   Work Item context switch, and lands on the `idea` Decision Workbench with the same Work Item,
   run, and stage identity.
2. Durable decision lifecycle: `test_question_recovery_restores_draft_and_resumes_from_durable_answer`
   passed at `390x844` and `1280x900`. A partial/deferred draft remains blocked, reload and
   history navigation restore the draft, Save performs one `/api/answers` write and durable
   readback without `/api/stage/run`, and the separate Resume performs one readiness-checked stage
   launch after the server confirms `resolved`.
3. Live execution: the Resume path produced a real active job with `run_id=run-browser`; the
   active-job journey passed `1280x900`, showing live output, reconnect/recovery, persisted logs,
   and cancellation without losing the originating context.
4. Recovery variants: rejected interview candidate recovery passed at `390x844` and `1280x900`;
   validation recovery passed across the supported viewport matrix; runtime retry remained
   separate from the validation repair budget.

## Rendered acceptance

- Focus Canvas hierarchy passed at `320x568`, `390x844`, `768x1024`, `1280x900`, and `1440x900`.
- Desktop keeps one primary decision action in the first viewport; supporting evidence remains
  in document flow.
- Mobile places Decision Impact before the editor, keeps the primary action touch-sized and
  fixed, and preserves the compact AIDD / Work Item / Inbox / overflow header.
- The fresh captures reported `scrollWidth=1280` and `scrollWidth=390` respectively. Browser
  diagnostics were clean: no console errors, page errors, failed requests, blocked requests, or
  HTTP responses at or above 400.
- The evidence disclosure exposes the source document, retained attempt, durable destination,
  and provenance strip; it never makes generated Markdown editable.

## Verification commands

```text
node --test tests/frontend/operator-decision-synchronization.test.mjs tests/frontend/operator-ui-state.test.mjs tests/frontend/operator-draft-store.test.mjs  # 47 passed
uv run --extra dev pytest -q tests/cli/test_ui_assets_contracts.py tests/test_docs_consistency.py tests/test_planning_integrity.py  # 105 passed
uv run --extra dev pytest -q browser_tests/test_w44_decision_recovery_target.py::test_question_workbench_keeps_target_hierarchy_at_supported_viewports  # 5 passed
uv run --extra dev pytest -q browser_tests/test_w44_decision_recovery_target.py::test_validation_and_review_recovery_routes_land_on_authoritative_surfaces  # 2 passed
uv run --extra dev pytest -q browser_tests/test_w44_decision_recovery_target.py::test_approval_workbench_exposes_one_primary_action_at_supported_viewports  # 5 passed
uv run --extra dev pytest -q browser_tests/test_journey_inbox.py::test_inbox_prioritizes_and_routes_durable_and_running_work  # 2 passed
uv run --extra dev pytest -q browser_tests/test_journey_question_recovery.py::test_question_recovery_restores_draft_and_resumes_from_durable_answer  # 2 focused viewports passed
uv run --extra dev pytest -q browser_tests/test_journey_question_recovery.py::test_rejected_interview_candidate_recovery_preserves_focus_and_repair_budget  # 2 passed
uv run --extra dev pytest -q browser_tests/test_journey_active_studio.py::test_active_studio_reconnects_cancels_and_returns_to_durable_logs[viewport3]  # 1 passed
uv run --extra dev pytest -q browser_tests/test_journey_runtime_validation_recovery.py::test_runtime_recovery_keeps_retry_single_and_separate_from_summary  # 2 passed
uv run --extra dev pytest -q browser_tests/test_journey_runtime_validation_recovery.py::test_validation_recovery_exposes_one_eligible_primary_action  # 2 passed
git diff --check
```

The provider-free live acceptance is complete for the Focus Canvas scope. Human first-time
operator sessions and external Codex/Claude provider acceptance remain separate, explicitly
parked gates and are not implied by this record.
