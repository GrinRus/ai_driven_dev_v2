from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import yaml

from aidd.cli.ui_assets import operator_static_asset_manifest
from aidd.core.contracts import repo_root_from
from aidd.core.stage_registry import resolve_prompt_pack_paths
from aidd.core.stages import STAGES

_ACTIVE_PROMPT_HASHES_PATH = Path("tests/fixtures/active_prompt_pack_hashes.json")
_REMOVED_COMMON_PROMPT = "prompt-packs/common/run-rules.md"


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _uv_command() -> str:
    return os.environ.get("UV") or "uv"


def _run_bounded(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


def _active_prompt_hashes() -> dict[str, str]:
    root = _repo_root()
    return {
        prompt_path: hashlib.sha256((root / prompt_path).read_bytes()).hexdigest()
        for stage in STAGES
        for prompt_path in resolve_prompt_pack_paths(stage=stage)
    }


def test_active_prompt_pack_paths_and_hashes_match_the_removal_baseline() -> None:
    expected = json.loads(
        (_repo_root() / _ACTIVE_PROMPT_HASHES_PATH).read_text(encoding="utf-8")
    )

    assert _active_prompt_hashes() == expected
    assert _REMOVED_COMMON_PROMPT not in expected
    assert not (_repo_root() / _REMOVED_COMMON_PROMPT).exists()


def test_built_wheel_includes_runtime_owned_contracts_and_prompt_packs(tmp_path: Path) -> None:
    offline_environment = {**os.environ, "UV_OFFLINE": "1"}
    completed = _run_bounded(
        [
            _uv_command(),
            "build",
            "--offline",
            "--wheel",
            "--out-dir",
            tmp_path.as_posix(),
        ],
        cwd=_repo_root(),
        environment=offline_environment,
        timeout_seconds=120.0,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    wheel_paths = sorted(tmp_path.glob("*.whl"))
    assert wheel_paths

    extracted_root = tmp_path / "wheel-root"
    with zipfile.ZipFile(wheel_paths[0]) as archive:
        archive_names = set(archive.namelist())
        metadata_name = next(
            name for name in archive_names if name.endswith(".dist-info/METADATA")
        )
        metadata_text = archive.read(metadata_name).decode("utf-8")
        archive.extractall(extracted_root)

    requires_dist = tuple(
        line.removeprefix("Requires-Dist: ").strip()
        for line in metadata_text.splitlines()
        if line.startswith("Requires-Dist: ")
    )
    normalized_requirements = tuple(requirement.lower() for requirement in requires_dist)
    assert any(requirement.startswith("pyyaml") for requirement in normalized_requirements)
    assert not any(
        requirement.startswith(("python-frontmatter", "markdown-it-py", "pydantic"))
        for requirement in normalized_requirements
    )
    runtime_requirements = tuple(
        requirement for requirement in normalized_requirements if "extra ==" not in requirement
    )
    assert not any(requirement.startswith("playwright") for requirement in runtime_requirements)
    assert any(
        requirement.startswith("playwright") and "extra == 'dev'" in requirement
        for requirement in normalized_requirements
    )
    assert "Provides-Extra: docs" not in metadata_text
    assert not any(
        requirement.startswith(("mkdocs", "mkdocs-material"))
        for requirement in normalized_requirements
    )

    for stage in STAGES:
        assert f"aidd/_resources/contracts/stages/{stage}.md" in archive_names
    assert "aidd/_resources/contracts/documents/stage-result.md" in archive_names
    assert "aidd/_resources/prompt-packs/stages/plan/system.md" in archive_names
    for prompt_path in _active_prompt_hashes():
        assert f"aidd/_resources/{prompt_path}" in archive_names
    assert f"aidd/_resources/{_REMOVED_COMMON_PROMPT}" not in archive_names
    for asset in operator_static_asset_manifest():
        assert f"aidd/cli/static/{asset.filename}" in archive_names

    smoke_cwd = tmp_path / "smoke-cwd"
    smoke_cwd.mkdir()
    smoke_environment = {
        **offline_environment,
        "AIDD_WHEEL_ROOT": extracted_root.as_posix(),
        "PYTHONPATH": extracted_root.as_posix(),
    }
    installed_check = _run_bounded(
        [
            sys.executable,
            "-c",
            (
                "import os; "
                "from pathlib import Path; "
                "import aidd; "
                "from aidd.core.resources import default_stage_contracts_root; "
                "from aidd.core.stages import STAGES; "
                "from aidd.cli.ui_assets import "
                "operator_static_asset_for_route, operator_static_asset_manifest; "
                "wheel_root = Path(os.environ['AIDD_WHEEL_ROOT']).resolve(); "
                "package_path = Path(aidd.__file__).resolve(); "
                "wrong_package = not package_path.is_relative_to(wheel_root); "
                "root = default_stage_contracts_root(); "
                "missing = [stage for stage in STAGES if not (root / f'{stage}.md').exists()]; "
                "assets = [operator_static_asset_for_route(asset.route) "
                "for asset in operator_static_asset_manifest()]; "
                "missing_assets = [asset for asset in assets if asset is None or not asset.text]; "
                "raise SystemExit("
                "f'package imported outside wheel: {package_path}' if wrong_package else "
                "f'missing stage contracts: {missing}' if missing else "
                "f'missing static assets: {missing_assets}' if missing_assets else 0)"
            ),
        ],
        cwd=smoke_cwd,
        environment=smoke_environment,
        timeout_seconds=30.0,
    )

    assert installed_check.returncode == 0, installed_check.stderr or installed_check.stdout


def test_docs_extra_is_absent_from_active_package_and_dependency_update_surfaces() -> None:
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    optional_dependencies = pyproject["project"]["optional-dependencies"]
    dependabot = yaml.safe_load(
        (_repo_root() / ".github/dependabot.yml").read_text(encoding="utf-8")
    )
    grouped_patterns = {
        pattern
        for update in dependabot["updates"]
        for group in update.get("groups", {}).values()
        for pattern in group.get("patterns", ())
    }

    assert "docs" not in optional_dependencies
    assert not any(pattern.startswith("mkdocs") for pattern in grouped_patterns)
