from __future__ import annotations

import json
import shlex
import sys
import threading
import time
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any

import typer

from aidd.cli import main as cli_main
from aidd.cli.stage_run import StageInteractOptions, StageRunOptions
from aidd.cli.ui import (
    OperatorUiService,
    UiRequestBodyTooLarge,
    UiServerOptions,
    _is_loopback_host,
    _read_json_body,
)
from aidd.cli.ui_assets import operator_static_asset_for_route, operator_static_asset_manifest
from aidd.core.run_store import (
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_runtime_log_path,
)
from aidd.core.runtime_operator import (
    RuntimeOperatorBroker,
    RuntimeOperatorDecision,
    RuntimeOperatorPolicy,
    RuntimeOperatorRequest,
    append_operator_request,
)
from aidd.core.runtime_readiness import RuntimeReadinessProbeReport
from aidd.core.stage_runner import prepare_stage_bundle
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
)
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimePermissionPolicy,
)


def _service(
    workspace_root: Path,
    *,
    config: Path | None = None,
    workflow_runner: Any | None = None,
    stage_runner: Any | None = None,
    stage_interact_runner: Any | None = None,
    readiness_probe_provider: Any | None = None,
    folder_opener: Any | None = None,
    host: str = "127.0.0.1",
    allow_remote_approvals: bool = False,
) -> OperatorUiService:
    options = UiServerOptions(
        work_item="WI-UI",
        root=workspace_root,
        config=config or Path("aidd.test.toml"),
        host=host,
        port=0,
        allow_remote_approvals=allow_remote_approvals,
    )
    kwargs: dict[str, Any] = {}
    if workflow_runner is not None:
        kwargs["workflow_runner"] = workflow_runner
    if stage_runner is not None:
        kwargs["stage_runner"] = stage_runner
    if stage_interact_runner is not None:
        kwargs["stage_interact_runner"] = stage_interact_runner
    if readiness_probe_provider is not None:
        kwargs["readiness_probe_provider"] = readiness_probe_provider
    if folder_opener is not None:
        kwargs["folder_opener"] = folder_opener
    return OperatorUiService(options, **kwargs)


def _payload(response) -> dict[str, object]:
    assert response.status == 200
    return json.loads(response.body.decode("utf-8"))


def _error_payload(response) -> dict[str, object]:
    assert response.status >= 400
    return json.loads(response.body.decode("utf-8"))


def _wait_job(service: OperatorUiService, job_id: str) -> dict[str, object]:
    for _ in range(100):
        payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
        if payload["status"] != "running":
            return payload
        time.sleep(0.01)
    raise AssertionError(f"job did not finish: {job_id}")


def _wait_job_status(
    service: OperatorUiService,
    job_id: str,
    expected_status: str,
) -> dict[str, object]:
    for _ in range(100):
        payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
        if payload["status"] == expected_status:
            return payload
        time.sleep(0.01)
    raise AssertionError(f"job did not reach {expected_status}: {job_id}")


def _operator_script_bundle(service: OperatorUiService) -> str:
    return "\n".join(
        service.handle_get(asset.route, {}).body.decode("utf-8")
        for asset in operator_static_asset_manifest()
        if asset.content_type == "text/javascript; charset=utf-8"
    )


def _operator_css_bundle(service: OperatorUiService) -> str:
    return "\n".join(
        service.handle_get(asset.route, {}).body.decode("utf-8")
        for asset in operator_static_asset_manifest()
        if asset.content_type == "text/css; charset=utf-8"
    )


class _BodyHandler:
    def __init__(self, body: bytes, *, content_length: str | None = None) -> None:
        self.headers = {"Content-Length": content_length or str(len(body))}
        self.rfile = BytesIO(body)


def _prepare_run(workspace_root: Path) -> None:
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "ui-test"},
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
    stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n"
        "## Result\n\n"
        "- Verdict: `fail`\n",
        encoding="utf-8",
    )
    stage_root.joinpath("stage-result.md").write_text(
        "# Stage Result\n\n"
        "## Summary\n\n"
        "Blocked on clarification.\n",
        encoding="utf-8",
    )
    stage_root.joinpath("plan.md").write_text(
        "# Plan\n\n"
        "## Goals\n\n"
        "- Keep stage primary output visible in the operator UI.\n",
        encoding="utf-8",
    )
    stage_root.joinpath("repair-brief.md").write_text(
        "# Failed checks\n\n"
        "- `SEM-INCOMPLETE-SECTION` `medium` in "
        "`workitems/WI-UI/stages/plan/plan.md`: Missing validation evidence.\n",
        encoding="utf-8",
    )


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
                "- `Q1` `[blocking]` Confirm release target.",
                "",
            )
        ),
        encoding="utf-8",
    )


def _materialize_plan_inputs(*, workspace_root: Path, work_item: str) -> None:
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
    )
    for index, path in enumerate(bundle.expected_input_bundle, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Input {index}\n\nPrepared for UI cancellation.\n", encoding="utf-8")


def _write_ui_runtime_config(*, tmp_path: Path, runtime_command: str) -> Path:
    config_path = tmp_path / "aidd.ui.test.toml"
    config_path.write_text(
        "\n".join(
            (
                "[workspace]",
                'root = ".aidd"',
                "",
                "[runtime.generic_cli]",
                f"command = {json.dumps(runtime_command)}",
                'mode = "adapter-flags"',
                "",
                "[repair]",
                "max_attempts = 0",
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path


def _write_long_running_runtime_script(tmp_path: Path) -> Path:
    script_path = tmp_path / "long_running_runtime.py"
    script_path.write_text(
        "\n".join(
            (
                "import os",
                "import signal",
                "import sys",
                "import time",
                "from pathlib import Path",
                "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
                "root.mkdir(parents=True, exist_ok=True)",
                "(root / 'long-runtime-started.txt').write_text('started\\n', encoding='utf-8')",
                "def _stop(signum, frame):",
                "    print('long-runtime-sigterm', flush=True)",
                "    stopped = root / 'long-runtime-stopped.txt'",
                "    stopped.write_text('sigterm\\n', encoding='utf-8')",
                "    raise SystemExit(130)",
                "signal.signal(signal.SIGTERM, _stop)",
                "print('long-runtime-start', flush=True)",
                "while True:",
                "    time.sleep(0.05)",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return script_path


def test_ui_service_exposes_private_read_endpoints(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)
    service = _service(workspace_root)

    run_payload = _payload(service.handle_get("/api/run", {}))
    stage_payload = _payload(service.handle_get("/api/stage", {"stage": ["plan"]}))
    logs_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"]}))
    artifacts_payload = _payload(service.handle_get("/api/artifacts", {"stage": ["plan"]}))

    assert run_payload["metadata"]["runtime_id"] == "generic-cli"
    assert stage_payload["result"]["final_state"] == "blocked"
    assert stage_payload["result"]["validator_fail_count"] == 1
    assert stage_payload["result"]["repair_output_paths"] == [
        "workitems/WI-UI/stages/plan/repair-brief.md"
    ]
    assert logs_payload["text"] == "runtime-line\n"
    assert logs_payload["truncated"] is False
    assert logs_payload["byte_size"] == len(b"runtime-line\n")
    assert artifacts_payload["documents"]["input_bundle"].endswith("input-bundle.md")


def test_ui_logs_endpoint_defaults_to_bounded_tail_and_accepts_limit_params(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    runtime_log_path = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    log_text = "".join(f"line-{index:05d}\n" for index in range(10000))
    runtime_log_path.write_text(log_text, encoding="utf-8")
    byte_size = len(log_text.encode("utf-8"))
    service = _service(workspace_root)

    default_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"]}))
    tail_payload = _payload(
        service.handle_get("/api/logs", {"stage": ["plan"], "tail": ["128"]})
    )
    limit_payload = _payload(
        service.handle_get("/api/logs", {"stage": ["plan"], "limit": ["128"]})
    )
    invalid_payload = service.handle_get(
        "/api/logs",
        {"stage": ["plan"], "tail": ["0"]},
    )

    assert default_payload["byte_size"] == byte_size
    assert default_payload["requested_bytes"] == 64 * 1024
    assert default_payload["start_byte"] == byte_size - (64 * 1024)
    assert default_payload["end_byte"] == byte_size
    assert default_payload["truncated"] is True
    assert default_payload["truncated_head"] is True
    assert default_payload["truncated_tail"] is False
    assert len(str(default_payload["text"]).encode("utf-8")) < byte_size

    assert tail_payload["start_byte"] == byte_size - 128
    assert tail_payload["end_byte"] == byte_size
    assert tail_payload["truncated_head"] is True
    assert tail_payload["truncated_tail"] is False
    assert str(tail_payload["text"]).endswith("line-09999\n")

    assert limit_payload["start_byte"] == 0
    assert limit_payload["end_byte"] == 128
    assert limit_payload["truncated_head"] is False
    assert limit_payload["truncated_tail"] is True
    assert str(limit_payload["text"]).startswith("line-00000\n")

    assert invalid_payload.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(invalid_payload)["error"] == "tail must be greater than zero."


def test_ui_dashboard_endpoint_exposes_operator_console_payload(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/dashboard", {"stage": ["plan"]}))

    assert isinstance(payload["app_version"], str)
    dashboard = payload["dashboard"]
    assert dashboard["work_item"] == "WI-UI"  # type: ignore[index]
    assert dashboard["active_stage"] == "plan"  # type: ignore[index]
    assert dashboard["run"]["run_id"] == "run-ui"  # type: ignore[index]
    assert dashboard["next_action"]["action"] == "answer-questions"  # type: ignore[index]
    assert dashboard["primary_artifact"]["key"] == "plan"  # type: ignore[index]
    assert any(
        artifact["path"] == "workitems/WI-UI/stages/plan/plan.md"
        for artifact in dashboard["recent_artifacts"]  # type: ignore[index]
    )


def test_ui_static_asset_routes_are_served_from_manifest(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    for manifest_asset in operator_static_asset_manifest():
        response = service.handle_get(manifest_asset.route, {})
        asset = operator_static_asset_for_route(manifest_asset.route)
        assert asset is not None
        assert response.content_type == asset.content_type
        assert response.body.decode("utf-8") == asset.text


def test_ui_run_endpoint_uses_empty_state_when_no_run_exists(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/run", {}))

    assert payload["metadata"] is None
    assert payload["message"] == "No runs found for work item 'WI-UI'."


def test_ui_dashboard_endpoint_uses_empty_state_when_no_run_exists(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/dashboard", {}))

    dashboard = payload["dashboard"]
    assert dashboard["run"]["run_id"] is None  # type: ignore[index]
    assert dashboard["next_action"]["action"] == "choose-runtime"  # type: ignore[index]
    assert dashboard["stages"][0]["stage"] == "idea"  # type: ignore[index]


def test_ui_service_persists_answer_through_operator_service(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_questions(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/answers",
        {
            "stage": "plan",
            "question_id": "Q1",
            "text": "Release target is 0.2.0.",
        },
    )

    payload = _payload(response)
    assert payload["unresolved_blocking_question_ids"] == []
    assert payload["questions"][0]["status"] == "resolved"  # type: ignore[index]
    assert payload["questions"][0]["answer_text"] == "Release target is 0.2.0."  # type: ignore[index]
    assert payload["questions"][0]["answer_resolution"] == "resolved"  # type: ignore[index]
    answers_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "answers.md"
    assert "Release target is 0.2.0." in answers_path.read_text(encoding="utf-8")


def test_ui_service_hardening_regression_metadata_surface(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)
    runtime_log_path = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    runtime_log_path.write_text("log-line\n" * 20000, encoding="utf-8")
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    plan_path.write_text("# Plan\n\n" + ("A" * (300 * 1024)), encoding="utf-8")

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        return WorkflowRunResult(
            run_id="run-ui-hardening",
            executed_stage_count=0,
            completed=True,
            incomplete=(),
        )

    service = _service(workspace_root, workflow_runner=fake_workflow_runner)

    run_payload = _payload(service.handle_post("/api/workflow/run", {"runtime": "codex"}))
    job_id = str(run_payload["job_id"])
    completed_payload = _wait_job(service, job_id)
    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))
    logs_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"]}))
    artifact_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["plan"],
                "mode": ["source"],
                "limit": ["999999"],
            },
        )
    )
    answer_payload = _payload(
        service.handle_post(
            "/api/answers",
            {
                "stage": "plan",
                "question_id": "Q1",
                "text": "Release target is local-alpha.",
            },
        )
    )

    assert completed_payload["status"] == "completed"
    assert cancel_payload["cancel_state"] == "already-finished"
    assert logs_payload["truncated"] is True
    assert logs_payload["truncated_head"] is True
    assert artifact_payload["truncated"] is True
    assert artifact_payload["max_bytes"] == 256 * 1024
    assert answer_payload["questions"][0]["answer_text"] == "Release target is local-alpha."  # type: ignore[index]


def test_ui_workflow_run_endpoint_delegates_through_internal_seam(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    captured: dict[str, object] = {}

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        captured.update(kwargs)
        request = kwargs["request"]
        assert isinstance(request, WorkflowRunRequest)
        return WorkflowRunResult(
            run_id="run-ui-seam",
            executed_stage_count=1,
            completed=True,
            incomplete=(),
        )

    service = _service(workspace_root, workflow_runner=fake_workflow_runner)

    response = service.handle_post(
        "/api/workflow/run",
        {
            "runtime": "codex",
            "from_stage": "research",
            "to_stage": "plan",
            "run_id": "run-ui-existing",
            "log_follow": True,
        },
    )

    payload = _payload(response)
    job_payload = _wait_job(service, str(payload["job_id"]))
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert payload["kind"] == "workflow"
    assert job_payload["status"] == "completed"
    assert job_payload["result"]["run_id"] == "run-ui-seam"  # type: ignore[index]
    assert job_payload["result"]["completed"] is True  # type: ignore[index]
    assert request.work_item == "WI-UI"
    assert request.runtime_id == "codex"
    assert request.run_id == "run-ui-existing"
    assert request.stage_start == "research"
    assert request.stage_end == "plan"
    assert request.log_follow is True
    assert "stage_executor" in captured


def test_ui_next_flow_preflight_endpoint_returns_launchable_warning_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/preflight",
        {"source_run_id": "run-ui", "runtime": "generic-cli"},
    )

    payload = _payload(response)
    preflight = payload["preflight"]
    assert preflight["status"] == "warning"  # type: ignore[index]
    assert preflight["can_launch"] is True  # type: ignore[index]
    assert preflight["blocking_codes"] == []  # type: ignore[index]
    assert preflight["warning_codes"] == ["baseline-fallback-source-run"]  # type: ignore[index]
    assert preflight["resolved_baseline_id"] == "run-ui"  # type: ignore[index]


def test_ui_next_flow_preflight_endpoint_returns_structured_blocking_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/preflight",
        {
            "source_run_id": "run-missing",
            "runtime": "unknown-runtime",
            "contracts_root": (tmp_path / "missing" / "contracts" / "stages").as_posix(),
        },
    )

    assert response.status == HTTPStatus.CONFLICT
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["error"] == "next-flow launch preflight blocked"
    assert set(payload["blocking_codes"]) == {
        "workspace-missing",
        "unsupported-runtime",
        "contracts-missing",
        "source-run-missing",
    }
    assert any(
        check["code"] == "unsupported-runtime" and check["severity"] == "blocking"
        for check in payload["checks"]
    )


def test_ui_workflow_stage_executor_passes_cancel_callback(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()
    observed_cancel = threading.Event()

    def fake_stage_runner(options: StageRunOptions) -> None:
        assert options.cancel_requested is not None
        started.set()
        assert release.wait(timeout=2)
        if options.cancel_requested():
            observed_cancel.set()
        raise typer.Exit(1)

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        request = kwargs["request"]
        assert isinstance(request, WorkflowRunRequest)
        stage_executor = kwargs["stage_executor"]
        assert callable(stage_executor)
        try:
            stage_executor(
                WorkflowStageExecutionRequest(
                    stage="plan",
                    work_item=request.work_item,
                    runtime_id=request.runtime_id,
                    run_id="run-ui-workflow-cancel",
                    workspace_root=request.workspace_root,
                    config_path=request.config_path,
                    log_follow=request.log_follow,
                )
            )
        except WorkflowStageExecutionError as exc:
            assert exc.exit_code == 1
        return WorkflowRunResult(
            run_id="run-ui-workflow-cancel",
            executed_stage_count=1,
            completed=False,
            incomplete=(),
            stopped_stage="plan",
            exit_code=1,
        )

    service = _service(
        workspace_root,
        workflow_runner=fake_workflow_runner,
        stage_runner=fake_stage_runner,
    )

    response = service.handle_post(
        "/api/workflow/run",
        {"runtime": "codex", "from_stage": "plan", "to_stage": "plan"},
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    assert started.wait(timeout=2)
    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))
    assert cancel_payload["status"] == "cancelling"
    release.set()

    cancelled_payload = _wait_job_status(service, job_id, "cancelled")
    assert observed_cancel.wait(timeout=2)
    assert cancelled_payload["cancel_state"] == "cancelled"


def test_ui_stage_run_endpoint_delegates_selected_stage_and_streams_live_logs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()
    captured: dict[str, object] = {}

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured["options"] = options
        assert options.runtime_chunk_sink is not None
        options.runtime_chunk_sink("stdout", "runtime-output-line\n")
        started.set()
        assert release.wait(timeout=2)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/stage/run",
        {
            "stage": "plan",
            "runtime": "codex",
            "run_id": "run-ui-flow",
            "log_follow": True,
        },
    )

    payload = _payload(response)
    assert payload["kind"] == "stage"
    assert payload["stage"] == "plan"
    assert started.wait(timeout=2)

    job_id = str(payload["job_id"])
    running_payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
    logs_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/logs", {"cursor": ["0"]}))
    options = captured["options"]
    assert isinstance(options, StageRunOptions)
    assert running_payload["status"] == "running"
    assert options.stage == "plan"
    assert options.runtime == "codex"
    assert options.run_id == "run-ui-flow"
    assert options.log_follow is True
    assert options.cancel_requested is not None
    assert options.cancel_requested() is False
    assert any(
        chunk["stream"] == "stdout" and chunk["text"] == "runtime-output-line\n"
        for chunk in logs_payload["chunks"]  # type: ignore[index]
    )

    release.set()
    completed_payload = _wait_job(service, job_id)
    assert completed_payload["status"] == "completed"
    assert completed_payload["result"]["completed"] is True  # type: ignore[index]


def test_ui_job_cancel_endpoint_marks_running_job_cancelling_then_cancelled(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()
    observed_cancel = threading.Event()

    def fake_stage_runner(options: StageRunOptions) -> None:
        assert options.runtime_chunk_sink is not None
        options.runtime_chunk_sink("stdout", "runtime-output-line\n")
        started.set()
        assert release.wait(timeout=2)
        assert options.cancel_requested is not None
        if options.cancel_requested():
            observed_cancel.set()

    service = _service(workspace_root, stage_runner=fake_stage_runner)
    response = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex", "run_id": "run-ui-cancel"},
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    assert started.wait(timeout=2)
    running_payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
    assert running_payload["status"] == "running"
    assert running_payload["cancel_state"] == "none"

    cancel_payload = _payload(
        service.handle_post(f"/api/jobs/{job_id}/cancel", {})
    )

    assert cancel_payload["status"] == "cancelling"
    assert cancel_payload["cancel_state"] == "cancelling"
    assert cancel_payload["previous_status"] == "running"
    assert cancel_payload["already_finished"] is False
    assert cancel_payload["cancel_requested"] is True
    assert cancel_payload["exit_code"] is None

    logs_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/logs", {"cursor": ["0"]}))
    assert any(
        chunk["stream"] == "stdout" and chunk["text"] == "runtime-output-line\n"
        for chunk in logs_payload["chunks"]  # type: ignore[index]
    )
    assert any(
        chunk["stream"] == "system" and "cancel requested" in str(chunk["text"])
        for chunk in logs_payload["chunks"]  # type: ignore[index]
    )

    release.set()
    cancelled_payload = _wait_job_status(service, job_id, "cancelled")
    assert observed_cancel.wait(timeout=2)
    assert cancelled_payload["exit_code"] == 130
    assert cancelled_payload["cancel_state"] == "cancelled"
    assert cancelled_payload["cancel_requested"] is True
    assert cancelled_payload["cancelled_at_utc"] is not None
    assert cancelled_payload["result"] is None


def test_ui_cancel_terminates_generic_cli_runtime_and_records_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    run_id = "run-ui-runtime-cancel"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-UI")
    runtime_script = _write_long_running_runtime_script(tmp_path)
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(runtime_script.as_posix())}"
    )
    config_path = _write_ui_runtime_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
    )
    service = _service(workspace_root, config=config_path)

    response = service.handle_post(
        "/api/stage/run",
        {
            "stage": "plan",
            "runtime": "generic-cli",
            "run_id": run_id,
            "log_follow": True,
        },
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    for _ in range(100):
        logs_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/logs", {"cursor": ["0"]}))
        if any("long-runtime-start" in str(chunk["text"]) for chunk in logs_payload["chunks"]):  # type: ignore[index]
            break
        time.sleep(0.01)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("runtime did not start")

    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))
    assert cancel_payload["status"] == "cancelling"

    cancelled_payload = _wait_job_status(service, job_id, "cancelled")
    assert cancelled_payload["cancel_state"] == "cancelled"
    assert cancelled_payload["exit_code"] == 130

    attempt_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-UI"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
    )
    runtime_exit = json.loads(
        (attempt_path / RUN_RUNTIME_EXIT_METADATA_FILENAME).read_text(encoding="utf-8")
    )
    stage_metadata = json.loads(
        (
            workspace_root
            / "reports"
            / "runs"
            / "WI-UI"
            / run_id
            / "stages"
            / "plan"
            / "stage-metadata.json"
        )
        .read_text(encoding="utf-8")
    )
    assert runtime_exit["exit_classification"] == "cancelled"
    assert stage_metadata["status"] == "failed"


def test_ui_job_cancel_endpoint_reports_completed_job_as_already_finished(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        return WorkflowRunResult(
            run_id="run-ui-already-finished",
            executed_stage_count=1,
            completed=True,
            incomplete=(),
        )

    service = _service(workspace_root, workflow_runner=fake_workflow_runner)
    response = service.handle_post(
        "/api/workflow/run",
        {"runtime": "codex", "from_stage": "idea", "to_stage": "plan"},
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    completed_payload = _wait_job(service, job_id)
    assert completed_payload["status"] == "completed"

    cancel_payload = _payload(
        service.handle_post(f"/api/jobs/{job_id}/cancel", {})
    )

    assert cancel_payload["status"] == "completed"
    assert cancel_payload["cancel_state"] == "already-finished"
    assert cancel_payload["previous_status"] == "completed"
    assert cancel_payload["already_finished"] is True
    assert cancel_payload["cancel_requested"] is False
    assert cancel_payload["result"]["run_id"] == "run-ui-already-finished"  # type: ignore[index]


def test_ui_job_operator_request_endpoints_record_decisions(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    request_ref: dict[str, RuntimeOperatorRequest] = {}

    def fake_stage_runner(options: StageRunOptions) -> None:
        run_id = options.run_id or "run-ui-approval"
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            runtime_id=options.runtime,
            stage_target=options.stage,
            config_snapshot={"mode": "ui-approval-test"},
        )
        attempt_path = create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            stage=options.stage,
        )
        request = RuntimeOperatorRequest.create(
            runtime_id=options.runtime,
            stage=options.stage,
            kind=RuntimeOperatorRequestKind.SHELL,
            payload={"command": "npm install"},
            cwd=tmp_path,
        )
        request_ref["request"] = request
        append_operator_request(path=attempt_path / "operator-requests.jsonl", request=request)
        raise typer.Exit(1)

    service = _service(workspace_root, stage_runner=fake_stage_runner)
    response = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex", "run_id": "run-ui-approval"},
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    job_payload = _wait_job(service, job_id)
    assert job_payload["status"] == "waiting-for-operator"

    request_id = request_ref["request"].id
    pending_payload = _payload(
        service.handle_get(f"/api/jobs/{job_id}/operator-requests", {})
    )
    assert pending_payload["pending_request_ids"] == [request_id]

    decision_payload = _payload(
        service.handle_post(
            f"/api/jobs/{job_id}/operator-requests/{request_id}/decision",
            {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
        )
    )

    assert decision_payload["pending_request_ids"] == []
    assert decision_payload["unapproved_request_ids"] == []
    assert decision_payload["decisions"][0]["source"] == "ui"  # type: ignore[index]
    assert (
        workspace_root
        / "reports"
        / "runs"
        / "WI-UI"
        / "run-ui-approval"
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / "operator-decisions.jsonl"
    ).exists()


def test_ui_operator_decision_endpoint_wakes_live_stage_job(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    request_ready = threading.Event()
    captured: dict[str, RuntimeOperatorDecision | RuntimeOperatorRequest] = {}

    def fake_stage_runner(options: StageRunOptions) -> None:
        run_id = options.run_id or "run-ui-live-approval"
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            runtime_id=options.runtime,
            stage_target=options.stage,
            config_snapshot={"mode": "ui-live-approval-test"},
        )
        attempt_path = create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            stage=options.stage,
        )
        request = RuntimeOperatorRequest.create(
            runtime_id=options.runtime,
            stage=options.stage,
            kind=RuntimeOperatorRequestKind.SHELL,
            payload={"command": "python -m pytest -q"},
            cwd=tmp_path,
        )
        captured["request"] = request
        broker = RuntimeOperatorBroker(
            policy=RuntimeOperatorPolicy(
                permission_policy=RuntimePermissionPolicy.BROKERED,
                auto_approval_preset=AutoApprovalPreset.OFF,
                project_roots=(tmp_path,),
                workspace_root=workspace_root,
            ),
            attempt_path=attempt_path,
        )
        request_ready.set()
        decision = broker.handle_request(
            request,
            decision_provider=options.runtime_operator_decision_provider,
        )
        assert decision is not None
        captured["decision"] = decision

    service = _service(workspace_root, stage_runner=fake_stage_runner)
    response = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex", "run_id": "run-ui-live-approval"},
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    assert request_ready.wait(timeout=2)
    for _ in range(100):
        waiting_payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
        if waiting_payload["status"] == "waiting-for-operator":
            break
        time.sleep(0.01)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("job did not enter waiting-for-operator")

    request = captured["request"]
    assert isinstance(request, RuntimeOperatorRequest)
    pending_payload = _payload(
        service.handle_get(f"/api/jobs/{job_id}/operator-requests", {})
    )
    assert pending_payload["pending_request_ids"] == [request.id]

    decision_payload = _payload(
        service.handle_post(
            f"/api/jobs/{job_id}/operator-requests/{request.id}/decision",
            {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
        )
    )
    assert decision_payload["pending_request_ids"] == []

    completed_payload = _wait_job(service, job_id)
    decision = captured["decision"]
    assert isinstance(decision, RuntimeOperatorDecision)
    assert completed_payload["status"] == "completed"
    assert decision.action is RuntimeOperatorDecisionAction.ALLOW_ONCE


def test_ui_remote_mutations_require_loopback_host(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd", host="0.0.0.0")

    denied = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex", "run_id": "run-ui-remote-approval"},
    )

    assert denied.status == HTTPStatus.FORBIDDEN
    assert "remote UI mutations require loopback" in _error_payload(denied)["error"]  # type: ignore[operator]


def test_ui_remote_operator_decision_endpoint_allows_explicit_opt_in(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    service = _service(
        workspace_root,
        host="0.0.0.0",
        allow_remote_approvals=True,
    )

    response = service.handle_post(
        "/api/jobs/job-missing/operator-requests/request-missing/decision",
        {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert "Unknown UI job" in _error_payload(response)["error"]  # type: ignore[operator]


def test_ui_stage_interact_endpoint_delegates_request_and_streams_logs(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()
    captured: dict[str, object] = {}

    def fake_stage_interact_runner(options: StageInteractOptions) -> None:
        captured["options"] = options
        assert options.runtime_chunk_sink is not None
        options.runtime_chunk_sink("stdout", "intervention-output-line\n")
        started.set()
        assert release.wait(timeout=2)

    service = _service(
        workspace_root,
        stage_interact_runner=fake_stage_interact_runner,
    )

    response = service.handle_post(
        "/api/stage/interact",
        {
            "stage": "plan",
            "runtime": "codex",
            "run_id": "run-ui-flow",
            "request": "Add migration rollback risks",
            "target_documents": ["workitems/WI-UI/stages/plan/plan.md"],
            "log_follow": True,
        },
    )

    payload = _payload(response)
    assert payload["kind"] == "intervention"
    assert payload["stage"] == "plan"
    assert started.wait(timeout=2)

    job_id = str(payload["job_id"])
    logs_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/logs", {"cursor": ["0"]}))
    options = captured["options"]
    assert isinstance(options, StageInteractOptions)
    assert options.stage == "plan"
    assert options.runtime == "codex"
    assert options.run_id == "run-ui-flow"
    assert options.request == "Add migration rollback risks"
    assert options.target_documents == ("workitems/WI-UI/stages/plan/plan.md",)
    assert options.cancel_requested is not None
    assert options.cancel_requested() is False
    assert any(
        chunk["stream"] == "stdout" and chunk["text"] == "intervention-output-line\n"
        for chunk in logs_payload["chunks"]  # type: ignore[index]
    )

    release.set()
    completed_payload = _wait_job(service, job_id)
    assert completed_payload["status"] == "completed"
    assert completed_payload["result"]["completed"] is True  # type: ignore[index]


def test_ui_stage_interact_cancel_callback_observes_cancel_request(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()
    observed_cancel = threading.Event()

    def fake_stage_interact_runner(options: StageInteractOptions) -> None:
        assert options.cancel_requested is not None
        started.set()
        assert release.wait(timeout=2)
        if options.cancel_requested():
            observed_cancel.set()

    service = _service(
        workspace_root,
        stage_interact_runner=fake_stage_interact_runner,
    )

    response = service.handle_post(
        "/api/stage/interact",
        {
            "stage": "plan",
            "runtime": "codex",
            "run_id": "run-ui-intervention-cancel",
            "request": "Cancel this intervention",
            "target_documents": [],
        },
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    assert started.wait(timeout=2)
    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))
    assert cancel_payload["status"] == "cancelling"
    release.set()

    cancelled_payload = _wait_job_status(service, job_id, "cancelled")
    assert observed_cancel.wait(timeout=2)
    assert cancelled_payload["cancel_state"] == "cancelled"


def test_ui_stage_run_endpoint_rejects_invalid_stage_and_runtime(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    invalid_stage = service.handle_post(
        "/api/stage/run",
        {
            "stage": "unknown",
            "runtime": "codex",
        },
    )
    invalid_runtime = service.handle_post(
        "/api/stage/run",
        {
            "stage": "plan",
            "runtime": "unknown-runtime",
        },
    )

    assert invalid_stage.status == HTTPStatus.BAD_REQUEST
    assert invalid_runtime.status == HTTPStatus.BAD_REQUEST
    assert "Unknown stage" in _error_payload(invalid_stage)["error"]  # type: ignore[operator]
    assert "Unsupported runtime" in _error_payload(invalid_runtime)["error"]  # type: ignore[operator]


def test_ui_stage_interact_endpoint_rejects_bad_payload(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    empty_request = service.handle_post(
        "/api/stage/interact",
        {
            "stage": "plan",
            "runtime": "codex",
            "request": " ",
        },
    )
    bad_targets = service.handle_post(
        "/api/stage/interact",
        {
            "stage": "plan",
            "runtime": "codex",
            "request": "Add migration rollback risks",
            "target_documents": "plan.md",
        },
    )

    assert empty_request.status == HTTPStatus.BAD_REQUEST
    assert bad_targets.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(empty_request)["error"] == "request is required."
    assert "target_documents must be an array" in _error_payload(bad_targets)["error"]  # type: ignore[operator]


def test_ui_open_folder_endpoint_allows_workspace_stage_and_artifact_paths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    opened: list[Path] = []
    service = _service(workspace_root, folder_opener=opened.append)

    workspace_payload = _payload(
        service.handle_post("/api/open-folder", {"target": "workspace"})
    )
    stage_payload = _payload(
        service.handle_post("/api/open-folder", {"target": "stage", "stage": "plan"})
    )
    artifact_payload = _payload(
        service.handle_post(
            "/api/open-folder",
            {"target": "artifact", "path": "workitems/WI-UI/stages/plan/plan.md"},
        )
    )

    assert workspace_payload["target"] == "workspace"
    assert stage_payload["target"] == "stage"
    assert artifact_payload["target"] == "artifact"
    assert opened == [
        workspace_root.resolve(strict=False),
        (workspace_root / "workitems" / "WI-UI" / "stages" / "plan").resolve(
            strict=False
        ),
        (workspace_root / "workitems" / "WI-UI" / "stages" / "plan").resolve(
            strict=False
        ),
    ]


def test_ui_open_folder_endpoint_rejects_escaping_and_unsupported_targets(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root, folder_opener=lambda path: None)

    escaped = service.handle_post(
        "/api/open-folder",
        {"target": "artifact", "path": "../outside.md"},
    )
    unsupported = service.handle_post("/api/open-folder", {"target": "project"})

    assert escaped.status == HTTPStatus.BAD_REQUEST
    assert unsupported.status == HTTPStatus.BAD_REQUEST
    assert "escapes workspace root" in _error_payload(escaped)["error"]  # type: ignore[operator]
    assert "unsupported folder target" in _error_payload(unsupported)["error"]  # type: ignore[operator]


def test_ui_server_stop_endpoint_is_local_server_action_only(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    payload = _payload(service.handle_post("/api/server/stop", {}))

    assert payload["status"] == "stopping"
    assert payload["runtime_job_cancellation"] is False
    assert service.consume_shutdown_requested() is True
    assert service.consume_shutdown_requested() is False


def test_ui_workflow_run_endpoint_requires_runtime(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    response = service.handle_post(
        "/api/workflow/run",
        {
            "from_stage": "idea",
            "to_stage": "plan",
        },
    )

    payload = _error_payload(response)
    assert response.status == HTTPStatus.BAD_REQUEST
    assert payload["error"] == "runtime is required."


def test_ui_runtime_readiness_endpoint_exposes_probe_and_config_data(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
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
    calls: list[object] = []

    def fake_readiness_probe_provider(cfg: object) -> dict[str, RuntimeReadinessProbeReport]:
        calls.append(cfg)
        return {
            "generic-cli": RuntimeReadinessProbeReport(
                provider_available=True,
                execution_command_available=False,
                provider_version="Python <3>",
                provider_command="/usr/bin/python",
            )
        }

    service = _service(
        workspace_root,
        config=config_path,
        readiness_probe_provider=fake_readiness_probe_provider,
    )

    payload = _payload(service.handle_get("/api/runtime-readiness", {}))

    runtimes = {
        str(runtime["runtime_id"]): runtime
        for runtime in payload["runtimes"]
        if isinstance(runtime, dict)
    }
    generic_cli = runtimes["generic-cli"]
    assert calls
    assert generic_cli["support_tier"] == "tier-1"
    assert generic_cli["command_source"] == "config"
    assert generic_cli["command"] == "python -m fixture_runtime"
    assert generic_cli["execution_mode"] == "adapter-flags"
    assert generic_cli["provider_available"] is True
    assert generic_cli["provider_version"] == "Python <3>"
    assert generic_cli["provider_command"] == "/usr/bin/python"
    assert generic_cli["execution_command_available"] is False
    assert generic_cli["default_timeout_seconds"] == 42
    assert generic_cli["stage_timeout_seconds"] == {"plan": 90}
    assert runtimes["codex"]["command_source"] == "default"


def test_ui_runtime_readiness_is_not_workflow_source_of_truth(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = tmp_path / "aidd.toml"
    config_path.write_text(
        "\n".join(
            (
                "[runtime.generic_cli]",
                'command = "python -m trusted_runtime"',
                "",
            )
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        captured.update(kwargs)
        return WorkflowRunResult(
            run_id="run-ui-source",
            executed_stage_count=1,
            completed=True,
            incomplete=(),
        )

    def forbidden_readiness_probe_provider(
        cfg: object,
    ) -> dict[str, RuntimeReadinessProbeReport]:
        raise AssertionError("workflow run must not call readiness probes")

    service = _service(
        workspace_root,
        config=config_path,
        workflow_runner=fake_workflow_runner,
        readiness_probe_provider=forbidden_readiness_probe_provider,
    )

    response = service.handle_post(
        "/api/workflow/run",
        {
            "runtime": "generic-cli",
            "from_stage": "idea",
            "to_stage": "plan",
        },
    )

    payload = _payload(response)
    job_payload = _wait_job(service, str(payload["job_id"]))
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert job_payload["result"]["run_id"] == "run-ui-source"  # type: ignore[index]
    assert request.config_snapshot["runtime_command"] == "python -m trusted_runtime"
    assert request.config_snapshot["mode"] == "ui-workflow"


def test_operator_ui_local_project_e2e_lane_covers_core_operator_flow(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    _write_questions(workspace_root)
    captured: dict[str, object] = {}

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        captured.update(kwargs)
        return WorkflowRunResult(
            run_id="run-ui-e2e",
            executed_stage_count=1,
            completed=False,
            incomplete=("plan",),
        )

    service = _service(workspace_root, workflow_runner=fake_workflow_runner)

    page = service.handle_get("/", {})
    favicon = service.handle_get("/favicon.ico", {})
    assert page.status == 200
    assert favicon.status == HTTPStatus.NO_CONTENT
    html = page.body.decode("utf-8")
    assert "AIDD Operator Console" in html
    assert "Loading operator workspace..." in html
    assert 'class="empty-state loading-state"' in html
    assert 'id="runtimeSelect"' in html
    assert 'id="openWorkspaceButton"' in html
    assert 'id="stopServerButton"' in html
    assert 'class="topbar" aria-label="Operator controls"' in html
    assert 'class="operator-shell" aria-label="Operator workspace"' in html
    assert 'class="stage-rail" aria-label="Workflow navigation"' in html
    assert 'class="cockpit" aria-label="Stage cockpit"' in html
    assert 'class="right-sidebar" aria-label="Run details"' in html
    assert 'class="bottom-dock" aria-label="Activity and recent artifacts"' in html
    assert 'id="stageRail" class="stage-list" aria-label="Workflow stages"' in html
    assert 'class="tabs" role="tablist" aria-label="Stage cockpit views"' in html
    assert (
        'id="tab-overview" data-tab="overview" role="tab" aria-selected="true" '
        'aria-controls="cockpitContent"'
        in html
    )
    assert (
        'id="cockpitContent" class="cockpit-content" role="tabpanel" '
        'aria-labelledby="tab-overview" tabindex="0"'
        in html
    )
    assert 'id="nextActionButton"' not in html

    run_response = service.handle_post(
        "/api/workflow/run",
        {
            "runtime": "generic-cli",
            "from_stage": "idea",
            "to_stage": "qa",
        },
    )
    run_payload = _payload(run_response)
    job_payload = _wait_job(service, str(run_payload["job_id"]))
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert job_payload["result"]["run_id"] == "run-ui-e2e"  # type: ignore[index]
    assert request.workspace_root == workspace_root
    assert request.stage_start == "idea"
    assert request.stage_end == "qa"

    answer_payload = _payload(
        service.handle_post(
            "/api/answers",
            {
                "stage": "plan",
                "question_id": "Q1",
                "text": "Release target is local-fixture.",
            },
        )
    )
    assert answer_payload["unresolved_blocking_question_ids"] == []
    assert "Release target is local-fixture." in (
        workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "answers.md"
    ).read_text(encoding="utf-8")

    logs_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"]}))
    artifacts_payload = _payload(service.handle_get("/api/artifacts", {"stage": ["plan"]}))
    stage_payload = _payload(service.handle_get("/api/stage", {"stage": ["plan"]}))

    assert logs_payload["text"] == "runtime-line\n"
    assert artifacts_payload["documents"]["plan"] == (
        "workitems/WI-UI/stages/plan/plan.md"
    )
    assert artifacts_payload["documents"]["stage_result"] == (
        "workitems/WI-UI/stages/plan/stage-result.md"
    )
    assert stage_payload["result"]["validator_report_path"] == (
        "workitems/WI-UI/stages/plan/validator-report.md"
    )
    assert stage_payload["result"]["validator_fail_count"] == 1
    assert stage_payload["result"]["repair_output_paths"] == [
        "workitems/WI-UI/stages/plan/repair-brief.md"
    ]


def test_operator_ui_artifacts_include_declared_project_set_roots(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    project_context_path = workspace_root / "workitems" / "WI-UI" / "context" / "project-set.md"
    project_context_path.parent.mkdir(parents=True)
    project_context_path.write_text(
        "# Project set\n\n"
        "## Projects\n\n"
        "| Project id | Root | Role |\n"
        "| --- | --- | --- |\n"
        "| `api` | `services/api` | `primary` |\n"
        "| `web` | `apps/web` | `unspecified` |\n",
        encoding="utf-8",
    )
    _prepare_run(workspace_root)
    service = _service(workspace_root)

    artifacts_payload = _payload(service.handle_get("/api/artifacts", {"stage": ["plan"]}))

    assert artifacts_payload["documents"]["project_set_context"] == (
        "workitems/WI-UI/context/project-set.md"
    )
    project_context = project_context_path.read_text(encoding="utf-8")
    assert "`api`" in project_context
    assert "`services/api`" in project_context
    assert "`web`" in project_context
    assert "`apps/web`" in project_context


def test_ui_artifact_document_endpoint_reads_known_document_content(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root)

    primary_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["plan"],
            },
        )
    )
    assert primary_payload["key"] == "plan"
    assert primary_payload["path"] == "workitems/WI-UI/stages/plan/plan.md"
    assert "stage primary output visible" in primary_payload["text"]  # type: ignore[operator]

    payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["stage_result"],
            },
        )
    )

    assert payload["key"] == "stage_result"
    assert payload["path"] == "workitems/WI-UI/stages/plan/stage-result.md"
    assert payload["content_type"] == "text/markdown"
    assert "Blocked on clarification." in payload["text"]  # type: ignore[operator]


def test_ui_artifact_document_endpoint_bounds_large_markdown_payloads(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    large_text = "# Plan\n\n" + ("A" * (300 * 1024)) + "\nEND\n"
    plan_path.write_text(large_text, encoding="utf-8")
    byte_size = len(large_text.encode("utf-8"))
    service = _service(workspace_root)

    preview_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["plan"],
            },
        )
    )
    source_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["plan"],
                "mode": ["source"],
                "limit": ["999999"],
            },
        )
    )
    explicit_limit_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["plan"],
                "key": ["plan"],
                "mode": ["source"],
                "limit": ["128"],
            },
        )
    )
    invalid_limit = service.handle_get(
        "/api/artifacts/document",
        {
            "stage": ["plan"],
            "key": ["plan"],
            "limit": ["0"],
        },
    )

    assert preview_payload["mode"] == "preview"
    assert preview_payload["byte_size"] == byte_size
    assert preview_payload["requested_bytes"] == 64 * 1024
    assert preview_payload["start_byte"] == 0
    assert preview_payload["end_byte"] == 64 * 1024
    assert preview_payload["truncated"] is True
    assert preview_payload["truncated_tail"] is True
    assert "END" not in str(preview_payload["text"])

    assert source_payload["mode"] == "source"
    assert source_payload["requested_bytes"] == 256 * 1024
    assert source_payload["max_bytes"] == 256 * 1024
    assert source_payload["end_byte"] == 256 * 1024
    assert source_payload["truncated_tail"] is True
    assert "END" not in str(source_payload["text"])

    assert explicit_limit_payload["start_byte"] == 0
    assert explicit_limit_payload["end_byte"] == 128
    assert explicit_limit_payload["requested_bytes"] == 128
    assert str(explicit_limit_payload["text"]).startswith("# Plan\n\n")

    assert invalid_limit.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(invalid_limit)["error"] == "limit must be greater than zero."


def test_ui_artifact_document_endpoint_rejects_unknown_key_and_escaping_paths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root)

    unknown = service.handle_get(
        "/api/artifacts/document",
        {
            "stage": ["plan"],
            "key": ["missing"],
        },
    )

    assert unknown.status == HTTPStatus.BAD_REQUEST
    assert "not available" in _error_payload(unknown)["error"]  # type: ignore[operator]

    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    payload["documents"]["escape"] = "../outside.md"
    artifact_index_path.write_text(json.dumps(payload), encoding="utf-8")

    known_after_unrelated_corruption = service.handle_get(
        "/api/artifacts/document",
        {
            "stage": ["plan"],
            "key": ["stage_result"],
        },
    )
    escaped = service.handle_get(
        "/api/artifacts/document",
        {
            "stage": ["plan"],
            "key": ["escape"],
        },
    )

    assert known_after_unrelated_corruption.status == HTTPStatus.OK
    assert escaped.status == HTTPStatus.BAD_REQUEST
    assert "escapes workspace root" in _error_payload(escaped)["error"]  # type: ignore[operator]


def test_ui_artifact_document_endpoint_rejects_non_utf8_documents(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    binary_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "bad.bin"
    binary_path.write_bytes(b"\xff\xfe\x00")
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    payload = json.loads(artifact_index_path.read_text(encoding="utf-8"))
    payload["documents"]["bad"] = "workitems/WI-UI/stages/plan/bad.bin"
    artifact_index_path.write_text(json.dumps(payload), encoding="utf-8")
    service = _service(workspace_root)

    response = service.handle_get(
        "/api/artifacts/document",
        {
            "stage": ["plan"],
            "key": ["bad"],
        },
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert "not UTF-8 text" in _error_payload(response)["error"]  # type: ignore[operator]


def test_operator_script_escapes_dynamic_markup(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    script = _operator_script_bundle(service)

    assert "function escapeHtml(value)" in script
    assert "function compactPath(value, maxLength = 56)" in script
    assert "function pathLine(value, maxLength = 56)" in script
    assert "function renderMarkdown(text)" in script
    assert "function preferredArtifactKey(documents)" in script
    assert "async function fetchDashboard()" in script
    assert "dashboardUrl()" in script
    assert 'api("/api/runtime-readiness")' in script
    assert '"plan"' in script
    assert '"stage_result"' in script
    assert 'activeRunId: ""' in script
    assert "readinessLoading: true" in script
    assert 'readinessError: ""' in script
    assert "state.activeRunId = state.dashboard.run?.run_id || \"\";" in script
    assert "version.startsWith(\"v\") ? version : `v${version || \"dev\"}`" in script
    assert "No artifacts for this stage yet" in script
    assert "No runtime log for this stage yet" in script
    assert "function questionControlId(prefix, questionId, index)" in script
    assert (
        'const questionTextId = questionControlId("question-text", question.question_id, index);'
        in script
    )
    assert 'const answerId = questionControlId("answer", question.question_id, index);' in script
    assert (
        'const resolutionId = questionControlId("resolution", question.question_id, index);'
        in script
    )
    assert '<p id="${questionTextId}">${escapeHtml(question.text)}</p>' in script
    assert (
        '<label class="sr-only" for="${answerId}">Answer for ${escapeHtml(questionLabel)}</label>'
        in script
    )
    assert (
        '<textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}"'
        in script
    )
    assert (
        '<label class="sr-only" for="${resolutionId}">Resolution for '
        "${escapeHtml(questionLabel)}</label>"
        in script
    )
    assert (
        '<select id="${resolutionId}" name="${resolutionId}" aria-describedby="${questionTextId}"'
        in script
    )
    assert 'const savedAnswer = resolved && question.answer_text' in script
    assert 'class="saved-answer"' in script
    assert "Saved answer" in script
    assert "${escapeHtml(question.answer_text)}" in script
    assert "function byteRangeSummary(view)" in script
    assert 'function renderTruncationNotice(kind, view, mode = "")' in script
    assert 'class="truncation-notice" role="status"' in script
    assert "Runtime log truncated" in script
    assert "Artifact view truncated" in script
    assert "Switch to Source for a larger bounded read" in script
    assert "Source view is bounded. Open the folder for the full file." in script
    assert "Full runtime.log remains on disk" in script
    assert (
        "function renderLogPanel({title, meta, entries, rawText, emptyText, actions = \"\", "
        "truncation = null})"
        in script
    )
    assert "async function renderRequestChange()" in script
    assert "async function renderApprovals()" in script
    assert "async function submitApproval(requestId, action)" in script
    assert "async function submitIntervention()" in script
    assert 'id="operatorRequestText"' in script
    assert 'id="submitInterventionButton"' in script
    assert "data-intervention-target" in script
    assert '"validator_report"' in script
    assert '"questions.md"' in script
    assert "!textPath.includes(\"/operator-requests/\")" in script
    assert "function interventionTargetLabel(key)" in script
    assert "function updateSubmitInterventionState()" in script
    assert 'event.target.id === "operatorRequestText"' in script
    assert "function logEntriesFromChunks(chunks)" in script
    assert "function logEntriesFromText(text)" in script
    assert "rawText.match(/^\\[(stdout|stderr|system)\\]\\s?(.*)$/i)" in script
    assert "function selectedRuntimeReady()" in script
    assert "function timeoutSummary(runtime)" in script
    assert "function readinessDetail(label, value, maxLength = 72)" in script
    assert 'title="${escapeHtml(text)}"' in script
    assert "${escapeHtml(compactPath(text, maxLength))}" in script
    assert "function ensureRunnableRuntime()" in script
    assert "function scrollActiveStageIntoView()" in script
    assert "function renderFirstLaunchState()" in script
    assert "first-launch-state" in script
    assert "Select a runtime to start the first governed workflow run." in script
    assert "data-first-launch-run" in script
    assert 'event.target.closest("[data-first-launch-run]")' in script
    assert 'if (state.activeTab === "overview") await renderCockpit();' in script
    assert 'window.matchMedia("(max-width: 760px)").matches' in script
    assert 'rail.querySelector(`[data-stage="${CSS.escape(state.activeStage)}"]`)' in script
    assert (
        'active?.scrollIntoView({behavior: "auto", block: "nearest", inline: "center"});'
        in script
    )
    assert "requestAnimationFrame(scrollActiveStageIntoView);" in script
    assert 'toast("Selected runtime is not ready.")' in script
    assert 'if (element.textContent === message) element.textContent = "";' in script
    assert 'button.setAttribute("aria-selected", isActive ? "true" : "false");' in script
    assert 'content.setAttribute("aria-labelledby", `tab-${tab}`);' in script
    assert 'aria-current="${isActive ? "step" : "false"}"' in script
    assert "data-log-filter" in script
    assert "data-log-raw" in script
    assert "state.rawLogMode" in script
    assert 'state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered)' in script
    assert "function renderLiveJobActions()" in script
    assert "function activeJobCancelLabel()" in script
    assert "async function cancelActiveJob()" in script
    assert "data-cancel-job" in script
    assert "Cancel job" in script
    assert "Cancelling..." in script
    assert "Cancelled" in script
    assert "/api/jobs/${encodeURIComponent(state.activeJobId)}/cancel" in script
    assert 'new Set(["running", "waiting-for-operator", "cancelling"])' in script
    assert "activeJobLogChunks.push(...(logs.chunks || []));" in script
    assert "function liveJobActivityEvents()" in script
    assert "function activityEvents()" in script
    assert "renderActivityTable();" in script
    assert "activeJobLogChunks.length" in script
    assert 'state.activeJobStatus?.status === "running"' in script
    assert "state.activeJobStatus.stage === state.activeStage" in script
    assert "/api/artifacts/document?${params.toString()}" in script
    assert 'params.set("mode", state.artifactViewMode);' in script
    assert "const MAX_ARTIFACT_READ_BYTES = 262144;" in script
    assert 'params.set("limit", String(MAX_ARTIFACT_READ_BYTES));' in script
    assert 'renderTruncationNotice("artifact", documentView, state.artifactViewMode)' in script
    assert "${renderMarkdown(documentView.text)}" in script
    assert "const payload = {stage, runtime: state.selectedRuntime, log_follow: true};" in script
    assert "target_documents: targetDocuments" in script
    assert "if (state.activeRunId) payload.run_id = state.activeRunId;" in script
    assert "const payload = {runtime: state.selectedRuntime, log_follow: true};" in script
    assert 'postJson("/api/workflow/run", payload)' in script
    assert "Resume workflow" in script
    assert "Continue with ${stageTitle(action.stage || state.activeStage)}" in script
    assert "Checking runtimes..." in script
    assert "Checking runtime readiness." in script
    assert (
        "const runtimes = state.readinessLoading ? [] : "
        "(state.readiness?.runtimes || []);"
    ) in script
    assert "if (state.readinessLoading) return null;" in script
    assert "Support tier" in script
    assert "Command source" in script
    assert "Execution mode" in script
    assert "Permission policy" in script
    assert "Interaction mode" in script
    assert "Auto approval" in script
    assert "Provider version" in script
    assert "Provider command" in script
    assert "await fetchDashboard();" in script
    assert "void fetchReadiness().then(renderAll)" in script
    assert "Promise.all([fetchDashboard(), fetchReadiness()])" not in script
    assert 'resolution: resolution?.value || "resolved"' in script
    assert 'option value="partial"' in script
    assert 'option value="deferred"' in script
    assert "async function answerAndResume(questionId)" in script
    assert "async function inspectArtifactReference({stage, key, path, kind})" in script
    assert "data-evidence-path" in script
    assert "data-artifact-key" in script
    assert "data-blocker-stage" in script
    assert 'class="stage-copy"' in script
    assert script.index('closest("[data-artifact-stage]")') < script.index(
        'closest("[data-artifact-key]")'
    )
    assert "function renderRuntimeSelector()" in script
    assert "/api/dashboard" in script
    assert "/api/stage/run" in script
    assert "/api/stage/interact" in script
    assert "/operator-requests/" in script
    assert '"waiting-for-operator"' in script
    assert "/api/open-folder" in script
    assert "/api/server/stop" in script
    assert (
        "/api/jobs/${encodeURIComponent(state.activeJobId)}/logs?cursor="
        "${state.activeJobCursor}"
        in script
    )
    assert 'body: JSON.stringify({runtime: "generic-cli"})' not in script

    css = _operator_css_bundle(service)
    assert ".status-badge.cancelled" in css
    assert ".small-badge.running" in css
    assert ".small-badge.cancelling" in css
    assert ".small-badge.waiting-for-operator" in css
    assert ".log-actions" in css
    assert ".truncation-notice" in css
    assert ".saved-answer" in css
    assert ".saved-answer-text" in css
    assert ".loading-state" in css
    assert "--focus-ring:" in css
    assert "button:focus-visible" in css
    assert "outline: 3px solid var(--focus-ring)" in css
    assert "box-shadow: 0 0 0 4px var(--focus-ring-soft)" in css
    assert "scroll-padding-inline: 10px" in css


def test_operator_question_controls_have_screen_reader_labels(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    script = _operator_script_bundle(service)
    css = _operator_css_bundle(service)

    assert '<label class="sr-only" for="${answerId}">Answer for' in script
    assert (
        '<textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}"'
        in script
    )
    assert '<label class="sr-only" for="${resolutionId}">Resolution for' in script
    assert (
        '<select id="${resolutionId}" name="${resolutionId}" aria-describedby="${questionTextId}"'
        in script
    )
    assert ".sr-only" in css
    assert "clip-path: inset(50%)" in css
    assert "position: absolute" in css


def test_ui_json_body_reader_rejects_oversized_payload() -> None:
    handler = _BodyHandler(b"x" * (64 * 1024 + 1))

    try:
        _read_json_body(handler)  # type: ignore[arg-type]
    except UiRequestBodyTooLarge as exc:
        assert "64 KiB" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected oversized body to be rejected")


def test_ui_json_body_reader_rejects_non_object_json() -> None:
    handler = _BodyHandler(b'["not", "object"]')

    try:
        _read_json_body(handler)  # type: ignore[arg-type]
    except ValueError as exc:
        assert str(exc) == "Request body must be a JSON object."
    else:  # pragma: no cover - assertion guard
        raise AssertionError("expected non-object JSON to be rejected")


def test_ui_loopback_detection_for_warn_only_bind_policy() -> None:
    assert _is_loopback_host("127.0.0.1") is True
    assert _is_loopback_host("localhost") is True
    assert _is_loopback_host("0.0.0.0") is False


def test_ui_command_is_registered() -> None:
    command_names = {command.name for command in cli_main.app.registered_commands}

    assert "ui" in command_names
