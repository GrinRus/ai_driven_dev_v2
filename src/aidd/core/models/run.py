from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
        return cls(
            status=str(payload["status"]),
            changed_at_utc=str(payload["changed_at_utc"]),
        )


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
        if normalized_trigger not in {"initial", "repair"}:
            raise ValueError("Repair history trigger must be either 'initial' or 'repair'.")
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
        return cls(
            attempt_number=int(payload["attempt_number"]),
            trigger=str(payload["trigger"]),
            outcome=str(payload["outcome"]),
            recorded_at_utc=str(payload["recorded_at_utc"]),
            validator_report_path=(
                str(payload["validator_report_path"])
                if payload.get("validator_report_path") is not None
                else None
            ),
            repair_brief_path=(
                str(payload["repair_brief_path"])
                if payload.get("repair_brief_path") is not None
                else None
            ),
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
        history = tuple(
            StageStatusChange.from_dict(change)
            for change in payload.get("status_history", [])
        )
        if not history:
            fallback_timestamp = str(
                payload.get("updated_at_utc", payload.get("created_at_utc", ""))
            )
            history = (
                StageStatusChange(
                    status=str(payload["status"]),
                    changed_at_utc=fallback_timestamp,
                ),
            )
        repair_history = tuple(
            RepairHistoryEntry.from_dict(entry)
            for entry in payload.get("repair_history", [])
        )

        return cls(
            schema_version=int(payload.get("schema_version", 1)),
            run_id=str(payload["run_id"]),
            work_item_id=str(payload["work_item_id"]),
            stage=str(payload["stage"]),
            status=str(payload["status"]),
            created_at_utc=str(payload["created_at_utc"]),
            updated_at_utc=str(payload["updated_at_utc"]),
            status_history=history,
            repair_history=repair_history,
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
        changed_at_utc: str,
    ) -> RunArtifactIndex:
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
            created_at_utc=changed_at_utc,
            updated_at_utc=changed_at_utc,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RunArtifactIndex:
        raw_prompt_pack_provenance = payload.get("prompt_pack_provenance", [])
        prompt_pack_provenance: list[RunArtifactIndex.PromptPackProvenanceEntry] = []
        if isinstance(raw_prompt_pack_provenance, list):
            for entry in raw_prompt_pack_provenance:
                if not isinstance(entry, dict):
                    continue
                parsed_entry = RunArtifactIndex.PromptPackProvenanceEntry.from_dict(entry)
                if parsed_entry is None:
                    continue
                prompt_pack_provenance.append(parsed_entry)
        return cls(
            schema_version=int(payload.get("schema_version", 1)),
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
                str(payload["resource_root"])
                if payload.get("resource_root") is not None
                else None
            ),
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
            "created_at_utc": self.created_at_utc,
            "updated_at_utc": self.updated_at_utc,
        }


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    stage: str
    status: str
