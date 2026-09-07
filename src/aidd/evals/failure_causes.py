"""Versioned failure-cause taxonomy for evaluation reports.

Verdict status and first decisive cause are separate facts.  This module defines the
current-format cause object and the compatibility rules that keep those facts from
contradicting one another.  Report projections may adopt the model incrementally; old
boundary category names are accepted only through the explicit legacy mapping below.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any


class FailureCauseCategory(StrEnum):
    """Canonical owner of a failed evaluation signal."""

    ENVIRONMENT = "environment"
    INFRASTRUCTURE = "infrastructure"
    ADAPTER = "adapter"
    RUNTIME = "runtime"
    VALIDATION = "validation"
    SCENARIO_VERIFICATION = "scenario-verification"
    NONE = "none"


class FailureCausePhase(StrEnum):
    """Lifecycle phase in which the first decisive cause was observed."""

    PREPARATION = "preparation"
    INSTALL = "install"
    SETUP = "setup"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    TEARDOWN = "teardown"
    ANALYSIS = "analysis"


class FailureCauseSource(StrEnum):
    """Typed producer of the first decisive signal."""

    ENVIRONMENT = "environment"
    HARNESS = "harness"
    ADAPTER = "adapter"
    RUNTIME = "runtime"
    VALIDATOR = "validator"
    SCENARIO = "scenario"
    NONE = "none"


FAILURE_VERDICTS = ("pass", "fail", "blocked", "infra-fail")

_ALLOWED_CATEGORIES_BY_VERDICT: dict[str, frozenset[FailureCauseCategory]] = {
    "pass": frozenset({FailureCauseCategory.NONE}),
    "fail": frozenset(
        {
            FailureCauseCategory.ADAPTER,
            FailureCauseCategory.RUNTIME,
            FailureCauseCategory.VALIDATION,
            FailureCauseCategory.SCENARIO_VERIFICATION,
        }
    ),
    "blocked": frozenset({FailureCauseCategory.SCENARIO_VERIFICATION}),
    "infra-fail": frozenset(
        {
            FailureCauseCategory.ENVIRONMENT,
            FailureCauseCategory.INFRASTRUCTURE,
        }
    ),
}

_ALLOWED_SOURCES_BY_CATEGORY: dict[FailureCauseCategory, frozenset[FailureCauseSource]] = {
    FailureCauseCategory.ENVIRONMENT: frozenset({FailureCauseSource.ENVIRONMENT}),
    FailureCauseCategory.INFRASTRUCTURE: frozenset(
        {FailureCauseSource.ENVIRONMENT, FailureCauseSource.HARNESS}
    ),
    FailureCauseCategory.ADAPTER: frozenset({FailureCauseSource.ADAPTER}),
    FailureCauseCategory.RUNTIME: frozenset(
        {FailureCauseSource.RUNTIME, FailureCauseSource.ADAPTER}
    ),
    FailureCauseCategory.VALIDATION: frozenset({FailureCauseSource.VALIDATOR}),
    FailureCauseCategory.SCENARIO_VERIFICATION: frozenset(
        {FailureCauseSource.SCENARIO, FailureCauseSource.HARNESS}
    ),
    FailureCauseCategory.NONE: frozenset({FailureCauseSource.NONE}),
}

# Historical boundary names were not all semantically distinct.  Keep their conversion
# explicit so a reader never silently guesses a cause category from a verdict or ordinal.
LEGACY_FAILURE_CATEGORY_MAP: dict[str, FailureCauseCategory] = {
    "": FailureCauseCategory.NONE,
    "none": FailureCauseCategory.NONE,
    "environment": FailureCauseCategory.ENVIRONMENT,
    "adapter": FailureCauseCategory.ADAPTER,
    "runtime": FailureCauseCategory.RUNTIME,
    "validation": FailureCauseCategory.VALIDATION,
    "scenario-verification": FailureCauseCategory.SCENARIO_VERIFICATION,
    "scenario_verification": FailureCauseCategory.SCENARIO_VERIFICATION,
    "infrastructure": FailureCauseCategory.INFRASTRUCTURE,
    "harness": FailureCauseCategory.INFRASTRUCTURE,
    "setup": FailureCauseCategory.INFRASTRUCTURE,
    "target-setup": FailureCauseCategory.INFRASTRUCTURE,
    "target_setup": FailureCauseCategory.INFRASTRUCTURE,
}


def _normalize_enum[T: StrEnum](value: T | str, *, enum_type: type[T], field_name: str) -> T:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        allowed = ", ".join(f"`{item.value}`" for item in enum_type)
        raise ValueError(f"{field_name} must be one of: {allowed}.") from exc


def _normalize_required_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty.")
    return normalized


def _normalize_evidence_link(value: str | None, *, category: FailureCauseCategory) -> str | None:
    if value is None:
        if category is not FailureCauseCategory.NONE:
            raise ValueError("evidence_link is required for a failure cause.")
        return None
    normalized = _normalize_required_text(value, field_name="evidence_link")
    if "\\" in normalized:
        raise ValueError("evidence_link must use a relative POSIX path.")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("evidence_link must stay workspace-relative.")
    return path.as_posix()


@dataclass(frozen=True, slots=True)
class FailureCause:
    """Current-format first decisive failure cause.

    ``evidence_link`` is a bundle-relative path and is mandatory for every non-``none``
    cause.  The associated verdict is deliberately not stored here; callers validate the
    two independent facts with :func:`validate_verdict_compatibility`.
    """

    category: FailureCauseCategory
    phase: FailureCausePhase
    source: FailureCauseSource
    reason: str
    evidence_link: str | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        category = _normalize_enum(
            self.category,
            enum_type=FailureCauseCategory,
            field_name="category",
        )
        phase = _normalize_enum(
            self.phase,
            enum_type=FailureCausePhase,
            field_name="phase",
        )
        source = _normalize_enum(
            self.source,
            enum_type=FailureCauseSource,
            field_name="source",
        )
        reason = _normalize_required_text(self.reason, field_name="reason")
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise ValueError("schema_version must be integer 1.")
        if self.schema_version != 1:
            raise ValueError(f"Unsupported failure-cause schema: {self.schema_version}")
        if source not in _ALLOWED_SOURCES_BY_CATEGORY[category]:
            allowed = ", ".join(
                f"`{item.value}`" for item in _ALLOWED_SOURCES_BY_CATEGORY[category]
            )
            raise ValueError(
                f"source `{source.value}` is incompatible with category `{category.value}`; "
                f"expected one of: {allowed}."
            )
        evidence_link = _normalize_evidence_link(
            self.evidence_link,
            category=category,
        )
        if category is FailureCauseCategory.NONE:
            if phase is not FailureCausePhase.ANALYSIS or reason.lower() != "no failure cause":
                raise ValueError(
                    "category `none` requires analysis phase and reason `No failure cause`."
                )
        object.__setattr__(self, "category", category)
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "evidence_link", evidence_link)

    @classmethod
    def none(cls) -> FailureCause:
        return cls(
            category=FailureCauseCategory.NONE,
            phase=FailureCausePhase.ANALYSIS,
            source=FailureCauseSource.NONE,
            reason="No failure cause",
        )

    @classmethod
    def from_dict(cls, payload: object) -> FailureCause:
        if not isinstance(payload, dict):
            raise ValueError("Failure cause must be a JSON object.")
        required = (
            "schema_version",
            "category",
            "phase",
            "source",
            "reason",
            "evidence_link",
        )
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError(
                "Failure cause is missing required fields: " + ", ".join(missing) + "."
            )
        evidence_link = payload["evidence_link"]
        if evidence_link is not None and not isinstance(evidence_link, str):
            raise ValueError("evidence_link must be a string or null.")
        return cls(
            schema_version=payload["schema_version"],
            category=payload["category"],
            phase=payload["phase"],
            source=payload["source"],
            reason=payload["reason"],
            evidence_link=evidence_link,
        )

    @classmethod
    def from_legacy(
        cls,
        *,
        category: str,
        phase: FailureCausePhase | str,
        source: FailureCauseSource | str,
        reason: str,
        evidence_link: str | None,
    ) -> FailureCause:
        normalized_category = category.strip().lower().replace(" ", "-")
        try:
            mapped_category = LEGACY_FAILURE_CATEGORY_MAP[normalized_category]
        except KeyError as exc:
            raise ValueError(f"Unknown legacy failure category: {category!r}.") from exc
        if mapped_category is FailureCauseCategory.NONE:
            return cls.none()
        return cls(
            category=mapped_category,
            phase=_normalize_enum(
                phase,
                enum_type=FailureCausePhase,
                field_name="phase",
            ),
            source=_normalize_enum(
                source,
                enum_type=FailureCauseSource,
                field_name="source",
            ),
            reason=reason,
            evidence_link=evidence_link,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "category": self.category.value,
            "phase": self.phase.value,
            "source": self.source.value,
            "reason": self.reason,
            "evidence_link": self.evidence_link,
        }


def validate_verdict_compatibility(
    *,
    verdict: str,
    cause: FailureCause | None,
) -> None:
    """Reject contradictory execution verdict and first-cause combinations."""

    normalized_verdict = verdict.strip().lower()
    if normalized_verdict not in FAILURE_VERDICTS:
        allowed = ", ".join(f"`{item}`" for item in FAILURE_VERDICTS)
        raise ValueError(f"verdict must be one of: {allowed}.")
    if normalized_verdict == "pass":
        if cause is not None and cause.category is not FailureCauseCategory.NONE:
            raise ValueError("pass verdict cannot carry a failure cause.")
        return
    if cause is None:
        raise ValueError(f"{normalized_verdict} verdict requires a failure cause.")
    allowed_categories = _ALLOWED_CATEGORIES_BY_VERDICT[normalized_verdict]
    if cause.category not in allowed_categories:
        allowed = ", ".join(f"`{item.value}`" for item in allowed_categories)
        raise ValueError(
            f"verdict `{normalized_verdict}` is incompatible with cause "
            f"`{cause.category.value}`; expected one of: {allowed}."
        )


__all__ = [
    "FAILURE_VERDICTS",
    "LEGACY_FAILURE_CATEGORY_MAP",
    "FailureCause",
    "FailureCauseCategory",
    "FailureCausePhase",
    "FailureCauseSource",
    "validate_verdict_compatibility",
]
