from __future__ import annotations

import shlex
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aidd.core.runtime_operator import RuntimeOperatorDecision, RuntimeOperatorRequest
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
)


def codex_approval_request_to_operator_request(
    *,
    method: str,
    payload: Mapping[str, Any],
    runtime_id: str,
    stage: str,
    cwd: Path | None,
) -> RuntimeOperatorRequest:
    request_id = str(
        payload.get("request_id")
        or payload.get("id")
        or payload.get("approvalId")
        or payload.get("itemId")
        or payload.get("item_id")
        or ""
    ).strip()
    kind = _kind_for_method(method)
    paths = tuple(Path(str(path)) for path in _payload_paths(payload))
    normalized_payload = dict(payload)
    command = _payload_command(payload)
    if command is not None:
        normalized_payload["command"] = command
    return RuntimeOperatorRequest(
        id=request_id or RuntimeOperatorRequest.create(
            runtime_id=runtime_id,
            stage=stage,
            kind=kind,
        ).id,
        runtime_id=runtime_id,
        stage=stage,
        kind=kind,
        tool_name=str(payload.get("tool_name") or method),
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


def operator_decision_to_codex_response(
    decision: RuntimeOperatorDecision,
) -> dict[str, object]:
    mapped_action = {
        RuntimeOperatorDecisionAction.ALLOW_ONCE: "accept",
        RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION: "acceptForSession",
        RuntimeOperatorDecisionAction.DENY: "decline",
        RuntimeOperatorDecisionAction.CANCEL: "cancel",
    }[decision.action]
    return {
        "request_id": decision.request_id,
        "decision": mapped_action,
        "reason": decision.reason,
    }


def _kind_for_method(method: str) -> RuntimeOperatorRequestKind:
    normalized = method.lower()
    if (
        "commandexecution" in normalized
        or "command_execution" in normalized
        or "execcommand" in normalized
    ):
        return RuntimeOperatorRequestKind.SHELL
    if (
        "filechange" in normalized
        or "file_change" in normalized
        or "applypatch" in normalized
    ):
        return RuntimeOperatorRequestKind.FILE_EDIT
    if "permissions" in normalized or "permission" in normalized:
        return RuntimeOperatorRequestKind.RUNTIME_PERMISSION
    return RuntimeOperatorRequestKind.UNKNOWN


def _payload_command(payload: Mapping[str, Any]) -> str | None:
    raw_command = (
        payload.get("command")
        or payload.get("cmd")
        or payload.get("commandLine")
        or payload.get("command_line")
    )
    if raw_command is None:
        return None
    if isinstance(raw_command, list | tuple):
        return shlex.join(str(token) for token in raw_command)
    return str(raw_command)


def _payload_paths(payload: Mapping[str, Any]) -> tuple[object, ...]:
    raw_paths = payload.get("paths")
    if isinstance(raw_paths, list | tuple):
        return tuple(raw_paths)
    raw_path = payload.get("path") or payload.get("file_path")
    paths: list[object] = [] if raw_path is None else [raw_path]
    grant_root = payload.get("grantRoot")
    if grant_root is not None:
        paths.append(grant_root)
    command_actions = payload.get("commandActions")
    if isinstance(command_actions, list):
        for action in command_actions:
            if isinstance(action, Mapping) and action.get("path") is not None:
                paths.append(action["path"])
    changes = payload.get("changes")
    if isinstance(changes, list):
        for change in changes:
            if isinstance(change, Mapping) and change.get("path") is not None:
                paths.append(change["path"])
    return tuple(paths)
