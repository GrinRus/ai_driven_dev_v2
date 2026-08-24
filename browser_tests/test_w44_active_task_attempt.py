from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
@pytest.mark.parametrize(
    ("status", "connection", "expect_cancel"),
    (
        ("running", "online", True),
        ("waiting-for-operator", "offline", True),
        ("cancelling", "reconnecting", True),
        ("failed", "online", False),
        ("completed", "online", False),
    ),
)
def test_active_task_attempt_tray_keeps_factual_live_output_and_one_primary(
    tmp_path: Path,
    viewport: tuple[int, int],
    status: str,
    connection: str,
    expect_cancel: bool,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"active-task-{viewport[0]}-{status}",
        "implementation-task-ready",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement&work_tab=tasks&task_id=TL-2",
            wait_until="networkidle",
        )
        assert response is not None and response.ok
        page.locator('[data-task-select="TL-2"]').wait_for(state="visible")
        page.evaluate(
            """({status, connection}) => {
              state.activeJobStatus = {
                kind: "task",
                job_id: "job-active-task",
                work_item: state.activeRouteWorkItem,
                run_id: state.activeRunId,
                stage: "implement",
                status,
                attempt_path: ".aidd/attempts/task-TL-2/1",
                elapsed_seconds: 87,
                runtime_output_age_seconds: 4,
                message: "Focused verification started",
              };
              state.activeJobConnection = {
                state: connection,
                failureCount: connection === "online" ? 0 : 1,
                retryDelayMs: 500,
              };
              state.activeJobCursor = 11;
              state.activeJobLogChunks = [{
                stream: "stdout",
                text: "pytest -q tests/example.py\\nfocused verification",
              }];
              return renderCockpit();
            }""",
            {"status": status, "connection": connection},
        )
        tray = page.locator('[data-task-attempt-tray][data-active-task-attempt="true"]')
        tray.wait_for(state="visible")
        assert "TL-2" in tray.inner_text()
        assert ".aidd/attempts/task-TL-2/1" in tray.inner_text()
        assert "1m 27s" in tray.inner_text()
        assert "Last runtime output 4s ago" in tray.inner_text()
        assert "Reconnect cursor" in tray.inner_text()
        assert page.locator("[data-task-attempt-primary]").count() == 1
        assert page.locator("[data-task-attempt-output]").count() == 1
        assert (
            page.locator("[data-task-attempt-output]")
            .evaluate("node => node.closest('details').open")
            is False
        )
        assert (page.locator("[data-cancel-job]").count() == 1) is expect_cancel
        if status == "cancelling":
            assert page.locator("[data-cancel-job]").is_disabled()
        if connection != "online":
            assert page.locator(f'[data-connection-state="{connection}"]').count() == 1
        tray_text = tray.inner_text().lower()
        assert "progress" not in tray_text
        assert "%" not in tray_text
        assert (
            page.locator(
                '[data-task-attempt-tray] [data-aidd-primary-action]:visible'
            ).count()
            == 1
        )
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        browser_page.diagnostics.assert_clean()
