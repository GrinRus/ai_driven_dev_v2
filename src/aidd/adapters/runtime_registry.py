from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeExecutionMode(StrEnum):
    NATIVE = "native"
    ADAPTER_FLAGS = "adapter-flags"


@dataclass(frozen=True, slots=True)
class RuntimeDefinition:
    runtime_id: str
    config_section: str
    support_tier: str
    default_command: str
    probe_command: str
    default_execution_mode: RuntimeExecutionMode
    supported_execution_modes: tuple[RuntimeExecutionMode, ...]
    live_command_env_var: str | None = None


_RUNTIME_DEFINITIONS: dict[str, RuntimeDefinition] = {
    "generic-cli": RuntimeDefinition(
        runtime_id="generic-cli",
        config_section="generic_cli",
        support_tier="tier-1",
        default_command="python",
        probe_command="python",
        default_execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
        supported_execution_modes=(RuntimeExecutionMode.ADAPTER_FLAGS,),
        live_command_env_var="AIDD_EVAL_GENERIC_CLI_COMMAND",
    ),
    "claude-code": RuntimeDefinition(
        runtime_id="claude-code",
        config_section="claude_code",
        support_tier="tier-1",
        default_command=(
            "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
        ),
        probe_command="claude",
        default_execution_mode=RuntimeExecutionMode.NATIVE,
        supported_execution_modes=(
            RuntimeExecutionMode.NATIVE,
            RuntimeExecutionMode.ADAPTER_FLAGS,
        ),
        live_command_env_var="AIDD_EVAL_CLAUDE_CODE_COMMAND",
    ),
    "codex": RuntimeDefinition(
        runtime_id="codex",
        config_section="codex",
        support_tier="tier-2",
        default_command="codex exec --full-auto --skip-git-repo-check --json -",
        probe_command="codex",
        default_execution_mode=RuntimeExecutionMode.NATIVE,
        supported_execution_modes=(
            RuntimeExecutionMode.NATIVE,
            RuntimeExecutionMode.ADAPTER_FLAGS,
        ),
        live_command_env_var="AIDD_EVAL_CODEX_COMMAND",
    ),
    "opencode": RuntimeDefinition(
        runtime_id="opencode",
        config_section="opencode",
        support_tier="tier-3",
        default_command="opencode run --format json --dangerously-skip-permissions",
        probe_command="opencode",
        default_execution_mode=RuntimeExecutionMode.NATIVE,
        supported_execution_modes=(
            RuntimeExecutionMode.NATIVE,
            RuntimeExecutionMode.ADAPTER_FLAGS,
        ),
        live_command_env_var="AIDD_EVAL_OPENCODE_COMMAND",
    ),
}


def runtime_definitions() -> tuple[RuntimeDefinition, ...]:
    return tuple(_RUNTIME_DEFINITIONS.values())


def runtime_ids() -> tuple[str, ...]:
    return tuple(_RUNTIME_DEFINITIONS)


def get_runtime_definition(runtime_id: str) -> RuntimeDefinition:
    try:
        return _RUNTIME_DEFINITIONS[runtime_id]
    except KeyError as exc:
        supported = ", ".join(runtime_ids())
        raise ValueError(f"Unsupported runtime id: {runtime_id}. Supported: {supported}.") from exc


def normalize_execution_mode(
    *,
    runtime_id: str,
    value: str | RuntimeExecutionMode | None,
) -> RuntimeExecutionMode:
    definition = get_runtime_definition(runtime_id)
    if value is None:
        return definition.default_execution_mode
    if isinstance(value, RuntimeExecutionMode):
        mode = value
    else:
        raw_value = value.strip()
        if not raw_value:
            return definition.default_execution_mode
        try:
            mode = RuntimeExecutionMode(raw_value)
        except ValueError as exc:
            supported = ", ".join(mode.value for mode in definition.supported_execution_modes)
            raise ValueError(
                f"Unsupported execution mode {raw_value!r} for runtime {runtime_id}. "
                f"Supported modes: {supported}."
            ) from exc
    if mode not in definition.supported_execution_modes:
        supported = ", ".join(item.value for item in definition.supported_execution_modes)
        raise ValueError(
            f"Execution mode {mode.value!r} is not supported by runtime {runtime_id}. "
            f"Supported modes: {supported}."
        )
    return mode
