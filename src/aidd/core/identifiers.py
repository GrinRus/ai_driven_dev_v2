from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True, slots=True)
class SafeIdentifier:
    value: str

    @classmethod
    def parse(cls, value: str, *, label: str = "identifier") -> SafeIdentifier:
        normalized = value.strip()
        if normalized in {"", ".", ".."} or not _IDENTIFIER_PATTERN.fullmatch(normalized):
            raise ValueError(
                f"{label} must be one plain path component containing only letters, "
                "numbers, '.', '_' or '-'."
            )
        return cls(normalized)


def resolve_contained_component(
    root: Path,
    identifier: str,
    *,
    label: str = "identifier",
) -> Path:
    safe = SafeIdentifier.parse(identifier, label=label)
    resolved_root = root.resolve(strict=False)
    resolved = (resolved_root / safe.value).resolve(strict=False)
    if resolved.parent != resolved_root:
        raise ValueError(f"{label} must resolve directly below its owning root.")
    return resolved


def contained_component_path(
    root: Path,
    identifier: str,
    *,
    boundary_root: Path,
    label: str = "identifier",
) -> Path:
    safe = SafeIdentifier.parse(identifier, label=label)
    resolved_boundary = boundary_root.resolve(strict=False)
    resolved_root = root.resolve(strict=False)
    if not resolved_root.is_relative_to(resolved_boundary):
        raise ValueError(f"{label} owning root must stay inside its storage boundary.")
    resolve_contained_component(root, safe.value, label=label)
    return root / safe.value


__all__ = ["SafeIdentifier", "contained_component_path", "resolve_contained_component"]
