from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.adapters.runtime_registry import (
    RuntimeExecutionMode,
    get_runtime_definition,
    normalize_execution_mode,
    runtime_ids,
)
from aidd.compatibility import should_upgrade_legacy_raw_provider_command
from aidd.core.stages import STAGES, is_valid_stage


@dataclass(frozen=True)
class RuntimeConfig:
    command: str
    execution_mode: RuntimeExecutionMode
    timeout_seconds: float | None
    stage_timeout_seconds: dict[str, float]


@dataclass(frozen=True)
class LegacyRuntimeConfigFields:
    generic_cli_command: str | None
    claude_code_command: str | None
    codex_command: str | None
    opencode_command: str | None
    generic_cli_execution_mode: RuntimeExecutionMode | None
    claude_code_execution_mode: RuntimeExecutionMode | None
    codex_execution_mode: RuntimeExecutionMode | None
    opencode_execution_mode: RuntimeExecutionMode | None
    generic_cli_timeout_seconds: float | None
    claude_code_timeout_seconds: float | None
    codex_timeout_seconds: float | None
    opencode_timeout_seconds: float | None
    generic_cli_stage_timeout_seconds: dict[str, float] | None
    claude_code_stage_timeout_seconds: dict[str, float] | None
    codex_stage_timeout_seconds: dict[str, float] | None
    opencode_stage_timeout_seconds: dict[str, float] | None


@dataclass(frozen=True, init=False)
class AiddConfig:
    workspace_root: Path
    log_mode: str
    max_repair_attempts: int
    runtime_configs: dict[str, RuntimeConfig]

    def __init__(
        self,
        *,
        workspace_root: Path,
        log_mode: str,
        max_repair_attempts: int,
        runtime_configs: dict[str, RuntimeConfig] | None = None,
        generic_cli_command: str | None = None,
        claude_code_command: str | None = None,
        codex_command: str | None = None,
        opencode_command: str | None = None,
        generic_cli_execution_mode: RuntimeExecutionMode | None = None,
        claude_code_execution_mode: RuntimeExecutionMode | None = None,
        codex_execution_mode: RuntimeExecutionMode | None = None,
        opencode_execution_mode: RuntimeExecutionMode | None = None,
        generic_cli_timeout_seconds: float | None = None,
        claude_code_timeout_seconds: float | None = None,
        codex_timeout_seconds: float | None = None,
        opencode_timeout_seconds: float | None = None,
        generic_cli_stage_timeout_seconds: dict[str, float] | None = None,
        claude_code_stage_timeout_seconds: dict[str, float] | None = None,
        codex_stage_timeout_seconds: dict[str, float] | None = None,
        opencode_stage_timeout_seconds: dict[str, float] | None = None,
    ) -> None:
        object.__setattr__(self, "workspace_root", workspace_root)
        object.__setattr__(self, "log_mode", log_mode)
        object.__setattr__(self, "max_repair_attempts", max_repair_attempts)
        object.__setattr__(
            self,
            "runtime_configs",
            _normalize_runtime_configs(
                runtime_configs=runtime_configs,
                legacy_fields=LegacyRuntimeConfigFields(
                    generic_cli_command=generic_cli_command,
                    claude_code_command=claude_code_command,
                    codex_command=codex_command,
                    opencode_command=opencode_command,
                    generic_cli_execution_mode=generic_cli_execution_mode,
                    claude_code_execution_mode=claude_code_execution_mode,
                    codex_execution_mode=codex_execution_mode,
                    opencode_execution_mode=opencode_execution_mode,
                    generic_cli_timeout_seconds=generic_cli_timeout_seconds,
                    claude_code_timeout_seconds=claude_code_timeout_seconds,
                    codex_timeout_seconds=codex_timeout_seconds,
                    opencode_timeout_seconds=opencode_timeout_seconds,
                    generic_cli_stage_timeout_seconds=generic_cli_stage_timeout_seconds,
                    claude_code_stage_timeout_seconds=claude_code_stage_timeout_seconds,
                    codex_stage_timeout_seconds=codex_stage_timeout_seconds,
                    opencode_stage_timeout_seconds=opencode_stage_timeout_seconds,
                ),
            ),
        )

    def runtime_config(self, runtime_id: str) -> RuntimeConfig:
        try:
            return self.runtime_configs[runtime_id]
        except KeyError as exc:
            supported = ", ".join(self.runtime_configs)
            message = f"Unsupported runtime id: {runtime_id}. Supported: {supported}."
            raise ValueError(message) from exc

    @property
    def generic_cli_command(self) -> str:
        return self.runtime_config("generic-cli").command

    @property
    def claude_code_command(self) -> str:
        return self.runtime_config("claude-code").command

    @property
    def codex_command(self) -> str:
        return self.runtime_config("codex").command

    @property
    def opencode_command(self) -> str:
        return self.runtime_config("opencode").command

    @property
    def generic_cli_execution_mode(self) -> RuntimeExecutionMode:
        return self.runtime_config("generic-cli").execution_mode

    @property
    def claude_code_execution_mode(self) -> RuntimeExecutionMode:
        return self.runtime_config("claude-code").execution_mode

    @property
    def codex_execution_mode(self) -> RuntimeExecutionMode:
        return self.runtime_config("codex").execution_mode

    @property
    def opencode_execution_mode(self) -> RuntimeExecutionMode:
        return self.runtime_config("opencode").execution_mode

    @property
    def generic_cli_timeout_seconds(self) -> float | None:
        return self.runtime_config("generic-cli").timeout_seconds

    @property
    def claude_code_timeout_seconds(self) -> float | None:
        return self.runtime_config("claude-code").timeout_seconds

    @property
    def codex_timeout_seconds(self) -> float | None:
        return self.runtime_config("codex").timeout_seconds

    @property
    def opencode_timeout_seconds(self) -> float | None:
        return self.runtime_config("opencode").timeout_seconds

    @property
    def generic_cli_stage_timeout_seconds(self) -> dict[str, float]:
        return dict(self.runtime_config("generic-cli").stage_timeout_seconds)

    @property
    def claude_code_stage_timeout_seconds(self) -> dict[str, float]:
        return dict(self.runtime_config("claude-code").stage_timeout_seconds)

    @property
    def codex_stage_timeout_seconds(self) -> dict[str, float]:
        return dict(self.runtime_config("codex").stage_timeout_seconds)

    @property
    def opencode_stage_timeout_seconds(self) -> dict[str, float]:
        return dict(self.runtime_config("opencode").stage_timeout_seconds)


def _require_runtime_value[T](runtime_id: str, field_name: str, value: T | None) -> T:
    if value is None:
        raise ValueError(
            f"Missing legacy AiddConfig constructor value for {runtime_id}: {field_name}."
        )
    return value


def _copy_runtime_configs(
    runtime_configs: dict[str, RuntimeConfig],
) -> dict[str, RuntimeConfig]:
    supported_runtime_ids = set(runtime_ids())
    configured_runtime_ids = set(runtime_configs)
    missing_runtime_ids = sorted(supported_runtime_ids - configured_runtime_ids)
    unknown_runtime_ids = sorted(configured_runtime_ids - supported_runtime_ids)
    if missing_runtime_ids or unknown_runtime_ids:
        problems: list[str] = []
        if missing_runtime_ids:
            problems.append(f"missing runtime configs: {', '.join(missing_runtime_ids)}")
        if unknown_runtime_ids:
            problems.append(f"unknown runtime configs: {', '.join(unknown_runtime_ids)}")
        raise ValueError("; ".join(problems))

    return {
        runtime_id: RuntimeConfig(
            command=runtime_config.command,
            execution_mode=runtime_config.execution_mode,
            timeout_seconds=runtime_config.timeout_seconds,
            stage_timeout_seconds=dict(runtime_config.stage_timeout_seconds),
        )
        for runtime_id, runtime_config in runtime_configs.items()
    }


def _normalize_runtime_configs(
    *,
    runtime_configs: dict[str, RuntimeConfig] | None,
    legacy_fields: LegacyRuntimeConfigFields,
) -> dict[str, RuntimeConfig]:
    if runtime_configs is not None:
        return _copy_runtime_configs(runtime_configs)

    return _legacy_runtime_configs_from_constructor_fields(legacy_fields)


def _legacy_runtime_configs_from_constructor_fields(
    legacy_fields: LegacyRuntimeConfigFields,
) -> dict[str, RuntimeConfig]:
    def runtime_config_from_legacy(
        *,
        runtime_id: str,
        command: str | None,
        execution_mode: RuntimeExecutionMode | None,
        timeout_seconds: float | None,
        stage_timeout_seconds: dict[str, float] | None,
    ) -> RuntimeConfig:
        return RuntimeConfig(
            command=_require_runtime_value(runtime_id, "command", command),
            execution_mode=_require_runtime_value(
                runtime_id,
                "execution_mode",
                execution_mode,
            ),
            timeout_seconds=timeout_seconds,
            stage_timeout_seconds=dict(stage_timeout_seconds or {}),
        )

    return {
        "generic-cli": runtime_config_from_legacy(
            runtime_id="generic-cli",
            command=legacy_fields.generic_cli_command,
            execution_mode=legacy_fields.generic_cli_execution_mode,
            timeout_seconds=legacy_fields.generic_cli_timeout_seconds,
            stage_timeout_seconds=legacy_fields.generic_cli_stage_timeout_seconds,
        ),
        "claude-code": runtime_config_from_legacy(
            runtime_id="claude-code",
            command=legacy_fields.claude_code_command,
            execution_mode=legacy_fields.claude_code_execution_mode,
            timeout_seconds=legacy_fields.claude_code_timeout_seconds,
            stage_timeout_seconds=legacy_fields.claude_code_stage_timeout_seconds,
        ),
        "codex": runtime_config_from_legacy(
            runtime_id="codex",
            command=legacy_fields.codex_command,
            execution_mode=legacy_fields.codex_execution_mode,
            timeout_seconds=legacy_fields.codex_timeout_seconds,
            stage_timeout_seconds=legacy_fields.codex_stage_timeout_seconds,
        ),
        "opencode": runtime_config_from_legacy(
            runtime_id="opencode",
            command=legacy_fields.opencode_command,
            execution_mode=legacy_fields.opencode_execution_mode,
            timeout_seconds=legacy_fields.opencode_timeout_seconds,
            stage_timeout_seconds=legacy_fields.opencode_stage_timeout_seconds,
        ),
    }


def _runtime_section(data: dict[str, Any], runtime_id: str) -> dict[str, Any]:
    definition = get_runtime_definition(runtime_id)
    raw_section = data.get("runtime", {}).get(definition.config_section, {})
    return raw_section if isinstance(raw_section, dict) else {}


def _runtime_command(data: dict[str, Any], runtime_id: str) -> str:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    command = str(section.get("command", definition.default_command)).strip()
    if should_upgrade_legacy_raw_provider_command(
        section=section,
        command=command,
        probe_command=definition.probe_command,
        default_execution_mode=definition.default_execution_mode,
        native_mode=RuntimeExecutionMode.NATIVE,
    ):
        return definition.default_command
    return command or definition.default_command


def _runtime_execution_mode(data: dict[str, Any], runtime_id: str) -> RuntimeExecutionMode:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    if "mode" in section:
        return normalize_execution_mode(runtime_id=runtime_id, value=str(section["mode"]))

    command = str(section.get("command", "")).strip()
    if (
        command
        and command != definition.default_command
        and command != definition.probe_command
        and RuntimeExecutionMode.ADAPTER_FLAGS in definition.supported_execution_modes
    ):
        return RuntimeExecutionMode.ADAPTER_FLAGS
    return definition.default_execution_mode


def _runtime_timeout_seconds(data: dict[str, Any], runtime_id: str) -> float | None:
    section = _runtime_section(data, runtime_id)
    raw_value = section.get("timeout_seconds")
    if raw_value is None:
        return None
    try:
        timeout_seconds = float(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"[runtime.{get_runtime_definition(runtime_id).config_section}] "
            "timeout_seconds must be a number when provided."
        ) from exc
    if timeout_seconds <= 0:
        raise ValueError(
            f"[runtime.{get_runtime_definition(runtime_id).config_section}] "
            "timeout_seconds must be greater than zero when provided."
        )
    return timeout_seconds


def _runtime_stage_timeout_seconds(data: dict[str, Any], runtime_id: str) -> dict[str, float]:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_stage_timeouts = section.get("stage_timeouts", {})
    if raw_stage_timeouts is None:
        return {}
    if not isinstance(raw_stage_timeouts, dict):
        raise ValueError(
            f"[runtime.{definition.config_section}.stage_timeouts] "
            "must be a table when provided."
        )

    stage_timeouts: dict[str, float] = {}
    for raw_stage, raw_value in raw_stage_timeouts.items():
        stage = str(raw_stage).strip()
        if not is_valid_stage(stage):
            expected = ", ".join(STAGES)
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts] "
                f"unknown stage {stage!r}. Expected one of: {expected}."
            )
        try:
            timeout_seconds = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts.{stage}] "
                "timeout must be a number when provided."
            ) from exc
        if timeout_seconds <= 0:
            raise ValueError(
                f"[runtime.{definition.config_section}.stage_timeouts.{stage}] "
                "timeout must be greater than zero when provided."
            )
        stage_timeouts[stage] = timeout_seconds
    return stage_timeouts


def load_config(path: Path) -> AiddConfig:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    workspace_root = Path(data.get("workspace", {}).get("root", ".aidd"))
    runtime_configs = {
        runtime_id: RuntimeConfig(
            command=_runtime_command(data, runtime_id),
            execution_mode=_runtime_execution_mode(data, runtime_id),
            timeout_seconds=_runtime_timeout_seconds(data, runtime_id),
            stage_timeout_seconds=_runtime_stage_timeout_seconds(data, runtime_id),
        )
        for runtime_id in runtime_ids()
    }
    log_mode = data.get("logging", {}).get("mode", "both")
    max_repair_attempts = int(data.get("repair", {}).get("max_attempts", 2))

    return AiddConfig(
        workspace_root=workspace_root,
        log_mode=log_mode,
        max_repair_attempts=max_repair_attempts,
        runtime_configs=runtime_configs,
    )
