from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
@pytest.mark.parametrize(
    ("fixture_state", "query", "decision_selector"),
    [
        ("no-run", "?ui=studio", "#globalNextActionButton"),
        ("running", "?ui=studio", "#globalNextActionButton"),
        ("no-run", "?ui=studio", ".studio-inbox [data-inbox-action]"),
    ],
)
def test_mobile_primary_decision_is_in_the_initial_viewport(
    tmp_path: Path,
    viewport: tuple[int, int],
    fixture_state: str,
    query: str,
    decision_selector: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"{fixture_state}-{viewport[0]}",
        fixture_state,
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}{query}", wait_until="networkidle")
        if decision_selector.startswith(".studio-inbox"):
            page.locator('[data-tab-shortcut="project-home"]').first.evaluate(
                "node => node.click()"
            )
        decision = page.locator(decision_selector).first
        decision.wait_for(state="visible", timeout=5_000)
        bounds = decision.bounding_box()

        assert bounds is not None
        assert bounds["y"] >= page.locator(".topbar").bounding_box()["height"]
        assert bounds["y"] + bounds["height"] <= viewport[1]
        assert page.locator(".right-sidebar").bounding_box()["y"] >= (
            bounds["y"] + bounds["height"]
        )
        browser_page.diagnostics.assert_clean()
