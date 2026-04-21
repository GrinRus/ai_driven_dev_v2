from __future__ import annotations

import shlex
import shutil

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


def probe(command: str) -> CapabilityReport:
    discovered = discover_command(command)
    return CapabilityReport(
        runtime_id="generic-cli",
        available=discovered is not None,
        command=discovered or command,
        supports_structured_log_stream=False,
        supports_questions=False,
        supports_resume=False,
        supports_subagents=False,
    )
