from __future__ import annotations

from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.core.stage_registry import stage_contract_path
from aidd.core.stages import STAGES


def test_stage_contracts_exist() -> None:
    repo_root = repo_root_from(Path(__file__).resolve())
    paths = tuple(
        stage_contract_path(stage=stage, contracts_root=repo_root / "contracts" / "stages")
        for stage in STAGES
    )
    assert len(paths) == 8
    assert all(path.is_file() for path in paths)
