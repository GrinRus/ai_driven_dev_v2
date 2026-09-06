from __future__ import annotations

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_shared_interaction_contract_is_packaged_with_semantic_state_markers() -> None:
    primitives = _asset("/operator-primitives.js")
    contract = primitives.split(
        "const SHARED_INTERACTION_STATE_CONTRACT = Object.freeze({", 1
    )[1].split("\n});", 1)[0]

    for state in (
        "loading",
        "empty",
        "partial",
        "error",
        "disabled",
        "selected",
        "pending",
        "conflict",
        "success",
        "offline",
        "reconnecting",
        "permission-denied",
        "focus",
        "keyboard",
    ):
        key = state if state.isidentifier() else f'"{state}"'
        assert f"  {key}: Object.freeze(" in contract
    assert "function validateSharedInteractionContract(" in primitives
    assert 'data-interaction-contract="shared-v1"' in primitives
    assert 'data-status-text' in primitives
    assert 'data-primary-action data-recovery-action=' in primitives


def test_shared_interaction_contract_keeps_recovery_and_decision_regions_scoped() -> None:
    primitives = _asset("/operator-primitives.js")

    assert 'data-interaction-region role="${role}"' in primitives
    assert 'data-decision-bar="recovery" data-recovery-summary=' in primitives
    assert 'data-primary-recovery-slot' in primitives
