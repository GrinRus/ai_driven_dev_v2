from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
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
                answer_posts.append(str(getattr(request, "url")))

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
