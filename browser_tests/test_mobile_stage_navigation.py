from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
def test_mobile_stage_navigation_preserves_identity_status_and_bounds(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"stages-{viewport[0]}", "running")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        cards = page.locator("#stageRail .stage-card")
        assert cards.count() == 8
        measurements = cards.evaluate_all(
            """nodes => nodes.map((card) => {
              const name = card.querySelector('.stage-name');
              const status = card.querySelector('.sr-only');
              const cardRect = card.getBoundingClientRect();
              const nameRect = name.getBoundingClientRect();
              return {
                name: name.textContent.trim(),
                status: status.textContent.trim(),
                labelledBy: card.getAttribute('aria-labelledby'),
                height: cardRect.height,
                overflow: card.scrollWidth > card.clientWidth,
                nameClipped: nameRect.left < cardRect.left || nameRect.right > cardRect.right,
              };
            })"""
        )
        assert all(item["name"] and item["status"] for item in measurements)
        assert all(item["labelledBy"] for item in measurements)
        assert all(item["height"] >= 44 for item in measurements)
        assert not any(item["overflow"] or item["nameClipped"] for item in measurements)
        browser_page.diagnostics.assert_clean()
