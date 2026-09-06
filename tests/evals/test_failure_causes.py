from __future__ import annotations

import json

import pytest

from aidd.evals.failure_causes import (
    FailureCause,
    FailureCauseCategory,
    FailureCausePhase,
    FailureCauseSource,
    validate_verdict_compatibility,
)


def _validation_cause(**overrides: object) -> FailureCause:
    values: dict[str, object] = {
        "category": FailureCauseCategory.VALIDATION,
        "phase": FailureCausePhase.VERIFICATION,
        "source": FailureCauseSource.VALIDATOR,
        "reason": "plan.md is malformed",
        "evidence_link": "validator-report.md",
    }
    values.update(overrides)
    return FailureCause(**values)


def test_failure_cause_round_trip_is_versioned_and_json_safe() -> None:
    cause = _validation_cause()

    payload = cause.to_dict()

    assert payload["schema_version"] == 1
    assert json.loads(json.dumps(payload)) == payload
    assert FailureCause.from_dict(payload) == cause


def test_failure_cause_none_is_the_only_no_failure_value() -> None:
    cause = FailureCause.none()

    assert cause.to_dict() == {
        "schema_version": 1,
        "category": "none",
        "phase": "analysis",
        "source": "none",
        "reason": "No failure cause",
        "evidence_link": None,
    }
    validate_verdict_compatibility(verdict="pass", cause=cause)
    validate_verdict_compatibility(verdict="pass", cause=None)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"schema_version": 2},
        {
            "schema_version": 1,
            "category": "validation",
            "phase": "verification",
            "source": "validator",
            "reason": "broken",
        },
    ],
)
def test_failure_cause_rejects_incomplete_or_retired_payloads(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        FailureCause.from_dict(payload)


@pytest.mark.parametrize(
    "link",
    ("/tmp/validator-report.md", "../validator-report.md", "reports\\validator.md", " "),
)
def test_failure_cause_requires_relative_evidence_link(link: str) -> None:
    with pytest.raises(ValueError, match="evidence_link"):
        _validation_cause(evidence_link=link)


def test_failure_cause_rejects_category_source_contradiction() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        _validation_cause(source=FailureCauseSource.RUNTIME)


@pytest.mark.parametrize(
    ("legacy_category", "expected_category", "source"),
    [
        ("environment", FailureCauseCategory.ENVIRONMENT, FailureCauseSource.ENVIRONMENT),
        ("harness", FailureCauseCategory.INFRASTRUCTURE, FailureCauseSource.HARNESS),
        ("target-setup", FailureCauseCategory.INFRASTRUCTURE, FailureCauseSource.HARNESS),
        (
            "scenario_verification",
            FailureCauseCategory.SCENARIO_VERIFICATION,
            FailureCauseSource.SCENARIO,
        ),
    ],
)
def test_failure_cause_legacy_mapping_is_explicit(
    legacy_category: str,
    expected_category: FailureCauseCategory,
    source: FailureCauseSource,
) -> None:
    cause = FailureCause.from_legacy(
        category=legacy_category,
        phase=FailureCausePhase.SETUP,
        source=source,
        reason="legacy signal",
        evidence_link="setup-transcript.json",
    )

    assert cause.category is expected_category


def test_failure_cause_legacy_none_discards_ordinal_only_signal() -> None:
    cause = FailureCause.from_legacy(
        category="none",
        phase=FailureCausePhase.EXECUTION,
        source=FailureCauseSource.RUNTIME,
        reason="attempt count was one",
        evidence_link=None,
    )

    assert cause == FailureCause.none()


def test_failure_cause_legacy_unknown_category_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown legacy failure category"):
        FailureCause.from_legacy(
            category="mystery",
            phase=FailureCausePhase.EXECUTION,
            source=FailureCauseSource.RUNTIME,
            reason="unknown",
            evidence_link="runtime.log",
        )


@pytest.mark.parametrize(
    ("verdict", "cause"),
    [
        ("fail", _validation_cause()),
        (
            "fail",
            FailureCause(
                category=FailureCauseCategory.ADAPTER,
                phase=FailureCausePhase.EXECUTION,
                source=FailureCauseSource.ADAPTER,
                reason="adapter exited non-zero",
                evidence_link="runtime.log",
            ),
        ),
        (
            "blocked",
            FailureCause(
                category=FailureCauseCategory.SCENARIO_VERIFICATION,
                phase=FailureCausePhase.VERIFICATION,
                source=FailureCauseSource.SCENARIO,
                reason="required answer is unresolved",
                evidence_link="questions.md",
            ),
        ),
        (
            "infra-fail",
            FailureCause(
                category=FailureCauseCategory.INFRASTRUCTURE,
                phase=FailureCausePhase.SETUP,
                source=FailureCauseSource.HARNESS,
                reason="fixture setup failed",
                evidence_link="setup-transcript.json",
            ),
        ),
    ],
)
def test_failure_cause_compatible_verdicts_are_accepted(
    verdict: str,
    cause: FailureCause,
) -> None:
    validate_verdict_compatibility(verdict=verdict, cause=cause)


@pytest.mark.parametrize(
    ("verdict", "cause"),
    [
        ("fail", None),
        ("fail", FailureCause.none()),
        ("blocked", _validation_cause()),
        ("infra-fail", _validation_cause()),
        (
            "pass",
            FailureCause(
                category=FailureCauseCategory.RUNTIME,
                phase=FailureCausePhase.EXECUTION,
                source=FailureCauseSource.RUNTIME,
                reason="runtime failed",
                evidence_link="runtime.log",
            ),
        ),
    ],
)
def test_failure_cause_contradictory_verdicts_are_rejected(
    verdict: str,
    cause: FailureCause | None,
) -> None:
    with pytest.raises(ValueError):
        validate_verdict_compatibility(verdict=verdict, cause=cause)


def test_failure_cause_unknown_verdict_is_rejected() -> None:
    with pytest.raises(ValueError, match="verdict must be one of"):
        validate_verdict_compatibility(verdict="unknown", cause=None)
