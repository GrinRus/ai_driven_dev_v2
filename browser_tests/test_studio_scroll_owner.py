from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((1280, 900), (1440, 900)))
def test_studio_shell_is_the_only_desktop_content_scroll_owner(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"running-{viewport[0]}", "running")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(harness.url, wait_until="networkidle")
        assert response is not None and response.ok
        page.locator("#cockpitContent").evaluate(
            "element => { const filler = document.createElement('div'); "
            "filler.style.height = '1800px'; element.append(filler); }"
        )

        result = page.evaluate(
            """
            () => {
              const shell = document.querySelector('[data-aidd-scroll-owner="studio"]');
              const topLevel = ['.stage-rail', '.cockpit', '.right-sidebar']
                .map((selector) => document.querySelector(selector));
              return {
                shellOverflow: getComputedStyle(shell).overflowY,
                shellScrollable: shell.scrollHeight > shell.clientHeight,
                childOverflow: topLevel.map((element) => getComputedStyle(element).overflowY),
                topbarPosition: getComputedStyle(document.querySelector('.topbar')).position,
              };
            }
            """
        )
        assert result == {
            "shellOverflow": "auto",
            "shellScrollable": True,
            "childOverflow": ["visible", "visible", "visible"],
            "topbarPosition": "sticky",
        }
        assert_rendered_geometry(page)
        browser_page.diagnostics.assert_clean()
