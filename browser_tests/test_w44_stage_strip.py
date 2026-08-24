from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", ((768, 1024), (1280, 900), (1440, 900)))
def test_stage_strip_keeps_labels_readable_on_desktop_and_tablet(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"stage-strip-{viewport[0]}",
        "remediation-stale",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa&work_tab=documents&artifact=qa_report",
            wait_until="networkidle",
        )
        stepper = page.locator("[data-intent-phase-stepper]")
        stepper.wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const stepper = document.querySelector('[data-intent-phase-stepper]');
              const lists = [...document.querySelectorAll(
                '.canonical-stage-group .intent-phase-list'
              )];
              const buttons = [...document.querySelectorAll('.canonical-stage-step')];
              const rect = stepper.getBoundingClientRect();
              return {
                stepperHeight: rect.height,
                listColumns: lists.map((list) => getComputedStyle(list)
                  .gridTemplateColumns.split(' ').length),
                buttons: buttons.map((button) => {
                  const buttonRect = button.getBoundingClientRect();
                  const strong = button.querySelector('strong');
                  const small = button.querySelector('small');
                  return {
                    width: buttonRect.width,
                    right: buttonRect.right,
                    nameClipped: Boolean(strong && strong.scrollWidth > strong.clientWidth),
                    statusClipped: Boolean(small && small.scrollWidth > small.clientWidth),
                  };
                }),
                documentWidth: document.documentElement.scrollWidth,
              };
            }"""
        )

        expected_columns = 1 if viewport[0] == 768 else 2
        assert geometry["listColumns"] == [expected_columns] * 4
        assert geometry["stepperHeight"] <= 220
        assert all(button["width"] >= 100 for button in geometry["buttons"])
        assert all(button["right"] <= viewport[0] + 0.5 for button in geometry["buttons"])
        assert not any(
            button["nameClipped"] or button["statusClipped"]
            for button in geometry["buttons"]
        )
        assert geometry["documentWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", ((320, 568), (390, 844)))
def test_mobile_stage_strip_is_compact_and_keyboard_expandable(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"stage-strip-mobile-{viewport[0]}",
        "remediation-stale",
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?ui=studio&mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage=qa&work_tab=documents&artifact=qa_report",
            wait_until="networkidle",
        )
        toggle = page.locator("[data-stage-mobile-toggle]")
        toggle.wait_for(state="visible")
        groups = page.locator("#canonicalStageGroups")

        assert "QA" in toggle.inner_text()
        assert "8 of 8" in toggle.inner_text()
        assert toggle.get_attribute("aria-expanded") == "false"
        assert groups.evaluate("node => getComputedStyle(node).display") == "none"
        assert page.locator(".canonical-stage-step").count() == 8
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

        toggle.focus()
        page.keyboard.press("Enter")
        assert toggle.get_attribute("aria-expanded") == "true"
        assert toggle.locator("[data-stage-mobile-toggle-label]").inner_text() == "Hide stages"
        assert groups.evaluate("node => getComputedStyle(node).display") == "grid"
        assert page.locator(".canonical-stage-step").count() == 8
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert page.locator(".canonical-stage-step").evaluate_all(
            """nodes => nodes.every(node => {
                const rect = node.getBoundingClientRect();
                return rect.right <= window.innerWidth + 0.5 && rect.height >= 44;
            })"""
        )
        browser_page.diagnostics.assert_clean()
