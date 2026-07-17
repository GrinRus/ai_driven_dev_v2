from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import operator_browser_harness

_STATES = """
<link rel="stylesheet" href="{origin}operator.css">
<main>
  <button id="primary">Run</button>
  <button id="disabled" disabled>Blocked</button>
  <button id="selected" class="secondary" aria-pressed="true">Selected</button>
  <button id="loading" aria-busy="true">Loading</button>
  <label for="invalid">Work item</label>
  <input id="invalid" aria-invalid="true" value="../bad">
</main>
"""


def _style(page: Page, selector: str) -> dict[str, str | float]:
    return page.locator(selector).evaluate(
        """
        (node) => {
          const style = getComputedStyle(node);
          return {
            background: style.backgroundColor,
            border: style.borderColor,
            color: style.color,
            cursor: style.cursor,
            opacity: Number(style.opacity),
            outline: style.outlineStyle,
            transform: style.transform,
            height: node.getBoundingClientRect().height,
          };
        }
        """
    )


def test_shared_control_states_cover_pointer_keyboard_and_durable_state(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(_STATES.format(origin=harness.url), wait_until="networkidle")

        page.locator("#primary").hover()
        page.wait_for_timeout(200)
        assert _style(page, "#primary")["background"] == "rgb(11, 94, 96)"

        page.keyboard.press("Tab")
        assert _style(page, "#primary")["outline"] == "solid"

        box = page.locator("#primary").bounding_box()
        assert box is not None
        page.mouse.move(box["x"] + 2, box["y"] + 2)
        page.mouse.down()
        assert _style(page, "#primary")["transform"] != "none"
        page.mouse.up()

        disabled = _style(page, "#disabled")
        assert disabled["cursor"] == "not-allowed"
        assert float(disabled["opacity"]) < 1
        assert _style(page, "#invalid")["border"] == "rgb(180, 35, 42)"
        assert _style(page, "#loading")["cursor"] == "progress"
        assert float(_style(page, "#loading")["opacity"]) < 1
        assert _style(page, "#selected")["background"] == "rgb(234, 245, 243)"
        browser_page.diagnostics.assert_clean()


def test_every_button_state_retains_touch_density(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((390, 844)) as browser_page:
        page = browser_page.page
        page.set_content(_STATES.format(origin=harness.url), wait_until="networkidle")

        heights = page.locator("button").evaluate_all(
            "nodes => nodes.map((node) => node.getBoundingClientRect().height)"
        )
        assert all(height >= 44 for height in heights)
        browser_page.diagnostics.assert_clean()
