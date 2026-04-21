from __future__ import annotations

import shlex
import shutil
import subprocess

from aidd.adapters.base import CapabilityReport


def discover_command(command: str) -> str | None:
    stripped = command.strip()
    if not stripped:
        return None

    try:
        tokens = shlex.split(stripped)
    except ValueError:
        return None
    if not tokens:
        return None

    return shutil.which(tokens[0])


def discover_version(command_path: str) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, PermissionError, OSError, subprocess.TimeoutExpired):
        return None

    output = result.stdout.strip() or result.stderr.strip()
    if not output:
        return None

    return output.splitlines()[0].strip() or None


def probe(command: str) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = discover_version(discovered) if discovered else None
    return CapabilityReport(
        runtime_id="generic-cli",
        available=available,
        command=discovered or command,
        version_text=version_text,
        supports_raw_log_stream=available,
        supports_structured_log_stream=False,
        supports_questions=False,
        supports_resume=False,
        supports_subagents=False,
        supports_non_interactive_mode=available,
        supports_working_directory_control=available,
        supports_env_injection=available,
    )
