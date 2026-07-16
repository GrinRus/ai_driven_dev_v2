from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aidd.adapters.generic_cli.runner import (
    GenericCliExitClassification,
    GenericCliStageContext,
    build_subprocess_spec,
    persist_attempt_runtime_artifacts,
    run_subprocess_with_streaming,
)
from aidd.config import ProjectConfig, ProjectSetConfig
from aidd.core.project_set import resolve_project_set
from aidd.core.repair import RepairBudgetPolicy, persist_repair_history_snapshot
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    load_stage_metadata,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempts_root,
    run_stage_metadata_path,
)
from aidd.core.runtime_operator import (
    OperatorDecisionConflict,
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    append_operator_request,
    resolve_operator_decision,
)
from aidd.core.stage_runner import (
    ATTEMPT_INPUT_BUNDLE_FILENAME,
    ATTEMPT_REPAIR_CONTEXT_FILENAME,
    AdapterExecutionOutcome,
    AdapterExecutionStatus,
    AdapterInvocationBundle,
    PostValidationAction,
    RepairBudgetValidationTransition,
    StageExecutionState,
    StageInputPreflightError,
    StageInterviewRouting,
    StageOrchestrationResult,
    StageOutputDiscovery,
    StageResumeResult,
    StageStructuralValidationResult,
    StageValidationState,
    ValidationVerdict,
    decide_post_validation_transition,
    derive_validation_verdict,
    discover_stage_markdown_outputs,
    persist_execution_state,
    persist_validation_state,
    persist_validation_state_with_repair_budget,
    prepare_adapter_invocation,
    prepare_stage_bundle,
    prepare_stage_resume_after_answers,
    publish_stage_outputs_after_validation_pass,
    restore_core_owned_repair_brief,
    route_stage_questions_to_interview,
    run_single_stage_orchestration,
    run_structural_validation_after_output_discovery,
    update_stage_unblock_state,
)
from aidd.core.state_machine import StageState, is_terminal_state, transition_stage_state
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
)
from aidd.validators.models import ValidationFinding


def _materialize_expected_inputs(paths: tuple[Path, ...]) -> None:
    for index, path in enumerate(paths, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Input {index}\n\nPrepared input for `{path.name}`.\n",
            encoding="utf-8",
        )


def _materialize_expected_outputs(paths: tuple[Path, ...]) -> None:
    for index, path in enumerate(paths, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Output {index}\n\nPrepared output for `{path.name}`.\n",
            encoding="utf-8",
        )


def _valid_plan_output_documents() -> dict[str, str]:
    return {
        "plan.md": (
            "# Plan\n\n"
            "## Goals\n\n- Deliver a reviewable execution plan.\n\n"
            "## Out of scope\n\n- Runtime migration is excluded.\n\n"
            "## Milestones\n\n- M1: Draft and validate plan.\n\n"
            "## Implementation strategy\n\n- Use staged, document-first increments.\n\n"
            "## Risks\n\n- Risk: Missing constraints; mitigation: clarify assumptions.\n\n"
            "## Dependencies\n\n- Research artifacts from prior stage.\n\n"
            "## Verification approach\n\n- Run structural and semantic checks.\n\n"
            "## Verification notes\n\n"
            "- M1: Validate highest-risk milestone with targeted tests.\n"
        ),
        "stage-result.md": (
            "# Stage result\n\n"
            "## Stage\n\nplan\n\n"
            "## Attempt history\n\n- attempt-0001\n\n"
            "## Status\n\nsucceeded\n\n"
            "## Produced outputs\n\n- plan.md\n\n"
            "## Validation summary\n\n- structural: pass\n\n"
            "## Blockers\n\n- none\n\n"
            "## Next actions\n\n- advance\n\n"
            "## Terminal state notes\n\nReady.\n"
        ),
        "validator-report.md": (
            "# Validator Report\n\n"
            "## Summary\n\n- Total issues: 0\n\n"
            "## Structural checks\n\n- none\n\n"
            "## Semantic checks\n\n- none\n\n"
            "## Cross-document checks\n\n- none\n\n"
            "## Result\n\n- Verdict: `pass`\n"
        ),
        "questions.md": "# Questions\n\n- none\n",
        "answers.md": "# Answers\n\n- none\n",
    }


def _write_runtime_writer_command(
    *,
    tmp_path: Path,
    documents: dict[str, str],
    exit_code: int = 0,
) -> str:
    script_path = tmp_path / f"runtime_writer_{exit_code}.py"
    script_lines = [
        "import os",
        "import sys",
        "from pathlib import Path",
        f"documents = {documents!r}",
        "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
        (
            "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM'] / "
            "'stages' / os.environ['AIDD_STAGE']"
        ),
        "stage_root.mkdir(parents=True, exist_ok=True)",
        "for name, content in documents.items():",
        "    (stage_root / name).write_text(content, encoding='utf-8')",
        f"raise SystemExit({exit_code})",
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return f"{sys.executable} {script_path.as_posix()}"


def test_prepare_stage_bundle_resolves_expected_inputs_and_outputs(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )

    assert bundle.stage == "implement"
    assert bundle.work_item == "WI-001"
    expected_required_inputs = (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md",
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "stage-result.md",
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "tasklist"
        / "output"
        / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "context" / "repository-state.md",
    )
    assert bundle.required_input_documents == expected_required_inputs
    assert bundle.optional_input_documents == ()
    assert bundle.expected_input_bundle == expected_required_inputs
    optional_constraints = (
        workspace_root / "workitems" / "WI-001" / "context" / "constraints.md"
    )
    optional_constraints.parent.mkdir(parents=True, exist_ok=True)
    optional_constraints.write_text("# Constraints\n\n- Keep scope narrow.\n", encoding="utf-8")

    bundle_with_optional = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )
    assert bundle_with_optional.optional_input_documents == (optional_constraints,)
    assert bundle_with_optional.expected_input_bundle == (
        *expected_required_inputs,
        optional_constraints,
    )
    assert bundle.expected_input_bundle == (
        *expected_required_inputs,
    )
    assert bundle.expected_output_documents == (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "implement"
        / "implementation-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "stage-result.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "questions.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "implement" / "answers.md",
    )


def test_prepare_stage_bundle_renders_stage_brief_with_relative_paths(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    content = bundle.stage_brief_markdown

    assert "# Stage" in content
    assert "\nplan\n" in content
    assert "# Expected input bundle" in content
    assert "`workitems/WI-001/stages/research/output/research-notes.md`" in content
    assert "# Expected output documents" in content
    assert "`workitems/WI-001/stages/plan/plan.md`" in content


def test_prepare_stage_bundle_renders_implementation_report_skeleton(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )
    content = bundle.stage_brief_markdown

    assert "## `implementation-report.md`" in content
    assert "# Implementation Report" in content
    assert "## Summary" in content
    assert "## Touched files" in content
    assert "## Verification" in content
    assert "## Risks" in content
    assert "## Follow-up" in content


def test_prepare_stage_bundle_renders_contract_skeletons_for_review_and_qa(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    review_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="review",
    )
    qa_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="qa",
    )

    assert "## `review-report.md`" in review_bundle.stage_brief_markdown
    assert "# Review Report" in review_bundle.stage_brief_markdown
    assert "## Verdict" in review_bundle.stage_brief_markdown
    assert "## Findings" in review_bundle.stage_brief_markdown
    assert "## Required follow-up" in review_bundle.stage_brief_markdown
    assert "## `qa-report.md`" in qa_bundle.stage_brief_markdown
    assert "# QA Report" in qa_bundle.stage_brief_markdown
    assert "## Verification summary" in qa_bundle.stage_brief_markdown
    assert "## Release recommendation" in qa_bundle.stage_brief_markdown
    assert "## Readiness" in qa_bundle.stage_brief_markdown


def test_prepare_stage_bundle_persists_project_set_context_when_declared(
    tmp_path: Path,
) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)
    workspace_root = tmp_path / ".aidd"
    project_set = resolve_project_set(
        repository_root=tmp_path,
        project_set=ProjectSetConfig(
            projects=(
                ProjectConfig(id="api", root=Path("services/api"), role="primary"),
                ProjectConfig(id="web", root=Path("apps/web")),
            )
        ),
    )

    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-PROJECT-SET",
        stage="plan",
        project_set=project_set,
    )

    context_path = (
        workspace_root / "workitems" / "WI-PROJECT-SET" / "context" / "project-set.md"
    )
    assert bundle.project_set_context_path == context_path
    assert context_path in bundle.expected_input_bundle
    assert "`workitems/WI-PROJECT-SET/context/project-set.md`" in (
        bundle.stage_brief_markdown
    )
    assert "- Project ids: `api`, `web`" in bundle.stage_brief_markdown
    assert "| `api` | `services/api` | `primary` |" in context_path.read_text(
        encoding="utf-8"
    )


def test_persist_execution_state_creates_attempt_and_sets_executing_status(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    assert execution_state.attempt_number == 1
    assert execution_state.attempt_path.name == "attempt-0001"
    assert run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ).exists()
    stage_metadata_payload = json.loads(
        execution_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == "executing"
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:00:00Z"


def test_persist_execution_state_uses_monotonic_attempt_numbers(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    first = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    second = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert first.attempt_number == 1
    assert second.attempt_number == 2


def test_prepare_adapter_invocation_initial_attempt_has_no_repair_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )

    assert invocation.attempt_number == 1
    assert invocation.repair_mode is False
    assert invocation.repair_context_markdown is None
    assert invocation.repair_brief_path is None
    assert invocation.input_bundle_path == (
        execution_state.attempt_path / ATTEMPT_INPUT_BUNDLE_FILENAME
    )
    assert invocation.input_bundle_path.exists()
    assert invocation.input_bundle_markdown == invocation.input_bundle_path.read_text(
        encoding="utf-8"
    )
    assert "# Input bundle" in invocation.input_bundle_markdown
    assert invocation.stage_brief_markdown == preparation_bundle.stage_brief_markdown


def test_prepare_adapter_invocation_initial_attempt_removes_stale_repair_brief(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    stale_repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    stale_repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    stale_repair_brief_path.write_text(
        "# Repair brief\n\nNo repair requested yet.\n",
        encoding="utf-8",
    )

    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )

    assert invocation.repair_mode is False
    assert invocation.repair_brief_path is None
    assert not stale_repair_brief_path.exists()


def test_prepare_adapter_invocation_repair_attempt_injects_repair_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    second_attempt = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    repair_brief_path.write_text(
        (
            "# Failed checks\n\n"
            "- `STRUCT-MISSING-REQUIRED-SECTION` `high` in "
            "`workitems/WI-001/stages/plan/plan.md`\n"
        ),
        encoding="utf-8",
    )

    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=second_attempt,
    )

    assert invocation.attempt_number == 2
    assert invocation.repair_mode is True
    assert invocation.repair_brief_path == repair_brief_path
    assert invocation.repair_context_markdown is not None
    assert "Mode: `repair`" in invocation.repair_context_markdown
    assert "Attempt number: `2`" in invocation.repair_context_markdown
    assert "repair-brief.md" in invocation.repair_context_markdown
    assert "STRUCT-MISSING-REQUIRED-SECTION" in invocation.repair_context_markdown
    assert invocation.input_bundle_path == (
        second_attempt.attempt_path / ATTEMPT_INPUT_BUNDLE_FILENAME
    )
    assert invocation.input_bundle_path.exists()
    repair_context_path = second_attempt.attempt_path / ATTEMPT_REPAIR_CONTEXT_FILENAME
    assert repair_context_path.exists()
    assert "STRUCT-MISSING-REQUIRED-SECTION" in repair_context_path.read_text(
        encoding="utf-8"
    )
    artifact_index = json.loads(
        (second_attempt.attempt_path / "artifact-index.json").read_text(encoding="utf-8")
    )
    assert artifact_index["documents"]["input_bundle"].endswith(
        "/attempts/attempt-0002/input-bundle.md"
    )
    assert artifact_index["documents"]["repair_context"].endswith(
        "/attempts/attempt-0002/repair-context.md"
    )


def test_restore_core_owned_repair_brief_reverts_runtime_overwrite(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    second_attempt = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    original_brief = (
        "# Failed checks\n\n"
        "- `SEM-PLACEHOLDER-CONTENT` `high` in `plan.md`: fix.\n\n"
        "## Required corrections\n\n- replace placeholder content\n\n"
        "## Relevant upstream docs\n\n- `context/intake.md`\n"
    )
    repair_brief_path.write_text(original_brief, encoding="utf-8")
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=second_attempt,
    )

    repair_brief_path.write_text("# Runtime overwrite\n\n- wrong owner\n", encoding="utf-8")
    restored_path = restore_core_owned_repair_brief(invocation_bundle=invocation)

    assert restored_path == repair_brief_path
    assert repair_brief_path.read_text(encoding="utf-8") == original_brief


def test_restore_core_owned_repair_brief_removes_model_created_initial_brief(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    repair_brief_path.write_text("# Runtime-created repair brief\n", encoding="utf-8")

    removed_path = restore_core_owned_repair_brief(
        invocation_bundle=invocation,
        workspace_root=workspace_root,
    )

    assert removed_path == repair_brief_path
    assert not repair_brief_path.exists()


def test_run_single_stage_orchestration_restores_repair_brief_when_adapter_raises(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    repair_brief_path = stage_root / "repair-brief.md"
    repair_brief_path.parent.mkdir(parents=True, exist_ok=True)
    original_brief = (
        "# Failed checks\n\n"
        "- `SEM-PLACEHOLDER-CONTENT` `high` in `plan.md`: fix.\n\n"
        "# Required corrections\n\n## Mandatory fixes\n\n- fix\n\n"
        "# Relevant upstream docs\n\n- `context/intake.md`\n"
    )
    repair_brief_path.write_text(original_brief, encoding="utf-8")

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        assert invocation.repair_brief_path is not None
        invocation.repair_brief_path.write_text(
            "# Runtime overwrite\n\n- adapter crashed after overwrite\n",
            encoding="utf-8",
        )
        raise RuntimeError("adapter crashed")

    with pytest.raises(RuntimeError, match="adapter crashed"):
        run_single_stage_orchestration(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            adapter_executor=_adapter_executor,
            repair_policy=RepairBudgetPolicy(default_max_repair_attempts=1),
        )

    assert repair_brief_path.read_text(encoding="utf-8") == original_brief
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is not None
    assert metadata.status == StageState.FAILED.value
    assert [change.status for change in metadata.status_history[-2:]] == [
        StageState.EXECUTING.value,
        StageState.FAILED.value,
    ]
    attempt_path = sorted(
        run_attempts_root(workspace_root, "WI-001", "run-001", "plan").glob("attempt-*")
    )[-1]
    exception_payload = json.loads(
        (attempt_path / "adapter-exception.json").read_text(encoding="utf-8")
    )
    assert exception_payload == {
        "schema_version": 1,
        "kind": "adapter-exception",
        "exception_type": "RuntimeError",
        "message": "adapter crashed",
        "work_item_id": "WI-001",
        "run_id": "run-001",
        "stage": "plan",
        "attempt_number": int(attempt_path.name.removeprefix("attempt-")),
    }
    artifact_index = json.loads(
        (attempt_path / "artifact-index.json").read_text(encoding="utf-8")
    )
    assert artifact_index["logs"]["adapter_exception"].endswith(
        "/adapter-exception.json"
    )
    assert not (attempt_path / "runtime-exit.json").exists()


def test_prepare_adapter_invocation_requires_existing_input_documents(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    with pytest.raises(FileNotFoundError, match="Input bundle preparation requires an existing"):
        prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=execution_state,
        )


def test_run_single_stage_preflight_blocks_missing_required_inputs_before_attempt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    def _unused_adapter_executor(
        _invocation: AdapterInvocationBundle,
        _execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        raise AssertionError("adapter must not run without a prepared input bundle")

    with pytest.raises(
        StageInputPreflightError,
        match=(
            "Stage input preflight failed: missing required input document: "
            "workitems/WI-001/stages/idea/output/idea-brief.md"
        ),
    ):
        run_single_stage_orchestration(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            adapter_executor=_unused_adapter_executor,
        )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is None
    assert not run_attempts_root(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    ).exists()
    assert not run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
    ).exists()


def test_run_single_stage_preflight_blocks_invalid_optional_inputs_before_attempt(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="implement",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="implement",
    )
    _materialize_expected_inputs(preparation_bundle.required_input_documents)
    optional_constraints = (
        workspace_root / "workitems" / "WI-001" / "context" / "constraints.md"
    )
    optional_constraints.parent.mkdir(parents=True, exist_ok=True)
    optional_constraints.write_bytes(b"\xff")

    def _unused_adapter_executor(
        _invocation: AdapterInvocationBundle,
        _execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        raise AssertionError("adapter must not run without valid stage inputs")

    with pytest.raises(
        StageInputPreflightError,
        match=(
            "Stage input preflight failed: optional input document is not UTF-8 text: "
            "workitems/WI-001/context/constraints.md"
        ),
    ):
        run_single_stage_orchestration(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="implement",
            adapter_executor=_unused_adapter_executor,
        )

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
    )
    assert metadata is None
    assert not run_attempts_root(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="implement",
    ).exists()


def test_discover_stage_markdown_outputs_returns_discovered_and_missing_documents(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    for output_path in preparation_bundle.expected_output_documents[:2]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("# Output\n\nPresent.\n", encoding="utf-8")

    invocation_with_non_markdown_output = replace(
        invocation,
        expected_output_documents=(
            *invocation.expected_output_documents,
            execution_state.attempt_path / "runtime.log",
        ),
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation_with_non_markdown_output,
    )

    assert isinstance(discovery, StageOutputDiscovery)
    assert discovery.stage == "plan"
    assert discovery.attempt_number == 1
    assert all(path.suffix.lower() == ".md" for path in discovery.expected_markdown_documents)
    assert execution_state.attempt_path / "runtime.log" not in discovery.expected_markdown_documents
    assert discovery.discovered_markdown_documents == (
        preparation_bundle.expected_output_documents[:2]
    )
    assert discovery.missing_markdown_documents == preparation_bundle.expected_output_documents[2:]


def test_discover_stage_markdown_outputs_promotes_misplaced_output_documents(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="claude-code",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    stage_root = preparation_bundle.expected_output_documents[0].parent
    misplaced_output_root = stage_root / "output"
    misplaced_output_root.mkdir(parents=True)
    valid_documents = _valid_plan_output_documents()
    for expected_output in preparation_bundle.expected_output_documents:
        (misplaced_output_root / expected_output.name).write_text(
            valid_documents[expected_output.name],
            encoding="utf-8",
        )
    (stage_root / "stage-result.md").write_text(
        "# Stage result\n\nStage not run yet.\n",
        encoding="utf-8",
    )
    (stage_root / "validator-report.md").write_text(
        "# Validator report\n\nNo validator output yet.\n",
        encoding="utf-8",
    )

    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    structural_validation = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert discovery.discovered_markdown_documents == preparation_bundle.expected_output_documents
    assert discovery.missing_markdown_documents == ()
    assert tuple(
        promotion.destination_path for promotion in discovery.promoted_misplaced_documents
    ) == preparation_bundle.expected_output_documents
    assert (stage_root / "plan.md").read_text(encoding="utf-8") == valid_documents["plan.md"]
    assert (stage_root / "stage-result.md").read_text(encoding="utf-8") == (
        valid_documents["stage-result.md"]
    )
    assert structural_validation.findings == ()
    validator_report_text = structural_validation.validator_report_path.read_text(
        encoding="utf-8"
    )
    assert "- Verdict: `pass`" in validator_report_text
    assert "`STRUCT-OUTPUT-PROMOTED` (`low`)" in validator_report_text
    assert "workitems/WI-001/stages/plan/output/plan.md" in validator_report_text
    assert "workitems/WI-001/stages/plan/plan.md" in validator_report_text


def test_discover_stage_markdown_outputs_rejects_mismatched_execution_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )

    with pytest.raises(ValueError, match="does not match adapter invocation stage"):
        discover_stage_markdown_outputs(
            execution_state=StageExecutionState(
                stage="qa",
                work_item=execution_state.work_item,
                run_id=execution_state.run_id,
                attempt_number=execution_state.attempt_number,
                attempt_path=execution_state.attempt_path,
                stage_metadata_path=execution_state.stage_metadata_path,
            ),
            invocation_bundle=invocation,
        )


def test_publish_stage_outputs_makes_downstream_output_references_satisfiable(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-idea",
        runtime_id="generic-cli",
        stage_target="idea",
        config_snapshot={"mode": "test"},
    )
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-research",
        runtime_id="generic-cli",
        stage_target="research",
        config_snapshot={"mode": "test"},
    )

    idea_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
    )
    _materialize_expected_inputs(idea_bundle.expected_input_bundle)
    _materialize_expected_outputs(idea_bundle.expected_output_documents)

    research_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="research",
    )
    for input_path in research_bundle.expected_input_bundle:
        if "/context/" not in input_path.as_posix():
            continue
        input_path.parent.mkdir(parents=True, exist_ok=True)
        input_path.write_text("# Repository state\n\nClean baseline.\n", encoding="utf-8")

    research_execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-research",
        stage="research",
    )
    with pytest.raises(
        FileNotFoundError,
        match="workitems/WI-001/stages/idea/output/idea-brief.md",
    ):
        prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=research_bundle,
            execution_state=research_execution_state,
        )

    publish_stage_outputs_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-idea",
        stage="idea",
    )

    research_invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=research_bundle,
        execution_state=research_execution_state,
    )
    assert research_invocation.input_bundle_path.exists()
    assert "workitems/WI-001/stages/idea/output/idea-brief.md" in (
        research_invocation.input_bundle_markdown
    )
    assert (
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "output" / "idea-brief.md"
    ).exists()


def test_publish_stage_outputs_restores_previous_publication_on_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="idea",
    )
    _materialize_expected_outputs(bundle.expected_output_documents)
    publish_stage_outputs_after_validation_pass(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-idea",
        stage="idea",
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "idea"
    published_brief = stage_root / "output" / "idea-brief.md"
    previous = published_brief.read_text(encoding="utf-8")
    (stage_root / "idea-brief.md").write_text("# Idea Brief\n\nreplacement\n", encoding="utf-8")
    original_replace = Path.replace

    def _replace_with_failure(source: Path, target: Path) -> Path:
        if source.name.startswith(".output.staging-") and target.name == "output":
            raise OSError("injected publication failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", _replace_with_failure)

    with pytest.raises(OSError, match="injected publication failure"):
        publish_stage_outputs_after_validation_pass(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-idea",
            stage="idea",
        )

    assert published_brief.read_text(encoding="utf-8") == previous
    assert not tuple(stage_root.glob(".output.staging-*"))
    assert not tuple(stage_root.glob(".output.backup-*"))


def test_run_single_stage_orchestration_executes_generic_cli_happy_path(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Status",
        "# Status",
    )
    command = _write_runtime_writer_command(
        tmp_path=tmp_path,
        documents=runtime_documents,
        exit_code=0,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        context = GenericCliStageContext(
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
        )
        spec = build_subprocess_spec(
            configured_command=command,
            workspace_root=workspace_root,
            context=context,
            base_env=dict(os.environ),
            repository_root=Path.cwd(),
        )
        run_result = run_subprocess_with_streaming(spec=spec)
        persist_attempt_runtime_artifacts(
            attempt_path=execution_state.attempt_path,
            run_result=run_result,
        )
        return AdapterExecutionOutcome(
            succeeded=run_result.exit_classification is GenericCliExitClassification.SUCCESS,
            details=run_result.exit_classification.value,
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert isinstance(orchestration, StageOrchestrationResult)
    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.transition.next_state is StageState.SUCCEEDED
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.PASS
    assert (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    ).exists()
    metadata_payload = json.loads(
        orchestration.transition.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert metadata_payload["status"] == StageState.SUCCEEDED.value


def test_run_single_stage_orchestration_includes_answers_after_blocked_resume(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert unblock_state.unblocked is True
    assert unblock_state.next_state is StageState.PREPARING
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Status",
        "# Status",
    )
    seen_input_bundle: list[str] = []

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        seen_input_bundle.append(invocation.input_bundle_markdown)
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert seen_input_bundle
    assert "`workitems/WI-001/stages/plan/questions.md`" in seen_input_bundle[0]
    assert "`workitems/WI-001/stages/plan/answers.md`" in seen_input_bundle[0]
    assert "Release owner approval is recorded." in seen_input_bundle[0]


def test_run_single_stage_orchestration_blocks_when_runtime_answers_own_question(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "## Questions\n\n"
        "- Q1 [blocking] Which rollout owner should approve this scope?\n"
    )
    runtime_documents["answers.md"] = (
        "# Answers\n\n"
        "## Answers\n\n"
        "- Q1 [resolved] The runtime picked the engineering lead.\n"
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.WAIT
    assert orchestration.transition.next_state is StageState.BLOCKED
    assert orchestration.interview_routing is not None
    assert orchestration.interview_routing.unresolved_blocking_question_ids == ("Q1",)
    answers_text = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "answers.md"
    ).read_text(encoding="utf-8")
    assert "runtime picked" not in answers_text
    assert "- none" in answers_text


def test_run_single_stage_orchestration_normalizes_runtime_malformed_answers_for_new_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "## Questions\n\n"
        "- Q1 [blocking] Which rollout owner should approve this scope?\n"
    )
    runtime_documents["answers.md"] = "# Answers\n\n- No answers have been provided yet.\n"

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        del invocation, execution_state
        stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.WAIT
    assert orchestration.transition.next_state is StageState.BLOCKED
    assert orchestration.interview_routing is not None
    assert orchestration.interview_routing.unresolved_blocking_question_ids == ("Q1",)
    assert orchestration.validation_result is not None
    assert all(
        finding.code != "INTERVIEW-MALFORMED-DOCUMENT"
        for finding in orchestration.validation_result.findings
    )
    answers_text = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "answers.md"
    ).read_text(encoding="utf-8")
    assert "No answers have been provided yet" not in answers_text
    assert "- none" in answers_text


@pytest.mark.parametrize("runtime_answer_action", ("rewrite", "delete"))
def test_run_single_stage_orchestration_preserves_operator_answers_after_runtime_attempt(
    tmp_path: Path,
    runtime_answer_action: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    operator_answers = (
        "# Answers\n\n"
        "## Answers\n\n"
        "- Q1 [resolved] Release owner approval is recorded.\n"
    )
    (stage_root / "answers.md").write_text(operator_answers, encoding="utf-8")

    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "## Questions\n\n"
        "- Q1 [blocking] Which rollout owner should approve this scope?\n"
    )
    runtime_documents["answers.md"] = (
        "# Answers\n\n"
        "## Answers\n\n"
        "- Q1 [resolved] The runtime rewrote the operator answer.\n"
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        del invocation, execution_state
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            if name == "answers.md" and runtime_answer_action == "delete":
                continue
            (stage_root / name).write_text(content, encoding="utf-8")
        if runtime_answer_action == "delete":
            (stage_root / "answers.md").unlink(missing_ok=True)
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.transition.next_state is StageState.SUCCEEDED
    answers_text = (stage_root / "answers.md").read_text(encoding="utf-8")
    assert answers_text == operator_answers


def test_run_single_stage_orchestration_preserves_repair_context_after_blocked_repair_resume(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root / "validator-report.md"
    validator_report_path.write_text(
        "# Validator Report\n\n"
        "## Result\n\n"
        "- Verdict: `repair`\n",
        encoding="utf-8",
    )
    repair_brief_path = stage_root / "repair-brief.md"
    repair_brief_text = (
        "# Failed checks\n\n"
        "- `STRUCT-MISSING-REQUIRED-SECTION` `high` in "
        "`workitems/WI-001/stages/plan/plan.md`\n"
    )
    repair_brief_path.write_text(repair_brief_text, encoding="utf-8")
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
        trigger="initial",
        outcome="failed validation",
        stage_status=StageState.REPAIR_NEEDED.value,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=2,
        trigger="repair",
        outcome="blocked by questions",
        stage_status=StageState.BLOCKED.value,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )
    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert unblock_state.unblocked is True
    seen_invocations: list[AdapterInvocationBundle] = []

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        seen_invocations.append(invocation)
        assert execution_state.attempt_number == 3
        runtime_documents = _valid_plan_output_documents()
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert seen_invocations
    invocation = seen_invocations[0]
    assert invocation.repair_mode is True
    assert invocation.repair_brief_path == repair_brief_path
    assert invocation.repair_brief_markdown == repair_brief_text
    assert invocation.repair_context_markdown is not None
    assert "Mode: `repair`" in invocation.repair_context_markdown
    assert "Attempt number: `3`" in invocation.repair_context_markdown
    assert repair_brief_path.exists()
    validator_report_text = (stage_root / "validator-report.md").read_text(encoding="utf-8")
    assert "CROSS-REPAIR-MENTION-WITHOUT-BRIEF" not in validator_report_text


def test_run_single_stage_orchestration_removes_model_authored_initial_repair_brief(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Status",
        "# Status",
    )
    runtime_documents["repair-brief.md"] = (
        "# Runtime-authored repair summary\n\n"
        "This document must not become validation input on an initial attempt.\n"
    )
    command = _write_runtime_writer_command(
        tmp_path=tmp_path,
        documents=runtime_documents,
        exit_code=0,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        context = GenericCliStageContext(
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
        )
        spec = build_subprocess_spec(
            configured_command=command,
            workspace_root=workspace_root,
            context=context,
            base_env=dict(os.environ),
            repository_root=Path.cwd(),
        )
        run_result = run_subprocess_with_streaming(spec=spec)
        persist_attempt_runtime_artifacts(
            attempt_path=execution_state.attempt_path,
            run_result=run_result,
        )
        return AdapterExecutionOutcome(
            succeeded=run_result.exit_classification is GenericCliExitClassification.SUCCESS,
            details=run_result.exit_classification.value,
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    repair_brief_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "repair-brief.md"
    )
    validator_report_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    )
    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.PASS
    assert not repair_brief_path.exists()
    assert "repair-brief.md" not in validator_report_path.read_text(encoding="utf-8")


def test_run_single_stage_orchestration_preserves_historical_repair_brief_trace_on_rerun(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report_path = stage_root / "validator-report.md"
    validator_report_path.write_text("# Validator Report\n", encoding="utf-8")
    repair_brief_path = stage_root / "repair-brief.md"
    repair_brief_path.write_text(
        "# Failed checks\n\n- `SEM-PLACEHOLDER-CONTENT` `high`: fix plan evidence.\n",
        encoding="utf-8",
    )

    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=1,
        trigger="initial",
        outcome="failed validation",
        stage_status=StageState.REPAIR_NEEDED.value,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.SUCCEEDED.value,
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        attempt_number=2,
        trigger="repair",
        outcome="succeeded",
        stage_status=StageState.SUCCEEDED.value,
        validator_report_path=validator_report_path,
        repair_brief_path=repair_brief_path,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        assert invocation.repair_mode is False
        assert invocation.repair_brief_path is None
        assert execution_state.attempt_number == 3
        runtime_documents = _valid_plan_output_documents()
        assert "repair-brief.md" not in runtime_documents["stage-result.md"]
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    validator_report_text = validator_report_path.read_text(encoding="utf-8")
    stage_result_text = (stage_root / "stage-result.md").read_text(encoding="utf-8")
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.PASS
    assert repair_brief_path.exists()
    assert "CROSS-REPAIR-MENTION-WITHOUT-BRIEF" not in validator_report_text
    assert "CROSS-REPAIR-BRIEF-NOT-REFERENCED" not in validator_report_text
    assert "`workitems/WI-001/stages/plan/repair-brief.md`" in stage_result_text
    assert metadata is not None
    assert [(entry.attempt_number, entry.trigger) for entry in metadata.repair_history] == [
        (1, "initial"),
        (2, "repair"),
        (3, "initial"),
    ]


def test_run_single_stage_orchestration_repairs_malformed_questions_document(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Status",
        "# Status",
    )
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "## Q1 [non-blocking]\n\n"
        "Which behavior should header-only imports preserve?\n\n"
        "Candidate outcomes:\n\n"
        "- (a) create an empty table.\n"
        "- (b) create no table and exit successfully.\n"
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_root = (
            workspace_root
            / "workitems"
            / invocation.work_item
            / "stages"
            / invocation.stage
        )
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.REPAIR
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.REPAIR
    assert orchestration.validation_result is not None
    assert any(
        finding.code == "INTERVIEW-MALFORMED-DOCUMENT"
        for finding in orchestration.validation_result.findings
    )
    validator_report_text = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    ).read_text(encoding="utf-8")
    assert "`INTERVIEW-MALFORMED-DOCUMENT`" in validator_report_text
    assert "Invalid question entry at line 9" in validator_report_text
    assert "`- <QID> [resolved|partial|deferred] <text>` for answers" in validator_report_text


def test_run_single_stage_orchestration_routes_task_diff_findings_into_repair(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        del execution_state
        stage_root = (
            workspace_root
            / "workitems"
            / invocation.work_item
            / "stages"
            / invocation.stage
        )
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
        validation_finding_provider=lambda execution_state, discovery: (
            ValidationFinding(
                code="SEM-TASK-DIFF-MISMATCH",
                message=(
                    f"Injected task diff mismatch for attempt {execution_state.attempt_number}; "
                    f"discovered {len(discovery.discovered_markdown_documents)} documents."
                ),
            ),
        ),
    )

    assert orchestration.transition.action is PostValidationAction.REPAIR
    assert orchestration.validation_result is not None
    assert any(
        finding.code == "SEM-TASK-DIFF-MISMATCH"
        for finding in orchestration.validation_result.findings
    )


def test_run_single_stage_orchestration_repairs_malformed_answers_document(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "## Questions\n\n"
        "- Q1 [non-blocking] Confirm compatibility-note placement.\n"
    )
    runtime_documents["answers.md"] = (
        "# Answers\n\n"
        "## Answers\n\n"
        "- Q1 [resolved]: Put compatibility notes in router documentation.\n"
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_root = (
            workspace_root
            / "workitems"
            / invocation.work_item
            / "stages"
            / invocation.stage
        )
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.REPAIR
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.REPAIR
    assert orchestration.validation_result is not None
    assert any(
        finding.code == "INTERVIEW-MALFORMED-DOCUMENT"
        for finding in orchestration.validation_result.findings
    )
    validator_report_text = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    ).read_text(encoding="utf-8")
    assert "`INTERVIEW-MALFORMED-DOCUMENT`" in validator_report_text
    assert "Invalid answer entry at line 5" in validator_report_text
    assert "`- <QID> [resolved|partial|deferred] <text>`" in validator_report_text


def test_run_single_stage_orchestration_repairs_malformed_questions_with_blockers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["questions.md"] = (
        "# Questions\n\n"
        "- Q1 [blocking] What input form should the CLI accept?\n"
        "  - Should it accept inline code, a Python file, or both?\n"
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_root = (
            workspace_root
            / "workitems"
            / invocation.work_item
            / "stages"
            / invocation.stage
        )
        stage_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.REPAIR
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.REPAIR
    assert orchestration.validation_result is not None
    finding_codes = {finding.code for finding in orchestration.validation_result.findings}
    assert "INTERVIEW-MALFORMED-DOCUMENT" in finding_codes
    assert "CROSS-BLOCKING-UNANSWERED" in finding_codes


def test_run_single_stage_orchestration_allows_final_repair_attempt_to_pass(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n- `SEM-PLACEHOLDER-CONTENT` `high` in `plan.md`: fix.\n\n"
        "# Required corrections\n\n## Mandatory fixes\n\n- fix\n\n"
        "# Relevant upstream docs\n\n- `context/intake.md`\n\n"
        "Repair attempt context: attempt `2` of max `2`; remaining retries after this "
        "attempt: `0`.\n"
        "Rerun allowed after this attempt: `no`.\n"
        "Repair budget status: `repair-budget-final-attempt`.\n",
        encoding="utf-8",
    )
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "Ready.\n",
        "Ready after resolving findings from `repair-brief.md`.\n",
    )
    command = _write_runtime_writer_command(
        tmp_path=tmp_path,
        documents=runtime_documents,
        exit_code=0,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        context = GenericCliStageContext(
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
        )
        spec = build_subprocess_spec(
            configured_command=command,
            workspace_root=workspace_root,
            context=context,
            base_env=dict(os.environ),
            repository_root=Path.cwd(),
        )
        run_result = run_subprocess_with_streaming(spec=spec)
        persist_attempt_runtime_artifacts(
            attempt_path=execution_state.attempt_path,
            run_result=run_result,
        )
        return AdapterExecutionOutcome(
            succeeded=run_result.exit_classification is GenericCliExitClassification.SUCCESS,
            details=run_result.exit_classification.value,
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=1),
    )

    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.transition.next_state is StageState.SUCCEEDED
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.PASS
    assert orchestration.validation_transition.budget_exhausted is False
    validator_report_text = (stage_root / "validator-report.md").read_text(encoding="utf-8")
    assert "CROSS-REPAIR-BUDGET-EXHAUSTED" not in validator_report_text
    assert (stage_root / "output" / "stage-result.md").exists()


def test_run_single_stage_orchestration_normalizes_missing_repair_brief_trace(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n- `SEM-PLACEHOLDER-CONTENT` `high` in `plan.md`: fix.\n\n"
        "# Required corrections\n\n## Mandatory fixes\n\n- fix\n\n"
        "# Relevant upstream docs\n\n- `context/intake.md`\n\n"
        "Repair attempt context: attempt `2` of max `3`; remaining retries after this "
        "attempt: `1`.\n"
        "Rerun allowed after this attempt: `yes`.\n"
        "Repair budget status: `repair-budget-available`.\n",
        encoding="utf-8",
    )
    runtime_documents = _valid_plan_output_documents()
    assert "repair-brief.md" not in runtime_documents["stage-result.md"]

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        stage_documents_root = (
            workspace_root
            / "workitems"
            / invocation.work_item
            / "stages"
            / invocation.stage
        )
        stage_documents_root.mkdir(parents=True, exist_ok=True)
        for name, content in runtime_documents.items():
            (stage_documents_root / name).write_text(content, encoding="utf-8")
        return AdapterExecutionOutcome(succeeded=True, details="success")

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    stage_result_text = (stage_root / "stage-result.md").read_text(encoding="utf-8")
    validator_report_text = (stage_root / "validator-report.md").read_text(encoding="utf-8")
    assert orchestration.transition.action is PostValidationAction.ADVANCE
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.resolved_verdict is ValidationVerdict.PASS
    assert "`workitems/WI-001/stages/plan/repair-brief.md`" in stage_result_text
    assert "CROSS-REPAIR-BRIEF-NOT-REFERENCED" not in validator_report_text


def test_run_single_stage_orchestration_forces_failed_status_on_exhausted_repair_budget(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "repair-brief.md").write_text(
        "# Failed checks\n\n- `SEM-PLACEHOLDER-CONTENT` `high` in `plan.md`: fix.\n\n"
        "# Required corrections\n\n## Mandatory fixes\n\n- fix\n\n"
        "# Relevant upstream docs\n\n- `context/intake.md`\n\n"
        "Repair attempt context: attempt `2` of max `2`; remaining retries after this "
        "attempt: `0`.\n"
        "Rerun allowed after this attempt: `no`.\n"
        "Repair budget status: `repair-budget-exhausted`.\n",
        encoding="utf-8",
    )
    runtime_documents = _valid_plan_output_documents()
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Status",
        "# Status",
    )
    runtime_documents["stage-result.md"] = runtime_documents["stage-result.md"].replace(
        "## Validation summary\n\n- structural: pass\n\n",
        "## Validation summary\n\n- Validator verdict: pass\n- structural: pass\n\n",
    )
    command = _write_runtime_writer_command(
        tmp_path=tmp_path,
        documents=runtime_documents,
        exit_code=0,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        context = GenericCliStageContext(
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
        )
        spec = build_subprocess_spec(
            configured_command=command,
            workspace_root=workspace_root,
            context=context,
            base_env=dict(os.environ),
            repository_root=Path.cwd(),
        )
        run_result = run_subprocess_with_streaming(spec=spec)
        persist_attempt_runtime_artifacts(
            attempt_path=execution_state.attempt_path,
            run_result=run_result,
        )
        return AdapterExecutionOutcome(
            succeeded=run_result.exit_classification is GenericCliExitClassification.SUCCESS,
            details=run_result.exit_classification.value,
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=1),
    )

    stage_result_text = (stage_root / "stage-result.md").read_text(encoding="utf-8")
    validator_report_text = (stage_root / "validator-report.md").read_text(encoding="utf-8")
    assert orchestration.transition.action is PostValidationAction.STOP
    assert orchestration.transition.next_state is StageState.FAILED
    assert orchestration.validation_transition is not None
    assert orchestration.validation_transition.budget_exhausted is True
    assert re.search(
        r"^#{1,6}\s+Status\s*\n+.*failed",
        stage_result_text,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    assert len(re.findall(r"^#{1,6}\s+Status\s*$", stage_result_text, re.MULTILINE)) == 1
    assert "Repair budget status: `repair-budget-exhausted`" in stage_result_text
    assert "Canonical AIDD validation found open findings" in stage_result_text
    assert "Validator verdict: `pass`" not in stage_result_text
    assert "Validator verdict: pass" not in stage_result_text
    assert "Validator verdict: fail" in stage_result_text
    assert "CROSS-REPAIR-BUDGET-EXHAUSTED" in validator_report_text
    assert not (stage_root / "output" / "stage-result.md").exists()


def test_run_single_stage_orchestration_stops_on_adapter_failure(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    command = _write_runtime_writer_command(
        tmp_path=tmp_path,
        documents={},
        exit_code=3,
    )

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        context = GenericCliStageContext(
            stage=invocation.stage,
            work_item=invocation.work_item,
            run_id=invocation.run_id,
            prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
        )
        spec = build_subprocess_spec(
            configured_command=command,
            workspace_root=workspace_root,
            context=context,
            base_env=dict(os.environ),
            repository_root=Path.cwd(),
        )
        run_result = run_subprocess_with_streaming(spec=spec)
        persist_attempt_runtime_artifacts(
            attempt_path=execution_state.attempt_path,
            run_result=run_result,
        )
        return AdapterExecutionOutcome(
            succeeded=run_result.exit_classification is GenericCliExitClassification.SUCCESS,
            details=run_result.exit_classification.value,
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    assert orchestration.transition.action is PostValidationAction.STOP
    assert orchestration.transition.next_state is StageState.FAILED
    assert orchestration.validation_result is None
    assert orchestration.validation_transition is None


def test_run_single_stage_orchestration_blocks_before_validation_for_operator_request(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)

    def _adapter_executor(
        invocation: AdapterInvocationBundle,
        execution_state: StageExecutionState,
    ) -> AdapterExecutionOutcome:
        assert invocation.stage == "plan"
        return AdapterExecutionOutcome(
            status=AdapterExecutionStatus.BLOCKED_FOR_OPERATOR,
            details="blocked_for_operator: runtime permission decision required",
            operator_requests_path=(
                execution_state.attempt_path / "operator-requests.jsonl"
            ),
            pending_operator_request_ids=("opr-test",),
        )

    orchestration = run_single_stage_orchestration(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        adapter_executor=_adapter_executor,
    )

    metadata_payload = json.loads(
        run_stage_metadata_path(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
        ).read_text(encoding="utf-8")
    )
    assert orchestration.transition.action is PostValidationAction.WAIT
    assert orchestration.transition.next_state is StageState.BLOCKED
    assert orchestration.validation_result is None
    assert orchestration.validation_transition is None
    assert orchestration.adapter_outcome.blocked_for_operator is True
    assert metadata_payload["status"] == StageState.BLOCKED.value


def test_run_structural_validation_after_output_discovery_writes_report_path(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    plan_output_path = preparation_bundle.expected_output_documents[0]
    plan_output_path.parent.mkdir(parents=True, exist_ok=True)
    plan_output_path.write_text("# Plan\n\nPartial output.\n", encoding="utf-8")
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )

    structural_validation = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert isinstance(structural_validation, StageStructuralValidationResult)
    assert structural_validation.stage == "plan"
    assert structural_validation.run_id == "run-001"
    assert structural_validation.attempt_number == 1
    assert structural_validation.validator_report_path == (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "validator-report.md"
    )
    assert structural_validation.validator_report_path.exists()
    assert any(
        finding.code == "STRUCT-MISSING-REQUIRED-DOCUMENT"
        for finding in structural_validation.findings
    )
    report_text = structural_validation.validator_report_path.read_text(encoding="utf-8")
    assert "`STRUCT-MISSING-REQUIRED-DOCUMENT`" in report_text


def test_validation_collects_semantic_findings_with_independent_structural_defects(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    plan_output_path = preparation_bundle.expected_output_documents[0]
    plan_output_path.parent.mkdir(parents=True, exist_ok=True)
    plan_output_path.write_text(
        (
            "# Plan\n\n"
            "## Goals\n\n- Deliver a reviewable execution plan.\n\n"
            "## Out of scope\n\n- Runtime migration is excluded.\n\n"
            "## Milestones\n\n- M1: Draft and validate plan.\n\n"
            "## Implementation strategy\n\n- Use staged, document-first increments.\n\n"
            "## Risks\n\n- R1: Missing constraints.\n\n"
            "## Dependencies\n\nResearch artifacts from prior stage.\n\n"
            "## Verification approach\n\n- Run structural and semantic checks.\n\n"
            "## Verification notes\n\n- Verify the plan with targeted tests.\n"
        ),
        encoding="utf-8",
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )

    structural_validation = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    finding_codes = [finding.code for finding in structural_validation.findings]
    assert "STRUCT-MISSING-REQUIRED-DOCUMENT" in finding_codes
    assert "SEM-INCOMPLETE-SECTION" in finding_codes
    report_text = structural_validation.validator_report_path.read_text(encoding="utf-8")
    assert "`STRUCT-MISSING-REQUIRED-DOCUMENT`" in report_text
    assert "`SEM-INCOMPLETE-SECTION`" in report_text


def test_route_stage_questions_to_interview_detects_unresolved_blocking_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        (
            "# Questions\n\n"
            "## Questions\n\n"
            "- `Q1` `[blocking]` Confirm scope.\n"
            "- `Q2` `[non-blocking]` Optional context.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "## Answers\n\n"
            "- `Q2` `[resolved]` Added optional context.\n"
        ),
        encoding="utf-8",
    )

    routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert isinstance(routing, StageInterviewRouting)
    assert routing.requires_interview is True
    assert routing.unresolved_blocking_question_ids == ("Q1",)
    assert routing.questions_path == stage_root / "questions.md"
    assert routing.answers_path == stage_root / "answers.md"


def test_route_stage_questions_to_interview_skips_when_blocking_questions_resolved(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preparation_bundle.expected_input_bundle)
    execution_state = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    invocation = prepare_adapter_invocation(
        workspace_root=workspace_root,
        preparation_bundle=preparation_bundle,
        execution_state=execution_state,
    )
    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        (
            "# Questions\n\n"
            "## Questions\n\n"
            "- `Q1` `[blocking]` Confirm scope.\n"
        ),
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        (
            "# Answers\n\n"
            "## Answers\n\n"
            "- `Q1` `[resolved]` Scope confirmed.\n"
        ),
        encoding="utf-8",
    )

    routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )

    assert routing.requires_interview is False
    assert routing.unresolved_blocking_question_ids == ()


def test_prepare_adapter_invocation_repair_attempt_requires_repair_brief(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.REPAIR_NEEDED.value,
    )
    second_attempt = persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    with pytest.raises(FileNotFoundError, match="Repair rerun requires an existing repair brief"):
        prepare_adapter_invocation(
            workspace_root=workspace_root,
            preparation_bundle=preparation_bundle,
            execution_state=second_attempt,
        )


def test_derive_validation_verdict_maps_combined_validation_outcomes() -> None:
    assert derive_validation_verdict(findings=()) is ValidationVerdict.PASS
    assert derive_validation_verdict(
        findings=(
            ValidationFinding(
                code="SEM-INCOMPLETE-SECTION",
                message="Semantic section is incomplete.",
            ),
        )
    ) is ValidationVerdict.REPAIR
    assert derive_validation_verdict(
        findings=(
            ValidationFinding(
                code="CROSS-BLOCKING-UNANSWERED",
                message="Blocking question is unresolved.",
            ),
        )
    ) is ValidationVerdict.BLOCKED
    assert derive_validation_verdict(
        findings=(
            ValidationFinding(
                code="CROSS-BLOCKING-UNANSWERED",
                message="Blocking question is unresolved.",
            ),
            ValidationFinding(
                code="INTERVIEW-MALFORMED-DOCUMENT",
                message="Question document contains invalid bullet continuation.",
            ),
        )
    ) is ValidationVerdict.REPAIR

    interview_routing = StageInterviewRouting(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        attempt_number=1,
        questions_path=Path("/tmp/questions.md"),
        answers_path=Path("/tmp/answers.md"),
        unresolved_blocking_question_ids=("Q1",),
        requires_interview=True,
    )
    assert derive_validation_verdict(
        findings=(),
        interview_routing=interview_routing,
    ) is ValidationVerdict.BLOCKED


@pytest.mark.parametrize(
    ("verdict", "expected_state"),
    (
        (ValidationVerdict.PASS, StageState.SUCCEEDED),
        (ValidationVerdict.REPAIR, StageState.REPAIR_NEEDED),
        (ValidationVerdict.BLOCKED, StageState.BLOCKED),
        (ValidationVerdict.FAIL, StageState.FAILED),
    ),
)
def test_persist_validation_state_persists_verdict_transition(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
        changed_at_utc=datetime(2026, 4, 22, 10, 5, tzinfo=UTC),
    )

    assert validation_state.verdict is verdict
    assert validation_state.next_state == expected_state
    stage_metadata_payload = json.loads(
        validation_state.stage_metadata_path.read_text(encoding="utf-8")
    )
    assert stage_metadata_payload["status"] == expected_state.value
    assert stage_metadata_payload["updated_at_utc"] == "2026-04-22T10:05:00Z"
    assert [entry["status"] for entry in stage_metadata_payload["status_history"]] == [
        "validating",
        expected_state.value,
    ]


def test_persist_validation_state_rejects_illegal_transition(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    with pytest.raises(ValueError, match="Illegal stage transition"):
        persist_validation_state(
            workspace_root=workspace_root,
            work_item="WI-001",
            run_id="run-001",
            stage="plan",
            verdict=ValidationVerdict.PASS,
            from_state=StageState.PENDING,
        )

    metadata_path = run_stage_metadata_path(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert not metadata_path.exists()


def test_persist_validation_state_with_repair_budget_keeps_repair_when_budget_remains(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )

    transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert isinstance(transition, RepairBudgetValidationTransition)
    assert transition.requested_verdict is ValidationVerdict.REPAIR
    assert transition.resolved_verdict is ValidationVerdict.REPAIR
    assert transition.budget_exhausted is False
    assert transition.remaining_repair_attempts == 2
    assert transition.validation_state.next_state is StageState.REPAIR_NEEDED


def test_persist_validation_state_with_repair_budget_forces_fail_when_exhausted(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )

    transition = persist_validation_state_with_repair_budget(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.REPAIR,
        repair_policy=RepairBudgetPolicy(default_max_repair_attempts=2),
    )

    assert transition.requested_verdict is ValidationVerdict.REPAIR
    assert transition.resolved_verdict is ValidationVerdict.FAIL
    assert transition.budget_exhausted is True
    assert transition.remaining_repair_attempts == 0
    assert transition.validation_state.next_state is StageState.FAILED


@pytest.mark.parametrize(
    ("verdict", "expected_state", "expected_action", "expected_terminal"),
    (
        (
            ValidationVerdict.PASS,
            StageState.SUCCEEDED,
            PostValidationAction.ADVANCE,
            True,
        ),
        (
            ValidationVerdict.REPAIR,
            StageState.REPAIR_NEEDED,
            PostValidationAction.REPAIR,
            False,
        ),
        (
            ValidationVerdict.BLOCKED,
            StageState.BLOCKED,
            PostValidationAction.WAIT,
            False,
        ),
        (
            ValidationVerdict.FAIL,
            StageState.FAILED,
            PostValidationAction.STOP,
            True,
        ),
    ),
)
def test_decide_post_validation_transition_maps_supported_outcomes(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
    expected_action: PostValidationAction,
    expected_terminal: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
    )

    transition = decide_post_validation_transition(validation_state)

    assert transition.next_state == expected_state
    assert transition.action == expected_action
    assert transition.is_terminal is expected_terminal
    assert transition.stage_metadata_path == validation_state.stage_metadata_path


def test_decide_post_validation_transition_rejects_unsupported_state() -> None:
    with pytest.raises(ValueError, match="Unsupported post-validation state"):
        decide_post_validation_transition(
            StageValidationState(
                stage="plan",
                work_item="WI-001",
                run_id="run-001",
                verdict=ValidationVerdict.PASS,
                next_state=StageState.VALIDATING,
                stage_metadata_path=Path("/tmp/stage-metadata.json"),
            )
        )


@pytest.mark.parametrize(
    ("verdict", "expected_state", "expected_action", "expected_terminal"),
    (
        (
            ValidationVerdict.PASS,
            StageState.SUCCEEDED,
            PostValidationAction.ADVANCE,
            True,
        ),
        (
            ValidationVerdict.REPAIR,
            StageState.REPAIR_NEEDED,
            PostValidationAction.REPAIR,
            False,
        ),
        (
            ValidationVerdict.BLOCKED,
            StageState.BLOCKED,
            PostValidationAction.WAIT,
            False,
        ),
    ),
)
def test_stage_transition_flow_covers_happy_validator_failure_and_blocked_paths(
    tmp_path: Path,
    verdict: ValidationVerdict,
    expected_state: StageState,
    expected_action: PostValidationAction,
    expected_terminal: bool,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )
    transition_stage_state(StageState.EXECUTING, StageState.VALIDATING)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 1, tzinfo=UTC),
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=verdict,
        changed_at_utc=datetime(2026, 4, 22, 10, 2, tzinfo=UTC),
    )

    transition = decide_post_validation_transition(validation_state)

    assert transition.next_state == expected_state
    assert transition.action == expected_action
    assert transition.is_terminal is expected_terminal
    payload = json.loads(validation_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.EXECUTING.value,
        StageState.VALIDATING.value,
        expected_state.value,
    ]


def test_stage_transition_flow_covers_adapter_failure_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )

    persist_execution_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        changed_at_utc=datetime(2026, 4, 22, 10, 0, tzinfo=UTC),
    )
    transition_stage_state(StageState.EXECUTING, StageState.FAILED)
    metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.FAILED.value,
        changed_at_utc=datetime(2026, 4, 22, 10, 1, tzinfo=UTC),
    )

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.FAILED.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.EXECUTING.value,
        StageState.FAILED.value,
    ]
    assert is_terminal_state(StageState.FAILED) is True


def test_decide_post_validation_transition_blocks_success_with_unresolved_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.next_state == StageState.BLOCKED
    assert transition.action == PostValidationAction.WAIT
    assert transition.is_terminal is False
    payload = json.loads(transition.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.VALIDATING.value,
        StageState.SUCCEEDED.value,
        StageState.BLOCKED.value,
    ]


def test_decide_post_validation_transition_allows_success_when_questions_resolved(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )
    prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    for name, content in _valid_plan_output_documents().items():
        (stage_root / name).write_text(content, encoding="utf-8")

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.next_state == StageState.SUCCEEDED
    assert transition.action == PostValidationAction.ADVANCE
    assert transition.is_terminal is True
    published_root = stage_root / "output"
    assert (published_root / "plan.md").exists()
    assert (published_root / "stage-result.md").exists()
    assert (published_root / "validator-report.md").exists()
    assert (published_root / "plan.md").read_text(encoding="utf-8") == (
        stage_root / "plan.md"
    ).read_text(encoding="utf-8")


def test_decide_post_validation_transition_can_defer_task_scoped_publication(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    for name, content in _valid_plan_output_documents().items():
        (stage_root / name).write_text(content, encoding="utf-8")
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
        defer_success_publication=True,
    )

    assert transition.action == PostValidationAction.ADVANCE
    assert not (stage_root / "output" / "plan.md").exists()
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    assert metadata is not None
    assert metadata.status == StageState.PENDING.value


def test_decide_post_validation_transition_reconciles_stale_stage_result_on_pass(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    preparation_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_outputs(preparation_bundle.expected_output_documents)
    stage_result_path = (
        workspace_root
        / "workitems"
        / "WI-001"
        / "stages"
        / "plan"
        / "stage-result.md"
    )
    stage_result_path.write_text(
        "# Stage result\n\n"
        "## Stage\n\n"
        "- Stage: `plan`\n\n"
        "## Attempt history\n\n"
        "- Attempt 1 (`initial`): runtime draft completed.\n\n"
        "## Status\n\n"
        "- Status: `failed`\n\n"
        "## Produced outputs\n\n"
        "- `workitems/WI-001/stages/plan/output/plan.md`\n\n"
        "## Validation summary\n\n"
        "- Validator verdict: `fail`\n\n"
        "## Blockers\n\n"
        "- none\n\n"
        "## Next actions\n\n"
        "- retry validation\n\n"
        "## Terminal state notes\n\n"
        "- Runtime draft still had stale failure text.\n",
        encoding="utf-8",
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.action == PostValidationAction.ADVANCE
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- Status: `succeeded`" in stage_result_text
    assert "- Validator verdict: `pass`" in stage_result_text
    assert "stale runtime draft status/verdict was normalized" in stage_result_text
    published_stage_result = stage_result_path.parent / "output" / "stage-result.md"
    assert "- Status: `succeeded`" in published_stage_result.read_text(encoding="utf-8")


def test_decide_post_validation_transition_does_not_reconcile_when_questions_block(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    stage_result_path = stage_root / "stage-result.md"
    stage_result_path.write_text(
        "# Stage result\n\n"
        "## Status\n\n"
        "- Status: `blocked`\n\n"
        "## Validation summary\n\n"
        "- Validator verdict: `fail`\n\n"
        "## Terminal state notes\n\n"
        "- Blocking question remains unresolved.\n",
        encoding="utf-8",
    )

    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.PASS,
    )

    transition = decide_post_validation_transition(
        validation_state,
        workspace_root=workspace_root,
    )

    assert transition.action == PostValidationAction.WAIT
    stage_result_text = stage_result_path.read_text(encoding="utf-8")
    assert "- Status: `blocked`" in stage_result_text
    assert "- Validator verdict: `fail`" in stage_result_text
    assert "stale runtime draft status/verdict was normalized" not in stage_result_text


def test_update_stage_unblock_state_keeps_stage_blocked_when_answers_missing(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    metadata_path = persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is False
    assert unblock_state.next_state == StageState.BLOCKED
    assert unblock_state.stage_metadata_path is not None
    payload = json.loads(unblock_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value
    assert unblock_state.next_state == StageState.BLOCKED
    assert unblock_state.stage_metadata_path == metadata_path
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.BLOCKED.value


def test_update_stage_unblock_state_moves_stage_to_preparing_when_answers_ready(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is True
    assert unblock_state.next_state == StageState.PREPARING
    assert unblock_state.stage_metadata_path is not None
    payload = json.loads(unblock_state.stage_metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == StageState.PREPARING.value
    assert [entry["status"] for entry in payload["status_history"]] == [
        StageState.BLOCKED.value,
        StageState.PREPARING.value,
    ]


def test_update_stage_unblock_state_keeps_stage_blocked_for_pending_operator_request(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    request = RuntimeOperatorRequest.create(
        runtime_id="generic-cli",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "npm install"},
        cwd=tmp_path,
    )
    append_operator_request(path=attempt_path / "operator-requests.jsonl", request=request)

    pending_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    resolve_operator_decision(
        attempt_path=attempt_path,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.DENY,
            source=RuntimeOperatorDecisionSource.UI,
            reason="denied in test",
        ),
    )
    denied_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    with pytest.raises(OperatorDecisionConflict, match="already resolved"):
        resolve_operator_decision(
            attempt_path=attempt_path,
            decision=RuntimeOperatorDecision(
                request_id=request.id,
                action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
                source=RuntimeOperatorDecisionSource.UI,
                reason="approved in test",
            ),
        )
    immutable_denied_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert pending_state.was_blocked is True
    assert pending_state.unblocked is False
    assert pending_state.next_state == StageState.BLOCKED
    assert denied_state.was_blocked is True
    assert denied_state.unblocked is False
    assert denied_state.next_state == StageState.BLOCKED
    assert immutable_denied_state.was_blocked is True
    assert immutable_denied_state.unblocked is False
    assert immutable_denied_state.next_state == StageState.BLOCKED


def test_update_stage_unblock_state_accepts_approved_operator_request(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    attempt_path = create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )
    request = RuntimeOperatorRequest.create(
        runtime_id="generic-cli",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "python -m pytest -q"},
        cwd=tmp_path,
    )
    append_operator_request(path=attempt_path / "operator-requests.jsonl", request=request)
    resolve_operator_decision(
        attempt_path=attempt_path,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
            source=RuntimeOperatorDecisionSource.UI,
            reason="approved in test",
        ),
    )

    unblocked_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblocked_state.was_blocked is True
    assert unblocked_state.unblocked is True
    assert unblocked_state.next_state == StageState.PREPARING


def test_update_stage_unblock_state_keeps_stage_blocked_with_partial_answer(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [partial] Approval requested; final sign-off pending.\n",
        encoding="utf-8",
    )

    unblock_state = update_stage_unblock_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert unblock_state.was_blocked is True
    assert unblock_state.unblocked is False


def test_prepare_stage_resume_after_answers_keeps_stage_blocked_without_resolved_answers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )

    resume_result = prepare_stage_resume_after_answers(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert isinstance(resume_result, StageResumeResult)
    assert resume_result.unblock_state.unblocked is False
    assert resume_result.preparation_bundle is None
    assert resume_result.execution_state is None
    assert resume_result.adapter_invocation is None


def test_prepare_stage_resume_after_answers_creates_new_attempt_and_invocation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.BLOCKED.value,
    )
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "questions.md").write_text(
        "# Questions\n\n## Questions\n\n- Q1 [blocking] Confirm release owner approval.\n",
        encoding="utf-8",
    )
    (stage_root / "answers.md").write_text(
        "# Answers\n\n## Answers\n\n- Q1 [resolved] Release owner approval is recorded.\n",
        encoding="utf-8",
    )

    preview_bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item="WI-001",
        stage="plan",
    )
    _materialize_expected_inputs(preview_bundle.expected_input_bundle)
    resume_result = prepare_stage_resume_after_answers(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
    )

    assert resume_result.unblock_state.unblocked is True
    assert resume_result.preparation_bundle is not None
    assert resume_result.execution_state is not None
    assert resume_result.adapter_invocation is not None
    assert resume_result.execution_state.attempt_number == 1
    assert resume_result.execution_state.attempt_path.name == "attempt-0001"
    assert resume_result.adapter_invocation.attempt_number == 1
    assert resume_result.adapter_invocation.input_bundle_path.exists()
    assert (
        "`workitems/WI-001/stages/plan/questions.md`"
        in resume_result.adapter_invocation.input_bundle_markdown
    )
    assert (
        "`workitems/WI-001/stages/plan/answers.md`"
        in resume_result.adapter_invocation.input_bundle_markdown
    )
    assert "Release owner approval is recorded." in (
        resume_result.adapter_invocation.input_bundle_markdown
    )
    assert (
        "`workitems/WI-001/stages/plan/answers.md`"
        in resume_result.preparation_bundle.stage_brief_markdown
    )
