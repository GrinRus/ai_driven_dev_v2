from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal

from aidd.config import AiddConfig, RuntimeConfig
from aidd.core.runtime_launch_history import RuntimeLaunchOutcome
from aidd.runtime_catalog import runtime_definitions
from aidd.runtime_permissions import RuntimePermissionPolicy

RuntimeCommandSource = Literal["default", "config"]
RuntimeBinaryStatus = Literal["detected", "unavailable", "unknown"]
RuntimeExecutionCommandStatus = Literal["available", "unavailable", "unknown"]
RuntimeAuthenticationStatus = Literal["verified", "failed", "unverified"]
RuntimeCapabilityStatus = Literal["known", "unknown"]

READINESS_PROBE_MAX_AGE_SECONDS = 300


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
    config_identity: str | None = None
    observed_at_utc: str | None = None


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
    supported_selectors: tuple[str, ...]
    selector_execution_modes: tuple[str, ...]


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
    configured_model: str | None
    configured_reasoning_effort: str | None
    config_identity: str
    probe_config_identity: str | None
    probe_observed_at_utc: str | None
    eligible: bool
    disabled_reason: str | None


@dataclass(frozen=True, slots=True)
class RuntimeReadinessView:
    runtimes: tuple[RuntimeReadinessItem, ...]


def resolve_runtime_readiness(
    *,
    config: AiddConfig,
    probe_reports: Mapping[str, RuntimeReadinessProbeReport],
    command_sources: Mapping[str, RuntimeCommandSource] | None = None,
    launch_history: Mapping[str, RuntimeLaunchOutcome] | None = None,
    now: datetime | None = None,
    max_probe_age_seconds: float = READINESS_PROBE_MAX_AGE_SECONDS,
) -> RuntimeReadinessView:
    observed_now = (now or datetime.now(UTC)).astimezone(UTC)
    if max_probe_age_seconds < 0:
        raise ValueError("max_probe_age_seconds must be non-negative.")
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
        probe_observed_at_utc = (
            None if probe_report is None else probe_report.observed_at_utc
        )
        item = RuntimeReadinessItem(
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
            capabilities=_capability_readiness(
                probe_report,
                supported_selectors=tuple(
                    selector.value for selector in definition.supported_selectors
                ),
                selector_execution_modes=tuple(
                    mode.value for mode in definition.selector_execution_modes
                ),
            ),
            latest_launch=(
                None
                if launch_history is None
                else launch_history.get(definition.runtime_id)
            ),
            configured_model=runtime_config.model,
            configured_reasoning_effort=runtime_config.reasoning_effort,
            config_identity=runtime_config_identity(
                runtime_id=definition.runtime_id,
                runtime_config=runtime_config,
            ),
            probe_config_identity=(
                None if probe_report is None else probe_report.config_identity
            ),
            probe_observed_at_utc=probe_observed_at_utc,
            eligible=False,
            disabled_reason=None,
        )
        disabled_reason = _launch_disabled_reason(
            item,
            now=observed_now,
            max_probe_age_seconds=max_probe_age_seconds,
        )
        runtimes.append(
            replace(
                item,
                eligible=disabled_reason is None,
                disabled_reason=disabled_reason,
            )
        )
    return RuntimeReadinessView(runtimes=tuple(runtimes))


def runtime_config_identity(*, runtime_id: str, runtime_config: RuntimeConfig) -> str:
    """Return a stable digest for the launch-relevant runtime configuration."""

    payload = {
        "runtime_id": runtime_id,
        "command": runtime_config.command,
        "execution_mode": runtime_config.execution_mode.value,
        "timeout_seconds": runtime_config.timeout_seconds,
        "stage_timeout_seconds": dict(sorted(runtime_config.stage_timeout_seconds.items())),
        "permission_policy": runtime_config.permission_policy.value,
        "interaction_mode": runtime_config.interaction_mode.value,
        "auto_approval_preset": runtime_config.auto_approval_preset.value,
        "model": runtime_config.model,
        "reasoning_effort": runtime_config.reasoning_effort,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _launch_disabled_reason(
    item: RuntimeReadinessItem,
    *,
    now: datetime,
    max_probe_age_seconds: float,
) -> str | None:
    if item.probe_observed_at_utc is None:
        return "Runtime readiness has not been observed."
    try:
        observed = datetime.fromisoformat(item.probe_observed_at_utc.replace("Z", "+00:00"))
    except ValueError:
        return "Runtime readiness observation time is invalid."
    if observed.tzinfo is None:
        return "Runtime readiness observation time is invalid."
    age_seconds = (now - observed.astimezone(UTC)).total_seconds()
    if age_seconds < 0 or age_seconds > max_probe_age_seconds:
        return "Runtime readiness is stale; refresh the probe before launching."
    if (
        item.probe_config_identity is not None
        and item.probe_config_identity != item.config_identity
    ):
        return "Runtime configuration changed; refresh readiness."
    if item.binary.status != "detected":
        return "Runtime binary is unavailable."
    if item.execution_command.status != "available":
        return "Runtime execution command is unavailable."
    if item.authentication.status == "failed":
        return "Runtime authentication failed."
    if (
        item.permission_policy != RuntimePermissionPolicy.FULL_ACCESS.value
        and item.capabilities.supports_permission_policy is not True
    ):
        return "Runtime permission policy is not supported by the adapter."
    if item.probe_config_identity is None:
        return "Runtime config identity is unavailable; refresh readiness."
    return None


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _capability_readiness(
    probe_report: RuntimeReadinessProbeReport | None,
    *,
    supported_selectors: tuple[str, ...],
    selector_execution_modes: tuple[str, ...],
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
            supported_selectors=supported_selectors,
            selector_execution_modes=selector_execution_modes,
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
        supported_selectors=supported_selectors,
        selector_execution_modes=selector_execution_modes,
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
