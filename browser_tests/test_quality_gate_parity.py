from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

from browser_tests.browser_harness import operator_browser_harness
from browser_tests.state_fixtures import build_browser_state_fixture


def _selector_url(base: str, selector: str, work_item: str, run_id: str) -> str:
    prefix = f"{selector}&" if selector else "?"
    return (
        f"{base}{prefix}mode=studio&work_item={work_item}"
        f"&run_id={run_id}&stage=implement"
    )


def test_implementation_and_review_qa_modes_share_canonical_read_models(
    tmp_path: Path,
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / "quality-gate-parity",
        "implementation-finalized",
    )
    snapshots: list[dict[str, object]] = []
    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness:
        for selector in ("", "?ui=legacy", "?ui=studio", "?ui=unknown"):
            with harness.open_page((1280, 900)) as browser_page:
                page = browser_page.page
                page.goto(
                    _selector_url(
                        harness.url,
                        selector,
                        fixture.work_item or "",
                        fixture.run_id or "",
                    ),
                    wait_until="networkidle",
                )
                snapshots.append(
                    page.evaluate(
                        "async () => {"
                        "  const query = '?run_id=run-browser';"
                        "  const [tasks, implementation, review, qa] = await Promise.all(["
                        "    fetch('/api/tasks' + query).then((item) => item.json()),"
                        "    fetch('/api/implement/evidence' + query).then((item) => item.json()),"
                        "    fetch('/api/review/findings' + query).then((item) => item.json()),"
                        "    fetch('/api/qa/verdict' + query).then((item) => item.json())"
                        "  ]);"
                        "  return {tasks, implementation, review, qa};"
                        "}"
                    )
                )
                browser_page.diagnostics.assert_clean()

    assert snapshots[1:] == snapshots[:1] * 3
