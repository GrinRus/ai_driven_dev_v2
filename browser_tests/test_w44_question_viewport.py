from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


def test_question_primary_action_is_visible_in_the_initial_viewport(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "question-recovery",
        "blocking-question",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for viewport in VIEWPORTS:
            with harness.open_page(viewport) as browser_page:
                page = browser_page.page
                response = page.goto(
                    f"{harness.url}?mode=studio&work_item={fixture.work_item}"
                    f"&run_id={fixture.run_id}&stage=idea&view=recovery",
                    wait_until="networkidle",
                )
                assert response is not None and response.ok

                surface = page.locator('[data-human-decision-surface="question"]').first
                action = page.locator(
                    '[data-human-decision-surface="question"] [data-primary-action]'
                )
                surface.wait_for(state="visible")
                action.wait_for(state="visible")
                assert action.count() == 1
                assert page.evaluate("() => window.scrollX === 0 && window.scrollY === 0")

                action_box = action.bounding_box()
                assert action_box is not None
                assert action_box["x"] >= -1
                assert action_box["x"] + action_box["width"] <= viewport[0] + 1
                assert action_box["y"] >= -1
                assert action_box["y"] + action_box["height"] <= viewport[1] + 1
                assert page.locator("[data-aidd-primary-action]:visible").count() <= 1
                assert page.evaluate(
                    "() => document.documentElement.scrollWidth <= window.innerWidth"
                )
                assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
                assert_rendered_geometry(page)
                browser_page.diagnostics.assert_clean()
