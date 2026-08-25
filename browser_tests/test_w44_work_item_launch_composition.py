from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

VIEWPORTS = ((1280, 900), (1440, 900), (768, 1024), (390, 844), (320, 568))


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_work_item_launch_has_one_runner_inspector_and_readable_overview(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"work-item-launch-{viewport[0]}",
        "no-run",
        work_item="WI-LAUNCH",
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok
        page.locator("[data-work-item-overview]").wait_for(state="visible")

        runner = page.locator('[data-runner-inspector-mode="launch"]')
        primary = page.locator("#globalNextActionButton")
        assert runner.count() == 1
        assert primary.count() == 1
        assert runner.locator("[data-open-runner]").count() == 1
        assert page.locator("[data-work-item-request-source]").count() == 1

        runner_box = runner.bounding_box()
        primary_box = primary.bounding_box()
        assert runner_box is not None and primary_box is not None
        assert runner_box["x"] + runner_box["width"] <= viewport[0] + 0.5
        assert primary_box["x"] + primary_box["width"] <= viewport[0] + 0.5
        assert primary_box["y"] >= runner_box["y"] + runner_box["height"] - 1
        if viewport == (320, 568):
            primary.focus()
            assert page.evaluate(
                "() => document.activeElement === document.querySelector('#globalNextActionButton')"
            )

        if viewport[0] >= 1100:
            stage_lists = page.locator(".canonical-stage-group .intent-phase-list")
            assert stage_lists.evaluate_all(
                "nodes => nodes.map(node => "
                "getComputedStyle(node).gridTemplateColumns.split(' ').length)"
            ) == [1, 1, 1, 1]
        assert page.locator(".canonical-stage-step").evaluate_all(
            "nodes => nodes.every(node => "
            "[...node.querySelectorAll('strong, small')].every("
            "text => text.scrollWidth <= text.clientWidth + 1))"
        )
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()
