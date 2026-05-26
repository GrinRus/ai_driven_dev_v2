from __future__ import annotations

from importlib.resources import files

_STATIC_PACKAGE = "aidd.cli.static"


def _read_static_text(filename: str) -> str:
    return files(_STATIC_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


_INDEX_HTML = _read_static_text("index.html")
_OPERATOR_CSS = _read_static_text("operator.css")
_OPERATOR_JS = _read_static_text("operator.js")

__all__ = ["_INDEX_HTML", "_OPERATOR_CSS", "_OPERATOR_JS"]
