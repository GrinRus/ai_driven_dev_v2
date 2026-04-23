from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from aidd.core.contracts import repo_root_from
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


def _aidd_repository_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _tool_bin_dir(*, install_home: Path) -> Path:
    if sys.platform.startswith("win"):
        return install_home / ".local" / "Scripts"
    return install_home / ".local" / "bin"


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


def prepare_local_wheel_install(
    *,
    workspace_root: Path,
    run_id: str,
) -> HarnessInstallResult:
    if not run_id.strip():
        raise ValueError("run_id must be non-empty.")

    cache_root = workspace_root / "harness-cache" / "installs" / run_id
    dist_root = cache_root / "dist"
    install_home = cache_root / "home"
    dist_root.mkdir(parents=True, exist_ok=True)
    install_home.mkdir(parents=True, exist_ok=True)

    repository_root = _aidd_repository_root()
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

    tool_bin_dir = _tool_bin_dir(install_home=install_home)
    install_env = dict(os.environ)
    install_env["HOME"] = install_home.as_posix()
    install_env["UV_CACHE_DIR"] = (workspace_root / "harness-cache" / "uv-cache").as_posix()
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

    installed_binary = tool_bin_dir / "aidd"
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

    cache_root = workspace_root / "harness-cache" / "installs" / run_id
    install_home = cache_root / "home"
    install_home.mkdir(parents=True, exist_ok=True)

    tool_bin_dir = _tool_bin_dir(install_home=install_home)
    install_env = dict(os.environ)
    install_env["HOME"] = install_home.as_posix()
    install_env["UV_CACHE_DIR"] = (workspace_root / "harness-cache" / "uv-cache").as_posix()
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
        cwd=_aidd_repository_root(),
        env=install_env,
    )
    if install_transcript.exit_code != 0:
        stderr = install_transcript.stderr_text.strip() or install_transcript.stdout_text.strip()
        raise HarnessInstallError(
            "Failed to install published AIDD package via uv tool for live harness execution: "
            f"{stderr or 'no command output'}"
        )

    installed_binary = tool_bin_dir / "aidd"
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
