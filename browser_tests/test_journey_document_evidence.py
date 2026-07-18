from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "document-evidence"


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


@pytest.mark.parametrize(
    "query",
    ("", "?ui=legacy", "?ui=studio", "?ui=unknown"),
)
def test_studio_workbench_ignores_retired_presentation_selector(
    tmp_path: Path,
    query: str,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / (query.removeprefix("?ui=") or "missing"),
        "remediation-stale",
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page((1280, 900)) as browser_page:
        page = browser_page.page
        selector = query.removeprefix("?")
        context = urlencode(
            {
                "mode": "studio",
                "work_item": fixture.work_item,
                "run_id": fixture.run_id,
                "stage": "qa",
            }
        )
        separator = "&" if selector else ""
        page.goto(
            f"{harness.url}?{selector}{separator}{context}", wait_until="networkidle"
        )
        page.locator(".active-studio").wait_for(state="visible")
        assert page.locator(".active-studio").count() == 1
        assert page.locator("#studioDocumentCanvas").count() == 1
        assert page.locator(".overview-grid").count() == 0
        browser_page.diagnostics.assert_clean()


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_document_canvas_and_evidence_inspector_preserve_safe_context(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"document-evidence-{viewport[0]}",
        "qa-decision",
    )

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        response = page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        assert response is not None and response.ok

        canvas = page.locator("#studioDocumentCanvas")
        canvas.locator('[data-document-canvas-mode="preview"]').wait_for(state="visible")
        assert "QA verdict: not-ready" in canvas.inner_text()
        _assert_rendered_gate(page, viewport)

        for mode in ("source", "diff", "preview"):
            canvas.locator(f'[data-artifact-mode="{mode}"]').click()
            canvas.locator(f'[data-document-canvas-mode="{mode}"]').wait_for(
                state="visible"
            )

        inspector = page.locator("#studioEvidenceInspector:visible")
        inspector.wait_for(state="visible")
        assert inspector.locator('[data-inspector-section="findings"]').count() == 1
        assert inspector.locator('[data-inspector-section="provenance"]').count() == 1
        assert inspector.locator(
            '[data-inspector-section="source-references"]'
        ).count() == 1
        assert inspector.locator('[data-inspector-section="related-artifacts"]').count() == 1
        inspector_text = inspector.inner_text()
        assert "validator-report" in inspector_text
        assert "Attempt 1" in inspector_text
        assert "required-section / document-contract" in inspector_text
        assert "missing" in inspector_text

        with page.expect_response(
            lambda item: urlsplit(item.url).path == "/api/stage/workbench"
            and parse_qs(urlsplit(item.url).query).get("key") == ["qa_report"]
        ) as selected_document:
            page.locator('[data-artifact-key="qa_report"]').click()
        assert selected_document.value.status == 200

        unsafe_query = urlencode(
            {
                "stage": "qa",
                "run_id": fixture.run_id,
                "key": "../../run-manifest.json",
            }
        )
        unsafe_response = page.request.get(
            f"{harness.url}api/stage/workbench?{unsafe_query}"
        )
        assert unsafe_response.status == 400
        assert "is not available" in unsafe_response.text()
        assert "config_snapshot" not in unsafe_response.text()

        page.reload(wait_until="networkidle")
        page.locator(
            '#artifactViewer [data-artifact-mode="preview"][aria-pressed="true"]'
        ).wait_for(state="visible")
        assert parse_qs(urlsplit(page.url).query).get("artifact") == ["qa_report"]

        page.go_back(wait_until="networkidle")
        page.evaluate("() => window.aiddRouteRestore || Promise.resolve()")
        canvas.locator('[data-document-canvas-mode="preview"]').wait_for(state="visible")

        page.locator(
            '[data-studio-observation="durable-attempt"] [data-tab-shortcut="logs"]'
        ).click()
        page.locator("#cockpitContent").get_by_text(
            "Saved runtime.log", exact=False
        ).first.wait_for(state="visible")
        assert "qa evidence collected" in page.locator("#cockpitContent").inner_text()

        page.go_back(wait_until="networkidle")
        page.evaluate("() => window.aiddRouteRestore || Promise.resolve()")
        canvas.locator('[data-document-canvas-mode="preview"]').wait_for(state="visible")
        _assert_rendered_gate(page, viewport)

        workbench_queries = [
            parse_qs(urlsplit(url).query)
            for url, status in browser_page.diagnostics.http_statuses
            if urlsplit(url).path == "/api/stage/workbench" and status == 200
        ]
        selected_keys = {
            key
            for query in workbench_queries
            for key in query.get("key", [])
        }
        assert selected_keys <= {"qa_report"}
        browser_page.diagnostics.assert_clean()
