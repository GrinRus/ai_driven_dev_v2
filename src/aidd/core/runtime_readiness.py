from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from aidd.config import AiddConfig
from aidd.core.runtime_launch_history import RuntimeLaunchOutcome
from aidd.runtime_catalog import runtime_definitions

RuntimeCommandSource = Literal["default", "config"]
RuntimeBinaryStatus = Literal["detected", "unavailable", "unknown"]
RuntimeExecutionCommandStatus = Literal["available", "unavailable", "unknown"]
RuntimeAuthenticationStatus = Literal["verified", "failed", "unverified"]
RuntimeCapabilityStatus = Literal["known", "unknown"]


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityProbeReport:
    supports_raw_log_stream: bool
    supports_structured_log_stream: bool
    supports_questions: bool
    supports_resume: bool
    supports_subagents: bool
    supports_permission_policy: bool
    supports_live_decisions: bool
    preferred_transport: str


@dataclass(frozen=True, slots=True)
class RuntimeReadinessProbeReport:
    provider_available: bool
    execution_command_available: bool
    provider_version: str | None = None
    provider_command: str | None = None
    authentication_status: RuntimeAuthenticationStatus = "unverified"
    authentication_detail: str | None = None
    capabilities: RuntimeCapabilityProbeReport | None = None


@dataclass(frozen=True, slots=True)
class RuntimeBinaryReadiness:
    status: RuntimeBinaryStatus
    command: str | None
    version: str | None


@dataclass(frozen=True, slots=True)
class RuntimeExecutionCommandReadiness:
    status: RuntimeExecutionCommandStatus
    command: str
    source: RuntimeCommandSource


@dataclass(frozen=True, slots=True)
class RuntimeAuthenticationReadiness:
    status: RuntimeAuthenticationStatus
    detail: str | None


@dataclass(frozen=True, slots=True)
class RuntimeCapabilityReadiness:
    status: RuntimeCapabilityStatus
    supports_raw_log_stream: bool | None
    supports_structured_log_stream: bool | None
    supports_questions: bool | None
    supports_resume: bool | None
    supports_subagents: bool | None
    supports_permission_policy: bool | None
    supports_live_decisions: bool | None
    preferred_transport: str | None


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
    binary: RuntimeBinaryReadiness
    execution_command: RuntimeExecutionCommandReadiness
    authentication: RuntimeAuthenticationReadiness
    capabilities: RuntimeCapabilityReadiness
    latest_launch: RuntimeLaunchOutcome | None


@dataclass(frozen=True, slots=True)
class RuntimeReadinessView:
    runtimes: tuple[RuntimeReadinessItem, ...]


def resolve_runtime_readiness(
    *,
    config: AiddConfig,
    probe_reports: Mapping[str, RuntimeReadinessProbeReport],
    command_sources: Mapping[str, RuntimeCommandSource] | None = None,
    launch_history: Mapping[str, RuntimeLaunchOutcome] | None = None,
) -> RuntimeReadinessView:
    runtimes: list[RuntimeReadinessItem] = []
    for definition in runtime_definitions():
        runtime_config = config.runtime_config(definition.runtime_id)
        probe_report = probe_reports.get(definition.runtime_id)
        command_source = _command_source(
            runtime_id=definition.runtime_id,
            command=runtime_config.command,
            default_command=definition.default_command,
            command_sources=command_sources,
        )
        provider_available = False if probe_report is None else probe_report.provider_available
        execution_command_available = (
            False if probe_report is None else probe_report.execution_command_available
        )
        runtimes.append(
            RuntimeReadinessItem(
                runtime_id=definition.runtime_id,
                support_tier=definition.support_tier,
                command_source=command_source,
                command=runtime_config.command,
                execution_mode=runtime_config.execution_mode.value,
                provider_available=provider_available,
                provider_version=None if probe_report is None else probe_report.provider_version,
                provider_command=None if probe_report is None else probe_report.provider_command,
                execution_command_available=execution_command_available,
                default_timeout_seconds=runtime_config.timeout_seconds,
                stage_timeout_seconds=dict(runtime_config.stage_timeout_seconds),
                permission_policy=runtime_config.permission_policy.value,
                interaction_mode=runtime_config.interaction_mode.value,
                auto_approval_preset=runtime_config.auto_approval_preset.value,
                binary=RuntimeBinaryReadiness(
                    status=(
                        "unknown"
                        if probe_report is None
                        else "detected"
                        if provider_available
                        else "unavailable"
                    ),
                    command=None if probe_report is None else probe_report.provider_command,
                    version=None if probe_report is None else probe_report.provider_version,
                ),
                execution_command=RuntimeExecutionCommandReadiness(
                    status=(
                        "unknown"
                        if probe_report is None
                        else "available"
                        if execution_command_available
                        else "unavailable"
                    ),
                    command=runtime_config.command,
                    source=command_source,
                ),
                authentication=RuntimeAuthenticationReadiness(
                    status=(
                        "unverified"
                        if probe_report is None
                        else probe_report.authentication_status
                    ),
                    detail=None if probe_report is None else probe_report.authentication_detail,
                ),
                capabilities=_capability_readiness(probe_report),
                latest_launch=(
                    None
                    if launch_history is None
                    else launch_history.get(definition.runtime_id)
                ),
            )
        )
    return RuntimeReadinessView(runtimes=tuple(runtimes))


def _capability_readiness(
    probe_report: RuntimeReadinessProbeReport | None,
) -> RuntimeCapabilityReadiness:
    capabilities = None if probe_report is None else probe_report.capabilities
    if capabilities is None:
        return RuntimeCapabilityReadiness(
            status="unknown",
            supports_raw_log_stream=None,
            supports_structured_log_stream=None,
            supports_questions=None,
            supports_resume=None,
            supports_subagents=None,
            supports_permission_policy=None,
            supports_live_decisions=None,
            preferred_transport=None,
        )
    return RuntimeCapabilityReadiness(
        status="known",
        supports_raw_log_stream=capabilities.supports_raw_log_stream,
        supports_structured_log_stream=capabilities.supports_structured_log_stream,
        supports_questions=capabilities.supports_questions,
        supports_resume=capabilities.supports_resume,
        supports_subagents=capabilities.supports_subagents,
        supports_permission_policy=capabilities.supports_permission_policy,
        supports_live_decisions=capabilities.supports_live_decisions,
        preferred_transport=capabilities.preferred_transport,
    )


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
