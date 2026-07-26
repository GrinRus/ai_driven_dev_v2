from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aidd.harness.live_e2e_black_box_steps import (
    BlackBoxCommandResult,
    _run_black_box_command,
)


class LiveTerminalReconciliationError(RuntimeError):
    """Raised when the installed public reconciliation command cannot be trusted."""


@dataclass(frozen=True, slots=True)
class LiveTerminalReconciliationResult:
    command_result: BlackBoxCommandResult
    payload: dict[str, object]
    evidence_path: Path


def _parse_payload(
    *,
    command_result: BlackBoxCommandResult,
    working_copy: Path,
    work_item: str,
    run_id: str,
    stage: str,
    expected_state: str,
    reason: str,
) -> tuple[dict[str, object], Path]:
    try:
        payload = json.loads(command_result.stdout_text)
    except json.JSONDecodeError as exc:
        raise LiveTerminalReconciliationError(
            "Installed terminal reconciliation did not emit one JSON result."
        ) from exc
    if not isinstance(payload, dict):
        raise LiveTerminalReconciliationError(
            "Installed terminal reconciliation result must be a JSON object."
        )
    expected_identity = {
        "work_item": work_item,
        "run_id": run_id,
        "stage": stage,
        "expected_state": expected_state,
        "reason": reason,
    }
    for field, expected in expected_identity.items():
        if payload.get(field) != expected:
            raise LiveTerminalReconciliationError(
                f"Installed terminal reconciliation returned wrong `{field}` identity."
            )
    raw_evidence_path = payload.get("evidence_path")
    if not isinstance(raw_evidence_path, str) or not raw_evidence_path:
        raise LiveTerminalReconciliationError(
            "Installed terminal reconciliation omitted its evidence path."
        )
    evidence_path = Path(raw_evidence_path)
    if not evidence_path.is_absolute():
        evidence_path = working_copy / evidence_path
    resolved_working_copy = working_copy.resolve(strict=False)
    resolved_evidence = evidence_path.resolve(strict=False)
    if not resolved_evidence.is_relative_to(resolved_working_copy):
        raise LiveTerminalReconciliationError(
            "Installed terminal reconciliation evidence escaped the target working copy."
        )
    return payload, resolved_evidence


def run_live_terminal_reconciliation(
    *,
    installed_command: tuple[str, ...],
    working_copy: Path,
    environment: dict[str, str],
    work_item: str,
    run_id: str,
    stage: str,
    expected_state: str,
    reason: str,
    timeout_seconds: float = 30.0,
) -> LiveTerminalReconciliationResult:
    command = (
        *installed_command,
        "stage",
        "reconcile-terminal",
        stage,
        "--work-item",
        work_item,
        "--run-id",
        run_id,
        "--expected-state",
        expected_state,
        "--reason",
        reason,
        "--root",
        ".aidd",
    )
    command_result = _run_black_box_command(
        command=command,
        cwd=working_copy,
        environment=environment,
        timeout_seconds=timeout_seconds,
    )
    if command_result.exit_code != 0:
        detail = command_result.stderr_text.strip() or command_result.stdout_text.strip()
        raise LiveTerminalReconciliationError(
            "Installed terminal reconciliation failed with exit "
            f"{command_result.exit_code}: {detail or 'no command output'}"
        )
    payload, evidence_path = _parse_payload(
        command_result=command_result,
        working_copy=working_copy,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        expected_state=expected_state,
        reason=reason,
    )
    return LiveTerminalReconciliationResult(
        command_result=command_result,
        payload=payload,
        evidence_path=evidence_path,
    )


__all__ = [
    "LiveTerminalReconciliationError",
    "LiveTerminalReconciliationResult",
    "run_live_terminal_reconciliation",
]
