from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import aidd.harness.install_artifact as install_artifact
from aidd.core.stages import STAGES
from aidd.harness.install_artifact import (
    HarnessInstallError,
    HarnessInstallResult,
    prepare_local_wheel_install,
)
from aidd.harness.runner import HarnessCommandTranscript


def _is_uv_build_command(command: tuple[str, ...]) -> bool:
    return command[1:3] == ("build", "--wheel")


def _is_uv_tool_install_command(command: tuple[str, ...]) -> bool:
    return command[1:3] == ("tool", "install")


def _transcript(command: tuple[str, ...]) -> HarnessCommandTranscript:
    return HarnessCommandTranscript(
        command=" ".join(command),
        exit_code=0,
        stdout_text="ok\n",
        stderr_text="",
        duration_seconds=0.1,
    )


def _write_fake_aidd_wheel(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w") as archive:
        for stage in STAGES:
            archive.writestr(f"aidd/_resources/contracts/stages/{stage}.md", "# Stage\n")
        archive.writestr(
            "aidd/_resources/contracts/documents/stage-result.md",
            "# Stage result\n",
        )
        archive.writestr(
            "aidd/_resources/contracts/documents/validator-report.md",
            "# Validator report\n",
        )


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit_source_checkout(repository_root: Path) -> None:
    _run(["git", "init", repository_root.as_posix()])
    _run(["git", "config", "user.email", "tests@example.invalid"], cwd=repository_root)
    _run(["git", "config", "user.name", "AIDD Tests"], cwd=repository_root)
    _run(["git", "add", "."], cwd=repository_root)
    _run(["git", "commit", "-m", "source baseline"], cwd=repository_root)


def test_prepare_local_wheel_install_returns_absolute_installed_command_for_relative_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (repository_root / "contracts").mkdir()
    _commit_source_checkout(repository_root)

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        if _is_uv_build_command(command):
            assert cwd != repository_root
            assert (cwd / "pyproject.toml").exists()
            out_dir = Path(command[-1])
            _write_fake_aidd_wheel(
                out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl"
            )
        elif _is_uv_tool_install_command(command):
            assert "--reinstall" in command
            assert "--refresh" in command
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
        work_root=Path("work-root"),
        run_id="eval-live-test",
        repository_root=repository_root,
    )

    assert Path(result.installed_command[0]).is_absolute()
    assert Path(result.installed_command[0]).exists()
    assert result.source_snapshot_path == (
        tmp_path / "work-root" / "eval-live-test" / "source" / "aidd"
    )
    assert result.build_dist_path == (
        tmp_path / "work-root" / "eval-live-test" / "build" / "dist"
    )
    assert result.install_home == tmp_path / "work-root" / "eval-live-test" / "install-home"
    assert result.uv_cache_dir == tmp_path / "work-root" / "eval-live-test" / "uv-cache"
    assert result.source_revision


def test_prepare_local_wheel_install_honors_uv_environment_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (repository_root / "contracts").mkdir()
    _commit_source_checkout(repository_root)
    uv_override = tmp_path / "bin" / "uv"
    uv_override.parent.mkdir(parents=True, exist_ok=True)
    uv_override.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    uv_override.chmod(0o755)
    observed_commands: list[tuple[str, ...]] = []
    monkeypatch.setenv("UV", uv_override.as_posix())

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        observed_commands.append(command)
        assert command[0] == uv_override.as_posix()
        if _is_uv_build_command(command):
            out_dir = Path(command[-1])
            _write_fake_aidd_wheel(
                out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl"
            )
        elif _is_uv_tool_install_command(command):
            assert env is not None
            home = Path(env["HOME"])
            tool_bin_dir = install_artifact._tool_bin_dir(install_home=home)
            tool_bin_dir.mkdir(parents=True, exist_ok=True)
            installed_binary = tool_bin_dir / "aidd"
            installed_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            installed_binary.chmod(0o755)
        return _transcript(command)

    monkeypatch.setattr(install_artifact, "_run_command", _fake_run_command)

    prepare_local_wheel_install(
        work_root=tmp_path / "work-root",
        run_id="eval-live-test",
        repository_root=repository_root,
    )

    assert len(observed_commands) == 2


def test_prepare_local_wheel_install_requires_source_checkout_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cwd = tmp_path / "not-a-source-checkout"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    try:
        prepare_local_wheel_install(
            work_root=tmp_path / "work-root",
            run_id="eval-live-test",
            repository_root=None,
        )
    except HarnessInstallError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected HarnessInstallError for missing source checkout.")

    assert "Local-wheel live eval requires a source checkout" in message
    assert "published package" not in message.lower()


def test_prepare_local_wheel_install_can_derive_source_checkout_from_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (source_root / "contracts").mkdir()
    _commit_source_checkout(source_root)
    monkeypatch.chdir(source_root)

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        if _is_uv_build_command(command):
            assert cwd != source_root
            assert (cwd / "pyproject.toml").exists()
            out_dir = Path(command[-1])
            _write_fake_aidd_wheel(
                out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl"
            )
        elif _is_uv_tool_install_command(command):
            assert "--reinstall" in command
            assert "--refresh" in command
            assert env is not None
            home = Path(env["HOME"])
            tool_bin_dir = install_artifact._tool_bin_dir(install_home=home)
            tool_bin_dir.mkdir(parents=True, exist_ok=True)
            installed_binary = tool_bin_dir / "aidd"
            installed_binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            installed_binary.chmod(0o755)
        return _transcript(command)

    monkeypatch.setattr(install_artifact, "_run_command", _fake_run_command)

    result = prepare_local_wheel_install(
        work_root=Path("work-root"),
        run_id="eval-live-test",
        repository_root=None,
    )

    assert Path(result.installed_command[0]).exists()


def test_prepare_local_wheel_install_rejects_dirty_tracked_source_checkout(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "source"
    repository_root.mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (repository_root / "contracts").mkdir()
    _commit_source_checkout(repository_root)
    (repository_root / "pyproject.toml").write_text(
        "[project]\nname='aidd-test-dirty'\n",
        encoding="utf-8",
    )

    try:
        prepare_local_wheel_install(
            work_root=tmp_path / "work-root",
            run_id="eval-live-test",
            repository_root=repository_root,
        )
    except HarnessInstallError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected HarnessInstallError for dirty tracked checkout.")

    assert "clean tracked source checkout" in message
    assert not (tmp_path / "work-root" / "eval-live-test" / "source" / "aidd").exists()


def test_prepare_local_wheel_install_rejects_invalid_source_checkout(
    tmp_path: Path,
) -> None:
    try:
        prepare_local_wheel_install(
            work_root=tmp_path / "work-root",
            run_id="eval-live-test",
            repository_root=tmp_path / "invalid-source",
        )
    except HarnessInstallError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected HarnessInstallError for missing source checkout.")

    assert "Local-wheel live eval requires a source checkout" in message
    assert "Received" in message
