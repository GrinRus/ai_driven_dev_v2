from __future__ import annotations

import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ruff: noqa: E501
from ipaddress import ip_address
from pathlib import Path
from typing import Annotated, Any, cast
from urllib.parse import parse_qs, urlparse

import typer

from aidd.adapters.runtime_registry import runtime_definitions
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli.stage_run import StageRunOptions, run_stage_command
from aidd.cli.support import (
    _execution_command_available,
    _runtime_command_for_runtime,
    _runtime_execution_mode_for_runtime,
    console,
)
from aidd.cli.ui_assets import _INDEX_HTML, _OPERATOR_CSS, _OPERATOR_JS
from aidd.cli.ui_http import (
    UiRequestBodyTooLarge,
    UiResponse,
    _error_response,
    _json_response,
    _read_json_body,
)
from aidd.config import AiddConfig, load_config
from aidd.core.interview import AnswerResolution
from aidd.core.operator_frontend import (
    persist_operator_answer,
    resolve_operator_artifacts_view,
    resolve_operator_questions_view,
    resolve_operator_run_log_view,
    resolve_operator_run_view,
    resolve_operator_stage_view,
)
from aidd.core.runtime_readiness import (
    RuntimeCommandSource,
    RuntimeReadinessProbeReport,
    resolve_runtime_readiness,
)
from aidd.core.stages import STAGES
from aidd.core.workflow_service import (
    WorkflowRunRequest,
    WorkflowRunResult,
    WorkflowStageExecutionError,
    WorkflowStageExecutionRequest,
    run_workflow,
)

WorkflowRunner = Callable[..., WorkflowRunResult]
ReadinessProbeProvider = Callable[[AiddConfig], Mapping[str, RuntimeReadinessProbeReport]]


@dataclass(frozen=True, slots=True)
class UiServerOptions:
    work_item: str
    root: Path
    config: Path
    host: str
    port: int


def _first_param(params: dict[str, list[str]], name: str, default: str | None = None) -> str | None:
    values = params.get(name)
    if not values:
        return default
    value = values[0].strip()
    return value or default


def _optional_attempt(params: dict[str, list[str]]) -> int | None:
    raw_attempt = _first_param(params, "attempt")
    if raw_attempt is None:
        return None
    try:
        attempt = int(raw_attempt)
    except ValueError as exc:
        raise ValueError("attempt must be an integer.") from exc
    if attempt <= 0:
        raise ValueError("attempt must be greater than zero.")
    return attempt


def _runtime_from_payload(payload: dict[str, Any]) -> str:
    raw_runtime = payload.get("runtime")
    if not isinstance(raw_runtime, str):
        raise ValueError("runtime is required.")
    runtime = raw_runtime.strip()
    if not runtime:
        raise ValueError("runtime is required.")
    return runtime


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized in {"localhost", "localhost.", "::1"}:
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _warn_if_non_loopback_host(host: str) -> None:
    if _is_loopback_host(host):
        return
    console.print(
        "[yellow]Warning:[/yellow] AIDD UI has no authentication in this release; "
        f"binding to {host!r} exposes the local operator surface to that network interface."
    )


def _runtime_command_sources_from_config(path: Path) -> dict[str, RuntimeCommandSource]:
    data: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as file_obj:
            data = tomllib.load(file_obj)

    raw_runtime = data.get("runtime", {})
    runtime_table = raw_runtime if isinstance(raw_runtime, dict) else {}
    sources: dict[str, RuntimeCommandSource] = {}
    for definition in runtime_definitions():
        raw_section = runtime_table.get(definition.config_section, {})
        section = raw_section if isinstance(raw_section, dict) else {}
        sources[definition.runtime_id] = "config" if "command" in section else "default"
    return sources


def _collect_runtime_readiness_probe_reports(
    cfg: AiddConfig,
) -> dict[str, RuntimeReadinessProbeReport]:
    reports: dict[str, RuntimeReadinessProbeReport] = {}
    for definition in runtime_definitions():
        provider_report = get_runtime_adapter_surface(definition.runtime_id).probe(
            definition.probe_command
        )
        runtime_config = cfg.runtime_config(definition.runtime_id)
        reports[definition.runtime_id] = RuntimeReadinessProbeReport(
            provider_available=provider_report.available,
            execution_command_available=_execution_command_available(runtime_config.command),
            provider_version=provider_report.version_text,
            provider_command=provider_report.command,
        )
    return reports


class OperatorUiService:
    def __init__(
        self,
        options: UiServerOptions,
        *,
        workflow_runner: WorkflowRunner = run_workflow,
        readiness_probe_provider: ReadinessProbeProvider = _collect_runtime_readiness_probe_reports,
    ) -> None:
        self.options = options
        self._workflow_runner = workflow_runner
        self._readiness_probe_provider = readiness_probe_provider

    @property
    def workspace_root(self) -> Path:
        return self.options.root

    def handle_get(self, path: str, params: dict[str, list[str]]) -> UiResponse:
        try:
            if path == "/":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/html; charset=utf-8",
                    body=_INDEX_HTML.encode("utf-8"),
                )
            if path == "/operator.js":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/javascript; charset=utf-8",
                    body=_OPERATOR_JS.encode("utf-8"),
                )
            if path == "/operator.css":
                return UiResponse(
                    status=int(HTTPStatus.OK),
                    content_type="text/css; charset=utf-8",
                    body=_OPERATOR_CSS.encode("utf-8"),
                )
            if path == "/api/run":
                return _json_response(
                    resolve_operator_run_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        run_id=_first_param(params, "run_id"),
                    )
                )
            if path == "/api/runtime-readiness":
                return _json_response(self._runtime_readiness())
            if path == "/api/stage":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_stage_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        run_id=_first_param(params, "run_id"),
                    )
                )
            if path == "/api/questions":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_questions_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                    )
                )
            if path == "/api/logs":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                summary = resolve_operator_run_log_view(
                    workspace_root=self.workspace_root,
                    work_item=self.options.work_item,
                    stage=stage,
                    run_id=_first_param(params, "run_id"),
                    attempt_number=_optional_attempt(params),
                )
                return _json_response(
                    {
                        "summary": summary,
                        "text": summary.runtime_log_path.read_text(encoding="utf-8"),
                    }
                )
            if path == "/api/artifacts":
                stage = _first_param(params, "stage", STAGES[0])
                assert stage is not None
                return _json_response(
                    resolve_operator_artifacts_view(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        run_id=_first_param(params, "run_id"),
                        attempt_number=_optional_attempt(params),
                    )
                )
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def handle_post(self, path: str, payload: dict[str, Any]) -> UiResponse:
        try:
            if path == "/api/answers":
                stage = str(payload.get("stage", STAGES[0])).strip() or STAGES[0]
                question_id = str(payload.get("question_id", "")).strip()
                text = str(payload.get("text", "")).strip()
                raw_resolution = str(payload.get("resolution", AnswerResolution.RESOLVED)).strip()
                if not question_id:
                    return _error_response("question_id is required.")
                if not text:
                    return _error_response("text is required.")
                return _json_response(
                    persist_operator_answer(
                        workspace_root=self.workspace_root,
                        work_item=self.options.work_item,
                        stage=stage,
                        question_id=question_id,
                        text=text,
                        resolution=AnswerResolution(raw_resolution),
                    )
                )
            if path == "/api/workflow/run":
                return _json_response(self._run_workflow(payload))
        except ValueError as exc:
            return _error_response(str(exc))
        return _error_response("not found", status=HTTPStatus.NOT_FOUND)

    def _run_workflow(self, payload: dict[str, Any]) -> object:
        runtime = _runtime_from_payload(payload)
        stage_start = str(payload.get("from_stage", STAGES[0])).strip() or STAGES[0]
        stage_end = str(payload.get("to_stage", STAGES[-1])).strip() or STAGES[-1]
        log_follow = bool(payload.get("log_follow", False))
        cfg = load_config(self.options.config)
        runtime_command = _runtime_command_for_runtime(runtime=runtime, cfg=cfg)
        runtime_execution_mode = _runtime_execution_mode_for_runtime(runtime=runtime, cfg=cfg)

        def _stage_executor(request: WorkflowStageExecutionRequest) -> None:
            try:
                run_stage_command(
                    StageRunOptions(
                        stage=request.stage,
                        work_item=request.work_item,
                        runtime=request.runtime_id,
                        run_id=request.run_id,
                        root=request.workspace_root,
                        config=request.config_path,
                        log_follow=request.log_follow,
                    )
                )
            except typer.Exit as exc:
                if exc.exit_code in (None, 0):
                    return
                raise WorkflowStageExecutionError(
                    stage=request.stage,
                    exit_code=int(exc.exit_code),
                ) from exc

        return self._workflow_runner(
            request=WorkflowRunRequest(
                work_item=self.options.work_item,
                runtime_id=runtime,
                workspace_root=self.workspace_root,
                config_path=self.options.config,
                config_snapshot={
                    "config_path": self.options.config.as_posix(),
                    "workspace_root": self.workspace_root.as_posix(),
                    "runtime_command": runtime_command,
                    "runtime_execution_mode": runtime_execution_mode.value,
                    "log_follow": log_follow,
                    "mode": "ui-workflow",
                },
                stage_start=stage_start,
                stage_end=stage_end,
                log_follow=log_follow,
            ),
            stage_executor=_stage_executor,
        )

    def _runtime_readiness(self) -> object:
        cfg = load_config(self.options.config)
        return resolve_runtime_readiness(
            config=cfg,
            probe_reports=self._readiness_probe_provider(cfg),
            command_sources=_runtime_command_sources_from_config(self.options.config),
        )


def _handler_for(service: OperatorUiService) -> type[BaseHTTPRequestHandler]:
    class OperatorUiHandler(BaseHTTPRequestHandler):
        def _send(self, response: UiResponse) -> None:
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            self._send(service.handle_get(parsed.path, parse_qs(parsed.query)))

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = _read_json_body(self)
            except UiRequestBodyTooLarge as exc:
                self._send(_error_response(str(exc), status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE))
                return
            except ValueError as exc:
                self._send(_error_response(str(exc)))
                return
            self._send(service.handle_post(parsed.path, payload))

        def log_message(self, format: str, *args: object) -> None:
            return

    return OperatorUiHandler


def run_ui_server(options: UiServerOptions) -> None:
    service = OperatorUiService(options)
    server = ThreadingHTTPServer((options.host, options.port), _handler_for(service))
    host, port = cast(tuple[str, int], server.server_address[:2])
    _warn_if_non_loopback_host(options.host)
    console.print(f"AIDD UI: http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("AIDD UI stopped.")
    finally:
        server.server_close()


def ui_command(
    work_item: Annotated[str, typer.Option("--work-item", help="Work item id")],
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
    config: Annotated[
        Path,
        typer.Option("--config", help="Path to an AIDD TOML config file."),
    ] = Path("aidd.example.toml"),
    host: Annotated[
        str,
        typer.Option("--host", help="Local bind host for the operator UI."),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", help="Local bind port; use 0 to allocate one."),
    ] = 0,
) -> None:
    """Start the local operator UI."""
    run_ui_server(
        UiServerOptions(
            work_item=work_item,
            root=root.resolve(strict=False),
            config=config,
            host=host,
            port=port,
        )
    )


__all__ = [
    "OperatorUiService",
    "UiServerOptions",
    "run_ui_server",
    "ui_command",
]
