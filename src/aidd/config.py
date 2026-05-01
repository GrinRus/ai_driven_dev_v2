from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.adapters.runtime_registry import (
    RuntimeExecutionMode,
    get_runtime_definition,
    normalize_execution_mode,
)
from aidd.core.stages import STAGES, is_valid_stage


@dataclass(frozen=True)
class AiddConfig:
    workspace_root: Path
    generic_cli_command: str
    claude_code_command: str
    codex_command: str
    opencode_command: str
    generic_cli_execution_mode: RuntimeExecutionMode
    claude_code_execution_mode: RuntimeExecutionMode
    codex_execution_mode: RuntimeExecutionMode
    opencode_execution_mode: RuntimeExecutionMode
    generic_cli_timeout_seconds: float | None
    claude_code_timeout_seconds: float | None
    codex_timeout_seconds: float | None
    opencode_timeout_seconds: float | None
    generic_cli_stage_timeout_seconds: dict[str, float]
    claude_code_stage_timeout_seconds: dict[str, float]
    codex_stage_timeout_seconds: dict[str, float]
    opencode_stage_timeout_seconds: dict[str, float]
    log_mode: str
    max_repair_attempts: int


def _runtime_section(data: dict[str, Any], runtime_id: str) -> dict[str, Any]:
    definition = get_runtime_definition(runtime_id)
    raw_section = data.get("runtime", {}).get(definition.config_section, {})
    return raw_section if isinstance(raw_section, dict) else {}


def _runtime_command(data: dict[str, Any], runtime_id: str) -> str:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    command = str(section.get("command", definition.default_command)).strip()
    if (
        "mode" not in section
        and command == definition.probe_command
        and definition.default_execution_mode is RuntimeExecutionMode.NATIVE
    ):
        return definition.default_command
    return command or definition.default_command


def _runtime_execution_mode(data: dict[str, Any], runtime_id: str) -> RuntimeExecutionMode:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    if "mode" in section:
        return normalize_execution_mode(runtime_id=runtime_id, value=str(section["mode"]))

    command = str(section.get("command", "")).strip()
    if (
        command
        and command != definition.default_command
        and command != definition.probe_command
        and RuntimeExecutionMode.ADAPTER_FLAGS in definition.supported_execution_modes
    ):
        return RuntimeExecutionMode.ADAPTER_FLAGS
    return definition.default_execution_mode


def _runtime_timeout_seconds(data: dict[str, Any], runtime_id: str) -> float | None:
    section = _runtime_section(data, runtime_id)
    raw_value = section.get("timeout_seconds")
    if raw_value is None:
        return None
    try:
        timeout_seconds = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"[runtime.{get_runtime_definition(runtime_id).config_section}] "
            "timeout_seconds must be a number when provided."
        ) from exc
    if timeout_seconds <= 0:
        raise ValueError(
            f"[runtime.{get_runtime_definition(runtime_id).config_section}] "
            "timeout_seconds must be greater than zero when provided."
        )
    return timeout_seconds


def _runtime_stage_timeout_seconds(data: dict[str, Any], runtime_id: str) -> dict[str, float]:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_stage_timeouts = section.get("stage_timeouts", {})
    if raw_stage_timeouts is None:
        return {}
    if not isinstance(raw_stage_timeouts, dict):
        raise ValueError(
            f"[runtime.{definition.config_section}.stage_timeouts] "
            "must be a table when provided."
        )

    stage_timeouts: dict[str, float] = {}
    for raw_stage, raw_value in raw_stage_timeouts.items():
        stage = str(raw_stage).strip()
        if not is_valid_stage(stage):
            expected = ", ".join(STAGES)
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts] "
                f"unknown stage {stage!r}. Expected one of: {expected}."
            )
        try:
            timeout_seconds = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts.{stage}] "
                "timeout must be a number when provided."
            ) from exc
        if timeout_seconds <= 0:
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts.{stage}] "
                "timeout must be greater than zero when provided."
            )
        stage_timeouts[stage] = timeout_seconds
    return stage_timeouts


def load_config(path: Path) -> AiddConfig:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    workspace_root = Path(data.get("workspace", {}).get("root", ".aidd"))
    generic_cli_command = _runtime_command(data, "generic-cli")
    claude_code_command = _runtime_command(data, "claude-code")
    codex_command = _runtime_command(data, "codex")
    opencode_command = _runtime_command(data, "opencode")
    generic_cli_execution_mode = _runtime_execution_mode(data, "generic-cli")
    claude_code_execution_mode = _runtime_execution_mode(data, "claude-code")
    codex_execution_mode = _runtime_execution_mode(data, "codex")
    opencode_execution_mode = _runtime_execution_mode(data, "opencode")
    generic_cli_timeout_seconds = _runtime_timeout_seconds(data, "generic-cli")
    claude_code_timeout_seconds = _runtime_timeout_seconds(data, "claude-code")
    codex_timeout_seconds = _runtime_timeout_seconds(data, "codex")
    opencode_timeout_seconds = _runtime_timeout_seconds(data, "opencode")
    generic_cli_stage_timeout_seconds = _runtime_stage_timeout_seconds(data, "generic-cli")
    claude_code_stage_timeout_seconds = _runtime_stage_timeout_seconds(data, "claude-code")
    codex_stage_timeout_seconds = _runtime_stage_timeout_seconds(data, "codex")
    opencode_stage_timeout_seconds = _runtime_stage_timeout_seconds(data, "opencode")
    log_mode = data.get("logging", {}).get("mode", "both")
    max_repair_attempts = int(data.get("repair", {}).get("max_attempts", 2))

    return AiddConfig(
        workspace_root=workspace_root,
        generic_cli_command=generic_cli_command,
        claude_code_command=claude_code_command,
        codex_command=codex_command,
        opencode_command=opencode_command,
        generic_cli_execution_mode=generic_cli_execution_mode,
        claude_code_execution_mode=claude_code_execution_mode,
        codex_execution_mode=codex_execution_mode,
        opencode_execution_mode=opencode_execution_mode,
        generic_cli_timeout_seconds=generic_cli_timeout_seconds,
        claude_code_timeout_seconds=claude_code_timeout_seconds,
        codex_timeout_seconds=codex_timeout_seconds,
        opencode_timeout_seconds=opencode_timeout_seconds,
        generic_cli_stage_timeout_seconds=generic_cli_stage_timeout_seconds,
        claude_code_stage_timeout_seconds=claude_code_stage_timeout_seconds,
        codex_stage_timeout_seconds=codex_stage_timeout_seconds,
        opencode_stage_timeout_seconds=opencode_stage_timeout_seconds,
        log_mode=log_mode,
        max_repair_attempts=max_repair_attempts,
    )
