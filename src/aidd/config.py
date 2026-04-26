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
        log_mode=log_mode,
        max_repair_attempts=max_repair_attempts,
    )
