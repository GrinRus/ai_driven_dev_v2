from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
def test_mobile_studio_header_is_compact_and_keeps_maintenance_after_decision(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(tmp_path / f"mobile-{viewport[0]}", "no-run")
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        settings = page.locator("#runtimeSettings")
        if settings.get_attribute("open") is None:
            page.locator("#runtimeSettings > summary").click()
        page.locator("#runtimeSelect").select_option("generic-cli")
        page.wait_for_timeout(100)

        geometry = page.evaluate(
            """() => {
              const bounds = (selector) => {
                const rect = document.querySelector(selector).getBoundingClientRect();
                return {top: rect.top, right: rect.right, bottom: rect.bottom, height: rect.height};
              };
              return {
                header: bounds('.topbar'),
                maintenance: bounds('#intentTechnicalDetails > summary'),
                phases: bounds('#intentPhaseStepper'),
                decision: bounds('#currentDecision, #intentDecisionSurface'),
                technical: bounds('#intentTechnicalDetails'),
              };
            }"""
        )
        assert geometry["header"]["height"] <= 80
        assert geometry["maintenance"]["top"] >= geometry["header"]["top"]
        assert geometry["maintenance"]["bottom"] >= geometry["header"]["bottom"]
        assert geometry["phases"]["top"] >= geometry["header"]["bottom"]
        assert geometry["decision"]["top"] >= geometry["header"]["bottom"]
        assert geometry["technical"]["top"] >= geometry["decision"]["bottom"]

        primary_precedes_maintenance = page.evaluate(
            """() => Boolean(
              document.querySelector(
                '#currentDecision, #globalNextActionButton'
              ).compareDocumentPosition(
                document.querySelector('[data-aidd-focus-role="technical-details"]')
              ) & Node.DOCUMENT_POSITION_FOLLOWING
            )"""
        )
        assert primary_precedes_maintenance
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("fixture_state", ["runtime-launch-failure", "validation-repair-exhausted"])
@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
def test_mobile_recovery_header_keeps_identity_and_decision_surface(
    tmp_path: Path,
    fixture_state: str,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"{fixture_state}-{viewport[0]}",
        fixture_state,
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="domcontentloaded")
        page.wait_for_function("typeof renderCockpit === 'function'")
        page.evaluate(
            "async () => {"
            "  activateTab('recovery', {historyMode: 'replace'});"
            "  await renderCockpit();"
            "}"
        )
        page.locator("[data-recovery-summary]").wait_for(state="visible")

        geometry = page.evaluate(
            """() => {
              const topbar = document.querySelector('.topbar').getBoundingClientRect();
              const brand = document.querySelector('.brand').getBoundingClientRect();
              const maintenance = document.querySelector(
                '#intentTechnicalDetails > summary'
              ).getBoundingClientRect();
              return {
                header: {top: topbar.top, height: topbar.height, bottom: topbar.bottom},
                brand: {
                  height: brand.height,
                  visible: getComputedStyle(document.querySelector('.brand')).display !== 'none',
                },
                maintenance: {
                  top: maintenance.top,
                  bottom: maintenance.bottom,
                  height: maintenance.height,
                },
                scrollWidth: document.documentElement.scrollWidth,
              };
            }"""
        )

        assert 56 <= geometry["header"]["height"] <= 80
        assert geometry["brand"]["visible"]
        assert geometry["brand"]["height"] > 0
        assert geometry["maintenance"]["height"] >= 44
        assert geometry["maintenance"]["top"] >= geometry["header"]["top"]
        assert geometry["maintenance"]["height"] >= 44
        assert geometry["scrollWidth"] <= viewport[0]
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("fixture_state, stage", [
    ("runtime-launch-failure", "idea"),
    ("validation-repair-exhausted", "plan"),
])
@pytest.mark.parametrize("viewport", [(320, 568), (390, 844)])
def test_mobile_recovery_route_exposes_current_work_item_identity(
    tmp_path: Path,
    fixture_state: str,
    stage: str,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"route-{fixture_state}-{viewport[0]}",
        fixture_state,
    )
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(
            f"{harness.url}?mode=studio&work_item={fixture.work_item}"
            f"&run_id={fixture.run_id}&stage={stage}&view=recovery",
            wait_until="domcontentloaded",
        )
        surface = "[data-recovery-summary]" if stage == "idea" else ".validation-repair-center"
        page.locator(surface).wait_for(state="visible")

        work_item_context = page.locator("#topContextIntent")
        work_item_context.wait_for(state="visible")
        assert work_item_context.inner_text() == fixture.work_item
        context_box = work_item_context.bounding_box()
        inbox_box = page.locator("#projectInboxButton").bounding_box()
        overflow_box = page.locator("#runtimeSettings > summary").bounding_box()
        assert context_box is not None and context_box["width"] > 0
        assert inbox_box is not None and inbox_box["width"] >= 44
        assert overflow_box is not None and overflow_box["width"] >= 44
        assert page.evaluate(
            """() => getComputedStyle(
              document.querySelector('#projectInboxButton'), '::before'
            ).content"""
        ) == '"←"'
        assert page.evaluate(
            """() => getComputedStyle(
              document.querySelector('#runtimeSettings > summary'), '::before'
            ).content"""
        ) == '"⋮"'
        assert page.evaluate(
            "() => document.documentElement.scrollWidth <= window.innerWidth"
        )
        browser_page.diagnostics.assert_clean()
