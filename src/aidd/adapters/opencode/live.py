from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OpenCodePermissionEndpoints:
    request_path: str
    response_path: str


def discover_permission_endpoints(
    openapi_document: Mapping[str, Any],
) -> OpenCodePermissionEndpoints | None:
    raw_paths = openapi_document.get("paths")
    if not isinstance(raw_paths, Mapping):
        return None

    request_path: str | None = None
    response_path: str | None = None
    for raw_path, raw_methods in raw_paths.items():
        if not isinstance(raw_path, str) or "permission" not in raw_path.lower():
            continue
        methods = raw_methods if isinstance(raw_methods, Mapping) else {}
        operation_blob = " ".join(
            str(value)
            for method_payload in methods.values()
            if isinstance(method_payload, Mapping)
            for value in (
                method_payload.get("operationId"),
                method_payload.get("summary"),
                method_payload.get("description"),
            )
            if value is not None
        ).lower()
        path_lower = raw_path.lower()
        if request_path is None and (
            "request" in path_lower or "pending" in path_lower or "list" in operation_blob
        ):
            request_path = raw_path
        if response_path is None and (
            "response" in path_lower
            or "decision" in path_lower
            or "respond" in operation_blob
            or "approve" in operation_blob
        ):
            response_path = raw_path

    if request_path is None or response_path is None:
        return None
    return OpenCodePermissionEndpoints(
        request_path=request_path,
        response_path=response_path,
    )


__all__ = ["OpenCodePermissionEndpoints", "discover_permission_endpoints"]
