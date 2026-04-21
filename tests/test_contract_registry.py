from __future__ import annotations

from pathlib import Path

from aidd.core.contracts import repo_root_from, stage_contract_paths


def test_stage_contracts_exist() -> None:
    repo_root = repo_root_from(Path(__file__).resolve())
    paths = stage_contract_paths(repo_root)
    assert len(paths) == 8
    assert all(path.exists() for path in paths.values())
