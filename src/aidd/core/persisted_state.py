from __future__ import annotations

from typing import Any


def require_fields(
    payload: object,
    *,
    label: str,
    fields: dict[str, type | tuple[type, ...]],
    schema_version: int | None = None,
) -> dict[str, Any]:
    """Check recorded JSON fields without coercing or reconstructing missing state."""

    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object.")
    if schema_version is not None:
        version = payload.get("schema_version")
        if type(version) is not int or version != schema_version:
            raise ValueError(f"{label} requires integer schema_version={schema_version}.")
    for name, expected in fields.items():
        if name not in payload:
            raise ValueError(f"{label} is missing required field `{name}`.")
        value = payload[name]
        if not isinstance(value, expected) or (expected is int and type(value) is not int):
            raise ValueError(f"{label} has an invalid type for `{name}`.")
    return payload
