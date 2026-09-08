"""Contract for locating and trusting an immutable retained evidence archive.

The result-bundle contract describes the files *inside* a bundle.  This module describes
the metadata needed when that bundle is copied to a retention store.  It deliberately
does not read or write an archive; the exporter and verifier can use this value object
without coupling the contract to a filesystem, object store, or runtime adapter.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, cast
from urllib.parse import urlsplit

EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION = 1
EVIDENCE_ARCHIVE_REFERENCE_MODE = "external-immutable"
EVIDENCE_SCHEMA_VERSION = 2
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REVISION = re.compile(r"^[0-9a-f]{7,64}$")
_URI_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*$")
_CONTROL_CHARACTERS = frozenset(chr(value) for value in range(32)) | {chr(127)}


class EvidenceArchiveContractError(ValueError):
    """Raised when retained evidence metadata is incomplete or unsafe."""


def _required_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceArchiveContractError(f"{field} must be a non-empty string.")
    normalized = value.strip()
    if any(character in _CONTROL_CHARACTERS for character in normalized):
        raise EvidenceArchiveContractError(f"{field} must not contain control characters.")
    return normalized


def _sha256(value: object, *, field: str) -> str:
    normalized = _required_text(value, field=field).lower()
    if _SHA256.fullmatch(normalized) is None:
        raise EvidenceArchiveContractError(f"{field} must be a lowercase SHA-256 digest.")
    return normalized


def _revision(value: object, *, field: str) -> str:
    normalized = _required_text(value, field=field).lower()
    if _REVISION.fullmatch(normalized) is None:
        raise EvidenceArchiveContractError(f"{field} must be a hexadecimal Git revision.")
    return normalized


def _relative_redacted_path(value: object) -> str:
    normalized = _required_text(value, field="redacted_paths entry")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise EvidenceArchiveContractError(
            "redacted_paths entries must be contained POSIX-relative paths."
        )
    return path.as_posix()


def _locator(value: object) -> str:
    normalized = _required_text(value, field="locator")
    if "://" in normalized:
        parsed = urlsplit(normalized)
        if not parsed.scheme or _URI_SCHEME.fullmatch(parsed.scheme.lower()) is None:
            raise EvidenceArchiveContractError("locator URI scheme is invalid.")
        if parsed.username is not None or parsed.password is not None:
            raise EvidenceArchiveContractError("locator must not contain URI user credentials.")
        if parsed.scheme.lower() == "file":
            if not PurePosixPath(parsed.path).is_absolute():
                raise EvidenceArchiveContractError(
                    "file locator URI must contain an absolute path."
                )
        elif not parsed.netloc:
            raise EvidenceArchiveContractError("locator URI must include an authority.")
        path_parts = PurePosixPath(parsed.path).parts
    else:
        path = PurePosixPath(normalized)
        if not path.is_absolute():
            raise EvidenceArchiveContractError(
                "locator must be an absolute filesystem path or an absolute URI."
            )
        path_parts = path.parts
    if ".aidd" in path_parts:
        raise EvidenceArchiveContractError("locator must not point into a mutable .aidd tree.")
    if any(part in {"", ".", ".."} for part in path_parts):
        raise EvidenceArchiveContractError("locator must not contain traversal components.")
    return normalized


@dataclass(frozen=True, slots=True)
class EvidenceRedaction:
    """Sanitization declaration for an archive copied outside the workspace."""

    credentials_removed: bool
    provider_payloads_removed: bool
    target_paths_redacted: bool
    redacted_paths: tuple[str, ...] = ()
    policy_version: int = 1

    def normalized(self) -> EvidenceRedaction:
        if self.policy_version != 1:
            raise EvidenceArchiveContractError(
                f"unsupported redaction policy version: {self.policy_version}."
            )
        if self.credentials_removed is not True:
            raise EvidenceArchiveContractError("redaction must declare credentials_removed=true.")
        if self.provider_payloads_removed is not True:
            raise EvidenceArchiveContractError(
                "redaction must declare provider_payloads_removed=true."
            )
        if self.target_paths_redacted is not True:
            raise EvidenceArchiveContractError("redaction must declare target_paths_redacted=true.")
        paths = tuple(sorted({_relative_redacted_path(item) for item in self.redacted_paths}))
        return EvidenceRedaction(
            credentials_removed=True,
            provider_payloads_removed=True,
            target_paths_redacted=True,
            redacted_paths=paths,
            policy_version=1,
        )

    @classmethod
    def from_dict(cls, payload: object) -> EvidenceRedaction:
        if not isinstance(payload, dict):
            raise EvidenceArchiveContractError("redaction must be a JSON object.")
        raw_paths = payload.get("redacted_paths")
        if not isinstance(raw_paths, list) or not all(isinstance(item, str) for item in raw_paths):
            raise EvidenceArchiveContractError("redaction.redacted_paths must be a string list.")
        return cls(
            credentials_removed=payload.get("credentials_removed") is True,
            provider_payloads_removed=payload.get("provider_payloads_removed") is True,
            target_paths_redacted=payload.get("target_paths_redacted") is True,
            redacted_paths=tuple(raw_paths),
            policy_version=cast(int, payload.get("policy_version")),
        ).normalized()

    def to_dict(self) -> dict[str, object]:
        value = self.normalized()
        return {
            "credentials_removed": value.credentials_removed,
            "policy_version": value.policy_version,
            "provider_payloads_removed": value.provider_payloads_removed,
            "redacted_paths": list(value.redacted_paths),
            "target_paths_redacted": value.target_paths_redacted,
        }


@dataclass(frozen=True, slots=True)
class EvidenceArchiveRetention:
    """Integrity and provenance required to retrieve one immutable evidence archive."""

    locator: str
    sha256: str
    size_bytes: int
    source_revision: str
    target_pin: str
    evidence_schema_version: int
    redaction: EvidenceRedaction
    schema_version: int = EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION
    reference_mode: str = EVIDENCE_ARCHIVE_REFERENCE_MODE

    @property
    def digest(self) -> str:
        """Compatibility alias for consumers that call the archive hash a digest."""

        return self.normalized().sha256

    @property
    def revision(self) -> str:
        """Compatibility alias for the candidate/source revision."""

        return self.normalized().source_revision

    def normalized(self) -> EvidenceArchiveRetention:
        if self.schema_version != EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION:
            raise EvidenceArchiveContractError(
                f"unsupported evidence archive schema: {self.schema_version}."
            )
        if self.reference_mode != EVIDENCE_ARCHIVE_REFERENCE_MODE:
            raise EvidenceArchiveContractError(
                "evidence archive references must use external-immutable mode."
            )
        if (
            isinstance(self.size_bytes, bool)
            or not isinstance(self.size_bytes, int)
            or self.size_bytes < 1
        ):
            raise EvidenceArchiveContractError("size_bytes must be a positive integer.")
        if (
            isinstance(self.evidence_schema_version, bool)
            or not isinstance(self.evidence_schema_version, int)
            or self.evidence_schema_version < 1
        ):
            raise EvidenceArchiveContractError(
                "evidence_schema_version must be a positive integer."
            )
        return EvidenceArchiveRetention(
            locator=_locator(self.locator),
            sha256=_sha256(self.sha256, field="sha256"),
            size_bytes=self.size_bytes,
            source_revision=_revision(self.source_revision, field="source_revision"),
            target_pin=_required_text(self.target_pin, field="target_pin"),
            evidence_schema_version=self.evidence_schema_version,
            redaction=self.redaction.normalized(),
            schema_version=EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION,
            reference_mode=EVIDENCE_ARCHIVE_REFERENCE_MODE,
        )

    @classmethod
    def from_dict(cls, payload: object) -> EvidenceArchiveRetention:
        if not isinstance(payload, dict):
            raise EvidenceArchiveContractError("evidence archive retention must be a JSON object.")
        required = (
            "locator",
            "sha256",
            "size_bytes",
            "source_revision",
            "target_pin",
            "evidence_schema_version",
            "redaction",
            "schema_version",
            "reference_mode",
        )
        missing = [field for field in required if field not in payload]
        if missing:
            raise EvidenceArchiveContractError(
                "evidence archive retention is missing required fields: " + ", ".join(missing) + "."
            )
        return cls(
            locator=payload["locator"],
            sha256=payload["sha256"],
            size_bytes=payload["size_bytes"],
            source_revision=payload["source_revision"],
            target_pin=payload["target_pin"],
            evidence_schema_version=payload["evidence_schema_version"],
            redaction=EvidenceRedaction.from_dict(payload["redaction"]),
            schema_version=payload["schema_version"],
            reference_mode=payload["reference_mode"],
        ).normalized()

    def to_dict(self) -> dict[str, Any]:
        value = self.normalized()
        return {
            "evidence_schema_version": value.evidence_schema_version,
            "locator": value.locator,
            "reference_mode": value.reference_mode,
            "redaction": value.redaction.to_dict(),
            "schema_version": value.schema_version,
            "sha256": value.sha256,
            "size_bytes": value.size_bytes,
            "source_revision": value.source_revision,
            "target_pin": value.target_pin,
        }


def validate_evidence_archive_retention(
    retention: EvidenceArchiveRetention,
) -> EvidenceArchiveRetention:
    """Normalize and validate metadata before it is persisted or exported."""

    return retention.normalized()


def dump_evidence_archive_retention(retention: EvidenceArchiveRetention) -> str:
    """Serialize a validated retention record deterministically."""

    return json.dumps(retention.to_dict(), indent=2, sort_keys=True) + "\n"


__all__ = [
    "EVIDENCE_ARCHIVE_CONTRACT_SCHEMA_VERSION",
    "EVIDENCE_ARCHIVE_REFERENCE_MODE",
    "EVIDENCE_SCHEMA_VERSION",
    "EvidenceArchiveContractError",
    "EvidenceArchiveRetention",
    "EvidenceRedaction",
    "dump_evidence_archive_retention",
    "validate_evidence_archive_retention",
]
