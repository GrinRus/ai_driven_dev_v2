from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

_STATIC_PACKAGE = "aidd.cli.static"


@dataclass(frozen=True, slots=True)
class OperatorStaticAsset:
    route: str
    filename: str
    content_type: str


@dataclass(frozen=True, slots=True)
class OperatorStaticAssetContent:
    route: str
    filename: str
    content_type: str
    text: str


_OPERATOR_STATIC_ASSET_MANIFEST = (
    OperatorStaticAsset(
        route="/",
        filename="index.html",
        content_type="text/html; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator.js",
        filename="operator.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-presentation.js",
        filename="operator-presentation.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-api-state.js",
        filename="operator-api-state.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-shell-rendering.js",
        filename="operator-shell-rendering.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-dashboard-actions.js",
        filename="operator-dashboard-actions.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-onboarding.js",
        filename="operator-onboarding.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-artifacts-documents.js",
        filename="operator-artifacts-documents.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-questions.js",
        filename="operator-questions.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-approvals-interventions.js",
        filename="operator-approvals-interventions.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-logs-jobs.js",
        filename="operator-logs-jobs.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-next-flow-actions.js",
        filename="operator-next-flow-actions.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-next-flow-view.js",
        filename="operator-next-flow-view.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-control-center.js",
        filename="operator-control-center.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-stage-cockpit.js",
        filename="operator-stage-cockpit.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-main.js",
        filename="operator-main.js",
        content_type="text/javascript; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator.css",
        filename="operator.css",
        content_type="text/css; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-tokens.css",
        filename="operator-tokens.css",
        content_type="text/css; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-base.css",
        filename="operator-base.css",
        content_type="text/css; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-layout.css",
        filename="operator-layout.css",
        content_type="text/css; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-components.css",
        filename="operator-components.css",
        content_type="text/css; charset=utf-8",
    ),
    OperatorStaticAsset(
        route="/operator-responsive.css",
        filename="operator-responsive.css",
        content_type="text/css; charset=utf-8",
    ),
)


def _read_static_text(filename: str) -> str:
    return files(_STATIC_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


_STATIC_TEXT_BY_FILENAME = {
    asset.filename: _read_static_text(asset.filename)
    for asset in _OPERATOR_STATIC_ASSET_MANIFEST
}
_STATIC_ASSET_BY_ROUTE = {
    asset.route: asset
    for asset in _OPERATOR_STATIC_ASSET_MANIFEST
}

_INDEX_HTML = _STATIC_TEXT_BY_FILENAME["index.html"]
_OPERATOR_CSS = _STATIC_TEXT_BY_FILENAME["operator.css"]
_OPERATOR_JS = _STATIC_TEXT_BY_FILENAME["operator.js"]


def operator_static_asset_manifest() -> tuple[OperatorStaticAsset, ...]:
    return _OPERATOR_STATIC_ASSET_MANIFEST


def operator_static_asset_for_route(route: str) -> OperatorStaticAssetContent | None:
    asset = _STATIC_ASSET_BY_ROUTE.get(route)
    if asset is None:
        return None
    return OperatorStaticAssetContent(
        route=asset.route,
        filename=asset.filename,
        content_type=asset.content_type,
        text=_STATIC_TEXT_BY_FILENAME[asset.filename],
    )


__all__ = [
    "OperatorStaticAsset",
    "OperatorStaticAssetContent",
    "_INDEX_HTML",
    "_OPERATOR_CSS",
    "_OPERATOR_JS",
    "operator_static_asset_for_route",
    "operator_static_asset_manifest",
]
