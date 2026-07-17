from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


@pytest.mark.parametrize("state", ["blocking", "running", "ready", "terminal", "malformed"])
def test_inbox_item_states_keep_visible_status_and_touch_safe_action(
    tmp_path: Path,
    state: str,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <article class="inbox-item" data-inbox-item="item" data-state="{state}">
              <div class="inbox-item-copy">
                <span class="status-marker" data-status="pending">
                  <span class="status-marker-symbol" aria-hidden="true"></span>
                  <span>{state}</span>
                </span>
                <strong>Implementation needs attention</strong>
                <p>Open the service-owned destination.</p>
              </div>
              <div class="inbox-item-action"><button>Open</button></div>
            </article>
            """,
            wait_until="networkidle",
        )

        assert page.get_by_text(state, exact=True).is_visible()
        assert page.get_by_role("button", name="Open").bounding_box()["height"] >= 44
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()
