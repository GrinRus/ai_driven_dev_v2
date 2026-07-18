from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, sync_playwright

from browser_tests.browser_harness import VIEWPORTS, operator_browser_harness
from browser_tests.rendered_assertions import assert_accessible_render
from browser_tests.rendered_geometry import assert_rendered_geometry
from browser_tests.state_fixtures import build_browser_state_fixture

JOURNEY_ID = "approval-recovery"

_ACTIONS_BY_WIDTH = {
    320: "allow_once",
    390: "deny",
    768: "cancel",
    1280: "allow_for_session",
    1440: "conflict",
}


def _configure_live_conformance(project_root: Path) -> None:
    project_root.joinpath("aidd.example.toml").write_text(
        "[workspace]\n"
        'root = ".aidd"\n\n'
        "[runtime.generic_cli]\n"
        'command = "generic-cli-live-conformance"\n'
        'mode = "adapter-flags"\n'
        'permission_policy = "brokered"\n'
        'interaction_mode = "live"\n'
        'auto_approval_preset = "broad"\n\n'
        "[logging]\n"
        'mode = "both"\n\n'
        "[repair]\n"
        "max_attempts = 2\n",
        encoding="utf-8",
    )


def _assert_rendered_gate(page: Page, viewport: tuple[int, int]) -> None:
    assert_accessible_render(page, target_size=44 if viewport[0] <= 760 else 32)
    assert_rendered_geometry(page)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_runtime_approval_preserves_scope_confirmation_and_durable_winner(
    tmp_path: Path,
    viewport: tuple[int, int],
) -> None:
    fixture = build_browser_state_fixture(
        tmp_path / f"approval-recovery-{viewport[0]}",
        "no-run",
    )
    _configure_live_conformance(fixture.project_root)
    action = _ACTIONS_BY_WIDTH[viewport[0]]

    with sync_playwright() as playwright, operator_browser_harness(
        fixture.project_root,
        playwright,
        work_item=fixture.work_item,
    ) as harness, harness.open_page(viewport) as browser_page:
        page = browser_page.page
        page.goto(f"{harness.url}?ui=studio", wait_until="networkidle")
        job = page.evaluate(
            """async () => {
              const launched = await postJson('/api/stage/run', {
                stage: 'idea', runtime: 'generic-cli', log_follow: true
              });
              await startJobPolling(launched);
              return launched;
            }"""
        )
        job_id = job["job_id"]
        page.wait_for_function(
            "eval('state.activeJobStatus?.status') === 'waiting-for-operator'",
            timeout=10_000,
        )
        page.evaluate("renderApprovals()")
        card = page.locator('[data-approval-request-id]').first
        card.wait_for(state="visible")
        request_id = card.get_attribute("data-approval-request-id")
        assert request_id
        assert card.get_attribute("data-approval-status") == "pending"
        assert card.get_attribute("data-approval-risk") == "high"
        assert card.get_attribute("data-approval-breadth") == "single-request"
        assert "npm install" in card.inner_text()
        assert "idea" in card.inner_text()
        _assert_rendered_gate(page, viewport)

        reason = card.locator(f'[data-approval-reason="{request_id}"]')
        reason.fill(f"provider-free {action} decision")
        decision_posts: list[str] = []
        page.on(
            "request",
            lambda item: decision_posts.append(item.url)
            if item.method == "POST" and item.url.endswith("/decision")
            else None,
        )

        if action == "allow_for_session":
            card.locator('[data-operator-action="allow_for_session"]').click()
            confirmation = card.locator("[data-approval-session-confirmation]")
            assert confirmation.is_visible()
            assert decision_posts == []
            assert "all matching requests" in confirmation.inner_text()
            confirmation.locator("[data-approval-confirm-session]").click()
            expected_winner = "allow_for_session"
        elif action == "conflict":
            outcomes = page.evaluate(
                """async ({jobId, requestId}) => {
                  const path = `/api/jobs/${jobId}/operator-requests/${requestId}/decision`;
                  const responses = await Promise.all([
                    fetch(path, {
                      method: 'POST', headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify({action: 'allow_once', reason: 'first'})
                    }),
                    fetch(path, {
                      method: 'POST', headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify({action: 'deny', reason: 'opposite'})
                    })
                  ]);
                  return Promise.all(responses.map(async response => ({
                    status: response.status,
                    body: await response.json()
                  })));
                }""",
                {"jobId": job_id, "requestId": request_id},
            )
            assert sorted(item["status"] for item in outcomes) == [200, 409]
            winner_payload = next(item["body"] for item in outcomes if item["status"] == 409)
            expected_winner = winner_payload["winner"]["action"]
            page.evaluate("renderApprovals()")
        else:
            card.locator(f'[data-operator-action="{action}"]').click()
            expected_winner = action

        winner = page.locator("[data-approval-durable-winner]").first
        winner.wait_for(state="visible", timeout=10_000)
        assert winner.get_attribute("data-approval-durable-winner") == expected_winner
        assert len(decision_posts) == (2 if action == "conflict" else 1)

        audit = page.request.get(
            f"{harness.url}api/jobs/{job_id}/operator-requests"
        )
        assert audit.status == 200
        payload = audit.json()
        assert len(payload["decisions"]) == 1
        assert payload["decisions"][0]["action"] == expected_winner
        assert payload["audit_history"][0]["decision_action"] == expected_winner
        assert payload["audit_history"][0]["runtime_id"] == "generic-cli"
        assert payload["audit_history"][0]["stage"] == "idea"

        page.reload(wait_until="networkidle")
        assert page.evaluate("eval('state.activeStage')") == "idea"
        browser_page.diagnostics.http_statuses = [
            item
            for item in browser_page.diagnostics.http_statuses
            if not (action == "conflict" and item[1] == 409)
        ]
        browser_page.diagnostics.console_errors = [
            item
            for item in browser_page.diagnostics.console_errors
            if not (action == "conflict" and "409 (Conflict)" in item)
        ]
        browser_page.diagnostics.assert_clean()
