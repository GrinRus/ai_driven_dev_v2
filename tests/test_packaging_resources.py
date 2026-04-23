from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from aidd.core.contracts import repo_root_from


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def test_built_wheel_includes_runtime_owned_contracts_and_prompt_packs(tmp_path: Path) -> None:
    completed = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", tmp_path.as_posix()],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    wheel_paths = sorted(tmp_path.glob("*.whl"))
    assert wheel_paths

    with zipfile.ZipFile(wheel_paths[0]) as archive:
        archive_names = set(archive.namelist())

    assert "aidd/_resources/contracts/stages/plan.md" in archive_names
    assert "aidd/_resources/contracts/documents/stage-result.md" in archive_names
    assert "aidd/_resources/prompt-packs/stages/plan/system.md" in archive_names
