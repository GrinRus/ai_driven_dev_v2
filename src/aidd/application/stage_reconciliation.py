from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from aidd.core.identifiers import SafeIdentifier
from aidd.core.mutation_lease import acquire_run_mutation_lease
from aidd.core.run_store import (
    load_stage_metadata,
    persist_stage_status,
    run_root,
    run_stage_metadata_path,
    run_stage_root,
    write_json_payload,
)
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState, is_terminal_state

TERMINAL_RECONCILIATION_FILENAME = "terminal-reconciliation.json"
TERMINAL_RECONCILIATION_SCHEMA_VERSION = 1
ABANDONED_STAGE_STATES = frozenset(
    {StageState.EXECUTING, StageState.VALIDATING}
)

ReconciliationDisposition = Literal[
    "reconciled",
    "already-terminal",
    "expected-state-mismatch",
    "metadata-identity-mismatch",
    "metadata-missing",
]


@dataclass(frozen=True, slots=True)
class TerminalStageReconciliationRequest:
    workspace_root: Path
    work_item: str
    run_id: str
    stage: str
    expected_state: str
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "workspace_root",
            self.workspace_root.resolve(strict=False),
        )
        object.__setattr__(
            self,
            "work_item",
            SafeIdentifier.parse(self.work_item, label="work item id").value,
        )
        object.__setattr__(
            self,
            "run_id",
            SafeIdentifier.parse(self.run_id, label="run id").value,
        )
        if self.stage not in STAGES:
            raise ValueError(f"Unknown stage: {self.stage!r}.")
        expected = StageState(self.expected_state.strip())
        if expected not in ABANDONED_STAGE_STATES:
            raise ValueError(
                "Expected stage state must be non-terminal and one of `executing` or "
                "`validating`."
            )
        object.__setattr__(self, "expected_state", expected.value)
        object.__setattr__(
            self,
            "reason",
            SafeIdentifier.parse(self.reason, label="reconciliation reason").value,
        )


@dataclass(frozen=True, slots=True)
class TerminalStageReconciliationResult:
    request: TerminalStageReconciliationRequest
    disposition: ReconciliationDisposition
    previous_status: str | None
    reconciled_status: str | None
    reconciled: bool
    status_history_count: int
    recorded_at_utc: str
    metadata_path: Path
    evidence_path: Path

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": TERMINAL_RECONCILIATION_SCHEMA_VERSION,
            "work_item": self.request.work_item,
            "run_id": self.request.run_id,
            "stage": self.request.stage,
            "expected_state": self.request.expected_state,
            "reason": self.request.reason,
            "disposition": self.disposition,
            "previous_status": self.previous_status,
            "reconciled_status": self.reconciled_status,
            "reconciled": self.reconciled,
            "status_history_count": self.status_history_count,
            "recorded_at_utc": self.recorded_at_utc,
            "metadata_path": self.metadata_path.as_posix(),
            "evidence_path": self.evidence_path.as_posix(),
        }


def _format_timestamp(value: datetime | None = None) -> str:
    return (value or datetime.now(UTC)).astimezone(UTC).isoformat().replace("+00:00", "Z")


def _evidence_path(request: TerminalStageReconciliationRequest) -> Path:
    return (
        run_stage_root(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )
        / TERMINAL_RECONCILIATION_FILENAME
    )


def _load_existing_result(
    *,
    request: TerminalStageReconciliationRequest,
    evidence_path: Path,
    current_status: str | None,
) -> TerminalStageReconciliationResult | None:
    if not evidence_path.exists():
        return None
    try:
        payload: Any = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    expected_identity = {
        "schema_version": TERMINAL_RECONCILIATION_SCHEMA_VERSION,
        "work_item": request.work_item,
        "run_id": request.run_id,
        "stage": request.stage,
        "expected_state": request.expected_state,
        "reason": request.reason,
    }
    if any(payload.get(key) != value for key, value in expected_identity.items()):
        return None
    reconciled_status = payload.get("reconciled_status")
    if reconciled_status != current_status:
        return None
    try:
        disposition = str(payload["disposition"])
        if disposition not in {
            "reconciled",
            "already-terminal",
            "expected-state-mismatch",
            "metadata-identity-mismatch",
            "metadata-missing",
        }:
            return None
        return TerminalStageReconciliationResult(
            request=request,
            disposition=cast(ReconciliationDisposition, disposition),
            previous_status=(
                str(payload["previous_status"])
                if payload.get("previous_status") is not None
                else None
            ),
            reconciled_status=(
                str(reconciled_status) if reconciled_status is not None else None
            ),
            reconciled=payload.get("reconciled") is True,
            status_history_count=int(payload.get("status_history_count", 0)),
            recorded_at_utc=str(payload["recorded_at_utc"]),
            metadata_path=Path(str(payload["metadata_path"])),
            evidence_path=evidence_path,
        )
    except (KeyError, TypeError, ValueError):
        return None


def reconcile_terminal_stage(
    request: TerminalStageReconciliationRequest,
    *,
    changed_at_utc: datetime | None = None,
) -> TerminalStageReconciliationResult:
    metadata_path = run_stage_metadata_path(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
        stage=request.stage,
    )
    evidence_path = _evidence_path(request)
    selected_run_root = run_root(
        workspace_root=request.workspace_root,
        work_item=request.work_item,
        run_id=request.run_id,
    )
    with acquire_run_mutation_lease(
        selected_run_root,
        operation=f"stage:reconcile-terminal:{request.stage}",
    ):
        before = load_stage_metadata(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )
        previous_status = None if before is None else before.status
        existing = _load_existing_result(
            request=request,
            evidence_path=evidence_path,
            current_status=previous_status,
        )
        if existing is not None:
            return existing

        disposition: ReconciliationDisposition
        reconciled = False
        if before is None:
            disposition = "metadata-missing"
        elif (
            before.run_id != request.run_id
            or before.work_item_id != request.work_item
            or before.stage != request.stage
        ):
            disposition = "metadata-identity-mismatch"
        else:
            try:
                current_state = StageState(before.status)
            except ValueError:
                disposition = "expected-state-mismatch"
            else:
                if is_terminal_state(current_state):
                    disposition = "already-terminal"
                elif current_state.value != request.expected_state:
                    disposition = "expected-state-mismatch"
                else:
                    persist_stage_status(
                        workspace_root=request.workspace_root,
                        work_item=request.work_item,
                        run_id=request.run_id,
                        stage=request.stage,
                        status=StageState.FAILED.value,
                        changed_at_utc=changed_at_utc,
                    )
                    disposition = "reconciled"
                    reconciled = True

        after = load_stage_metadata(
            workspace_root=request.workspace_root,
            work_item=request.work_item,
            run_id=request.run_id,
            stage=request.stage,
        )
        result = TerminalStageReconciliationResult(
            request=request,
            disposition=disposition,
            previous_status=previous_status,
            reconciled_status=None if after is None else after.status,
            reconciled=reconciled,
            status_history_count=0 if after is None else len(after.status_history),
            recorded_at_utc=(
                after.updated_at_utc
                if reconciled and after is not None
                else _format_timestamp(changed_at_utc)
            ),
            metadata_path=metadata_path,
            evidence_path=evidence_path,
        )
        write_json_payload(evidence_path, result.to_payload())
        return result


__all__ = [
    "ABANDONED_STAGE_STATES",
    "TERMINAL_RECONCILIATION_FILENAME",
    "TERMINAL_RECONCILIATION_SCHEMA_VERSION",
    "TerminalStageReconciliationRequest",
    "TerminalStageReconciliationResult",
    "reconcile_terminal_stage",
]
