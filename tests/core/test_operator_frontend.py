from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.config import load_config
from aidd.core.interview import AnswerResolution
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifact_document_content,
    resolve_operator_artifacts_view,
    resolve_operator_dashboard_view,
    resolve_operator_evidence_graph_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_document_workbench,
    resolve_operator_stage_view,
)
from aidd.core.operator_intervention import persist_operator_intervention_request
from aidd.core.repair import persist_repair_history_snapshot
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_run_archive_decision,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
    run_attempt_runtime_log_path,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    append_operator_decision,
    append_operator_request,
)
from aidd.core.runtime_readiness import (
    RuntimeReadinessProbeReport,
    resolve_runtime_readiness,
)
from aidd.core.stages import STAGES
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
)


def _prepare_run(workspace_root: Path) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="blocked",
    )
    run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).write_text("runtime-line\n", encoding="utf-8")


def _write_questions(workspace_root: Path) -> None:
    questions_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "questions.md"
    questions_path.parent.mkdir(parents=True, exist_ok=True)
    questions_path.write_text(
        "\n".join(
            (
                "# Questions",
                "",
                "## Questions",
                "",
                "- `Q1` `[blocking]` Confirm the target release.",
                "- `Q2` `[non-blocking]` Confirm reviewer preference.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _write_valid_plan_outputs(workspace_root: Path, *, body_suffix: str = "") -> Path:
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    plan_path = stage_root / "plan.md"
    plan_path.write_text(
        "\n".join(
            (
                "# Plan",
                "",
                "## Goals",
                "",
                "- Ship the operator workbench.",
                "",
                "## Out of scope",
                "",
                "- No runtime mutation.",
                "",
                "## Milestones",
                "",
                "- Add a read model.",
                "",
                "## Implementation strategy",
                "",
                "- Read existing artifacts only.",
                "",
                "## Risks",
                "",
                "- Truncated files can hide headings; mark unknown.",
                "",
                "## Dependencies",
                "",
                "- Existing artifact index.",
                "",
                "## Verification approach",
                "",
                "- Run core read-model tests.",
                "",
                "## Verification notes",
                "",
                "- Check present, missing, truncated, and invalid documents.",
                body_suffix,
            )
        ),
        encoding="utf-8",
    )
    stage_root.joinpath("stage-result.md").write_text(
        "# Stage Result\n\n## Status\n\n- `blocked`\n",
        encoding="utf-8",
    )
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `pass`\n",
        encoding="utf-8",
    )
    return plan_path


def _prepare_terminal_qa_run(
    workspace_root: Path,
    *,
    qa_stage_status: str = "succeeded",
    qa_verdict: str = "ready",
    validator_verdict: str = "pass",
    lineage: dict[str, object] | None = None,
) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target="qa",
        config_snapshot={"mode": "test"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
        lineage=lineage,
    )
    for stage in STAGES:
        create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage=stage,
        )
        status = qa_stage_status if stage == "qa" else "succeeded"
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage=stage,
            status=status,
        )
        stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / stage
        stage_root.mkdir(parents=True, exist_ok=True)
        stage_validator_verdict = validator_verdict if stage == "qa" else "pass"
        stage_root.joinpath("validator-report.md").write_text(
            f"# Validator Report\n\n- Verdict: `{stage_validator_verdict}`\n",
            encoding="utf-8",
        )
        stage_root.joinpath("stage-result.md").write_text(
            f"# Stage Result\n\n## Status\n\n- `{status}`\n",
            encoding="utf-8",
        )
        run_attempt_runtime_log_path(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage=stage,
            attempt_number=1,
        ).write_text(f"{stage} runtime log\n", encoding="utf-8")

    qa_root = workspace_root / "workitems" / "WI-UI" / "stages" / "qa"
    qa_root.joinpath("qa-report.md").write_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "## Verification summary",
                "",
                "- Verification completed.",
                "",
                "## Release recommendation",
                "",
                "- Release recommendation: `proceed`.",
                "",
                "## Evidence",
                "",
                "- EV-1 `workitems/WI-UI/stages/qa/stage-result.md`",
                "",
                "## Known issues",
                "",
                "- Known issues: none.",
                "",
                "## Readiness",
                "",
                f"- QA verdict: `{qa_verdict}`.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _write_operator_approval(attempt_path: Path) -> None:
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="qa",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "uv run --extra dev pytest tests/core/test_operator_frontend.py"},
        risk=RuntimeOperatorRisk.MEDIUM,
    )
    append_operator_request(
        path=attempt_path / OPERATOR_REQUESTS_FILENAME,
        request=request,
    )
    append_operator_decision(
        path=attempt_path / OPERATOR_DECISIONS_FILENAME,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
            source=RuntimeOperatorDecisionSource.UI,
            reason="approved in operator UI",
        ),
    )


def test_operator_dashboard_view_handles_no_runs(tmp_path: Path) -> None:
    dashboard = resolve_operator_dashboard_view(
        workspace_root=tmp_path / ".aidd",
        work_item="WI-UI",
        active_stage="idea",
        project_root=tmp_path,
    )

    assert dashboard.run.run_id is None
    assert dashboard.next_action.action == "choose-runtime"
    assert dashboard.next_action.enabled is False
    assert dashboard.stages[0].stage == "idea"
    assert dashboard.stages[0].can_run is True
    assert dashboard.activity == ()
    assert dashboard.recent_artifacts == ()


def test_operator_dashboard_view_surfaces_blocked_stage_evidence_and_activity(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.joinpath("plan.md").write_text("# Plan\n\n- Ship UI cockpit.\n", encoding="utf-8")
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )
    stage_root.joinpath("repair-brief.md").write_text(
        "# Repair\n\n- Missing evidence.\n",
        encoding="utf-8",
    )
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        request_text="Add rollback risk coverage.",
        target_documents=("plan.md",),
    )
    run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).joinpath("input-bundle.md").write_text(
        f"# Input bundle\n\n## `{request.request_path.relative_to(workspace_root)}`\n",
        encoding="utf-8",
    )
    run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).joinpath(RUN_EVENTS_JSONL_FILENAME).write_text(
        (
            '{"timestamp":"2026-05-25T00:00:00Z","level":"warn",'
            '"source":"runtime","event":"question","message":"Need release target"}\n'
        ),
        encoding="utf-8",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="plan",
        run_id="run-ui",
        project_root=tmp_path,
    )

    assert dashboard.run.run_id == "run-ui"
    assert dashboard.next_action.action == "answer-questions"
    assert dashboard.primary_artifact is not None
    assert dashboard.primary_artifact.key == "plan"
    assert "Ship UI cockpit" in dashboard.primary_artifact.excerpt
    assert {blocker.kind for blocker in dashboard.blockers} == {"questions", "validation"}
    assert all(
        blocker.path is None or not Path(blocker.path).is_absolute()
        for blocker in dashboard.blockers
    )
    assert all(not Path(ref.path).is_absolute() for ref in dashboard.evidence_refs)
    assert any(ref.kind == "operator-request" for ref in dashboard.evidence_refs)
    assert any(ref.key == "plan" for ref in dashboard.recent_artifacts)
    assert any(ref.key == "operator_request" for ref in dashboard.recent_artifacts)
    assert any(ref.key == "runtime_log" for ref in dashboard.recent_artifacts)
    assert all(
        (workspace_root / ref.path).exists()
        for ref in dashboard.recent_artifacts
    )
    assert any(event.event == "question" for event in dashboard.activity)
    assert any(event.event == "operator.request.created" for event in dashboard.activity)

    dashboard_from_other_stage = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="idea",
        run_id="run-ui",
        project_root=tmp_path,
    )

    assert any(event.event == "question" for event in dashboard_from_other_stage.activity)


def test_operator_dashboard_next_action_finds_blocked_stage_when_another_stage_is_selected(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="idea",
        run_id="run-ui",
    )

    assert dashboard.next_action.action == "answer-questions"
    assert dashboard.next_action.stage == "plan"
    assert dashboard.next_action.enabled is True
    assert any(
        blocker.kind == "questions" and blocker.stage == "plan"
        for blocker in dashboard.blockers
    )


def test_operator_dashboard_next_action_inspects_failed_validation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="failed",
    )
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="plan",
        run_id="run-ui",
    )

    assert dashboard.next_action.action == "inspect-validation"
    assert any(blocker.kind == "validation" for blocker in dashboard.blockers)


def test_operator_dashboard_next_action_reviews_failed_intervention_result(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="failed",
    )
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        request_text="Add rollback risk coverage.",
        target_documents=("plan.md",),
    )
    run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).joinpath("input-bundle.md").write_text(
        f"# Input bundle\n\n## `{request.request_path.relative_to(workspace_root)}`\n",
        encoding="utf-8",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="plan",
        run_id="run-ui",
    )

    assert dashboard.next_action.action == "review-intervention"
    assert dashboard.next_action.label == "Review requested change result"


def test_operator_dashboard_keeps_intervention_next_action_after_repair_retry_failure(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )
    stage_root.joinpath("repair-brief.md").write_text(
        "# Failed checks\n\n- retry failed\n",
        encoding="utf-8",
    )
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        request_text="Add rollback risk coverage.",
        target_documents=("plan.md",),
    )
    run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).joinpath("input-bundle.md").write_text(
        f"# Input bundle\n\n## `{request.request_path.relative_to(workspace_root)}`\n",
        encoding="utf-8",
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
        trigger="intervention",
        outcome="failed validation",
        stage_status="repair-needed",
        validator_report_path=stage_root / "validator-report.md",
        repair_brief_path=stage_root / "repair-brief.md",
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="failed",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="plan",
        run_id="run-ui",
    )

    assert dashboard.next_action.action == "review-intervention"
    assert any(event.event == "repair.intervention" for event in dashboard.activity)


def test_operator_dashboard_reports_missing_prerequisite_blockers(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target="implement",
        config_snapshot={"mode": "test"},
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="implement",
        run_id="run-ui",
    )

    assert any(blocker.kind == "missing-prerequisite" for blocker in dashboard.blockers)
    implement = {item.stage: item for item in dashboard.stages}["implement"]
    assert implement.can_run is False
    assert "missing prerequisites" in implement.reason


def test_operator_dashboard_next_action_marks_completed_flow(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(workspace_root)
    _write_questions(workspace_root)
    persist_operator_answer(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        question_id="Q1",
        text="The target release is 0.2.0.",
    )
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
        trigger="repair",
        outcome="succeeded",
        stage_status="succeeded",
        validator_report_path=(
            workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "validator-report.md"
        ),
        repair_brief_path=(
            workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "repair-brief.md"
        ),
    )
    _write_operator_approval(
        run_attempt_root(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage="qa",
            attempt_number=1,
        )
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )

    assert dashboard.next_action.action == "review-complete"
    assert dashboard.next_action.enabled is True
    assert dashboard.terminal_handoff is not None
    assert dashboard.terminal_handoff.status == "completed"
    assert dashboard.terminal_handoff.final_qa_status == "ready"
    assert dashboard.terminal_handoff.qa_stage_state == "succeeded"
    assert dashboard.terminal_handoff.repair_counts.attempts == 1
    assert dashboard.terminal_handoff.repair_counts.succeeded == 1
    assert dashboard.terminal_handoff.approval_counts.requested == 1
    assert dashboard.terminal_handoff.approval_counts.approved == 1
    assert dashboard.terminal_handoff.questions_answered_count == 1
    assert dashboard.terminal_handoff.questions_total_count == 2
    assert {artifact.key for artifact in dashboard.terminal_handoff.final_artifacts} >= {
        "qa_report",
        "stage_result",
        "validator_report",
        "runtime_log",
    }
    assert {
        action.action
        for action in dashboard.terminal_handoff.recommended_next_flow_actions
    } == {
        "create-new-work-item",
        "start-follow-up-flow",
        "clone-flow",
        "run-eval-batch",
        "archive-run",
    }


def test_operator_dashboard_terminal_handoff_reports_failed_qa(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(
        workspace_root,
        qa_stage_status="failed",
        qa_verdict="not-ready",
        validator_verdict="fail",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )

    assert dashboard.terminal_handoff is not None
    assert dashboard.terminal_handoff.status == "failed"
    assert dashboard.terminal_handoff.final_qa_status == "not-ready"
    assert dashboard.terminal_handoff.qa_stage_state == "failed"
    assert any(blocker.kind == "validation" for blocker in dashboard.terminal_handoff.blockers)
    follow_up = next(
        action
        for action in dashboard.terminal_handoff.recommended_next_flow_actions
        if action.action == "start-follow-up-flow"
    )
    assert follow_up.enabled is True
    assert "blockers" in follow_up.detail


def test_operator_dashboard_terminal_handoff_reports_completed_with_warning(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(
        workspace_root,
        qa_stage_status="succeeded",
        qa_verdict="ready-with-risks",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )

    assert dashboard.terminal_handoff is not None
    assert dashboard.terminal_handoff.status == "completed-with-warning"
    assert dashboard.terminal_handoff.final_qa_status == "ready-with-risks"
    assert dashboard.terminal_handoff.qa_stage_state == "succeeded"
    assert dashboard.terminal_handoff.blockers == ()


def test_operator_dashboard_exposes_archive_state_without_hiding_artifacts(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(workspace_root)

    archive = persist_run_archive_decision(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        reason="Archived after final QA review.",
        source="ui",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )
    qa_document = resolve_operator_artifact_document_content(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="qa",
        key="qa_report",
        run_id="run-ui",
        attempt_number=1,
    )

    assert archive["archived"] is True
    assert dashboard.run.archive.archived is True
    assert dashboard.run.archive.reason == "Archived after final QA review."
    assert dashboard.run.archive.source == "ui"
    assert dashboard.terminal_handoff is not None
    assert dashboard.terminal_handoff.status == "completed"
    assert "# QA Report" in qa_document.text


def test_operator_dashboard_run_summary_exposes_optional_lineage_references(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(
        workspace_root,
        lineage={
            "source_run_id": "run-source<script>",
            "source_work_item_id": "WI-SOURCE<&>",
            "baseline_id": "baseline-main@abc123",
            "baseline_label": "main before UI handoff <candidate>",
        },
    )
    work_item_metadata_path = workspace_root / "workitems" / "WI-UI" / "work-item.json"
    work_item_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    work_item_metadata_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "work_item_id": "WI-UI",
                "lineage": {
                    "child_work_item_candidates": [
                        {
                            "work_item_id": "WI-CHILD<&>",
                            "label": "Follow-up for <risk>",
                            "relationship": "follow-up",
                            "source_run_id": "run-ui",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )

    lineage = dashboard.run.lineage
    assert lineage.source_run_id == "run-source<script>"
    assert lineage.source_work_item_id == "WI-SOURCE<&>"
    assert lineage.baseline_id == "baseline-main@abc123"
    assert lineage.baseline_label == "main before UI handoff <candidate>"
    assert len(lineage.child_work_item_candidates) == 1
    candidate = lineage.child_work_item_candidates[0]
    assert candidate.work_item_id == "WI-CHILD<&>"
    assert candidate.label == "Follow-up for <risk>"
    assert candidate.relationship == "follow-up"
    assert candidate.source_run_id == "run-ui"


def test_operator_dashboard_run_summary_keeps_lineage_empty_for_old_runs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_terminal_qa_run(workspace_root)

    dashboard = resolve_operator_dashboard_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        active_stage="qa",
        run_id="run-ui",
    )

    assert dashboard.run.lineage.source_run_id is None
    assert dashboard.run.lineage.source_work_item_id is None
    assert dashboard.run.lineage.baseline_id is None
    assert dashboard.run.lineage.baseline_label is None
    assert dashboard.run.lineage.child_work_item_candidates == ()


def test_operator_read_models_expose_run_stage_logs_artifacts_and_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)

    run_view = resolve_operator_run_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
    )
    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )
    log_view = resolve_operator_run_log_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
    )
    artifacts_view = resolve_operator_artifacts_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert run_view.metadata.runtime_id == "codex"
    assert stage_view.result.final_state == "blocked"
    assert stage_view.questions.unresolved_blocking_question_ids == ("Q1",)
    assert log_view.runtime_log_path.read_text(encoding="utf-8") == "runtime-line\n"
    assert artifacts_view.documents["stage_result"] == (
        "workitems/WI-UI/stages/plan/stage-result.md"
    )


def test_operator_stage_view_diagnostics_report_blocked_questions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    diagnostics = stage_view.diagnostics
    assert diagnostics.status == "blocked"
    assert diagnostics.blocking_questions.status == "blocked"
    assert diagnostics.blocking_questions.unresolved_count == 1
    assert diagnostics.blocking_questions.unresolved_question_ids == ("Q1",)
    assert diagnostics.blocking_questions.answers_path == (
        "workitems/WI-UI/stages/plan/answers.md"
    )


def test_operator_stage_view_diagnostics_report_repair_available(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    validator_report = stage_root / "validator-report.md"
    repair_brief = stage_root / "repair-brief.md"
    validator_report.write_text("# Validator Report\n\n- Verdict: `fail`\n", encoding="utf-8")
    repair_brief.write_text("# Repair Brief\n\n- Add missing risk evidence.\n", encoding="utf-8")
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
        trigger="repair",
        outcome="failed validation",
        stage_status="repair-needed",
        validator_report_path=validator_report,
        repair_brief_path=repair_brief,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="repair-needed",
    )

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    validation = stage_view.diagnostics.validation
    assert stage_view.diagnostics.status == "repair-available"
    assert validation.status == "repair-available"
    assert validation.final_state == "repair-needed"
    assert validation.validator_fail_count == 1
    assert len(validation.repair_attempts) == 1
    assert validation.repair_attempts[0].trigger == "repair"
    assert validation.repair_attempts[0].outcome == "failed validation"


def test_operator_stage_view_diagnostics_report_stopped_event(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    events_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ) / RUN_EVENTS_JSONL_FILENAME
    events_path.write_text(
        (
            '{"timestamp":"2026-05-25T00:00:00Z","level":"error",'
            '"source":"runtime","event":"stopped","message":"Workflow stopped at plan"}\n'
        ),
        encoding="utf-8",
    )

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    assert stage_view.diagnostics.status == "stopped"
    assert stage_view.diagnostics.stopped.stopped is True
    assert stage_view.diagnostics.stopped.source == (
        "reports/runs/WI-UI/run-ui/stages/plan/attempts/attempt-0001/events.jsonl"
    )
    assert stage_view.diagnostics.stopped.detail == "Workflow stopped at plan"


def test_operator_stage_view_diagnostics_report_pending_approval_queue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "uv run --extra dev pytest tests/core/test_operator_frontend.py"},
        risk=RuntimeOperatorRisk.MEDIUM,
    )
    append_operator_request(
        path=(
            run_attempt_root(
                workspace_root=workspace_root,
                work_item="WI-UI",
                run_id="run-ui",
                stage="plan",
                attempt_number=1,
            )
            / OPERATOR_REQUESTS_FILENAME
        ),
        request=request,
    )

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    approvals = stage_view.diagnostics.approvals
    assert stage_view.diagnostics.status == "approval-waiting"
    assert approvals.status == "approval-waiting"
    assert approvals.requested_count == 1
    assert approvals.pending_count == 1
    assert approvals.pending_request_ids == (request.id,)
    assert approvals.approved_count == 0


def test_operator_stage_view_diagnostics_report_truncated_log_source(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).write_text("x" * (33 * 1024), encoding="utf-8")

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    raw_log = stage_view.diagnostics.raw_log
    assert stage_view.diagnostics.status == "log-truncated"
    assert raw_log.status == "truncated"
    assert raw_log.byte_size == 33 * 1024
    assert raw_log.truncated is True
    assert raw_log.truncated_head is True
    assert raw_log.truncated_tail is False


def test_operator_stage_view_diagnostics_exposes_request_change_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root)
    request = persist_operator_intervention_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        request_text="Add rollback risk coverage to the plan.",
        target_documents=("plan.md",),
    )

    stage_view = resolve_operator_stage_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    request_change = stage_view.diagnostics.request_change
    assert request_change.status == "has-request"
    assert request_change.latest_request_id == request.request_id
    assert request_change.latest_request_path == (
        f"workitems/WI-UI/stages/plan/operator-requests/{request.request_id}.md"
    )
    assert request_change.latest_request_excerpt == "Add rollback risk coverage to the plan."
    assert request_change.target_documents == ("workitems/WI-UI/stages/plan/plan.md",)


def test_operator_run_log_view_returns_bounded_text_with_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    runtime_log_path = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    runtime_log_path.write_text("abcdefghij", encoding="utf-8")

    head_view = resolve_operator_run_log_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
        limit_bytes=4,
    )
    tail_view = resolve_operator_run_log_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
        tail_bytes=4,
    )

    assert head_view.text == "abcd"
    assert head_view.byte_size == 10
    assert head_view.start_byte == 0
    assert head_view.end_byte == 4
    assert head_view.truncated is True
    assert head_view.truncated_tail is True
    assert tail_view.text == "ghij"
    assert tail_view.start_byte == 6
    assert tail_view.end_byte == 10
    assert tail_view.truncated_head is True


def test_operator_artifact_document_content_returns_bounded_text_with_metadata(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    text = "# Plan\n\n" + ("A" * 4096)
    plan_path.write_text(text, encoding="utf-8")

    preview = resolve_operator_artifact_document_content(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
        limit_bytes=32,
    )
    source = resolve_operator_artifact_document_content(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
        mode="source",
        limit_bytes=64,
    )

    assert preview.text == text[:32]
    assert preview.mode == "preview"
    assert preview.byte_size == len(text.encode("utf-8"))
    assert preview.start_byte == 0
    assert preview.end_byte == 32
    assert preview.truncated is True
    assert preview.truncated_head is False
    assert preview.truncated_tail is True
    assert source.mode == "source"
    assert source.requested_bytes == 64
    assert source.end_byte == 64


def test_operator_evidence_graph_view_links_artifacts_events_and_approvals(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root)
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    attempt_path.joinpath(RUN_EVENTS_JSONL_FILENAME).write_text(
        (
            '{"timestamp":"2026-05-25T00:00:00Z","level":"info",'
            '"source":"runtime","event":"stage.started","message":"Plan stage started"}\n'
        ),
        encoding="utf-8",
    )
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "uv run --extra dev pytest tests/core/test_operator_frontend.py"},
        risk=RuntimeOperatorRisk.MEDIUM,
    )
    append_operator_request(path=attempt_path / OPERATOR_REQUESTS_FILENAME, request=request)
    append_operator_decision(
        path=attempt_path / OPERATOR_DECISIONS_FILENAME,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
            source=RuntimeOperatorDecisionSource.UI,
            reason="approved for graph test",
        ),
    )

    graph = resolve_operator_evidence_graph_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    nodes = {node.node_id: node for node in graph.nodes}
    edges = {(edge.source_id, edge.target_id, edge.kind) for edge in graph.edges}
    assert graph.mode == "graph"
    assert graph.incomplete_reasons == ()
    assert nodes["stage:plan"].status == "blocked"
    assert nodes["document:plan"].path == "workitems/WI-UI/stages/plan/plan.md"
    assert nodes["document:validator_report"].status == "pass"
    assert nodes["document:stage_result"].status == "blocked"
    assert nodes["log:runtime_log"].path == (
        "reports/runs/WI-UI/run-ui/stages/plan/attempts/attempt-0001/runtime.log"
    )
    assert nodes["event:1"].detail == "Plan stage started"
    assert nodes[f"approval-request:{request.id}"].status == "approved"
    assert nodes[f"approval-decision:{request.id}"].status == "allow_once"
    assert ("stage:plan", "attempt:1", "attempt") in edges
    assert ("attempt:1", "document:plan", "artifact-index") in edges
    assert ("document:validator_report", "document:stage_result", "validation") in edges
    assert ("log:events_jsonl", "event:1", "event-entry") in edges
    assert (
        f"approval-request:{request.id}",
        f"approval-decision:{request.id}",
        "approval-decision",
    ) in edges
    assert any(ref.key == "plan" for ref in graph.artifact_table)
    assert any(ref.key == "runtime_log" for ref in graph.artifact_table)
    assert all(
        node.path is None or not Path(node.path).is_absolute()
        for node in graph.nodes
    )
    assert all(not Path(ref.path).is_absolute() for ref in graph.artifact_table)


def test_operator_evidence_graph_view_degrades_to_flat_table_without_artifact_index(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root)
    run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    ).unlink()

    graph = resolve_operator_evidence_graph_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
    )

    table = {(ref.key, ref.kind, ref.path) for ref in graph.artifact_table}
    assert graph.mode == "flat-table"
    assert graph.nodes == ()
    assert graph.edges == ()
    assert graph.incomplete_reasons == ("artifact-index-missing",)
    assert ("plan", "document", "workitems/WI-UI/stages/plan/plan.md") in table
    assert (
        "runtime_log",
        "log",
        "reports/runs/WI-UI/run-ui/stages/plan/attempts/attempt-0001/runtime.log",
    ) in table


def test_operator_stage_document_workbench_returns_present_markdown_contract_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root)

    workbench = resolve_operator_stage_document_workbench(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert workbench.document.status == "present"
    assert workbench.document.preview is not None
    assert workbench.document.preview.mode == "preview"
    assert workbench.document.source is not None
    assert workbench.document.source.mode == "source"
    assert "Ship the operator workbench" in workbench.document.preview.text
    requirements = {(item.kind, item.label): item for item in workbench.requirements}
    assert requirements[("required-output", "plan.md")].status == "satisfied"
    assert requirements[("required-section", "Goals")].status == "satisfied"
    assert requirements[("required-section", "Verification notes")].status == "satisfied"
    validation = {item.label: item for item in workbench.validation_results}
    assert validation["validator-report"].status == "pass"
    assert validation["stage-result"].status == "blocked"
    assert any(
        ref.kind == "document" and ref.label == "validator_report"
        for ref in workbench.references
    )
    assert any(
        item.kind == "current-document" and item.key == "stage_result"
        for item in workbench.diff_inputs
    )
    assert [(version.attempt_number, version.source) for version in workbench.versions] == [
        (1, "model-authored")
    ]


def test_operator_stage_document_workbench_reports_missing_required_document(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)

    workbench = resolve_operator_stage_document_workbench(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert workbench.document.status == "missing"
    assert workbench.document.preview is None
    assert workbench.document.source is None
    assert "does not exist" in str(workbench.document.message)
    requirements = {(item.kind, item.label): item for item in workbench.requirements}
    assert requirements[("required-output", "plan.md")].status == "missing"
    assert requirements[("required-section", "Goals")].status == "unknown"


def test_operator_stage_document_workbench_reports_truncated_large_document(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root, body_suffix="\n" + ("large-line\n" * 256))

    workbench = resolve_operator_stage_document_workbench(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
        preview_limit_bytes=64,
        source_limit_bytes=96,
    )

    assert workbench.document.status == "present"
    assert workbench.document.preview is not None
    assert workbench.document.preview.truncated is True
    assert workbench.document.preview.truncated_tail is True
    assert workbench.document.source is not None
    assert workbench.document.source.requested_bytes == 96
    assert workbench.document.source.truncated_tail is True
    requirements = {(item.kind, item.label): item for item in workbench.requirements}
    assert requirements[("required-section", "Goals")].status == "satisfied"
    assert requirements[("required-section", "Verification notes")].status == "unknown"


def test_operator_stage_document_workbench_reports_invalid_utf8_without_mutating_artifact(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    raw_bytes = b"\xff\xfe\x00"
    plan_path.write_bytes(raw_bytes)

    workbench = resolve_operator_stage_document_workbench(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert workbench.document.status == "invalid"
    assert workbench.document.byte_size == len(raw_bytes)
    assert "not UTF-8 text" in str(workbench.document.message)
    assert workbench.document.preview is None
    assert workbench.document.source is None
    assert plan_path.read_bytes() == raw_bytes


def test_operator_stage_document_workbench_lists_previous_attempt_diff_and_versions(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_valid_plan_outputs(workspace_root)
    persist_repair_history_snapshot(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=2,
        trigger="repair",
        outcome="succeeded",
        stage_status="blocked",
        validator_report_path=(
            workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "validator-report.md"
        ),
        repair_brief_path=(
            workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "repair-brief.md"
        ),
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
    )

    workbench = resolve_operator_stage_document_workbench(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        key="plan",
        run_id="run-ui",
        attempt_number=2,
    )

    assert any(
        item.kind == "previous-version" and item.attempt_number == 1
        for item in workbench.diff_inputs
    )
    assert [(version.attempt_number, version.source) for version in workbench.versions] == [
        (1, "model-authored"),
        (2, "repair"),
    ]


def test_operator_artifacts_view_exposes_project_set_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    project_context_path = workspace_root / "workitems" / "WI-UI" / "context" / "project-set.md"
    project_context_path.parent.mkdir(parents=True)
    project_context_path.write_text("# Project Set\n\n- Project id: `api`\n", encoding="utf-8")
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
    )

    artifacts_view = resolve_operator_artifacts_view(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        run_id="run-ui",
        attempt_number=1,
    )

    assert artifacts_view.documents["project_set_context"] == (
        "workitems/WI-UI/context/project-set.md"
    )


def test_persist_operator_answer_writes_standard_answers_document(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    questions_view = persist_operator_answer(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        question_id="Q1",
        text="The target release is 0.2.0.",
    )

    assert questions_view.has_unresolved_blocking_questions is False
    assert questions_view.questions[0].status == "resolved"
    assert questions_view.questions[0].answer_text == "The target release is 0.2.0."
    assert questions_view.questions[0].answer_resolution is AnswerResolution.RESOLVED
    assert questions_view.answers_path.read_text(encoding="utf-8") == (
        "# Answers\n\n"
        "## Answers\n\n"
        "- `Q1` `[resolved]` The target release is 0.2.0.\n"
    )


def test_persist_operator_answer_preserves_partial_semantics(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    questions_view = persist_operator_answer(
        workspace_root=workspace_root,
        work_item="WI-UI",
        stage="plan",
        question_id="Q1",
        text="Release is not final yet.",
        resolution=AnswerResolution.PARTIAL,
    )

    assert questions_view.has_unresolved_blocking_questions is True
    assert questions_view.questions[0].status == "pending-blocking"
    assert questions_view.questions[0].answer_text is None
    assert questions_view.questions[0].answer_resolution is AnswerResolution.PARTIAL


def test_persist_operator_answer_rejects_unknown_question_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)

    with pytest.raises(ValueError, match="does not exist"):
        persist_operator_answer(
            workspace_root=workspace_root,
            work_item="WI-UI",
            stage="plan",
            question_id="Q404",
            text="Unknown answer.",
        )


def test_resolve_operator_questions_rejects_unknown_stage(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown stage"):
        resolve_operator_questions_view(
            workspace_root=tmp_path / ".aidd",
            work_item="WI-UI",
            stage="unknown",
        )


def test_runtime_readiness_view_uses_config_and_passed_probe_reports(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.generic_cli]",
                'command = "python -m fixture_runtime"',
                'mode = "adapter-flags"',
                "timeout_seconds = 42",
                "",
                "[runtime.generic_cli.stage_timeouts]",
                "plan = 90",
                "",
            )
        ),
        encoding="utf-8",
    )
    cfg = load_config(config_path)

    view = resolve_runtime_readiness(
        config=cfg,
        probe_reports={
            "generic-cli": RuntimeReadinessProbeReport(
                provider_available=True,
                execution_command_available=False,
                provider_version="Python 3.12.0",
                provider_command="/usr/bin/python",
            )
        },
        command_sources={
            "generic-cli": "config",
            "claude-code": "default",
            "codex": "default",
            "opencode": "default",
        },
    )

    runtimes = {runtime.runtime_id: runtime for runtime in view.runtimes}
    generic_cli = runtimes["generic-cli"]
    assert generic_cli.support_tier == "tier-1"
    assert generic_cli.command_source == "config"
    assert generic_cli.command == "python -m fixture_runtime"
    assert generic_cli.execution_mode == "adapter-flags"
    assert generic_cli.provider_available is True
    assert generic_cli.provider_version == "Python 3.12.0"
    assert generic_cli.provider_command == "/usr/bin/python"
    assert generic_cli.execution_command_available is False
    assert generic_cli.default_timeout_seconds == 42
    assert generic_cli.stage_timeout_seconds == {"plan": 90}
    assert runtimes["codex"].provider_available is False
    assert runtimes["codex"].command_source == "default"
