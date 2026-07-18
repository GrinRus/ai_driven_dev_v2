from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.state_fixtures import build_browser_state_fixture


def test_question_draft_survives_reload_and_clears_after_readback(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "question", "blocking-question")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(harness.url, wait_until="networkidle")
        answer = page.locator('[data-question-text="Q1"]')
        answer.wait_for(state="visible")
        answer.fill("Preserve the public CLI boundary.")
        page.locator('[data-question-resolution="Q1"]').select_option("resolved")

        page.reload(wait_until="networkidle")
        restored = page.locator('[data-question-text="Q1"]')
        restored.wait_for(state="visible")
        assert restored.input_value() == "Preserve the public CLI boundary."
        assert page.locator('[data-question-draft-restored="Q1"]').is_visible()
        card = page.locator('[data-question-id="Q1"]')
        assert card.get_attribute("data-question-status") == "pending-blocking"
        assert card.get_attribute("data-answer-resolution") == "resolved"

        page.route(
            "**/api/answers",
            lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body='{"error":"simulated failure"}',
            ),
        )
        with page.expect_response(lambda response: response.url.endswith("/api/answers")):
            page.locator('[data-save-answer="Q1"]').click()
        assert page.evaluate("readOperatorDraft(questionDraftIdentity('Q1')) !== null")
        page.unroute("**/api/answers")
        expected_failures = [
            item for item in browser_page.diagnostics.http_statuses if item[1] == 500
        ]
        assert len(expected_failures) == 1
        browser_page.diagnostics.http_statuses = [
            item for item in browser_page.diagnostics.http_statuses if item[1] != 500
        ]
        expected_console = [
            item
            for item in browser_page.diagnostics.console_errors
            if "500 (Internal Server Error)" in item
        ]
        assert len(expected_console) == 1
        browser_page.diagnostics.console_errors = [
            item
            for item in browser_page.diagnostics.console_errors
            if "500 (Internal Server Error)" not in item
        ]

        answer_posts: list[str] = []

        def record_answer_post(request: object) -> None:
            if getattr(request, "method", None) == "POST" and str(
                getattr(request, "url", "")
            ).endswith("/api/answers"):
                answer_posts.append(str(request.url))

        page.on("request", record_answer_post)
        page.evaluate("Promise.all([saveAnswer('Q1'), saveAnswer('Q1')])")
        page.wait_for_function(
            "readOperatorDraft(questionDraftIdentity('Q1')) === null"
        )
        assert len(answer_posts) == 1
        assert restored.input_value() == "Preserve the public CLI boundary."
        browser_page.diagnostics.assert_clean()


def test_intervention_draft_isolated_from_question_and_restored(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "intervention", "blocking-question")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(harness.url, wait_until="networkidle")
        page.evaluate("renderRequestChange()")
        request = page.locator("#operatorRequestText")
        request.wait_for(state="visible")
        request.fill("Update only the current stage document.")
        assert page.evaluate(
            """() => {
              const event = new Event("beforeunload", {cancelable: true});
              window.dispatchEvent(event);
              return event.defaultPrevented;
            }"""
        )
        page.evaluate("renderRequestChange()")
        restored = page.locator("#operatorRequestText")
        assert restored.input_value() == "Update only the current stage document."
        counts = page.evaluate(
            """() => {
              const bucket = loadOperatorDraftBucket();
              return Object.values(bucket.entries).reduce((result, item) => {
                result[item.form] = (result[item.form] || 0) + 1;
                return result;
              }, {});
            }"""
        )
        assert counts == {"intervention": 1}
        browser_page.diagnostics.assert_clean()


def test_intervention_submit_creates_one_stage_scoped_request(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "allowed-intervention", "blocking-question")
    configure_sleeping_fixture_runtime(fixture.project_root, sleep_seconds=20)
    request_root = (
        fixture.workspace_root
        / "workitems"
        / fixture.work_item
        / "stages"
        / "idea"
        / "operator-requests"
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        page.evaluate("renderRequestChange()")
        page.locator('[data-intervention-eligible="true"]').first.wait_for(
            state="visible"
        )
        page.locator("#operatorRequestText").fill(
            "Update only the current stage evidence."
        )
        with page.expect_response(
            lambda response: response.url.endswith("/api/stage/interact")
        ) as launch:
            page.locator("#submitInterventionButton").click()
        assert launch.value.status == 200
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not list(request_root.glob("request-*.md")):
            time.sleep(0.05)
        requests = list(request_root.glob("request-*.md"))
        assert len(requests) == 1
        assert "Update only the current stage evidence." in requests[0].read_text(
            encoding="utf-8"
        )
        browser_page.diagnostics.assert_clean()


def test_intervention_rejects_succeeded_downstream_without_request(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(tmp_path / "blocked-intervention", "qa-decision")
    request_root = (
        fixture.workspace_root
        / "workitems"
        / fixture.work_item
        / "stages"
        / "plan"
        / "operator-requests"
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.evaluate(
            "state.activeStage = 'plan'; state.activeStageExplicit = true; fetchDashboard()"
        )
        page.evaluate("renderRequestChange()")
        blocked = page.locator('[data-intervention-eligible="false"]').first
        blocked.wait_for(state="visible")
        assert "requires remediation routing" in page.locator(
            "#cockpitContent"
        ).inner_text()
        assert page.locator("#submitInterventionButton").is_disabled()
        page.evaluate("submitIntervention()")
        page.wait_for_timeout(100)
        assert not request_root.exists()
        browser_page.diagnostics.assert_clean()
