from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.scenarios import Scenario
from aidd.runtime_catalog import (
    RuntimeExecutionMode,
    get_runtime_definition,
)


@dataclass(frozen=True, slots=True)
class LiveRuntimeCommand:
    runtime_id: str
    command: str
    execution_mode: RuntimeExecutionMode
    source: str
    env_var: str | None = None


_PROVIDER_AUTH_CHECK_TIMEOUT_SECONDS = 10
LIVE_E2E_RUNTIME_ALLOWLIST = ("codex", "opencode", "claude-code", "qwen")
LIVE_E2E_PROVIDER_TIMEOUT_SECONDS = 3600
LIVE_E2E_STAGE_TIMEOUT_SECONDS = 3600
LIVE_E2E_CODEX_MODEL = "gpt-5.5"
LIVE_E2E_CODEX_REASONING_EFFORT = "xhigh"
LIVE_E2E_RUNTIME_COMMAND_ENV_VARS = {
    "claude-code": "AIDD_EVAL_CLAUDE_CODE_COMMAND",
    "codex": "AIDD_EVAL_CODEX_COMMAND",
    "opencode": "AIDD_EVAL_OPENCODE_COMMAND",
    "qwen": "AIDD_EVAL_QWEN_COMMAND",
}


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _default_live_native_command(*, runtime_id: str) -> str:
    definition = get_runtime_definition(runtime_id)
    if runtime_id != "codex":
        return definition.default_command

    command_tokens = shlex.split(definition.default_command)
    if not command_tokens or command_tokens[-1] != "-":
        raise ValueError(
            "The native Codex default command must end with the stdin prompt marker '-'."
        )
    return shlex.join(
        (
            *command_tokens[:-1],
            "--model",
            LIVE_E2E_CODEX_MODEL,
            "--config",
            f'model_reasoning_effort="{LIVE_E2E_CODEX_REASONING_EFFORT}"',
            command_tokens[-1],
        )
    )


def resolve_live_runtime_commands(
    *,
    environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    return {
        runtime_id: entry.command
        for runtime_id, entry in resolve_live_runtime_command_entries(
            environment=environment,
        ).items()
    }


def resolve_live_runtime_command_entries(
    *,
    environment: Mapping[str, str] | None = None,
) -> dict[str, LiveRuntimeCommand]:
    source = dict(os.environ)
    if environment is not None:
        source.update(environment)

    entries: dict[str, LiveRuntimeCommand] = {}
    for runtime_id in LIVE_E2E_RUNTIME_ALLOWLIST:
        definition = get_runtime_definition(runtime_id)
        command_env = LIVE_E2E_RUNTIME_COMMAND_ENV_VARS.get(runtime_id)
        command_value = source.get(command_env, "").strip() if command_env is not None else ""
        env_var: str | None = command_env if command_value else None
        execution_mode = definition.default_execution_mode
        command_source = "default-native"
        if command_value:
            execution_mode = RuntimeExecutionMode.ADAPTER_FLAGS
            command_source = "environment"
        if not command_value:
            command_value = _default_live_native_command(runtime_id=runtime_id)
            command_source = (
                "default-native"
                if execution_mode is RuntimeExecutionMode.NATIVE
                else "default"
            )
        entries[runtime_id] = LiveRuntimeCommand(
            runtime_id=runtime_id,
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

    if runtime_id not in LIVE_E2E_RUNTIME_ALLOWLIST:
        allowed = ", ".join(LIVE_E2E_RUNTIME_ALLOWLIST)
        raise RuntimeError(
            f"Unsupported live runtime: {runtime_id}. Black-box live E2E allows "
            f"only supported live runtimes: {allowed}."
        )
    if runtime_id not in scenario.runtime_targets:
        supported = ", ".join(scenario.runtime_targets)
        raise RuntimeError(
            f"Runtime '{runtime_id}' is not allowed by scenario '{scenario.scenario_id}'. "
            f"Supported runtime targets: {supported}."
        )
    try:
        command_entry = resolve_live_runtime_command_entries(
            environment=environment,
        )[runtime_id]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported live runtime: {runtime_id}") from exc

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
    _validate_provider_auth_for_native_live_runtime(
        runtime_id=runtime_id,
        command_entry=command_entry,
        source=source,
        executable=tokens[0],
    )
    return command_entry


def _validate_provider_auth_for_native_live_runtime(
    *,
    runtime_id: str,
    command_entry: LiveRuntimeCommand,
    source: Mapping[str, str],
    executable: str,
) -> None:
    if (
        runtime_id != "codex"
        or command_entry.execution_mode is not RuntimeExecutionMode.NATIVE
    ):
        return

    check_command = [executable, "login", "status"]
    try:
        completed = subprocess.run(
            check_command,
            env=dict(source),
            capture_output=True,
            text=True,
            check=False,
            timeout=_PROVIDER_AUTH_CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            "Live runtime provider auth check failed for codex: "
            "`codex login status` timed out. provider-auth readiness is unknown."
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            "Live runtime provider auth check failed for codex: "
            f"could not run `codex login status`: {exc}."
        ) from exc

    if completed.returncode == 0:
        return

    output = (completed.stderr or completed.stdout or "no command output").strip()
    raise RuntimeError(
        "Live runtime provider auth check failed for codex: "
        f"`codex login status` exited {completed.returncode}. "
        f"provider-auth blocker: {output}"
    )


def write_live_runtime_config(
    *,
    working_copy_path: Path,
    runtime_id: str,
    scenario: Scenario,
    environment: Mapping[str, str] | None = None,
) -> Path:
    validate_live_runtime_command(
        runtime_id=runtime_id,
        scenario=scenario,
        environment=environment,
    )

    runtime_entries = resolve_live_runtime_command_entries(
        environment=environment,
    )

    def _runtime_command(runtime_key: str) -> str:
        entry = runtime_entries[runtime_key]
        return entry.command

    config_path = working_copy_path / "aidd.example.toml"
    config_path.write_text(
        "\n".join(
            (
                "[workspace]",
                'root = ".aidd"',
                "",
                "[runtime.claude_code]",
                f"command = {_toml_string(_runtime_command('claude-code'))}",
                f"mode = {_toml_string(runtime_entries['claude-code'].execution_mode.value)}",
                f"timeout_seconds = {LIVE_E2E_PROVIDER_TIMEOUT_SECONDS}",
                "",
                "[runtime.claude_code.stage_timeouts]",
                f"idea = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"research = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"plan = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review-spec = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"tasklist = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"implement = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"qa = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                "",
                "[runtime.codex]",
                f"command = {_toml_string(_runtime_command('codex'))}",
                f"mode = {_toml_string(runtime_entries['codex'].execution_mode.value)}",
                f"timeout_seconds = {LIVE_E2E_PROVIDER_TIMEOUT_SECONDS}",
                "",
                "[runtime.codex.stage_timeouts]",
                f"idea = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"research = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"plan = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review-spec = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"tasklist = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"implement = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"qa = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                "",
                "[runtime.opencode]",
                f"command = {_toml_string(_runtime_command('opencode'))}",
                f"mode = {_toml_string(runtime_entries['opencode'].execution_mode.value)}",
                f"timeout_seconds = {LIVE_E2E_PROVIDER_TIMEOUT_SECONDS}",
                "",
                "[runtime.opencode.stage_timeouts]",
                f"idea = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"research = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"plan = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review-spec = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"tasklist = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"implement = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"qa = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                "",
                "[runtime.qwen]",
                f"command = {_toml_string(_runtime_command('qwen'))}",
                f"mode = {_toml_string(runtime_entries['qwen'].execution_mode.value)}",
                f"timeout_seconds = {LIVE_E2E_PROVIDER_TIMEOUT_SECONDS}",
                "",
                "[runtime.qwen.stage_timeouts]",
                f"idea = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"research = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"plan = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review-spec = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"tasklist = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"implement = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"review = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
                f"qa = {LIVE_E2E_STAGE_TIMEOUT_SECONDS}",
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
