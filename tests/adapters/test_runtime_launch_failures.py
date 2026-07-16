from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from aidd.adapters.runtime_evidence import RuntimeAdapterOutcome
from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.surface import (
    default_execution_mode_for_surface,
    get_runtime_adapter_surface,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimePermissionPolicy,
)

_RUNTIME_IDS = ("generic-cli", "claude-code", "codex", "opencode", "qwen")


def _request(tmp_path: Path, runtime_id: str) -> StageRuntimeRequest:
    workspace_root = tmp_path / ".aidd"
    repository_root = tmp_path / "repo"
    workspace_root.mkdir(exist_ok=True)
    repository_root.mkdir(exist_ok=True)
    stage_brief_path = workspace_root / "stage-brief.md"
    prompt_pack_path = workspace_root / "prompt-pack.md"
    stage_brief_path.write_text("# Stage brief\n", encoding="utf-8")
    prompt_pack_path.write_text("# Prompt pack\n", encoding="utf-8")
    surface = get_runtime_adapter_surface(runtime_id)
    return StageRuntimeRequest(
        runtime_id=runtime_id,
        execution_mode=default_execution_mode_for_surface(surface),
        permission_policy=RuntimePermissionPolicy.FULL_ACCESS,
        interaction_mode=RuntimeInteractionMode.BATCH,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        timeout_seconds=1.0,
        stage="idea",
        work_item="WI-LAUNCH",
        run_id="run-launch",
        workspace_root=workspace_root,
        stage_brief_path=stage_brief_path,
        prompt_pack_paths=(prompt_pack_path,),
        repository_root=repository_root,
        project_roots=(repository_root,),
    )


@pytest.mark.parametrize("runtime_id", _RUNTIME_IDS)
@pytest.mark.parametrize("failure_kind", ("missing", "non_executable"))
def test_registered_runtime_launch_failures_commit_equivalent_evidence(
    tmp_path: Path,
    runtime_id: str,
    failure_kind: str,
) -> None:
    if failure_kind == "missing":
        configured_command = str(tmp_path / "missing-runtime")
    else:
        executable_path = tmp_path / "non-executable-runtime"
        executable_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable_path.chmod(0o644)
        configured_command = str(executable_path)
    attempt_path = tmp_path / f"attempt-{runtime_id}-{failure_kind}"

    result = get_runtime_adapter_surface(runtime_id).execute_stage_request(
        configured_command=configured_command,
        request=_request(tmp_path, runtime_id),
        attempt_path=attempt_path,
        base_env=dict(os.environ),
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.adapter_outcome is RuntimeAdapterOutcome.LAUNCH_FAILURE
    assert result.runtime_log_path == attempt_path / "runtime.log"
    assert result.runtime_exit_metadata_path == attempt_path / "runtime-exit.json"
    assert result.runtime_log_path is not None
    assert result.runtime_exit_metadata_path is not None
    assert "[launch-failure]" in result.runtime_log_path.read_text(encoding="utf-8")
    metadata = json.loads(
        result.runtime_exit_metadata_path.read_text(encoding="utf-8")
    )
    assert metadata["adapter_outcome"] == "launch_failure"
    assert metadata["exit_code"] is None
    assert metadata["stop_reason"] == "launch_failure"
