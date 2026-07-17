from __future__ import annotations

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_segmented_filters_publish_pressed_state_from_the_same_selection() -> None:
    logs = _asset("/operator-logs-jobs.js")
    implementation = _asset("/operator-control-center.js")
    artifacts = _asset("/operator-artifacts-documents.js")

    assert 'aria-pressed="${state.logFilter === filter ? "true" : "false"}"' in logs
    assert 'aria-pressed="${state.logViewMode === mode ? "true" : "false"}"' in logs
    assert 'aria-pressed="${state.rawLogMode ? "true" : "false"}"' in logs
    assert (
        'aria-pressed="${state.implementDiffFilter === id ? "true" : "false"}"'
        in implementation
    )
    assert artifacts.count('aria-pressed="${state.artifactViewMode ===') == 3


def test_radio_cards_and_clickable_rows_publish_authoritative_selection_state() -> None:
    onboarding = _asset("/operator-onboarding.js")
    next_flow = _asset("/operator-next-flow-view.js")
    artifacts = _asset("/operator-artifacts-documents.js")
    shell = _asset("/operator-shell-rendering.js")

    assert 'aria-pressed="${selected ? "true" : "false"}"' in onboarding
    assert 'role="radio"' in next_flow
    assert 'aria-checked="${selected ? "true" : "false"}"' in next_flow
    assert artifacts.count('aria-pressed="${selected ? "true" : "false"}"') >= 1
    assert 'aria-current="${item.work_item === current?.work_item ? "true" : "false"}"' in shell


def test_composite_selection_css_is_driven_by_aria_as_well_as_legacy_classes() -> None:
    styles = "\n".join(
        _asset(route)
        for route in (
            "/operator-base.css",
            "/operator-layout.css",
            "/operator-components.css",
        )
    )

    for selector in (
        '.tabs button[aria-selected="true"]',
        '.log-filter button[aria-pressed="true"]',
        '.viewer-modes button[aria-pressed="true"]',
        '.setup-mode-card[aria-checked="true"]',
        '.runner-card[aria-pressed="true"]',
        '.work-item-card[aria-current="true"]',
        '.artifact-doc[aria-pressed="true"]',
        '.filter-row button[aria-pressed="true"]',
    ):
        assert selector in styles
