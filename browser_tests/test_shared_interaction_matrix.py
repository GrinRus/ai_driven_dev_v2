from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry

_STATES = (
    "loading",
    "empty",
    "partial",
    "error",
    "disabled",
    "selected",
    "pending",
    "conflict",
    "success",
    "offline",
    "unavailable",
    "reconnecting",
    "permission-denied",
    "focus",
    "keyboard",
)


def _matrix_markup(origin: str) -> str:
    regions = "".join(
        f"""
          <section id="state-{state}" data-interaction-region data-state="{state}"
                 data-aidd-clipping-check role="status" aria-live="polite"
                 aria-busy="{
                     'true' if state in {'loading', 'pending', 'reconnecting'} else 'false'
                 }">
          <span class="status-marker" data-status="pending">
            <span class="status-marker-symbol" aria-hidden="true"></span>
            <span data-status-text>{state} state</span>
          </span>
          <h2>{state.title()} state</h2>
          <p>The service-owned consequence remains visible.</p>
          <button data-primary-action type="button">Continue from {state}</button>
        </section>
        """
        for state in _STATES
    )
    return f"""
      <link rel="stylesheet" href="{origin}operator.css">
      <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; }}
        main {{ display: grid; gap: 12px; max-width: 100%; padding: 12px; }}
        [data-interaction-region] {{
          display: grid; gap: 8px; min-width: 0; max-width: 100%; padding: 12px;
        }}
        [data-primary-action] {{ min-height: 44px; min-width: 44px; }}
      </style>
      <main aria-label="Shared interaction state matrix">{regions}</main>
    """


def test_shared_interaction_matrix_keeps_semantics_geometry_and_focus(
    tmp_path: Path,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(_matrix_markup(harness.url), wait_until="networkidle")

        assert_accessible_render(page)
        assert_rendered_geometry(page)
        assert page.locator("[data-interaction-region]").count() == len(_STATES)

        for state in _STATES:
            region = page.locator(f"#state-{state}")
            assert region.locator("[data-status-text]").inner_text() == f"{state} state"
            assert region.locator("[data-primary-action]").count() == 1
            assert region.locator("[data-primary-action]").get_attribute("aria-label") is None
            assert region.locator("[data-primary-action]").inner_text()

        selected_button = page.locator("#state-selected [data-primary-action]")
        selected_button.focus()
        page.locator("#state-selected [data-status-text]").evaluate(
            "node => { node.textContent = 'selected state updated'; }"
        )
        assert page.evaluate(
            "document.activeElement.matches('#state-selected [data-primary-action]')"
        )
        browser_page.diagnostics.assert_clean()


def test_shared_interaction_matrix_rejects_duplicate_primary_and_color_only_status(
    tmp_path: Path,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main data-interaction-region>
              <span class="status-marker" data-status="error">
                <span class="status-marker-symbol" aria-hidden="true"></span>
              </span>
              <button data-primary-action type="button">Retry</button>
              <button data-primary-action type="button">Cancel</button>
            </main>
            """,
            wait_until="networkidle",
        )
        assert page.locator("[data-interaction-region] [data-primary-action]").count() == 2
        assert page.locator("[data-interaction-region] [data-status-text]").count() == 0
        browser_page.diagnostics.assert_clean()
