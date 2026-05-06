from __future__ import annotations

# ruff: noqa: E501
import json
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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


@dataclass(frozen=True, slots=True)
class UiResponse:
    status: int
    content_type: str
    body: bytes


def _jsonable(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple | list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _json_response(payload: object, *, status: int = HTTPStatus.OK) -> UiResponse:
    return UiResponse(
        status=int(status),
        content_type="application/json; charset=utf-8",
        body=json.dumps(_jsonable(payload), indent=2, sort_keys=True).encode("utf-8"),
    )


def _error_response(message: str, *, status: int = HTTPStatus.BAD_REQUEST) -> UiResponse:
    return _json_response({"error": message}, status=status)


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
    runtime = str(payload.get("runtime", "generic-cli")).strip()
    return runtime or "generic-cli"


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


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError as exc:
        raise ValueError("Content-Length must be an integer.") from exc
    if length <= 0:
        return {}
    raw_body = handler.rfile.read(length)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    return payload


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


_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIDD Operator</title>
  <link rel="stylesheet" href="/operator.css">
</head>
<body>
  <header class="topbar">
    <div>
      <h1>AIDD Operator</h1>
      <p id="runLine">No run selected</p>
    </div>
    <button id="runButton" type="button">Run</button>
  </header>
  <main class="layout">
    <nav id="stages" class="stages"></nav>
    <section class="pane">
      <div class="tabs">
        <button data-tab="questions" class="active" type="button">Questions</button>
        <button data-tab="logs" type="button">Logs</button>
        <button data-tab="artifacts" type="button">Artifacts</button>
        <button data-tab="readiness" type="button">Readiness</button>
      </div>
      <div id="stageMeta" class="meta"></div>
      <div id="content" class="content"></div>
    </section>
  </main>
  <script src="/operator.js"></script>
</body>
</html>
"""


_OPERATOR_CSS = """
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f7f7f4;
  color: #1d211c;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; }
.topbar {
  align-items: center;
  background: #ffffff;
  border-bottom: 1px solid #d8ddd2;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 16px 24px;
}
h1 { font-size: 20px; line-height: 1.2; margin: 0; }
p { margin: 4px 0 0; }
button {
  background: #285e61;
  border: 1px solid #285e61;
  border-radius: 6px;
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  min-height: 36px;
  padding: 7px 12px;
}
button.secondary, .tabs button {
  background: #ffffff;
  border-color: #cdd5c6;
  color: #1d211c;
}
.tabs button.active { border-color: #285e61; color: #285e61; }
.layout {
  display: grid;
  gap: 0;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr);
  min-height: calc(100vh - 73px);
}
.stages {
  background: #eef1ea;
  border-right: 1px solid #d8ddd2;
  padding: 12px;
}
.stage-button {
  align-items: center;
  background: transparent;
  border-color: transparent;
  color: #1d211c;
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  width: 100%;
}
.stage-button.active { background: #dfe9e2; border-color: #9bb7a2; }
.stage-status {
  color: #647067;
  font-size: 12px;
  margin-left: 8px;
}
.pane { padding: 16px 20px; }
.tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.meta {
  border-bottom: 1px solid #d8ddd2;
  color: #4d584f;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 12px;
}
.content { padding-top: 12px; }
.question {
  border-bottom: 1px solid #e0e5dc;
  display: grid;
  gap: 8px;
  padding: 12px 0;
}
.question textarea {
  border: 1px solid #cdd5c6;
  border-radius: 6px;
  font: inherit;
  min-height: 70px;
  padding: 8px;
  resize: vertical;
  width: 100%;
}
pre {
  background: #111614;
  border-radius: 6px;
  color: #e8efe9;
  margin: 0;
  max-height: 66vh;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
}
.list { margin: 0; padding-left: 18px; }
.readiness-table {
  border-collapse: collapse;
  min-width: 960px;
  width: 100%;
}
.readiness-table th,
.readiness-table td {
  border-bottom: 1px solid #d8ddd2;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}
.readiness-table th {
  color: #4d584f;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.readiness-scroll { overflow-x: auto; }
.runtime-command {
  background: #eef1ea;
  border-radius: 4px;
  display: inline-block;
  max-width: 360px;
  overflow-wrap: anywhere;
  padding: 2px 4px;
}
@media (max-width: 780px) {
  .layout { grid-template-columns: 1fr; }
  .stages { border-right: 0; border-bottom: 1px solid #d8ddd2; }
  .topbar { align-items: flex-start; flex-direction: column; }
}
"""


_OPERATOR_JS = """
const stages = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
let activeStage = "idea";
let activeTab = "questions";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok || payload.error) throw new Error(payload.error || response.statusText);
  return payload;
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

async function loadRun() {
  try {
    const run = await api("/api/run");
    const metadata = run.metadata;
    setText("runLine", `${metadata.work_item} / ${metadata.run_id} / ${metadata.runtime_id}`);
    const statusByStage = Object.fromEntries(metadata.stages.map((stage) => [stage.stage, stage]));
    document.getElementById("stages").innerHTML = stages.map((stage) => {
      const status = statusByStage[stage]?.status || "pending";
      return `<button class="stage-button ${stage === activeStage ? "active" : ""}" data-stage="${escapeHtml(stage)}" type="button"><span>${escapeHtml(stage)}</span><span class="stage-status">${escapeHtml(status)}</span></button>`;
    }).join("");
  } catch (error) {
    setText("runLine", error.message);
    document.getElementById("stages").innerHTML = stages.map((stage) => `<button class="stage-button ${stage === activeStage ? "active" : ""}" data-stage="${escapeHtml(stage)}" type="button">${escapeHtml(stage)}</button>`).join("");
  }
}

async function loadStage() {
  try {
    const stage = await api(`/api/stage?stage=${encodeURIComponent(activeStage)}`);
    const result = stage.result;
    document.getElementById("stageMeta").innerHTML = [
      `stage: ${result.stage}`,
      `state: ${result.final_state}`,
      `attempts: ${result.attempt_count}`,
      `validator pass/fail: ${result.validator_pass_count}/${result.validator_fail_count}`
    ].map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  } catch (error) {
    document.getElementById("stageMeta").textContent = error.message;
  }
}

async function loadQuestions() {
  const view = await api(`/api/questions?stage=${encodeURIComponent(activeStage)}`);
  if (!view.questions.length) {
    document.getElementById("content").textContent = "No questions";
    return;
  }
  document.getElementById("content").innerHTML = view.questions.map((question) => `
    <div class="question">
      <strong>${escapeHtml(question.question_id)} / ${escapeHtml(question.status)}</strong>
      <div>${escapeHtml(question.text)}</div>
      <textarea data-question="${escapeHtml(question.question_id)}" ${question.status === "resolved" ? "disabled" : ""}></textarea>
      <button class="answer" data-question="${escapeHtml(question.question_id)}" type="button">Answer</button>
    </div>
  `).join("");
}

async function loadLogs() {
  const view = await api(`/api/logs?stage=${encodeURIComponent(activeStage)}`);
  document.getElementById("content").innerHTML = `<pre>${escapeHtml(view.text)}</pre>`;
}

async function loadArtifacts() {
  const view = await api(`/api/artifacts?stage=${encodeURIComponent(activeStage)}`);
  const docs = Object.entries(view.documents).map(([key, value]) => `<li>${escapeHtml(key)}: ${escapeHtml(value)}</li>`).join("");
  const logs = Object.entries(view.logs).map(([key, value]) => `<li>${escapeHtml(key)}: ${escapeHtml(value)}</li>`).join("");
  document.getElementById("content").innerHTML = `<h2>Documents</h2><ul class="list">${docs}</ul><h2>Logs</h2><ul class="list">${logs}</ul>`;
}

function timeoutSummary(value) {
  return value === null || value === undefined ? "none" : `${value}s`;
}

function stageTimeoutSummary(stageTimeouts) {
  const entries = Object.entries(stageTimeouts || {});
  if (!entries.length) return "none";
  return entries.map(([stage, seconds]) => `${stage}: ${timeoutSummary(seconds)}`).join(", ");
}

async function loadReadiness() {
  const view = await api("/api/runtime-readiness");
  const rows = view.runtimes.map((runtime) => `
    <tr>
      <td>${escapeHtml(runtime.runtime_id)}</td>
      <td>${escapeHtml(runtime.support_tier)}</td>
      <td>${escapeHtml(runtime.command_source)}</td>
      <td><code class="runtime-command">${escapeHtml(runtime.command)}</code></td>
      <td>${escapeHtml(runtime.execution_mode)}</td>
      <td>${escapeHtml(runtime.provider_available ? "available" : "unavailable")}</td>
      <td>${escapeHtml(runtime.provider_version || "unknown")}</td>
      <td>${escapeHtml(runtime.provider_command || "unknown")}</td>
      <td>${escapeHtml(runtime.execution_command_available ? "available" : "unavailable")}</td>
      <td>${escapeHtml(timeoutSummary(runtime.default_timeout_seconds))}</td>
      <td>${escapeHtml(stageTimeoutSummary(runtime.stage_timeout_seconds))}</td>
    </tr>
  `).join("");
  document.getElementById("content").innerHTML = `
    <div class="readiness-scroll">
      <table class="readiness-table">
        <thead>
          <tr>
            <th>Runtime</th>
            <th>Tier</th>
            <th>Source</th>
            <th>Command</th>
            <th>Mode</th>
            <th>Provider</th>
            <th>Version</th>
            <th>Probe</th>
            <th>Exec</th>
            <th>Timeout</th>
            <th>Stage timeouts</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

async function refresh() {
  await loadRun();
  try {
    if (activeTab === "readiness") {
      document.getElementById("stageMeta").innerHTML = `<span>${escapeHtml("runtime readiness")}</span>`;
      await loadReadiness();
      return;
    }
    await loadStage();
    if (activeTab === "questions") await loadQuestions();
    if (activeTab === "logs") await loadLogs();
    if (activeTab === "artifacts") await loadArtifacts();
  } catch (error) {
    document.getElementById("content").textContent = error.message;
  }
}

document.addEventListener("click", async (event) => {
  const stage = event.target.closest("[data-stage]")?.dataset.stage;
  if (stage) {
    activeStage = stage;
    await refresh();
    return;
  }
  const tab = event.target.closest("[data-tab]")?.dataset.tab;
  if (tab) {
    activeTab = tab;
    document.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
    await refresh();
    return;
  }
  const answerButton = event.target.closest(".answer");
  if (answerButton) {
    const questionId = answerButton.dataset.question;
    const textarea = answerButton.closest(".question")?.querySelector("textarea");
    if (!questionId || !textarea) return;
    await api("/api/answers", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({stage: activeStage, question_id: questionId, text: textarea.value})
    });
    await refresh();
    return;
  }
  if (event.target.id === "runButton") {
    await api("/api/workflow/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({runtime: "generic-cli"})
    });
    await refresh();
  }
});

refresh();
"""


__all__ = [
    "OperatorUiService",
    "UiServerOptions",
    "run_ui_server",
    "ui_command",
]
