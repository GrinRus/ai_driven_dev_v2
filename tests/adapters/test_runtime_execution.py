from __future__ import annotations

from pathlib import Path

import pytest

from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimePermissionPolicy,
)


@pytest.mark.parametrize("timeout_seconds", (False, 0.0, -1.0, float("nan"), float("inf")))
def test_stage_runtime_request_rejects_invalid_timeout_budget(
    tmp_path: Path,
    timeout_seconds: float,
) -> None:
    with pytest.raises(ValueError, match="finite number greater than zero"):
        StageRuntimeRequest(
            runtime_id="codex",
            execution_mode=RuntimeExecutionMode.NATIVE,
            permission_policy=RuntimePermissionPolicy.FULL_ACCESS,
            interaction_mode=RuntimeInteractionMode.BATCH,
            auto_approval_preset=AutoApprovalPreset.OFF,
            timeout_seconds=timeout_seconds,
            stage="idea",
            work_item="WI-1",
            run_id="run-1",
            workspace_root=tmp_path,
            stage_brief_path=tmp_path / "stage-brief.md",
            prompt_pack_paths=(),
            repository_root=tmp_path,
        )
