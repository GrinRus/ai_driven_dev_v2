from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Page, Route, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, BrowserDiagnostics, operator_browser_harness
from browser_tests.journey_support import configure_sleeping_fixture_runtime
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "active-studio"


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


def _assert_expected_diagnostics(diagnostics: BrowserDiagnostics) -> None:
    assert len(diagnostics.console_errors) == 1
    assert "503" in diagnostics.console_errors[0]
    assert diagnostics.page_errors == []
    assert diagnostics.failed_requests == []
    assert diagnostics.blocked_requests == []
    unexpected = [
        (url, status)
        for url, status in diagnostics.http_statuses
        if status >= 400
        and not (status == 503 and "/logs" in urlsplit(url).path)
    ]
    assert unexpected == []


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_active_studio_reconnects_cancels_and_returns_to_durable_logs(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"active-{viewport[0]}", "no-run")
    configure_sleeping_fixture_runtime(fixture.project_root, sleep_seconds=60)

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_function("eval('selectedRuntimeReady()')", timeout=15_000)
        page.wait_for_function(
            "!document.querySelector('#globalNextActionButton')?.disabled",
            timeout=5_000,
        )
        _assert_rendered_gate(page, viewport)

        page.locator("#globalNextActionButton").click()
        page.wait_for_function("eval('state.activeJobStatus?.status') === 'running'", timeout=5_000)
        page.wait_for_function("eval('state.activeJobCursor') > 0", timeout=10_000)
        job_id = page.evaluate("eval('state.activeJobId')")
        assert isinstance(job_id, str) and job_id

        page.locator("#tab-work").click()
        observation = page.locator('[data-studio-observation="ui-job"]')
        observation.wait_for(state="visible")
        assert "Live runtime evidence is updating" in observation.inner_text()
        assert "%" not in observation.inner_text()
        _assert_rendered_gate(page, viewport)

        def _silence_status(route: Route) -> None:
            if urlsplit(route.request.url).path != f"/api/jobs/{job_id}":
                route.continue_()
                return
            response = route.fetch()
            payload = response.json()
            payload.update(
                {
                    "elapsed_seconds": 140,
                    "runtime_output_age_seconds": 140,
                    "silence_warning": True,
                }
            )
            route.fulfill(response=response, json=payload)

        page.route("**/api/jobs/**", _silence_status)
        page.evaluate("pollActiveJob()")
        page.unroute("**/api/jobs/**", _silence_status)
        page.locator("#tab-work").click()
        observation.wait_for(state="visible")
        assert "No runtime output" in observation.inner_text()

        observation.locator('[data-tab-shortcut="logs"]').click()
        cursor_before_failure = page.evaluate("eval('state.activeJobCursor')")
        failed_once = False

        def _transient_log_failure(route: Route) -> None:
            nonlocal failed_once
            if failed_once:
                route.continue_()
                return
            failed_once = True
            route.fulfill(
                status=503,
                content_type="application/json",
                body='{"error":"transient browser journey failure"}',
            )

        page.route("**/api/jobs/*/logs?*", _transient_log_failure)
        page.evaluate("pollActiveJob()")
        page.unroute("**/api/jobs/*/logs?*", _transient_log_failure)
        page.locator('[data-connection-state="reconnecting"]').wait_for(state="visible")
        assert page.evaluate("eval('state.activeJobCursor')") == cursor_before_failure
        page.locator('[data-connection-state="recovered"]').wait_for(
            state="visible",
            timeout=5_000,
        )
        assert page.evaluate("eval('state.activeJobCursor')") >= cursor_before_failure
        _assert_rendered_gate(page, viewport)

        page.locator("[data-cancel-job]:visible").first.click()
        page.wait_for_function("eval('state.activeJobId') === ''", timeout=15_000)
        page.locator("#cockpitContent").get_by_text(
            "Saved runtime.log", exact=False
        ).first.wait_for(state="visible", timeout=10_000)
        assert "runtime" in page.locator("#cockpitContent").inner_text().lower()
        _assert_rendered_gate(page, viewport)
        _assert_expected_diagnostics(browser_page.diagnostics)
