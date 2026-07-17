from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_all_stage_buttons_include_their_visible_label_in_the_accessible_name(
    tmp_path: Path,
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <span id="stageCounter"></span><nav id="stageRail"></nav>
            <script src="{harness.url}operator-api-state.js"></script>
            <script src="{harness.url}operator-shell-rendering.js"></script>
            """,
            wait_until="networkidle",
        )
        page.evaluate(
            """
            () => {
              state.activeStage = "idea";
              state.dashboard = {
                stages: STAGES.map((stage) => ({
                  stage,
                  title: stage === "review-spec" ? "Review Spec" :
                    stage[0].toUpperCase() + stage.slice(1),
                  subtitle: `Work on ${stage}`,
                  status: stage === "idea" ? "succeeded" : "pending",
                  attempt_count: stage === "idea" ? 1 : 0,
                })),
              };
              renderStageRail();
            }
            """
        )

        names = page.locator("[data-stage]").evaluate_all(
            r"""
            (buttons) => buttons.map((button) => {
              const visible = button.querySelector(".stage-name").textContent.trim();
              const name = button.getAttribute("aria-labelledby")
                .split(/\s+/)
                .map((id) => document.getElementById(id).textContent.trim())
                .join(" ");
              return {visible, name};
            })
            """
        )
        assert len(names) == 8
        assert all(item["visible"] in item["name"] for item in names)
        browser_page.diagnostics.assert_clean()
