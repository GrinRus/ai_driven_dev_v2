from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_recovery_summary_prioritizes_one_failure_evidence_and_action(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <section class="recovery-summary" data-recovery-summary="validation">
              <header class="recovery-summary-header">
                <h2>Validation repair required</h2>
                <p>Progression is closed.</p>
              </header>
              <div class="recovery-summary-failure" data-decisive-failure>
                <span>First failure</span><strong>Required section is missing</strong>
              </div>
              <div class="recovery-summary-evidence" data-evidence-path="validator-report.md">
                <span>Evidence</span><code>validator-report.md</code>
              </div>
              <div class="recovery-summary-primary" data-primary-recovery-slot>
                <button>Run Repair</button>
              </div>
            </section>
            """,
            wait_until="networkidle",
        )

        assert page.locator("[data-decisive-failure]").count() == 1
        assert page.locator("[data-evidence-path]").count() == 1
        assert page.locator("[data-primary-recovery-slot]").count() == 1
        button = page.get_by_role("button", name="Run Repair").bounding_box()
        assert button is not None and button["height"] >= 44
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()
