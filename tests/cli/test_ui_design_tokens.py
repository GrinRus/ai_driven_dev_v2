from __future__ import annotations

import re
from collections import Counter

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_operator_token_inventory_covers_accepted_semantic_roles() -> None:
    tokens = _asset("/operator-tokens.css")
    declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", tokens))
    required = {
        "--color-bg-canvas",
        "--color-bg-surface",
        "--color-bg-subtle",
        "--color-border-default",
        "--color-text-primary",
        "--color-text-secondary",
        "--color-action-primary",
        "--color-state-info",
        "--color-state-success",
        "--color-state-warning",
        "--color-state-danger",
        "--color-state-danger-bg",
        "--color-state-danger-border",
        "--color-state-info-bg",
        "--color-state-info-border",
        "--color-state-success-bg",
        "--color-state-success-border",
        "--color-state-warning-bg",
        "--color-state-warning-border",
        "--color-focus",
        "--font-sans",
        "--font-mono",
        "--type-display-size",
        "--type-title-size",
        "--type-body-size",
        "--type-label-size",
        "--type-caption-size",
        "--space-1",
        "--space-2",
        "--space-3",
        "--space-4",
        "--space-6",
        "--space-8",
        "--space-12",
        "--space-16",
        "--radius-control",
        "--radius-surface",
        "--radius-panel",
        "--radius-pill",
        "--elevation-surface",
        "--elevation-overlay",
        "--elevation-sticky",
        "--control-height-compact",
        "--control-height-default",
        "--control-height-touch",
        "--focus-width",
        "--focus-offset",
        "--focus-shadow",
        "--motion-duration-fast",
        "--motion-duration-default",
        "--motion-duration-slow",
        "--motion-ease-standard",
    }
    assert required <= declared


def test_raw_value_inventory_outside_token_layer_cannot_grow() -> None:
    styles = "\n".join(
        _asset(route)
        for route in (
            "/operator-base.css",
            "/operator-layout.css",
            "/operator-components.css",
            "/operator-responsive.css",
        )
    )
    colors = set(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", styles))
    lengths = set(re.findall(r"(?<![-\w.])\d+(?:\.\d+)?(?:px|rem)\b", styles))
    motion = set(re.findall(r"(?<![-\w.])\d+(?:\.\d+)?(?:ms|s)\b", styles))

    assert len(colors) <= 89
    assert len(lengths) <= 83
    assert len(motion) <= 1
    color_counts = Counter(
        re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", styles)
    )
    assert not {
        color: count
        for color, count in color_counts.items()
        if count > 1
    }
