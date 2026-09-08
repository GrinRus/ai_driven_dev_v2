from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath


def _normalize_path_metadata(values: Iterable[str], *, field_name: str) -> tuple[str, ...]:
    if isinstance(values, str):
        values = (values,)
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} entries must be strings.")
        candidate = value.strip()
        if not candidate:
            raise ValueError(f"{field_name} entries must not be empty.")
        if "\\" in candidate or "\x00" in candidate:
            raise ValueError(f"{field_name} entries must use safe POSIX paths.")
        path = PurePosixPath(candidate)
        if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError(
                f"{field_name} entries must be repository-relative and must not traverse parents."
            )
        canonical = path.as_posix()
        if canonical not in normalized:
            normalized.append(canonical)
    return tuple(normalized)


def _normalize_capabilities(values: Iterable[str]) -> frozenset[str]:
    if isinstance(values, str):
        values = (values,)
    normalized: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise TypeError("capabilities entries must be strings.")
        capability = value.strip()
        if not capability:
            raise ValueError("capabilities entries must not be empty.")
        if any(character.isspace() for character in capability) or "\x00" in capability:
            raise ValueError("capabilities entries must be non-empty labels without whitespace.")
        normalized.add(capability)
    return frozenset(normalized)


@dataclass(frozen=True, slots=True)
class RuntimeAdapterRegistration:
    """Adapter-owned runtime/config compatibility metadata.

    Values intentionally use stable strings so the adapter protocol does not depend on
    the runtime catalog's enum implementation.  The catalog converts these values at its
    neutral boundary and keeps the existing public ``RuntimeDefinition`` API intact.
    """

    runtime_id: str
    config_section: str
    support_tier: str
    default_command: str
    probe_command: str
    default_execution_mode: str
    supported_execution_modes: tuple[str, ...]
    brokered_default_command: str | None = None
    supported_selectors: tuple[str, ...] = ()
    selector_execution_modes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "runtime_id",
            "config_section",
            "support_tier",
            "default_command",
            "probe_command",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")
        default_execution_mode = self.default_execution_mode
        if not isinstance(default_execution_mode, str):
            raise TypeError("default_execution_mode must be a string.")
        if not default_execution_mode.strip():
            raise ValueError("default_execution_mode must not be blank.")
        object.__setattr__(self, "default_execution_mode", default_execution_mode.strip())
        for field_name in (
            "supported_execution_modes",
            "supported_selectors",
            "selector_execution_modes",
        ):
            values = getattr(self, field_name)
            if isinstance(values, str):
                values = (values,)
            normalized_values: list[str] = []
            for value in values:
                if not isinstance(value, str):
                    raise TypeError(f"{field_name} entries must be strings.")
                normalized_values.append(value.strip())
            normalized = tuple(normalized_values)
            if any(not value for value in normalized):
                raise ValueError(f"{field_name} entries must be non-empty strings.")
            object.__setattr__(self, field_name, normalized)
        if self.brokered_default_command is not None:
            if not isinstance(self.brokered_default_command, str):
                raise TypeError("brokered_default_command must be a string when provided.")
            if not self.brokered_default_command.strip():
                raise ValueError("brokered_default_command must not be blank.")
            object.__setattr__(
                self,
                "brokered_default_command",
                self.brokered_default_command.strip(),
            )


@dataclass(frozen=True, slots=True)
class RuntimeAdapterDescriptor:
    """Static adapter-owned security and capability metadata.

    Path fields are repository-relative POSIX prefixes or filename markers.  They identify
    provider-managed material; they never contain credential values.  The descriptor is static
    adapter metadata, while :class:`CapabilityReport` remains the result of probing a concrete
    runtime installation.
    """

    runtime_id: str
    protected_paths: tuple[str, ...] = ()
    credential_paths: tuple[str, ...] = ()
    config_paths: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()
    registration: RuntimeAdapterRegistration | None = None

    def __post_init__(self) -> None:
        runtime_id = self.runtime_id.strip()
        if not runtime_id:
            raise ValueError("runtime_id must not be empty.")
        if any(character.isspace() for character in runtime_id) or "/" in runtime_id:
            raise ValueError("runtime_id must be a stable adapter identifier.")
        object.__setattr__(self, "runtime_id", runtime_id)
        if self.registration is not None:
            if not isinstance(self.registration, RuntimeAdapterRegistration):
                raise TypeError("registration must be a RuntimeAdapterRegistration when provided.")
            if self.registration.runtime_id != runtime_id:
                raise ValueError("registration.runtime_id must match descriptor.runtime_id.")
        for field_name in ("protected_paths", "credential_paths", "config_paths"):
            object.__setattr__(
                self,
                field_name,
                _normalize_path_metadata(getattr(self, field_name), field_name=field_name),
            )
        object.__setattr__(self, "capabilities", _normalize_capabilities(self.capabilities))

    def supports_capability(self, capability: str) -> bool:
        """Return whether this adapter statically advertises ``capability``."""

        return isinstance(capability, str) and capability.strip() in self.capabilities

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, non-secret representation for diagnostics/tests."""

        return {
            "runtime_id": self.runtime_id,
            "protected_paths": list(self.protected_paths),
            "credential_paths": list(self.credential_paths),
            "config_paths": list(self.config_paths),
            "capabilities": sorted(self.capabilities),
        }


@dataclass(frozen=True)
class CapabilityReport:
    runtime_id: str
    available: bool
    command: str
    version_text: str | None = None
    supports_raw_log_stream: bool = True
    supports_structured_log_stream: bool = False
    supports_questions: bool = False
    supports_resume: bool = False
    supports_subagents: bool = False
    supports_non_interactive_mode: bool = True
    supports_working_directory_control: bool = True
    supports_env_injection: bool = True
    supports_permission_policy: bool = False
    supports_live_decisions: bool = False
    supports_deferred_resume: bool = False
    preferred_transport: str = "subprocess"
