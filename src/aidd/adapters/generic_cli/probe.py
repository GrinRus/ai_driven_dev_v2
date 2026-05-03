from __future__ import annotations

from aidd.adapters.base import CapabilityReport
from aidd.adapters.probe_support import (
    discover_command as _discover_command,
)
from aidd.adapters.probe_support import (
    discover_version as _discover_version,
)
from aidd.adapters.probe_support import (
    probe_basic_runtime,
)


def discover_command(command: str) -> str | None:
    return _discover_command(command)


def discover_version(command_path: str) -> str | None:
    return _discover_version(command_path, timeout_seconds=5)


def probe(command: str) -> CapabilityReport:
    return probe_basic_runtime(
        runtime_id="generic-cli",
        command=command,
        timeout_seconds=5,
    )
