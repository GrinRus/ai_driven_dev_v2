from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

from aidd.adapters.generic_cli.runner import (
    GenericCliExitClassification,
    GenericCliStageContext,
    build_subprocess_spec,
    persist_attempt_runtime_artifacts,
    run_subprocess_with_streaming,
)
from aidd.core.run_store import create_run_manifest, persist_stage_status
from aidd.core.stage_runner import (
    AdapterInvocationBundle,
    PostValidationAction,
    StageExecutionState,
    ValidationVerdict,
    decide_post_validation_transition,
    discover_stage_markdown_outputs,
    persist_execution_state,
    persist_validation_state,
    prepare_adapter_invocation,
    prepare_stage_bundle,
    route_stage_questions_to_interview,
    run_structural_validation_after_output_discovery,
)
from aidd.core.state_machine import StageState


def _materialize_expected_inputs(paths: tuple[Path, ...]) -> None:
    for index, path in enumerate(paths, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# Input {index}\n\nPrepared upstream input for `{path.name}`.\n",
            encoding="utf-8",
        )


def _prepare_plan_attempt(
    tmp_path: Path,
) -> tuple[Path, StageExecutionState, AdapterInvocationBundle]:
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
    return workspace_root, execution_state, invocation


def _run_runtime_script(
    *,
    tmp_path: Path,
    workspace_root: Path,
    documents: dict[str, str],
) -> None:
    script_path = tmp_path / "runtime_writer.py"
    script_body = "\n".join(
        [
            "import os",
            "from pathlib import Path",
            f"documents = {documents!r}",
            "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
            "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM']",
            "stage_root = stage_root / 'stages' / os.environ['AIDD_STAGE']",
            "stage_root.mkdir(parents=True, exist_ok=True)",
            "for name, content in documents.items():",
            "    (stage_root / name).write_text(content, encoding='utf-8')",
            "",
        ]
    )
    script_path.write_text(script_body, encoding="utf-8")
    context = GenericCliStageContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
    )
    command = f"{shlex.quote(sys.executable)} {shlex.quote(script_path.as_posix())}"
    spec = build_subprocess_spec(
        configured_command=command,
        workspace_root=workspace_root,
        context=context,
        base_env=dict(os.environ),
        repository_root=Path.cwd(),
    )
    run_result = run_subprocess_with_streaming(spec=spec)
    assert run_result.exit_classification is GenericCliExitClassification.SUCCESS
    persist_attempt_runtime_artifacts(
        attempt_path=(
            workspace_root
            / "reports"
            / "runs"
            / "WI-001"
            / "run-001"
            / "stages"
            / "plan"
            / "attempts"
            / "attempt-0001"
        ),
        run_result=run_result,
    )


def _valid_output_documents(*, unresolved_question: bool = False) -> dict[str, str]:
    questions_block = (
        "- `Q1` `[blocking]` Confirm scope boundaries.\n"
        if unresolved_question
        else "- none\n"
    )
    answers_block = (
        "- `Q1` `[partial]` Scope still under review.\n"
        if unresolved_question
        else "- none\n"
    )
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
            "## Verification notes\n\n- Validate highest-risk milestone with targeted tests.\n"
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
        "repair-brief.md": (
            "# Failed checks\n\n- none\n\n"
            "## Required corrections\n\n- none\n\n"
            "## Relevant upstream docs\n\n- none\n"
        ),
        "questions.md": f"# Questions\n\n{questions_block}",
        "answers.md": f"# Answers\n\n{answers_block}",
    }


def test_generic_cli_handshake_valid_output_flow_advances(tmp_path: Path) -> None:
    workspace_root, execution_state, invocation = _prepare_plan_attempt(tmp_path)
    _run_runtime_script(
        tmp_path=tmp_path,
        workspace_root=workspace_root,
        documents=_valid_output_documents(),
    )

    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    structural = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    assert structural.findings == ()
    interview_routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    assert interview_routing.requires_interview is False

    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
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
    assert transition.action is PostValidationAction.ADVANCE
    assert transition.next_state is StageState.SUCCEEDED
    published_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output"
    stage_root = workspace_root / "workitems" / "WI-001" / "stages" / "plan"
    assert (published_root / "plan.md").exists()
    assert (published_root / "stage-result.md").exists()
    assert (published_root / "validator-report.md").exists()
    assert (published_root / "plan.md").read_text(encoding="utf-8") == (
        stage_root / "plan.md"
    ).read_text(encoding="utf-8")


def test_generic_cli_handshake_invalid_output_flow_stops(tmp_path: Path) -> None:
    workspace_root, execution_state, invocation = _prepare_plan_attempt(tmp_path)
    _run_runtime_script(
        tmp_path=tmp_path,
        workspace_root=workspace_root,
        documents={
            "plan.md": "# Plan\n\nIncomplete output.\n",
        },
    )

    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    structural = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    assert any(
        finding.code == "STRUCT-MISSING-REQUIRED-DOCUMENT"
        for finding in structural.findings
    )

    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
    )
    validation_state = persist_validation_state(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        verdict=ValidationVerdict.FAIL,
    )
    transition = decide_post_validation_transition(validation_state)
    assert transition.action is PostValidationAction.STOP
    assert transition.next_state is StageState.FAILED


def test_generic_cli_handshake_question_blocked_flow_waits(tmp_path: Path) -> None:
    workspace_root, execution_state, invocation = _prepare_plan_attempt(tmp_path)
    _run_runtime_script(
        tmp_path=tmp_path,
        workspace_root=workspace_root,
        documents=_valid_output_documents(unresolved_question=True),
    )

    discovery = discover_stage_markdown_outputs(
        execution_state=execution_state,
        invocation_bundle=invocation,
    )
    structural = run_structural_validation_after_output_discovery(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    assert structural.findings == ()
    interview_routing = route_stage_questions_to_interview(
        workspace_root=workspace_root,
        discovery=discovery,
    )
    assert interview_routing.requires_interview is True
    assert interview_routing.unresolved_blocking_question_ids == ("Q1",)

    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-001",
        run_id="run-001",
        stage="plan",
        status=StageState.VALIDATING.value,
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
    assert transition.action is PostValidationAction.WAIT
    assert transition.next_state is StageState.BLOCKED
