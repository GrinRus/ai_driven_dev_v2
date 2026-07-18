from __future__ import annotations

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_skip_link_precedes_maintenance_controls_and_targets_current_decision() -> None:
    html = _asset("/")
    focus = _asset("/operator-focus.js")

    assert html.index('id="skipToDecision"') < html.index('class="topbar"')
    assert html.index('id="cockpitContent"') < html.index('class="maintenance-overflow"')
    assert '<summary data-aidd-focus-role="maintenance">Maintenance</summary>' in html
    assert 'role="group" aria-label="Service maintenance commands"' in html
    assert 'href="#currentDecision"' in html
    assert 'target.id = "currentDecision";' in focus
    assert '"#cockpitContent [data-primary-recovery-slot]"' in focus
    assert '"#cockpitContent [data-primary-slot]"' in focus


def test_focus_controller_owns_detail_entry_and_escape_return() -> None:
    focus = _asset("/operator-focus.js")
    cockpit = _asset("/operator-stage-cockpit.js")

    assert "rememberOperatorFocusReturn(detailTrigger)" in focus
    assert 'event.key !== "Escape"' in focus
    assert "operatorFocusReturnTarget?.isConnected" in focus
    assert "async function renderCockpitContent()" in cockpit
    assert "syncCurrentDecisionTarget();" in cockpit
