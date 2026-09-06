from __future__ import annotations

from pathlib import Path

from aidd.adapters.codex.approvals import (
    codex_approval_request_to_operator_request,
    operator_decision_to_codex_response,
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


def test_codex_approval_mapper_extracts_real_file_change_path_shapes() -> None:
    request = codex_approval_request_to_operator_request(
        method="item/fileChange/requestApproval",
        payload={
            "itemId": "file-change-1",
            "files": [
                {"filePath": ".aidd/workitems/WI-001/stages/idea/idea-brief.md"},
                ".aidd/workitems/WI-001/stages/idea/stage-result.md",
            ],
            "patches": [
                {"targetPath": ".aidd/workitems/WI-001/stages/idea/validator-report.md"}
            ],
            "modifiedFiles": [
                {"absolutePath": "/repo/.aidd/workitems/WI-001/stages/idea/questions.md"}
            ],
        },
        runtime_id="codex",
        stage="idea",
        cwd=Path("/repo"),
    )

    assert request.id == "file-change-1"
    assert request.kind is RuntimeOperatorRequestKind.FILE_EDIT
    assert request.paths == (
        Path(".aidd/workitems/WI-001/stages/idea/idea-brief.md"),
        Path(".aidd/workitems/WI-001/stages/idea/stage-result.md"),
        Path("/repo/.aidd/workitems/WI-001/stages/idea/questions.md"),
        Path(".aidd/workitems/WI-001/stages/idea/validator-report.md"),
    )


def test_codex_approval_mapper_keeps_file_change_without_paths_unbounded() -> None:
    request = codex_approval_request_to_operator_request(
        method="item/fileChange/requestApproval",
        payload={"itemId": "file-change-2", "grantRoot": None, "reason": None},
        runtime_id="codex",
        stage="idea",
        cwd=Path("/repo"),
    )

    assert request.id == "file-change-2"
    assert request.kind is RuntimeOperatorRequestKind.FILE_EDIT
    assert request.paths == ()
