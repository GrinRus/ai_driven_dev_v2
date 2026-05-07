from __future__ import annotations

from collections.abc import Iterable


def patch_module_value(module: object, name: str, value: object) -> None:
    setattr(module, name, value)


def patch_module_values(
    module: object,
    values: Iterable[tuple[str, object]],
) -> None:
    for name, value in values:
        patch_module_value(module, name, value)


__all__ = ["patch_module_value", "patch_module_values"]
