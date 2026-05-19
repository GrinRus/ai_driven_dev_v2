from __future__ import annotations

import tomllib
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
    ScenarioAuthoredTask,
    ScenarioCommandSteps,
    ScenarioFeatureSource,
    ScenarioLiveFlowConfig,
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


def _scenario(
    *,
    runtime_targets: tuple[str, ...] = ("codex", "opencode"),
    raw: dict[str, object] | None = None,
) -> Scenario:
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
            mode="authored-task-pool",
            selection_policy="first-listed",
            tasks=(
                ScenarioAuthoredTask(
                    task_id="TASK-123",
                    title="task",
                    summary="task",
                    intent="exercise runtime config",
                    target_change="write config",
                    expected_scope="test helper only",
                    acceptance_criteria=("config is written",),
                    verification=("true",),
                    quality_bar="config remains valid",
                    size_rationale="small test helper",
                    interview=tuple(),
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
        live_flow=ScenarioLiveFlowConfig(
            driver="stepwise-black-box",
            checkpoint_policy="after-each-step",
            answer_policy="agent-decides",
            frontend_checkpoints=True,
        ),
        runtime_targets=runtime_targets,
        is_live=True,
        raw={} if raw is None else raw,
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
    assert config_text.count("timeout_seconds = 1200") == 2
    assert "[runtime.claude_code.stage_timeouts]" in config_text
    config = tomllib.loads(config_text)
    claude_stage_timeouts = config["runtime"]["claude_code"]["stage_timeouts"]
    assert claude_stage_timeouts["idea"] == 1500
    assert claude_stage_timeouts["research"] == 1500
    assert claude_stage_timeouts["tasklist"] == 1800
    assert claude_stage_timeouts["implement"] == 1800
    assert claude_stage_timeouts["review"] == 1800
    assert claude_stage_timeouts["qa"] == 1800
    assert config["runtime"]["codex"]["timeout_seconds"] == 1800
    codex_stage_timeouts = config["runtime"]["codex"]["stage_timeouts"]
    assert codex_stage_timeouts == {
        "idea": 1800,
        "research": 2400,
        "plan": 1800,
        "review-spec": 1800,
        "tasklist": 2400,
        "implement": 2400,
        "review": 1800,
        "qa": 1800,
    }
    assert "[runtime.opencode.stage_timeouts]" in config_text
    assert "idea = 1500" in config_text
    assert "plan = 1500" in config_text
    assert "review-spec = 1500" in config_text


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


def test_release_proof_helper_uses_explicit_source_repository_root(tmp_path: Path) -> None:
    source_root = tmp_path / "aidd-source"
    helper_path = source_root / "scripts" / "release_live_proof_runtime.py"
    helper_path.parent.mkdir(parents=True)
    helper_path.write_text("print('ok')\n", encoding="utf-8")
    scenario = _scenario(
        runtime_targets=("generic-cli",),
        raw={"workflow_bundle": {"release_proof_runtime": "generic-cli"}},
    )

    entries = resolve_live_runtime_command_entries(
        environment=_empty_live_command_env(),
        scenario=scenario,
        source_repository_root=source_root,
    )

    assert entries["generic-cli"].source == "release-proof-helper"
    assert entries["generic-cli"].execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert helper_path.as_posix() in entries["generic-cli"].command
