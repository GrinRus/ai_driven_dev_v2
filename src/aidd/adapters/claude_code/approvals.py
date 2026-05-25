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


def claude_permission_prompt_to_operator_request(
    *,
    tool_name: str,
    tool_input: Mapping[str, Any],
    runtime_id: str,
    stage: str,
    cwd: Path | None,
    request_id: str | None = None,
) -> RuntimeOperatorRequest:
    kind = _kind_for_tool(tool_name)
    paths = tuple(Path(str(path)) for path in _payload_paths(tool_input))
    normalized_payload = dict(tool_input)
    command = tool_input.get("command") or tool_input.get("cmd")
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
        tool_name=tool_name,
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


def operator_decision_to_claude_permission_response(
    decision: RuntimeOperatorDecision,
) -> dict[str, object]:
    return {
        "behavior": "allow" if decision.is_approval else "deny",
        "updatedInput": {},
        "message": decision.reason,
    }


def _kind_for_tool(tool_name: str) -> RuntimeOperatorRequestKind:
    normalized = tool_name.lower()
    if normalized in {"bash", "shell"}:
        return RuntimeOperatorRequestKind.SHELL
    if normalized in {"edit", "multiedit", "notebookedit"}:
        return RuntimeOperatorRequestKind.FILE_EDIT
    if normalized in {"write"}:
        return RuntimeOperatorRequestKind.FILE_WRITE
    if normalized in {"read", "ls", "glob", "grep"}:
        return RuntimeOperatorRequestKind.FILE_READ
    if normalized in {"webfetch", "websearch"}:
        return RuntimeOperatorRequestKind.NETWORK
    return RuntimeOperatorRequestKind.UNKNOWN


def _payload_paths(payload: Mapping[str, Any]) -> tuple[object, ...]:
    raw_paths = payload.get("paths")
    if isinstance(raw_paths, list | tuple):
        return tuple(raw_paths)
    raw_path = payload.get("path") or payload.get("file_path")
    return () if raw_path is None else (raw_path,)
