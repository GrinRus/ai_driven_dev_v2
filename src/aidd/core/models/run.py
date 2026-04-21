from __future__ import annotations

from dataclasses import dataclass
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
class StageRunMetadata:
    run_id: str
    work_item_id: str
    stage: str
    status: str
    created_at_utc: str
    updated_at_utc: str
    status_history: tuple[StageStatusChange, ...]
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

        return cls(
            schema_version=int(payload.get("schema_version", 1)),
            run_id=str(payload["run_id"]),
            work_item_id=str(payload["work_item_id"]),
            stage=str(payload["stage"]),
            status=str(payload["status"]),
            created_at_utc=str(payload["created_at_utc"]),
            updated_at_utc=str(payload["updated_at_utc"]),
            status_history=history,
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
        )


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    stage: str
    status: str
