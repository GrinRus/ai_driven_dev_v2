from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Mapping
from pathlib import Path

from aidd.core.contracts import repo_root_from
from aidd.harness.scenarios import Scenario

_DEFAULT_RUNTIME_COMMANDS: dict[str, str] = {
    "generic-cli": "python",
    "claude-code": "claude",
    "codex": "codex",
    "opencode": "opencode",
}

_RUNTIME_COMMAND_ENV_VARS: dict[str, str] = {
    "generic-cli": "AIDD_EVAL_GENERIC_CLI_COMMAND",
    "claude-code": "AIDD_EVAL_CLAUDE_CODE_COMMAND",
    "codex": "AIDD_EVAL_CODEX_COMMAND",
    "opencode": "AIDD_EVAL_OPENCODE_COMMAND",
}


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _aidd_repository_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _release_proof_generic_cli_command(*, scenario: Scenario | None) -> str | None:
    if scenario is None:
        return None
    workflow_bundle = scenario.raw.get("workflow_bundle")
    if not isinstance(workflow_bundle, dict):
        return None
    if str(workflow_bundle.get("release_proof_runtime", "")).strip() != "generic-cli":
        return None

    helper_path = _aidd_repository_root() / "scripts" / "release_live_proof_runtime.py"
    if not helper_path.exists():
        return None

    return shlex.join((sys.executable, helper_path.as_posix()))


def resolve_live_runtime_commands(
    *,
    environment: Mapping[str, str] | None = None,
    scenario: Scenario | None = None,
) -> dict[str, str]:
    source = dict(os.environ)
    if environment is not None:
        source.update(environment)

    release_proof_command = _release_proof_generic_cli_command(scenario=scenario)
    commands: dict[str, str] = {}
    for runtime_id, default_command in _DEFAULT_RUNTIME_COMMANDS.items():
        command_env = _RUNTIME_COMMAND_ENV_VARS[runtime_id]
        command_value = source.get(command_env, "").strip()
        if not command_value and runtime_id == "generic-cli" and release_proof_command is not None:
            command_value = release_proof_command
        if not command_value:
            command_value = default_command
        commands[runtime_id] = command_value
    return commands


def write_live_runtime_config(
    *,
    working_copy_path: Path,
    runtime_id: str,
    scenario: Scenario,
    environment: Mapping[str, str] | None = None,
) -> Path:
    source = dict(os.environ)
    if environment is not None:
        source.update(environment)

    generic_cli_override = source.get(_RUNTIME_COMMAND_ENV_VARS["generic-cli"], "").strip()
    generic_cli_release_proof = _release_proof_generic_cli_command(scenario=scenario)
    if (
        runtime_id == "generic-cli"
        and not generic_cli_override
        and generic_cli_release_proof is None
    ):
        raise RuntimeError(
            "Live generic-cli eval requires `AIDD_EVAL_GENERIC_CLI_COMMAND` unless the "
            "selected scenario declares a built-in generic-cli release-proof helper."
        )

    runtime_commands = resolve_live_runtime_commands(
        environment=environment,
        scenario=scenario,
    )
    config_path = working_copy_path / "aidd.example.toml"
    config_path.write_text(
        "\n".join(
            (
                "[workspace]",
                'root = ".aidd"',
                "",
                "[runtime.generic_cli]",
                f"command = {_toml_string(runtime_commands['generic-cli'])}",
                "",
                "[runtime.claude_code]",
                f"command = {_toml_string(runtime_commands['claude-code'])}",
                "",
                "[runtime.codex]",
                f"command = {_toml_string(runtime_commands['codex'])}",
                "",
                "[runtime.opencode]",
                f"command = {_toml_string(runtime_commands['opencode'])}",
                "",
                "[logging]",
                'mode = "both"',
                "",
                "[repair]",
                "max_attempts = 2",
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path


__all__ = [
    "resolve_live_runtime_commands",
    "write_live_runtime_config",
]
