from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aidd.cli import main as cli_main
from aidd.cli.ui import OperatorUiService, UiServerOptions
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_runtime_log_path,
)
from aidd.core.workflow_service import WorkflowRunRequest, WorkflowRunResult


def _service(
    workspace_root: Path,
    *,
    workflow_runner: Any | None = None,
) -> OperatorUiService:
    options = UiServerOptions(
        work_item="WI-UI",
        root=workspace_root,
        config=Path("aidd.test.toml"),
        host="127.0.0.1",
        port=0,
    )
    if workflow_runner is not None:
        return OperatorUiService(options, workflow_runner=workflow_runner)
    return OperatorUiService(
        options
    )


def _payload(response) -> dict[str, object]:
    assert response.status == 200
    return json.loads(response.body.decode("utf-8"))


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
    assert logs_payload["text"] == "runtime-line\n"
    assert artifacts_payload["documents"]["input_bundle"].endswith("input-bundle.md")


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
    answers_path = workspace_root / "workitems" / "WI-UI" / "stages" / "plan" / "answers.md"
    assert "Release target is 0.2.0." in answers_path.read_text(encoding="utf-8")


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
            "runtime": "generic-cli",
            "from_stage": "research",
            "to_stage": "plan",
            "log_follow": True,
        },
    )

    payload = _payload(response)
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert payload["run_id"] == "run-ui-seam"
    assert payload["completed"] is True
    assert request.work_item == "WI-UI"
    assert request.runtime_id == "generic-cli"
    assert request.stage_start == "research"
    assert request.stage_end == "plan"
    assert request.log_follow is True
    assert "stage_executor" in captured


def test_operator_script_escapes_dynamic_markup(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    response = service.handle_get("/operator.js", {})
    script = response.body.decode("utf-8")

    assert "function escapeHtml(value)" in script
    assert "${escapeHtml(question.text)}" in script
    assert "`<span>${escapeHtml(item)}</span>`" in script
    assert "`<pre>${escapeHtml(view.text)}</pre>`" in script
    assert "${escapeHtml(key)}: ${escapeHtml(value)}" in script


def test_ui_command_is_registered() -> None:
    command_names = {command.name for command in cli_main.app.registered_commands}

    assert "ui" in command_names
