from __future__ import annotations

from pathlib import Path


def repo_root_from(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "contracts").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root from the provided path.")
