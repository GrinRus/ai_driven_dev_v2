from __future__ import annotations

from playwright.sync_api import sync_playwright

from browser_tests.rendered_assertions import (
    RenderedAssertionError,
    assert_accessible_render,
)


def test_valid_render_passes_accessibility_gate() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(
                """
                <style>
                  body { background: #fff; color: #111; }
                  button, input { box-sizing: border-box; min-width: 44px; min-height: 44px; }
                  #motion { transition: opacity 200ms; }
                  @media (prefers-reduced-motion: reduce) {
                    #motion { transition-duration: 0s; }
                  }
                </style>
                <main>
                  <button id="primary" data-aidd-focus-role="primary">Run workflow</button>
                  <label for="request">Request</label>
                  <input id="request" value="Bounded change">
                  <button id="maintenance" data-aidd-focus-role="maintenance">Refresh</button>
                  <p id="motion">Ready for operator input.</p>
                </main>
                """
            )
            assert_accessible_render(page)
        finally:
            browser.close()


def test_invalid_render_reports_every_accessibility_rule_with_measurement() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(
                """
                <style>
                  body { background: #fff; color: #111; }
                  #lowContrast { color: #aaa; }
                  #tiny { width: 20px; height: 20px; padding: 0; }
                  #motion { transition: transform 2s; }
                </style>
                <main>
                  <button id="maintenance" data-aidd-focus-role="maintenance">Refresh</button>
                  <button id="unnamed" aria-label=""></button>
                  <input id="unlabelled">
                  <button id="primary" data-aidd-focus-role="primary">Run workflow</button>
                  <button id="tiny">Tiny</button>
                  <p id="lowContrast">Low contrast evidence.</p>
                  <div id="motion">Animated status.</div>
                </main>
                """
            )
            try:
                assert_accessible_render(page)
            except RenderedAssertionError as exc:
                rules = {violation.rule for violation in exc.violations}
                assert rules == {
                    "accessible-name",
                    "label",
                    "focus-order",
                    "contrast",
                    "target-size",
                    "reduced-motion",
                }
                assert all(violation.selector for violation in exc.violations)
                assert all(violation.measured for violation in exc.violations)
                assert "#lowContrast measured" in str(exc)
                assert "#tiny measured" in str(exc)
            else:
                raise AssertionError("invalid rendered fixture unexpectedly passed")
        finally:
            browser.close()
