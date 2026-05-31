from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from aidd.cli.ui_assets import operator_static_asset_manifest
from aidd.core.contracts import repo_root_from
from aidd.core.stages import STAGES


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _uv_command() -> str:
    return os.environ.get("UV") or shutil.which("uv") or "uv"


def test_built_wheel_includes_runtime_owned_contracts_and_prompt_packs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [_uv_command(), "build", "--wheel", "--out-dir", tmp_path.as_posix()],
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

    for stage in STAGES:
        assert f"aidd/_resources/contracts/stages/{stage}.md" in archive_names
    assert "aidd/_resources/contracts/documents/stage-result.md" in archive_names
    assert "aidd/_resources/prompt-packs/stages/plan/system.md" in archive_names
    for asset in operator_static_asset_manifest():
        assert f"aidd/cli/static/{asset.filename}" in archive_names

    installed_check = subprocess.run(
        [
            _uv_command(),
            "run",
            "--isolated",
            "--no-cache",
            "--python",
            sys.executable,
            "--with",
            wheel_paths[0].as_posix(),
            "python",
            "-c",
            (
                "from aidd.core.resources import default_stage_contracts_root; "
                "from aidd.core.stages import STAGES; "
                "from aidd.cli.ui_assets import "
                "operator_static_asset_for_route, operator_static_asset_manifest; "
                "root = default_stage_contracts_root(); "
                "missing = [stage for stage in STAGES if not (root / f'{stage}.md').exists()]; "
                "assets = [operator_static_asset_for_route(asset.route) "
                "for asset in operator_static_asset_manifest()]; "
                "missing_assets = [asset for asset in assets if asset is None or not asset.text]; "
                "raise SystemExit("
                "f'missing stage contracts: {missing}' if missing else "
                "f'missing static assets: {missing_assets}' if missing_assets else 0)"
            ),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert installed_check.returncode == 0, installed_check.stderr or installed_check.stdout
