from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aidd.core.runtime_operator import RuntimeOperatorDecision, RuntimeOperatorRequest
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
)


def opencode_permission_request_to_operator_request(
    payload: Mapping[str, Any],
    *,
    runtime_id: str,
    stage: str,
    cwd: Path | None,
) -> RuntimeOperatorRequest:
    request_id = str(payload.get("request_id") or payload.get("id") or "").strip()
    tool_name = str(payload.get("tool") or payload.get("tool_name") or "")
    kind = _kind_for_payload(payload=payload, tool_name=tool_name)
    paths = tuple(Path(str(path)) for path in _payload_paths(payload))
    normalized_payload = dict(payload)
    command = payload.get("command") or payload.get("cmd")
    if command is not None:
        normalized_payload["command"] = str(command)
    return RuntimeOperatorRequest(
        id=request_id or RuntimeOperatorRequest.create(
            runtime_id=runtime_id,
            stage=stage,
            kind=kind,
        ).id,
        runtime_id=runtime_id,
        stage=stage,
        kind=kind,
        tool_name=tool_name or None,
        payload=normalized_payload,
        cwd=cwd,
        paths=paths,
        risk=RuntimeOperatorRisk.HIGH if kind is RuntimeOperatorRequestKind.SHELL else (
            RuntimeOperatorRisk.MEDIUM
        ),
        suggestions=(
            RuntimeOperatorDecisionAction.ALLOW_ONCE,
            RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
            RuntimeOperatorDecisionAction.DENY,
            RuntimeOperatorDecisionAction.CANCEL,
        ),
    )


def operator_decision_to_opencode_response(
    decision: RuntimeOperatorDecision,
) -> dict[str, object]:
    return {
        "request_id": decision.request_id,
        "allow": decision.is_approval,
        "session": decision.action is RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
        "cancel": decision.action is RuntimeOperatorDecisionAction.CANCEL,
        "reason": decision.reason,
    }


def _kind_for_payload(
    *,
    payload: Mapping[str, Any],
    tool_name: str,
) -> RuntimeOperatorRequestKind:
    normalized = f"{payload.get('kind', '')} {payload.get('type', '')} {tool_name}".lower()
    if "bash" in normalized or "shell" in normalized or "command" in normalized:
        return RuntimeOperatorRequestKind.SHELL
    if "delete" in normalized:
        return RuntimeOperatorRequestKind.FILE_DELETE
    if "write" in normalized:
        return RuntimeOperatorRequestKind.FILE_WRITE
    if "edit" in normalized:
        return RuntimeOperatorRequestKind.FILE_EDIT
    if "read" in normalized:
        return RuntimeOperatorRequestKind.FILE_READ
    return RuntimeOperatorRequestKind.UNKNOWN


def _payload_paths(payload: Mapping[str, Any]) -> tuple[object, ...]:
    raw_paths = payload.get("paths")
    if isinstance(raw_paths, list | tuple):
        return tuple(raw_paths)
    raw_path = payload.get("path") or payload.get("file_path")
    return () if raw_path is None else (raw_path,)
