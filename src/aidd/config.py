from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AiddConfig:
    workspace_root: Path
    generic_cli_command: str
    claude_code_command: str
    codex_command: str
    opencode_command: str
    pi_mono_command: str
    log_mode: str
    max_repair_attempts: int


def load_config(path: Path) -> AiddConfig:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    workspace_root = Path(data.get("workspace", {}).get("root", ".aidd"))
    generic_cli_command = data.get("runtime", {}).get("generic_cli", {}).get("command", "python")
    claude_code_command = data.get("runtime", {}).get("claude_code", {}).get("command", "claude")
    codex_command = data.get("runtime", {}).get("codex", {}).get("command", "codex")
    opencode_command = data.get("runtime", {}).get("opencode", {}).get("command", "opencode")
    pi_mono_command = data.get("runtime", {}).get("pi_mono", {}).get("command", "pi-mono")
    log_mode = data.get("logging", {}).get("mode", "both")
    max_repair_attempts = int(data.get("repair", {}).get("max_attempts", 2))

    return AiddConfig(
        workspace_root=workspace_root,
        generic_cli_command=generic_cli_command,
        claude_code_command=claude_code_command,
        codex_command=codex_command,
        opencode_command=opencode_command,
        pi_mono_command=pi_mono_command,
        log_mode=log_mode,
        max_repair_attempts=max_repair_attempts,
    )
