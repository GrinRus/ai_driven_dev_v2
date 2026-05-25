from __future__ import annotations

import json
import sys
from pathlib import Path

from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.core.runtime_operator import (
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    load_operator_requests,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
    RuntimePermissionPolicy,
)


class _DecisionProvider:
    def __init__(self, action: RuntimeOperatorDecisionAction) -> None:
        self.action = action
        self.requests: list[RuntimeOperatorRequest] = []

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> RuntimeOperatorDecision:
        _ = requests_path, decisions_path
        self.requests.append(request)
        return RuntimeOperatorDecision(
            request_id=request.id,
            action=self.action,
            source=RuntimeOperatorDecisionSource.CLI,
            reason="codex fake decision",
        )


class _NoDecisionProvider:
    def __init__(self) -> None:
        self.requests: list[RuntimeOperatorRequest] = []

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> None:
        _ = requests_path, decisions_path
        self.requests.append(request)
        return None


def _request(tmp_path: Path, *, timeout_seconds: float = 5.0) -> StageRuntimeRequest:
    repo = tmp_path / "repo"
    workspace = tmp_path / ".aidd"
    repo.mkdir(exist_ok=True)
    workspace.mkdir(exist_ok=True)
    stage_brief = workspace / "stage-brief.md"
    prompt_pack = workspace / "prompt-pack.md"
    stage_brief.write_text("# Stage brief\n", encoding="utf-8")
    prompt_pack.write_text("# Prompt pack\n", encoding="utf-8")
    return StageRuntimeRequest(
        runtime_id="codex",
        execution_mode=RuntimeExecutionMode.NATIVE,
        permission_policy=RuntimePermissionPolicy.BROKERED,
        interaction_mode=RuntimeInteractionMode.LIVE,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        timeout_seconds=timeout_seconds,
        stage="implement",
        work_item="WI-CODEX",
        run_id="run-codex",
        workspace_root=workspace,
        stage_brief_path=stage_brief,
        prompt_pack_paths=(prompt_pack,),
        repository_root=repo,
        project_roots=(repo,),
    )


def _fake_codex(tmp_path: Path, *, scenario: str = "command") -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "codex"
    script.write_text(
        f"#!{sys.executable}\n"
        f"scenario = {scenario!r}\n"
        "import json, sys, time\n"
        "def emit(payload):\n"
        "    print(json.dumps(payload), flush=True)\n"
        "if sys.argv[1:3] == ['app-server', '--help']:\n"
        "    print('Usage: codex app-server --listen generate-json-schema')\n"
        "    raise SystemExit(0)\n"
        "if sys.argv[1:4] == ['app-server', 'generate-json-schema', '--help']:\n"
        "    print('Usage: generate-json-schema --out DIR')\n"
        "    raise SystemExit(0)\n"
        "if sys.argv[1:4] != ['app-server', '--listen', 'stdio://']:\n"
        "    raise SystemExit(2)\n"
        "if scenario == 'timeout':\n"
        "    time.sleep(10)\n"
        "    raise SystemExit(3)\n"
        "thread_id = 'thread-1'\n"
        "for line in sys.stdin:\n"
        "    msg = json.loads(line)\n"
        "    method = msg.get('method')\n"
        "    if method == 'initialize':\n"
        "        emit({'id': msg['id'], 'result': {'userAgent': 'fake', "
        "'codexHome': '/tmp/fake', 'platformFamily': 'unix', 'platformOs': 'test'}})\n"
        "    elif method == 'initialized':\n"
        "        pass\n"
        "    elif method == 'thread/start':\n"
        "        emit({'id': msg['id'], 'result': {'thread': {'id': thread_id}, "
        "'approvalPolicy': 'on-request', 'approvalsReviewer': 'user', "
        "'cwd': msg['params']['cwd'], 'model': 'fake', 'modelProvider': 'fake', "
        "'sandbox': {'type': 'workspaceWrite'}}})\n"
        "    elif method == 'turn/start':\n"
        "        emit({'id': msg['id'], 'result': {'turn': {'id': 'turn-1'}}})\n"
        "        if scenario == 'file_permissions':\n"
        "            print('not-json-from-server', flush=True)\n"
        "            emit({'id': 'file-approval', 'method': "
        "'item/fileChange/requestApproval', 'params': {'approvalId': "
        "'file-approval', 'itemId': 'file-item', 'cwd': msg['params']['cwd'], "
        "'grantRoot': msg['params']['cwd'] + '/src', "
        "'changes': [{'path': 'src/app.py'}]}})\n"
        "            continue\n"
        "        emit({'id': 'approval-1', 'method': 'item/commandExecution/requestApproval', "
        "'params': {'approvalId': 'approval-1', 'itemId': 'item-1', "
        "'threadId': thread_id, 'turnId': 'turn-1', 'startedAtMs': 1, "
        "'cwd': msg['params']['cwd'], 'command': 'npm install'}})\n"
        "    elif msg.get('id') == 'file-approval':\n"
        "        emit({'id': 'perm-approval', 'method': "
        "'item/permissions/requestApproval', 'params': {'approvalId': "
        "'perm-approval', 'itemId': 'perm-item', 'cwd': msg.get('params', {}).get('cwd'), "
        "'permissions': {'network': True}}})\n"
        "    elif msg.get('id') == 'perm-approval':\n"
        "        emit({'method': 'turn/completed', 'params': {'threadId': thread_id, "
        "'turn': {'id': 'turn-1'}}})\n"
        "        raise SystemExit(0)\n"
        "    elif msg.get('id') == 'approval-1':\n"
        "        emit({'method': 'turn/completed', 'params': {'threadId': thread_id, "
        "'turn': {'id': 'turn-1'}}})\n"
        "        raise SystemExit(0)\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_codex_live_transport_resumes_after_provider_decision(tmp_path: Path) -> None:
    fake_codex = _fake_codex(tmp_path)
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("codex").execute_stage_request(
        configured_command=f"{fake_codex} exec --json -",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    assert provider.requests[0].payload["command"] == "npm install"
    transcript = [
        json.loads(line)
        for line in (attempt_path / "codex-app-server.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
    ]
    approval_response = [
        item["payload"]
        for item in transcript
        if item["direction"] == "client" and item["payload"].get("id") == "approval-1"
    ][0]
    assert approval_response["result"] == {"decision": "acceptForSession"}


def test_codex_live_transport_denial_fails_stage(tmp_path: Path) -> None:
    fake_codex = _fake_codex(tmp_path)
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.DENY)

    result = get_runtime_adapter_surface("codex").execute_stage_request(
        configured_command=f"{fake_codex} exec --json -",
        request=_request(tmp_path),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == "permission-denied: deny"


def test_codex_live_transport_blocks_when_provider_has_no_decision(tmp_path: Path) -> None:
    fake_codex = _fake_codex(tmp_path)
    provider = _NoDecisionProvider()
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("codex").execute_stage_request(
        configured_command=f"{fake_codex} exec --json -",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert result.pending_operator_request_ids == ("approval-1",)
    assert provider.requests[0].id == "approval-1"
    assert (attempt_path / "operator-requests.jsonl").exists()
    assert (attempt_path / "codex-app-server.jsonl").exists()


def test_codex_live_transport_timeout_fails_stage(tmp_path: Path) -> None:
    fake_codex = _fake_codex(tmp_path, scenario="timeout")

    result = get_runtime_adapter_surface("codex").execute_stage_request(
        configured_command=f"{fake_codex} exec --json -",
        request=_request(tmp_path, timeout_seconds=0.2),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=_DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE),
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == "codex-live: timeout"


def test_codex_live_transport_handles_file_and_permissions_requests(
    tmp_path: Path,
) -> None:
    fake_codex = _fake_codex(tmp_path, scenario="file_permissions")
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("codex").execute_stage_request(
        configured_command=f"{fake_codex} exec --json -",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    requests = load_operator_requests(attempt_path / "operator-requests.jsonl")
    assert [request.kind for request in requests] == [
        RuntimeOperatorRequestKind.FILE_EDIT,
        RuntimeOperatorRequestKind.RUNTIME_PERMISSION,
    ]
    assert requests[0].paths == (tmp_path / "repo" / "src", Path("src/app.py"))
    assert provider.requests[0].id == "perm-approval"
    transcript = [
        json.loads(line)
        for line in (attempt_path / "codex-app-server.jsonl").read_text(
            encoding="utf-8",
        ).splitlines()
    ]
    permission_response = [
        item["payload"]
        for item in transcript
        if item["direction"] == "client" and item["payload"].get("id") == "perm-approval"
    ][0]
    assert permission_response["result"] == {
        "permissions": {"network": True},
        "scope": "session",
        "strictAutoReview": True,
    }
