from __future__ import annotations

from pathlib import Path

from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.runtime_registry import RuntimeExecutionMode
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.core.runtime_operator import (
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    load_operator_decisions,
    load_operator_requests,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
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
        assert load_operator_requests(requests_path)[-1].id == request.id
        assert not decisions_path.exists()
        self.requests.append(request)
        return RuntimeOperatorDecision(
            request_id=request.id,
            action=self.action,
            source=RuntimeOperatorDecisionSource.CLI,
            reason="generic conformance decision",
        )


def _request(tmp_path: Path) -> StageRuntimeRequest:
    repo = tmp_path / "repo"
    workspace = tmp_path / ".aidd"
    repo.mkdir()
    workspace.mkdir()
    stage_brief = workspace / "stage-brief.md"
    prompt_pack = workspace / "prompt-pack.md"
    stage_brief.write_text("# Stage brief\n", encoding="utf-8")
    prompt_pack.write_text("# Prompt pack\n", encoding="utf-8")
    return StageRuntimeRequest(
        runtime_id="generic-cli",
        execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
        permission_policy=RuntimePermissionPolicy.BROKERED,
        interaction_mode=RuntimeInteractionMode.LIVE,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        timeout_seconds=None,
        stage="implement",
        work_item="WI-LIVE",
        run_id="run-live",
        workspace_root=workspace,
        stage_brief_path=stage_brief,
        prompt_pack_paths=(prompt_pack,),
        repository_root=repo,
        project_roots=(repo,),
    )


def test_generic_live_conformance_resumes_after_allow_decision(tmp_path: Path) -> None:
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("generic-cli").execute_stage_request(
        configured_command="generic-cli-live-conformance",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    assert result.operator_requests_path is not None
    assert result.operator_decisions_path is not None
    assert provider.requests[0].payload["command"] == "npm install"
    assert load_operator_decisions(result.operator_decisions_path)[-1].action is (
        RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION
    )


def test_generic_live_conformance_blocks_without_provider(tmp_path: Path) -> None:
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("generic-cli").execute_stage_request(
        configured_command="generic-cli-live-conformance",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert result.pending_operator_request_ids
    assert result.operator_requests_path is not None
    assert load_operator_decisions(attempt_path / "operator-decisions.jsonl") == ()


def test_standard_subprocess_path_stays_blocked_even_with_live_provider(
    tmp_path: Path,
) -> None:
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("generic-cli").execute_stage_request(
        configured_command="python",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert result.pending_operator_request_ids
    assert provider.requests == []
    assert load_operator_decisions(attempt_path / "operator-decisions.jsonl") == ()


def test_generic_live_conformance_fails_after_cancel_decision(tmp_path: Path) -> None:
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.CANCEL)

    result = get_runtime_adapter_surface("generic-cli").execute_stage_request(
        configured_command="generic-cli-live-conformance",
        request=_request(tmp_path),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == "permission-denied: cancel"
