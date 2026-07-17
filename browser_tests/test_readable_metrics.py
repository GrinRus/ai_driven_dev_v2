from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import collect_accessibility_violations


def test_microcopy_contrast_minimums_and_tabular_metrics_are_rendered(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main>
              <section class="surface"><span class="muted">Supporting evidence</span></section>
              <section class="state-surface" data-state="unavailable">
                <div class="state-surface-copy"><p>Runtime is unavailable.</p></div>
              </section>
              <span class="counter">08/12</span>
              <span class="small-badge">12 attempts</span>
              <div class="metric"><span>Elapsed</span><strong>01:29</strong></div>
            </main>
            """,
            wait_until="networkidle",
        )

        violations = collect_accessibility_violations(page, target_size=0)
        assert [item for item in violations if item.rule == "contrast"] == []
        font_sizes = page.locator(".muted, .state-surface-copy p, .small-badge").evaluate_all(
            "nodes => nodes.map((node) => Number.parseFloat(getComputedStyle(node).fontSize))"
        )
        assert all(size >= 12 for size in font_sizes)
        numeric = page.locator(".counter, .small-badge, .metric strong").evaluate_all(
            "nodes => nodes.map((node) => getComputedStyle(node).fontVariantNumeric)"
        )
        assert numeric == ["tabular-nums", "tabular-nums", "tabular-nums"]
        browser_page.diagnostics.assert_clean()
