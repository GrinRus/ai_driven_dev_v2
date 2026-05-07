from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

_MAX_JSON_BODY_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class UiResponse:
    status: int
    content_type: str
    body: bytes


class UiRequestBodyTooLarge(ValueError):
    """Raised when a UI request body exceeds the private local API limit."""


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _json_response(payload: object, *, status: int = HTTPStatus.OK) -> UiResponse:
    return UiResponse(
        status=int(status),
        content_type="application/json; charset=utf-8",
        body=json.dumps(_jsonable(payload), indent=2, sort_keys=True).encode("utf-8"),
    )


def _error_response(message: str, *, status: int = HTTPStatus.BAD_REQUEST) -> UiResponse:
    return _json_response({"error": message}, status=status)


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer.") from exc
    if length > _MAX_JSON_BODY_BYTES:
        handler.rfile.read(_MAX_JSON_BODY_BYTES)
        raise UiRequestBodyTooLarge("Request body exceeds the 64 KiB UI API limit.")
    if length <= 0:
        return {}
    raw_body = handler.rfile.read(length)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    return payload


__all__ = [
    "UiRequestBodyTooLarge",
    "UiResponse",
    "_error_response",
    "_json_response",
    "_read_json_body",
]
