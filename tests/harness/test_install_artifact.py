from __future__ import annotations

import zipfile
from pathlib import Path

import aidd.harness.install_artifact as install_artifact
from aidd.core.stages import STAGES
from aidd.harness.install_artifact import (
    HarnessInstallError,
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


def test_prepare_local_wheel_install_returns_absolute_installed_command_for_relative_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    repository_root = tmp_path / "repo"
    repository_root.mkdir()
    (repository_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (repository_root / "contracts").mkdir()

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        _ = cwd
        if command[:3] == ("uv", "build", "--wheel"):
            out_dir = Path(command[-1])
            _write_fake_aidd_wheel(
                out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl"
            )
        elif command[:3] == ("uv", "tool", "install"):
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
        workspace_root=Path(".aidd"),
        run_id="eval-live-test",
        repository_root=repository_root,
    )

    assert Path(result.installed_command[0]).is_absolute()
    assert Path(result.installed_command[0]).exists()


def test_prepare_published_package_install_returns_absolute_installed_command(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    source_lookup_called = False
    monkeypatch.setattr(
        install_artifact,
        "_source_repository_root_from_cwd",
        lambda: (_ for _ in ()).throw(AssertionError("source root lookup not expected")),
    )

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        nonlocal source_lookup_called
        source_lookup_called = cwd.name == "repo"
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
    assert source_lookup_called is False


def test_prepare_local_wheel_install_requires_source_checkout_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    cwd = tmp_path / "not-a-source-checkout"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    try:
        prepare_local_wheel_install(
            workspace_root=tmp_path / ".aidd",
            run_id="eval-live-test",
            repository_root=None,
        )
    except HarnessInstallError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected HarnessInstallError for missing source checkout.")

    assert "Local-wheel live eval requires a source checkout" in message
    assert "AIDD_EVAL_PUBLISHED_PACKAGE_SPEC" in message


def test_prepare_local_wheel_install_can_derive_source_checkout_from_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "pyproject.toml").write_text("[project]\nname='aidd-test'\n")
    (source_root / "contracts").mkdir()
    monkeypatch.chdir(source_root)

    def _fake_run_command(
        *,
        command: tuple[str, ...],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> HarnessCommandTranscript:
        assert cwd == source_root
        if command[:3] == ("uv", "build", "--wheel"):
            out_dir = Path(command[-1])
            _write_fake_aidd_wheel(
                out_dir / "ai_driven_dev_v2-0.0.0-py3-none-any.whl"
            )
        elif command[:3] == ("uv", "tool", "install"):
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
        workspace_root=Path(".aidd"),
        run_id="eval-live-test",
        repository_root=None,
    )

    assert Path(result.installed_command[0]).exists()


def test_prepare_local_wheel_install_rejects_invalid_source_checkout(
    tmp_path: Path,
) -> None:
    try:
        prepare_local_wheel_install(
            workspace_root=tmp_path / ".aidd",
            run_id="eval-live-test",
            repository_root=tmp_path / "invalid-source",
        )
    except HarnessInstallError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected HarnessInstallError for missing source checkout.")

    assert "Local-wheel live eval requires a source checkout" in message
    assert "Received" in message
