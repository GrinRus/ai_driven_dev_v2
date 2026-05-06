from __future__ import annotations

import tomllib
from pathlib import Path

from aidd import __version__
from aidd.core.contracts import repo_root_from


def test_package_version_matches_project_metadata() -> None:
    repo_root = repo_root_from(Path(__file__).resolve())
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ == pyproject["project"]["version"]
