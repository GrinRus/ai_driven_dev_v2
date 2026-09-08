"""Typed freshness classification for retained evidence.

Evidence is useful for a candidate only when its identity can be compared with the
candidate currently under evaluation.  This module deliberately contains no filesystem,
Git, or runtime integration: callers provide the observed identity and the result is a
small, deterministic core projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

FRESHNESS_CONTRACT_SCHEMA_VERSION = 1


class EvidenceFreshnessStatus(StrEnum):
    """The four operator-visible states for a retained evidence record."""

    CURRENT = "current"
    STALE = "stale"
    INCOMPATIBLE = "incompatible"
    UNAVAILABLE = "unavailable"


def _optional_text(value: str | None, *, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null.")
    normalized = value.strip()
    return normalized or None


def _optional_sha(value: str | None, *, field_name: str) -> str | None:
    normalized = _optional_text(value, field_name=field_name)
    return None if normalized is None else normalized.lower()


def _optional_schema_version(value: int | None, *, field_name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive integer or null.")
    return value


def _supported_versions(value: tuple[int, ...]) -> tuple[int, ...]:
    if not isinstance(value, tuple) or not value:
        raise ValueError("supported_schema_versions must be a non-empty tuple.")
    if any(type(version) is not int or version < 1 for version in value):
        raise ValueError("supported_schema_versions must contain positive integers.")
    normalized = tuple(sorted(set(value)))
    if len(normalized) != len(value):
        raise ValueError("supported_schema_versions must not contain duplicates.")
    return normalized


@dataclass(frozen=True, slots=True)
class EvidenceFreshnessRequest:
    """Observed evidence identity and the candidate identity to compare it with.

    ``locator_available`` is supplied by the owning reader.  It defaults to ``True``
    because a caller that already has a successfully loaded record has established
    retrievability; readers that only have metadata should pass ``False`` until the
    locator is resolved.
    """

    candidate_sha: str | None
    evidence_sha: str | None
    evidence_schema_version: int | None
    target_pin: str | None
    evidence_target_pin: str | None
    locator: str | None
    locator_available: bool = True
    supported_schema_versions: tuple[int, ...] = (1,)

    def __post_init__(self) -> None:
        for field_name in ("target_pin", "evidence_target_pin", "locator"):
            object.__setattr__(
                self,
                field_name,
                _optional_text(getattr(self, field_name), field_name=field_name),
            )
        for field_name in ("candidate_sha", "evidence_sha"):
            object.__setattr__(
                self,
                field_name,
                _optional_sha(getattr(self, field_name), field_name=field_name),
            )
        object.__setattr__(
            self,
            "evidence_schema_version",
            _optional_schema_version(
                self.evidence_schema_version,
                field_name="evidence_schema_version",
            ),
        )
        if type(self.locator_available) is not bool:
            raise ValueError("locator_available must be a boolean.")
        object.__setattr__(
            self, "supported_schema_versions", _supported_versions(self.supported_schema_versions)
        )


@dataclass(frozen=True, slots=True)
class EvidenceFreshness:
    """Deterministic freshness result with the compared identity retained for audit."""

    status: EvidenceFreshnessStatus
    reason: str
    candidate_sha: str | None
    evidence_sha: str | None
    evidence_schema_version: int | None
    target_pin: str | None
    evidence_target_pin: str | None
    locator: str | None

    @property
    def state(self) -> str:
        """String alias for API/read-model consumers that call the value a state."""

        return self.status.value

    @property
    def is_current(self) -> bool:
        return self.status is EvidenceFreshnessStatus.CURRENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": FRESHNESS_CONTRACT_SCHEMA_VERSION,
            "status": self.status.value,
            "reason": self.reason,
            "candidate_sha": self.candidate_sha,
            "evidence_sha": self.evidence_sha,
            "evidence_schema_version": self.evidence_schema_version,
            "target_pin": self.target_pin,
            "evidence_target_pin": self.evidence_target_pin,
            "locator": self.locator,
        }


def classify_evidence_freshness(request: EvidenceFreshnessRequest) -> EvidenceFreshness:
    """Classify retained evidence without guessing missing provenance.

    The order is intentional: an unreadable locator is unavailable; a readable record
    with an unsupported schema or target pin is incompatible; a valid historical record
    for another candidate is stale; only a complete identity match is current.
    """

    if request.locator is None or not request.locator_available:
        status = EvidenceFreshnessStatus.UNAVAILABLE
        reason = "Evidence locator is unavailable."
    elif request.evidence_schema_version is None:
        status = EvidenceFreshnessStatus.UNAVAILABLE
        reason = "Evidence schema version is unavailable."
    elif request.evidence_schema_version not in request.supported_schema_versions:
        status = EvidenceFreshnessStatus.INCOMPATIBLE
        supported = ", ".join(str(v) for v in request.supported_schema_versions)
        reason = (
            f"Evidence schema version {request.evidence_schema_version} is not supported; "
            f"supported versions are {supported}."
        )
    elif request.target_pin is None or request.evidence_target_pin is None:
        status = EvidenceFreshnessStatus.UNAVAILABLE
        reason = "Candidate or evidence target pin is unavailable."
    elif request.target_pin != request.evidence_target_pin:
        status = EvidenceFreshnessStatus.INCOMPATIBLE
        reason = (
            "Evidence target pin does not match the candidate target pin "
            f"({request.evidence_target_pin!r} != {request.target_pin!r})."
        )
    elif request.candidate_sha is None or request.evidence_sha is None:
        status = EvidenceFreshnessStatus.UNAVAILABLE
        reason = "Candidate or evidence Git SHA is unavailable."
    elif request.candidate_sha != request.evidence_sha:
        status = EvidenceFreshnessStatus.STALE
        reason = (
            "Evidence was produced for a different candidate Git SHA "
            f"({request.evidence_sha}); current candidate is {request.candidate_sha}."
        )
    else:
        status = EvidenceFreshnessStatus.CURRENT
        reason = "Evidence matches the candidate SHA, schema, target pin, and locator."

    return EvidenceFreshness(
        status=status,
        reason=reason,
        candidate_sha=request.candidate_sha,
        evidence_sha=request.evidence_sha,
        evidence_schema_version=request.evidence_schema_version,
        target_pin=request.target_pin,
        evidence_target_pin=request.evidence_target_pin,
        locator=request.locator,
    )


# Keep the verb used by the roadmap available for callers that prefer an evaluator name.
evaluate_evidence_freshness = classify_evidence_freshness


__all__ = [
    "EvidenceFreshness",
    "EvidenceFreshnessRequest",
    "EvidenceFreshnessStatus",
    "FRESHNESS_CONTRACT_SCHEMA_VERSION",
    "classify_evidence_freshness",
    "evaluate_evidence_freshness",
]
