"""AIDD package."""

from __future__ import annotations

import tomllib
from importlib import metadata
from pathlib import Path

__all__ = ["__version__"]


def _resolve_version() -> str:
    try:
        return metadata.version("ai-driven-dev-v2")
    except metadata.PackageNotFoundError:
        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
        if pyproject_path.exists():
            project = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
            version = project.get("project", {}).get("version")
            if isinstance(version, str):
                return version
        return "0.0.0+unknown"


__version__ = _resolve_version()
