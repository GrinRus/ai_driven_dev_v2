from __future__ import annotations

from pathlib import Path

import aidd.harness.install_artifact as install_artifact
from aidd.harness.install_artifact import (
    HarnessInstallResult,
    prepare_local_wheel_install,
    prepare_published_package_install,
)
from aidd.harness.runner import HarnessCommandTranscript


def _transcript(command: tuple[str, ...]) -> HarnessCommandTranscript:
    return HarnessCommandTranscript(
        command=" ".join(command),
        exit_code=0,
        stdout_text="ok\n",
        stderr_text="",
        duration_seconds=0.1,
    )


def test_prepare_local_wheel_install_returns_absolute_installed_command_for_relative_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    monkeypatch.setattr(install_artifact, "_aidd_repository_root", lambda: repository_root)

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        _ = cwd
        if command[:3] == ("uv", "build", "--wheel"):
            out_dir = Path(command[-1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl").write_text(
                "wheel\n",
                encoding="utf-8",
            )
        elif command[:3] == ("uv", "tool", "install"):
            assert env is not None
            assert Path(env["UV_CACHE_DIR"]).is_absolute()
            home = Path(env["HOME"])
            tool_bin_dir = install_artifact._tool_bin_dir(install_home=home)
            tool_bin_dir.mkdir(parents=True, exist_ok=True)
            installed_binary = tool_bin_dir / "aidd"
            installed_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            installed_binary.chmod(0o755)
        return _transcript(command)

    monkeypatch.setattr(install_artifact, "_run_command", _fake_run_command)

    result: HarnessInstallResult = prepare_local_wheel_install(
        workspace_root=Path(".aidd"),
        run_id="eval-live-test",
    )

    assert Path(result.installed_command[0]).is_absolute()
    assert Path(result.installed_command[0]).exists()


def test_prepare_published_package_install_returns_absolute_installed_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    monkeypatch.setattr(install_artifact, "_aidd_repository_root", lambda: repository_root)

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        _ = cwd
        assert env is not None
        assert Path(env["UV_CACHE_DIR"]).is_absolute()
        home = Path(env["HOME"])
        tool_bin_dir = install_artifact._tool_bin_dir(install_home=home)
        tool_bin_dir.mkdir(parents=True, exist_ok=True)
        installed_binary = tool_bin_dir / "aidd"
        installed_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        installed_binary.chmod(0o755)
        return _transcript(command)

    monkeypatch.setattr(install_artifact, "_run_command", _fake_run_command)

    result = prepare_published_package_install(
        workspace_root=Path(".aidd"),
        run_id="eval-live-test",
        package_spec="ai-driven-dev-v2==9.9.9",
    )

    assert Path(result.installed_command[0]).is_absolute()
    assert Path(result.installed_command[0]).exists()
