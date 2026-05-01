from __future__ import annotations

from pathlib import Path

import pytest

from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.harness.live_runtime_config import (
    resolve_live_runtime_command_entries,
    validate_live_runtime_command,
    write_live_runtime_config,
)
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioFeatureSource,
    ScenarioIssueSeed,
    ScenarioQualityConfig,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _empty_live_command_env() -> dict[str, str]:
    return {
        "AIDD_EVAL_CLAUDE_CODE_COMMAND": "",
        "AIDD_EVAL_CODEX_COMMAND": "",
        "AIDD_EVAL_GENERIC_CLI_COMMAND": "",
        "AIDD_EVAL_OPENCODE_COMMAND": "",
    }


def _scenario(*, runtime_targets: tuple[str, ...] = ("codex", "opencode")) -> Scenario:
    return Scenario(
        scenario_id="AIDD-LIVE-TEST",
        scenario_class="live-full-flow",
        feature_size="small",
        automation_lane="manual",
        canonical_runtime=runtime_targets[0],
        task="exercise live runtime config",
        repo=ScenarioRepoSource(
            url="https://example.invalid/repo.git",
            default_branch=None,
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=tuple()),
        run=ScenarioRunConfig(
            stage_start="idea",
            stage_end="qa",
            runtime_targets=runtime_targets,
            patch_budget_files=None,
            timeout_minutes=None,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=tuple()),
        feature_source=ScenarioFeatureSource(
            mode="curated-issue-pool",
            selection_policy="first-listed",
            issues=(
                ScenarioIssueSeed(
                    issue_id="123",
                    title="issue",
                    url="https://example.invalid/issues/123",
                    summary="issue",
                    labels=tuple(),
                ),
            ),
            fixture_path=None,
            seed_id=None,
            summary=None,
        ),
        quality=ScenarioQualityConfig(
            commands=tuple(),
            rubric_profile="live-full",
            require_review_status="approved",
            allowed_qa_verdicts=("ready",),
            code_review_required=True,
        ),
        runtime_targets=runtime_targets,
        is_live=True,
        raw={},
    )


def test_resolve_live_runtime_command_entries_defaults_codex_to_native() -> None:
    entries = resolve_live_runtime_command_entries(
        environment=_empty_live_command_env(),
        scenario=_scenario(runtime_targets=("codex",)),
    )

    assert entries["codex"].execution_mode is RuntimeExecutionMode.NATIVE
    assert entries["codex"].command.startswith("codex exec")
    assert entries["codex"].source == "default-native"


def test_resolve_live_runtime_command_entries_defaults_claude_code_to_native() -> None:
    entries = resolve_live_runtime_command_entries(
        environment=_empty_live_command_env(),
        scenario=_scenario(runtime_targets=("claude-code",)),
    )

    assert entries["claude-code"].execution_mode is RuntimeExecutionMode.NATIVE
    assert entries["claude-code"].command.startswith("claude -p")
    assert entries["claude-code"].source == "default-native"


def test_resolve_live_runtime_command_entries_uses_env_override_as_adapter_flags() -> None:
    entries = resolve_live_runtime_command_entries(
        environment={
            **_empty_live_command_env(),
            "AIDD_EVAL_CODEX_COMMAND": "/tmp/aidd-codex-wrapper",
        },
        scenario=_scenario(runtime_targets=("codex",)),
    )

    assert entries["codex"].execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert entries["codex"].command == "/tmp/aidd-codex-wrapper"
    assert entries["codex"].source == "environment"


def test_resolve_live_runtime_command_entries_uses_claude_env_override_as_adapter_flags() -> None:
    entries = resolve_live_runtime_command_entries(
        environment={
            **_empty_live_command_env(),
            "AIDD_EVAL_CLAUDE_CODE_COMMAND": "/tmp/aidd-claude-wrapper",
        },
        scenario=_scenario(runtime_targets=("claude-code",)),
    )

    assert entries["claude-code"].execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert entries["claude-code"].command == "/tmp/aidd-claude-wrapper"
    assert entries["claude-code"].source == "environment"


def test_write_live_runtime_config_records_native_modes(tmp_path: Path) -> None:
    config_path = write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex", "opencode")),
        environment=_empty_live_command_env(),
    )

    config_text = config_path.read_text(encoding="utf-8")
    assert "[runtime.claude_code]" in config_text
    assert (
        'command = "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"'
        in config_text
    )
    assert 'mode = "native"' in config_text
    assert "[runtime.codex]" in config_text
    assert 'command = "codex exec --full-auto --skip-git-repo-check --json -"' in config_text
    assert 'mode = "native"' in config_text
    assert "[runtime.opencode]" in config_text
    assert 'command = "opencode run --format json --dangerously-skip-permissions"' in config_text
    assert "timeout_seconds = 1200" in config_text
    assert config_text.count("timeout_seconds = 900") == 2
    assert "[runtime.claude_code.stage_timeouts]" in config_text
    assert "research = 1500" in config_text
    assert "implement = 1800" in config_text


def test_write_live_runtime_config_records_env_override_as_adapter_flags(
    tmp_path: Path,
) -> None:
    config_path = write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex",)),
        environment={
            **_empty_live_command_env(),
            "AIDD_EVAL_CODEX_COMMAND": "/tmp/aidd-codex-wrapper",
        },
    )

    config_text = config_path.read_text(encoding="utf-8")
    assert 'command = "/tmp/aidd-codex-wrapper"' in config_text
    assert 'mode = "adapter-flags"' in config_text


def test_validate_live_runtime_command_checks_native_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    codex.chmod(0o755)
    monkeypatch.setenv("PATH", "")

    entry = validate_live_runtime_command(
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex",)),
        environment={
            **_empty_live_command_env(),
            "PATH": bin_dir.as_posix(),
        },
    )

    assert entry.execution_mode is RuntimeExecutionMode.NATIVE


def test_validate_live_runtime_command_checks_claude_native_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    claude = bin_dir / "claude"
    claude.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    claude.chmod(0o755)
    monkeypatch.setenv("PATH", "")

    entry = validate_live_runtime_command(
        runtime_id="claude-code",
        scenario=_scenario(runtime_targets=("claude-code",)),
        environment={
            **_empty_live_command_env(),
            "PATH": bin_dir.as_posix(),
        },
    )

    assert entry.execution_mode is RuntimeExecutionMode.NATIVE
    assert entry.command.startswith("claude -p")


def test_validate_live_runtime_command_fails_before_repo_prep_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATH", "")

    with pytest.raises(RuntimeError, match="executable is not available"):
        validate_live_runtime_command(
            runtime_id="codex",
            scenario=_scenario(runtime_targets=("codex",)),
            environment=_empty_live_command_env(),
        )


def test_validate_live_runtime_command_rejects_default_generic_cli() -> None:
    with pytest.raises(RuntimeError, match="AIDD_EVAL_GENERIC_CLI_COMMAND"):
        validate_live_runtime_command(
            runtime_id="generic-cli",
            scenario=_scenario(runtime_targets=("generic-cli",)),
            environment=_empty_live_command_env(),
        )
