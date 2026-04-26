from __future__ import annotations

from pathlib import Path

from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.config import load_config


def test_load_config_defaults_codex_and_opencode_to_native(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")

    assert cfg.codex_command == "codex exec --full-auto --skip-git-repo-check --json -"
    assert cfg.codex_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.opencode_command == "opencode run --format json --dangerously-skip-permissions"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.NATIVE
    assert cfg.generic_cli_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.claude_code_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS


def test_load_config_upgrades_legacy_raw_provider_commands_to_native(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
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

    assert cfg.codex_command == "/tmp/aidd-codex-wrapper --profile live"
    assert cfg.codex_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS
    assert cfg.opencode_command == "/tmp/aidd-opencode-wrapper --profile live"
    assert cfg.opencode_execution_mode is RuntimeExecutionMode.ADAPTER_FLAGS

