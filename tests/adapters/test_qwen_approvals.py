from __future__ import annotations

from pathlib import Path

from aidd.adapters.qwen.approvals import (
    operator_decision_to_qwen_confirmation,
    qwen_control_request_to_operator_request,
)
from aidd.core.runtime_operator import RuntimeOperatorDecision
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
)


def test_qwen_control_request_maps_shell_approval() -> None:
    request = qwen_control_request_to_operator_request(
        {
            "type": "control_request",
            "payload": {
                "request_id": "qwen-1",
                "kind": "shell",
                "command": "npm install",
                "tool_name": "shell",
            },
        },
        runtime_id="qwen",
        stage="implement",
        cwd=Path("/repo"),
    )

    assert request.id == "qwen-1"
    assert request.kind is RuntimeOperatorRequestKind.SHELL
    assert request.payload["command"] == "npm install"
    assert request.cwd == Path("/repo")


def test_qwen_control_request_maps_unknown_kind_to_operator_question() -> None:
    request = qwen_control_request_to_operator_request(
        {
            "type": "control_request",
            "payload": {
                "request_id": "qwen-unknown",
                "kind": "provider_specific",
                "payload": {"raw": True},
            },
        },
        runtime_id="qwen",
        stage="qa",
        cwd=None,
    )

    assert request.kind is RuntimeOperatorRequestKind.UNKNOWN
    assert request.id == "qwen-unknown"


def test_qwen_control_request_maps_nested_real_tool_payload() -> None:
    request = qwen_control_request_to_operator_request(
        {
            "type": "control_request",
            "id": "evt-outer",
            "payload": {
                "request": {
                    "id": "qwen-real-1",
                    "kind": "tool_call",
                    "tool": {
                        "name": "bash",
                        "input": {
                            "command": "uv run pytest -q",
                            "paths": ["tests"],
                        },
                    },
                },
            },
        },
        runtime_id="qwen",
        stage="qa",
        cwd=Path("/repo"),
    )

    assert request.id == "qwen-real-1"
    assert request.kind is RuntimeOperatorRequestKind.SHELL
    assert request.tool_name == "bash"
    assert request.payload["command"] == "uv run pytest -q"
    assert request.paths == (Path("tests"),)


def test_qwen_control_request_maps_file_path_aliases() -> None:
    request = qwen_control_request_to_operator_request(
        {
            "type": "confirmation_request",
            "payload": {
                "request_id": "qwen-file-1",
                "kind": "write",
                "tool_name": "write_file",
                "file_path": "src/app.py",
            },
        },
        runtime_id="qwen",
        stage="implement",
        cwd=Path("/repo"),
    )

    assert request.kind is RuntimeOperatorRequestKind.FILE_WRITE
    assert request.paths == (Path("src/app.py"),)


def test_qwen_decision_maps_to_confirmation_response() -> None:
    decision = RuntimeOperatorDecision(
        request_id="qwen-1",
        action=RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
        source=RuntimeOperatorDecisionSource.UI,
        reason="approved",
    )

    response = operator_decision_to_qwen_confirmation(decision)

    assert response == {
        "type": "confirmation_response",
        "request_id": "qwen-1",
        "allowed": True,
        "scope": "session",
        "cancel": False,
        "reason": "approved",
    }
