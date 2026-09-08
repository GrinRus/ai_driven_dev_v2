from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from aidd.harness.evidence_archive_contract import (
    EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION,
    EVIDENCE_ARCHIVE_REFERENCE_MODE,
    EvidenceArchiveContractError,
    EvidenceArchiveRetention,
    EvidenceRedaction,
    dump_evidence_archive_retention,
    validate_evidence_archive_retention,
)


def _retention(tmp_path: Path) -> EvidenceArchiveRetention:
    return EvidenceArchiveRetention(
        locator=(tmp_path / "retained" / "eval-001.tar.zst").as_posix(),
        sha256="a" * 64,
        size_bytes=128,
        source_revision="abcdef1234567",
        target_pin="1234567890abc",
        evidence_schema_version=2,
        redaction=EvidenceRedaction(
            credentials_removed=True,
            provider_payloads_removed=True,
            target_paths_redacted=True,
            redacted_paths=("harness-metadata.json", "canonical-evidence/runtime.log"),
        ),
    )


def test_retention_round_trips_deterministically(tmp_path: Path) -> None:
    retention = validate_evidence_archive_retention(_retention(tmp_path))

    assert retention.schema_version == EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION
    assert retention.reference_mode == EVIDENCE_ARCHIVE_REFERENCE_MODE
    assert retention.digest == retention.sha256
    assert retention.revision == retention.source_revision
    payload = json.loads(dump_evidence_archive_retention(retention))
    assert payload["redaction"]["redacted_paths"] == [
        "canonical-evidence/runtime.log",
        "harness-metadata.json",
    ]
    assert EvidenceArchiveRetention.from_dict(payload) == retention


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("sha256", "not-a-digest", "SHA-256"),
        ("size_bytes", 0, "positive"),
        ("source_revision", "unknown", "revision"),
        ("target_pin", "", "target_pin"),
        ("locator", "retained/eval-001.tar.zst", "absolute"),
        ("locator", "/tmp/.aidd/eval-001.tar.zst", "mutable"),
    ),
)
def test_retention_rejects_incomplete_integrity_or_provenance(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(EvidenceArchiveContractError, match=message):
        validate_evidence_archive_retention(replace(_retention(tmp_path), **{field: value}))


@pytest.mark.parametrize(
    ("redaction", "message"),
    (
        (
            EvidenceRedaction(
                credentials_removed=False,
                provider_payloads_removed=True,
                target_paths_redacted=True,
            ),
            "credentials",
        ),
        (
            EvidenceRedaction(
                credentials_removed=True,
                provider_payloads_removed=False,
                target_paths_redacted=True,
            ),
            "provider",
        ),
        (
            EvidenceRedaction(
                credentials_removed=True,
                provider_payloads_removed=True,
                target_paths_redacted=False,
            ),
            "target_paths",
        ),
        (
            EvidenceRedaction(
                credentials_removed=True,
                provider_payloads_removed=True,
                target_paths_redacted=True,
                redacted_paths=("../secret",),
            ),
            "contained",
        ),
    ),
)
def test_redaction_contract_fails_closed(
    tmp_path: Path,
    redaction: EvidenceRedaction,
    message: str,
) -> None:
    with pytest.raises(EvidenceArchiveContractError, match=message):
        validate_evidence_archive_retention(replace(_retention(tmp_path), redaction=redaction))


def test_from_dict_requires_all_archive_metadata() -> None:
    with pytest.raises(EvidenceArchiveContractError, match="sha256.*target_pin"):
        EvidenceArchiveRetention.from_dict(
            {
                "locator": "/retained/eval-001.tar.zst",
                "size_bytes": 128,
                "source_revision": "abcdef1234567",
                "evidence_schema_version": 2,
                "redaction": {
                    "credentials_removed": True,
                    "provider_payloads_removed": True,
                    "target_paths_redacted": True,
                    "redacted_paths": [],
                    "policy_version": 1,
                },
                "schema_version": 1,
                "reference_mode": "external-immutable",
            }
        )


def test_uri_locator_is_supported_but_userinfo_is_rejected(tmp_path: Path) -> None:
    retention = replace(_retention(tmp_path), locator="https://evidence.example/eval-001.tar.zst")
    assert validate_evidence_archive_retention(retention).locator.startswith("https://")
    with pytest.raises(EvidenceArchiveContractError, match="user credentials"):
        validate_evidence_archive_retention(
            replace(retention, locator="https://user:secret@evidence.example/eval-001.tar.zst")
        )
