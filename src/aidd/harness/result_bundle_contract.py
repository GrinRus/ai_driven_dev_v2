"""Versioned contract for self-contained evaluation result bundles.

This module defines the data that later materialization and sealing tasks persist.  It
does not copy files or make provider-specific decisions: references are always relative
to the bundle root and legacy, ambiguous evidence is rejected explicitly.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, cast

from aidd.core.identifiers import SafeIdentifier

RESULT_BUNDLE_CONTRACT_SCHEMA_VERSION = 2
RESULT_BUNDLE_REFERENCE_MODE = "bundle-relative"
RESULT_BUNDLE_LEGACY_POLICY = "reject"

BundleStatus = Literal["pass", "fail", "blocked", "infra-fail"]
BundleArtifactCondition = Literal["always", "pass", "fail", "blocked", "infra-fail"]
_STATUSES = frozenset({"pass", "fail", "blocked", "infra-fail"})
_CONDITIONS = frozenset({"always", "pass", "fail", "blocked", "infra-fail"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ResultBundleContractError(ValueError):
    """Raised when a bundle identity, inventory, or reference is invalid."""


def _identifier(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ResultBundleContractError(f"{field} must be a string.")
    try:
        return SafeIdentifier.parse(value, label=field).value
    except ValueError as exc:
        raise ResultBundleContractError(str(exc)) from exc


def _optional_identifier(value: object, *, field: str) -> str | None:
    return None if value is None else _identifier(value, field=field)


def _reference(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResultBundleContractError("artifact path must be a non-empty string.")
    path = value.strip()
    if "\\" in path:
        raise ResultBundleContractError("artifact path must use POSIX separators.")
    relative = PurePosixPath(path)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ResultBundleContractError(
            f"artifact path must be a contained bundle-relative reference: {value!r}."
        )
    return relative.as_posix()


def _condition(value: object) -> BundleArtifactCondition:
    if not isinstance(value, str) or value not in _CONDITIONS:
        raise ResultBundleContractError(
            "condition must be one of: " + ", ".join(sorted(_CONDITIONS)) + "."
        )
    return cast(BundleArtifactCondition, value)


@dataclass(frozen=True, slots=True)
class ResultBundleIdentity:
    """Identity that keeps evaluator and product executions distinct."""

    evaluation_run_id: str
    product_run_id: str | None
    scenario_id: str
    runtime_id: str
    work_item: str

    @property
    def eval_run_id(self) -> str:
        """Short compatibility spelling for callers that use ``eval_run_id``."""

        return self.evaluation_run_id

    def normalized(self) -> ResultBundleIdentity:
        evaluation_run_id = _identifier(self.evaluation_run_id, field="evaluation_run_id")
        product_run_id = _optional_identifier(self.product_run_id, field="product_run_id")
        if product_run_id == evaluation_run_id:
            raise ResultBundleContractError(
                "evaluation_run_id and product_run_id must remain distinct."
            )
        return ResultBundleIdentity(
            evaluation_run_id=evaluation_run_id,
            product_run_id=product_run_id,
            scenario_id=_identifier(self.scenario_id, field="scenario_id"),
            runtime_id=_identifier(self.runtime_id, field="runtime_id"),
            work_item=_identifier(self.work_item, field="work_item"),
        )

    @classmethod
    def from_dict(cls, payload: object) -> ResultBundleIdentity:
        if not isinstance(payload, dict):
            raise ResultBundleContractError("bundle identity must be a JSON object.")
        if "run_id" in payload:
            raise ResultBundleContractError(
                "legacy run_id identity is rejected; provide evaluation_run_id and "
                "product_run_id explicitly."
            )
        fields = ("evaluation_run_id", "product_run_id", "scenario_id", "runtime_id", "work_item")
        missing = [field for field in fields if field not in payload]
        if missing:
            raise ResultBundleContractError(
                "bundle identity is missing required fields: " + ", ".join(missing) + "."
            )
        return cls(
            evaluation_run_id=payload["evaluation_run_id"],
            product_run_id=payload["product_run_id"],
            scenario_id=payload["scenario_id"],
            runtime_id=payload["runtime_id"],
            work_item=payload["work_item"],
        ).normalized()

    def to_dict(self) -> dict[str, str | None]:
        value = self.normalized()
        return {
            "evaluation_run_id": value.evaluation_run_id,
            "product_run_id": value.product_run_id,
            "scenario_id": value.scenario_id,
            "runtime_id": value.runtime_id,
            "work_item": value.work_item,
        }


@dataclass(frozen=True, slots=True)
class BundleArtifactRequirement:
    """An artifact required for one or more terminal bundle statuses."""

    path: str
    required_for: frozenset[BundleStatus]
    condition: BundleArtifactCondition = "always"

    def normalized(self) -> BundleArtifactRequirement:
        path = _reference(self.path)
        statuses = set(self.required_for)
        if not statuses or not statuses <= _STATUSES:
            raise ResultBundleContractError(
                f"required_for contains an unsupported bundle status: {self.path!r}."
            )
        return BundleArtifactRequirement(
            path=path,
            required_for=frozenset(statuses),
            condition=_condition(self.condition),
        )

    def to_dict(self) -> dict[str, object]:
        value = self.normalized()
        return {
            "path": value.path,
            "required_for": sorted(value.required_for),
            "condition": value.condition,
        }


@dataclass(frozen=True, slots=True)
class ResultBundleArtifact:
    """A bundle-relative artifact reference with optional integrity metadata."""

    path: str
    condition: BundleArtifactCondition = "always"
    sha256: str | None = None
    size_bytes: int | None = None

    def normalized(self) -> ResultBundleArtifact:
        path = _reference(self.path)
        digest = self.sha256
        if digest is not None and (
            not isinstance(digest, str) or _SHA256.fullmatch(digest.lower()) is None
        ):
            raise ResultBundleContractError(f"sha256 is invalid for artifact {path!r}.")
        if self.size_bytes is not None and (
            isinstance(self.size_bytes, bool)
            or not isinstance(self.size_bytes, int)
            or self.size_bytes < 0
        ):
            raise ResultBundleContractError(f"size_bytes is invalid for artifact {path!r}.")
        return ResultBundleArtifact(
            path=path,
            condition=_condition(self.condition),
            sha256=None if digest is None else digest.lower(),
            size_bytes=self.size_bytes,
        )

    def to_dict(self) -> dict[str, object]:
        value = self.normalized()
        return {
            "path": value.path,
            "condition": value.condition,
            "sha256": value.sha256,
            "size_bytes": value.size_bytes,
        }


@dataclass(frozen=True, slots=True)
class ResultBundleInventory:
    """Versioned inventory, identity, and conditional-artifact contract."""

    identity: ResultBundleIdentity
    status: BundleStatus
    artifacts: tuple[ResultBundleArtifact, ...]
    requirements: tuple[BundleArtifactRequirement, ...] = ()
    schema_version: int = RESULT_BUNDLE_CONTRACT_SCHEMA_VERSION
    reference_mode: str = RESULT_BUNDLE_REFERENCE_MODE
    legacy_policy: str = RESULT_BUNDLE_LEGACY_POLICY

    def normalized(self) -> ResultBundleInventory:
        if self.schema_version != RESULT_BUNDLE_CONTRACT_SCHEMA_VERSION:
            raise ResultBundleContractError(
                f"unsupported result bundle schema: {self.schema_version}."
            )
        if self.reference_mode != RESULT_BUNDLE_REFERENCE_MODE:
            raise ResultBundleContractError("result bundle references must be bundle-relative.")
        if self.legacy_policy != RESULT_BUNDLE_LEGACY_POLICY:
            raise ResultBundleContractError("legacy result bundle policy must be reject.")
        if self.status not in _STATUSES:
            raise ResultBundleContractError(f"unsupported bundle status: {self.status!r}.")
        identity = self.identity.normalized()
        artifacts = tuple(item.normalized() for item in self.artifacts)
        if len({item.path for item in artifacts}) != len(artifacts):
            raise ResultBundleContractError("bundle inventory contains duplicate artifact paths.")
        requirements = tuple(item.normalized() for item in self.requirements)
        if len({item.path for item in requirements}) != len(requirements):
            raise ResultBundleContractError("bundle contract contains duplicate requirements.")
        return ResultBundleInventory(
            identity=identity,
            status=self.status,
            artifacts=artifacts,
            requirements=requirements,
        )

    @classmethod
    def from_dict(cls, payload: object) -> ResultBundleInventory:
        if not isinstance(payload, dict):
            raise ResultBundleContractError("result bundle inventory must be a JSON object.")
        if "run_id" in payload:
            raise ResultBundleContractError("legacy result bundle payload is rejected.")
        raw_artifacts = payload.get("artifacts")
        if not isinstance(raw_artifacts, list):
            raise ResultBundleContractError("result bundle artifacts must be a JSON list.")
        raw_requirements = payload.get("requirements", [])
        if not isinstance(raw_requirements, list):
            raise ResultBundleContractError("result bundle requirements must be a JSON list.")
        artifacts: list[ResultBundleArtifact] = []
        for raw in raw_artifacts:
            if not isinstance(raw, dict):
                raise ResultBundleContractError("result bundle artifact record is invalid.")
            artifacts.append(
                ResultBundleArtifact(
                    path=cast(str, raw.get("path")),
                    condition=raw.get("condition", "always"),
                    sha256=cast(str | None, raw.get("sha256")),
                    size_bytes=cast(int | None, raw.get("size_bytes")),
                )
            )
        requirements: list[BundleArtifactRequirement] = []
        for raw in raw_requirements:
            if not isinstance(raw, dict) or not isinstance(raw.get("required_for"), list):
                raise ResultBundleContractError("result bundle requirement record is invalid.")
            raw_statuses = raw["required_for"]
            if not all(isinstance(item, str) for item in raw_statuses):
                raise ResultBundleContractError("result bundle requirement statuses are invalid.")
            requirements.append(
                BundleArtifactRequirement(
                    path=cast(str, raw.get("path")),
                    required_for=frozenset(cast(BundleStatus, item) for item in raw_statuses),
                    condition=raw.get("condition", "always"),
                )
            )
        return cls(
            identity=ResultBundleIdentity.from_dict(payload.get("identity")),
            status=cast(BundleStatus, payload.get("status")),
            artifacts=tuple(artifacts),
            requirements=tuple(requirements),
            schema_version=cast(int, payload.get("schema_version")),
            reference_mode=cast(str, payload.get("reference_mode")),
            legacy_policy=payload.get("legacy_policy", RESULT_BUNDLE_LEGACY_POLICY),
        ).normalized()

    def to_dict(self) -> dict[str, object]:
        value = self.normalized()
        return {
            "artifacts": [item.to_dict() for item in value.artifacts],
            "identity": value.identity.to_dict(),
            "legacy_policy": value.legacy_policy,
            "reference_mode": value.reference_mode,
            "requirements": [item.to_dict() for item in value.requirements],
            "schema_version": value.schema_version,
            "status": value.status,
        }


def validate_result_bundle_inventory(
    *, inventory: ResultBundleInventory, bundle_root: Path
) -> ResultBundleInventory:
    """Reject dangling references, missing conditional artifacts, or bad digests."""

    value = inventory.normalized()
    root = bundle_root.resolve(strict=False)
    if not root.is_dir():
        raise ResultBundleContractError(f"bundle root does not exist: {bundle_root!s}.")
    artifacts = {item.path: item for item in value.artifacts}
    for artifact in value.artifacts:
        if artifact.condition not in {"always", value.status}:
            continue
        path = (root / PurePosixPath(artifact.path)).resolve(strict=False)
        if not path.is_relative_to(root) or not path.is_file():
            raise ResultBundleContractError(
                f"bundle artifact reference is dangling: {artifact.path!r}."
            )
        if artifact.size_bytes is not None and path.stat().st_size != artifact.size_bytes:
            raise ResultBundleContractError(
                f"bundle artifact size does not match: {artifact.path!r}."
            )
        if artifact.sha256 is not None:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != artifact.sha256:
                raise ResultBundleContractError(
                    f"bundle artifact digest does not match: {artifact.path!r}."
                )
    for requirement in value.requirements:
        if value.status not in requirement.required_for:
            continue
        required_artifact = artifacts.get(requirement.path)
        if required_artifact is None:
            raise ResultBundleContractError(
                f"bundle is missing required artifact: {requirement.path!r}."
            )
        if requirement.condition not in {"always", value.status}:
            raise ResultBundleContractError(
                f"artifact condition does not match bundle status: {requirement.path!r}."
            )
        if required_artifact.condition not in {"always", value.status}:
            raise ResultBundleContractError(
                f"artifact condition does not match bundle status: {requirement.path!r}."
            )
    return value


def dump_result_bundle_inventory(inventory: ResultBundleInventory) -> str:
    """Serialize a normalized inventory deterministically for later persistence."""

    return json.dumps(inventory.to_dict(), indent=2, sort_keys=True) + "\n"


__all__ = [
    "BundleArtifactCondition",
    "BundleArtifactRequirement",
    "BundleStatus",
    "RESULT_BUNDLE_CONTRACT_SCHEMA_VERSION",
    "RESULT_BUNDLE_LEGACY_POLICY",
    "RESULT_BUNDLE_REFERENCE_MODE",
    "ResultBundleArtifact",
    "ResultBundleContractError",
    "ResultBundleIdentity",
    "ResultBundleInventory",
    "dump_result_bundle_inventory",
    "validate_result_bundle_inventory",
]
