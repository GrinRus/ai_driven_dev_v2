from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aidd.core.attempt_lineage import AttemptKind, AttemptLineage, AttemptScope
from aidd.core.persisted_state import require_fields


def _normalize_required_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty.")
    return normalized


def _normalize_sha256(value: str, *, field_name: str) -> str:
    normalized = _normalize_required_text(value, field_name=field_name).lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field_name} must be a 64-character SHA-256 digest.")
    return normalized


@dataclass(frozen=True, slots=True)
class StageStatusChange:
    status: str
    changed_at_utc: str

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "changed_at_utc": self.changed_at_utc,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageStatusChange:
        require_fields(
            payload,
            label="Stage status history entry",
            fields={"status": str, "changed_at_utc": str},
        )
        return cls(status=payload["status"], changed_at_utc=payload["changed_at_utc"])


@dataclass(frozen=True, slots=True)
class RepairHistoryEntry:
    attempt_number: int
    trigger: str
    outcome: str
    recorded_at_utc: str
    validator_report_path: str | None = None
    repair_brief_path: str | None = None

    def __post_init__(self) -> None:
        if self.attempt_number < 1:
            raise ValueError("Repair history attempt number must be >= 1.")

        normalized_trigger = self.trigger.strip().lower()
        if normalized_trigger not in {
            "initial",
            "repair",
            "resume",
            "intervention",
            "repair-extension",
        }:
            raise ValueError(
                "Repair history trigger must be one of 'initial', 'repair', 'resume', "
                "'intervention', or 'repair-extension'."
            )
        object.__setattr__(self, "trigger", normalized_trigger)

        normalized_outcome = self.outcome.strip()
        if not normalized_outcome:
            raise ValueError("Repair history outcome must not be empty.")
        object.__setattr__(self, "outcome", normalized_outcome)

        normalized_recorded_at = self.recorded_at_utc.strip()
        if not normalized_recorded_at:
            raise ValueError("Repair history recorded_at_utc must not be empty.")
        object.__setattr__(self, "recorded_at_utc", normalized_recorded_at)

        for field_name in ("validator_report_path", "repair_brief_path"):
            value = getattr(self, field_name)
            if value is None:
                continue
            normalized_path = value.strip()
            if not normalized_path:
                object.__setattr__(self, field_name, None)
                continue
            if Path(normalized_path).is_absolute():
                raise ValueError(
                    "Repair history paths must be workspace-relative: "
                    f"{field_name}={normalized_path}"
                )
            object.__setattr__(self, field_name, normalized_path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt_number": self.attempt_number,
            "trigger": self.trigger,
            "outcome": self.outcome,
            "recorded_at_utc": self.recorded_at_utc,
            "validator_report_path": self.validator_report_path,
            "repair_brief_path": self.repair_brief_path,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RepairHistoryEntry:
        require_fields(
            payload,
            label="Repair history entry",
            fields={
                "attempt_number": int,
                "trigger": str,
                "outcome": str,
                "recorded_at_utc": str,
                "validator_report_path": (str, type(None)),
                "repair_brief_path": (str, type(None)),
            },
        )
        return cls(
            attempt_number=payload["attempt_number"],
            trigger=payload["trigger"],
            outcome=payload["outcome"],
            recorded_at_utc=payload["recorded_at_utc"],
            validator_report_path=payload["validator_report_path"],
            repair_brief_path=payload["repair_brief_path"],
        )


@dataclass(frozen=True, slots=True)
class RepairExtensionGrant:
    """Immutable evidence for the single operator-authorized repair extension.

    The grant is deliberately separate from :class:`RepairHistoryEntry`: automatic repair
    accounting and the extension attempt mode are added by the accounting slice. This model
    freezes the identity and evidence that a later preflight must revalidate.
    """

    work_item_id: str
    run_id: str
    stage: str
    validator_report_path: str
    validator_report_sha256: str
    repair_brief_path: str
    repair_brief_sha256: str
    configuration_identity: str
    author: str
    authorized_at_utc: str
    reason: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        for field_name in ("work_item_id", "run_id", "stage", "configuration_identity", "author"):
            object.__setattr__(
                self,
                field_name,
                _normalize_required_text(getattr(self, field_name), field_name=field_name),
            )

        for field_name in ("validator_report_path", "repair_brief_path"):
            value = _normalize_required_text(getattr(self, field_name), field_name=field_name)
            if Path(value).is_absolute() or "\\" in value:
                raise ValueError(f"{field_name} must be workspace-relative.")
            object.__setattr__(self, field_name, value)

        object.__setattr__(
            self,
            "validator_report_sha256",
            _normalize_sha256(self.validator_report_sha256, field_name="validator_report_sha256"),
        )
        object.__setattr__(
            self,
            "repair_brief_sha256",
            _normalize_sha256(self.repair_brief_sha256, field_name="repair_brief_sha256"),
        )
        object.__setattr__(
            self,
            "authorized_at_utc",
            _normalize_required_text(self.authorized_at_utc, field_name="authorized_at_utc"),
        )
        object.__setattr__(
            self,
            "reason",
            _normalize_required_text(self.reason, field_name="reason"),
        )
        if self.schema_version != 1:
            raise ValueError(f"Unsupported repair-extension grant schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "work_item_id": self.work_item_id,
            "run_id": self.run_id,
            "stage": self.stage,
            "validator_report_path": self.validator_report_path,
            "validator_report_sha256": self.validator_report_sha256,
            "repair_brief_path": self.repair_brief_path,
            "repair_brief_sha256": self.repair_brief_sha256,
            "configuration_identity": self.configuration_identity,
            "author": self.author,
            "authorized_at_utc": self.authorized_at_utc,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RepairExtensionGrant:
        require_fields(
            payload,
            label="Repair-extension grant",
            schema_version=1,
            fields={
                "work_item_id": str,
                "run_id": str,
                "stage": str,
                "validator_report_path": str,
                "validator_report_sha256": str,
                "repair_brief_path": str,
                "repair_brief_sha256": str,
                "configuration_identity": str,
                "author": str,
                "authorized_at_utc": str,
                "reason": str,
            },
        )
        return cls(
            schema_version=1,
            work_item_id=payload["work_item_id"],
            run_id=payload["run_id"],
            stage=payload["stage"],
            validator_report_path=payload["validator_report_path"],
            validator_report_sha256=payload["validator_report_sha256"],
            repair_brief_path=payload["repair_brief_path"],
            repair_brief_sha256=payload["repair_brief_sha256"],
            configuration_identity=payload["configuration_identity"],
            author=payload["author"],
            authorized_at_utc=payload["authorized_at_utc"],
            reason=payload["reason"],
        )


@dataclass(frozen=True, slots=True)
class StageRunMetadata:
    run_id: str
    work_item_id: str
    stage: str
    status: str
    created_at_utc: str
    updated_at_utc: str
    status_history: tuple[StageStatusChange, ...]
    repair_history: tuple[RepairHistoryEntry, ...] = ()
    repair_extension_grant: RepairExtensionGrant | None = None
    schema_version: int = 1

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        work_item_id: str,
        stage: str,
        status: str,
        changed_at_utc: str,
    ) -> StageRunMetadata:
        initial_change = StageStatusChange(status=status, changed_at_utc=changed_at_utc)
        return cls(
            run_id=run_id,
            work_item_id=work_item_id,
            stage=stage,
            status=status,
            created_at_utc=changed_at_utc,
            updated_at_utc=changed_at_utc,
            status_history=(initial_change,),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StageRunMetadata:
        require_fields(
            payload,
            label="Stage metadata",
            schema_version=1,
            fields={
                "run_id": str,
                "work_item_id": str,
                "stage": str,
                "status": str,
                "created_at_utc": str,
                "updated_at_utc": str,
                "status_history": list,
                "repair_history": list,
                "repair_extension_grant": (dict, type(None)),
            },
        )
        if not payload["status_history"]:
            raise ValueError("Stage metadata requires nonempty status_history.")
        history = tuple(
            StageStatusChange.from_dict(change) for change in payload["status_history"]
        )
        repair_history = tuple(
            RepairHistoryEntry.from_dict(entry) for entry in payload["repair_history"]
        )
        raw_grant = payload["repair_extension_grant"]
        repair_extension_grant = (
            None if raw_grant is None else RepairExtensionGrant.from_dict(raw_grant)
        )
        return cls(
            schema_version=1,
            run_id=payload["run_id"],
            work_item_id=payload["work_item_id"],
            stage=payload["stage"],
            status=payload["status"],
            created_at_utc=payload["created_at_utc"],
            updated_at_utc=payload["updated_at_utc"],
            status_history=history,
            repair_history=repair_history,
            repair_extension_grant=repair_extension_grant,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "work_item_id": self.work_item_id,
            "stage": self.stage,
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            "status_history": [change.to_dict() for change in self.status_history],
            "repair_history": [entry.to_dict() for entry in self.repair_history],
            "repair_extension_grant": (
                None
                if self.repair_extension_grant is None
                else self.repair_extension_grant.to_dict()
            ),
        }

    def with_status(self, *, status: str, changed_at_utc: str) -> StageRunMetadata:
        history = self.status_history
        if status != self.status:
            history = (*history, StageStatusChange(status=status, changed_at_utc=changed_at_utc))
        return StageRunMetadata(
            schema_version=self.schema_version,
            run_id=self.run_id,
            work_item_id=self.work_item_id,
            stage=self.stage,
            status=status,
            created_at_utc=self.created_at_utc,
            updated_at_utc=changed_at_utc,
            status_history=history,
            repair_history=self.repair_history,
            repair_extension_grant=self.repair_extension_grant,
        )

    def with_repair_history_entry(
        self,
        *,
        entry: RepairHistoryEntry,
        changed_at_utc: str,
    ) -> StageRunMetadata:
        history = list(self.repair_history)
        for index, existing in enumerate(history):
            if (
                existing.attempt_number == entry.attempt_number
                and existing.trigger == entry.trigger
            ):
                history[index] = entry
                break
        else:
            history.append(entry)

        return StageRunMetadata(
            schema_version=self.schema_version,
            run_id=self.run_id,
            work_item_id=self.work_item_id,
            stage=self.stage,
            status=self.status,
            created_at_utc=self.created_at_utc,
            updated_at_utc=changed_at_utc,
            status_history=self.status_history,
            repair_history=tuple(history),
            repair_extension_grant=self.repair_extension_grant,
        )

    def with_repair_extension_grant(
        self,
        *,
        grant: RepairExtensionGrant,
        changed_at_utc: str,
    ) -> StageRunMetadata:
        if self.repair_extension_grant is not None:
            raise ValueError("A repair-extension grant already exists for this stage run.")
        if (
            grant.work_item_id != self.work_item_id
            or grant.run_id != self.run_id
            or grant.stage != self.stage
        ):
            raise ValueError("Repair-extension grant identity does not match stage metadata.")
        return StageRunMetadata(
            schema_version=self.schema_version,
            run_id=self.run_id,
            work_item_id=self.work_item_id,
            stage=self.stage,
            status=self.status,
            created_at_utc=self.created_at_utc,
            updated_at_utc=changed_at_utc,
            status_history=self.status_history,
            repair_history=self.repair_history,
            repair_extension_grant=grant,
        )


@dataclass(frozen=True, slots=True)
class RunArtifactIndex:
    @dataclass(frozen=True, slots=True)
    class PromptPackProvenanceEntry:
        path: str
        sha256: str

        def to_dict(self) -> dict[str, str]:
            return {
                "path": self.path,
                "sha256": self.sha256,
            }

        @classmethod
        def from_dict(
            cls,
            payload: dict[str, Any],
        ) -> RunArtifactIndex.PromptPackProvenanceEntry | None:
            path = str(payload.get("path", "")).strip()
            sha256 = str(payload.get("sha256", "")).strip()
            if not path or not sha256:
                return None
            return cls(path=path, sha256=sha256)

    run_id: str
    work_item_id: str
    stage: str
    attempt_number: int
    documents: dict[str, str]
    logs: dict[str, str]
    prompt_pack_provenance: tuple[PromptPackProvenanceEntry, ...]
    resource_source: str | None
    resource_root: str | None
    created_at_utc: str
    updated_at_utc: str
    attempt_mode: str | None = None
    lineage: AttemptLineage | None = None
    schema_version: int = 1

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        work_item_id: str,
        stage: str,
        attempt_number: int,
        documents: dict[str, str],
        logs: dict[str, str],
        prompt_pack_provenance: tuple[PromptPackProvenanceEntry, ...] = (),
        resource_source: str | None = None,
        resource_root: str | None = None,
        attempt_mode: str | None = None,
        lineage: AttemptLineage | None = None,
        changed_at_utc: str,
    ) -> RunArtifactIndex:
        if lineage is None:
            normalized_mode = None if attempt_mode is None else attempt_mode.strip().lower()
            if normalized_mode is not None:
                try:
                    attempt_kind = AttemptKind(normalized_mode)
                except ValueError as exc:
                    raise ValueError(
                        f"Unknown artifact-index attempt_mode: {normalized_mode}"
                    ) from exc
            else:
                attempt_kind = AttemptKind.UNKNOWN
            lineage = AttemptLineage(
                scope=AttemptScope.STAGE,
                attempt_kind=attempt_kind,
                attempt_number=attempt_number,
            )
        if lineage is not None:
            lineage.validate_identity(scope=AttemptScope.STAGE, attempt_number=attempt_number)
            if (
                attempt_mode is not None
                and lineage.attempt_kind.value != attempt_mode.strip().lower()
            ):
                raise ValueError("Artifact index attempt_mode disagrees with its lineage.")
        return cls(
            run_id=run_id,
            work_item_id=work_item_id,
            stage=stage,
            attempt_number=attempt_number,
            documents=dict(documents),
            logs=dict(logs),
            prompt_pack_provenance=tuple(prompt_pack_provenance),
            resource_source=resource_source,
            resource_root=resource_root,
            attempt_mode=attempt_mode,
            lineage=lineage,
            created_at_utc=changed_at_utc,
            updated_at_utc=changed_at_utc,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RunArtifactIndex:
        prompt_pack_provenance: list[RunArtifactIndex.PromptPackProvenanceEntry] = []
        if payload.get("schema_version") != 1:
            raise ValueError("Unsupported artifact-index schema version.")
        raw_provenance = payload.get("prompt_pack_provenance")
        if not isinstance(raw_provenance, list):
            raise ValueError("Artifact index requires a prompt_pack_provenance list.")
        for entry in raw_provenance:
            if not isinstance(entry, dict):
                raise ValueError("Artifact-index prompt provenance entries must be objects.")
            parsed_entry = RunArtifactIndex.PromptPackProvenanceEntry.from_dict(entry)
            if parsed_entry is None:
                raise ValueError("Artifact-index prompt provenance entry is malformed.")
            prompt_pack_provenance.append(parsed_entry)
        if "attempt_mode" not in payload:
            raise ValueError("Artifact index requires an attempt_mode field.")
        if "lineage" not in payload:
            raise ValueError("Artifact index requires current-format lineage.")
        raw_attempt_mode = payload["attempt_mode"]
        attempt_mode = None
        if raw_attempt_mode is not None:
            attempt_mode = str(raw_attempt_mode).strip().lower()
            if attempt_mode not in {
                "initial",
                "repair",
                "resume",
                "intervention",
                "repair-extension",
            }:
                raise ValueError(f"Unknown artifact-index attempt_mode: {attempt_mode}")
        lineage = None
        if payload.get("lineage") is not None:
            lineage = AttemptLineage.from_dict(payload["lineage"])
            lineage.validate_identity(
                scope=AttemptScope.STAGE,
                attempt_number=int(payload["attempt_number"]),
            )
            if attempt_mode is not None and lineage.attempt_kind.value != attempt_mode:
                raise ValueError("Artifact index attempt_mode disagrees with its lineage.")
        return cls(
            schema_version=1,
            run_id=str(payload["run_id"]),
            work_item_id=str(payload["work_item_id"]),
            stage=str(payload["stage"]),
            attempt_number=int(payload["attempt_number"]),
            documents=dict(payload.get("documents", {})),
            logs=dict(payload.get("logs", {})),
            prompt_pack_provenance=tuple(prompt_pack_provenance),
            resource_source=(
                str(payload["resource_source"])
                if payload.get("resource_source") is not None
                else None
            ),
            resource_root=(
                str(payload["resource_root"]) if payload.get("resource_root") is not None else None
            ),
            attempt_mode=attempt_mode,
            lineage=lineage,
            created_at_utc=str(payload["created_at_utc"]),
            updated_at_utc=str(payload["updated_at_utc"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "work_item_id": self.work_item_id,
            "stage": self.stage,
            "attempt_number": self.attempt_number,
            "documents": dict(self.documents),
            "logs": dict(self.logs),
            "prompt_pack_provenance": [entry.to_dict() for entry in self.prompt_pack_provenance],
            "resource_source": self.resource_source,
            "resource_root": self.resource_root,
            "attempt_mode": self.attempt_mode,
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
            **({"lineage": self.lineage.to_dict()} if self.lineage is not None else {}),
        }

    @property
    def effective_lineage(self) -> AttemptLineage:
        """Return the explicit current-format lineage."""

        if self.lineage is None:
            raise ValueError("Artifact index is missing current-format lineage.")
        return self.lineage
