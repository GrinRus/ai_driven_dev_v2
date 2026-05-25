from __future__ import annotations

from pathlib import Path

from aidd.adapters.claude_code.approvals import (
    claude_permission_prompt_to_operator_request,
    operator_decision_to_claude_permission_response,
)
from aidd.adapters.codex.approvals import (
    codex_approval_request_to_operator_request,
    operator_decision_to_codex_response,
)
from aidd.adapters.opencode.approvals import (
    opencode_permission_request_to_operator_request,
    operator_decision_to_opencode_response,
)
from aidd.core.runtime_operator import RuntimeOperatorDecision
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
)


def test_codex_approval_mapper_handles_command_execution() -> None:
    request = codex_approval_request_to_operator_request(
        method="item/commandExecution/requestApproval",
        payload={"request_id": "codex-1", "command": "git push"},
        runtime_id="codex",
        stage="qa",
        cwd=Path("/repo"),
    )

    assert request.id == "codex-1"
    assert request.kind is RuntimeOperatorRequestKind.SHELL
    assert request.payload["command"] == "git push"

    response = operator_decision_to_codex_response(
        RuntimeOperatorDecision(
            request_id="codex-1",
            action=RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION,
            source=RuntimeOperatorDecisionSource.UI,
        )
    )
    assert response["decision"] == "acceptForSession"


def test_codex_approval_mapper_handles_real_command_payload_aliases() -> None:
    request = codex_approval_request_to_operator_request(
        method="item/commandExecution/requestApproval",
        payload={
            "approvalId": "approval-1",
            "itemId": "item-1",
            "commandLine": ["bash", "-lc", "npm test"],
            "commandActions": [{"path": "package.json"}],
        },
        runtime_id="codex",
        stage="qa",
        cwd=Path("/repo"),
    )

    assert request.id == "approval-1"
    assert request.kind is RuntimeOperatorRequestKind.SHELL
    assert request.payload["command"] == "bash -lc 'npm test'"
    assert request.paths == (Path("package.json"),)


def test_codex_approval_mapper_handles_file_permissions_and_legacy_names() -> None:
    file_request = codex_approval_request_to_operator_request(
        method="item/fileChange/requestApproval",
        payload={"approvalId": "file-1", "grantRoot": "/repo/src", "changes": [{"path": "a.py"}]},
        runtime_id="codex",
        stage="implement",
        cwd=Path("/repo"),
    )
    permissions_request = codex_approval_request_to_operator_request(
        method="item/permissions/requestApproval",
        payload={"approvalId": "perm-1", "permissions": {"network": True}},
        runtime_id="codex",
        stage="qa",
        cwd=Path("/repo"),
    )
    legacy_exec_request = codex_approval_request_to_operator_request(
        method="execCommandApproval",
        payload={"id": "legacy-exec", "command": "pwd"},
        runtime_id="codex",
        stage="qa",
        cwd=Path("/repo"),
    )
    legacy_patch_request = codex_approval_request_to_operator_request(
        method="applyPatchApproval",
        payload={"id": "legacy-patch", "path": "src/app.py"},
        runtime_id="codex",
        stage="implement",
        cwd=Path("/repo"),
    )

    assert file_request.kind is RuntimeOperatorRequestKind.FILE_EDIT
    assert file_request.paths == (Path("/repo/src"), Path("a.py"))
    assert permissions_request.kind is RuntimeOperatorRequestKind.RUNTIME_PERMISSION
    assert legacy_exec_request.kind is RuntimeOperatorRequestKind.SHELL
    assert legacy_patch_request.kind is RuntimeOperatorRequestKind.FILE_EDIT


def test_opencode_permission_mapper_handles_file_edit() -> None:
    request = opencode_permission_request_to_operator_request(
        {"id": "open-1", "tool": "edit", "path": "src/app.py"},
        runtime_id="opencode",
        stage="implement",
        cwd=Path("/repo"),
    )

    assert request.id == "open-1"
    assert request.kind is RuntimeOperatorRequestKind.FILE_EDIT
    assert request.paths == (Path("src/app.py"),)

    response = operator_decision_to_opencode_response(
        RuntimeOperatorDecision(
            request_id="open-1",
            action=RuntimeOperatorDecisionAction.DENY,
            source=RuntimeOperatorDecisionSource.CLI,
        )
    )
    assert response["allow"] is False


def test_claude_permission_prompt_mapper_handles_bash_and_response() -> None:
    request = claude_permission_prompt_to_operator_request(
        tool_name="Bash",
        tool_input={"command": "npm install"},
        runtime_id="claude-code",
        stage="implement",
        cwd=Path("/repo"),
        request_id="claude-1",
    )

    assert request.id == "claude-1"
    assert request.kind is RuntimeOperatorRequestKind.SHELL
    assert request.payload["command"] == "npm install"

    response = operator_decision_to_claude_permission_response(
        RuntimeOperatorDecision(
            request_id="claude-1",
            action=RuntimeOperatorDecisionAction.CANCEL,
            source=RuntimeOperatorDecisionSource.UI,
            reason="cancelled",
        )
    )
    assert response["behavior"] == "deny"
    assert response["message"] == "cancelled"
