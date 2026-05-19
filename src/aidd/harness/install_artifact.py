from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tarfile
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
    source_snapshot_path: Path | None = None
    build_dist_path: Path | None = None
    uv_cache_dir: Path | None = None
    source_revision: str | None = None


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


def _run_uv_cache_dir(*, run_root: Path) -> Path:
    return run_root / "uv-cache"


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


def _git_stdout(args: tuple[str, ...], *, cwd: Path) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return completed.stdout.strip()
    stderr = completed.stderr.strip() or completed.stdout.strip() or "unknown git error"
    raise HarnessInstallError(stderr)


def _require_clean_tracked_head(repository_root: Path) -> str:
    try:
        source_revision = _git_stdout(("rev-parse", "HEAD"), cwd=repository_root)
    except HarnessInstallError as exc:
        raise HarnessInstallError(
            "Local-wheel live eval requires a git checkout so the black-box source "
            "snapshot can be built from tracked HEAD. "
            f"{exc}"
        ) from exc

    status = subprocess.run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode != 0:
        stderr = status.stderr.strip() or status.stdout.strip() or "unknown git error"
        raise HarnessInstallError(
            "Failed to inspect source checkout cleanliness before live eval: "
            f"{stderr}"
        )
    if status.stdout.strip():
        raise HarnessInstallError(
            "Local-wheel live eval requires a clean tracked source checkout because "
            "the black-box artifact is built from tracked HEAD. Commit or stash "
            "tracked changes before running live E2E."
        )
    return source_revision


def _snapshot_tracked_head(
    *,
    repository_root: Path,
    source_snapshot_path: Path,
) -> str:
    source_revision = _require_clean_tracked_head(repository_root)
    if source_snapshot_path.exists():
        shutil.rmtree(source_snapshot_path)
    source_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    source_snapshot_path.mkdir(parents=True, exist_ok=True)

    archive = subprocess.run(
        ("git", "archive", "--format=tar", "HEAD"),
        cwd=repository_root,
        capture_output=True,
        check=False,
    )
    if archive.returncode != 0:
        stderr = archive.stderr.decode(errors="replace").strip()
        stdout = archive.stdout.decode(errors="replace").strip()
        raise HarnessInstallError(
            "Failed to snapshot tracked HEAD for local-wheel live eval: "
            f"{stderr or stdout or 'no command output'}"
        )

    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
        tar.extractall(source_snapshot_path)
    return source_revision


def prepare_local_wheel_install(
    *,
    work_root: Path,
    run_id: str,
    repository_root: Path | None = None,
) -> HarnessInstallResult:
    if not run_id.strip():
        raise ValueError("run_id must be non-empty.")

    resolved_work_root = work_root.resolve(strict=False)
    run_root = resolved_work_root / run_id
    source_snapshot_path = run_root / "source" / "aidd"
    dist_root = run_root / "build" / "dist"
    install_home = run_root / "install-home"
    uv_cache_dir = _run_uv_cache_dir(run_root=run_root)
    dist_root.mkdir(parents=True, exist_ok=True)
    install_home.mkdir(parents=True, exist_ok=True)
    uv_cache_dir.mkdir(parents=True, exist_ok=True)

    repository_root = _validate_local_wheel_repository_root(
        repository_root or _source_repository_root_from_cwd()
    )
    source_revision = _snapshot_tracked_head(
        repository_root=repository_root,
        source_snapshot_path=source_snapshot_path,
    )
    build_transcript = _run_command(
        command=("uv", "build", "--wheel", "--out-dir", dist_root.as_posix()),
        cwd=source_snapshot_path,
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
    install_env["UV_CACHE_DIR"] = uv_cache_dir.as_posix()
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
        cwd=source_snapshot_path,
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
        source_snapshot_path=source_snapshot_path,
        build_dist_path=dist_root,
        uv_cache_dir=uv_cache_dir,
        source_revision=source_revision,
    )


def prepare_published_package_install(
    *,
    work_root: Path,
    run_id: str,
    package_spec: str,
) -> HarnessInstallResult:
    normalized_package_spec = package_spec.strip()
    if not normalized_package_spec:
        raise ValueError("package_spec must be non-empty.")
    if not run_id.strip():
        raise ValueError("run_id must be non-empty.")

    resolved_work_root = work_root.resolve(strict=False)
    run_root = resolved_work_root / run_id
    install_home = run_root / "install-home"
    uv_cache_dir = _run_uv_cache_dir(run_root=run_root)
    resolved_work_root.mkdir(parents=True, exist_ok=True)
    install_home.mkdir(parents=True, exist_ok=True)
    uv_cache_dir.mkdir(parents=True, exist_ok=True)

    tool_bin_dir = _tool_bin_dir(install_home=install_home)
    install_env = dict(os.environ)
    install_env["HOME"] = install_home.as_posix()
    install_env["UV_CACHE_DIR"] = uv_cache_dir.as_posix()
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
        cwd=run_root,
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
        uv_cache_dir=uv_cache_dir,
    )


__all__ = [
    "HarnessInstallError",
    "HarnessInstallResult",
    "prepare_local_wheel_install",
    "prepare_published_package_install",
]
