from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_legacy_stage_renderer_does_not_recreate_removed_shell_regions(
    tmp_path: Path,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <nav id="intentPhaseStepper" aria-label="Intent delivery phases"></nav>
            <script src="{harness.url}operator-api-state.js"></script>
            <script src="{harness.url}operator-shell-rendering.js"></script>
            """,
            wait_until="networkidle",
        )
        page.evaluate(
            """
            () => {
              state.activeStage = "idea";
              renderStageRail();
            }
            """
        )

        assert page.locator("#intentPhaseStepper").count() == 1
        assert page.locator(".stage-rail, #stageRail, .stage-card").count() == 0
        browser_page.diagnostics.assert_clean()
