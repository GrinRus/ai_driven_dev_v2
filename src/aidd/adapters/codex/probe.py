from __future__ import annotations

import subprocess

from aidd.adapters.base import CapabilityReport
from aidd.adapters.probe_support import (
    detect_capability_flags,
    discover_command,
)
from aidd.adapters.probe_support import (
    discover_help_text as _discover_help_text,
)
from aidd.adapters.probe_support import (
    discover_version as _discover_version,
)

_PROBE_TIMEOUT_SECONDS = 5


def discover_version(command_path: str) -> str | None:
    return _discover_version(command_path, timeout_seconds=_PROBE_TIMEOUT_SECONDS)


def discover_help_text(command_path: str) -> str | None:
    return _discover_help_text(command_path, timeout_seconds=_PROBE_TIMEOUT_SECONDS)


def discover_app_server_help_text(command_path: str) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "app-server", "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, PermissionError, OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def discover_app_server_schema_help_text(command_path: str) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "app-server", "generate-json-schema", "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, PermissionError, OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def _supports_live_decisions(command_path: str | None) -> bool:
    if command_path is None:
        return False
    app_server_help = discover_app_server_help_text(command_path) or ""
    schema_help = discover_app_server_schema_help_text(command_path) or ""
    return (
        "--listen" in app_server_help
        and "generate-json-schema" in app_server_help
        and "--out" in schema_help
    )


def probe(command: str) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = discover_version(discovered) if discovered else None
    help_text = discover_help_text(discovered) or "" if discovered else ""
    detected = detect_capability_flags(help_text) if discovered else {}

    supports_live_decisions = _supports_live_decisions(discovered)
    return CapabilityReport(
        runtime_id="codex",
        available=available,
        command=discovered or command,
        version_text=version_text,
        supports_raw_log_stream=available,
        supports_structured_log_stream=detected.get("supports_structured_log_stream", False),
        supports_questions=detected.get("supports_questions", False),
        supports_resume=detected.get("supports_resume", False),
        supports_subagents=detected.get("supports_subagents", False),
        supports_non_interactive_mode=detected.get("supports_non_interactive_mode", False),
        supports_working_directory_control=detected.get(
            "supports_working_directory_control",
            False,
        ),
        supports_env_injection=detected.get("supports_env_injection", False),
        supports_permission_policy=available,
        supports_live_decisions=supports_live_decisions,
        supports_deferred_resume=False,
        preferred_transport="app-server" if supports_live_decisions else "subprocess",
    )
