from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness


@pytest.mark.parametrize("viewport", [(1280, 900), (390, 844)])
def test_document_and_evidence_hierarchy_keeps_one_primary_frame(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main class="workbench-main" data-evidence-inspector="present">
              <section id="canvas"
                class="workbench-document-pane hierarchy-primary document-canvas">
                <h1>Implementation report</h1><p>Primary document content.</p>
              </section>
              <aside id="inspector"
                class="workbench-sidebar hierarchy-supporting evidence-inspector">
                <div class="surface-title evidence-inspector-title">Evidence Inspector</div>
                <section id="evidence" class="surface"><strong>Verification</strong></section>
              </aside>
            </main>
            """,
            wait_until="networkidle",
        )

        canvas = page.locator("#canvas").bounding_box()
        inspector = page.locator("#inspector").bounding_box()
        assert canvas is not None and inspector is not None
        if viewport[0] > 1120:
            assert canvas["width"] > inspector["width"]
            assert abs(canvas["y"] - inspector["y"]) < 1
        else:
            assert inspector["y"] >= canvas["y"] + canvas["height"]
        evidence_style = page.locator("#evidence").evaluate(
            """
            node => ({
              background: getComputedStyle(node).backgroundColor,
              borderTop: getComputedStyle(node).borderTopWidth,
            })
            """
        )
        assert evidence_style == {"background": "rgba(0, 0, 0, 0)", "borderTop": "1px"}
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        browser_page.diagnostics.assert_clean()


def test_absent_evidence_inspector_does_not_create_an_empty_peer_frame(tmp_path: Path) -> None:
    with sync_playwright() as playwright, operator_browser_harness(
        tmp_path,
        playwright,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        page.set_content(
            f"""
            <link rel="stylesheet" href="{harness.url}operator.css">
            <main class="workbench-main" data-evidence-inspector="absent">
              <section class="workbench-document-pane hierarchy-primary document-canvas">
                <h1>Plan</h1>
              </section>
            </main>
            """,
            wait_until="networkidle",
        )
        assert page.locator(".document-canvas").count() == 1
        assert page.locator(".evidence-inspector").count() == 0
        browser_page.diagnostics.assert_clean()
