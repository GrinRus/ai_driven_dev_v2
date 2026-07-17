from __future__ import annotations

import pytest
from playwright.sync_api import sync_playwright

from browser_tests.rendered_assertions import RenderedAssertionError
from browser_tests.rendered_geometry import assert_rendered_geometry

_INVALID_GEOMETRY: tuple[tuple[str, str], ...] = (
    (
        "sticky-header",
        "<header id='badHeader' data-aidd-sticky-header style='height: 120px'>Header</header>",
    ),
    (
        "primary-action",
        "<div style='height: 900px'></div>"
        "<button id='offscreenCta' data-aidd-primary-action>Run</button>",
    ),
    (
        "clipping",
        "<div id='clippedLabel' data-aidd-clipping-check "
        "style='width: 80px; overflow: hidden; white-space: nowrap'>"
        "A deliberately clipped primary label</div>",
    ),
    (
        "overlap",
        "<div style='position: relative'>"
        "<div id='surfaceA' data-aidd-overlap-check "
        "style='position:absolute;width:100px;height:60px'>A</div>"
        "<div id='surfaceB' data-aidd-overlap-check "
        "style='position:absolute;left:50px;width:100px;height:60px'>B</div>"
        "</div>",
    ),
    (
        "nested-scroll",
        "<div id='outerScroll' style='height:100px;overflow-y:auto'>"
        "<div style='height:220px'>"
        "<div id='innerScroll' style='height:60px;overflow-y:auto'>"
        "<div style='height:180px'>Nested</div>"
        "</div></div></div>",
    ),
    (
        "horizontal-overflow",
        "<div id='wideSurface' style='width:700px'>Too wide</div>",
    ),
)


def test_valid_render_passes_geometry_gate() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(
                """
                <style>* { box-sizing: border-box; } body { margin: 0; }</style>
                <header data-aidd-sticky-header style="height: 64px">Context</header>
                <main style="max-width: 100%">
                  <button data-aidd-primary-action>Run workflow</button>
                  <div data-aidd-clipping-check>Complete label</div>
                  <section data-aidd-overlap-check>Document</section>
                  <aside data-aidd-overlap-check>Evidence</aside>
                </main>
                """
            )
            assert_rendered_geometry(page)
        finally:
            browser.close()


@pytest.mark.parametrize(("expected_rule", "markup"), _INVALID_GEOMETRY)
def test_invalid_render_reports_expected_geometry_rule(
    expected_rule: str,
    markup: str,
) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.set_content(f"<style>* {{ box-sizing: border-box; }}</style>{markup}")
            with pytest.raises(RenderedAssertionError) as failure:
                assert_rendered_geometry(page)
            matching = [
                violation
                for violation in failure.value.violations
                if violation.rule == expected_rule
            ]
            assert matching, str(failure.value)
            assert matching[0].selector
            assert matching[0].measured
        finally:
            browser.close()
