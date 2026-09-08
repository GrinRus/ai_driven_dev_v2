"""Validate exact-candidate CI gate evidence and write a hashed readiness record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from scripts.release.candidate_manifest import (
    CandidateManifestError,
    read_candidate_manifest,
)

READINESS_SCHEMA_VERSION = 1
DEFAULT_OUTPUT_PATH = Path(".aidd/candidate-readiness.json")
REQUIRED_GATE_NAMES = (
    "lint-type-test:3.12",
    "lint-type-test:3.13",
    "lint-type-test:3.14",
    "critical-coverage",
    "adapter-conformance",
    "deterministic-scenarios",
    "packaged-ui-browser",
    "build",
    "codeql",
    "dependency-review",
    "scorecard",
)
_ALLOWED_STATUSES = frozenset({"pass", "fail", "skipped", "pending"})
_GIT_OBJECT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CandidateReadinessError(ValueError):
    """Raised when candidate gate evidence cannot prove readiness."""


@dataclass(frozen=True, slots=True)
class GateResult:
    name: str
    status: str
    result_id: str
    result_url: str
    observed_commit: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "observed_commit": self.observed_commit,
            "result_id": self.result_id,
            "result_url": self.result_url,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class CandidateReadiness:
    candidate_manifest_sha256: str
    project_version: str
    source_commit: str
    source_tree: str
    captured_at_utc: str
    gates: tuple[GateResult, ...]
    success: bool
    readiness_sha256: str
    schema_version: int = READINESS_SCHEMA_VERSION

    def _payload(self) -> dict[str, object]:
        return {
            "candidate_manifest_sha256": self.candidate_manifest_sha256,
            "captured_at_utc": self.captured_at_utc,
            "gates": [gate.to_dict() for gate in self.gates],
            "project_version": self.project_version,
            "schema_version": self.schema_version,
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "success": self.success,
        }

    def to_dict(self) -> dict[str, object]:
        return {**self._payload(), "readiness_sha256": self.readiness_sha256}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _string(payload: Mapping[str, object], key: str, *, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CandidateReadinessError(f"{label}.{key} must be a non-empty string.")
    return value.strip()


def _validate_timestamp(value: str) -> str:
    normalized = value.strip()
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CandidateReadinessError(
            "captured_at_utc must be an ISO-8601 timestamp with a timezone."
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise CandidateReadinessError("captured_at_utc must include the UTC timezone.")
    return normalized


def _validate_git_object(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _GIT_OBJECT_RE.fullmatch(normalized) is None:
        raise CandidateReadinessError(f"{label} must be a full hexadecimal Git object id.")
    return normalized


def _validate_sha256(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if _SHA256_RE.fullmatch(normalized) is None:
        raise CandidateReadinessError(f"{label} must be a lowercase SHA-256 digest.")
    return normalized


def _validate_result_url(value: str, *, name: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme != "https" or not parsed.netloc:
        raise CandidateReadinessError(f"Gate {name} result_url must be an HTTPS URL.")
    return value.strip()


def _parse_gate(raw: object) -> GateResult:
    if not isinstance(raw, dict):
        raise CandidateReadinessError("Gate evidence entries must be objects.")
    name = _string(raw, "name", label="gate")
    status = _string(raw, "status", label=f"gate {name}").lower()
    if status not in _ALLOWED_STATUSES:
        raise CandidateReadinessError(f"Gate {name} has unsupported status {status!r}.")
    return GateResult(
        name=name,
        status=status,
        result_id=_string(raw, "result_id", label=f"gate {name}"),
        result_url=_validate_result_url(
            _string(raw, "result_url", label=f"gate {name}"), name=name
        ),
        observed_commit=_string(raw, "observed_commit", label=f"gate {name}").lower(),
    )


def _validate_gates(expected_commit: str, gates: Sequence[GateResult]) -> tuple[GateResult, ...]:
    expected = set(REQUIRED_GATE_NAMES)
    actual = [gate.name for gate in gates]
    duplicates = sorted({name for name in actual if actual.count(name) > 1})
    if duplicates:
        raise CandidateReadinessError(
            f"Gate evidence contains duplicate lanes: {', '.join(duplicates)}."
        )
    missing = sorted(expected - set(actual))
    extra = sorted(set(actual) - expected)
    if missing or extra:
        detail: list[str] = []
        if missing:
            detail.append(f"missing={missing}")
        if extra:
            detail.append(f"unsupported={extra}")
        raise CandidateReadinessError("Gate evidence inventory mismatch: " + "; ".join(detail))
    for gate in gates:
        _validate_git_object(gate.observed_commit, label=f"Gate {gate.name} observed_commit")
        if gate.observed_commit != expected_commit:
            raise CandidateReadinessError(
                f"Gate {gate.name} observed commit does not match candidate source_commit."
            )
    return tuple(sorted(gates, key=lambda gate: REQUIRED_GATE_NAMES.index(gate.name)))


def build_candidate_readiness(
    manifest_path: Path,
    evidence_path: Path,
) -> CandidateReadiness:
    """Build a readiness record from supplied, immutable gate evidence."""

    try:
        manifest = read_candidate_manifest(manifest_path)
        raw_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (CandidateManifestError, OSError, json.JSONDecodeError) as exc:
        raise CandidateReadinessError(
            f"Unable to read candidate manifest or gate evidence: {exc}"
        ) from exc
    if not isinstance(raw_payload, dict):
        raise CandidateReadinessError("Gate evidence must be a JSON object.")
    manifest_digest = _validate_sha256(
        _string(raw_payload, "candidate_manifest_sha256", label="evidence"),
        label="evidence.candidate_manifest_sha256",
    )
    if manifest_digest != manifest.manifest_sha256:
        raise CandidateReadinessError("Gate evidence manifest digest does not match candidate.")
    project_version = _string(raw_payload, "project_version", label="evidence")
    if project_version != manifest.project_version:
        raise CandidateReadinessError("Gate evidence project version does not match candidate.")
    source_commit = _validate_git_object(
        _string(raw_payload, "source_commit", label="evidence"), label="evidence.source_commit"
    )
    source_tree = _validate_git_object(
        _string(raw_payload, "source_tree", label="evidence"), label="evidence.source_tree"
    )
    if source_commit != manifest.source_commit or source_tree != manifest.source_tree:
        raise CandidateReadinessError("Gate evidence Git identity does not match candidate.")
    captured_at_utc = _validate_timestamp(_string(raw_payload, "captured_at_utc", label="evidence"))
    raw_gates = raw_payload.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise CandidateReadinessError("evidence.gates must be a non-empty list.")
    gates = _validate_gates(manifest.source_commit, tuple(_parse_gate(item) for item in raw_gates))
    success = all(gate.status == "pass" for gate in gates)
    provisional = CandidateReadiness(
        candidate_manifest_sha256=manifest.manifest_sha256,
        project_version=manifest.project_version,
        source_commit=manifest.source_commit,
        source_tree=manifest.source_tree,
        captured_at_utc=captured_at_utc,
        gates=gates,
        success=success,
        readiness_sha256="",
    )
    return CandidateReadiness(
        candidate_manifest_sha256=provisional.candidate_manifest_sha256,
        project_version=provisional.project_version,
        source_commit=provisional.source_commit,
        source_tree=provisional.source_tree,
        captured_at_utc=provisional.captured_at_utc,
        gates=provisional.gates,
        success=provisional.success,
        readiness_sha256=_canonical_digest(provisional._payload()),
    )


def read_candidate_readiness(
    path: Path,
    *,
    manifest_path: Path | None = None,
) -> CandidateReadiness:
    """Read and integrity-check a readiness record without external side effects."""

    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateReadinessError(f"Candidate readiness is missing or invalid: {path}") from exc
    if not isinstance(raw_payload, dict):
        raise CandidateReadinessError("Candidate readiness must be a JSON object.")
    if raw_payload.get("schema_version") != READINESS_SCHEMA_VERSION:
        raise CandidateReadinessError("Unsupported candidate readiness schema.")
    raw_gates = raw_payload.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise CandidateReadinessError("candidate readiness gates must be a non-empty list.")
    gates = tuple(_parse_gate(item) for item in raw_gates)
    source_commit = _validate_git_object(
        _string(raw_payload, "source_commit", label="candidate readiness"),
        label="candidate readiness.source_commit",
    )
    source_tree = _validate_git_object(
        _string(raw_payload, "source_tree", label="candidate readiness"),
        label="candidate readiness.source_tree",
    )
    manifest_digest = _validate_sha256(
        _string(raw_payload, "candidate_manifest_sha256", label="candidate readiness"),
        label="candidate readiness.candidate_manifest_sha256",
    )
    project_version = _string(raw_payload, "project_version", label="candidate readiness")
    captured_at_utc = _validate_timestamp(
        _string(raw_payload, "captured_at_utc", label="candidate readiness")
    )
    success = raw_payload.get("success")
    if not isinstance(success, bool):
        raise CandidateReadinessError("candidate readiness success must be a boolean.")
    readiness_sha256 = _validate_sha256(
        _string(raw_payload, "readiness_sha256", label="candidate readiness"),
        label="candidate readiness.readiness_sha256",
    )
    provisional = CandidateReadiness(
        candidate_manifest_sha256=manifest_digest,
        project_version=project_version,
        source_commit=source_commit,
        source_tree=source_tree,
        captured_at_utc=captured_at_utc,
        gates=_validate_gates(source_commit, gates),
        success=success,
        readiness_sha256=readiness_sha256,
    )
    if success != all(gate.status == "pass" for gate in provisional.gates):
        raise CandidateReadinessError("candidate readiness success does not match gate statuses.")
    if readiness_sha256 != _canonical_digest(provisional._payload()):
        raise CandidateReadinessError("Candidate readiness digest does not match its contents.")
    if manifest_path is not None:
        manifest = read_candidate_manifest(manifest_path)
        if (
            manifest.manifest_sha256 != manifest_digest
            or manifest.project_version != project_version
            or manifest.source_commit != source_commit
            or manifest.source_tree != source_tree
        ):
            raise CandidateReadinessError("Candidate readiness identity does not match manifest.")
        gates = _validate_gates(manifest.source_commit, gates)
    return provisional


def write_candidate_readiness(record: CandidateReadiness, output_path: Path) -> Path:
    """Write a readiness record atomically, refusing accidental overwrite."""

    destination = output_path.resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        raise CandidateReadinessError(
            f"Refusing to overwrite existing candidate readiness: {destination}"
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.tmp")
        temporary.write_text(record.to_json(), encoding="utf-8")
        temporary.replace(destination)
    except OSError as exc:
        raise CandidateReadinessError(
            f"Unable to write candidate readiness: {destination}"
        ) from exc
    return destination


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        record = build_candidate_readiness(args.manifest, args.evidence)
        output = write_candidate_readiness(record, args.output)
    except (CandidateReadinessError, CandidateManifestError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "success": False}, sort_keys=True))
        return 1
    print(json.dumps({"readiness": output.as_posix(), "success": record.success}, sort_keys=True))
    return 0 if record.success else 1


__all__ = [
    "CandidateReadiness",
    "CandidateReadinessError",
    "DEFAULT_OUTPUT_PATH",
    "GateResult",
    "READINESS_SCHEMA_VERSION",
    "REQUIRED_GATE_NAMES",
    "build_candidate_readiness",
    "main",
    "read_candidate_readiness",
    "write_candidate_readiness",
]


if __name__ == "__main__":
    raise SystemExit(main())
