from __future__ import annotations

import pytest

from aidd.core.evidence_freshness import (
    EvidenceFreshnessRequest,
    EvidenceFreshnessStatus,
    classify_evidence_freshness,
)

_CANDIDATE_SHA = "a" * 40
_HISTORICAL_SHA = "b" * 40


def _request(**overrides: object) -> EvidenceFreshnessRequest:
    values: dict[str, object] = {
        "candidate_sha": _CANDIDATE_SHA,
        "evidence_sha": _CANDIDATE_SHA,
        "evidence_schema_version": 1,
        "target_pin": "linux-py313",
        "evidence_target_pin": "linux-py313",
        "locator": "bundles/run-1/summary.json",
    }
    values.update(overrides)
    return EvidenceFreshnessRequest(**values)  # type: ignore[arg-type]


def test_matching_identity_is_current() -> None:
    result = classify_evidence_freshness(_request())

    assert result.status is EvidenceFreshnessStatus.CURRENT
    assert result.state == "current"
    assert result.is_current is True
    assert result.to_dict()["schema_version"] == 1


def test_git_sha_comparison_is_case_insensitive() -> None:
    result = classify_evidence_freshness(
        _request(candidate_sha=_CANDIDATE_SHA.upper(), evidence_sha=_CANDIDATE_SHA.upper())
    )

    assert result.status is EvidenceFreshnessStatus.CURRENT


def test_historical_sha_is_stale_on_a_different_candidate() -> None:
    result = classify_evidence_freshness(_request(evidence_sha=_HISTORICAL_SHA))

    assert result.status is EvidenceFreshnessStatus.STALE
    assert "different candidate Git SHA" in result.reason


def test_unsupported_schema_is_incompatible() -> None:
    result = classify_evidence_freshness(_request(evidence_schema_version=2))

    assert result.status is EvidenceFreshnessStatus.INCOMPATIBLE
    assert "schema version 2" in result.reason


def test_target_pin_mismatch_is_incompatible() -> None:
    result = classify_evidence_freshness(_request(evidence_target_pin="macos-py313"))

    assert result.status is EvidenceFreshnessStatus.INCOMPATIBLE
    assert "target pin" in result.reason


@pytest.mark.parametrize(
    "overrides",
    [
        {"locator": None},
        {"locator_available": False},
        {"candidate_sha": None},
        {"evidence_sha": None},
        {"evidence_schema_version": None},
        {"target_pin": None},
        {"evidence_target_pin": None},
    ],
)
def test_missing_identity_or_locator_is_unavailable(overrides: dict[str, object]) -> None:
    result = classify_evidence_freshness(_request(**overrides))

    assert result.status is EvidenceFreshnessStatus.UNAVAILABLE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_schema_version", True),
        ("evidence_schema_version", 0),
        ("locator_available", None),
        ("supported_schema_versions", (1, 1)),
    ],
)
def test_request_rejects_malformed_typed_identity(field: str, value: object) -> None:
    with pytest.raises(ValueError, match=field):
        _request(**{field: value})
