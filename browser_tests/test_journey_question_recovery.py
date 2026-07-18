from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, Route, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "question-recovery"


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


def _discard_expected_answer_failure(browser_page: object) -> None:
    diagnostics = browser_page.diagnostics
    failures = [
        item for item in diagnostics.http_statuses if item[1] == 500
    ]
    assert len(failures) == 1
    diagnostics.http_statuses = [
        item for item in diagnostics.http_statuses if item[1] != 500
    ]
    console = [
        item
        for item in diagnostics.console_errors
        if "500 (Internal Server Error)" in item
    ]
    assert len(console) == 1
    diagnostics.console_errors = [
        item
        for item in diagnostics.console_errors
        if "500 (Internal Server Error)" not in item
    ]


@pytest.mark.parametrize("selector", ("studio", "legacy"))
def test_question_recovery_parity_preserves_answer_service_path(
    tmp_path: Path,
    selector: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"question-parity-{selector}",
        "blocking-question",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui={selector}", wait_until="networkidle")
        assert page.evaluate(
            "window.aiddPresentation.surfaces['question-recovery'].presentation"
        ) == selector
        page.locator('[data-question-text="Q1"]').fill(
            "Use the same durable answer service path."
        )
        page.locator('[data-question-resolution="Q1"]').select_option("resolved")
        with page.expect_response(
            lambda response: response.url.endswith("/api/answers")
        ) as saved:
            page.locator('[data-save-answer="Q1"]').click()
        assert saved.value.status == 200
        assert saved.value.request.post_data_json == {
            "stage": "idea",
            "question_id": "Q1",
            "text": "Use the same durable answer service path.",
            "resolution": "resolved",
        }
        page.wait_for_function("readOperatorDraft(questionDraftIdentity('Q1')) === null")
        assert "Use the same durable answer service path." in (
            fixture.workspace_root
            / "workitems"
            / fixture.work_item
            / "stages"
            / "idea"
            / "answers.md"
        ).read_text(encoding="utf-8")
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_question_recovery_restores_draft_and_resumes_from_durable_answer(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"question-recovery-{viewport[0]}",
        "blocking-question",
    )
    configure_sleeping_fixture_runtime(fixture.project_root, sleep_seconds=30)

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        root = page.locator('[data-human-decision-surface="question"]')
        root.wait_for(state="visible")
        _assert_rendered_gate(page, viewport)

        answer = page.locator('[data-question-text="Q1"]')
        answer.fill("Keep the public CLI and durable evidence boundaries unchanged.")
        resolution = page.locator('[data-question-resolution="Q1"]')
        resolution.select_option("partial" if viewport[0] % 2 == 0 else "deferred")
        assert page.locator('[data-answer-resume="Q1"]').is_disabled()

        page.reload(wait_until="networkidle")
        answer = page.locator('[data-question-text="Q1"]')
        answer.wait_for(state="visible")
        assert answer.input_value().startswith("Keep the public CLI")
        assert page.locator('[data-question-draft-restored="Q1"]').is_visible()

        page.evaluate(
            "navigateOperatorRouteIntent('historical-run', {"
            f"workItem: '{fixture.work_item}', runId: '{fixture.run_id}', stage: 'idea'"
            "})"
        )
        page.wait_for_function(
            "new URLSearchParams(location.search).get('mode') === 'history'",
            timeout=10_000,
        )
        page.go_back(wait_until="networkidle")
        answer = page.locator('[data-question-text="Q1"]')
        answer.wait_for(state="visible")
        assert answer.input_value().startswith("Keep the public CLI")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)

        resolution = page.locator('[data-question-resolution="Q1"]')
        resolution.select_option("resolved")

        def _fail_answer(route: Route) -> None:
            if urlsplit(route.request.url).path != "/api/answers":
                route.continue_()
                return
            route.fulfill(
                status=500,
                content_type="application/json",
                body='{"error":"simulated durable answer failure"}',
            )

        page.route("**/api/answers", _fail_answer)
        with page.expect_response(
            lambda response: urlsplit(response.url).path == "/api/answers"
        ):
            page.locator('[data-save-answer="Q1"]').click()
        page.unroute("**/api/answers", _fail_answer)
        assert page.evaluate("readOperatorDraft(questionDraftIdentity('Q1')) !== null")
        _discard_expected_answer_failure(browser_page)

        answer_posts: list[str] = []
        stage_posts: list[str] = []

        def _record_answer(request: object) -> None:
            if getattr(request, "method", None) == "POST" and urlsplit(
                str(getattr(request, "url", ""))
            ).path == "/api/answers":
                answer_posts.append(str(request.url))
            if getattr(request, "method", None) == "POST" and urlsplit(
                str(getattr(request, "url", ""))
            ).path == "/api/stage/run":
                stage_posts.append(str(request.url))

        page.on("request", _record_answer)
        resume_button = page.locator('[data-answer-resume="Q1"]')
        assert not resume_button.is_disabled()
        page.evaluate("answerAndResume('Q1')")
        assert len(answer_posts) == 1
        assert len(stage_posts) == 1
        page.wait_for_function("readOperatorDraft(questionDraftIdentity('Q1')) === null")

        answers = page.evaluate(
            "eval('state.dashboard.active_stage_view.questions.questions')"
        )
        durable = next(item for item in answers if item["question_id"] == "Q1")
        assert durable["answer_resolution"] == "resolved"
        assert durable["answer_text"].startswith("Keep the public CLI")

        job_id = page.evaluate("eval('state.activeJobId')")
        if job_id:
            cancel = page.request.post(f"{harness.url}api/jobs/{job_id}/cancel")
            assert cancel.status == 200
        browser_page.diagnostics.assert_clean()
