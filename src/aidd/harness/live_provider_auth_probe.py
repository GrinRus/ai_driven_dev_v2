from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from aidd.harness.live_provider_auth_seed import ProviderAuthRuntime

ProviderAuthProbeStatus = Literal["pass", "fail", "timeout", "error"]
_PROVIDER_AUTH_PROBE_TIMEOUT_SECONDS = 10
_STATUS_COMMANDS: dict[ProviderAuthRuntime, tuple[str, ...]] = {
    "codex": ("codex", "login", "status"),
    "claude-code": ("claude", "auth", "status", "--json"),
}


class _IsolationBoundary(Protocol):
    @property
    def provider_root(self) -> Path: ...

    @property
    def environment(self) -> Mapping[str, str]: ...

    def wrap_command(self, command: Sequence[str]) -> tuple[str, ...]: ...


@dataclass(frozen=True, slots=True)
class ProviderAuthProbeResult:
    runtime: ProviderAuthRuntime
    status: ProviderAuthProbeStatus
    exit_code: int | None


def probe_provider_auth_state(
    *,
    runtime: ProviderAuthRuntime,
    boundary: _IsolationBoundary,
    timeout_seconds: int = _PROVIDER_AUTH_PROBE_TIMEOUT_SECONDS,
) -> ProviderAuthProbeResult:
    command = _STATUS_COMMANDS[runtime]
    try:
        completed = subprocess.run(
            boundary.wrap_command(command),
            cwd=boundary.provider_root,
            env=dict(boundary.environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return ProviderAuthProbeResult(
            runtime=runtime,
            status="timeout",
            exit_code=None,
        )
    except OSError:
        return ProviderAuthProbeResult(
            runtime=runtime,
            status="error",
            exit_code=None,
        )
    return ProviderAuthProbeResult(
        runtime=runtime,
        status="pass" if completed.returncode == 0 else "fail",
        exit_code=completed.returncode,
    )


__all__ = [
    "ProviderAuthProbeResult",
    "ProviderAuthProbeStatus",
    "probe_provider_auth_state",
]
