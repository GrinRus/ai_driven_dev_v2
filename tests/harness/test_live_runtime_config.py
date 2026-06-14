from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

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
    ScenarioRepoSource,
    ScenarioRunConfig,
)
from aidd.runtime_catalog import RuntimeExecutionMode


def _empty_live_command_env() -> dict[str, str]:
    return {
        "AIDD_EVAL_CLAUDE_CODE_COMMAND": "",
        "AIDD_EVAL_CODEX_COMMAND": "",
        "AIDD_EVAL_OPENCODE_COMMAND": "",
        "AIDD_EVAL_QWEN_COMMAND": "",
    }


def _fake_codex_bin_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then exit 0; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    return {"PATH": bin_dir.as_posix()}


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
    )

    assert entries["codex"].execution_mode is RuntimeExecutionMode.NATIVE
    assert entries["codex"].command.startswith("codex exec")
    assert entries["codex"].source == "default-native"


def test_resolve_live_runtime_command_entries_defaults_claude_code_to_native() -> None:
    entries = resolve_live_runtime_command_entries(
        environment=_empty_live_command_env(),
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
    )

    assert entries["claude-code"].execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert entries["claude-code"].command == "/tmp/aidd-claude-wrapper"
    assert entries["claude-code"].source == "environment"


def test_resolve_live_runtime_command_entries_defaults_qwen_to_native() -> None:
    entries = resolve_live_runtime_command_entries(
        environment=_empty_live_command_env(),
    )

    assert entries["qwen"].execution_mode is RuntimeExecutionMode.NATIVE
    assert entries["qwen"].command.startswith("qwen --approval-mode yolo")
    assert entries["qwen"].source == "default-native"


def test_resolve_live_runtime_command_entries_uses_qwen_env_override_as_adapter_flags() -> None:
    entries = resolve_live_runtime_command_entries(
        environment={
            **_empty_live_command_env(),
            "AIDD_EVAL_QWEN_COMMAND": "/tmp/aidd-qwen-wrapper",
        },
    )

    assert entries["qwen"].execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert entries["qwen"].command == "/tmp/aidd-qwen-wrapper"
    assert entries["qwen"].source == "environment"


def test_write_live_runtime_config_records_native_modes(tmp_path: Path) -> None:
    config_path = write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex", "opencode")),
        environment={
            **_empty_live_command_env(),
            **_fake_codex_bin_env(tmp_path),
        },
    )

    config_text = config_path.read_text(encoding="utf-8")
    assert "[runtime.claude_code]" in config_text
    assert (
        'command = "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"'
        in config_text
    )
    assert 'mode = "native"' in config_text
    assert "[runtime.codex]" in config_text
    assert (
        'command = "codex exec --dangerously-bypass-approvals-and-sandbox '
        '--skip-git-repo-check --json -"'
        in config_text
    )
    assert 'mode = "native"' in config_text
    assert "[runtime.opencode]" in config_text
    assert 'command = "opencode run --format json --dangerously-skip-permissions"' in config_text
    assert "[runtime.qwen]" in config_text
    assert 'command = "qwen --approval-mode yolo --output-format stream-json"' in config_text
    assert "[runtime.generic_cli]" not in config_text
    assert config_text.count("timeout_seconds = 1200") == 2
    assert "[runtime.claude_code.stage_timeouts]" in config_text
    config = tomllib.loads(config_text)
    claude_stage_timeouts = config["runtime"]["claude_code"]["stage_timeouts"]
    assert claude_stage_timeouts["idea"] == 1500
    assert claude_stage_timeouts["research"] == 1500
    assert claude_stage_timeouts["plan"] == 1500
    assert claude_stage_timeouts["review-spec"] == 1500
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
    assert config["runtime"]["qwen"]["timeout_seconds"] == 1800
    assert config["runtime"]["qwen"]["stage_timeouts"] == codex_stage_timeouts


def test_write_live_runtime_config_records_env_override_as_adapter_flags(
    tmp_path: Path,
) -> None:
    wrapper = tmp_path / "aidd-codex-wrapper"
    wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    wrapper.chmod(0o755)
    config_path = write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex",)),
        environment={
            **_empty_live_command_env(),
            "AIDD_EVAL_CODEX_COMMAND": wrapper.as_posix(),
        },
    )

    config_text = config_path.read_text(encoding="utf-8")
    assert f'command = "{wrapper.as_posix()}"' in config_text
    assert 'mode = "adapter-flags"' in config_text


def test_write_live_runtime_config_preserves_real_runtime_defaults(tmp_path: Path) -> None:
    config_path = write_live_runtime_config(
        working_copy_path=tmp_path,
        runtime_id="codex",
        scenario=_scenario(runtime_targets=("codex",)),
        environment={
            **_empty_live_command_env(),
            **_fake_codex_bin_env(tmp_path),
        },
    )

    config = tomllib.loads(config_path.read_text(encoding="utf-8"))

    assert "permission_policy" not in config["runtime"]["codex"]
    assert (
        config["runtime"]["codex"]["command"]
        == "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
    )


def test_validate_live_runtime_command_checks_native_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then exit 0; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
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


def test_validate_live_runtime_command_rejects_codex_native_auth_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'not logged in' >&2\n"
        "  exit 7\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.setenv("PATH", "")

    with pytest.raises(RuntimeError, match="provider-auth blocker"):
        validate_live_runtime_command(
            runtime_id="codex",
            scenario=_scenario(runtime_targets=("codex",)),
            environment={
                **_empty_live_command_env(),
                "PATH": bin_dir.as_posix(),
            },
        )


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


def test_validate_live_runtime_command_checks_qwen_native_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    qwen = bin_dir / "qwen"
    qwen.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    qwen.chmod(0o755)
    monkeypatch.setenv("PATH", "")

    entry = validate_live_runtime_command(
        runtime_id="qwen",
        scenario=_scenario(runtime_targets=("qwen",)),
        environment={
            **_empty_live_command_env(),
            "PATH": bin_dir.as_posix(),
        },
    )

    assert entry.execution_mode is RuntimeExecutionMode.NATIVE
    assert entry.command.startswith("qwen --approval-mode yolo")


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


def test_validate_live_runtime_command_rejects_generic_cli_for_live() -> None:
    with pytest.raises(RuntimeError, match="supported live runtimes"):
        validate_live_runtime_command(
            runtime_id="generic-cli",
            scenario=_scenario(runtime_targets=("generic-cli",)),
            environment=_empty_live_command_env(),
        )
