from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aidd.adapters.base import RuntimeAdapterDescriptor
from aidd.adapters.registry import runtime_adapter_descriptors


class RuntimeExecutionMode(StrEnum):
    NATIVE = "native"
    ADAPTER_FLAGS = "adapter-flags"


class RuntimeSelector(StrEnum):
    MODEL = "model"
    REASONING_EFFORT = "reasoning_effort"


@dataclass(frozen=True, slots=True)
class RuntimeDefinition:
    runtime_id: str
    config_section: str
    support_tier: str
    default_command: str
    probe_command: str
    default_execution_mode: RuntimeExecutionMode
    supported_execution_modes: tuple[RuntimeExecutionMode, ...]
    brokered_default_command: str | None = None
    supported_selectors: frozenset[RuntimeSelector] = frozenset()
    selector_execution_modes: tuple[RuntimeExecutionMode, ...] = ()


def _runtime_definition_from_descriptor(
    descriptor: RuntimeAdapterDescriptor,
) -> RuntimeDefinition:
    registration = descriptor.registration
    if registration is None:
        raise ValueError(
            f"Adapter {descriptor.runtime_id!r} is missing runtime registration metadata."
        )
    try:
        default_execution_mode = RuntimeExecutionMode(registration.default_execution_mode)
        supported_execution_modes = tuple(
            RuntimeExecutionMode(value) for value in registration.supported_execution_modes
        )
        supported_selectors = frozenset(
            RuntimeSelector(value) for value in registration.supported_selectors
        )
        selector_execution_modes = tuple(
            RuntimeExecutionMode(value) for value in registration.selector_execution_modes
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid runtime registration for {descriptor.runtime_id!r}: {exc}"
        ) from exc
    if default_execution_mode not in supported_execution_modes:
        raise ValueError(
            f"Runtime registration for {descriptor.runtime_id!r} must include its default "
            "execution mode in supported_execution_modes."
        )
    return RuntimeDefinition(
        runtime_id=registration.runtime_id,
        config_section=registration.config_section,
        support_tier=registration.support_tier,
        default_command=registration.default_command,
        probe_command=registration.probe_command,
        default_execution_mode=default_execution_mode,
        supported_execution_modes=supported_execution_modes,
        brokered_default_command=registration.brokered_default_command,
        supported_selectors=supported_selectors,
        selector_execution_modes=selector_execution_modes,
    )


_RUNTIME_DEFINITIONS: dict[str, RuntimeDefinition] = {
    definition.runtime_id: definition
    for definition in (
        _runtime_definition_from_descriptor(descriptor)
        for descriptor in runtime_adapter_descriptors()
    )
}

if len(_RUNTIME_DEFINITIONS) != len(runtime_adapter_descriptors()):
    raise ValueError("Runtime adapter registrations must use unique runtime IDs.")


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


def validate_runtime_selectors(
    *,
    runtime_id: str,
    execution_mode: RuntimeExecutionMode,
    model: str | None,
    reasoning_effort: str | None,
) -> None:
    definition = get_runtime_definition(runtime_id)
    values = (
        (RuntimeSelector.MODEL, model),
        (RuntimeSelector.REASONING_EFFORT, reasoning_effort),
    )
    for selector, value in values:
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(
                f"Runtime selector {selector.value!r} for {runtime_id} must be a string."
            )
        if not value.strip():
            raise ValueError(
                f"Runtime selector {selector.value!r} for {runtime_id} must not be blank."
            )
        if selector not in definition.supported_selectors:
            raise ValueError(
                f"Runtime {runtime_id} does not support typed selector {selector.value!r}."
            )
        if execution_mode not in definition.selector_execution_modes:
            supported = (
                ", ".join(mode.value for mode in definition.selector_execution_modes) or "none"
            )
            raise ValueError(
                f"Runtime selector {selector.value!r} is not supported for runtime "
                f"{runtime_id} execution mode {execution_mode.value!r}. "
                f"Supported modes: {supported}."
            )
