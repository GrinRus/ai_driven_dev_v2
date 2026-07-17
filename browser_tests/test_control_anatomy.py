from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


def test_journey_forms_share_one_native_control_anatomy(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main>
              <section class="onboarding-shell"><input id="onboarding" value="WI-001"></section>
              <section class="interview-loop-screen">
                <textarea id="question">Answer</textarea>
              </section>
              <section class="request-change-grid">
                <select id="intervention"><option>implement</option></select>
              </section>
              <section class="run-comparison"><input id="comparison" value="run-1"></section>
              <section class="next-flow-actions-grid">
                <button id="nextFlow">Create</button>
              </section>
              <label><input id="checkbox" type="checkbox"> Include evidence</label>
            </main>
            """,
            wait_until="networkidle",
        )

        styles = page.evaluate(
            """
            () => Object.fromEntries(
              ["onboarding", "question", "intervention", "comparison", "nextFlow", "checkbox"]
                .map((id) => {
                  const node = document.getElementById(id);
                  const style = getComputedStyle(node);
                  return [id, {
                    borderWidth: style.borderWidth,
                    borderRadius: style.borderRadius,
                    fontFamily: style.fontFamily,
                    fontSize: style.fontSize,
                    lineHeight: style.lineHeight,
                    height: node.getBoundingClientRect().height,
                    width: node.getBoundingClientRect().width,
                  }];
                })
            )
            """
        )

        text_controls = [
            styles[name]
            for name in ("onboarding", "question", "intervention", "comparison", "nextFlow")
        ]
        assert {control["borderWidth"] for control in text_controls} == {"1px"}
        assert {control["borderRadius"] for control in text_controls} == {"6px"}
        assert len({control["fontFamily"] for control in text_controls}) == 1
        assert {control["fontSize"] for control in text_controls} == {"12px"}
        assert len(
            {
                styles[name]["lineHeight"]
                for name in ("onboarding", "question", "comparison", "nextFlow")
            }
        ) == 1
        # Chromium retains its native `normal` computed line-height for select while
        # inheriting the same declared control typography.
        assert styles["intervention"]["lineHeight"] in {
            "normal",
            styles["onboarding"]["lineHeight"],
        }
        assert styles["checkbox"]["height"] == 18
        assert styles["checkbox"]["width"] == 18
        browser_page.diagnostics.assert_clean()


def test_focus_geometry_uses_shared_roles(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f'<link rel="stylesheet" href="{harness.url}operator.css"><input id="field">',
            wait_until="networkidle",
        )
        page.locator("#field").focus()

        focus = page.locator("#field").evaluate(
            """
            (node) => {
              const style = getComputedStyle(node);
              return {
                outlineWidth: style.outlineWidth,
                outlineOffset: style.outlineOffset,
                outlineColor: style.outlineColor,
                boxShadow: style.boxShadow,
              };
            }
            """
        )
        assert focus["outlineWidth"] == "3px"
        assert focus["outlineOffset"] == "2px"
        assert focus["outlineColor"] == "rgb(36, 95, 179)"
        assert focus["boxShadow"] != "none"
        browser_page.diagnostics.assert_clean()
