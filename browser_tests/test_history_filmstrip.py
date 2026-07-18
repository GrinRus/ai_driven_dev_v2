from __future__ import annotations

from pathlib import Path

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
