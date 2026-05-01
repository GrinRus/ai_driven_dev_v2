from __future__ import annotations

from pathlib import Path

from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.config import load_config


def test_load_config_defaults_native_providers_to_native(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")

    assert (
        cfg.claude_code_command
        == "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
    )
    assert cfg.claude_code_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.codex_command == "codex exec --full-auto --skip-git-repo-check --json -"
    assert cfg.codex_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.opencode_command == "opencode run --format json --dangerously-skip-permissions"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.generic_cli_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.claude_code_timeout_seconds is None
    assert cfg.codex_timeout_seconds is None
    assert cfg.opencode_timeout_seconds is None
    assert cfg.claude_code_stage_timeout_seconds == {}
    assert cfg.codex_stage_timeout_seconds == {}
    assert cfg.opencode_stage_timeout_seconds == {}


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
    assert cfg.codex_command == "codex exec --full-auto --skip-git-repo-check --json -"
    assert cfg.codex_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.opencode_command == "opencode run --format json --dangerously-skip-permissions"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.NATIVE


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
