from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
def test_mobile_studio_header_is_compact_and_keeps_maintenance_after_decision(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"mobile-{viewport[0]}", "no-run")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_timeout(100)

        geometry = page.evaluate(
            """() => {
              const bounds = (selector) => {
                const rect = document.querySelector(selector).getBoundingClientRect();
                return {top: rect.top, right: rect.right, bottom: rect.bottom, height: rect.height};
              };
              return {
                header: bounds('.topbar'),
                maintenance: bounds('.maintenance-overflow summary'),
                tabs: bounds('.tabs'),
                decision: bounds('.global-next-action-strip'),
              };
            }"""
        )
        assert geometry["header"]["height"] <= 80
        assert geometry["maintenance"]["top"] >= geometry["header"]["top"]
        assert geometry["maintenance"]["bottom"] <= geometry["header"]["bottom"]
        assert geometry["tabs"]["top"] >= geometry["header"]["bottom"]
        assert geometry["decision"]["top"] >= geometry["header"]["bottom"]

        primary_precedes_maintenance = page.evaluate(
            """() => Boolean(
              document.querySelector('#globalNextActionButton').compareDocumentPosition(
                document.querySelector('[data-aidd-focus-role="maintenance"]')
              ) & Node.DOCUMENT_POSITION_FOLLOWING
            )"""
        )
        assert primary_precedes_maintenance
        browser_page.diagnostics.assert_clean()
