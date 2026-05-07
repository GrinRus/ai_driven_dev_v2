from __future__ import annotations

import json
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any

from aidd.cli import main as cli_main
from aidd.cli.ui import (
    OperatorUiService,
    UiRequestBodyTooLarge,
    UiServerOptions,
    _is_loopback_host,
    _read_json_body,
)
from aidd.core.run_store import (
    create_next_attempt_directory,
    create_run_manifest,
    persist_stage_status,
    run_attempt_runtime_log_path,
)
from aidd.core.runtime_readiness import RuntimeReadinessProbeReport
from aidd.core.workflow_service import WorkflowRunRequest, WorkflowRunResult


def _service(
    workspace_root: Path,
    *,
    config: Path | None = None,
    workflow_runner: Any | None = None,
    readiness_probe_provider: Any | None = None,
) -> OperatorUiService:
    options = UiServerOptions(
        work_item="WI-UI",
        root=workspace_root,
        config=config or Path("aidd.test.toml"),
        host="127.0.0.1",
        port=0,
    )
    kwargs: dict[str, Any] = {}
    if workflow_runner is not None:
        kwargs["workflow_runner"] = workflow_runner
    if readiness_probe_provider is not None:
        kwargs["readiness_probe_provider"] = readiness_probe_provider
    return OperatorUiService(options, **kwargs)


def _payload(response) -> dict[str, object]:
    assert response.status == 200
    return json.loads(response.body.decode("utf-8"))


def _error_payload(response) -> dict[str, object]:
    assert response.status >= 400
    return json.loads(response.body.decode("utf-8"))


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
            "runtime": "codex",
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
    assert request.runtime_id == "codex"
    assert request.stage_start == "research"
    assert request.stage_end == "plan"
    assert request.log_follow is True
    assert "stage_executor" in captured


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
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert payload["run_id"] == "run-ui-source"
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
    assert page.status == 200
    html = page.body.decode("utf-8")
    assert "AIDD Operator" in html
    assert 'id="runtimeSelect"' in html
    assert '<button id="runButton" type="button" disabled>Run</button>' in html

    run_response = service.handle_post(
        "/api/workflow/run",
        {
            "runtime": "generic-cli",
            "from_stage": "idea",
            "to_stage": "qa",
        },
    )
    run_payload = _payload(run_response)
    request = captured["request"]
    assert isinstance(request, WorkflowRunRequest)
    assert run_payload["run_id"] == "run-ui-e2e"
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


def test_operator_script_escapes_dynamic_markup(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")

    response = service.handle_get("/operator.js", {})
    script = response.body.decode("utf-8")

    assert "function escapeHtml(value)" in script
    assert "${escapeHtml(question.text)}" in script
    assert "`<span>${escapeHtml(item)}</span>`" in script
    assert "`<pre>${escapeHtml(view.text)}</pre>`" in script
    assert "${escapeHtml(key)}: ${escapeHtml(value)}" in script
    assert "${escapeHtml(runtime.command)}" in script
    assert "${escapeHtml(runtime.provider_version || \"unknown\")}" in script
    assert "${escapeHtml(stageTimeoutSummary(runtime.stage_timeout_seconds))}" in script
    assert "function renderRuntimeSelector(runtimes)" in script
    assert "body: JSON.stringify({runtime: selectedRuntime})" in script
    assert 'body: JSON.stringify({runtime: "generic-cli"})' not in script


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
