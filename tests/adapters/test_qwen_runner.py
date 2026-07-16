from __future__ import annotations

import os
import sys
from pathlib import Path

import aidd.adapters.surface as surface_module
from aidd.adapters.qwen.runner import (
    QwenCommandContext,
    QwenExitClassification,
    QwenRunResult,
    QwenSubprocessSpec,
    build_subprocess_spec,
    run_subprocess_with_streaming,
)
from aidd.adapters.runtime_execution import StageRuntimeRequest
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimePermissionPolicy,
)


def test_qwen_intervention_metadata_reaches_native_prompt_and_all_environments(
    tmp_path: Path,
) -> None:
    repository_root = tmp_path / "repo"
    workspace = repository_root / ".aidd"
    stage_root = workspace / "workitems" / "WI-QWEN" / "stages" / "plan"
    stage_root.mkdir(parents=True)
    stage_brief = stage_root / "stage-brief.md"
    prompt_pack = repository_root / "prompt-packs" / "stages" / "plan" / "intervention.md"
    operator_request = stage_root / "operator-requests" / "request-0001.md"
    prompt_pack.parent.mkdir(parents=True)
    operator_request.parent.mkdir(parents=True)
    stage_brief.write_text("# Stage brief\n", encoding="utf-8")
    prompt_pack.write_text("# Intervention prompt\n", encoding="utf-8")
    operator_request.write_text(
        "# Operator Request\n\nAdd rollback evidence.\n",
        encoding="utf-8",
    )
    context = QwenCommandContext(
        stage="plan",
        work_item="WI-QWEN",
        run_id="run-qwen",
        workspace_root=workspace,
        stage_brief_path=stage_brief,
        prompt_pack_paths=(prompt_pack,),
        attempt_number=2,
        attempt_mode="intervention",
        operator_request_path=operator_request,
        operator_request_markdown="# Operator Request\n\nUse the requested scope only.\n",
    )

    native_spec = build_subprocess_spec(
        configured_command="qwen",
        context=context,
        repository_root=repository_root,
        execution_mode=RuntimeExecutionMode.NATIVE,
    )
    adapter_flags_spec = build_subprocess_spec(
        configured_command="qwen-wrapper",
        context=context,
        repository_root=repository_root,
        execution_mode=RuntimeExecutionMode.ADAPTER_FLAGS,
    )

    for spec in (native_spec, adapter_flags_spec):
        assert spec.env["AIDD_ATTEMPT_MODE"] == "intervention"
        assert spec.env["AIDD_OPERATOR_REQUEST_PATH"] == operator_request.as_posix()
    assert native_spec.stdin_text is not None
    assert "- Attempt mode: intervention" in native_spec.stdin_text
    assert "## Operator request context" in native_spec.stdin_text
    assert "Use the requested scope only." in native_spec.stdin_text
    assert adapter_flags_spec.stdin_text is None


def test_qwen_runner_completes_when_expected_documents_settle(tmp_path: Path) -> None:
    stage_root = tmp_path / ".aidd" / "workitems" / "WI-QWEN" / "stages" / "qa"
    stage_root.mkdir(parents=True)
    qa_report = stage_root / "qa-report.md"
    stage_result = stage_root / "stage-result.md"
    validator_report = stage_root / "validator-report.md"
    for path, text in (
        (qa_report, "# QA Report\n\nPending.\n"),
        (stage_result, "# Stage result\n\nStage not run yet.\n"),
        (validator_report, "# Validator report\n\nNo validator output yet.\n"),
    ):
        path.write_text(text, encoding="utf-8")
    script = (
        "import pathlib, sys, time\n"
        "pathlib.Path(sys.argv[1]).write_text('# QA Report\\n\\nReady.\\n', "
        "encoding='utf-8')\n"
        "pathlib.Path(sys.argv[2]).write_text("
        "'# Stage Result\\n\\n## Status\\n\\n- Status: `succeeded`\\n', "
        "encoding='utf-8')\n"
        "pathlib.Path(sys.argv[3]).write_text("
        "'# Validator Report\\n\\n## Result\\n\\n- Validator verdict: `pass`\\n', "
        "encoding='utf-8')\n"
        "print('documents-written', flush=True)\n"
        "time.sleep(5)\n"
    )
    spec = QwenSubprocessSpec(
        command=(
            sys.executable,
            "-c",
            script,
            qa_report.as_posix(),
            stage_result.as_posix(),
            validator_report.as_posix(),
        ),
        cwd=tmp_path,
        env=dict(os.environ),
    )

    result = run_subprocess_with_streaming(
        spec=spec,
        timeout_seconds=5.0,
        document_completion_paths=(qa_report, stage_result, validator_report),
        document_completion_settle_seconds=0.01,
    )

    assert result.exit_classification is QwenExitClassification.DOCUMENT_COMPLETE
    assert result.exit_code != 0
    assert "documents-written\n" in result.runtime_log_text


def test_qwen_surface_treats_document_complete_as_success(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    workspace = repo / ".aidd"
    stage_root = workspace / "workitems" / "WI-QWEN" / "stages" / "qa"
    stage_root.mkdir(parents=True)
    repo.mkdir(exist_ok=True)
    stage_brief = stage_root / "stage-brief.md"
    prompt_pack = stage_root / "prompt-pack.md"
    qa_report = stage_root / "qa-report.md"
    stage_result = stage_root / "stage-result.md"
    validator_report = stage_root / "validator-report.md"
    for path, text in (
        (stage_brief, "# Stage brief\n"),
        (prompt_pack, "# Prompt pack\n"),
        (qa_report, "# QA Report\n\nPending.\n"),
        (stage_result, "# Stage result\n\nStage not run yet.\n"),
        (validator_report, "# Validator report\n\nNo validator output yet.\n"),
    ):
        path.write_text(text, encoding="utf-8")
    operator_request = stage_root / "operator-requests" / "request-0001.md"
    operator_request.parent.mkdir(parents=True)
    operator_request.write_text(
        "# Operator Request\n\nStrengthen release evidence.\n",
        encoding="utf-8",
    )

    def fake_run_qwen_subprocess_with_streaming(**kwargs):
        assert kwargs["document_completion_paths"] == (qa_report, stage_result, validator_report)
        spec = kwargs["spec"]
        assert spec.env["AIDD_ATTEMPT_MODE"] == "intervention"
        assert spec.env["AIDD_OPERATOR_REQUEST_PATH"] == operator_request.as_posix()
        assert "- Attempt mode: intervention" in spec.stdin_text
        assert "Strengthen release evidence." in spec.stdin_text
        return QwenRunResult(
            exit_code=-15,
            stdout_text="documents-written\n",
            stderr_text="",
            runtime_log_text="documents-written\n",
            exit_classification=QwenExitClassification.DOCUMENT_COMPLETE,
        )

    monkeypatch.setattr(
        surface_module,
        "run_qwen_subprocess_with_streaming",
        fake_run_qwen_subprocess_with_streaming,
    )
    request = StageRuntimeRequest(
        runtime_id="qwen",
        execution_mode=RuntimeExecutionMode.NATIVE,
        permission_policy=RuntimePermissionPolicy.FULL_ACCESS,
        interaction_mode=RuntimeInteractionMode.BATCH,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        timeout_seconds=5.0,
        stage="qa",
        work_item="WI-QWEN",
        run_id="run-qwen",
        workspace_root=workspace,
        stage_brief_path=stage_brief,
        prompt_pack_paths=(prompt_pack,),
        repository_root=repo,
        attempt_number=2,
        attempt_mode="intervention",
        operator_request_path=operator_request,
        operator_request_markdown=operator_request.read_text(encoding="utf-8"),
        expected_output_documents=(qa_report, stage_result, validator_report),
    )

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=sys.executable,
        request=request,
        attempt_path=tmp_path / "attempt",
        base_env={},
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    assert result.details == "document_complete"
