from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_guided_step_anatomy_is_complete_and_touch_safe(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <section class="guided-step" data-guided-step="runtime" data-state="current">
              <header class="guided-step-header">
                <h2>Choose runtime</h2>
                <p>Select the execution command.</p>
              </header>
              <div class="guided-step-inputs">
                <div class="guided-step-field">
                  <label for="runtime">Runtime</label>
                  <select id="runtime"><option>Generic CLI</option></select>
                </div>
              </div>
              <div class="guided-step-actions">
                <button class="secondary">Back</button><button>Continue</button>
              </div>
              <details class="guided-step-advanced"><summary>Advanced</summary></details>
            </section>
            """,
            wait_until="networkidle",
        )

        assert page.get_by_label("Runtime").is_visible()
        assert page.get_by_text("Select the execution command.").is_visible()
        assert page.get_by_text("Advanced", exact=True).is_visible()
        heights = page.locator("button, select").evaluate_all(
            "nodes => nodes.map((node) => node.getBoundingClientRect().height)"
        )
        assert all(height >= 44 for height in heights)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()
