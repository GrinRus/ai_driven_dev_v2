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
        route="/operator.css",
        filename="operator.css",
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
