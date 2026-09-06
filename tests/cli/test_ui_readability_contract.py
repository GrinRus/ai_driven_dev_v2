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
    numeric_rule = re.search(
        r"([^{}]+)\{([^{}]*font-variant-numeric:\s*tabular-nums;[^{}]*)\}",
        styles,
    )
    assert numeric_rule is not None
    selectors = {selector.strip() for selector in numeric_rule[1].split(",")}
    assert {
        ".small-badge",
        ".metric strong",
        ".approval-summary-metric strong",
    }.issubset(selectors)
    assert 'font-feature-settings: "tnum" 1;' in numeric_rule[2]
    assert "font-variant-numeric: tabular-nums;" in numeric_rule[2]
