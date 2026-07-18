from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import operator_browser_harness

_CONTROL_MARKUP = """
<link rel="stylesheet" href="{origin}/operator.css">
<main>
  <button id="button">Continue</button>
  <label for="input">Work item</label>
  <input id="input" type="text" value="WI-001">
  <label for="select">Runtime</label>
  <select id="select"><option>generic-cli</option></select>
</main>
"""


def _control_metrics(page: Page) -> dict[str, dict[str, float | str]]:
    return page.evaluate(
        """
        () => Object.fromEntries(["button", "input", "select"].map((id) => {
          const node = document.getElementById(id);
          const style = getComputedStyle(node);
          return [id, {
            height: node.getBoundingClientRect().height,
            minHeight: style.minHeight,
            paddingInline: style.paddingInline,
          }];
        }))
        """
    )


@pytest.mark.parametrize(
    ("viewport", "expected_height"),
    [
        ((1280, 900), 32),
        ((1440, 900), 32),
        ((320, 568), 44),
        ((390, 844), 44),
    ],
)
def test_shared_density_tokens_control_rendered_form_anatomy(
    tmp_path: Path,
    viewport: tuple[int, int],
    expected_height: int,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.set_content(
            _CONTROL_MARKUP.format(origin=harness.url),
            wait_until="networkidle",
        )

        metrics = _control_metrics(page)

        for control in metrics.values():
            assert control["minHeight"] == f"{expected_height}px"
            assert float(control["height"]) >= expected_height
            assert control["paddingInline"] == "12px"
        browser_page.diagnostics.assert_clean()
