from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (390, 844)))
def test_ready_task_workspace_keeps_core_ledger_and_one_launch_action_visible(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"ready-{viewport[0]}",
        "implementation-task-ready",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        route = (
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement&work_tab=tasks"
            "&task_id=TL-2"
        )
        response = page.goto(route, wait_until="networkidle")
        assert response is not None and response.ok

        workspace = page.locator("[data-task-workspace]")
        workspace.wait_for(state="visible")
        selected = page.locator('[data-task-select="TL-2"]')
        selected.wait_for(state="visible")
        assert selected.get_attribute("aria-pressed") == "true"
        assert selected.get_attribute("data-task-status") == "pending"
        assert page.locator('[data-task-group="Ready"] [data-task-select]').count() == 1
        assert page.locator('[data-task-group="Done"] [data-task-select]').count() == 1
        assert (
            page.locator('[data-task-group="Ready"] .task-dependency-badge').inner_text()
            == "TL-1"
        )
        assert (
            page.locator('[data-task-group="Ready"] [data-task-group-count="Ready"]').inner_text()
            == "1"
        )
        assert page.locator('[data-task-group="Running"] [data-task-group-empty]').count() == 1
        assert page.locator('[data-task-group="Blocked"] [data-task-group-empty]').count() == 1

        detail = page.locator("[data-task-detail]")
        detail.wait_for(state="visible")
        assert "src/changed.py" in detail.inner_text()
        assert "src/new.py" in detail.inner_text()
        assert "Repository evidence agrees with the report" in detail.inner_text()
        assert page.locator('[data-task-action="run"]').count() == 1
        assert page.locator('[data-task-action-bar][data-action-recommended="run"]').count() == 1
        assert page.locator("[data-task-action-bar] [data-contextual-runner-control]").count() == 1
        assert page.locator('[data-task-action="resume"]').count() == 0
        assert page.locator('[data-task-action="finalize"]').count() == 0
        assert page.locator("[data-task-attempt-tray]").count() == 1

        table_headers = page.locator(".task-workspace-table-head [role=columnheader]")
        if viewport[0] > 760:
            assert table_headers.count() == 5
        else:
            assert table_headers.count() == 5
            assert all(not table_headers.nth(index).is_visible() for index in range(5))

        page.reload(wait_until="networkidle")
        page.locator('[data-task-select="TL-2"].selected').wait_for(state="visible")
        assert "task_id=TL-2" in page.url

        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        browser_page.diagnostics.assert_clean()
