from __future__ import annotations

import os
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.core.stages import STAGES
from aidd.harness.runner import HarnessCommandTranscript


class HarnessInstallError(RuntimeError):
    """Raised when preparing the installed AIDD artifact fails."""


@dataclass(frozen=True, slots=True)
class HarnessInstallResult:
    install_channel: str
    artifact_source: str
    artifact_identity: str
    artifact_path: Path | None
    install_home: Path
    tool_bin_dir: Path
    installed_command: tuple[str, ...]
    command_transcripts: tuple[HarnessCommandTranscript, ...]
    duration_seconds: float


def _source_repository_root_from_cwd() -> Path | None:
    try:
        return repo_root_from(Path.cwd().resolve(strict=False))
    except FileNotFoundError:
        return None


def _validate_local_wheel_repository_root(repository_root: Path | None) -> Path:
    if repository_root is None:
        raise HarnessInstallError(
            "Local-wheel live eval requires a source checkout containing "
            "`pyproject.toml` and `contracts/`. Could not locate that checkout from "
            "the scenario path or current working directory. Run the eval from a "
            "source checkout, pass a scenario path inside the source checkout, or set "
            "`AIDD_EVAL_PUBLISHED_PACKAGE_SPEC=ai-driven-dev-v2==<version>` to test "
            "an already published package."
        )
    resolved_repository_root = repository_root.resolve(strict=False)
    if not (resolved_repository_root / "pyproject.toml").exists() or not (
        resolved_repository_root / "contracts"
    ).exists():
        raise HarnessInstallError(
            "Local-wheel live eval requires a source checkout containing "
            "`pyproject.toml` and `contracts/`. Received "
            f"{resolved_repository_root.as_posix()}."
        )
    return resolved_repository_root


def _tool_bin_dir(*, install_home: Path) -> Path:
    if sys.platform.startswith("win"):
        return install_home / ".local" / "Scripts"
    return install_home / ".local" / "bin"


def _uv_cache_dir(*, workspace_root: Path) -> Path:
    return workspace_root / "harness-cache" / "uv-cache"


def _run_command(
    *,
    command: tuple[str, ...],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> HarnessCommandTranscript:
    start = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    duration_seconds = time.monotonic() - start
    return HarnessCommandTranscript(
        command=" ".join(command),
        exit_code=completed.returncode,
        stdout_text=completed.stdout,
        stderr_text=completed.stderr,
        duration_seconds=duration_seconds,
    )


def _validate_built_wheel_resources(wheel_path: Path) -> None:
    expected_stage_contracts = {
        f"aidd/_resources/contracts/stages/{stage}.md" for stage in STAGES
    }
    expected_document_contracts = {
        "aidd/_resources/contracts/documents/stage-result.md",
        "aidd/_resources/contracts/documents/validator-report.md",
    }
    try:
        with zipfile.ZipFile(wheel_path) as archive:
            archive_names = set(archive.namelist())
    except zipfile.BadZipFile as exc:
        raise HarnessInstallError(
            f"Built local AIDD wheel is not a valid wheel archive: {wheel_path.as_posix()}."
        ) from exc

    missing_resources = sorted(
        (expected_stage_contracts | expected_document_contracts) - archive_names
    )
    if missing_resources:
        missing = ", ".join(missing_resources)
        raise HarnessInstallError(
            "Built local AIDD wheel is missing packaged runtime resources required "
            f"for installed live execution: {missing}."
        )


def prepare_local_wheel_install(
    *,
    workspace_root: Path,
    run_id: str,
    repository_root: Path | None = None,
) -> HarnessInstallResult:
    if not run_id.strip():
        raise ValueError("run_id must be non-empty.")

    resolved_workspace_root = workspace_root.resolve(strict=False)
    cache_root = resolved_workspace_root / "harness-cache" / "installs" / run_id
    dist_root = cache_root / "dist"
    install_home = cache_root / "home"
    dist_root.mkdir(parents=True, exist_ok=True)
    install_home.mkdir(parents=True, exist_ok=True)

    repository_root = _validate_local_wheel_repository_root(
        repository_root or _source_repository_root_from_cwd()
    )
    build_transcript = _run_command(
        command=("uv", "build", "--wheel", "--out-dir", dist_root.as_posix()),
        cwd=repository_root,
        env=dict(os.environ),
    )
    if build_transcript.exit_code != 0:
        stderr = build_transcript.stderr_text.strip() or build_transcript.stdout_text.strip()
        raise HarnessInstallError(
            "Failed to build local AIDD wheel for live harness execution: "
            f"{stderr or 'no command output'}"
        )

    wheel_paths = sorted(dist_root.glob("*.whl"))
    if not wheel_paths:
        raise HarnessInstallError(
            f"Local wheel build produced no wheel artifacts in {dist_root.as_posix()}."
        )
    wheel_path = wheel_paths[-1]
    _validate_built_wheel_resources(wheel_path)

    tool_bin_dir = _tool_bin_dir(install_home=install_home)
    install_env = dict(os.environ)
    install_env["HOME"] = install_home.as_posix()
    install_env["UV_CACHE_DIR"] = _uv_cache_dir(workspace_root=resolved_workspace_root).as_posix()
    install_env["PATH"] = os.pathsep.join(
        [
            tool_bin_dir.as_posix(),
            install_env.get("PATH", ""),
        ]
    )
    install_transcript = _run_command(
        command=(
            "uv",
            "tool",
            "install",
            "--force",
            "--reinstall",
            "--refresh",
            "--python",
            sys.executable,
            wheel_path.as_posix(),
        ),
        cwd=repository_root,
        env=install_env,
    )
    if install_transcript.exit_code != 0:
        stderr = install_transcript.stderr_text.strip() or install_transcript.stdout_text.strip()
        raise HarnessInstallError(
            "Failed to install local AIDD wheel via uv tool for live harness execution: "
            f"{stderr or 'no command output'}"
        )

    installed_binary = (tool_bin_dir / "aidd").resolve(strict=False)
    if not installed_binary.exists():
        raise HarnessInstallError(
            "uv tool install completed but the installed AIDD binary was not found at "
            f"{installed_binary.as_posix()}."
        )

    return HarnessInstallResult(
        install_channel="uv-tool",
        artifact_source="local-wheel",
        artifact_identity=wheel_path.name,
        artifact_path=wheel_path,
        install_home=install_home,
        tool_bin_dir=tool_bin_dir,
        installed_command=(installed_binary.as_posix(),),
        command_transcripts=(build_transcript, install_transcript),
        duration_seconds=sum(
            transcript.duration_seconds
            for transcript in (build_transcript, install_transcript)
        ),
    )


def prepare_published_package_install(
    *,
    workspace_root: Path,
    run_id: str,
    package_spec: str,
) -> HarnessInstallResult:
    normalized_package_spec = package_spec.strip()
    if not normalized_package_spec:
        raise ValueError("package_spec must be non-empty.")
    if not run_id.strip():
        raise ValueError("run_id must be non-empty.")

    resolved_workspace_root = workspace_root.resolve(strict=False)
    cache_root = resolved_workspace_root / "harness-cache" / "installs" / run_id
    install_home = cache_root / "home"
    resolved_workspace_root.mkdir(parents=True, exist_ok=True)
    install_home.mkdir(parents=True, exist_ok=True)

    tool_bin_dir = _tool_bin_dir(install_home=install_home)
    install_env = dict(os.environ)
    install_env["HOME"] = install_home.as_posix()
    install_env["UV_CACHE_DIR"] = _uv_cache_dir(workspace_root=resolved_workspace_root).as_posix()
    install_env["PATH"] = os.pathsep.join(
        [
            tool_bin_dir.as_posix(),
            install_env.get("PATH", ""),
        ]
    )
    install_transcript = _run_command(
        command=(
            "uv",
            "tool",
            "install",
            "--force",
            "--python",
            sys.executable,
            normalized_package_spec,
        ),
        cwd=resolved_workspace_root,
        env=install_env,
    )
    if install_transcript.exit_code != 0:
        stderr = install_transcript.stderr_text.strip() or install_transcript.stdout_text.strip()
        raise HarnessInstallError(
            "Failed to install published AIDD package via uv tool for live harness execution: "
            f"{stderr or 'no command output'}"
        )

    installed_binary = (tool_bin_dir / "aidd").resolve(strict=False)
    if not installed_binary.exists():
        raise HarnessInstallError(
            "uv tool install completed but the installed AIDD binary was not found at "
            f"{installed_binary.as_posix()}."
        )

    return HarnessInstallResult(
        install_channel="uv-tool",
        artifact_source="published-package",
        artifact_identity=normalized_package_spec,
        artifact_path=None,
        install_home=install_home,
        tool_bin_dir=tool_bin_dir,
        installed_command=(installed_binary.as_posix(),),
        command_transcripts=(install_transcript,),
        duration_seconds=install_transcript.duration_seconds,
    )


__all__ = [
    "HarnessInstallError",
    "HarnessInstallResult",
    "prepare_local_wheel_install",
    "prepare_published_package_install",
]
