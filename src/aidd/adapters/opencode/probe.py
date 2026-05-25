from __future__ import annotations

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


def probe(command: str) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = discover_version(discovered) if discovered else None
    help_text = discover_help_text(discovered) or "" if discovered else ""
    detected = detect_capability_flags(help_text) if discovered else {}

    return CapabilityReport(
        runtime_id="opencode",
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
        supports_live_decisions=False,
        supports_deferred_resume=False,
        preferred_transport="subprocess",
    )
