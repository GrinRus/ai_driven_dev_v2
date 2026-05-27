from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from aidd.config import AiddConfig
from aidd.runtime_catalog import runtime_definitions

RuntimeCommandSource = Literal["default", "config"]


@dataclass(frozen=True, slots=True)
class RuntimeReadinessProbeReport:
    provider_available: bool
    execution_command_available: bool
    provider_version: str | None = None
    provider_command: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeReadinessItem:
    runtime_id: str
    support_tier: str
    command_source: RuntimeCommandSource
    command: str
    execution_mode: str
    provider_available: bool
    provider_version: str | None
    provider_command: str | None
    execution_command_available: bool
    default_timeout_seconds: float | None
    stage_timeout_seconds: dict[str, float]
    permission_policy: str
    interaction_mode: str
    auto_approval_preset: str


@dataclass(frozen=True, slots=True)
class RuntimeReadinessView:
    runtimes: tuple[RuntimeReadinessItem, ...]


def resolve_runtime_readiness(
    *,
    config: AiddConfig,
    probe_reports: Mapping[str, RuntimeReadinessProbeReport],
    command_sources: Mapping[str, RuntimeCommandSource] | None = None,
) -> RuntimeReadinessView:
    runtimes: list[RuntimeReadinessItem] = []
    for definition in runtime_definitions():
        runtime_config = config.runtime_config(definition.runtime_id)
        probe_report = probe_reports.get(definition.runtime_id)
        runtimes.append(
            RuntimeReadinessItem(
                runtime_id=definition.runtime_id,
                support_tier=definition.support_tier,
                command_source=_command_source(
                    runtime_id=definition.runtime_id,
                    command=runtime_config.command,
                    default_command=definition.default_command,
                    command_sources=command_sources,
                ),
                command=runtime_config.command,
                execution_mode=runtime_config.execution_mode.value,
                provider_available=(
                    False if probe_report is None else probe_report.provider_available
                ),
                provider_version=None if probe_report is None else probe_report.provider_version,
                provider_command=None if probe_report is None else probe_report.provider_command,
                execution_command_available=(
                    False
                    if probe_report is None
                    else probe_report.execution_command_available
                ),
                default_timeout_seconds=runtime_config.timeout_seconds,
                stage_timeout_seconds=dict(runtime_config.stage_timeout_seconds),
                permission_policy=runtime_config.permission_policy.value,
                interaction_mode=runtime_config.interaction_mode.value,
                auto_approval_preset=runtime_config.auto_approval_preset.value,
            )
        )
    return RuntimeReadinessView(runtimes=tuple(runtimes))


def _command_source(
    *,
    runtime_id: str,
    command: str,
    default_command: str,
    command_sources: Mapping[str, RuntimeCommandSource] | None,
) -> RuntimeCommandSource:
    if command_sources is not None and runtime_id in command_sources:
        return command_sources[runtime_id]
    if command == default_command:
        return "default"
    return "config"
