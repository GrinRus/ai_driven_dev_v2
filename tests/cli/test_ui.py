from __future__ import annotations

import inspect
import json
import os
import shlex
import socket
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
import typer

from aidd.cli import main as cli_main
from aidd.cli import ui as ui_module
from aidd.cli.stage_run import StageInteractOptions, StageRunOptions
from aidd.cli.ui import (
    OperatorUiService,
    UiRunJobStore,
    UiServerOptions,
    _is_loopback_host,
    ui_command,
)
from aidd.cli.ui_assets import operator_static_asset_for_route, operator_static_asset_manifest
from aidd.cli.ui_http import UiRequestBodyTooLarge, _read_json_body
from aidd.core.remediation import (
    create_remediation_request,
    mark_downstream_stale,
)
from aidd.core.repair import persist_repair_history_snapshot
from aidd.core.run_store import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RUN_EVENTS_JSONL_FILENAME,
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
    run_attempt_root,
    run_attempt_runtime_log_path,
    run_manifest_path,
    run_root,
    write_attempt_artifact_index,
)
from aidd.core.runtime_operator import (
    RuntimeOperatorBroker,
    RuntimeOperatorDecision,
    RuntimeOperatorPolicy,
    RuntimeOperatorRequest,
    append_operator_decision,
    append_operator_request,
    load_operator_decisions,
)
from aidd.core.runtime_readiness import RuntimeReadinessProbeReport
from aidd.core.stage_runner import prepare_stage_bundle
from aidd.core.stages import STAGES
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
)
from aidd.core.workspace import seed_work_item_metadata
from aidd.runtime_catalog import runtime_definitions
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
    RuntimeOperatorRisk,
    RuntimePermissionPolicy,
)


def test_ui_implementation_adapter_does_not_import_cli_task_business_service() -> None:
    assert "aidd.cli.task" not in inspect.getsource(ui_module)


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


def _onboarding_service(tmp_path: Path, monkeypatch: Any) -> OperatorUiService:
    return _onboarding_service_with_runner(tmp_path, monkeypatch)


def _onboarding_service_with_runner(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    workflow_runner: Any | None = None,
) -> OperatorUiService:
    monkeypatch.chdir(tmp_path)

    def _ready_probe(_config: object) -> dict[str, RuntimeReadinessProbeReport]:
        return {
            definition.runtime_id: RuntimeReadinessProbeReport(
                provider_available=True,
                execution_command_available=True,
                provider_version="test",
                provider_command=definition.probe_command,
            )
            for definition in runtime_definitions()
        }

    kwargs: dict[str, Any] = {"readiness_probe_provider": _ready_probe}
    if workflow_runner is not None:
        kwargs["workflow_runner"] = workflow_runner
    return OperatorUiService(
        UiServerOptions(
            work_item=None,
            root=Path(".aidd"),
            config=Path("aidd.test.toml"),
            host="127.0.0.1",
            port=0,
        ),
        **kwargs,
    )


def _payload(response) -> dict[str, object]:
    assert response.status == 200
    return json.loads(response.body.decode("utf-8"))


def _payload_with_status(response, status: int) -> dict[str, object]:
    assert response.status == status
    return json.loads(response.body.decode("utf-8"))


def _seed_rich_tasklist(workspace_root: Path) -> None:
    path = workspace_root / "workitems" / "WI-UI" / "stages" / "tasklist" / "output" / "tasklist.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Tasklist

## Task summary

One complete UI-visible implementation task.

## Ordered tasks

### TL-1 — Add task progress

- Outcome: Task progress is visible.
- Dominant deliverable: The operator task panel renders state.
- In scope: `src/aidd/cli/ui.py` and `tests/cli/test_ui.py`.
- Acceptance criteria:
  - TL-1-AC1: The task endpoint returns status and acceptance evidence.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: UI endpoint contract test
""",
        encoding="utf-8",
    )


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


def test_ui_job_store_bounds_live_chunks_and_paginates_absolute_cursors() -> None:
    store = UiRunJobStore(
        max_live_log_bytes=48,
        max_log_response_bytes=16,
    )
    job_id = store.create(kind="stage", stage="plan")
    chunks = [f"chunk-{index:04d}\n" for index in range(10)]
    for text in chunks:
        store.append_chunk(job_id, stream="stdout", text=text)

    view = store.view(job_id)
    assert int(view["retained_live_log_bytes"]) <= 48
    assert int(view["dropped_live_log_bytes"]) > 0

    cursor = 0
    collected = ""
    page_count = 0
    first_page = True
    while True:
        page = store.logs(job_id, cursor=cursor)
        payload_bytes = sum(
            len(str(chunk["text"]).encode("utf-8")) for chunk in page["chunks"]  # type: ignore[union-attr]
        )
        assert payload_bytes <= 16
        if first_page:
            assert page["truncated"] is True
            assert int(page["oldest_cursor"]) > 0
            first_page = False
        next_cursor = int(page["cursor"])
        assert next_cursor > cursor
        collected += "".join(
            str(chunk["text"]) for chunk in page["chunks"]  # type: ignore[union-attr]
        )
        page_count += 1
        cursor = next_cursor
        if not page["has_more"]:
            break

    assert page_count > 1
    assert collected == "".join(chunks[-4:])


def test_ui_job_store_truncates_oversized_unicode_chunk_by_tail() -> None:
    store = UiRunJobStore(
        max_live_log_bytes=16,
        max_log_response_bytes=8,
    )
    job_id = store.create(kind="stage", stage="plan")
    store.append_chunk(job_id, stream="stdout", text="🙂" * 10)

    first = store.logs(job_id, cursor=0)
    assert first["oldest_cursor"] == 24
    assert first["truncated"] is True
    assert first["dropped_bytes"] == 24
    assert first["has_more"] is True
    assert first["chunks"][0]["sequence"] == 1  # type: ignore[index]
    assert first["chunks"][0]["truncated"] is True  # type: ignore[index]
    assert first["chunks"][0]["dropped_bytes"] == 24  # type: ignore[index]
    assert first["chunks"][0]["text"] == "🙂🙂"  # type: ignore[index]

    second = store.logs(job_id, cursor=int(first["cursor"]))
    assert second["chunks"][0]["text"] == "🙂🙂"  # type: ignore[index]
    assert second["has_more"] is False


def test_ui_job_store_evicts_terminal_jobs_by_ttl_and_count() -> None:
    now = [datetime(2026, 7, 16, tzinfo=UTC)]
    store = UiRunJobStore(
        max_terminal_jobs=2,
        terminal_job_ttl_seconds=3600,
        now=lambda: now[0],
    )

    first = store.create(kind="stage", stage="idea")
    store.complete(first, result={}, exit_code=0, message="completed")
    now[0] += timedelta(seconds=1)
    second = store.create(kind="stage", stage="research")
    store.complete(second, result={}, exit_code=0, message="completed")
    now[0] += timedelta(seconds=1)
    active = store.create(kind="stage", stage="plan")
    now[0] += timedelta(seconds=1)
    third = store.create(kind="stage", stage="review")
    store.complete(third, result={}, exit_code=0, message="completed")

    with pytest.raises(ValueError, match="Unknown UI job"):
        store.view(first)
    assert store.view(active)["status"] == "running"
    assert store.view(second)["status"] == "completed"
    assert store.view(third)["status"] == "completed"

    now[0] += timedelta(seconds=3601)
    assert store.view(active)["status"] == "running"
    with pytest.raises(ValueError, match="Unknown UI job"):
        store.view(second)
    with pytest.raises(ValueError, match="Unknown UI job"):
        store.view(third)


class _BodyHandler:
    def __init__(self, body: bytes, *, content_length: str | None = None) -> None:
        self.headers = {"Content-Length": content_length or str(len(body))}
        self.rfile = BytesIO(body)


def _prepare_run(workspace_root: Path) -> None:
    seed_work_item_metadata(root=workspace_root, work_item="WI-UI")
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
    (
        run_attempt_root(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage="plan",
            attempt_number=1,
        )
        / "input-bundle.md"
    ).write_text("# Input bundle\n\nPrepared UI fixture.\n", encoding="utf-8")
    write_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
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
        "# Validator Report\n\n## Result\n\n- Verdict: `fail`\n",
        encoding="utf-8",
    )
    stage_root.joinpath("stage-result.md").write_text(
        "# Stage Result\n\n## Summary\n\nBlocked on clarification.\n",
        encoding="utf-8",
    )
    stage_root.joinpath("plan.md").write_text(
        "# Plan\n\n## Goals\n\n- Keep stage primary output visible in the operator UI.\n",
        encoding="utf-8",
    )
    stage_root.joinpath("repair-brief.md").write_text(
        "# Failed checks\n\n"
        "- `SEM-INCOMPLETE-SECTION` `medium` in "
        "`workitems/WI-UI/stages/plan/plan.md`: Missing validation evidence.\n",
        encoding="utf-8",
    )


def _prepare_completed_qa_run(
    workspace_root: Path,
    *,
    lineage: dict[str, object] | None = None,
    stage_target: str = "qa",
) -> None:
    seed_work_item_metadata(root=workspace_root, work_item="WI-UI")
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        runtime_id="codex",
        stage_target=stage_target,
        config_snapshot={"mode": "ui-terminal-test"},
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
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage=stage,
            status="succeeded",
        )
        stage_root = workspace_root / "workitems" / "WI-UI" / "stages" / stage
        stage_root.mkdir(parents=True, exist_ok=True)
        stage_root.joinpath("validator-report.md").write_text(
            "# Validator Report\n\n- Verdict: `pass`\n",
            encoding="utf-8",
        )
        stage_root.joinpath("stage-result.md").write_text(
            "# Stage Result\n\n## Status\n\n- `succeeded`\n",
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
                "## Readiness",
                "",
                "- QA verdict: `ready`.",
                "",
            )
        ),
        encoding="utf-8",
    )
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="qa",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "uv run --extra dev pytest tests/cli/test_ui.py"},
        risk=RuntimeOperatorRisk.MEDIUM,
    )
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="qa",
        attempt_number=1,
    )
    append_operator_request(
        path=attempt_root / OPERATOR_REQUESTS_FILENAME,
        request=request,
    )
    append_operator_decision(
        path=attempt_root / OPERATOR_DECISIONS_FILENAME,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
            source=RuntimeOperatorDecisionSource.UI,
            reason="approved in UI terminal handoff fixture",
        ),
    )


def _git(project_root: Path, *args: str) -> None:
    subprocess.run(
        ("git", "-C", project_root.as_posix(), *args),
        check=True,
        capture_output=True,
        text=True,
    )


def _prepare_ui_project_repo(tmp_path: Path, monkeypatch: Any) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()
    _git(project_root, "init")
    _git(project_root, "config", "user.email", "aidd@example.test")
    _git(project_root, "config", "user.name", "AIDD Test")
    project_root.joinpath("app.py").write_text("print('old')\n", encoding="utf-8")
    _git(project_root, "add", "app.py")
    _git(project_root, "commit", "-m", "initial")
    monkeypatch.chdir(project_root)
    return project_root


def _write_operator_control_reports(workspace_root: Path) -> None:
    implement_root = workspace_root / "workitems" / "WI-UI" / "stages" / "implement"
    implement_root.mkdir(parents=True, exist_ok=True)
    implement_root.joinpath("implementation-report.md").write_text(
        "\n".join(
            (
                "# Implementation Report",
                "",
                "- Selected task id: `TASK-1`",
                "",
                "## Touched files",
                "",
                "- `app.py`",
                "",
                "## Verification",
                "",
                "- `uv run pytest` -> exit 0.",
            )
        ),
        encoding="utf-8",
    )
    review_root = workspace_root / "workitems" / "WI-UI" / "stages" / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    review_root.joinpath("review-report.md").write_text(
        "\n".join(
            (
                "# Review Report",
                "",
                "- Approval status: `rejected`",
                "",
                "## Findings",
                "",
                "- RV-1 Missing guard",
                "  - Severity: `high`",
                "  - Disposition: `must-fix`",
                "  - Evidence: `app.py`",
            )
        ),
        encoding="utf-8",
    )
    qa_root = workspace_root / "workitems" / "WI-UI" / "stages" / "qa"
    qa_root.mkdir(parents=True, exist_ok=True)
    qa_root.joinpath("qa-report.md").write_text(
        "\n".join(
            (
                "# QA Report",
                "",
                "- Quality verdict: `not-ready`",
                "- Release recommendation: `hold`",
                "- Evidence: EV-1",
                "",
                "## Residual risks",
                "",
                "- Retry path is unverified.",
            )
        ),
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
    project_home_payload = _payload(service.handle_get("/api/project-home", {}))
    resume_payload = _payload(service.handle_get("/api/work-item/resume", {"work_item": ["WI-UI"]}))

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
    assert project_home_payload["project_home"]["work_items"][0]["work_item"] == "WI-UI"  # type: ignore[index]
    assert resume_payload["resume"]["latest_run"]["run_id"] == "run-ui"  # type: ignore[index]


def test_ui_project_home_resume_switches_active_context_with_absolute_workspace_root(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    seed_work_item_metadata(root=workspace_root, work_item="WI-OTHER")
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-OTHER",
        run_id="run-other",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    create_next_attempt_directory(
        workspace_root=workspace_root,
        work_item="WI-OTHER",
        run_id="run-other",
        stage="plan",
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item="WI-OTHER",
        run_id="run-other",
        stage="plan",
        status="blocked",
    )
    service = _service(workspace_root)

    resume = _payload(
        service.handle_post(
            "/api/onboarding/work-item",
            {
                "action": "resume",
                "project_root": tmp_path.as_posix(),
                "work_item": "WI-OTHER",
            },
        )
    )
    dashboard = _payload(service.handle_get("/api/dashboard", {}))

    assert resume["context"]["work_item"] == "WI-OTHER"  # type: ignore[index]
    assert dashboard["dashboard"]["work_item"] == "WI-OTHER"  # type: ignore[index]
    assert dashboard["dashboard"]["run"]["run_id"] == "run-other"  # type: ignore[index]


def test_ui_stage_workbench_endpoint_returns_document_state_and_sidebars(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    plan_path.write_text(
        "# Plan\n\n## Goals\n\n" + "\n".join(f"- Workbench line {index}" for index in range(80)),
        encoding="utf-8",
    )
    output_path = plan_path.parent / "output" / "plan.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("# Plan\n\n## Goals\n\n- Published handoff copy.\n", encoding="utf-8")
    service = _service(workspace_root)

    payload = _payload(
        service.handle_get(
            "/api/stage/workbench",
            {
                "stage": ["plan"],
                "key": ["plan"],
                "run_id": ["run-ui"],
                "preview_limit": ["96"],
                "source_limit": ["128"],
            },
        )
    )

    document = payload["document"]
    assert payload["run_id"] == "run-ui"
    assert payload["stage"] == "plan"
    assert payload["selected_key"] == "plan"
    assert document["status"] == "present"  # type: ignore[index]
    assert document["preview"]["mode"] == "preview"  # type: ignore[index]
    assert document["preview"]["requested_bytes"] == 96  # type: ignore[index]
    assert document["preview"]["truncated_tail"] is True  # type: ignore[index]
    assert document["source"]["mode"] == "source"  # type: ignore[index]
    assert document["source"]["requested_bytes"] == 128  # type: ignore[index]
    assert document["source"]["truncated_tail"] is True  # type: ignore[index]

    requirements = payload["requirements"]
    validation_results = payload["validation_results"]
    references = payload["references"]
    versions = payload["versions"]
    assert any(
        item["kind"] == "required-output" and item["status"] == "satisfied"
        for item in requirements  # type: ignore[union-attr]
    )
    assert any(
        item["status"] == "missing"
        for item in requirements  # type: ignore[union-attr]
    )
    assert {
        item["label"]: item["status"]
        for item in validation_results  # type: ignore[union-attr]
    } == {"stage-result": "blocked", "validator-report": "fail"}
    assert any(
        item["label"] == "plan" and item["kind"] == "document"
        for item in references  # type: ignore[union-attr]
    )
    assert any(
        item["label"] == "output/plan.md"
        and item["kind"] == "mirror"
        and item["category"] == "published-stage-output"
        for item in references  # type: ignore[union-attr]
    )
    assert versions[0]["label"] == "Attempt 1"  # type: ignore[index]


def test_ui_evidence_graph_endpoint_returns_graph_and_flat_table_fallback(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    attempt_root.joinpath(RUN_EVENTS_JSONL_FILENAME).write_text(
        (
            '{"timestamp":"2026-05-28T00:00:00Z","level":"info",'
            '"source":"runtime","event":"stage.started","message":"Plan started"}\n'
        ),
        encoding="utf-8",
    )
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "uv run --extra dev pytest tests/cli/test_ui.py"},
    )
    append_operator_request(path=attempt_root / OPERATOR_REQUESTS_FILENAME, request=request)
    append_operator_decision(
        path=attempt_root / OPERATOR_DECISIONS_FILENAME,
        decision=RuntimeOperatorDecision(
            request_id=request.id,
            action=RuntimeOperatorDecisionAction.ALLOW_ONCE,
            source=RuntimeOperatorDecisionSource.UI,
            reason="approved for UI evidence graph endpoint test",
        ),
    )
    service = _service(workspace_root)
    plan_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "plan.md"
    output_path = plan_path.parent / "output" / "plan.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("# Plan\n\n## Goals\n\n- Published handoff copy.\n", encoding="utf-8")
    runtime_log_path = run_attempt_runtime_log_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    artifact_index_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    original_plan = plan_path.read_text(encoding="utf-8")
    original_runtime_log = runtime_log_path.read_text(encoding="utf-8")
    original_artifact_index = artifact_index_path.read_text(encoding="utf-8")

    graph_payload = _payload(
        service.handle_get(
            "/api/artifacts/evidence-graph",
            {"stage": ["plan"], "run_id": ["run-ui"]},
        )
    )

    nodes = {node["node_id"]: node for node in graph_payload["nodes"]}  # type: ignore[index]
    edges = {
        (edge["source_id"], edge["target_id"], edge["kind"])
        for edge in graph_payload["edges"]  # type: ignore[index]
    }
    assert graph_payload["mode"] == "graph"
    assert nodes["document:plan"]["path"] == "workitems/WI-UI/stages/plan/plan.md"
    assert nodes["mirror:output/plan.md"]["path"] == ("workitems/WI-UI/stages/plan/output/plan.md")
    assert nodes["event:1"]["detail"] == "Plan started"
    assert nodes[f"approval-request:{request.id}"]["status"] == "approved"
    assert ("attempt:1", "mirror:output/plan.md", "published-output") in edges
    assert ("document:validator_report", "document:stage_result", "validation") in edges
    assert all(
        not Path(str(node["path"])).is_absolute()
        for node in graph_payload["nodes"]  # type: ignore[index]
        if node["path"] is not None
    )
    assert any(
        ref["key"] == "runtime_log" and ref["kind"] == "log"
        for ref in graph_payload["artifact_table"]  # type: ignore[index]
    )
    assert any(
        ref["key"] == "output/plan.md"
        and ref["kind"] == "mirror"
        and ref["category"] == "published-stage-output"
        for ref in graph_payload["artifact_table"]  # type: ignore[index]
    )
    assert plan_path.read_text(encoding="utf-8") == original_plan
    assert runtime_log_path.read_text(encoding="utf-8") == original_runtime_log
    assert artifact_index_path.read_text(encoding="utf-8") == original_artifact_index

    artifact_index_path.unlink()
    fallback_payload = _payload(
        service.handle_get(
            "/api/artifacts/evidence-graph",
            {"stage": ["plan"], "run_id": ["run-ui"]},
        )
    )

    assert fallback_payload["mode"] == "flat-table"
    assert fallback_payload["nodes"] == []
    assert fallback_payload["edges"] == []
    assert fallback_payload["incomplete_reasons"] == ["artifact-index-missing"]
    assert any(
        ref["key"] == "plan" and ref["path"] == "workitems/WI-UI/stages/plan/plan.md"
        for ref in fallback_payload["artifact_table"]  # type: ignore[index]
    )
    assert any(
        ref["key"] == "output/plan.md"
        and ref["path"] == "workitems/WI-UI/stages/plan/output/plan.md"
        for ref in fallback_payload["artifact_table"]  # type: ignore[index]
    )
    assert plan_path.read_text(encoding="utf-8") == original_plan
    assert runtime_log_path.read_text(encoding="utf-8") == original_runtime_log


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
    tail_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"], "tail": ["128"]}))
    limit_payload = _payload(service.handle_get("/api/logs", {"stage": ["plan"], "limit": ["128"]}))
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


def test_ui_logs_endpoint_treats_missing_runtime_log_as_pending(
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
    runtime_log_path.unlink()
    service = _service(workspace_root)

    response = service.handle_get("/api/logs", {"stage": ["plan"], "run_id": ["run-ui"]})
    payload = _payload(response)

    assert response.status == HTTPStatus.OK
    assert payload["available"] is False
    assert payload["message"] == "Runtime log is not available yet."
    assert payload["text"] == ""
    assert payload["byte_size"] == 0
    assert payload["summary"]["stage"] == "plan"
    assert payload["summary"]["run_id"] == "run-ui"


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


def test_ui_dashboard_endpoint_exposes_previous_run_context_for_setup(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    metadata_path = workspace_root / "workitems" / "WI-UI" / "work-item.json"
    metadata_path.parent.mkdir(parents=True)
    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "work_item_id": "WI-UI",
                "lineage": {
                    "source_run_id": "run-source",
                    "source_work_item_id": "WI-SOURCE",
                    "baseline_id": "baseline-main",
                    "baseline_label": "main before setup",
                },
            }
        ),
        encoding="utf-8",
    )
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/dashboard", {"stage": ["idea"]}))

    lineage = payload["dashboard"]["run"]["lineage"]  # type: ignore[index]
    assert payload["dashboard"]["run"]["run_id"] is None  # type: ignore[index]
    assert lineage["source_run_id"] == "run-source"  # type: ignore[index]
    assert lineage["source_work_item_id"] == "WI-SOURCE"  # type: ignore[index]
    assert lineage["baseline_id"] == "baseline-main"  # type: ignore[index]
    assert lineage["baseline_label"] == "main before setup"  # type: ignore[index]


def test_ui_dashboard_endpoint_exposes_flow_complete_handoff(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["qa"], "run_id": ["run-ui"]})
    )

    dashboard = payload["dashboard"]
    handoff = dashboard["terminal_handoff"]  # type: ignore[index]
    assert dashboard["next_action"]["action"] == "review-complete"  # type: ignore[index]
    assert dashboard["run"]["runtime_id"] == "codex"  # type: ignore[index]
    assert handoff["status"] == "completed"  # type: ignore[index]
    assert handoff["final_qa_status"] == "ready"  # type: ignore[index]
    assert handoff["recommended_outcome"] == "create-new-work-item"  # type: ignore[index]
    assert "fresh and clean" in handoff["recommendation_rationale"]  # type: ignore[index]
    assert handoff["approval_counts"]["requested"] == 1  # type: ignore[index]
    assert handoff["approval_counts"]["approved"] == 1  # type: ignore[index]
    assert {artifact["key"] for artifact in handoff["final_artifacts"]} >= {  # type: ignore[index]
        "qa_report",
        "runtime_log",
        "stage_result",
        "validator_report",
    }
    actions = {
        action["action"]: action
        for action in handoff["recommended_next_flow_actions"]  # type: ignore[index]
    }
    assert set(actions) == {
        "create-new-work-item",
        "start-follow-up-flow",
        "clone-flow",
        "run-eval-batch",
        "archive-run",
    }
    assert "codex" in actions["clone-flow"]["detail"]
    assert "generic-cli" not in actions["clone-flow"]["detail"]


def test_ui_dashboard_endpoint_defaults_completed_flow_to_qa_when_stage_is_omitted(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root, stage_target="idea")
    context_root = workspace_root / "workitems" / "WI-UI" / "context"
    context_root.mkdir(parents=True, exist_ok=True)
    context_root.joinpath("user-request.md").write_text("Ship the terminal UI.\n", encoding="utf-8")
    service = _service(workspace_root)

    default_payload = _payload(service.handle_get("/api/dashboard", {"run_id": ["run-ui"]}))
    explicit_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["idea"], "run_id": ["run-ui"]})
    )
    project_home_payload = _payload(service.handle_get("/api/project-home", {}))

    assert default_payload["dashboard"]["active_stage"] == "qa"  # type: ignore[index]
    assert default_payload["dashboard"]["next_action"]["action"] == "review-complete"  # type: ignore[index]
    assert explicit_payload["dashboard"]["active_stage"] == "idea"  # type: ignore[index]
    work_items = project_home_payload["project_home"]["work_items"]  # type: ignore[index]
    assert work_items[0]["active_stage"] == "qa"


def test_ui_dashboard_endpoint_defaults_runtime_failure_to_failed_stage_when_stage_is_omitted(
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
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    (attempt_root / RUN_RUNTIME_EXIT_METADATA_FILENAME).write_text(
        json.dumps(
            {
                "exit_code": 130,
                "exit_classification": "cancelled",
                "adapter_outcome": "cancelled",
                "completed_at_utc": "2026-07-09T08:26:12Z",
            }
        ),
        encoding="utf-8",
    )
    service = _service(workspace_root)

    default_payload = _payload(service.handle_get("/api/dashboard", {"run_id": ["run-ui"]}))
    explicit_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["idea"], "run_id": ["run-ui"]})
    )
    project_home_payload = _payload(service.handle_get("/api/project-home", {}))

    default_dashboard = default_payload["dashboard"]  # type: ignore[index]
    explicit_dashboard = explicit_payload["dashboard"]  # type: ignore[index]
    work_items = project_home_payload["project_home"]["work_items"]  # type: ignore[index]
    assert default_dashboard["active_stage"] == "plan"  # type: ignore[index]
    assert default_dashboard["first_failure"]["stage"] == "plan"  # type: ignore[index]
    assert default_dashboard["primary_artifact"]["key"] == "plan"  # type: ignore[index]
    assert any(
        action["action"] == "resume-stage" and action["stage"] == "plan"
        for action in default_dashboard["recovery_actions"]  # type: ignore[index,union-attr]
    )
    assert explicit_dashboard["active_stage"] == "idea"  # type: ignore[index]
    assert explicit_dashboard["first_failure"]["stage"] == "plan"  # type: ignore[index]
    assert work_items[0]["active_stage"] == "plan"


def test_ui_dashboard_endpoint_exposes_run_history_lineage_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(
        workspace_root,
        lineage={
            "source_run_id": "run-source<script>",
            "source_work_item_id": "WI-SOURCE<&>",
            "baseline_id": "baseline-main",
            "baseline_label": "main before UI handoff <candidate>",
            "child_work_item_candidates": [
                {
                    "work_item_id": "WI-CHILD",
                    "label": "Retry risky QA <script>",
                    "relationship": "follow-up",
                    "source_run_id": "run-ui",
                }
            ],
        },
    )
    service = _service(workspace_root)

    payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["qa"], "run_id": ["run-ui"]})
    )

    dashboard = payload["dashboard"]
    lineage = dashboard["run"]["lineage"]  # type: ignore[index]
    assert lineage["source_run_id"] == "run-source<script>"  # type: ignore[index]
    assert lineage["source_work_item_id"] == "WI-SOURCE<&>"  # type: ignore[index]
    assert lineage["baseline_label"] == "main before UI handoff <candidate>"  # type: ignore[index]
    assert lineage["child_work_item_candidates"][0] == {  # type: ignore[index]
        "work_item_id": "WI-CHILD",
        "label": "Retry risky QA <script>",
        "relationship": "follow-up",
        "source_run_id": "run-ui",
    }
    assert any(
        artifact["key"] == "runtime_log"
        for artifact in dashboard["recent_artifacts"]  # type: ignore[index]
    )


def test_ui_next_flow_source_findings_endpoint_groups_source_context(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/next-flow/source-findings", {"run_id": ["run-ui"]}))

    groups = {group["id"]: group for group in payload["groups"]}  # type: ignore[index]
    assert set(groups) == {
        "qa-findings",
        "review-notes",
        "failed-evidence",
        "manual-request",
    }
    qa_items = groups["qa-findings"]["items"]
    assert groups["qa-findings"]["count"] == len(qa_items)
    assert any(
        item["kind"] == "qa-finding"
        and item["artifact_key"] == "qa_report"
        and item["display_label"] == "Final QA report"
        and item["priority"] == 10
        and item["recommended"] is True
        and item["collapsible"] is False
        and item["source_path"].endswith("qa-report.md")
        and item["selected"] is True
        for item in qa_items
    )
    assert any(
        item["kind"] == "qa-finding"
        and item["artifact_key"] == "runtime_log"
        and item["collapsible"] is True
        and item["recommended"] is False
        for item in qa_items
    )
    manual_items = groups["manual-request"]["items"]
    assert manual_items == [
        {
            "id": "manual-request:operator-note",
            "kind": "manual-request",
            "title": "Manual operator request",
            "display_label": "Manual request",
            "detail": "Add a scoped operator note in the follow-up definition step.",
            "priority": 40,
            "recommended": False,
            "collapsible": False,
            "stage": None,
            "artifact_key": None,
            "artifact_kind": None,
            "source_path": None,
            "selected": False,
        }
    ]
    assert payload["counts"]["required_context_groups"] == 4  # type: ignore[index]
    assert payload["counts"]["selected_defaults"] >= 1  # type: ignore[index]
    assert payload["counts"]["recommended_items"] >= 1  # type: ignore[index]
    assert payload["counts"]["collapsible_items"] >= 1  # type: ignore[index]
    assert payload["counts"]["source_artifact_links"] >= 4  # type: ignore[index]
    assert "Clean QA run" in payload["recommendation"]


def test_ui_next_flow_follow_up_draft_endpoint_returns_editable_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/follow-up-draft",
        {
            "source_run_id": "run-ui",
            "selected_source_ids": ["qa-finding:qa:qa_report"],
        },
    )

    payload = _payload(response)
    draft = payload["draft"]
    assert draft["source_work_item"] == "WI-UI"  # type: ignore[index]
    assert draft["source_run_id"] == "run-ui"  # type: ignore[index]
    assert draft["new_work_item"] == "WI-UI-FOLLOW-UP"  # type: ignore[index]
    assert "Follow-up for WI-UI from run-ui" == draft["title"]  # type: ignore[index]
    assert draft["selected_sources"][0]["source_path"].endswith("qa-report.md")  # type: ignore[index]
    assert "Resolve follow-up source: QA artifact: qa_report" in draft["acceptance_criteria"]  # type: ignore[index]
    assert "Updated evidence for QA artifact: qa_report" in draft["required_evidence"]  # type: ignore[index]
    assert any(
        item["id"] == "source-run-lineage" and item["enabled"] is True
        for item in draft["inherited_context"]  # type: ignore[index]
    )
    assert "Source run: `run-ui`." in draft["first_stage_input_preview"]  # type: ignore[index]
    assert "`qa-finding` QA artifact: qa_report" in draft["first_stage_input_preview"]  # type: ignore[index]


def test_ui_next_flow_follow_up_draft_create_endpoint_writes_core_draft(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-FOLLOW-UP",
            "title": "Fix QA follow-up from UI",
            "selected_source_ids": ["qa-finding:qa:qa_report"],
            "first_stage_input": (
                "# Edited UI follow-up\n\nPersist this edited first-stage input before launch."
            ),
            "acceptance_criteria": ["Edited UI acceptance criterion"],
            "required_evidence": ["Edited UI evidence bundle"],
            "inherited_context": ["Source run lineage: run-ui"],
        },
    )

    assert response.status == HTTPStatus.CREATED
    payload = json.loads(response.body.decode("utf-8"))
    draft = payload["draft"]
    created = payload["created"]
    assert draft["title"] == "Fix QA follow-up from UI"
    assert draft["acceptance_criteria"] == ["Edited UI acceptance criterion"]
    assert draft["required_evidence"] == ["Edited UI evidence bundle"]
    assert draft["inherited_context_lines"] == ["Source run lineage: run-ui"]
    assert "Persist this edited first-stage input" in draft["first_stage_input_preview"]
    assert created["work_item"] == "WI-UI-FOLLOW-UP"
    assert created["request_path"] == ("workitems/WI-UI-FOLLOW-UP/context/follow-up-request.md")
    request_path = workspace_root / created["request_path"]
    assert request_path.exists()
    request_text = request_path.read_text(encoding="utf-8")
    user_request_text = (
        workspace_root / "workitems" / "WI-UI-FOLLOW-UP" / "context" / "user-request.md"
    ).read_text(encoding="utf-8")
    assert "Persist this edited first-stage input before launch." in user_request_text
    assert "Edited UI acceptance criterion" in request_text
    assert "Edited UI evidence bundle" in request_text
    assert "Source run lineage: run-ui" in request_text
    assert "`workitems/WI-UI/stages/qa/qa-report.md`" in request_path.read_text(encoding="utf-8")
    assert created["context"]["user_request_path"] == (  # type: ignore[index]
        "workitems/WI-UI-FOLLOW-UP/context/user-request.md"
    )
    assert not (workspace_root / "reports" / "runs" / "WI-UI-FOLLOW-UP").exists()


def test_ui_next_flow_clone_draft_create_endpoint_writes_core_draft(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/clone-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-CLONE",
            "title": "Clone completed QA flow",
        },
    )

    assert response.status == HTTPStatus.CREATED
    payload = json.loads(response.body.decode("utf-8"))
    created = payload["created"]
    assert payload["draft"]["new_work_item"] == "WI-UI-CLONE"
    assert created["draft_path"] == "workitems/WI-UI-CLONE/context/clone-flow-draft.md"
    assert created["config"]["runtime_id"] == "codex"
    assert created["config"]["stage_target"] == "qa"
    assert (
        workspace_root / "workitems" / "WI-UI-CLONE" / "context" / "clone-flow-draft.md"
    ).exists()
    assert not (workspace_root / "reports" / "runs" / "WI-UI-CLONE").exists()


def test_ui_next_flow_clone_draft_create_conflicts_for_existing_work_item(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    payload = {
        "source_run_id": "run-ui",
        "new_work_item": "WI-UI-CLONE",
        "title": "Duplicate clone work item",
    }
    first_response = service.handle_post("/api/next-flow/clone-draft/create", payload)
    response = service.handle_post("/api/next-flow/clone-draft/create", payload)

    assert first_response.status == HTTPStatus.CREATED
    assert response.status == HTTPStatus.CONFLICT
    payload = _error_payload(response)
    assert "Request context documents already exist for work item 'WI-UI-CLONE'" in payload["error"]


def test_ui_next_flow_follow_up_draft_create_conflicts_for_existing_work_item(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    payload = {
        "source_run_id": "run-ui",
        "new_work_item": "WI-UI-FOLLOW-UP",
        "title": "Duplicate follow-up work item",
        "selected_source_ids": ["qa-finding:qa:qa_report"],
    }
    first_response = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        payload,
    )
    response = service.handle_post("/api/next-flow/follow-up-draft/create", payload)

    assert first_response.status == HTTPStatus.CREATED
    assert response.status == HTTPStatus.CONFLICT
    payload = _error_payload(response)
    assert (
        "Request context documents already exist for work item 'WI-UI-FOLLOW-UP'"
        in payload["error"]
    )


def test_ui_next_flow_draft_create_endpoints_return_deterministic_bad_requests(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    malformed_follow_up = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {"source_run_id": "run-ui", "selected_source_ids": "qa-finding:qa:qa_report"},
    )
    malformed_editable_fields = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {
            "source_run_id": "run-ui",
            "selected_source_ids": ["qa-finding:qa:qa_report"],
            "acceptance_criteria": "not-a-list",
        },
    )
    manual_without_artifact = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-MANUAL-FOLLOW-UP",
            "title": "Manual follow-up request",
            "selected_source_ids": ["manual-request:operator-note"],
        },
    )
    malformed_clone = service.handle_post(
        "/api/next-flow/clone-draft/create",
        {"new_work_item": "WI-UI-CLONE"},
    )

    assert malformed_follow_up.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(malformed_follow_up)["error"] == ("selected_source_ids must be a list.")
    assert malformed_editable_fields.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(malformed_editable_fields)["error"] == (
        "acceptance_criteria must be a list."
    )
    assert manual_without_artifact.status == HTTPStatus.CREATED
    manual_payload = json.loads(manual_without_artifact.body.decode("utf-8"))
    assert manual_payload["created"]["source_artifact_paths"] == []
    assert "- Source artifact: manual operator request only" in (
        workspace_root / "workitems" / "WI-UI-MANUAL-FOLLOW-UP" / "context" / "follow-up-request.md"
    ).read_text(encoding="utf-8")
    assert malformed_clone.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(malformed_clone)["error"] == "source_run_id is required."


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


def test_ui_onboarding_mode_serves_setup_until_context_handoff(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    captured: dict[str, object] = {}

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        captured.update(kwargs)
        return WorkflowRunResult(
            run_id="run-onboarding-generic",
            executed_stage_count=2,
            completed=True,
            incomplete=(),
        )

    service = _onboarding_service_with_runner(
        tmp_path,
        monkeypatch,
        workflow_runner=fake_workflow_runner,
    )

    state_payload = _payload(service.handle_get("/api/onboarding/state", {}))
    blocked_dashboard = service.handle_get("/api/dashboard", {})

    assert state_payload["setup_required"] is True
    assert "Complete project setup" in _error_payload(blocked_dashboard)["error"]

    inspect_payload = _payload(
        service.handle_post("/api/onboarding/project", {"project_root": "project"})
    )
    assert inspect_payload["project"]["project_root"] == project_root.as_posix()  # type: ignore[index]
    assert inspect_payload["project"]["workspace_exists"] is False  # type: ignore[index]
    assert {
        runtime["runtime_id"]
        for runtime in inspect_payload["readiness"]["runtimes"]  # type: ignore[index]
    } >= {"codex", "claude-code", "opencode", "qwen", "generic-cli"}

    created_payload = _payload(
        service.handle_post(
            "/api/onboarding/work-item",
            {
                "action": "create",
                "project_root": "project",
                "work_item": "WI-ONBOARD",
                "request": "Implement UI onboarding smoke.",
            },
        )
    )

    assert created_payload["context"]["work_item"] == "WI-ONBOARD"  # type: ignore[index]
    assert (
        created_payload["context"]["workspace_root"]
        == (  # type: ignore[index]
            project_root / ".aidd"
        ).as_posix()
    )
    assert (
        (project_root / ".aidd" / "workitems" / "WI-ONBOARD" / "context" / "user-request.md")
        .read_text(encoding="utf-8")
        .endswith("Implement UI onboarding smoke.\n")
    )

    active_state_payload = _payload(service.handle_get("/api/onboarding/state", {}))
    dashboard_payload = _payload(service.handle_get("/api/dashboard", {}))
    missing_runtime = service.handle_post("/api/workflow/run", {})
    workflow_payload = _payload(
        service.handle_post(
            "/api/workflow/run",
            {"runtime": "generic-cli", "from_stage": "idea", "to_stage": "plan"},
        )
    )
    workflow_job = _wait_job(service, str(workflow_payload["job_id"]))
    workflow_request = captured["request"]

    assert active_state_payload["setup_required"] is False
    assert dashboard_payload["dashboard"]["work_item"] == "WI-ONBOARD"  # type: ignore[index]
    assert _error_payload(missing_runtime)["error"] == "runtime is required."
    assert workflow_job["result"]["run_id"] == "run-onboarding-generic"  # type: ignore[index]
    assert isinstance(workflow_request, WorkflowRunRequest)
    assert workflow_request.work_item == "WI-ONBOARD"
    assert workflow_request.runtime_id == "generic-cli"
    assert workflow_request.workspace_root == project_root.resolve() / ".aidd"
    assert workflow_request.config_path == project_root.resolve() / "aidd.test.toml"
    assert workflow_request.stage_start == "idea"
    assert workflow_request.stage_end == "plan"


def test_ui_onboarding_can_resume_existing_project_work_item(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    creator = _onboarding_service(tmp_path, monkeypatch)
    _payload(
        creator.handle_post(
            "/api/onboarding/work-item",
            {
                "action": "create",
                "project_root": "project",
                "work_item": "WI-RESUME",
                "request": "Resume from setup.",
            },
        )
    )
    service = _onboarding_service(tmp_path, monkeypatch)

    inspect_payload = _payload(
        service.handle_post("/api/onboarding/project", {"project_root": "project"})
    )
    resumed_payload = _payload(
        service.handle_post(
            "/api/onboarding/work-item",
            {
                "action": "resume",
                "project_root": "project",
                "work_item": "WI-RESUME",
            },
        )
    )

    assert inspect_payload["project"]["work_items"] == [  # type: ignore[index]
        {"has_request_context": True, "work_item": "WI-RESUME"}
    ]
    assert resumed_payload["context"]["work_item"] == "WI-RESUME"  # type: ignore[index]
    assert _payload(service.handle_get("/api/dashboard", {}))["dashboard"]["work_item"] == (
        "WI-RESUME"
    )


def test_ui_onboarding_create_requires_request_and_safe_work_item_id(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    service = _onboarding_service(tmp_path, monkeypatch)

    missing_request = service.handle_post(
        "/api/onboarding/work-item",
        {
            "action": "create",
            "project_root": "project",
            "work_item": "WI-NO-REQUEST",
        },
    )
    unsafe_work_item = service.handle_post(
        "/api/onboarding/work-item",
        {
            "action": "create",
            "project_root": "project",
            "work_item": "../WI-ESCAPE",
            "request": "Keep the work item inside the selected workspace.",
        },
    )

    assert _error_payload(missing_request)["error"] == "request is required."
    assert "work_item" in _error_payload(unsafe_work_item)["error"]  # type: ignore[operator]
    assert not (project_root / ".aidd" / "WI-ESCAPE").exists()


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
    answers_text = answers_path.read_text(encoding="utf-8")
    assert "- Q1 [resolved] Release target is 0.2.0." in answers_text
    assert "- `Q1` `[resolved]`" not in answers_text


def test_ui_stage_endpoint_exposes_interview_recovery_answer_states(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    questions_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "questions.md"
    questions_path.write_text(
        "\n".join(
            (
                "# Questions",
                "",
                "## Questions",
                "",
                "- `Q1` `[blocking]` Confirm release target.",
                "- `Q2` `[blocking]` Confirm rollout risk.",
                "- `Q3` `[blocking]` Confirm owner signoff.",
            )
        ),
        encoding="utf-8",
    )
    service = _service(workspace_root)
    for question_id, resolution in (
        ("Q1", "resolved"),
        ("Q2", "partial"),
        ("Q3", "deferred"),
    ):
        _payload(
            service.handle_post(
                "/api/answers",
                {
                    "stage": "plan",
                    "question_id": question_id,
                    "text": f"{question_id} answer",
                    "resolution": resolution,
                },
            )
        )

    payload = _payload(service.handle_get("/api/stage", {"stage": ["plan"], "run_id": ["run-ui"]}))
    questions = {item["question_id"]: item for item in payload["questions"]["questions"]}  # type: ignore[index]

    assert payload["diagnostics"]["blocking_questions"]["unresolved_question_ids"] == [  # type: ignore[index]
        "Q2",
        "Q3",
    ]
    assert questions["Q1"]["status"] == "resolved"
    assert questions["Q1"]["answer_resolution"] == "resolved"
    assert questions["Q2"]["status"] == "pending-blocking"
    assert questions["Q2"]["answer_resolution"] == "partial"
    assert questions["Q3"]["status"] == "pending-blocking"
    assert questions["Q3"]["answer_resolution"] == "deferred"


def test_ui_stage_endpoint_exposes_repair_and_explicit_stop_recovery_states(
    tmp_path: Path,
) -> None:
    repair_root = tmp_path / "repair" / ".aidd"
    _prepare_run(repair_root)
    repair_stage_root = repair_root / "workitems" / "WI-UI" / "stages" / "plan"
    persist_repair_history_snapshot(
        workspace_root=repair_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
        trigger="repair",
        outcome="failed validation",
        stage_status="repair-needed",
        validator_report_path=repair_stage_root / "validator-report.md",
        repair_brief_path=repair_stage_root / "repair-brief.md",
    )
    persist_stage_status(
        workspace_root=repair_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="repair-needed",
    )
    repair_payload = _payload(
        _service(repair_root).handle_get("/api/stage", {"stage": ["plan"], "run_id": ["run-ui"]})
    )

    validation = repair_payload["diagnostics"]["validation"]  # type: ignore[index]
    assert repair_payload["diagnostics"]["status"] == "repair-available"  # type: ignore[index]
    assert validation["status"] == "repair-available"
    assert validation["repair_attempts"][0]["trigger"] == "repair"
    assert validation["repair_attempts"][0]["outcome"] == "failed validation"

    stopped_root = tmp_path / "stopped" / ".aidd"
    _prepare_run(stopped_root)
    stopped_stage_root = stopped_root / "workitems" / "WI-UI" / "stages" / "plan"
    stopped_stage_root.joinpath("validator-report.md").write_text(
        "# Validator Report\n\n- Verdict: `pass`\n",
        encoding="utf-8",
    )
    persist_stage_status(
        workspace_root=stopped_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="failed",
    )
    events_path = (
        run_attempt_root(
            workspace_root=stopped_root,
            work_item="WI-UI",
            run_id="run-ui",
            stage="plan",
            attempt_number=1,
        )
        / RUN_EVENTS_JSONL_FILENAME
    )
    events_path.write_text(
        '{"timestamp":"2026-05-28T00:00:00Z","level":"error","event":"stopped",'
        '"message":"Workflow stopped at plan"}\n',
        encoding="utf-8",
    )
    stopped_payload = _payload(
        _service(stopped_root).handle_get("/api/stage", {"stage": ["plan"], "run_id": ["run-ui"]})
    )

    assert stopped_payload["diagnostics"]["status"] == "stopped"  # type: ignore[index]
    assert stopped_payload["diagnostics"]["stopped"]["stopped"] is True  # type: ignore[index]
    assert stopped_payload["diagnostics"]["stopped"]["detail"] == "Workflow stopped at plan"  # type: ignore[index]


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


def test_ui_next_flow_preflight_endpoint_returns_pass_payload(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/preflight",
        {
            "source_run_id": "run-ui",
            "runtime": "generic-cli",
            "baseline_id": "run-ui",
        },
    )

    payload = _payload(response)
    preflight = payload["preflight"]
    assert preflight["status"] == "pass"  # type: ignore[index]
    assert preflight["can_launch"] is True  # type: ignore[index]
    assert preflight["blocking_codes"] == []  # type: ignore[index]
    assert preflight["warning_codes"] == []  # type: ignore[index]
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


def test_ui_next_flow_launch_endpoint_delegates_new_work_item_workflow(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    source_manifest = run_manifest_path(workspace_root, "WI-UI", "run-ui")
    source_before = source_manifest.read_text(encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        request = kwargs["request"]
        assert isinstance(request, WorkflowRunRequest)
        captured["request"] = request
        return WorkflowRunResult(
            run_id=request.run_id or "run-follow-up-ui",
            executed_stage_count=0,
            completed=True,
            incomplete=(),
            exit_code=0,
        )

    service = _service(workspace_root, workflow_runner=fake_workflow_runner)

    response = service.handle_post(
        "/api/next-flow/launch",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-FOLLOW-UP",
            "runtime": "codex",
            "baseline_id": "run-ui",
            "run_id": "run-follow-up-ui",
            "from_stage": "idea",
            "to_stage": "qa",
        },
    )

    assert response.status == HTTPStatus.ACCEPTED
    payload = json.loads(response.body.decode("utf-8"))
    job_payload = _wait_job(service, str(payload["job_id"]))
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert payload["kind"] == "next-flow-launch"
    assert payload["work_item"] == "WI-UI-FOLLOW-UP"
    assert payload["preflight"]["status"] == "pass"
    assert job_payload["status"] == "completed"
    assert request.work_item == "WI-UI-FOLLOW-UP"
    assert request.runtime_id == "codex"
    assert request.run_id == "run-follow-up-ui"
    assert request.stage_start == "idea"
    assert request.stage_end == "qa"
    assert request.config_snapshot["mode"] == "ui-next-flow-launch"
    assert request.lineage == {
        "baseline_id": "run-ui",
        "relationship": "follow-up",
        "source_run_id": "run-ui",
        "source_work_item_id": "WI-UI",
    }
    assert source_manifest.read_text(encoding="utf-8") == source_before


def test_ui_next_flow_launch_endpoint_requires_runtime_before_preflight(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/launch",
        {"source_run_id": "run-ui", "new_work_item": "WI-UI-FOLLOW-UP"},
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(response)["error"] == "runtime is required."


def test_ui_next_flow_launch_endpoint_returns_blocked_preflight_payload(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path / ".aidd")

    response = service.handle_post(
        "/api/next-flow/launch",
        {
            "source_run_id": "run-missing",
            "new_work_item": "WI-UI-FOLLOW-UP",
            "runtime": "generic-cli",
        },
    )

    assert response.status == HTTPStatus.CONFLICT
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["error"] == "next-flow launch preflight blocked"
    assert "source-run-missing" in payload["blocking_codes"]


def test_ui_next_flow_archive_endpoint_records_decision_and_keeps_artifacts_readable(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    qa_report_path = workspace_root / "workitems" / "WI-UI" / "stages" / "qa" / "qa-report.md"
    original_qa_report = qa_report_path.read_text(encoding="utf-8")
    manifest_path = run_manifest_path(workspace_root, "WI-UI", "run-ui")
    manifest_before = manifest_path.read_bytes()
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/next-flow/archive",
        {
            "source_run_id": "run-ui",
            "reason": "Archive after QA acceptance.",
        },
    )

    payload = _payload(response)
    artifact_payload = _payload(
        service.handle_get(
            "/api/artifacts/document",
            {
                "stage": ["qa"],
                "key": ["qa_report"],
                "run_id": ["run-ui"],
                "mode": ["source"],
            },
        )
    )
    history_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["qa"], "run_id": ["run-ui"]})
    )

    assert payload["archive"]["archived"] is True  # type: ignore[index]
    assert payload["archive"]["reason"] == "Archive after QA acceptance."  # type: ignore[index]
    assert payload["dashboard"]["run"]["archive"]["archived"] is True  # type: ignore[index]
    assert payload["dashboard"]["run"]["archive"]["source"] == "ui"  # type: ignore[index]
    assert manifest_path.read_bytes() == manifest_before
    assert history_payload["dashboard"]["run"]["archive"]["archived"] is True  # type: ignore[index]
    assert artifact_payload["text"] == original_qa_report
    assert qa_report_path.read_text(encoding="utf-8") == original_qa_report


def test_ui_next_flow_archive_endpoint_rejects_malformed_or_non_terminal_requests(
    tmp_path: Path,
) -> None:
    terminal_workspace = tmp_path / "terminal" / ".aidd"
    _prepare_completed_qa_run(terminal_workspace)
    terminal_service = _service(terminal_workspace)

    malformed = terminal_service.handle_post(
        "/api/next-flow/archive",
        {"source_run_id": "run-ui", "reason": ["not", "a", "string"]},
    )

    non_terminal_workspace = tmp_path / "non-terminal" / ".aidd"
    _prepare_run(non_terminal_workspace)
    non_terminal_service = _service(non_terminal_workspace)
    non_terminal = non_terminal_service.handle_post(
        "/api/next-flow/archive",
        {"source_run_id": "run-ui", "reason": "Not terminal yet."},
    )

    assert malformed.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(malformed)["error"] == "reason must be a string."
    assert non_terminal.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(non_terminal)["error"] == ("archive decision requires a terminal QA run.")


def test_ui_completed_run_next_action_service_regression_sequence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    source_manifest_path = run_manifest_path(workspace_root, "WI-UI", "run-ui")
    source_manifest_before_bytes = source_manifest_path.read_bytes()
    source_manifest_before = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    qa_report_path = workspace_root / "workitems" / "WI-UI" / "stages" / "qa" / "qa-report.md"
    qa_report_before = qa_report_path.read_text(encoding="utf-8")
    service = _service(workspace_root)

    dashboard_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["qa"], "run_id": ["run-ui"]})
    )
    handoff = dashboard_payload["dashboard"]["terminal_handoff"]  # type: ignore[index]
    actions = {
        action["action"]
        for action in handoff["recommended_next_flow_actions"]  # type: ignore[index]
    }
    follow_up = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-FOLLOW-UP",
            "title": "Fix completed-run QA finding",
            "selected_source_ids": ["qa-finding:qa:qa_report"],
        },
    )
    clone = service.handle_post(
        "/api/next-flow/clone-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-UI-CLONE",
            "title": "Clone completed flow",
        },
    )
    preflight_payload = _payload(
        service.handle_post(
            "/api/next-flow/preflight",
            {
                "source_run_id": "run-ui",
                "runtime": "codex",
                "baseline_id": "run-ui",
            },
        )
    )
    archive_payload = _payload(
        service.handle_post(
            "/api/next-flow/archive",
            {
                "source_run_id": "run-ui",
                "reason": "Archive after service-level next-action regression.",
            },
        )
    )
    source_manifest_after = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    follow_up_payload = json.loads(follow_up.body.decode("utf-8"))
    clone_payload = json.loads(clone.body.decode("utf-8"))

    assert dashboard_payload["dashboard"]["next_action"]["action"] == "review-complete"  # type: ignore[index]
    assert actions == {
        "create-new-work-item",
        "start-follow-up-flow",
        "clone-flow",
        "run-eval-batch",
        "archive-run",
    }
    assert follow_up.status == HTTPStatus.CREATED
    assert follow_up_payload["created"]["work_item"] == "WI-UI-FOLLOW-UP"
    assert clone.status == HTTPStatus.CREATED
    assert clone_payload["created"]["work_item"] == "WI-UI-CLONE"
    assert preflight_payload["preflight"]["status"] == "pass"  # type: ignore[index]
    assert preflight_payload["preflight"]["can_launch"] is True  # type: ignore[index]
    assert archive_payload["dashboard"]["run"]["archive"]["archived"] is True  # type: ignore[index]
    assert source_manifest_path.read_bytes() == source_manifest_before_bytes
    assert source_manifest_after["run_id"] == source_manifest_before["run_id"]
    assert source_manifest_after["runtime_id"] == source_manifest_before["runtime_id"]
    assert source_manifest_after["stage_target"] == source_manifest_before["stage_target"]
    assert qa_report_path.read_text(encoding="utf-8") == qa_report_before
    assert not (workspace_root / "reports" / "runs" / "WI-UI-FOLLOW-UP").exists()
    assert not (workspace_root / "reports" / "runs" / "WI-UI-CLONE").exists()


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
    dashboard_payload = _payload(service.handle_get("/api/dashboard", {}))
    options = captured["options"]
    assert isinstance(options, StageRunOptions)
    assert running_payload["status"] == "running"
    assert dashboard_payload["active_job"]["job_id"] == job_id  # type: ignore[index]
    assert dashboard_payload["active_job"]["status"] == "running"  # type: ignore[index]
    assert dashboard_payload["active_job"]["runtime_log_chunk_count"] == 1  # type: ignore[index]
    assert isinstance(running_payload["elapsed_seconds"], int)
    assert running_payload["last_output_at_utc"] is not None
    assert running_payload["last_output_age_seconds"] is not None
    assert running_payload["last_output_text"] == "runtime-output-line"
    assert running_payload["runtime_output_at_utc"] is not None
    assert running_payload["runtime_output_age_seconds"] is not None
    assert running_payload["runtime_output_text"] == "runtime-output-line"
    assert running_payload["runtime_log_chunk_count"] == 1
    assert running_payload["silence_warning"] is False
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
    assert all("time_utc" in chunk for chunk in logs_payload["chunks"])  # type: ignore[operator]

    release.set()
    completed_payload = _wait_job(service, job_id)
    assert completed_payload["status"] == "completed"
    assert completed_payload["result"]["completed"] is True  # type: ignore[index]
    terminal_dashboard_payload = _payload(service.handle_get("/api/dashboard", {}))
    assert terminal_dashboard_payload["active_job"] is None


def test_ui_live_job_status_distinguishes_system_logs_from_runtime_output(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    started = threading.Event()
    release = threading.Event()

    def fake_stage_runner(options: StageRunOptions) -> None:
        started.set()
        assert release.wait(timeout=2)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/stage/run",
        {
            "stage": "plan",
            "runtime": "codex",
            "run_id": "run-ui-system-only",
            "log_follow": True,
        },
    )

    payload = _payload(response)
    job_id = str(payload["job_id"])
    assert started.wait(timeout=2)

    running_payload = _payload(service.handle_get(f"/api/jobs/{job_id}", {}))
    logs_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/logs", {"cursor": ["0"]}))

    assert running_payload["status"] == "running"
    assert running_payload["last_output_at_utc"] is not None
    assert running_payload["last_output_age_seconds"] is not None
    assert running_payload["last_output_text"] == "AIDD UI stage job started."
    assert running_payload["runtime_output_at_utc"] is None
    assert running_payload["runtime_output_age_seconds"] is None
    assert running_payload["runtime_output_text"] is None
    assert running_payload["runtime_log_chunk_count"] == 0
    assert running_payload["silence_warning"] is False
    assert any(
        chunk["stream"] == "system" and "AIDD UI stage job started." in str(chunk["text"])
        for chunk in logs_payload["chunks"]  # type: ignore[index]
    )

    release.set()
    completed_payload = _wait_job(service, job_id)
    assert completed_payload["status"] == "completed"


def test_ui_operator_control_center_endpoints_return_structured_views(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project_root = _prepare_ui_project_repo(tmp_path, monkeypatch)
    workspace_root = project_root / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    _write_operator_control_reports(workspace_root)
    project_root.joinpath("app.py").write_text("print('new')\n", encoding="utf-8")
    project_root.joinpath("untracked.py").write_text("print('new')\n", encoding="utf-8")
    service = _service(workspace_root)

    timeline = _payload(
        service.handle_get(
            "/api/run/timeline",
            {"run_id": ["run-ui"], "stage": ["implement"]},
        )
    )
    diff = _payload(
        service.handle_get(
            "/api/repository/diff",
            {"run_id": ["run-ui"], "stage": ["implement"]},
        )
    )
    accountability = _payload(service.handle_get("/api/run/accountability", {"run_id": ["run-ui"]}))
    implementation = _payload(service.handle_get("/api/implement/evidence", {"run_id": ["run-ui"]}))
    review = _payload(service.handle_get("/api/review/findings", {"run_id": ["run-ui"]}))
    qa = _payload(service.handle_get("/api/qa/verdict", {"run_id": ["run-ui"]}))

    assert timeline["events"]
    assert accountability["runtime_id"] == "codex"
    assert accountability["stage_graph"][:3] == ["idea", "research", "plan"]
    assert "config_snapshot" in accountability
    assert "prompt_pack_provenance" in accountability
    assert "attempts" in accountability
    source_paths = {item["path"] for item in diff["source_files"]}  # type: ignore[index]
    assert {"app.py", "untracked.py"}.issubset(source_paths)
    assert diff["aidd_artifacts"]  # type: ignore[index]
    assert implementation["selected_task_id"] == "TASK-1"
    assert review["approval_status"] == "rejected"
    assert review["findings"][0]["finding_id"] == "RV-1"  # type: ignore[index]
    assert qa["quality_verdict"] == "not-ready"


def test_ui_run_comparison_endpoint_is_bounded_and_work_item_scoped(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    for run_id, status, text in (
        ("run-a", "blocked", "baseline input\n"),
        ("run-b", "succeeded", "target input\n"),
    ):
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            runtime_id="generic-cli",
            stage_target="plan",
            config_snapshot={"mode": "comparison-test"},
        )
        create_next_attempt_directory(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            stage="plan",
        )
        persist_stage_status(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            stage="plan",
            status=status,
        )
        run_attempt_root(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            stage="plan",
            attempt_number=1,
        ).joinpath("input-bundle.md").write_text(text, encoding="utf-8")
    create_run_manifest(
        workspace_root=workspace_root,
        work_item="WI-OTHER",
        run_id="run-other",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "comparison-test"},
    )
    service = _service(workspace_root)

    missing = service.handle_get("/api/run/comparison", {"target_run_id": ["run-b"]})
    assert "baseline_run_id is required" in _error_payload(missing)["error"]  # type: ignore[operator]
    payload = _payload(
        service.handle_get(
            "/api/run/comparison",
            {"baseline_run_id": ["run-a"], "target_run_id": ["run-b"]},
        )
    )
    assert payload["baseline"]["run_id"] == "run-a"  # type: ignore[index]
    assert payload["target"]["run_id"] == "run-b"  # type: ignore[index]
    stage_delta = next(
        item
        for item in payload["stage_status_deltas"]
        if item["stage"] == "plan"  # type: ignore[index]
    )
    assert stage_delta["status"] == "changed"
    assert stage_delta["baseline_status"] == "blocked"
    assert stage_delta["target_status"] == "succeeded"

    cross_work_item = service.handle_get(
        "/api/run/comparison",
        {"baseline_run_id": ["run-a"], "target_run_id": ["run-other"]},
    )
    assert cross_work_item.status == 400
    assert "run-other" in _error_payload(cross_work_item)["error"]  # type: ignore[operator]


def test_ui_remediation_launch_requires_runtime_before_request_creation(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/remediation/launch",
        {
            "source_stage": "review",
            "source_ids": ["RV-1"],
            "target_stage": "implement",
            "operator_note": "Fix it.",
            "run_id": "run-ui",
        },
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert _error_payload(response)["error"] == "runtime is required."
    requests = _payload(service.handle_get("/api/remediation/requests", {"run_id": ["run-ui"]}))
    assert requests["requests"] == []


def test_ui_remediation_launch_requires_finalization_before_marking_downstream_stale(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    _write_operator_control_reports(workspace_root)
    captured: list[StageRunOptions] = []

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured.append(options)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/launch",
        {
            "source_stage": "review",
            "source_ids": ["RV-1"],
            "target_stage": "implement",
            "operator_note": "Fix rejected review finding.",
            "runtime": "generic-cli",
            "run_id": "run-ui",
        },
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    completed = _wait_job(service, str(payload["job_id"]))
    status = _payload(service.handle_get("/api/remediation/status", {"run_id": ["run-ui"]}))
    dashboard = _payload(
        service.handle_get("/api/dashboard", {"run_id": ["run-ui"], "stage": ["qa"]})
    )
    stages = {
        item["stage"]: item
        for item in dashboard["dashboard"]["stages"]  # type: ignore[index]
    }
    assert captured == []
    assert completed["status"] == "failed"
    assert "tasklist" in str(completed).lower()
    assert status["stale_stages"] == []
    assert stages["review"]["stale"] is False
    assert stages["qa"]["stale"] is False


def test_ui_remediation_request_rejects_ids_missing_from_source_report(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    _write_operator_control_reports(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/remediation/request",
        {
            "source_stage": "review",
            "source_ids": ["RV-404"],
            "target_stage": "implement",
            "operator_note": "Fix missing finding.",
            "run_id": "run-ui",
        },
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert "source_ids do not match review report" in _error_payload(response)["error"]
    requests = _payload(service.handle_get("/api/remediation/requests", {"run_id": ["run-ui"]}))
    assert requests["requests"] == []


def test_ui_remediation_launch_accepts_operator_audit_source_id_with_explicit_flag(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    _write_operator_control_reports(workspace_root)
    captured: list[StageRunOptions] = []

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured.append(options)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/launch",
        {
            "source_stage": "review",
            "source_ids": ["OP-RV-1"],
            "target_stage": "implement",
            "operator_note": "Fix operator audit finding.",
            "runtime": "generic-cli",
            "run_id": "run-ui",
            "allow_operator_audit_source_ids": True,
        },
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    completed = _wait_job(service, str(payload["job_id"]))
    requests = _payload(service.handle_get("/api/remediation/requests", {"run_id": ["run-ui"]}))
    assert completed["status"] == "failed"
    assert captured == []
    assert requests["requests"][0]["source_ids"] == ["OP-RV-1"]  # type: ignore[index]


def test_ui_remediation_request_accepts_structured_qa_risk_id(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    _write_operator_control_reports(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/remediation/request",
        {
            "source_stage": "qa",
            "source_ids": ["risk-1"],
            "target_stage": "implement",
            "operator_note": "Fix QA risk.",
            "run_id": "run-ui",
        },
    )

    payload = _payload_with_status(response, HTTPStatus.CREATED)
    assert payload["source_ids"] == ["risk-1"]
    assert payload["source_stage"] == "qa"


def test_ui_remediation_rerun_downstream_runs_review_qa_and_clears_stale(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="qa",
        source_ids=("risk-1",),
        operator_note="Fix QA risk.",
    )
    mark_downstream_stale(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by=request.request_id,
    )
    captured: list[StageRunOptions] = []

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured.append(options)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/rerun-downstream",
        {"runtime": "generic-cli", "run_id": "run-ui"},
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    completed = _wait_job(service, str(payload["job_id"]))
    status = _payload(service.handle_get("/api/remediation/status", {"run_id": ["run-ui"]}))
    assert [options.stage for options in captured] == ["review", "qa"]
    assert all(options.runtime == "generic-cli" for options in captured)
    assert completed["status"] == "completed"
    assert completed["result"]["rerun_stages"] == ["review", "qa"]  # type: ignore[index]
    assert status["stale_stages"] == []


def test_ui_remediation_rerun_downstream_clears_successful_stages_before_failure(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="review",
        source_ids=("RV-1",),
        operator_note="Fix review finding.",
    )
    mark_downstream_stale(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by=request.request_id,
    )
    captured: list[StageRunOptions] = []

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured.append(options)
        if options.stage == "qa":
            raise typer.Exit(1)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/rerun-downstream",
        {"runtime": "generic-cli", "run_id": "run-ui"},
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    failed = _wait_job_status(service, str(payload["job_id"]), "failed")
    status = _payload(service.handle_get("/api/remediation/status", {"run_id": ["run-ui"]}))

    assert [options.stage for options in captured] == ["review", "qa"]
    assert failed["result"]["completed"] is False  # type: ignore[index]
    assert failed["result"]["exit_code"] == 1  # type: ignore[index]
    assert [item["stage"] for item in status["stale_stages"]] == ["qa"]  # type: ignore[index]


def test_ui_remediation_rerun_stage_runs_one_stale_stage_and_clears_it(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="review",
        source_ids=("RV-1",),
        operator_note="Fix review finding.",
    )
    mark_downstream_stale(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by=request.request_id,
    )
    captured: list[StageRunOptions] = []

    def fake_stage_runner(options: StageRunOptions) -> None:
        captured.append(options)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/rerun-stage",
        {"runtime": "generic-cli", "run_id": "run-ui", "stage": "review"},
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    completed = _wait_job(service, str(payload["job_id"]))
    status = _payload(service.handle_get("/api/remediation/status", {"run_id": ["run-ui"]}))

    assert [options.stage for options in captured] == ["review"]
    assert captured[0].runtime == "generic-cli"
    assert completed["status"] == "completed"
    assert completed["result"]["rerun_stage"] == "review"  # type: ignore[index]
    assert [item["stage"] for item in status["stale_stages"]] == ["qa"]  # type: ignore[index]


def test_ui_remediation_rerun_stage_does_not_clear_failed_stage(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    request = create_remediation_request(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        source_stage="qa",
        source_ids=("risk-1",),
        operator_note="Fix QA risk.",
    )
    mark_downstream_stale(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by=request.request_id,
    )

    def fake_stage_runner(options: StageRunOptions) -> None:
        if options.stage == "review":
            raise typer.Exit(1)

    service = _service(workspace_root, stage_runner=fake_stage_runner)

    response = service.handle_post(
        "/api/remediation/rerun-stage",
        {"runtime": "generic-cli", "run_id": "run-ui", "stage": "review"},
    )

    payload = _payload_with_status(response, HTTPStatus.ACCEPTED)
    failed = _wait_job_status(service, str(payload["job_id"]), "failed")
    status = _payload(service.handle_get("/api/remediation/status", {"run_id": ["run-ui"]}))

    assert failed["result"]["completed"] is False  # type: ignore[index]
    assert [item["stage"] for item in status["stale_stages"]] == ["review", "qa"]  # type: ignore[index]


def test_ui_remediation_rerun_stage_rejects_non_stale_stage(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_completed_qa_run(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/remediation/rerun-stage",
        {"runtime": "generic-cli", "run_id": "run-ui", "stage": "review"},
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert "is not stale" in _error_payload(response)["error"]


def test_ui_dashboard_exposes_runtime_log_recovery_for_non_zero_exit(
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
    attempt_root = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    (attempt_root / RUN_RUNTIME_EXIT_METADATA_FILENAME).write_text(
        json.dumps(
            {
                "exit_code": 1,
                "exit_classification": "non_zero_exit",
                "adapter_outcome": "failed",
                "completed_at_utc": "2026-07-08T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    service = _service(workspace_root)
    dashboard_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["plan"], "run_id": ["run-ui"]})
    )["dashboard"]

    assert dashboard_payload["first_failure"]["kind"] == "non_zero_exit"  # type: ignore[index]
    assert dashboard_payload["first_failure"]["stage"] == "plan"  # type: ignore[index]
    recovery_actions = dashboard_payload["recovery_actions"]  # type: ignore[index]
    assert any(
        action["action"] == "inspect-runtime-log" and action["stage"] == "plan"
        for action in recovery_actions  # type: ignore[union-attr]
    )
    assert any(
        action["action"] == "request-change" and action["stage"] == "plan"
        for action in recovery_actions  # type: ignore[union-attr]
    )


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

    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))

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
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(runtime_script.as_posix())}"
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
        ).read_text(encoding="utf-8")
    )
    assert runtime_exit["exit_classification"] == "cancelled"
    assert stage_metadata["status"] == "failed"

    dashboard_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["plan"], "run_id": [run_id]})
    )["dashboard"]
    recovery_actions = dashboard_payload["recovery_actions"]  # type: ignore[index]
    assert any(
        action["action"] == "inspect-runtime-log" and action["stage"] == "plan"
        for action in recovery_actions  # type: ignore[union-attr]
    )
    assert any(
        action["action"] == "request-change" and action["stage"] == "plan"
        for action in recovery_actions  # type: ignore[union-attr]
    )


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

    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))

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
    pending_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/operator-requests", {}))
    assert pending_payload["pending_request_ids"] == [request_id]
    assert pending_payload["audit_history"][0]["request_id"] == request_id  # type: ignore[index]
    assert pending_payload["audit_history"][0]["status"] == "pending"  # type: ignore[index]
    assert pending_payload["audit_history"][0]["runtime_id"] == "codex"  # type: ignore[index]
    assert pending_payload["audit_history"][0]["stage"] == "plan"  # type: ignore[index]
    assert pending_payload["audit_history"][0]["command"] == "npm install"  # type: ignore[index]

    decision_payload = _payload(
        service.handle_post(
            f"/api/jobs/{job_id}/operator-requests/{request_id}/decision",
            {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
        )
    )

    assert decision_payload["pending_request_ids"] == []
    assert decision_payload["unapproved_request_ids"] == []
    assert decision_payload["decisions"][0]["source"] == "ui"  # type: ignore[index]
    assert decision_payload["audit_history"][0]["status"] == "approved"  # type: ignore[index]
    assert decision_payload["audit_history"][0]["decision_action"] == "allow_once"  # type: ignore[index]
    assert decision_payload["audit_history"][0]["decision_source"] == "ui"  # type: ignore[index]
    decisions_path = (
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
    )
    assert decisions_path.exists()

    idempotent_payload = _payload(
        service.handle_post(
            f"/api/jobs/{job_id}/operator-requests/{request_id}/decision",
            {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
        )
    )
    assert idempotent_payload["decisions"] == decision_payload["decisions"]
    assert len(decisions_path.read_text(encoding="utf-8").splitlines()) == 1

    conflict = service.handle_post(
        f"/api/jobs/{job_id}/operator-requests/{request_id}/decision",
        {"action": RuntimeOperatorDecisionAction.DENY.value},
    )
    conflict_payload = _payload_with_status(conflict, HTTPStatus.CONFLICT)
    assert conflict_payload["winner"]["action"] == "allow_once"  # type: ignore[index]
    assert len(decisions_path.read_text(encoding="utf-8").splitlines()) == 1


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
    pending_payload = _payload(service.handle_get(f"/api/jobs/{job_id}/operator-requests", {}))
    assert pending_payload["pending_request_ids"] == [request.id]

    decision_payload = _payload(
        service.handle_post(
            f"/api/jobs/{job_id}/operator-requests/{request.id}/decision",
            {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
        )
    )
    assert decision_payload["pending_request_ids"] == []

    completed_payload = _wait_job_status(service, job_id, "completed")
    decision = captured["decision"]
    assert isinstance(decision, RuntimeOperatorDecision)
    assert completed_payload["status"] == "completed"
    assert decision.action is RuntimeOperatorDecisionAction.ALLOW_ONCE


def test_ui_cancellation_wakes_operator_waiter_and_rejects_late_decision(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    request_ready = threading.Event()
    captured: dict[str, RuntimeOperatorDecision | RuntimeOperatorRequest] = {}
    continued = threading.Event()

    def fake_stage_runner(options: StageRunOptions) -> None:
        run_id = options.run_id or "run-ui-cancel-approval"
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            runtime_id=options.runtime,
            stage_target=options.stage,
            config_snapshot={"mode": "ui-cancel-approval-test"},
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
        if decision.is_approval:
            continued.set()

    service = _service(workspace_root, stage_runner=fake_stage_runner)
    response = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex", "run_id": "run-ui-cancel-approval"},
    )
    job_id = str(_payload(response)["job_id"])
    assert request_ready.wait(timeout=2)
    _wait_job_status(service, job_id, "waiting-for-operator")

    cancel_payload = _payload(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))

    assert cancel_payload["status"] == "cancelled"
    for _ in range(100):
        if not service._operator_decisions.has_waiter(job_id):
            break
        time.sleep(0.01)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("operator waiter did not exit")
    decision = captured["decision"]
    request = captured["request"]
    assert isinstance(decision, RuntimeOperatorDecision)
    assert isinstance(request, RuntimeOperatorRequest)
    assert decision.action is RuntimeOperatorDecisionAction.CANCEL
    assert not continued.is_set()

    late = service.handle_post(
        f"/api/jobs/{job_id}/operator-requests/{request.id}/decision",
        {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
    )
    assert late.status == HTTPStatus.CONFLICT
    assert "terminal" in _error_payload(late)["error"]  # type: ignore[operator]


@pytest.mark.parametrize(
    "action",
    [RuntimeOperatorDecisionAction.ALLOW_ONCE, RuntimeOperatorDecisionAction.DENY],
)
def test_ui_operator_decision_and_cancel_race_share_one_winner(
    tmp_path: Path,
    action: RuntimeOperatorDecisionAction,
) -> None:
    workspace_root = tmp_path / ".aidd"
    request_ready = threading.Event()
    release = threading.Event()
    captured: dict[str, RuntimeOperatorDecision | RuntimeOperatorRequest | Path] = {}

    def fake_stage_runner(options: StageRunOptions) -> None:
        run_id = options.run_id or "run-ui-approval-race"
        create_run_manifest(
            workspace_root=workspace_root,
            work_item="WI-UI",
            run_id=run_id,
            runtime_id=options.runtime,
            stage_target=options.stage,
            config_snapshot={"mode": "ui-approval-race-test"},
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
        captured.update(request=request, attempt_path=attempt_path)
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
        assert release.wait(timeout=2)

    service = _service(workspace_root, stage_runner=fake_stage_runner)
    job_id = str(
        _payload(
            service.handle_post(
                "/api/stage/run",
                {"stage": "plan", "runtime": "codex", "run_id": "run-ui-approval-race"},
            )
        )["job_id"]
    )
    assert request_ready.wait(timeout=2)
    _wait_job_status(service, job_id, "waiting-for-operator")
    request = captured["request"]
    assert isinstance(request, RuntimeOperatorRequest)
    barrier = threading.Barrier(2)
    responses: list[Any] = []

    def decide() -> None:
        barrier.wait()
        responses.append(
            service.handle_post(
                f"/api/jobs/{job_id}/operator-requests/{request.id}/decision",
                {"action": action.value},
            )
        )

    def cancel() -> None:
        barrier.wait()
        responses.append(service.handle_post(f"/api/jobs/{job_id}/cancel", {}))

    threads = [threading.Thread(target=decide), threading.Thread(target=cancel)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)
    release.set()

    assert all(not thread.is_alive() for thread in threads)
    assert {response.status for response in responses}.issubset({200, HTTPStatus.CONFLICT})
    attempt_path = captured["attempt_path"]
    assert isinstance(attempt_path, Path)
    winners = load_operator_decisions(attempt_path / OPERATOR_DECISIONS_FILENAME)
    assert len(winners) == 1
    for _ in range(100):
        if "decision" in captured and not service._operator_decisions.has_waiter(job_id):
            break
        time.sleep(0.01)
    decision = captured["decision"]
    assert isinstance(decision, RuntimeOperatorDecision)
    assert decision == winners[0]


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

    workspace_payload = _payload(service.handle_post("/api/open-folder", {"target": "workspace"}))
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
        (workspace_root / "workitems" / "WI-UI" / "stages" / "plan").resolve(strict=False),
        (workspace_root / "workitems" / "WI-UI" / "stages" / "plan").resolve(strict=False),
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


def test_ui_workflow_run_endpoint_requires_setup_context(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    def forbidden_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        raise AssertionError("setup-incomplete workflow run must not create a job")

    service = _onboarding_service_with_runner(
        tmp_path,
        monkeypatch,
        workflow_runner=forbidden_workflow_runner,
    )

    response = service.handle_post(
        "/api/workflow/run",
        {
            "runtime": "generic-cli",
            "from_stage": "idea",
            "to_stage": "plan",
        },
    )

    payload = _error_payload(response)
    assert response.status == HTTPStatus.BAD_REQUEST
    assert payload["error"] == "Complete project setup before using this UI action."
    assert "job_id" not in payload


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
    assert generic_cli["binary"] == {
        "command": "/usr/bin/python",
        "status": "detected",
        "version": "Python <3>",
    }
    assert generic_cli["execution_command"]["status"] == "unavailable"
    assert generic_cli["authentication"] == {"detail": None, "status": "unverified"}
    assert generic_cli["capabilities"]["status"] == "unknown"
    assert generic_cli["latest_launch"] is None
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
        'id="tab-work" data-tab="work" role="tab" aria-selected="true" '
        'aria-controls="cockpitContent" tabindex="0"' in html
    )
    assert 'id="tab-recovery" data-tab="recovery" role="tab"' in html
    assert 'id="tab-evidence" data-tab="evidence" role="tab"' in html
    assert (
        'id="tab-history" data-tab="history" role="tab" aria-selected="false" '
        'aria-controls="cockpitContent" tabindex="-1"' in html
    )
    assert (
        'id="cockpitContent" class="cockpit-content" role="tabpanel" '
        'aria-labelledby="tab-work" tabindex="0"' in html
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
    assert artifacts_payload["documents"]["plan"] == ("workitems/WI-UI/stages/plan/plan.md")
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


def test_operator_ui_local_project_terminal_fixture_creates_follow_up_without_runtime(
    tmp_path: Path,
) -> None:
    fixture_project = tmp_path / "local-fixture"
    workspace_root = fixture_project / ".aidd"
    fixture_project.mkdir()
    _prepare_completed_qa_run(workspace_root)

    def forbidden_workflow_runner(**kwargs: object) -> WorkflowRunResult:
        raise AssertionError("terminal fixture follow-up must not invoke a runtime")

    service = _service(workspace_root, workflow_runner=forbidden_workflow_runner)

    dashboard_payload = _payload(
        service.handle_get("/api/dashboard", {"stage": ["qa"], "run_id": ["run-ui"]})
    )
    findings_payload = _payload(
        service.handle_get("/api/next-flow/source-findings", {"run_id": ["run-ui"]})
    )
    response = service.handle_post(
        "/api/next-flow/follow-up-draft/create",
        {
            "source_run_id": "run-ui",
            "new_work_item": "WI-LOCAL-FOLLOW-UP",
            "title": "Local fixture completed-run follow-up",
            "selected_source_ids": ["qa-finding:qa:qa_report"],
        },
    )

    assert response.status == HTTPStatus.CREATED
    payload = json.loads(response.body.decode("utf-8"))
    request_path = workspace_root / payload["created"]["request_path"]
    metadata_path = workspace_root / "workitems" / "WI-LOCAL-FOLLOW-UP" / "work-item.json"
    request_text = request_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    qa_group = next(
        group
        for group in findings_payload["groups"]  # type: ignore[index]
        if group["id"] == "qa-findings"
    )

    assert dashboard_payload["dashboard"]["terminal_handoff"]["status"] == "completed"  # type: ignore[index]
    assert payload["created"]["work_item"] == "WI-LOCAL-FOLLOW-UP"
    assert payload["created"]["source_artifact_paths"] == ["workitems/WI-UI/stages/qa/qa-report.md"]
    assert any(
        item["id"] == "qa-finding:qa:qa_report"
        and item["source_path"] == "workitems/WI-UI/stages/qa/qa-report.md"
        for item in qa_group["items"]
    )
    assert "- Source work item: `WI-UI`" in request_text
    assert "- Source run: `run-ui`" in request_text
    assert "`workitems/WI-UI/stages/qa/qa-report.md`" in request_text
    assert metadata["lineage"] == {
        "source_run_id": "run-ui",
        "source_work_item_id": "WI-UI",
    }
    assert not (workspace_root / "reports" / "runs" / "WI-LOCAL-FOLLOW-UP").exists()


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
    work_item_parameter = inspect.signature(ui_command).parameters["work_item"]

    assert "ui" in command_names
    assert work_item_parameter.default is None


def test_ui_tasks_endpoint_returns_rich_task_state(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_rich_tasklist(workspace_root)
    service = _service(workspace_root)

    payload = _payload(service.handle_get("/api/tasks", {}))

    tasks = payload["tasks"]
    assert isinstance(tasks, list)
    task = tasks[0]
    assert isinstance(task, dict)
    assert task["id"] == "TL-1"
    assert task["status"] == "pending"
    assert task["ready"] is True
    acceptance = task["acceptance_criteria"]
    assert isinstance(acceptance, list)
    assert acceptance[0]["id"] == "TL-1-AC1"
    finalization = payload["finalization"]
    assert isinstance(finalization, dict)
    assert finalization["status"] == "pending"
    assert finalization["attempts"] == []


def test_ui_task_run_requires_explicit_run_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_rich_tasklist(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/tasks/run",
        {"task_id": "TL-1", "runtime": "generic-cli"},
    )

    payload = _payload_with_status(response, 400)
    assert payload["error"] == "run_id is required."


def test_ui_task_run_returns_conflict_before_background_job(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_rich_tasklist(workspace_root)
    service = _service(workspace_root)
    selected_run_root = run_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-1",
    )
    lease_path = selected_run_root / ".mutation-lease"
    lease_path.mkdir(parents=True)
    (lease_path / "owner.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "operation": "workflow",
                "token": "external",
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
            }
        ),
        encoding="utf-8",
    )

    response = service.handle_post(
        "/api/tasks/run",
        {"task_id": "TL-1", "runtime": "generic-cli", "run_id": "run-1"},
    )

    payload = _payload_with_status(response, HTTPStatus.CONFLICT)
    assert "workflow" in str(payload["error"])


def test_ui_task_finalize_requires_explicit_run_id(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _seed_rich_tasklist(workspace_root)
    service = _service(workspace_root)

    response = service.handle_post(
        "/api/tasks/finalize",
        {"runtime": "generic-cli"},
    )

    payload = _payload_with_status(response, HTTPStatus.BAD_REQUEST)
    assert payload["error"] == "run_id is required."
