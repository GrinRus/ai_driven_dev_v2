from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_composite_controls_align_visual_and_accessibility_selection(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main>
              <div class="filter-row" role="group" aria-label="Log presentation">
                <button id="selected-filter" aria-pressed="true">Summary</button>
                <button id="idle-filter" aria-pressed="false">Raw</button>
              </div>
              <div class="setup-mode-grid" role="radiogroup" aria-label="Mode">
                <button class="setup-mode-card" role="radio" aria-checked="true">
                  <strong>Fresh run</strong>
                </button>
                <button class="setup-mode-card" role="radio" aria-checked="false">
                  <strong>Resume</strong>
                </button>
              </div>
              <button class="artifact-doc" aria-pressed="true">implementation-report.md</button>
              <button class="work-item-card" aria-current="true">WI-001</button>
            </main>
            """,
            wait_until="networkidle",
        )

        selected = page.locator("#selected-filter")
        idle = page.locator("#idle-filter")
        assert selected.get_attribute("aria-pressed") == "true"
        assert selected.evaluate("node => getComputedStyle(node).backgroundColor") != idle.evaluate(
            "node => getComputedStyle(node).backgroundColor"
        )
        assert page.get_by_role("radio", checked=True).count() == 1
        assert page.get_by_role("radio", checked=False).count() == 1
        assert page.locator('.artifact-doc[aria-pressed="true"]').count() == 1
        assert page.locator('.work-item-card[aria-current="true"]').count() == 1
        assert all(
            height >= 44
            for height in page.locator("button").evaluate_all(
                "nodes => nodes.map((node) => node.getBoundingClientRect().height)"
            )
        )
        browser_page.diagnostics.assert_clean()
