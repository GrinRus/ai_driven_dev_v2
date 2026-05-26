from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from aidd.config import AiddConfig, RuntimeConfig, load_config
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimePermissionPolicy,
)


def _runtime_configs() -> dict[str, RuntimeConfig]:
    return {
        "generic-cli": RuntimeConfig(
            command="python",
            execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
            timeout_seconds=None,
            stage_timeout_seconds={},
        ),
        "claude-code": RuntimeConfig(
            command="claude",
            execution_mode=RuntimeExecutionMode.NATIVE,
            timeout_seconds=1200,
            stage_timeout_seconds={"research": 1500},
        ),
        "codex": RuntimeConfig(
            command="codex",
            execution_mode=RuntimeExecutionMode.NATIVE,
            timeout_seconds=900,
            stage_timeout_seconds={},
        ),
        "opencode": RuntimeConfig(
            command="opencode",
            execution_mode=RuntimeExecutionMode.NATIVE,
            timeout_seconds=900,
            stage_timeout_seconds={},
        ),
        "qwen": RuntimeConfig(
            command="qwen",
            execution_mode=RuntimeExecutionMode.NATIVE,
            timeout_seconds=900,
            stage_timeout_seconds={},
        ),
    }


def test_load_config_defaults_native_providers_to_native(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")

    assert (
        cfg.claude_code_command
        == "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
    )
    assert cfg.claude_code_execution_mode is RuntimeExecutionMode.NATIVE
    assert (
        cfg.codex_command
        == "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
    )
    assert cfg.codex_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.opencode_command == "opencode run --format json --dangerously-skip-permissions"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.qwen_command == "qwen --approval-mode yolo --output-format stream-json"
    assert cfg.qwen_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.generic_cli_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.claude_code_timeout_seconds is None
    assert cfg.codex_timeout_seconds is None
    assert cfg.opencode_timeout_seconds is None
    assert cfg.qwen_timeout_seconds is None
    assert cfg.claude_code_stage_timeout_seconds == {}
    assert cfg.codex_stage_timeout_seconds == {}
    assert cfg.opencode_stage_timeout_seconds == {}
    assert cfg.qwen_stage_timeout_seconds == {}
    assert cfg.project_set.projects == ()
    assert cfg.runtime_config("codex").permission_policy is RuntimePermissionPolicy.FULL_ACCESS
    assert cfg.runtime_config("codex").interaction_mode is RuntimeInteractionMode.BATCH
    assert cfg.runtime_config("codex").auto_approval_preset is AutoApprovalPreset.BROAD


def test_runtime_configs_are_primary_config_storage(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")

    field_names = {field.name for field in fields(AiddConfig)}
    assert "runtime_configs" in field_names
    assert "codex_command" not in field_names
    assert cfg.runtime_config("codex").command == cfg.codex_command
    assert cfg.runtime_config("codex").execution_mode is cfg.codex_execution_mode


def test_legacy_runtime_properties_are_read_only_map_shims() -> None:
    cfg = AiddConfig(
        workspace_root=Path(".aidd"),
        log_mode="both",
        max_repair_attempts=2,
        runtime_configs=_runtime_configs(),
    )

    assert cfg.claude_code_command == "claude"
    assert cfg.claude_code_stage_timeout_seconds == {"research": 1500}
    stage_timeout_copy = cfg.claude_code_stage_timeout_seconds
    stage_timeout_copy["qa"] = 10
    assert cfg.claude_code_stage_timeout_seconds == {"research": 1500}


def test_runtime_config_map_requires_all_supported_runtime_ids() -> None:
    runtime_configs = _runtime_configs()
    runtime_configs.pop("codex")

    try:
        AiddConfig(
            workspace_root=Path(".aidd"),
            log_mode="both",
            max_repair_attempts=2,
            runtime_configs=runtime_configs,
        )
    except ValueError as exc:
        assert "missing runtime configs: codex" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for incomplete runtime config map.")


def test_runtime_config_map_rejects_unknown_runtime_ids() -> None:
    runtime_configs = _runtime_configs()
    runtime_configs["unknown"] = RuntimeConfig(
        command="unknown",
        execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
        timeout_seconds=None,
        stage_timeout_seconds={},
    )

    try:
        AiddConfig(
            workspace_root=Path(".aidd"),
            log_mode="both",
            max_repair_attempts=2,
            runtime_configs=runtime_configs,
        )
    except ValueError as exc:
        assert "unknown runtime configs: unknown" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for unknown runtime config id.")


def test_load_config_upgrades_legacy_raw_provider_commands_to_native(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.claude_code]",
                'command = "claude"',
                "",
                "[runtime.codex]",
                'command = "codex"',
                "",
                "[runtime.opencode]",
                'command = "opencode"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert (
        cfg.claude_code_command
        == "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
    )
    assert cfg.claude_code_execution_mode is RuntimeExecutionMode.NATIVE
    assert (
        cfg.codex_command
        == "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
    )
    assert cfg.codex_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.opencode_command == "opencode run --format json --dangerously-skip-permissions"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.NATIVE


def test_load_config_parses_runtime_permission_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.codex]",
                'permission_policy = "brokered"',
                'interaction_mode = "live"',
                'auto_approval_preset = "conservative"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)
    runtime_config = cfg.runtime_config("codex")

    assert runtime_config.permission_policy is RuntimePermissionPolicy.BROKERED
    assert runtime_config.interaction_mode is RuntimeInteractionMode.LIVE
    assert runtime_config.auto_approval_preset is AutoApprovalPreset.CONSERVATIVE
    assert runtime_config.command == (
        "codex exec --sandbox workspace-write --skip-git-repo-check --json -"
    )


def test_brokered_config_rewrites_explicit_default_managed_command(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.codex]",
                'permission_policy = "brokered"',
                (
                    'command = "codex exec --dangerously-bypass-approvals-and-sandbox '
                    '--skip-git-repo-check --json -"'
                ),
                "",
                "[runtime.qwen]",
                'permission_policy = "brokered"',
                'command = "qwen --approval-mode yolo --output-format stream-json"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.runtime_config("codex").command == (
        "codex exec --sandbox workspace-write --skip-git-repo-check --json -"
    )
    assert cfg.runtime_config("qwen").command == (
        "qwen --approval-mode default --output-format stream-json"
    )
    assert cfg.runtime_config("codex").execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.runtime_config("qwen").execution_mode is RuntimeExecutionMode.NATIVE


def test_brokered_default_command_infers_native_mode_when_explicit(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.codex]",
                'permission_policy = "brokered"',
                'command = "codex exec --sandbox workspace-write --skip-git-repo-check --json -"',
                "",
                "[runtime.qwen]",
                'permission_policy = "brokered"',
                'command = "qwen --approval-mode default --output-format stream-json"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.runtime_config("codex").execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.runtime_config("qwen").execution_mode is RuntimeExecutionMode.NATIVE


def test_load_config_rejects_custom_bypass_command_in_brokered_mode(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.codex]",
                'permission_policy = "brokered"',
                'command = "codex exec --full-auto --json -"',
                "",
            )
        ),
        encoding="utf-8",
    )

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "permission-policy-conflict" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for brokered bypass command.")


def test_load_config_treats_custom_provider_commands_as_adapter_flags(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.claude_code]",
                'command = "/tmp/aidd-claude-wrapper --profile live"',
                "",
                "[runtime.codex]",
                'command = "/tmp/aidd-codex-wrapper --profile live"',
                "",
                "[runtime.opencode]",
                'command = "/tmp/aidd-opencode-wrapper --profile live"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.claude_code_command == "/tmp/aidd-claude-wrapper --profile live"
    assert cfg.claude_code_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.codex_command == "/tmp/aidd-codex-wrapper --profile live"
    assert cfg.codex_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.opencode_command == "/tmp/aidd-opencode-wrapper --profile live"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS


def test_load_config_parses_runtime_timeout_seconds(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.claude_code]",
                "timeout_seconds = 900",
                "",
                "[runtime.codex]",
                "timeout_seconds = 300.5",
                "",
                "[runtime.opencode]",
                "timeout_seconds = 120",
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.claude_code_timeout_seconds == 900
    assert cfg.codex_timeout_seconds == 300.5
    assert cfg.opencode_timeout_seconds == 120


def test_load_config_parses_stage_timeout_seconds(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.claude_code]",
                "timeout_seconds = 1200",
                "",
                "[runtime.claude_code.stage_timeouts]",
                "research = 1500",
                "implement = 1800",
                "",
                "[runtime.codex.stage_timeouts]",
                "plan = 900",
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert cfg.claude_code_timeout_seconds == 1200
    assert cfg.claude_code_stage_timeout_seconds == {
        "research": 1500,
        "implement": 1800,
    }
    assert cfg.codex_stage_timeout_seconds == {"plan": 900}


def test_load_config_rejects_non_positive_runtime_timeout_seconds(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(("[runtime.claude_code]", "timeout_seconds = 0")),
        encoding="utf-8",
    )

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "timeout_seconds must be greater than zero" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for non-positive timeout_seconds")


def test_load_config_rejects_invalid_stage_timeout_key(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(("[runtime.codex.stage_timeouts]", "unknown = 10")),
        encoding="utf-8",
    )

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "unknown stage" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for invalid stage timeout.")


def test_load_config_parses_project_set_projects(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[[project_set.projects]]",
                'id = "api"',
                'root = "services/api"',
                'role = "primary"',
                "",
                "[[project_set.projects]]",
                'id = "web"',
                'root = "apps/web"',
                "",
            )
        ),
        encoding="utf-8",
    )

    cfg = load_config(config_path)

    assert tuple(project.id for project in cfg.project_set.projects) == ("api", "web")
    assert cfg.project_set.projects[0].root == Path("services/api")
    assert cfg.project_set.projects[0].role == "primary"
    assert cfg.project_set.projects[1].role is None


def test_load_config_rejects_duplicate_project_set_ids(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[[project_set.projects]]",
                'id = "api"',
                'root = "services/api"',
                "",
                "[[project_set.projects]]",
                'id = "api"',
                'root = "services/api-copy"',
                "",
            )
        ),
        encoding="utf-8",
    )

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "Duplicate project_set project id: api" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for duplicate project id.")


def test_load_config_rejects_project_set_missing_required_fields(tmp_path: Path) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(("[[project_set.projects]]", 'id = "api"')),
        encoding="utf-8",
    )

    try:
        load_config(config_path)
    except ValueError as exc:
        assert "project_set.projects[1].root is required" in str(exc)
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("Expected ValueError for missing project root.")
