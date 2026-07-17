from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_skip_link_and_detail_focus_return_are_deterministic(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <a id="skipToDecision" class="skip-link" href="#currentDecision">
              Skip to current decision
            </a>
            <button id="details" data-tab-shortcut="evidence">Open evidence</button>
            <div id="cockpitContent" tabindex="0">
              <section data-primary-slot><button>Run</button></section>
            </div>
            <button data-tab="work" aria-selected="true">Work</button>
            <script src="{harness.url}operator-focus.js"></script>
            """,
            wait_until="networkidle",
        )
        page.evaluate("syncCurrentDecisionTarget()")

        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") == "skipToDecision"
        page.keyboard.press("Enter")
        assert page.evaluate("document.activeElement.id") == "currentDecision"

        page.locator("#details").click()
        page.locator("#cockpitContent").evaluate(
            """
            node => {
              node.innerHTML = '<section data-primary-slot><button>Inspect</button></section>';
            }
            """
        )
        page.evaluate("syncCurrentDecisionTarget()")
        assert page.evaluate("document.activeElement.id") == "cockpitContent"
        page.keyboard.press("Escape")
        assert page.evaluate("document.activeElement.id") == "details"
        browser_page.diagnostics.assert_clean()
