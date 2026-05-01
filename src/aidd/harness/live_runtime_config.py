from __future__ import annotations

import os
import shlex
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from aidd.adapters.runtime_registry import (
    RuntimeExecutionMode,
    get_runtime_definition,
    runtime_definitions,
)
from aidd.core.contracts import repo_root_from
from aidd.harness.scenarios import Scenario


@dataclass(frozen=True, slots=True)
class LiveRuntimeCommand:
    runtime_id: str
    command: str
    execution_mode: RuntimeExecutionMode
    source: str
    env_var: str | None = None


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
    return {
        runtime_id: entry.command
        for runtime_id, entry in resolve_live_runtime_command_entries(
            environment=environment,
            scenario=scenario,
        ).items()
    }


def resolve_live_runtime_command_entries(
    *,
    environment: Mapping[str, str] | None = None,
    scenario: Scenario | None = None,
) -> dict[str, LiveRuntimeCommand]:
    source = dict(os.environ)
    if environment is not None:
        source.update(environment)

    release_proof_command = _release_proof_generic_cli_command(scenario=scenario)
    entries: dict[str, LiveRuntimeCommand] = {}
    for definition in runtime_definitions():
        command_env = definition.live_command_env_var
        command_value = source.get(command_env, "").strip() if command_env is not None else ""
        env_var: str | None = command_env if command_value else None
        execution_mode = definition.default_execution_mode
        command_source = "default-native"
        if command_value:
            execution_mode = RuntimeExecutionMode.ADAPTER_FLAGS
            command_source = "environment"
        elif (
            definition.runtime_id == "generic-cli"
            and release_proof_command is not None
        ):
            command_value = release_proof_command
            execution_mode = RuntimeExecutionMode.ADAPTER_FLAGS
            command_source = "release-proof-helper"
        if not command_value:
            command_value = definition.default_command
            command_source = (
                "default-native"
                if execution_mode is RuntimeExecutionMode.NATIVE
                else "default"
            )
        entries[definition.runtime_id] = LiveRuntimeCommand(
            runtime_id=definition.runtime_id,
            command=command_value,
            execution_mode=execution_mode,
            source=command_source,
            env_var=env_var,
        )
    return entries


def validate_live_runtime_command(
    *,
    runtime_id: str,
    scenario: Scenario,
    environment: Mapping[str, str] | None = None,
) -> LiveRuntimeCommand:
    source = dict(os.environ)
    if environment is not None:
        source.update(environment)

    if runtime_id not in scenario.runtime_targets:
        supported = ", ".join(scenario.runtime_targets)
        raise RuntimeError(
            f"Runtime '{runtime_id}' is not allowed by scenario '{scenario.scenario_id}'. "
            f"Supported runtime targets: {supported}."
        )
    try:
        command_entry = resolve_live_runtime_command_entries(
            environment=environment,
            scenario=scenario,
        )[runtime_id]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported live runtime: {runtime_id}") from exc

    if runtime_id == "generic-cli" and command_entry.source == "default":
        raise RuntimeError(
            "Live generic-cli eval requires `AIDD_EVAL_GENERIC_CLI_COMMAND` unless the "
            "selected scenario declares a built-in generic-cli release-proof helper."
        )

    try:
        tokens = shlex.split(command_entry.command)
    except ValueError as exc:
        raise RuntimeError(
            f"Live runtime command for {runtime_id} is not valid shell syntax: "
            f"{command_entry.command!r}"
        ) from exc
    if not tokens:
        raise RuntimeError(f"Live runtime command for {runtime_id} must not be empty.")
    if shutil.which(tokens[0], path=source.get("PATH")) is None:
        mode_hint = command_entry.execution_mode.value
        raise RuntimeError(
            f"Live runtime command executable is not available for {runtime_id}: "
            f"{tokens[0]!r} (mode={mode_hint}, source={command_entry.source})."
        )
    return command_entry


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

    generic_cli_definition = get_runtime_definition("generic-cli")
    generic_cli_env_var = generic_cli_definition.live_command_env_var
    generic_cli_override = (
        source.get(generic_cli_env_var, "").strip()
        if generic_cli_env_var is not None
        else ""
    )
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

    runtime_entries = resolve_live_runtime_command_entries(
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
                f"command = {_toml_string(runtime_entries['generic-cli'].command)}",
                f"mode = {_toml_string(runtime_entries['generic-cli'].execution_mode.value)}",
                "",
                "[runtime.claude_code]",
                f"command = {_toml_string(runtime_entries['claude-code'].command)}",
                f"mode = {_toml_string(runtime_entries['claude-code'].execution_mode.value)}",
                "timeout_seconds = 1200",
                "",
                "[runtime.claude_code.stage_timeouts]",
                "research = 1500",
                "implement = 1800",
                "",
                "[runtime.codex]",
                f"command = {_toml_string(runtime_entries['codex'].command)}",
                f"mode = {_toml_string(runtime_entries['codex'].execution_mode.value)}",
                "timeout_seconds = 900",
                "",
                "[runtime.opencode]",
                f"command = {_toml_string(runtime_entries['opencode'].command)}",
                f"mode = {_toml_string(runtime_entries['opencode'].execution_mode.value)}",
                "timeout_seconds = 900",
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
    "LiveRuntimeCommand",
    "resolve_live_runtime_command_entries",
    "resolve_live_runtime_commands",
    "validate_live_runtime_command",
    "write_live_runtime_config",
]
