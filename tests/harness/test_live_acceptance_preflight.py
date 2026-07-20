from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from aidd.harness.live_acceptance_preflight import (
    LiveAcceptancePreflightError,
    assert_tracked_source_unchanged,
    capture_tracked_source_state,
    prepare_live_acceptance_layout,
)


def _git(repository: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=repository, check=True, capture_output=True, text=True)


def _source_checkout(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "contracts").mkdir()
    (source / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
    scenario = source / "scenario.yaml"
    scenario.write_text("fixture\n", encoding="utf-8")
    _git(source, "init")
    _git(source, "config", "user.email", "fixture@example.test")
    _git(source, "config", "user.name", "Fixture")
    _git(source, "add", ".")
    _git(source, "commit", "-m", "fixture")
    return source


def test_tracked_source_state_rejects_dirty_tracked_checkout(tmp_path: Path) -> None:
    source = _source_checkout(tmp_path)
    (source / "pyproject.toml").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(LiveAcceptancePreflightError, match="clean tracked"):
        capture_tracked_source_state(source)


def test_tracked_source_postflight_detects_revision_change(tmp_path: Path) -> None:
    source = _source_checkout(tmp_path)
    expected = capture_tracked_source_state(source)
    (source / "new.txt").write_text("new\n", encoding="utf-8")
    _git(source, "add", "new.txt")
    _git(source, "commit", "-m", "changed")

    with pytest.raises(LiveAcceptancePreflightError, match="changed during"):
        assert_tracked_source_unchanged(source, expected)


@pytest.mark.parametrize("external_name", ("source/external", "source"))
def test_preflight_rejects_external_root_overlapping_source(
    tmp_path: Path,
    external_name: str,
) -> None:
    source = _source_checkout(tmp_path)
    external = tmp_path / external_name

    with pytest.raises(LiveAcceptancePreflightError, match="must not overlap"):
        prepare_live_acceptance_layout(
            source_checkout=source,
            external_root=external,
            scenario_path=source / "scenario.yaml",
            provider_id="codex",
        )


def test_preflight_rejects_scenario_outside_source(tmp_path: Path) -> None:
    source = _source_checkout(tmp_path)
    scenario = tmp_path / "external-scenario.yaml"
    scenario.write_text("fixture\n", encoding="utf-8")

    with pytest.raises(LiveAcceptancePreflightError, match="tracked AIDD source"):
        prepare_live_acceptance_layout(
            source_checkout=source,
            external_root=tmp_path / "external",
            scenario_path=scenario,
            provider_id="codex",
        )


def test_preflight_builds_independent_provider_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source_checkout(tmp_path)
    scenario_path = source / "scenario.yaml"

    class _Run:
        stage_start = "idea"
        stage_end = "qa"

    class _LiveFlow:
        frontend_checkpoints = True

    class _Scenario:
        scenario_id = "LIVE-FIXTURE"
        is_live = True
        automation_lane = "manual"
        run = _Run()
        live_flow = _LiveFlow()

    class _Mode:
        value = "native"

    class _Command:
        command = "provider command"
        execution_mode = _Mode()

    monkeypatch.setattr(
        "aidd.harness.live_acceptance_preflight.load_scenario",
        lambda *args, **kwargs: _Scenario(),
    )
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_preflight.validate_live_runtime_command",
        lambda *args, **kwargs: _Command(),
    )

    external = tmp_path / "external"
    external.mkdir()
    codex = prepare_live_acceptance_layout(
        source_checkout=source,
        external_root=external,
        scenario_path=scenario_path,
        provider_id="codex",
    )
    claude = prepare_live_acceptance_layout(
        source_checkout=source,
        external_root=external,
        scenario_path=scenario_path,
        provider_id="claude-code",
    )

    assert codex.provider_root == external / "codex"
    assert claude.provider_root == external / "claude-code"
    assert not codex.provider_root.is_relative_to(claude.provider_root)
    assert not claude.provider_root.is_relative_to(codex.provider_root)
    assert {codex.work_root.name, codex.report_root.name, codex.browser_root.name} == {
        "work",
        "reports",
        "browser",
    }


@pytest.mark.skipif(sys.platform.startswith("win"), reason="symlink fixture is POSIX-specific")
def test_preflight_rejects_provider_symlink_alias(tmp_path: Path) -> None:
    source = _source_checkout(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    (external / "codex").mkdir()
    (external / "claude-code").symlink_to(external / "codex", target_is_directory=True)

    with pytest.raises(LiveAcceptancePreflightError, match="unsymlinked component"):
        prepare_live_acceptance_layout(
            source_checkout=source,
            external_root=external,
            scenario_path=source / "scenario.yaml",
            provider_id="claude-code",
        )
