from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES


def repo_root_from(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "contracts").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root from the provided path.")


def stage_contract_paths(repo_root: Path) -> dict[str, Path]:
    contracts_root = repo_root / "contracts" / "stages"
    return {stage: contracts_root / f"{stage}.md" for stage in STAGES}
