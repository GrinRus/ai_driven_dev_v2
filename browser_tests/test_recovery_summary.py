from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


@pytest.mark.parametrize("viewport", ((320, 568), (390, 844)))
@pytest.mark.parametrize(
    ("title", "action"),
    (
        ("Runtime failure", "Retry stage"),
        ("Validation repair required", "Run Repair"),
        ("Repair budget exhausted", "Request Change"),
    ),
)
def test_mobile_recovery_prioritizes_failure_then_decision_then_evidence(
    tmp_path: Path,
    viewport: tuple[int, int],
    title: str,
    action: str,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <body class="recovery-mode">
              <main class="cockpit">
                <div class="recovery-workbench">
                  <section class="recovery-summary" data-recovery-summary="validation">
                    <header class="recovery-summary-header">
                      <h2>{title}</h2>
                      <p>Progression is closed until the selected recovery path completes.</p>
                    </header>
                    <div class="recovery-summary-failure" data-decisive-failure>
                      <span>First failure</span>
                      <strong>Required stage evidence is unavailable</strong>
                    </div>
                    <div class="recovery-summary-evidence" data-evidence-path="validator-report.md">
                      <span>Evidence</span><code>validator-report.md</code>
                      <button class="secondary">Open Evidence</button>
                    </div>
                    <div class="recovery-summary-primary" data-primary-recovery-slot>
                      <button>{action}</button>
                    </div>
                  </section>
                </div>
              </main>
            </body>
            """,
            wait_until="networkidle",
        )

        assert page.locator("[data-decisive-failure]").count() == 1
        assert page.locator("[data-evidence-path]").count() == 1
        assert page.locator("[data-primary-recovery-slot]").count() == 1
        positions = [
            page.locator(selector).evaluate("node => node.getBoundingClientRect().top")
            for selector in (
                "[data-decisive-failure]",
                "[data-primary-recovery-slot]",
                "[data-evidence-path]",
            )
        ]
        assert positions == sorted(positions)
        button = page.get_by_role("button", name=action).bounding_box()
        assert button is not None and button["height"] >= 44
        assert button["y"] + button["height"] <= viewport[1]
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert page.locator(".recovery-workbench").evaluate(
            "node => getComputedStyle(node).overflowY !== 'auto' "
            "&& getComputedStyle(node).overflowY !== 'scroll'"
        )
        browser_page.diagnostics.assert_clean()
