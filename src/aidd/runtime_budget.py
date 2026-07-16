from __future__ import annotations

import math


def validate_runtime_budget(
    value: object,
    *,
    label: str = "timeout_seconds",
) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number greater than zero when provided.")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0:
        raise ValueError(f"{label} must be a finite number greater than zero when provided.")
    return normalized


__all__ = ["validate_runtime_budget"]
