from __future__ import annotations

import json
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def test_studio_history_selects_durable_frame_and_returns_to_live(tmp_path: Path) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "history-filmstrip",
        "implementation-finalization-failed",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=history&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="networkidle",
        )
        history = page.locator("[data-studio-history]")
        history.wait_for(state="visible")
        comparison = page.locator("[data-studio-run-comparison]")
        comparison.wait_for(state="visible")
        assert "retained-evidence comparison" in comparison.inner_text().lower()
        frames = history.locator("[data-history-frame]")
        assert frames.count() >= 3
        assert "TL-1 · attempt 1" in history.inner_text()
        assert "Aggregate finalization · attempt 1" in history.inner_text()

        frames.first.click()
        page.wait_for_function(
            "document.querySelector('[data-studio-history]')?.dataset.historyAutoFollow"
            " === 'false'"
        )
        assert history.get_attribute("data-history-auto-follow") == "false"
        assert history.locator("[data-history-selection]").get_attribute(
            "data-history-selection"
        ) == frames.first.get_attribute("data-history-frame")
        assert "active runtime is not stopped" in history.inner_text()
        return_live = history.get_by_role("button", name="Return to live")
        assert return_live.is_enabled()
        return_live.click()
        page.wait_for_function(
            "document.querySelector('[data-studio-history]')?.dataset.historyAutoFollow"
            " === 'true'"
        )
        assert history.get_attribute("data-history-auto-follow") == "true"
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((320, 568), (390, 844)))
def test_studio_history_is_a_vertical_mobile_drill_down(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"history-mobile-{viewport[0]}",
        "implementation-finalization-failed",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=history&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=implement",
            wait_until="networkidle",
        )
        history = page.locator("[data-studio-history]")
        history.wait_for(state="visible")
        measurements = history.locator(".history-filmstrip-frames").evaluate(
            """element => ({
              display: getComputedStyle(element).display,
              overflowX: getComputedStyle(element).overflowX,
              frameWidths: Array.from(element.children)
                .map(child => child.getBoundingClientRect().width),
              width: element.getBoundingClientRect().width
            })"""
        )
        assert measurements["display"] == "grid"
        assert measurements["overflowX"] == "visible"
        assert all(width <= measurements["width"] for width in measurements["frameWidths"])
        overflow = page.evaluate(
            """() => ({
              fits: document.documentElement.scrollWidth <= window.innerWidth,
              documentWidth: document.documentElement.scrollWidth,
              viewportWidth: window.innerWidth,
              offenders: Array.from(document.querySelectorAll('body *'))
                .map(element => ({
                  selector: element.id || element.className || element.tagName,
                  left: element.getBoundingClientRect().left,
                  right: element.getBoundingClientRect().right,
                  width: element.getBoundingClientRect().width,
                  scrollWidth: element.scrollWidth
                }))
                .filter(item => (
                  item.right > window.innerWidth + 0.5
                  || item.left < -0.5
                  || item.scrollWidth > Math.ceil(item.width) + 1
                ))
                .slice(0, 30)
            })"""
        )
        assert overflow["fits"], json.dumps(overflow, indent=2)
        return_live = history.get_by_role("button", name="Return to live")
        return_box = return_live.bounding_box()
        assert return_box is not None and return_box["height"] >= 44
        browser_page.diagnostics.assert_clean()
