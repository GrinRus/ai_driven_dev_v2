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
    with_run: bool = True,
) -> BrowserStateFixture:
    return BrowserStateFixture(
        name=name,
        project_root=project_root,
        workspace_root=project_root / ".aidd",
        work_item=WORK_ITEM if name != "setup" else None,
        run_id=RUN_ID if with_run else None,
        expected_route_intent=route,
        context_keys=context_keys,
        primary_surface=surface,
        primary_action=action,
        state_marker=marker,
        api_path=(
            "/api/onboarding/state"
            if name == "setup"
            else f"/api/dashboard?run_id={RUN_ID}" if with_run else "/api/dashboard"
        ),
    )


def _bootstrap(project_root: Path) -> Path:
    workspace_root = project_root / ".aidd"
    service = WorkspaceBootstrapService(root=workspace_root)
    service.bootstrap_work_item(WORK_ITEM)
    service.seed_request_context(
        work_item=WORK_ITEM,
        request_text="Exercise the provider-free operator browser state.",
        project_root=project_root,
    )
    return workspace_root


def _create_run(workspace_root: Path, *, stage_target: str = "qa") -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        runtime_id="generic-cli",
        stage_target=stage_target,
        config_snapshot={"mode": "browser-fixture"},
        workflow_stage_start="idea",
        workflow_stage_end="qa",
    )


def _attempt(workspace_root: Path, stage: str) -> Path:
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        stage=stage,
    )
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=WORK_ITEM,
        run_id=RUN_ID,
        stage=stage,
        attempt_number=1,
    )


def _write_qa_report(workspace_root: Path, verdict: str) -> None:
    qa_root = workspace_root / "workitems" / WORK_ITEM / "stages" / "qa"
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


def _succeed_through(workspace_root: Path, final_stage: str) -> None:
    for stage in STAGES[: STAGES.index(final_stage) + 1]:
        attempt_root = _attempt(workspace_root, stage)
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
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, stage, "succeeded")


def build_browser_state_fixture(project_root: Path, state: str) -> BrowserStateFixture:
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

    workspace_root = _bootstrap(project_root)
    if state == "no-run":
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item"),
            surface="Studio",
            action="Run workflow",
            marker="no-run",
            with_run=False,
        )

    _create_run(workspace_root)
    if state == "running":
        _attempt(workspace_root, "idea")
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, "idea", "executing")
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt"),
            surface="Active Studio",
            action="Idea running",
            marker="wait-for-stage",
        )
    if state == "blocking-question":
        _attempt(workspace_root, "idea")
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, "idea", "blocked")
        persist_questions_document(
            workspace_root=workspace_root,
            work_item=WORK_ITEM,
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
        )
    if state == "runtime-failure":
        attempt_root = _attempt(workspace_root, "idea")
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, "idea", "failed")
        commit_runtime_evidence(
            RuntimeEvidenceCommitRequest(
                attempt_path=attempt_root,
                adapter_outcome=RuntimeAdapterOutcome.RUNTIME_FAILURE,
                exit_classification="provider_error",
                exit_code=1,
                stdout_text="",
                stderr_text="provider failed\n",
                runtime_log_text="provider failed\n",
                stop_reason=RuntimeStopReason.RUNTIME_FAILURE,
            )
        )
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "attempt"),
            surface="Runtime Failure Recovery",
            action="Retry stage",
            marker="resume-stage",
        )
    if state == "pending-approval":
        attempt_root = _attempt(workspace_root, "idea")
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, "idea", "blocked")
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
        )
    if state == "qa-decision":
        _succeed_through(workspace_root, "review")
        attempt_root = _attempt(workspace_root, "qa")
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
        persist_stage_status(workspace_root, WORK_ITEM, RUN_ID, "qa", "succeeded")
        _write_qa_report(workspace_root, "not-ready")
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "document"),
            surface="Quality Gate",
            action="QA Verdict",
            marker="qa-report.md",
        )
    if state == "remediation-stale":
        _succeed_through(workspace_root, "qa")
        _write_qa_report(workspace_root, "ready")
        request = create_remediation_request(
            workspace_root=workspace_root,
            work_item=WORK_ITEM,
            run_id=RUN_ID,
            source_stage="qa",
            source_ids=("QA-RISK-1",),
            operator_note="Re-run implementation evidence for the selected risk.",
        )
        mark_downstream_stale(
            workspace_root=workspace_root,
            work_item=WORK_ITEM,
            run_id=RUN_ID,
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
        )
    if state == "terminal-handoff":
        _succeed_through(workspace_root, "qa")
        _write_qa_report(workspace_root, "ready")
        return _descriptor(
            name=state,
            project_root=project_root,
            route="studio",
            context_keys=("project", "work_item", "run", "stage", "document"),
            surface="Flow Complete",
            action="Start Next Flow",
            marker="review-complete",
        )
    raise ValueError(f"Unknown browser fixture state: {state}")


BROWSER_FIXTURE_STATES = (
    "setup",
    "no-run",
    "running",
    "blocking-question",
    "runtime-failure",
    "pending-approval",
    "qa-decision",
    "remediation-stale",
    "terminal-handoff",
)
