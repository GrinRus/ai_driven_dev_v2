from __future__ import annotations

import re

from aidd.cli.ui_assets import operator_static_asset_for_route


def _asset(route: str) -> str:
    asset = operator_static_asset_for_route(route)
    assert asset is not None
    return asset.text


def test_packaged_styles_do_not_restore_subminimum_microcopy() -> None:
    styles = "\n".join(
        _asset(route)
        for route in (
            "/operator-layout.css",
            "/operator-components.css",
            "/operator-responsive.css",
        )
    )

    assert re.findall(r"font-size:\s*(?:[0-9]|1[01])px", styles) == []
    assert "font-size: var(--type-caption-size);" in styles
    assert "--type-caption-size: 12px;" in _asset("/operator-tokens.css")


def test_scannable_runtime_and_status_metrics_use_tabular_numerals() -> None:
    styles = _asset("/operator-components.css")

    for selector in (
        ".counter",
        ".small-badge",
        ".stage-index",
        ".metric strong",
        ".decision-metric strong",
        ".handoff-metric strong",
        ".approval-summary-metric strong",
    ):
        assert selector in styles
    assert 'font-feature-settings: "tnum" 1;' in styles
    assert "font-variant-numeric: tabular-nums;" in styles
