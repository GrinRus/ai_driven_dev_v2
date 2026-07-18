from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aidd.adapters.runtime_evidence import (
    RuntimeAdapterOutcome,
    RuntimeEvidenceCommitRequest,
    RuntimeStopReason,
    commit_runtime_evidence,
)
from aidd.core.interview import AdapterQuestionEvent, QuestionPolicy, persist_questions_document
from aidd.core.remediation import create_remediation_request, mark_downstream_stale
from aidd.core.repair import persist_repair_history_snapshot
from aidd.core.run_store import (
    OPERATOR_REQUESTS_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_root,
)
from aidd.core.runtime_operator import RuntimeOperatorRequest, append_operator_request
from aidd.core.stages import STAGES
from aidd.core.workspace import WorkspaceBootstrapService
from aidd.runtime_permissions import RuntimeOperatorRequestKind, RuntimeOperatorRisk
from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.reports import write_validator_report

WORK_ITEM = "WI-BROWSER"
RUN_ID = "run-browser"


@dataclass(frozen=True, slots=True)
class BrowserStateFixture:
    name: str
    project_root: Path
    workspace_root: Path
    work_item: str | None
    run_id: str | None
    expected_route_intent: str
    context_keys: tuple[str, ...]
    primary_surface: str
    primary_action: str
    state_marker: str
    api_path: str


def _descriptor(
    *,
    name: str,
    project_root: Path,
    route: str,
    context_keys: tuple[str, ...],
    surface: str,
    action: str,
    marker: str,
    work_item: str = WORK_ITEM,
    run_id: str = RUN_ID,
    with_run: bool = True,
) -> BrowserStateFixture:
    return BrowserStateFixture(
        name=name,
        project_root=project_root,
        workspace_root=project_root / ".aidd",
        work_item=work_item if name != "setup" else None,
        run_id=run_id if with_run else None,
        expected_route_intent=route,
        context_keys=context_keys,
        primary_surface=surface,
        primary_action=action,
        state_marker=marker,
        api_path=(
            "/api/onboarding/state"
            if name == "setup"
            else f"/api/dashboard?run_id={run_id}" if with_run else "/api/dashboard"
        ),
    )


def _bootstrap(project_root: Path, *, work_item: str) -> Path:
    workspace_root = project_root / ".aidd"
    service = WorkspaceBootstrapService(root=workspace_root)
    service.bootstrap_work_item(work_item)
    service.seed_request_context(
        work_item=work_item,
        request_text="Exercise the provider-free operator browser state.",
        project_root=project_root,
    )
    return workspace_root


def _create_run(
    workspace_root: Path,
    *,
    work_item: str,
    run_id: str,
    stage_target: str = "qa",
) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        runtime_id="generic-cli",
        stage_target=stage_target,
        config_snapshot={"mode": "browser-fixture"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )


def _attempt(workspace_root: Path, stage: str, *, work_item: str, run_id: str) -> Path:
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=1,
    )


def _write_qa_report(workspace_root: Path, verdict: str, *, work_item: str) -> None:
    qa_root = workspace_root / "workitems" / work_item / "stages" / "qa"
    qa_root.joinpath("qa-report.md").write_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "## Readiness",
                "",
                f"- QA verdict: `{verdict}`.",
                "",
                "## Residual risks",
                "",
                "- None.",
                "",
                "## Verification",
                "",
                "- Evidence: `runtime.log`.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _succeed_through(
    workspace_root: Path,
    final_stage: str,
    *,
    work_item: str,
    run_id: str,
) -> None:
    for stage in STAGES[: STAGES.index(final_stage) + 1]:
        attempt_root = _attempt(
            workspace_root,
            stage,
            work_item=work_item,
            run_id=run_id,
        )
        commit_runtime_evidence(
            RuntimeEvidenceCommitRequest(
                attempt_path=attempt_root,
                adapter_outcome=RuntimeAdapterOutcome.SUCCESS,
                exit_classification="success",
                exit_code=0,
                stdout_text=f"{stage} complete\n",
                stderr_text="",
                runtime_log_text=f"{stage} complete\n",
            )
        )
        persist_stage_status(workspace_root, work_item, run_id, stage, "succeeded")


def build_browser_state_fixture(
    project_root: Path,
    state: str,
    *,
    work_item: str = WORK_ITEM,
    run_id: str = RUN_ID,
) -> BrowserStateFixture:
    project_root.mkdir(parents=True, exist_ok=True)
    if state == "setup":
        return _descriptor(
            name=state,
            project_root=project_root,
            route="setup",
            context_keys=("project",),
            surface="Guided Setup",
            action="Validate project",
            marker="setup-required",
            with_run=False,
        )

    workspace_root = _bootstrap(project_root, work_item=work_item)
    if state == "no-run":
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item"),
            surface="Studio",
            action="Run workflow",
            marker="no-run",
            work_item=work_item,
            run_id=run_id,
            with_run=False,
        )

    _create_run(workspace_root, work_item=work_item, run_id=run_id)
    if state == "running":
        _attempt(workspace_root, "idea", work_item=work_item, run_id=run_id)
        persist_stage_status(workspace_root, work_item, run_id, "idea", "executing")
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt"),
            surface="Active Studio",
            action="Idea running",
            marker="wait-for-stage",
            work_item=work_item,
            run_id=run_id,
        )
    if state == "blocking-question":
        _attempt(workspace_root, "idea", work_item=work_item, run_id=run_id)
        persist_stage_status(workspace_root, work_item, run_id, "idea", "blocked")
        persist_questions_document(
            workspace_root=workspace_root,
            work_item=work_item,
            stage="idea",
            adapter_question_events=(
                AdapterQuestionEvent(
                    question_id="Q1",
                    policy=QuestionPolicy.BLOCKING,
                    text="Which acceptance boundary should the run preserve?",
                ),
            ),
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "recovery_target"),
            surface="Question Recovery",
            action="Answer required questions",
            marker="answer-questions",
            work_item=work_item,
            run_id=run_id,
        )
    runtime_failures = {
        "runtime-failure": (
            RuntimeAdapterOutcome.RUNTIME_FAILURE,
            RuntimeStopReason.RUNTIME_FAILURE,
            "provider_error",
            1,
        ),
        "runtime-launch-failure": (
            RuntimeAdapterOutcome.LAUNCH_FAILURE,
            RuntimeStopReason.LAUNCH_FAILURE,
            "launch_failure",
            None,
        ),
        "runtime-authentication-failure": (
            RuntimeAdapterOutcome.RUNTIME_FAILURE,
            RuntimeStopReason.RUNTIME_FAILURE,
            "authentication_failure",
            1,
        ),
        "runtime-timeout": (
            RuntimeAdapterOutcome.TIMEOUT,
            RuntimeStopReason.TIMEOUT,
            "timeout",
            124,
        ),
        "runtime-cancelled": (
            RuntimeAdapterOutcome.CANCELLATION,
            RuntimeStopReason.CANCELLATION,
            "cancelled",
            130,
        ),
        "runtime-no-progress": (
            RuntimeAdapterOutcome.RUNTIME_FAILURE,
            RuntimeStopReason.RUNTIME_FAILURE,
            "provider-no-progress",
            1,
        ),
    }
    if state in runtime_failures:
        outcome, stop_reason, classification, exit_code = runtime_failures[state]
        attempt_root = _attempt(
            workspace_root,
            "idea",
            work_item=work_item,
            run_id=run_id,
        )
        persist_stage_status(workspace_root, work_item, run_id, "idea", "failed")
        commit_runtime_evidence(
            RuntimeEvidenceCommitRequest(
                attempt_path=attempt_root,
                adapter_outcome=outcome,
                exit_classification=classification,
                exit_code=exit_code,
                stdout_text="",
                stderr_text=f"{classification}\n",
                runtime_log_text=f"{classification}\n",
                stop_reason=stop_reason,
            )
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt"),
            surface="Runtime Failure Recovery",
            action="Retry stage",
            marker=classification.replace("_", "-"),
            work_item=work_item,
            run_id=run_id,
        )
    if state in {"validation-repair", "validation-repair-exhausted"}:
        stage = "plan"
        attempt_root = _attempt(
            workspace_root,
            stage,
            work_item=work_item,
            run_id=run_id,
        )
        persist_stage_status(
            workspace_root,
            work_item,
            run_id,
            stage,
            "repair-needed" if state == "validation-repair" else "failed",
        )
        stage_root = workspace_root / "workitems" / work_item / "stages" / stage
        validator_report = stage_root / "validator-report.md"
        repair_brief = stage_root / "repair-brief.md"
        write_validator_report(
            path=validator_report,
            findings=(
                ValidationFinding(
                    code="STRUCT-MISSING-REQUIRED-SECTION",
                    message="Required verification section is missing.",
                    location=ValidationIssueLocation(
                        workspace_relative_path=(
                            f"workitems/{work_item}/stages/{stage}/plan.md"
                        ),
                        line_number=3,
                    ),
                ),
            ),
        )
        repair_brief.write_text(
            "# Repair Brief\n\nRestore the required verification section.\n",
            encoding="utf-8",
        )
        exhausted = state == "validation-repair-exhausted"
        persist_repair_history_snapshot(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=1,
            trigger="repair",
            outcome="repair budget exhausted" if exhausted else "failed validation",
            stage_status="failed" if exhausted else "repair-needed",
            validator_report_path=validator_report,
            repair_brief_path=repair_brief,
        )
        attempt_root.joinpath("runtime.log").write_text(
            "validation checkpoint reached\n",
            encoding="utf-8",
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt"),
            surface="Validation Recovery",
            action="Request Change" if exhausted else "Run Repair",
            marker="repair-exhausted" if exhausted else "repair-available",
            work_item=work_item,
            run_id=run_id,
        )
    if state == "pending-approval":
        attempt_root = _attempt(
            workspace_root,
            "idea",
            work_item=work_item,
            run_id=run_id,
        )
        persist_stage_status(workspace_root, work_item, run_id, "idea", "blocked")
        request = RuntimeOperatorRequest.create(
            runtime_id="generic-cli",
            stage="idea",
            kind=RuntimeOperatorRequestKind.SHELL,
            payload={"command": "python -m pytest -q"},
            risk=RuntimeOperatorRisk.MEDIUM,
        )
        append_operator_request(
            path=attempt_root / OPERATOR_REQUESTS_FILENAME,
            request=request,
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt", "recovery_target"),
            surface="Approval Recovery",
            action="Resume stage",
            marker="approval-waiting",
            work_item=work_item,
            run_id=run_id,
        )
    if state == "qa-decision":
        _succeed_through(
            workspace_root,
            "review",
            work_item=work_item,
            run_id=run_id,
        )
        attempt_root = _attempt(
            workspace_root,
            "qa",
            work_item=work_item,
            run_id=run_id,
        )
        commit_runtime_evidence(
            RuntimeEvidenceCommitRequest(
                attempt_path=attempt_root,
                adapter_outcome=RuntimeAdapterOutcome.SUCCESS,
                exit_classification="success",
                exit_code=0,
                stdout_text="qa evidence collected\n",
                stderr_text="",
                runtime_log_text="qa evidence collected\n",
            )
        )
        persist_stage_status(workspace_root, work_item, run_id, "qa", "succeeded")
        _write_qa_report(workspace_root, "not-ready", work_item=work_item)
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "document"),
            surface="Quality Gate",
            action="QA Verdict",
            marker="qa-report.md",
            work_item=work_item,
            run_id=run_id,
        )
    if state == "remediation-stale":
        _succeed_through(
            workspace_root,
            "qa",
            work_item=work_item,
            run_id=run_id,
        )
        _write_qa_report(workspace_root, "ready", work_item=work_item)
        request = create_remediation_request(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            source_stage="qa",
            source_ids=("QA-RISK-1",),
            operator_note="Re-run implementation evidence for the selected risk.",
        )
        mark_downstream_stale(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            invalidated_by=request.request_id,
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "recovery_target"),
            surface="Remediation Recovery",
            action="Rerun stale downstream",
            marker="rerun-stale-downstream",
            work_item=work_item,
            run_id=run_id,
        )
    if state == "terminal-handoff":
        _succeed_through(
            workspace_root,
            "qa",
            work_item=work_item,
            run_id=run_id,
        )
        _write_qa_report(workspace_root, "ready", work_item=work_item)
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "document"),
            surface="Flow Complete",
            action="Start Next Flow",
            marker="review-complete",
            work_item=work_item,
            run_id=run_id,
        )
    raise ValueError(f"Unknown browser fixture state: {state}")


BROWSER_FIXTURE_STATES = (
    "setup",
    "no-run",
    "running",
    "blocking-question",
    "runtime-failure",
    "runtime-launch-failure",
    "runtime-authentication-failure",
    "runtime-timeout",
    "runtime-cancelled",
    "runtime-no-progress",
    "validation-repair",
    "validation-repair-exhausted",
    "pending-approval",
    "qa-decision",
    "remediation-stale",
    "terminal-handoff",
)
