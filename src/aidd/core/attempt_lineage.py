"""Typed lineage for stage, task, and aggregate-finalization attempts.

Attempt directory numbers are local storage coordinates, not evidence of why an
attempt exists.  Current artifacts carry an explicit lineage object; retired
ordinal-only payloads are rejected by lifecycle readers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any


class AttemptScope(StrEnum):
    STAGE = "stage"
    TASK = "task"
    FINALIZATION = "finalization"


class AttemptKind(StrEnum):
    INITIAL = "initial"
    REPAIR = "repair"
    RESUME = "resume"
    INTERVENTION = "intervention"
    REPAIR_EXTENSION = "repair-extension"
    TASK = "task"
    FINALIZATION = "finalization"
    UNKNOWN = "unknown"


_STAGE_KINDS = frozenset(
    {
        AttemptKind.INITIAL,
        AttemptKind.REPAIR,
        AttemptKind.RESUME,
        AttemptKind.INTERVENTION,
        AttemptKind.REPAIR_EXTENSION,
        AttemptKind.UNKNOWN,
    }
)
_TASK_KINDS = frozenset({AttemptKind.TASK, AttemptKind.UNKNOWN})
_FINALIZATION_KINDS = frozenset({AttemptKind.FINALIZATION, AttemptKind.UNKNOWN})


def _normalize_relative_path(value: str) -> str:
    normalized = value.strip()
    if not normalized or "\\" in normalized:
        raise ValueError("Attempt lineage parent path must be a relative POSIX path.")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("Attempt lineage parent path must stay workspace-relative.")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class AttemptLineage:
    """Versioned identity and optional parent link for one durable attempt."""

    scope: AttemptScope
    attempt_kind: AttemptKind
    attempt_number: int
    parent_attempt_path: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        try:
            scope = AttemptScope(self.scope)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unknown attempt lineage scope: {self.scope}") from exc
        try:
            attempt_kind = AttemptKind(self.attempt_kind)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Unknown attempt lineage kind: {self.attempt_kind}") from exc
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise ValueError("Attempt lineage schema_version must be integer 1.")
        if self.schema_version != 1:
            raise ValueError(f"Unsupported attempt lineage schema: {self.schema_version}")
        if not isinstance(self.attempt_number, int) or isinstance(self.attempt_number, bool):
            raise ValueError("Attempt lineage number must be a positive integer.")
        if self.attempt_number < 1:
            raise ValueError("Attempt lineage number must be a positive integer.")
        allowed = {
            AttemptScope.STAGE: _STAGE_KINDS,
            AttemptScope.TASK: _TASK_KINDS,
            AttemptScope.FINALIZATION: _FINALIZATION_KINDS,
        }[scope]
        if attempt_kind not in allowed:
            raise ValueError(
                f"Attempt lineage kind `{attempt_kind.value}` is invalid for `{scope.value}` scope."
            )
        parent = self.parent_attempt_path
        if parent is not None:
            parent = _normalize_relative_path(parent)
        object.__setattr__(self, "scope", scope)
        object.__setattr__(self, "attempt_kind", attempt_kind)
        object.__setattr__(self, "parent_attempt_path", parent)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "attempt_kind": self.attempt_kind.value,
            "attempt_number": self.attempt_number,
            "parent_attempt_path": self.parent_attempt_path,
        }

    @classmethod
    def from_dict(cls, payload: object) -> AttemptLineage:
        if not isinstance(payload, dict):
            raise ValueError("Attempt lineage must be a JSON object.")
        required = ("schema_version", "scope", "attempt_kind", "attempt_number")
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError(f"Attempt lineage is missing required fields: {', '.join(missing)}.")
        parent = payload.get("parent_attempt_path")
        if parent is not None and not isinstance(parent, str):
            raise ValueError("Attempt lineage parent_attempt_path must be a string or null.")
        return cls(
            schema_version=payload["schema_version"],
            scope=payload["scope"],
            attempt_kind=payload["attempt_kind"],
            attempt_number=payload["attempt_number"],
            parent_attempt_path=parent,
        )

    def validate_identity(self, *, scope: AttemptScope, attempt_number: int) -> None:
        if self.scope is not AttemptScope(scope):
            raise ValueError(
                "Attempt lineage scope does not match its containing artifact: "
                f"expected {AttemptScope(scope).value}, got {self.scope.value}."
            )
        if self.attempt_number != attempt_number:
            raise ValueError(
                "Attempt lineage number does not match its containing artifact: "
                f"expected {attempt_number}, got {self.attempt_number}."
            )


@dataclass(frozen=True, slots=True)
class FinalizationAttemptState:
    """Typed current-format view of aggregate-finalization state."""

    attempt_number: int
    status: str
    blocker: str | None = None
    created_at_utc: str | None = None
    updated_at_utc: str | None = None
    lineage: AttemptLineage | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.attempt_number, int) or isinstance(self.attempt_number, bool):
            raise ValueError("Finalization attempt number must be a positive integer.")
        if self.attempt_number < 1:
            raise ValueError("Finalization attempt number must be a positive integer.")
        if not isinstance(self.status, str) or not self.status.strip():
            raise ValueError("Finalization attempt status must not be empty.")
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise ValueError("Finalization attempt schema_version must be integer 1.")
        if self.schema_version != 1:
            raise ValueError(f"Unsupported finalization attempt schema: {self.schema_version}")
        if self.lineage is not None:
            self.lineage.validate_identity(
                scope=AttemptScope.FINALIZATION,
                attempt_number=self.attempt_number,
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attempt_number": self.attempt_number,
            "status": self.status,
            "blocker": self.blocker,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            **({"lineage": self.lineage.to_dict()} if self.lineage is not None else {}),
        }

    @classmethod
    def from_dict(cls, payload: object) -> FinalizationAttemptState:
        if not isinstance(payload, dict):
            raise ValueError("Finalization attempt state must be a JSON object.")
        if "schema_version" not in payload:
            raise ValueError("Finalization attempt state requires schema_version.")
        schema_version = payload["schema_version"]
        if "attempt_number" not in payload or "status" not in payload:
            raise ValueError("Finalization attempt state requires attempt_number and status.")
        blocker = payload.get("blocker")
        if blocker is not None and not isinstance(blocker, str):
            raise ValueError("Finalization attempt blocker must be a string or null.")
        created_at_utc = payload.get("created_at_utc")
        updated_at_utc = payload.get("updated_at_utc")
        for field_name, value in (
            ("created_at_utc", created_at_utc),
            ("updated_at_utc", updated_at_utc),
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Finalization attempt {field_name} must be a string or null.")
        if "lineage" not in payload:
            raise ValueError("Finalization attempt state requires current-format lineage.")
        lineage = AttemptLineage.from_dict(payload["lineage"])
        return cls(
            schema_version=schema_version,
            attempt_number=payload["attempt_number"],
            status=payload["status"],
            blocker=blocker,
            created_at_utc=created_at_utc,
            updated_at_utc=updated_at_utc,
            lineage=lineage,
        )

    @property
    def effective_lineage(self) -> AttemptLineage:
        if self.lineage is None:
            raise ValueError("Finalization attempt state is missing current-format lineage.")
        return self.lineage


__all__ = [
    "AttemptKind",
    "AttemptLineage",
    "AttemptScope",
    "FinalizationAttemptState",
]
