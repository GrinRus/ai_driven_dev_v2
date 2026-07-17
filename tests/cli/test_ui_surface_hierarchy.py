from __future__ import annotations

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_document_canvas_is_primary_and_evidence_inspector_is_conditional() -> None:
    artifacts = _asset("/operator-artifacts-documents.js")

    assert "function renderWorkbenchEvidenceInspector(workbench)" in artifacts
    assert 'if (!visible) return "";' in artifacts
    assert "hierarchy-primary document-canvas" in artifacts
    assert "hierarchy-supporting evidence-inspector" in artifacts
    assert 'data-evidence-inspector="${evidenceInspector ? "present" : "absent"}"' in artifacts


def test_history_uses_primary_filmstrip_and_supporting_event_hierarchy() -> None:
    history = _asset("/operator-next-flow-view.js")
    cockpit = _asset("/operator-stage-cockpit.js")

    assert "hierarchy-primary history-filmstrip" in history
    assert "history-mode hierarchy-sequence" in cockpit
    assert "hierarchy-supporting history-events" in cockpit


def test_supporting_hierarchy_cannot_restore_an_equal_weight_card_wall() -> None:
    styles = _asset("/operator-components.css")

    assert ".hierarchy-supporting > .surface {" in styles
    assert "background: transparent;" in styles
    assert "grid-template-columns: minmax(0, 1fr) minmax(260px, 320px);" in styles
    assert "@media (max-width: 1120px)" in styles
