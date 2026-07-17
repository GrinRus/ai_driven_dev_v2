from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.compatibility import should_upgrade_legacy_raw_provider_command
from aidd.core.stages import STAGES, is_valid_stage
from aidd.runtime_budget import validate_runtime_budget
from aidd.runtime_catalog import (
    RuntimeExecutionMode,
    get_runtime_definition,
    normalize_execution_mode,
    runtime_ids,
)
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimePermissionPolicy,
    command_contains_permission_bypass,
    normalize_auto_approval_preset,
    normalize_interaction_mode,
    normalize_permission_policy,
)

_PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

_TOP_LEVEL_CONFIG_KEYS = frozenset(
    {"workspace", "runtime", "logging", "repair", "project_set"}
)
_CONFIG_SECTION_KEYS: dict[str, frozenset[str]] = {
    "workspace": frozenset({"root"}),
    "logging": frozenset({"mode"}),
    "repair": frozenset({"max_attempts"}),
    "project_set": frozenset({"projects"}),
}
_RUNTIME_CONFIG_KEYS = frozenset(
    {
        "command",
        "mode",
        "timeout_seconds",
        "stage_timeouts",
        "permission_policy",
        "interaction_mode",
        "auto_approval_preset",
    }
)
_PROJECT_CONFIG_KEYS = frozenset({"id", "root", "role"})


@dataclass(frozen=True)
class RuntimeConfig:
    command: str
    execution_mode: RuntimeExecutionMode
    timeout_seconds: float | None
    stage_timeout_seconds: dict[str, float]
    permission_policy: RuntimePermissionPolicy = RuntimePermissionPolicy.FULL_ACCESS
    interaction_mode: RuntimeInteractionMode = RuntimeInteractionMode.BATCH
    auto_approval_preset: AutoApprovalPreset = AutoApprovalPreset.BROAD


@dataclass(frozen=True)
class ProjectConfig:
    id: str
    root: Path
    role: str | None = None


@dataclass(frozen=True)
class ProjectSetConfig:
    projects: tuple[ProjectConfig, ...] = ()


@dataclass(frozen=True)
class LegacyRuntimeConfigFields:
    generic_cli_command: str | None
    claude_code_command: str | None
    codex_command: str | None
    opencode_command: str | None
    qwen_command: str | None
    generic_cli_execution_mode: RuntimeExecutionMode | None
    claude_code_execution_mode: RuntimeExecutionMode | None
    codex_execution_mode: RuntimeExecutionMode | None
    opencode_execution_mode: RuntimeExecutionMode | None
    qwen_execution_mode: RuntimeExecutionMode | None
    generic_cli_timeout_seconds: float | None
    claude_code_timeout_seconds: float | None
    codex_timeout_seconds: float | None
    opencode_timeout_seconds: float | None
    qwen_timeout_seconds: float | None
    generic_cli_stage_timeout_seconds: dict[str, float] | None
    claude_code_stage_timeout_seconds: dict[str, float] | None
    codex_stage_timeout_seconds: dict[str, float] | None
    opencode_stage_timeout_seconds: dict[str, float] | None
    qwen_stage_timeout_seconds: dict[str, float] | None


@dataclass(frozen=True, init=False)
class AiddConfig:
    workspace_root: Path
    log_mode: str
    max_repair_attempts: int
    runtime_configs: dict[str, RuntimeConfig]
    project_set: ProjectSetConfig

    def __init__(
        self,
        *,
        workspace_root: Path,
        log_mode: str,
        max_repair_attempts: int,
        runtime_configs: dict[str, RuntimeConfig] | None = None,
        project_set: ProjectSetConfig | None = None,
        generic_cli_command: str | None = None,
        claude_code_command: str | None = None,
        codex_command: str | None = None,
        opencode_command: str | None = None,
        qwen_command: str | None = None,
        generic_cli_execution_mode: RuntimeExecutionMode | None = None,
        claude_code_execution_mode: RuntimeExecutionMode | None = None,
        codex_execution_mode: RuntimeExecutionMode | None = None,
        opencode_execution_mode: RuntimeExecutionMode | None = None,
        qwen_execution_mode: RuntimeExecutionMode | None = None,
        generic_cli_timeout_seconds: float | None = None,
        claude_code_timeout_seconds: float | None = None,
        codex_timeout_seconds: float | None = None,
        opencode_timeout_seconds: float | None = None,
        qwen_timeout_seconds: float | None = None,
        generic_cli_stage_timeout_seconds: dict[str, float] | None = None,
        claude_code_stage_timeout_seconds: dict[str, float] | None = None,
        codex_stage_timeout_seconds: dict[str, float] | None = None,
        opencode_stage_timeout_seconds: dict[str, float] | None = None,
        qwen_stage_timeout_seconds: dict[str, float] | None = None,
    ) -> None:
        object.__setattr__(self, "workspace_root", workspace_root)
        object.__setattr__(self, "log_mode", log_mode)
        object.__setattr__(self, "max_repair_attempts", max_repair_attempts)
        object.__setattr__(self, "project_set", project_set or ProjectSetConfig())
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
                    qwen_command=qwen_command,
                    generic_cli_execution_mode=generic_cli_execution_mode,
                    claude_code_execution_mode=claude_code_execution_mode,
                    codex_execution_mode=codex_execution_mode,
                    opencode_execution_mode=opencode_execution_mode,
                    qwen_execution_mode=qwen_execution_mode,
                    generic_cli_timeout_seconds=generic_cli_timeout_seconds,
                    claude_code_timeout_seconds=claude_code_timeout_seconds,
                    codex_timeout_seconds=codex_timeout_seconds,
                    opencode_timeout_seconds=opencode_timeout_seconds,
                    qwen_timeout_seconds=qwen_timeout_seconds,
                    generic_cli_stage_timeout_seconds=generic_cli_stage_timeout_seconds,
                    claude_code_stage_timeout_seconds=claude_code_stage_timeout_seconds,
                    codex_stage_timeout_seconds=codex_stage_timeout_seconds,
                    opencode_stage_timeout_seconds=opencode_stage_timeout_seconds,
                    qwen_stage_timeout_seconds=qwen_stage_timeout_seconds,
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
    def qwen_command(self) -> str:
        return self.runtime_config("qwen").command

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
    def qwen_execution_mode(self) -> RuntimeExecutionMode:
        return self.runtime_config("qwen").execution_mode

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
    def qwen_timeout_seconds(self) -> float | None:
        return self.runtime_config("qwen").timeout_seconds

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

    @property
    def qwen_stage_timeout_seconds(self) -> dict[str, float]:
        return dict(self.runtime_config("qwen").stage_timeout_seconds)


def _require_runtime_value[T](runtime_id: str, field_name: str, value: T | None) -> T:
    if value is None:
        raise ValueError(
            f"Missing legacy AiddConfig constructor value for {runtime_id}: {field_name}."
        )
    return value


def _config_table(data: dict[str, Any], section_name: str) -> dict[str, Any]:
    raw_section = data.get(section_name, {})
    if raw_section is None:
        return {}
    if not isinstance(raw_section, dict):
        raise ValueError(f"[{section_name}] must be a table when provided.")
    return raw_section


def _nested_config_table(
    data: dict[str, Any],
    *,
    parent_section: str,
    section_name: str,
) -> dict[str, Any]:
    parent = _config_table(data, parent_section)
    raw_section = parent.get(section_name, {})
    if raw_section is None:
        return {}
    if not isinstance(raw_section, dict):
        raise ValueError(
            f"[{parent_section}.{section_name}] must be a table when provided."
        )
    return raw_section


def _string_config_value(
    section: dict[str, Any],
    *,
    section_label: str,
    field_name: str,
    default: str,
    reject_blank: bool = False,
) -> str:
    raw_value = section.get(field_name, default)
    if not isinstance(raw_value, str):
        raise ValueError(f"[{section_label}.{field_name}] must be a string when provided.")
    if reject_blank and field_name in section and not raw_value.strip():
        raise ValueError(f"[{section_label}.{field_name}] must not be blank when provided.")
    return raw_value


def _reject_unknown_keys(
    values: dict[str, Any],
    *,
    allowed: frozenset[str],
    label: str,
) -> None:
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"[{label}] contains unknown keys: {', '.join(unknown)}.")


def _validate_known_config_keys(data: dict[str, Any]) -> None:
    unknown_top_level = sorted(set(data) - _TOP_LEVEL_CONFIG_KEYS)
    if unknown_top_level:
        raise ValueError(
            "Configuration contains unknown top-level keys: "
            f"{', '.join(unknown_top_level)}."
        )

    for section_name, allowed_keys in _CONFIG_SECTION_KEYS.items():
        section = _config_table(data, section_name)
        _reject_unknown_keys(section, allowed=allowed_keys, label=section_name)

    runtime = _config_table(data, "runtime")
    runtime_sections = {
        get_runtime_definition(runtime_id).config_section for runtime_id in runtime_ids()
    }
    unknown_runtime_sections = sorted(set(runtime) - runtime_sections)
    if unknown_runtime_sections:
        raise ValueError(
            "[runtime] contains unknown runtime sections: "
            f"{', '.join(unknown_runtime_sections)}."
        )
    for runtime_id in runtime_ids():
        definition = get_runtime_definition(runtime_id)
        section = _runtime_section(data, runtime_id)
        _reject_unknown_keys(
            section,
            allowed=_RUNTIME_CONFIG_KEYS,
            label=f"runtime.{definition.config_section}",
        )


def _integer_config_value(
    section: dict[str, Any],
    *,
    section_label: str,
    field_name: str,
    default: int,
) -> int:
    raw_value = section.get(field_name, default)
    if isinstance(raw_value, bool) or not isinstance(raw_value, int):
        raise ValueError(
            f"[{section_label}.{field_name}] must be a non-negative integer."
        )
    if raw_value < 0:
        raise ValueError(
            f"[{section_label}.{field_name}] must be a non-negative integer."
        )
    return int(raw_value)


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
            permission_policy=runtime_config.permission_policy,
            interaction_mode=runtime_config.interaction_mode,
            auto_approval_preset=runtime_config.auto_approval_preset,
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
        "qwen": runtime_config_from_legacy(
            runtime_id="qwen",
            command=legacy_fields.qwen_command or get_runtime_definition("qwen").default_command,
            execution_mode=(
                legacy_fields.qwen_execution_mode
                or get_runtime_definition("qwen").default_execution_mode
            ),
            timeout_seconds=legacy_fields.qwen_timeout_seconds,
            stage_timeout_seconds=legacy_fields.qwen_stage_timeout_seconds,
        ),
    }


def _runtime_section(data: dict[str, Any], runtime_id: str) -> dict[str, Any]:
    definition = get_runtime_definition(runtime_id)
    return _nested_config_table(
        data,
        parent_section="runtime",
        section_name=definition.config_section,
    )


def _brokered_default_command(runtime_id: str) -> str:
    definition = get_runtime_definition(runtime_id)
    return definition.brokered_default_command or definition.default_command


def _runtime_command(
    data: dict[str, Any],
    runtime_id: str,
    permission_policy: RuntimePermissionPolicy,
) -> str:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    has_custom_command = "command" in section
    command = _string_config_value(
        section,
        section_label=f"runtime.{definition.config_section}",
        field_name="command",
        default=definition.default_command,
        reject_blank=True,
    ).strip()
    is_default_managed_command = command == definition.default_command
    if (
        has_custom_command
        and is_default_managed_command
        and permission_policy is not RuntimePermissionPolicy.FULL_ACCESS
    ):
        return _brokered_default_command(runtime_id)
    if (
        has_custom_command
        and permission_policy is not RuntimePermissionPolicy.FULL_ACCESS
        and command_contains_permission_bypass(command)
    ):
        raise ValueError(
            f"permission-policy-conflict: [runtime.{definition.config_section}] custom "
            f"command includes full-access bypass flags while permission_policy is "
            f"{permission_policy.value!r}."
        )
    if should_upgrade_legacy_raw_provider_command(
        section=section,
        command=command,
        probe_command=definition.probe_command,
        default_execution_mode=definition.default_execution_mode,
        native_mode=RuntimeExecutionMode.NATIVE,
    ):
        if permission_policy is not RuntimePermissionPolicy.FULL_ACCESS:
            return _brokered_default_command(runtime_id)
        return definition.default_command
    if (
        not has_custom_command
        and permission_policy is not RuntimePermissionPolicy.FULL_ACCESS
    ):
        return _brokered_default_command(runtime_id)
    return command or definition.default_command


def _runtime_execution_mode(data: dict[str, Any], runtime_id: str) -> RuntimeExecutionMode:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    if "mode" in section:
        mode = _string_config_value(
            section,
            section_label=f"runtime.{definition.config_section}",
            field_name="mode",
            default="",
            reject_blank=True,
        )
        return normalize_execution_mode(runtime_id=runtime_id, value=mode)

    command = _string_config_value(
        section,
        section_label=f"runtime.{definition.config_section}",
        field_name="command",
        default="",
    ).strip()
    if (
        command
        and command != definition.default_command
        and command != _brokered_default_command(runtime_id)
        and command != definition.probe_command
        and RuntimeExecutionMode.ADAPTER_FLAGS in definition.supported_execution_modes
    ):
        return RuntimeExecutionMode.ADAPTER_FLAGS
    return definition.default_execution_mode


def _runtime_timeout_seconds(data: dict[str, Any], runtime_id: str) -> float | None:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_value = section.get("timeout_seconds")
    if raw_value is None:
        return None
    try:
        return validate_runtime_budget(
            raw_value,
            label=f"[runtime.{definition.config_section}] timeout_seconds",
        )
    except ValueError as exc:
        raise ValueError(
            str(exc)
        ) from exc


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
            timeout_seconds = validate_runtime_budget(
                raw_value,
                label=(
                    f"[runtime.{definition.config_section}.stage_timeouts.{stage}] timeout"
                ),
            )
        except ValueError as exc:
            raise ValueError(
                str(exc)
            ) from exc
        assert timeout_seconds is not None
        stage_timeouts[stage] = timeout_seconds
    return stage_timeouts


def _runtime_permission_policy(
    data: dict[str, Any],
    runtime_id: str,
) -> RuntimePermissionPolicy:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_policy = _string_config_value(
        section,
        section_label=f"runtime.{definition.config_section}",
        field_name="permission_policy",
        default=RuntimePermissionPolicy.FULL_ACCESS.value,
        reject_blank=True,
    )
    try:
        return normalize_permission_policy(raw_policy)
    except ValueError as exc:
        raise ValueError(
            f"[runtime.{definition.config_section}] {exc}"
        ) from exc


def _runtime_interaction_mode(
    data: dict[str, Any],
    runtime_id: str,
) -> RuntimeInteractionMode:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_mode = _string_config_value(
        section,
        section_label=f"runtime.{definition.config_section}",
        field_name="interaction_mode",
        default=RuntimeInteractionMode.BATCH.value,
        reject_blank=True,
    )
    try:
        return normalize_interaction_mode(raw_mode)
    except ValueError as exc:
        raise ValueError(
            f"[runtime.{definition.config_section}] {exc}"
        ) from exc


def _runtime_auto_approval_preset(
    data: dict[str, Any],
    runtime_id: str,
) -> AutoApprovalPreset:
    definition = get_runtime_definition(runtime_id)
    section = _runtime_section(data, runtime_id)
    raw_preset = _string_config_value(
        section,
        section_label=f"runtime.{definition.config_section}",
        field_name="auto_approval_preset",
        default=AutoApprovalPreset.BROAD.value,
        reject_blank=True,
    )
    try:
        return normalize_auto_approval_preset(raw_preset)
    except ValueError as exc:
        raise ValueError(
            f"[runtime.{definition.config_section}] {exc}"
        ) from exc


def _parse_project_set(data: dict[str, Any]) -> ProjectSetConfig:
    raw_project_set = data.get("project_set", {})
    if raw_project_set is None:
        return ProjectSetConfig()
    if not isinstance(raw_project_set, dict):
        raise ValueError("[project_set] must be a table when provided.")

    raw_projects = raw_project_set.get("projects", ())
    if raw_projects in (None, ()):
        return ProjectSetConfig()
    if not isinstance(raw_projects, list):
        raise ValueError("[[project_set.projects]] must be an array of tables.")

    projects: list[ProjectConfig] = []
    seen_ids: set[str] = set()
    for index, raw_project in enumerate(raw_projects, start=1):
        if not isinstance(raw_project, dict):
            raise ValueError(
                f"project_set.projects[{index}] must be a table when provided."
            )
        _reject_unknown_keys(
            raw_project,
            allowed=_PROJECT_CONFIG_KEYS,
            label=f"project_set.projects[{index}]",
        )
        project_id = str(raw_project.get("id", "")).strip()
        if not project_id:
            raise ValueError(f"project_set.projects[{index}].id is required.")
        if _PROJECT_ID_PATTERN.match(project_id) is None:
            raise ValueError(
                f"project_set.projects[{index}].id must use letters, numbers, "
                "underscores, or hyphens and start with a letter or number."
            )
        if project_id in seen_ids:
            raise ValueError(f"Duplicate project_set project id: {project_id}.")
        seen_ids.add(project_id)

        raw_root = str(raw_project.get("root", "")).strip()
        if not raw_root:
            raise ValueError(f"project_set.projects[{index}].root is required.")

        raw_role = raw_project.get("role")
        role = str(raw_role).strip() if raw_role is not None else None
        projects.append(
            ProjectConfig(
                id=project_id,
                root=Path(raw_root),
                role=role or None,
            )
        )

    return ProjectSetConfig(projects=tuple(projects))


def load_config(path: Path) -> AiddConfig:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    _validate_known_config_keys(data)

    workspace_root = Path(
        _string_config_value(
            _config_table(data, "workspace"),
            section_label="workspace",
            field_name="root",
            default=".aidd",
            reject_blank=True,
        )
    )
    runtime_configs: dict[str, RuntimeConfig] = {}
    for runtime_id in runtime_ids():
        permission_policy = _runtime_permission_policy(data, runtime_id)
        runtime_configs[runtime_id] = RuntimeConfig(
            command=_runtime_command(data, runtime_id, permission_policy),
            execution_mode=_runtime_execution_mode(data, runtime_id),
            timeout_seconds=_runtime_timeout_seconds(data, runtime_id),
            stage_timeout_seconds=_runtime_stage_timeout_seconds(data, runtime_id),
            permission_policy=permission_policy,
            interaction_mode=_runtime_interaction_mode(data, runtime_id),
            auto_approval_preset=_runtime_auto_approval_preset(data, runtime_id),
        )
    log_mode = _string_config_value(
        _config_table(data, "logging"),
        section_label="logging",
        field_name="mode",
        default="both",
        reject_blank=True,
    )
    max_repair_attempts = _integer_config_value(
        _config_table(data, "repair"),
        section_label="repair",
        field_name="max_attempts",
        default=2,
    )

    return AiddConfig(
        workspace_root=workspace_root,
        log_mode=log_mode,
        max_repair_attempts=max_repair_attempts,
        runtime_configs=runtime_configs,
        project_set=_parse_project_set(data),
    )
