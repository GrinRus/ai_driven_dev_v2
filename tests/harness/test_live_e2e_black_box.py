from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import yaml

from aidd.core.stages import STAGES
from aidd.harness import live_e2e_black_box_orchestration as live_orchestration
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.live_e2e_black_box import (
    _harness_environment,
    _implementation_verification_evidence_shape,
    run_black_box_live_e2e,
)
from aidd.harness.live_e2e_black_box_orchestration import (
    BlackBoxCommandResult,
    BlackBoxLiveE2EResult,
    LiveE2EInterrupted,
    _find_resume_state,
    _live_interruption_handlers,
    _next_flow_complete_visible,
    _run_black_box_command,
)
from aidd.harness.runner import HarnessCommandTranscript
from aidd.harness.scenarios import load_scenario

_PRIMARY_OUTPUTS: dict[str, str] = {
    "idea": "idea-brief.md",
    "research": "research-notes.md",
    "plan": "plan.md",
    "review-spec": "review-spec-report.md",
    "tasklist": "tasklist.md",
    "implement": "implementation-report.md",
    "review": "review-report.md",
    "qa": "qa-report.md",
}


@pytest.mark.parametrize("qa_stage_state", ("passed", "succeeded", " SUCCEEDED "))
def test_next_flow_complete_visible_accepts_stage_audit_and_dashboard_states(
    qa_stage_state: str,
) -> None:
    assert _next_flow_complete_visible(
        status="pass",
        qa_stage_state=qa_stage_state,
    )


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_source_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", path.as_posix()])
    _run(["git", "config", "user.email", "tests@example.com"], cwd=path)
    _run(["git", "config", "user.name", "AIDD Tests"], cwd=path)
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    (path / "feature.txt").write_text("before\n", encoding="utf-8")
    _run(["git", "add", "README.md", "feature.txt"], cwd=path)
    _run(["git", "commit", "-m", "init"], cwd=path)


def _put_fake_provider_on_path(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    executable_name: str = "opencode",
) -> None:
    bin_dir = tmp_path / "provider-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    executable_path = bin_dir / executable_name
    executable_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir.as_posix()}:{os.environ.get('PATH', '')}")


def _clear_live_runtime_command_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIDD_EVAL_CLAUDE_CODE_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_CODEX_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_OPENCODE_COMMAND", raising=False)


def _write_fake_aidd(
    path: Path,
    *,
    fail_stage: str | None = None,
    timeout_stage: str | None = None,
    no_progress_stage: str | None = None,
    adapter_timeout_stage: str | None = None,
    block_stage: str | None = None,
    ui_operator_request_stage: str | None = None,
    ui_operator_request_command: str = "pwd",
    internal_operator_decision_stage: str | None = None,
    inspect_block_stage: str | None = None,
    inspect_fail_command: str | None = None,
    log_blocking_text: bool = False,
    stage_result_validator_verdict: str | None = None,
    stage_result_direct_qa_next_action_stage: str | None = None,
    stage_result_generic_next_action_stage: str | None = None,
    stray_top_level_workitems_stage: str | None = None,
    ignored_pollution_stage: str | None = None,
    implement_untracked_product_file: str | None = None,
) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PRIMARY_OUTPUTS = {json.dumps(_PRIMARY_OUTPUTS)}
FAIL_STAGE = {fail_stage!r}
TIMEOUT_STAGE = {timeout_stage!r}
NO_PROGRESS_STAGE = {no_progress_stage!r}
ADAPTER_TIMEOUT_STAGE = {adapter_timeout_stage!r}
BLOCK_STAGE = {block_stage!r}
UI_OPERATOR_REQUEST_STAGE = {ui_operator_request_stage!r}
UI_OPERATOR_REQUEST_COMMAND = {ui_operator_request_command!r}
INTERNAL_OPERATOR_DECISION_STAGE = {internal_operator_decision_stage!r}
INSPECT_BLOCK_STAGE = {inspect_block_stage!r}
INSPECT_FAIL_COMMAND = {inspect_fail_command!r}
LOG_BLOCKING_TEXT = {log_blocking_text!r}
STAGE_RESULT_VALIDATOR_VERDICT = {stage_result_validator_verdict!r}
STAGE_RESULT_DIRECT_QA_NEXT_ACTION_STAGE = {stage_result_direct_qa_next_action_stage!r}
STAGE_RESULT_GENERIC_NEXT_ACTION_STAGE = {stage_result_generic_next_action_stage!r}
STRAY_TOP_LEVEL_WORKITEMS_STAGE = {stray_top_level_workitems_stage!r}
IGNORED_POLLUTION_STAGE = {ignored_pollution_stage!r}
IMPLEMENT_UNTRACKED_PRODUCT_FILE = {implement_untracked_product_file!r}
TRANSITION_BARRIER_STAGE = os.environ.get("AIDD_FAKE_RUNTIME_BARRIER_STAGE")
TRANSITION_BARRIER_READY_PATH = os.environ.get("AIDD_FAKE_RUNTIME_BARRIER_READY_PATH")
TRANSITION_BARRIER_RELEASE_PATH = os.environ.get("AIDD_FAKE_RUNTIME_BARRIER_RELEASE_PATH")
TRANSITION_BARRIER_TIMEOUT_SECONDS = float(
    os.environ.get("AIDD_FAKE_RUNTIME_BARRIER_TIMEOUT_SECONDS", "30")
)


def option(args: list[str], name: str, default: str = "") -> str:
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        return default
    return args[index + 1]


def write_stage_outputs(stage: str, work_item: str, run_id: str) -> None:
    write_executing_stage_metadata(stage, work_item, run_id)
    if stage == TRANSITION_BARRIER_STAGE:
        if not TRANSITION_BARRIER_READY_PATH or not TRANSITION_BARRIER_RELEASE_PATH:
            raise RuntimeError("transition barrier requires ready and release paths")
        ready_path = Path(TRANSITION_BARRIER_READY_PATH)
        release_path = Path(TRANSITION_BARRIER_RELEASE_PATH)
        ready_path.parent.mkdir(parents=True, exist_ok=True)
        ready_path.write_text("ready\\n")
        deadline = time.monotonic() + TRANSITION_BARRIER_TIMEOUT_SECONDS
        while not release_path.exists():
            if time.monotonic() >= deadline:
                raise TimeoutError("transition barrier release timed out")
            time.sleep(0.01)
    output_root = Path(".aidd") / "workitems" / work_item / "stages" / stage / "output"
    output_root.mkdir(parents=True, exist_ok=True)
    root = output_root.parent
    if not (root / "questions.md").exists():
        (root / "questions.md").write_text(
            "# Questions\\n\\nNo blocking or non-blocking questions remain.\\n"
        )
    if not (root / "answers.md").exists():
        (root / "answers.md").write_text("# Answers\\n\\nNo questions were raised.\\n")
    validation_summary = ""
    if STAGE_RESULT_VALIDATOR_VERDICT is not None:
        validation_summary = (
            "## Validation summary\\n\\n"
            f"- Validator verdict: `{{STAGE_RESULT_VALIDATOR_VERDICT}}`\\n\\n"
        )
    next_actions = ""
    if stage == STAGE_RESULT_DIRECT_QA_NEXT_ACTION_STAGE:
        next_actions = "## Next actions\\n\\n- Proceed directly to `qa`.\\n\\n"
    elif stage == STAGE_RESULT_GENERIC_NEXT_ACTION_STAGE:
        next_actions = "## Next actions\\n\\n- Proceed to the downstream planning stage.\\n\\n"
    (output_root / "stage-result.md").write_text(
        "# Stage\\n\\n"
        f"{{stage}}\\n\\n"
        "## Attempt history\\n\\n"
        "- Attempt `1` (`initial`) -> succeeded.\\n\\n"
        + validation_summary +
        "## Status\\n\\n"
        "- `succeeded`\\n\\n"
        + next_actions
    )
    (output_root / "validator-report.md").write_text(
        "# Validator report\\n\\n## Result\\n\\n- Verdict: `pass`\\n"
    )
    primary = PRIMARY_OUTPUTS[stage]
    if stage == "review":
        text = "# Review Report\\n\\n- Review status: `approved`\\n- Findings: none\\n"
    elif stage == "qa":
        text = "# QA Report\\n\\n- QA verdict: `ready`\\n- EV-001: runtime.log\\n"
    elif stage == "implement":
        Path("feature.txt").write_text(f"after {{run_id}}\\n")
        if IMPLEMENT_UNTRACKED_PRODUCT_FILE:
            untracked_path = Path(IMPLEMENT_UNTRACKED_PRODUCT_FILE)
            untracked_path.parent.mkdir(parents=True, exist_ok=True)
            untracked_path.write_text("// untracked product helper\\n")
        text = (
            "# Implementation Report\\n\\n"
            "## Verification\\n\\n"
            "- Result: `pass`; command: `pytest -q`; evidence: `runtime.log`.\\n"
        )
    else:
        text = f"# {{stage}} output\\n\\n- generated by fake AIDD\\n"
    (output_root / primary).write_text(text)
    if stage == STRAY_TOP_LEVEL_WORKITEMS_STAGE:
        stray_root = Path("workitems") / work_item / "stages" / stage
        stray_root.mkdir(parents=True, exist_ok=True)
        (stray_root / "stage-result.md").write_text(
            "# Stray Stage Result\\n\\n- This duplicate is outside `.aidd`.\\n"
        )
    if stage == IGNORED_POLLUTION_STAGE:
        ignored_files = (
            (Path(".venv") / "pyvenv.cfg", "home = test\\n"),
            (Path("coverage") / "index.html", "coverage\\n"),
            (Path(".pdm-build") / "wheel", "wheel\\n"),
            (Path(".pytest_cache") / "CACHEDIR.TAG", "cache\\n"),
            (Path("package") / "__pycache__" / "module.pyc", "pyc\\n"),
        )
        for ignored_path, ignored_text in ignored_files:
            ignored_path.parent.mkdir(parents=True, exist_ok=True)
            ignored_path.write_text(ignored_text)

    stage_root = (
        Path(".aidd") / "reports" / "runs" / work_item / run_id / "stages" / stage
    )
    attempt_root = stage_root / "attempts" / "attempt-0001"
    attempt_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {{
                "schema_version": 1,
                "run_id": run_id,
                "work_item_id": work_item,
                "stage": stage,
                "status": "succeeded",
                "created_at_utc": "2026-05-25T00:00:00Z",
                "updated_at_utc": "2026-05-25T00:00:00Z",
                "status_history": [
                    {{
                        "status": "succeeded",
                        "changed_at_utc": "2026-05-25T00:00:00Z",
                    }}
                ],
                "repair_history": [],
                "attempt_count": 1,
            }}
        )
    )
    (attempt_root / "runtime.log").write_text(f"stage {{stage}} completed\\n")
    (attempt_root / "runtime.jsonl").write_text(
        json.dumps({{"event": "stage_completed", "stage": stage}}) + "\\n"
    )
    (attempt_root / "events.jsonl").write_text(
        json.dumps({{"event": "stage_completed", "stage": stage}}) + "\\n"
    )
    if stage == INTERNAL_OPERATOR_DECISION_STAGE:
        request_id = f"auto-{{stage}}"
        request = {{
            "id": request_id,
            "runtime_id": "codex",
            "stage": stage,
            "kind": "shell",
            "tool_name": "shell",
            "payload": {{"command": "pytest -q"}},
            "cwd": Path.cwd().as_posix(),
            "paths": [],
            "risk": "medium",
            "suggestions": ["allow_once", "allow_for_session", "deny", "cancel"],
            "created_at_utc": "2026-05-25T00:00:00Z",
        }}
        decision = {{
            "request_id": request_id,
            "action": "allow_once",
            "source": "policy",
            "reason": "auto-approved broad preset project-local shell request",
            "created_at_utc": "2026-05-25T00:00:01Z",
        }}
        (attempt_root / "operator-requests.jsonl").write_text(json.dumps(request) + "\\n")
        (attempt_root / "operator-decisions.jsonl").write_text(json.dumps(decision) + "\\n")


def write_failed_stage_artifacts(stage: str, work_item: str) -> None:
    stage_root = Path(".aidd") / "workitems" / work_item / "stages" / stage
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-result.md").write_text(
        "# Stage result\\n\\n## Status\\n\\n- Status: `failed`\\n"
    )
    (stage_root / "validator-report.md").write_text(
        "# Validator report\\n\\n## Result\\n\\n- Verdict: `fail`\\n"
    )
    primary = PRIMARY_OUTPUTS[stage]
    (stage_root / primary).write_text(f"# {{stage}} output\\n\\n- failed by fake AIDD\\n")


def write_executing_stage_metadata(stage: str, work_item: str, run_id: str) -> None:
    stage_root = (
        Path(".aidd") / "reports" / "runs" / work_item / run_id / "stages" / stage
    )
    attempt_root = stage_root / "attempts" / "attempt-0001"
    attempt_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {{
                "schema_version": 1,
                "run_id": run_id,
                "work_item_id": work_item,
                "stage": stage,
                "status": "executing",
                "created_at_utc": "2026-05-25T00:00:00Z",
                "updated_at_utc": "2026-05-25T00:00:00Z",
                "status_history": [
                    {{
                        "status": "executing",
                        "changed_at_utc": "2026-05-25T00:00:00Z",
                    }}
                ],
            }}
        )
    )


def write_adapter_timeout_stage_artifacts(stage: str, work_item: str, run_id: str) -> None:
    stage_workspace_root = Path(".aidd") / "workitems" / work_item / "stages" / stage
    stage_workspace_root.mkdir(parents=True, exist_ok=True)
    (stage_workspace_root / "questions.md").write_text("# Questions\\n\\n- none\\n")
    (stage_workspace_root / "answers.md").write_text("# Answers\\n\\n- none\\n")
    (stage_workspace_root / "stage-result.md").write_text(
        "# Stage Result\\n\\n"
        "## Status\\n\\n"
        "- Status: `failed`\\n"
    )
    (stage_workspace_root / "validator-report.md").write_text(
        "# Validator Report\\n\\n"
        "## Result\\n\\n"
        "- Validator verdict: `not-run`\\n"
    )

    stage_root = (
        Path(".aidd") / "reports" / "runs" / work_item / run_id / "stages" / stage
    )
    attempt_root = stage_root / "attempts" / "attempt-0001"
    attempt_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {{
                "schema_version": 1,
                "run_id": run_id,
                "work_item_id": work_item,
                "stage": stage,
                "status": "failed",
                "created_at_utc": "2026-05-25T00:00:00Z",
                "updated_at_utc": "2026-05-25T01:00:00Z",
                "status_history": [
                    {{
                        "status": "executing",
                        "changed_at_utc": "2026-05-25T00:00:00Z",
                    }},
                    {{
                        "status": "failed",
                        "changed_at_utc": "2026-05-25T01:00:00Z",
                    }},
                ],
            }}
        )
    )
    (attempt_root / "runtime-exit.json").write_text(
        json.dumps(
            {{
                "schema_version": 1,
                "exit_classification": "timeout",
                "exit_code": 0,
                "stdout_char_count": 0,
                "stderr_char_count": 0,
                "runtime_log_char_count": 0,
            }}
        )
    )
    (attempt_root / "runtime.log").write_text("adapter timed out\\n")
    (attempt_root / "runtime.jsonl").write_text(
        json.dumps({{"event": "runtime_timeout", "stage": stage}}) + "\\n"
    )
    (attempt_root / "events.jsonl").write_text(
        json.dumps({{"event": "runtime_timeout", "stage": stage}}) + "\\n"
    )


def stage_run(args: list[str]) -> int:
    stage = args[2]
    work_item = option(args, "--work-item")
    run_id = option(args, "--run-id")
    if stage == FAIL_STAGE:
        write_failed_stage_artifacts(stage, work_item)
        print(f"Stage run result: action=stop state=failed stage={{stage}}")
        return 7
    if stage == TIMEOUT_STAGE:
        write_executing_stage_metadata(stage, work_item, run_id)
        print(f"Stage run started: state=executing stage={{stage}}", flush=True)
        time.sleep(5)
        return 0
    if stage == NO_PROGRESS_STAGE:
        write_executing_stage_metadata(stage, work_item, run_id)
        print(f"Stage run started: state=executing stage={{stage}}", flush=True)
        time.sleep(5)
        return 0
    if stage == ADAPTER_TIMEOUT_STAGE:
        write_adapter_timeout_stage_artifacts(stage, work_item, run_id)
        print(f"AIDD stage run: stage={{stage}} work_item={{work_item}} runtime=opencode")
        print("Stage run result: action=stop state=failed")
        print("Adapter outcome: timeout")
        return 1
    if stage == BLOCK_STAGE:
        stage_root = Path(".aidd") / "workitems" / work_item / "stages" / stage
        answers_path = stage_root / "answers.md"
        questions_path = stage_root / "questions.md"
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        questions_path.write_text(
            "# Questions\\n\\n- Q1 [blocking]: Which behavior should be implemented?\\n"
        )
        if not answers_path.exists() or "[resolved]" not in answers_path.read_text().lower():
            print("Stage run result: action=wait state=blocked")
            print("Blocking questions are unresolved.")
            print(f"Questions: {{questions_path}}")
            print(f"Answers: {{answers_path}}")
            return 1
    write_stage_outputs(stage, work_item, run_id)
    print(f"Stage run result: action=advance state=succeeded stage={{stage}}")
    return 0


def ui(args: list[str]) -> int:
    port = int(option(args, "--port", "0"))
    work_item = option(args, "--work-item")
    jobs: dict[str, dict[str, object]] = {{}}

    def stage_metadata_status(stage: str, run_id: str) -> str:
        metadata_path = (
            Path(".aidd")
            / "reports"
            / "runs"
            / work_item
            / run_id
            / "stages"
            / stage
            / "stage-metadata.json"
        )
        if not metadata_path.exists():
            return "pending"
        try:
            payload = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            return "pending"
        status = payload.get("status")
        return status if isinstance(status, str) and status else "pending"

    def stage_runtime_log_path(stage: str, run_id: str) -> Path:
        return (
            Path(".aidd")
            / "reports"
            / "runs"
            / work_item
            / run_id
            / "stages"
            / stage
            / "attempts"
            / "attempt-0001"
            / "runtime.log"
        )

    def job_payload(job_id: str) -> dict[str, object]:
        job = jobs[job_id]
        return {{
            "job_id": job_id,
            "kind": "stage",
            "stage": job.get("stage"),
            "status": job.get("status", "running"),
            "exit_code": job.get("exit_code"),
            "message": job.get("message", ""),
            "result": job.get("result"),
            "attempt_path": job.get("attempt_path"),
            "created_at_utc": "2026-05-25T00:00:00Z",
            "updated_at_utc": "2026-05-25T00:00:00Z",
        }}

    def operator_request_view(job: dict[str, object]) -> dict[str, object]:
        attempt_path = Path(str(job.get("attempt_path", "")))
        request_path = attempt_path / "operator-requests.jsonl"
        decision_path = attempt_path / "operator-decisions.jsonl"
        requests = [
            json.loads(line)
            for line in request_path.read_text().splitlines()
            if line.strip()
        ] if request_path.exists() else []
        decisions = [
            json.loads(line)
            for line in decision_path.read_text().splitlines()
            if line.strip()
        ] if decision_path.exists() else []
        decided = {{decision["request_id"] for decision in decisions}}
        return {{
            "attempt_path": attempt_path.as_posix(),
            "requests_path": request_path.as_posix() if request_path.exists() else None,
            "decisions_path": decision_path.as_posix() if decision_path.exists() else None,
            "requests": requests,
            "pending_request_ids": [
                request["id"] for request in requests if request["id"] not in decided
            ],
            "unapproved_request_ids": [
                request["id"] for request in requests if request["id"] not in decided
            ],
            "decisions": decisions,
        }}

    def write_runtime_request(stage: str, run_id: str) -> tuple[str, str]:
        request_id = f"opr-{{stage}}"
        attempt_root = (
            Path(".aidd")
            / "reports"
            / "runs"
            / work_item
            / run_id
            / "stages"
            / stage
            / "attempts"
            / "attempt-0001"
        )
        attempt_root.mkdir(parents=True, exist_ok=True)
        request = {{
            "id": request_id,
            "runtime_id": "codex",
            "stage": stage,
            "kind": "shell",
            "tool_name": "shell",
            "payload": {{"command": UI_OPERATOR_REQUEST_COMMAND}},
            "cwd": Path.cwd().as_posix(),
            "paths": [],
            "risk": "high",
            "suggestions": ["allow_once", "allow_for_session", "deny", "cancel"],
            "created_at_utc": "2026-05-25T00:00:00Z",
        }}
        (attempt_root / "operator-requests.jsonl").write_text(json.dumps(request) + "\\n")
        (attempt_root / "runtime.log").write_text("waiting for operator approval\\n")
        return request_id, attempt_root.as_posix()

    def send_json(
        handler: BaseHTTPRequestHandler,
        payload: dict[str, object],
        status: int = 200,
    ) -> None:
        body = json.dumps(payload).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                body = (
                    "<html><body>"
                    f"<h1>AIDD Operator Console</h1><p>Work item {{work_item}}</p>"
                    "</body></html>"
                ).encode()
                content_type = "text/html; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path.startswith("/api/jobs/"):
                parts = self.path.split("?")[0].strip("/").split("/")
                job_id = parts[2]
                if len(parts) == 3 and job_id in jobs:
                    send_json(self, job_payload(job_id))
                    return
                if len(parts) == 4 and parts[3] == "logs" and job_id in jobs:
                    send_json(
                        self,
                        {{
                            "job_id": job_id,
                            "cursor": 1,
                            "chunks": jobs[job_id].get("chunks", []),
                        }},
                    )
                    return
                if len(parts) == 4 and parts[3] == "operator-requests" and job_id in jobs:
                    send_json(self, operator_request_view(jobs[job_id]))
                    return
            else:
                query = self.path.split("?", 1)[1] if "?" in self.path else ""
                params = dict(
                    item.split("=", 1)
                    for item in query.split("&")
                    if "=" in item
                )
                stage = params.get("stage", "")
                run_id = params.get("run_id", "")
                stage_status = stage_metadata_status(stage, run_id)
                running_stage = stage_status in {{"preparing", "executing", "validating"}}
                next_action = (
                    {{
                        "action": "wait-for-stage",
                        "label": f"{{stage}} running",
                        "detail": "Refresh after the active stage leaves running state.",
                        "stage": stage,
                        "enabled": False,
                    }}
                    if running_stage
                    else {{
                        "action": "run-stage",
                        "label": "Run next stage",
                        "detail": "Continue through the governed flow.",
                        "stage": stage,
                        "enabled": True,
                    }}
                )
                if self.path.startswith("/api/dashboard"):
                    payload = {{
                        "app_version": "test",
                        "dashboard": {{
                            "work_item": work_item,
                            "active_stage": stage,
                            "run": {{
                                "run_id": run_id,
                                "runtime_id": "codex",
                                "stage_target": stage,
                            }},
                            "next_action": next_action,
                            "terminal_handoff": None,
                            "recent_artifacts": [
                                {{"stage": stage, "path": PRIMARY_OUTPUTS.get(stage, "")}}
                            ],
                            "evidence_refs": [
                                {{
                                    "stage": stage,
                                    "kind": "artifact",
                                    "path": PRIMARY_OUTPUTS.get(stage, ""),
                                }}
                            ],
                            "blockers": [],
                            "recovery_actions": [],
                        }},
                    }}
                elif self.path.startswith("/api/run"):
                    payload = {{
                        "run_id": run_id,
                        "work_item": work_item,
                        "status": "succeeded",
                        "recent_artifacts": [
                            {{"stage": stage, "path": PRIMARY_OUTPUTS.get(stage, "")}}
                        ],
                        "evidence_refs": [
                            {{
                                "stage": stage,
                                "kind": "artifact",
                                "path": PRIMARY_OUTPUTS.get(stage, ""),
                            }}
                        ],
                        "blockers": [],
                        "recovery_actions": [],
                    }}
                elif self.path.startswith("/api/stage"):
                    payload = {{
                        "run_id": run_id,
                        "work_item": work_item,
                        "stage": stage,
                        "status": stage_status,
                        "final_state": stage_status,
                    }}
                elif self.path.startswith("/api/questions"):
                    payload = {{
                        "work_item": work_item,
                        "stage": stage,
                        "state": "resolved",
                        "questions": [],
                    }}
                elif self.path.startswith("/api/logs"):
                    runtime_log = stage_runtime_log_path(stage, run_id)
                    if running_stage and not runtime_log.exists():
                        payload = {{
                            "run_id": run_id,
                            "work_item": work_item,
                            "stage": stage,
                            "available": False,
                            "message": "Runtime log is not available yet.",
                        }}
                    else:
                        payload = {{
                            "run_id": run_id,
                            "work_item": work_item,
                            "stage": stage,
                            "chunks": [{{"text": f"stage {{stage}} completed"}}],
                        }}
                elif self.path.startswith("/api/artifacts"):
                    payload = {{
                        "run_id": run_id,
                        "work_item": work_item,
                        "stage": stage,
                        "artifacts": [{{"path": PRIMARY_OUTPUTS.get(stage, "")}}],
                    }}
                else:
                    payload = {{"ok": True, "path": self.path}}
                body = json.dumps(payload).encode()
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode() or "{{}}")
            if self.path == "/api/stage/run":
                stage = str(payload.get("stage", ""))
                run_id = str(payload.get("run_id", ""))
                job_id = f"job-{{len(jobs) + 1}}"
                if stage == UI_OPERATOR_REQUEST_STAGE:
                    request_id, attempt_path = write_runtime_request(stage, run_id)
                    jobs[job_id] = {{
                        "stage": stage,
                        "status": "waiting-for-operator",
                        "exit_code": None,
                        "message": "waiting for operator decision",
                        "attempt_path": attempt_path,
                        "request_id": request_id,
                        "run_id": run_id,
                        "chunks": [{{"sequence": 1, "stream": "stdout", "text": "waiting\\n"}}],
                        "result": {{"waiting_for_operator": True, "request_id": request_id}},
                    }}
                else:
                    write_stage_outputs(stage, work_item, run_id)
                    jobs[job_id] = {{
                        "stage": stage,
                        "status": "completed",
                        "exit_code": 0,
                        "message": "completed",
                        "attempt_path": "",
                        "run_id": run_id,
                        "chunks": [{{"sequence": 1, "stream": "stdout", "text": "done\\n"}}],
                        "result": {{"completed": True, "stage": stage, "run_id": run_id}},
                    }}
                send_json(self, {{"job_id": job_id, "stage": stage, "kind": "stage"}})
                return
            if "/operator-requests/" in self.path and self.path.endswith("/decision"):
                parts = self.path.strip("/").split("/")
                job_id = parts[2]
                request_id = parts[4]
                job = jobs[job_id]
                attempt_path = Path(str(job["attempt_path"]))
                decision = {{
                    "request_id": request_id,
                    "action": str(payload.get("action", "")),
                    "source": "ui",
                    "reason": payload.get("reason"),
                    "created_at_utc": "2026-05-25T00:00:00Z",
                }}
                with (attempt_path / "operator-decisions.jsonl").open("a") as handle:
                    handle.write(json.dumps(decision) + "\\n")
                write_stage_outputs(str(job["stage"]), work_item, str(job.get("run_id", "")))
                job["status"] = "completed"
                job["exit_code"] = 0
                job["message"] = "completed"
                job["result"] = {{"completed": True, "waiting_for_operator": False}}
                send_json(self, operator_request_view(job))
                return
            send_json(self, {{"error": "not found"}}, status=404)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    host, resolved_port = server.server_address[:2]
    print(f"AIDD UI: http://{{host}}:{{resolved_port}}/", flush=True)
    server.serve_forever()
    return 0


def stage_questions(args: list[str]) -> int:
    stage = args[2]
    work_item = option(args, "--work-item")
    stage_root = Path(".aidd") / "workitems" / work_item / "stages" / stage
    answers_path = stage_root / "answers.md"
    questions_path = stage_root / "questions.md"
    if stage == INSPECT_BLOCK_STAGE:
        questions_path.parent.mkdir(parents=True, exist_ok=True)
        questions_path.write_text(
            "# Questions\\n\\n- Q1 [blocking]: Which behavior should be implemented?\\n"
        )
    print(f"Stage questions: {{stage}}")
    questions_text = questions_path.read_text().lower() if questions_path.exists() else ""
    if "[blocking]" in questions_text and (
        not answers_path.exists() or "[resolved]" not in answers_path.read_text().lower()
    ):
        print("pending-blocking")
        print("Blocking questions are unresolved.")
        print(f"Questions: {{questions_path}}")
        print(f"Answers: {{answers_path}}")
        return 0
    print("No unresolved blocking questions.")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["init"]:
        work_item = option(args, "--work-item")
        root = option(args, "--root", ".aidd")
        work_item_root = Path(root) / "workitems" / work_item
        work_item_root.mkdir(parents=True, exist_ok=True)
        print(f"Initialized {{work_item_root}}")
        return 0
    if args[:1] == ["ui"]:
        return ui(args)
    if args[:2] == ["stage", "run"]:
        return stage_run(args)
    if INSPECT_FAIL_COMMAND and " ".join(args[:2]) == INSPECT_FAIL_COMMAND:
        print(f"inspection command failed: {{INSPECT_FAIL_COMMAND}}")
        return 11
    if args[:2] == ["stage", "summary"]:
        print(f"Stage summary: {{args[2]}}")
        return 0
    if args[:2] == ["stage", "questions"]:
        return stage_questions(args)
    if args[:2] == ["run", "show"]:
        print("Run metadata")
        return 0
    if args[:2] == ["run", "logs"]:
        if LOG_BLOCKING_TEXT:
            print("Historical log: Blocking questions are unresolved.")
        print("Run log")
        return 0
    if args[:2] == ["run", "artifacts"]:
        print("Run artifacts")
        return 0
    print("unsupported fake command", args)
    return 2


raise SystemExit(main())
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_scenario_manifest(
    *,
    path: Path,
    repo_url: str,
    setup_commands: tuple[str, ...] = ("printf 'setup\\n' > setup.log",),
    verify_commands: tuple[str, ...] = (
        "test -f .aidd/workitems/WI-LIVE-BLACKBOX/stages/qa/output/stage-result.md",
    ),
    interview_required: bool = False,
    frontend_checkpoints: bool = True,
    runtime_targets: tuple[str, ...] = ("opencode",),
    acceptance_criteria: tuple[str, ...] = ("The fake AIDD stages complete.",),
    product_evaluation: bool = False,
    repo_revision: str = "abc123",
    no_progress_timeout_minutes: int | None = None,
) -> None:
    feature_size = (
        "xlarge"
        if product_evaluation and interview_required
        else "medium"
        if product_evaluation
        else "small"
    )
    live_matrix_role = "product-evaluation" if product_evaluation else "flow-regression"
    patch_budget_files = (
        60
        if feature_size == "xlarge"
        else 20
        if feature_size == "medium"
        else 8
    )
    limits: dict[str, int] = {
        "timeout_minutes": 240,
        "patch_budget_files": patch_budget_files,
    }
    if no_progress_timeout_minutes is not None:
        limits["no_progress_timeout_minutes"] = no_progress_timeout_minutes
    payload = {
        "id": "AIDD-TEST-LIVE-BLACKBOX",
        "scenario_class": "live-full-flow-interview" if interview_required else "live-full-flow",
        "feature_size": feature_size,
        "live_matrix_role": live_matrix_role,
        "automation_lane": "manual",
        "canonical_runtime": runtime_targets[0],
        "task": "exercise black-box live evaluator",
        "repo": {"url": repo_url, "revision": repo_revision},
        "setup": {"commands": list(setup_commands)},
        "aidd_invocation": {"work_item": "WI-LIVE-BLACKBOX"},
        "verify": {"commands": list(verify_commands)},
        "stage_scope": {"start": "idea", "end": "qa"},
        "limits": limits,
        "interview": {"required": interview_required},
        "runtime_targets": list(runtime_targets),
        "live_flow": {
            "driver": "stepwise-black-box",
            "checkpoint_policy": "after-each-step",
            "answer_policy": "agent-decides",
            "frontend_checkpoints": frontend_checkpoints,
        },
        "feature_source": {
            "mode": "authored-task-pool",
            "selection_policy": "first-listed",
            "tasks": [
                {
                    "id": "TASK-123",
                    "title": "exercise live black-box evaluator",
                    "summary": "Use the first authored task as the full-flow seed.",
                    "intent": "Exercise black-box task selection.",
                    "target_change": "Produce fake stage evidence.",
                    "expected_scope": "Test fixture only.",
                    "acceptance_criteria": list(acceptance_criteria),
                    "verification": list(verify_commands),
                    "quality_bar": "Execution evidence is complete.",
                    "size_rationale": "Small test fixture.",
                    **(
                        {
                            "visible_request": (
                                "Implement a realistic product behavior change and "
                                "prove it with focused verification."
                            ),
                            "audit_rubric": (
                                "Review stage quality, product alignment, code quality, "
                                "and verification evidence after every stage."
                            ),
                            "complexity_axes": ["cross-module", "docs"],
                        }
                        if product_evaluation
                        else {}
                    ),
                    **(
                        {
                            "interview": [
                                "Ask which behavior should be implemented before planning."
                            ]
                        }
                        if interview_required
                        else {}
                    ),
                }
            ],
        },
    }
    if interview_required:
        payload["interview"] = {
            "required": True,
            "must_ask_at_least_one": True,
            "blocking_question_topics": ["Behavior choice."],
        }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _install_result_for_fake_aidd(fake_aidd: Path) -> HarnessInstallResult:
    return HarnessInstallResult(
        install_channel="uv-tool",
        artifact_source="local-wheel",
        artifact_identity="ai_driven_dev_v2-test.whl",
        artifact_path=fake_aidd,
        install_home=fake_aidd.parent / "install-home",
        tool_bin_dir=fake_aidd.parent,
        installed_command=(fake_aidd.as_posix(),),
        command_transcripts=(
            HarnessCommandTranscript(
                command="uv tool install --force /tmp/ai_driven_dev_v2-test.whl",
                exit_code=0,
                stdout_text="installed\n",
                stderr_text="",
                duration_seconds=0.25,
            ),
        ),
        duration_seconds=0.25,
    )


def test_harness_environment_preserves_operator_home_after_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator_home = tmp_path / "operator-home"
    operator_home.mkdir()
    monkeypatch.setenv("HOME", operator_home.as_posix())
    fake_aidd = tmp_path / "fake-aidd"
    install_result = _install_result_for_fake_aidd(fake_aidd)
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "scenario-live.yaml"
    scenario_path.parent.mkdir(parents=True)
    _write_scenario_manifest(path=scenario_path, repo_url="https://example.invalid/repo.git")
    scenario = load_scenario(
        scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    environment = _harness_environment(
        scenario=scenario,
        runtime_id="opencode",
        work_item="WI-TEST",
        install_result=install_result,
    )

    assert environment["HOME"] == operator_home.as_posix()
    assert environment["PATH"].split(os.pathsep)[0] == install_result.tool_bin_dir.as_posix()


def test_harness_environment_removes_source_virtualenv_from_target_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator_home = tmp_path / "operator-home"
    operator_home.mkdir()
    source_venv = tmp_path / "source-checkout" / ".venv"
    source_venv_bin = source_venv / ("Scripts" if os.name == "nt" else "bin")
    source_venv_bin.mkdir(parents=True)
    system_bin = tmp_path / "system-bin"
    system_bin.mkdir()
    monkeypatch.setenv("HOME", operator_home.as_posix())
    monkeypatch.setenv("VIRTUAL_ENV", source_venv.as_posix())
    monkeypatch.setenv(
        "PATH",
        os.pathsep.join([source_venv_bin.as_posix(), system_bin.as_posix()]),
    )
    fake_aidd = tmp_path / "fake-aidd"
    install_result = _install_result_for_fake_aidd(fake_aidd)
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "scenario-live.yaml"
    scenario_path.parent.mkdir(parents=True)
    _write_scenario_manifest(path=scenario_path, repo_url="https://example.invalid/repo.git")
    scenario = load_scenario(
        scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    environment = _harness_environment(
        scenario=scenario,
        runtime_id="opencode",
        work_item="WI-TEST",
        install_result=install_result,
    )

    assert "VIRTUAL_ENV" not in environment
    path_entries = environment["PATH"].split(os.pathsep)
    assert path_entries[0] == install_result.tool_bin_dir.as_posix()
    assert source_venv_bin.as_posix() not in path_entries
    assert system_bin.as_posix() in path_entries
    assert environment["HOME"] == operator_home.as_posix()


def _prepare_live_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    runtime_targets: tuple[str, ...] = ("opencode",),
    fail_stage: str | None = None,
    timeout_stage: str | None = None,
    no_progress_stage: str | None = None,
    adapter_timeout_stage: str | None = None,
    block_stage: str | None = None,
    ui_operator_request_stage: str | None = None,
    ui_operator_request_command: str = "pwd",
    internal_operator_decision_stage: str | None = None,
    setup_commands: tuple[str, ...] = ("printf 'setup\\n' > setup.log",),
    verify_commands: tuple[str, ...] = (
        "test -f .aidd/workitems/WI-LIVE-BLACKBOX/stages/qa/output/stage-result.md",
    ),
    interview_required: bool = False,
    frontend_checkpoints: bool = True,
    acceptance_criteria: tuple[str, ...] = ("The fake AIDD stages complete.",),
    inspect_block_stage: str | None = None,
    inspect_fail_command: str | None = None,
    log_blocking_text: bool = False,
    stage_result_validator_verdict: str | None = None,
    stage_result_direct_qa_next_action_stage: str | None = None,
    stage_result_generic_next_action_stage: str | None = None,
    stray_top_level_workitems_stage: str | None = None,
    ignored_pollution_stage: str | None = None,
    implement_untracked_product_file: str | None = None,
    product_evaluation: bool = False,
    no_progress_timeout_minutes: int | None = None,
) -> tuple[Path, Path, Path]:
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name=runtime_targets[0],
    )
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    source_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=source_repo,
        text=True,
    ).strip()
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(
        fake_aidd,
        fail_stage=fail_stage,
        timeout_stage=timeout_stage,
        no_progress_stage=no_progress_stage,
        adapter_timeout_stage=adapter_timeout_stage,
        block_stage=block_stage,
        ui_operator_request_stage=ui_operator_request_stage,
        ui_operator_request_command=ui_operator_request_command,
        internal_operator_decision_stage=internal_operator_decision_stage,
        inspect_block_stage=inspect_block_stage,
        inspect_fail_command=inspect_fail_command,
        log_blocking_text=log_blocking_text,
        stage_result_validator_verdict=stage_result_validator_verdict,
        stage_result_direct_qa_next_action_stage=(
            stage_result_direct_qa_next_action_stage
        ),
        stage_result_generic_next_action_stage=stage_result_generic_next_action_stage,
        stray_top_level_workitems_stage=stray_top_level_workitems_stage,
        ignored_pollution_stage=ignored_pollution_stage,
        implement_untracked_product_file=implement_untracked_product_file,
    )
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=setup_commands,
        verify_commands=verify_commands,
        interview_required=interview_required,
        frontend_checkpoints=frontend_checkpoints,
        runtime_targets=runtime_targets,
        acceptance_criteria=acceptance_criteria,
        product_evaluation=product_evaluation,
        repo_revision=source_revision,
        no_progress_timeout_minutes=no_progress_timeout_minutes,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box.prepare_local_wheel_install",
        lambda *, work_root, run_id, repository_root: _install_result_for_fake_aidd(
            fake_aidd
        ),
    )
    return scenario_path, tmp_path / "work-root", tmp_path / ".aidd" / "reports" / "evals"


def test_fake_runtime_success_has_no_unconditional_delay(tmp_path: Path) -> None:
    fake_aidd = tmp_path / "fake-aidd"
    working_copy = tmp_path / "working-copy"
    working_copy.mkdir()
    _write_fake_aidd(fake_aidd)

    completed = subprocess.run(
        (
            fake_aidd.as_posix(),
            "stage",
            "run",
            "idea",
            "--work-item",
            "WI-BARRIER",
            "--run-id",
            "run-barrier",
        ),
        cwd=working_copy,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )

    assert completed.returncode == 0
    assert "time.sleep(0.75)" not in fake_aidd.read_text(encoding="utf-8")


def test_fake_runtime_transition_barrier_is_explicit_and_bounded(tmp_path: Path) -> None:
    fake_aidd = tmp_path / "fake-aidd"
    working_copy = tmp_path / "working-copy"
    working_copy.mkdir()
    ready_path = tmp_path / "barrier.ready"
    release_path = tmp_path / "barrier.release"
    _write_fake_aidd(fake_aidd)
    environment = dict(os.environ)
    environment.update(
        {
            "AIDD_FAKE_RUNTIME_BARRIER_STAGE": "idea",
            "AIDD_FAKE_RUNTIME_BARRIER_READY_PATH": ready_path.as_posix(),
            "AIDD_FAKE_RUNTIME_BARRIER_RELEASE_PATH": release_path.as_posix(),
            "AIDD_FAKE_RUNTIME_BARRIER_TIMEOUT_SECONDS": "2",
        }
    )

    process = subprocess.Popen(
        (
            fake_aidd.as_posix(),
            "stage",
            "run",
            "idea",
            "--work-item",
            "WI-BARRIER",
            "--run-id",
            "run-barrier",
        ),
        cwd=working_copy,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + 2.0
    while not ready_path.exists() and time.monotonic() < deadline:
        time.sleep(0.01)

    assert ready_path.exists()
    assert process.poll() is None
    release_path.write_text("release\n", encoding="utf-8")
    stdout_text, stderr_text = process.communicate(timeout=2)

    assert process.returncode == 0, stderr_text
    assert "state=succeeded" in stdout_text


def _write_stage_quality_audit(
    bundle_root: Path,
    *,
    stage: str,
    flow_decision: str = "continue",
    remediation_request: dict[str, object] | None = None,
) -> Path:
    state_path = bundle_root / "flow-state.json"
    stage_run_id = stage
    if state_path.exists():
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
        required_path = state_payload.get("quality_review_required_path")
        required_stage_run_id = state_payload.get("quality_review_required_stage_run_id")
        if isinstance(required_stage_run_id, str) and required_stage_run_id:
            stage_run_id = required_stage_run_id
        path = Path(required_path) if isinstance(required_path, str) else (
            bundle_root / "stage-quality-audits" / f"{stage}.md"
        )
    else:
        path = bundle_root / "stage-quality-audits" / f"{stage}.md"
    remediation_lines: list[str] = []
    if remediation_request is not None:
        raw_source_ids = remediation_request.get("source_ids", ())
        source_ids = (
            raw_source_ids
            if isinstance(raw_source_ids, list | tuple)
            else (raw_source_ids,)
        )
        remediation_lines = [
            "",
            "## Remediation Request",
            f"- Source stage: {remediation_request['source_stage']}",
            "- Source ids: " + ", ".join(str(item) for item in source_ids),
            f"- Operator note: {remediation_request['operator_note']}",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            (
                f"# Stage Quality Audit: {stage}",
                "",
                "## Decision",
                "- Stage quality: acceptable",
                f"- Flow decision: {flow_decision}",
                "- Reason: Synthetic test audit.",
                "",
                "## Checks",
                "- Product alignment: checked",
                "- Evidence quality: checked",
                "- Repository understanding: checked",
                "- Missing questions or assumptions: none",
                "- Cross-stage consistency: checked",
                "- Risk handling: checked",
                "- Specific defects: none",
                "",
                "## Evidence Reviewed",
                f"- Stage artifacts: stage-audits/{stage_run_id}.json",
                "- Runtime logs: runtime-log.txt",
                "- Runner stage audit: present",
                "- Target repo evidence: synthetic fixture",
                "",
                "## Notes For Final Report",
                "- AIDD quality signal: synthetic",
                "- Residual risks: none",
                *remediation_lines,
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _run_product_evaluation_to_terminal(
    *,
    scenario_path: Path,
    work_root: Path,
    report_root: Path,
    runtime_id: str = "opencode",
) -> BlackBoxLiveE2EResult:
    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        work_root=work_root,
        report_root=report_root,
    )
    while result.status == "awaiting-quality-review":
        state_payload = json.loads(
            (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
        )
        required_stage = state_payload["quality_review_required_stage"]
        assert isinstance(required_stage, str)
        _write_stage_quality_audit(result.bundle_root, stage=required_stage)
        result = run_black_box_live_e2e(
            scenario_path=scenario_path,
            runtime_id=runtime_id,
            work_root=work_root,
            report_root=report_root,
            run_id=result.run_id,
        )
    return result


def _continue_product_evaluation_until_stage(
    *,
    scenario_path: Path,
    work_root: Path,
    report_root: Path,
    stage: str,
    runtime_id: str = "opencode",
) -> BlackBoxLiveE2EResult:
    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id=runtime_id,
        work_root=work_root,
        report_root=report_root,
    )
    while result.status == "awaiting-quality-review":
        state_payload = json.loads(
            (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
        )
        required_stage = state_payload["quality_review_required_stage"]
        assert isinstance(required_stage, str)
        if required_stage == stage:
            return result
        _write_stage_quality_audit(result.bundle_root, stage=required_stage)
        result = run_black_box_live_e2e(
            scenario_path=scenario_path,
            runtime_id=runtime_id,
            work_root=work_root,
            report_root=report_root,
            run_id=result.run_id,
        )
    raise AssertionError(f"run reached {result.status}, not quality review for {stage}")


def _fake_remediation_ui_job(
    *,
    ctx: object,
    endpoint: str,
    payload: dict[str, object],
    stage: str,
    stage_run_id: str,
    action: str,
) -> tuple[str, Path, dict[str, object]]:
    bundle_root = ctx.bundle_root
    assert isinstance(bundle_root, Path)
    stale_stages = (
        ["review", "qa"]
        if endpoint == "/api/remediation/launch"
        else (["qa"] if str(payload.get("stage", "")) == "review" else [])
    )
    evidence_payload: dict[str, object] = {
        "endpoint": endpoint,
        "payload": payload,
        "stage": stage,
        "stage_run_id": stage_run_id,
        "action": action,
        "job_payload": {
            "status": "completed",
            "result": {
                "completed": True,
                "status": {
                    "stale_stages": [
                        {"stage": stale_stage} for stale_stage in stale_stages
                    ],
                },
            },
        },
    }
    evidence_path = (
        bundle_root
        / "remediation-actions"
        / f"fake-{stage_run_id}-{action}.json"
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence_payload, indent=2) + "\n", encoding="utf-8")
    return "pass", evidence_path, evidence_payload


def test_black_box_live_e2e_passes_stepwise_and_writes_flow_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    assert result.bundle_root == report_root / result.run_id
    for filename in (
        "flow-state.json",
        "flow-steps.json",
        "flow-report.md",
        "operator-actions.jsonl",
        "verdict.md",
        "grader.json",
        "log-analysis.md",
        "stage-timing.json",
        "repair-history.md",
        "install-transcript.json",
        "setup-transcript.json",
        "run-transcript.json",
        "verify-transcript.json",
        "teardown-transcript.json",
        "target-workspace-evidence.json",
        "target-workspace-evidence.md",
        "next-flow-checkpoint.json",
        "next-flow-checkpoint.md",
    ):
        assert (result.bundle_root / filename).exists(), filename
    for filename in (
        "quality-report.md",
        "quality-transcript.json",
        "acceptance-coverage.json",
        "acceptance-coverage.md",
        "operator-quality-analysis.md",
        "operator-quality-analysis-validation.json",
        "ui-ux-checkpoints.json",
        "ui-ux-checkpoints.md",
    ):
        assert not (result.bundle_root / filename).exists(), filename
    assert not (result.bundle_root / "next-flow-lineage.json").exists()

    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    run_stage_steps = [step for step in steps if step["action"] == "run-stage"]
    assert [step["stage"] for step in run_stage_steps] == list(STAGES)
    assert all(
        command["command"][1:3] == ["stage", "run"]
        for step in run_stage_steps
        for command in step["commands"]
    )
    assert "black-box" in (result.bundle_root / "harness-metadata.json").read_text(
        encoding="utf-8"
    )
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["work_root"] == work_root.as_posix()
    assert state_payload["report_root"] == report_root.as_posix()
    assert state_payload["run_work_root"] == (work_root / result.run_id).as_posix()
    assert Path(state_payload["install_home"]).is_absolute()
    assert state_payload["install_home"] == state_payload["install"]["install_home"]
    assert str(state_payload["target_repo_root"]).startswith(
        (work_root / result.run_id / "target").as_posix()
    )
    assert ".aidd/harness-cache" not in str(state_payload["target_repo_root"])
    workspace_baseline_context = (
        Path(state_payload["target_repo_root"])
        / ".aidd"
        / "workitems"
        / "WI-LIVE-BLACKBOX"
        / "context"
        / "workspace-baseline.md"
    ).read_text(encoding="utf-8")
    assert "# Workspace Baseline" in workspace_baseline_context
    assert "## Setup-Owned Workspace Baseline" in workspace_baseline_context
    assert "## Setup-Owned Files Present" in workspace_baseline_context
    assert "`aidd.example.toml`" in workspace_baseline_context
    assert "## Baseline Untracked Files" in workspace_baseline_context
    assert "`setup.log`" in workspace_baseline_context
    completed_stage_runs = state_payload["completed_stage_runs"]
    assert [item["stage"] for item in completed_stage_runs] == list(STAGES)
    for index, stage in enumerate(STAGES, start=1):
        stage_run_id = f"stage-{index:04d}-{stage}"
        assert (result.bundle_root / "stage-audits" / f"{stage_run_id}.json").exists()
        assert (result.bundle_root / "stage-audits" / f"{stage_run_id}.md").exists()
        stage_audit = json.loads(
            (result.bundle_root / "stage-audits" / f"{stage_run_id}.json").read_text(
                encoding="utf-8"
            )
        )
        assert stage_audit["stage_run_id"] == stage_run_id
        assert stage_audit["stage_state"] == "passed"
        assert stage_audit["unresolved_questions"] is False
        assert stage_audit["consistency_findings"] == []
    run_transcript = json.loads(
        (result.bundle_root / "run-transcript.json").read_text(encoding="utf-8")
    )
    assert run_transcript["timed_out"] is False
    assert run_transcript["timeout_seconds"] is None
    assert run_transcript["timeout_policy"] == {
        "scope": "per-stage-command",
        "stage_command_timeout_seconds": 14400.0,
        "no_progress_timeout_seconds": 1800.0,
        "global_flow_timeout_seconds": None,
        "runtime_config_source": "aidd.example.toml",
    }
    stage_timing = json.loads(
        (result.bundle_root / "stage-timing.json").read_text(encoding="utf-8")
    )
    run_stage_timing_steps = [
        step for step in stage_timing["steps"] if step["step"] == "run-stage"
    ]
    assert run_stage_timing_steps
    assert all(step["timeout_seconds"] == 14400.0 for step in run_stage_timing_steps)
    log_analysis = (result.bundle_root / "log-analysis.md").read_text(encoding="utf-8")
    assert "- Scope: `per-stage-command`" in log_analysis
    assert "- Stage Command Timeout: `14400.000s`" in log_analysis
    assert "- Global Flow Timeout: `none`" in log_analysis
    assert "Runtime Adapter Timeout Profile" in log_analysis
    grader_payload = json.loads((result.bundle_root / "grader.json").read_text(encoding="utf-8"))
    assert grader_payload["execution"]["status"] == "pass"
    assert "quality" not in grader_payload
    assert grader_payload["manual_quality_artifacts"] == {
        "required_for_counted_clean": False,
        "stage_quality_audits": [],
        "final_reports": [],
    }
    assert len(grader_payload["stage_audits"]) == len(STAGES)
    assert grader_payload["steps"][-1]["action"] == "finish"
    metadata_payload = json.loads(
        (result.bundle_root / "harness-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["temp_layout"]["work_root"] == work_root.as_posix()
    assert metadata_payload["temp_layout"]["report_root"] == report_root.as_posix()
    assert metadata_payload["black_box"]["frontend_checkpoint_evidence"].endswith(
        "frontend-checkpoints.json"
    )
    assert metadata_payload["aidd_artifact_references"][
        "target_workspace_evidence"
    ].endswith("target-workspace-evidence.json")
    target_workspace_evidence = json.loads(
        (result.bundle_root / "target-workspace-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    assert target_workspace_evidence["classification"]["known_harness_files"] == [
        "aidd.example.toml"
    ]
    assert "setup.log" in target_workspace_evidence["classification"][
        "baseline_untracked_files"
    ]
    assert target_workspace_evidence["non_gating_findings"] == []
    finish_step = next(
        step for step in steps if step["action"] == "finish"
    )
    assert any(
        path.endswith("target-workspace-evidence.json")
        for path in finish_step["evidence_paths"]
    )
    frontend_payload = json.loads(
        (result.bundle_root / "frontend-checkpoints.json").read_text(encoding="utf-8")
    )
    assert frontend_payload["enabled"] is True
    assert len(frontend_payload["checkpoints"]) == len(STAGES) * 2
    assert all(
        checkpoint["classification"] in {"pass", "skipped"}
        for checkpoint in frontend_payload["checkpoints"]
    )
    assert all(
        checkpoint["operator_surface"]["ok"] is True
        for checkpoint in frontend_payload["checkpoints"]
        if checkpoint["classification"] == "pass"
    )
    skipped_running_checkpoints = [
        checkpoint
        for checkpoint in frontend_payload["checkpoints"]
        if checkpoint["classification"] == "skipped"
    ]
    assert all(
        checkpoint["phase"] == "running-stage"
        and checkpoint["operator_surface"]["failed_checks"] == ["checkpoint-not-run"]
        and checkpoint["failure_reason"]
        == "Running stage state ended before UI checkpoint probes could run."
        for checkpoint in skipped_running_checkpoints
    )
    running_checkpoint = next(
        checkpoint
        for checkpoint in frontend_payload["checkpoints"]
        if checkpoint["stage"] == STAGES[0] and checkpoint["phase"] == "running-stage"
    )
    assert running_checkpoint["observed_stage_status"] == "executing"
    assert {
        check["name"]
        for check in running_checkpoint["operator_surface"]["checks"]
    }.issuperset(
        {
            "operator-shell-visible",
            "work-item-context-visible",
            "run-context-visible",
            "running-stage-visible",
            "running-wait-action-visible",
            "runtime-log-affordance-visible",
        }
    )
    first_operator_surface = next(
        checkpoint["operator_surface"]
        for checkpoint in frontend_payload["checkpoints"]
        if checkpoint["stage"] == STAGES[0] and checkpoint["phase"] == "post-stage"
    )
    assert {
        check["name"]
        for check in first_operator_surface["checks"]
    }.issuperset(
        {
            "operator-shell-visible",
            "work-item-context-visible",
            "run-context-visible",
            "active-stage-visible",
            "stage-status-visible",
            "next-action-visible",
            "runtime-log-surface-visible",
            "artifact-surface-visible",
        }
    )
    frontend_markdown = (
        result.bundle_root / "frontend-checkpoints.md"
    ).read_text(encoding="utf-8")
    assert "- Scope: raw UI/API and operator-surface run-integrity evidence" in (
        frontend_markdown
    )
    assert "not a UI/UX audit, not screenshot evidence, and not a quality gate" in (
        frontend_markdown
    )
    assert "## Manual Visual Review Checklist" in frontend_markdown
    assert "Visible next action and active stage match the checkpoint stage." in (
        frontend_markdown
    )
    assert "without clipped single-letter chips" in frontend_markdown
    assert "Record screenshot paths or browser notes in the manual final report" in (
        frontend_markdown
    )
    assert "- Operator surface: ok=`True`" in frontend_markdown
    assert "- Phase: `running-stage`" in frontend_markdown
    assert "`running-wait-action-visible`: ok=`True`" in frontend_markdown
    assert "`runtime-log-affordance-visible`: ok=`True`" in frontend_markdown
    assert "- Phase: `post-stage`" in frontend_markdown
    assert "`next-action-visible`: ok=`True`" in frontend_markdown
    next_flow_payload = json.loads(
        (result.bundle_root / "next-flow-checkpoint.json").read_text(encoding="utf-8")
    )
    assert next_flow_payload["terminal_status"] == "pass"
    assert "quality_gate" not in next_flow_payload
    assert "counting_status" not in next_flow_payload
    assert "acceptance_coverage_status" not in next_flow_payload
    assert "ui_ux_gate" not in next_flow_payload
    assert next_flow_payload["flow_complete_visible"] is True
    assert next_flow_payload["source_run_summary"]["source_run_id"] == result.run_id
    assert next_flow_payload["source_run_summary"]["source_work_item_id"] == (
        "WI-LIVE-BLACKBOX"
    )
    assert next_flow_payload["source_run_summary"]["final_qa_status"] == "ready"
    assert next_flow_payload["source_run_summary"]["qa_stage_state"] == "passed"
    assert next_flow_payload["next_flow_actions"]["operator_decision"]["decision"] == (
        "no-follow-up"
    )
    assert (
        next_flow_payload["next_flow_actions"]["operator_decision"][
            "requires_second_public_repository_flow"
        ]
        is False
    )
    assert next_flow_payload["optional_lineage_metadata"]["child_flow_required"] is False
    assert next_flow_payload["optional_lineage_metadata"]["source_run_id"] == result.run_id
    assert "start-follow-up-flow" in {
        action["action"]
        for action in next_flow_payload["next_flow_actions"][
            "recommended_next_flow_actions"
        ]
    }
    next_flow_markdown = (result.bundle_root / "next-flow-checkpoint.md").read_text(
        encoding="utf-8"
    )
    assert "Default decision: `no-follow-up`" in next_flow_markdown
    assert "Requires second public-repository flow: `false`" in next_flow_markdown


def test_black_box_live_e2e_imports_manual_frontend_evidence_without_gating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)
    manual_evidence = tmp_path / "manual-frontend-evidence-source"
    screenshot_dir = manual_evidence / "screenshots"
    screenshot_dir.mkdir(parents=True)
    (manual_evidence / "browser-notes.md").write_text(
        "# Browser Notes\n\n- Desktop next action looked clear.\n",
        encoding="utf-8",
    )
    (screenshot_dir / "mobile-flow-complete.png").write_bytes(b"fake screenshot")

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        manual_frontend_evidence=manual_evidence,
    )

    assert result.status == "pass"
    frontend_payload = json.loads(
        (result.bundle_root / "frontend-checkpoints.json").read_text(encoding="utf-8")
    )
    assert all(
        checkpoint["classification"] == "pass"
        for checkpoint in frontend_payload["checkpoints"]
    )
    manual_payload = frontend_payload["manual_visual_evidence"]
    assert manual_payload["status"] == "imported"
    assert manual_payload["imported"] is True
    assert manual_payload["non_gating"] is True
    assert manual_payload["kind"] == "directory"
    assert manual_payload["source_path"] == manual_evidence.resolve().as_posix()
    assert manual_payload["files"] == [
        "browser-notes.md",
        "screenshots/mobile-flow-complete.png",
    ]
    imported_root = result.bundle_root / "manual-frontend-evidence"
    assert manual_payload["bundle_path"] == imported_root.as_posix()
    assert (imported_root / "browser-notes.md").read_text(encoding="utf-8").startswith(
        "# Browser Notes"
    )
    assert (imported_root / "screenshots" / "mobile-flow-complete.png").read_bytes() == (
        b"fake screenshot"
    )

    frontend_markdown = (
        result.bundle_root / "frontend-checkpoints.md"
    ).read_text(encoding="utf-8")
    assert "## Manual Browser Evidence" in frontend_markdown
    assert "- Status: `imported`" in frontend_markdown
    assert "- Non-gating: `True`" in frontend_markdown
    assert "`screenshots/mobile-flow-complete.png`" in frontend_markdown
    assert "they do not change runner classifications" in frontend_markdown

    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["manual_frontend_evidence_source"] == (
        manual_evidence.resolve().as_posix()
    )
    metadata_payload = json.loads(
        (result.bundle_root / "harness-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["black_box"]["manual_frontend_evidence"] == (
        imported_root.as_posix()
    )


def test_black_box_live_product_evaluation_stops_after_stage_for_quality_review(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "awaiting-quality-review"
    required_path = result.bundle_root / "stage-quality-audits" / "stage-0001-idea.md"
    assert result.quality_review_request_path == required_path
    assert not required_path.exists()
    assert (result.bundle_root / "stage-audits" / "stage-0001-idea.json").exists()
    assert not (result.bundle_root / "stage-audits" / "idea.json").exists()
    assert not (result.bundle_root / "stage-audits" / "stage-0002-research.json").exists()
    assert not (result.bundle_root / "verdict.md").exists()
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["status"] == "awaiting-quality-review"
    assert state_payload["next_action"] == "quality-review"
    assert state_payload["quality_review_required_stage"] == "idea"
    assert state_payload["quality_review_required_stage_run_id"] == "stage-0001-idea"
    assert state_payload["completed_stages"] == ["idea"]
    assert [item["stage_run_id"] for item in state_payload["completed_stage_runs"]] == [
        "stage-0001-idea"
    ]


def test_black_box_live_product_evaluation_resume_requires_stage_quality_audit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    with pytest.raises(ValueError, match="awaiting quality review"):
        run_black_box_live_e2e(
            scenario_path=scenario_path,
            runtime_id="opencode",
            work_root=work_root,
            report_root=report_root,
            run_id=first.run_id,
        )


def test_black_box_live_product_evaluation_resume_requires_valid_flow_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    invalid_audit_path = first.quality_review_request_path
    assert invalid_audit_path is not None
    invalid_audit_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_audit_path.write_text(
        "\n".join(
            (
                "# Stage Quality Audit: idea",
                "",
                "## Decision",
                "- Stage quality: acceptable",
                "- Reason: Missing flow decision should not unlock the next stage.",
                "",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    resumed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert resumed.status == "awaiting-quality-review"
    assert resumed.quality_review_request_path == invalid_audit_path
    assert not (resumed.bundle_root / "stage-audits" / "stage-0002-research.json").exists()
    state_payload = json.loads(
        (resumed.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["completed_stages"] == ["idea"]
    assert (
        state_payload["quality_review_reason"]
        == "stage quality audit is missing a valid Flow decision"
    )


def test_black_box_live_product_evaluation_resume_continues_after_audit_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    _write_stage_quality_audit(first.bundle_root, stage="idea")

    resumed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert resumed.status == "awaiting-quality-review"
    assert resumed.run_id == first.run_id
    assert resumed.quality_review_request_path == (
        resumed.bundle_root / "stage-quality-audits" / "stage-0002-research.md"
    )
    state_payload = json.loads(
        (resumed.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["completed_stages"] == ["idea", "research"]
    assert [item["stage_run_id"] for item in state_payload["completed_stage_runs"]] == [
        "stage-0001-idea",
        "stage-0002-research",
    ]
    assert (resumed.bundle_root / "stage-audits" / "stage-0002-research.json").exists()
    assert not (resumed.bundle_root / "stage-audits" / "research.json").exists()


def test_black_box_live_product_evaluation_stop_not_counted_is_manual_quality_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    _write_stage_quality_audit(
        first.bundle_root,
        stage="idea",
        flow_decision="stop-not-counted",
    )
    monkeypatch.setattr(
        live_orchestration,
        "_run_setup",
        lambda ctx: (_ for _ in ()).throw(
            AssertionError("manual quality stop resume must not rerun setup")
        ),
    )

    stopped = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert stopped.status == "manual-quality-stop"
    assert not (stopped.bundle_root / "verdict.md").exists()
    assert stopped.manual_quality_stop_path == (
        stopped.bundle_root / "manual-quality-stop.md"
    )
    assert stopped.manual_quality_stop_path.exists()
    assert (stopped.bundle_root / "target-workspace-evidence.json").exists()
    assert (stopped.bundle_root / "target-workspace-evidence.md").exists()
    manual_stop_payload = json.loads(
        (stopped.bundle_root / "manual-quality-stop.json").read_text(encoding="utf-8")
    )
    assert manual_stop_payload["status"] == "manual-quality-stop"
    assert manual_stop_payload["manual_decision"] == "stop-not-counted"
    assert manual_stop_payload["stage"] == "idea"
    assert manual_stop_payload["runner_execution_verdict"] == {
        "emitted": False,
        "reason": (
            "manual-quality-stop is a manual product-quality terminal state, "
            "not an execution verdict"
        ),
    }
    assert manual_stop_payload["evidence_paths"]["target_workspace_evidence_json"].endswith(
        "target-workspace-evidence.json"
    )
    manual_stop_markdown = stopped.manual_quality_stop_path.read_text(encoding="utf-8")
    assert "Runner execution verdict: `not emitted`" in manual_stop_markdown
    state_payload = json.loads(
        (stopped.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["status"] == "manual-quality-stop"
    assert state_payload["quality_review_decision"] == "stop-not-counted"
    steps = json.loads((stopped.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    assert steps[-1]["classification"] == "manual-quality-stop"


def test_black_box_live_product_evaluation_request_remediation_from_review_runs_new_implement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    monkeypatch.setattr(
        live_orchestration,
        "_run_ui_remediation_job",
        _fake_remediation_ui_job,
    )
    review_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="review",
    )
    _write_stage_quality_audit(
        review_checkpoint.bundle_root,
        stage="review",
        flow_decision="request-remediation",
        remediation_request={
            "source_stage": "review",
            "source_ids": ["RV-1"],
            "operator_note": "Fix rejected review finding.",
        },
    )

    remediated = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    assert remediated.status == "awaiting-quality-review"
    state_payload = json.loads(
        (remediated.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["quality_review_required_stage"] == "implement"
    assert state_payload["quality_review_required_stage_run_id"] == "stage-0008-implement"
    assert state_payload["stale_downstream_stages"] == ["review", "qa"]
    assert state_payload["handled_quality_stage_run_ids"] == ["stage-0007-review"]
    assert state_payload["remediation_cycles"] == 1
    assert [item["stage_run_id"] for item in state_payload["completed_stage_runs"]] == [
        "stage-0001-idea",
        "stage-0002-research",
        "stage-0003-plan",
        "stage-0004-review-spec",
        "stage-0005-tasklist",
        "stage-0006-implement",
        "stage-0007-review",
        "stage-0008-implement",
    ]
    assert (remediated.bundle_root / "stage-audits" / "stage-0006-implement.json").exists()
    assert (remediated.bundle_root / "stage-audits" / "stage-0008-implement.json").exists()
    assert not (remediated.bundle_root / "stage-audits" / "implement.json").exists()


def test_black_box_live_product_evaluation_request_remediation_allows_operator_audit_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    calls: list[dict[str, object]] = []

    def fake_remediation_ui_job(
        *,
        ctx: object,
        endpoint: str,
        payload: dict[str, object],
        stage: str,
        stage_run_id: str,
        action: str,
    ) -> tuple[str, Path, dict[str, object]]:
        calls.append(
            {
                "endpoint": endpoint,
                "payload": payload,
                "stage": stage,
                "stage_run_id": stage_run_id,
                "action": action,
            }
        )
        return _fake_remediation_ui_job(
            ctx=ctx,
            endpoint=endpoint,
            payload=payload,
            stage=stage,
            stage_run_id=stage_run_id,
            action=action,
        )

    monkeypatch.setattr(
        live_orchestration,
        "_run_ui_remediation_job",
        fake_remediation_ui_job,
    )
    review_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="review",
    )
    _write_stage_quality_audit(
        review_checkpoint.bundle_root,
        stage="review",
        flow_decision="request-remediation",
        remediation_request={
            "source_stage": "review",
            "source_ids": ["OP-RV-1"],
            "operator_note": "Fix operator audit finding.",
        },
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    assert result.status == "awaiting-quality-review"
    assert calls[0]["payload"] == {
        "source_stage": "review",
        "source_ids": ["OP-RV-1"],
        "operator_note": "Fix operator audit finding.",
        "target_stage": "implement",
        "runtime": "opencode",
        "run_id": review_checkpoint.run_id,
        "log_follow": True,
        "allow_operator_audit_source_ids": True,
    }


def test_black_box_live_product_evaluation_failed_remediation_launch_stops_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    calls: list[dict[str, object]] = []

    def fake_failed_remediation_ui_job(
        *,
        ctx: object,
        endpoint: str,
        payload: dict[str, object],
        stage: str,
        stage_run_id: str,
        action: str,
    ) -> tuple[str, Path, dict[str, object]]:
        bundle_root = ctx.bundle_root
        assert isinstance(bundle_root, Path)
        calls.append(
            {
                "endpoint": endpoint,
                "payload": payload,
                "stage": stage,
                "stage_run_id": stage_run_id,
                "action": action,
            }
        )
        evidence_payload: dict[str, object] = {
            "endpoint": endpoint,
            "payload": payload,
            "stage": stage,
            "stage_run_id": stage_run_id,
            "action": action,
            "failure_reason": "Remediation job ended with status `failed`.",
            "job_payload": {
                "status": "failed",
                "result": {
                    "completed": False,
                    "stage_result": {
                        "stage": stage,
                        "run_id": payload["run_id"],
                        "exit_code": 1,
                    },
                },
            },
        }
        evidence_path = (
            bundle_root
            / "remediation-actions"
            / f"fake-{stage_run_id}-{action}-failed.json"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence_payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return "fail", evidence_path, evidence_payload

    monkeypatch.setattr(
        live_orchestration,
        "_run_ui_remediation_job",
        fake_failed_remediation_ui_job,
    )
    review_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="review",
    )
    _write_stage_quality_audit(
        review_checkpoint.bundle_root,
        stage="review",
        flow_decision="request-remediation",
        remediation_request={
            "source_stage": "review",
            "source_ids": ["RV-1"],
            "operator_note": "Fix rejected review finding.",
        },
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    assert result.status == "fail"
    assert calls == [
        {
            "endpoint": "/api/remediation/launch",
            "payload": {
                "source_stage": "review",
                "source_ids": ["RV-1"],
                "operator_note": "Fix rejected review finding.",
                "target_stage": "implement",
                "runtime": "opencode",
                "run_id": review_checkpoint.run_id,
                "log_follow": True,
            },
            "stage": "implement",
            "stage_run_id": "stage-0008-implement",
            "action": "launch",
        }
    ]
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["status"] == "fail"
    assert state_payload["error"] == "remediation operator UI job failed"


def test_black_box_live_product_evaluation_reruns_stale_review_then_qa(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    monkeypatch.setattr(
        live_orchestration,
        "_run_ui_remediation_job",
        _fake_remediation_ui_job,
    )
    review_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="review",
    )
    _write_stage_quality_audit(
        review_checkpoint.bundle_root,
        stage="review",
        flow_decision="request-remediation",
        remediation_request={
            "source_stage": "review",
            "source_ids": ["RV-1"],
            "operator_note": "Fix rejected review finding.",
        },
    )
    implement_checkpoint = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )
    _write_stage_quality_audit(implement_checkpoint.bundle_root, stage="implement")

    review_rerun = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    assert review_rerun.status == "awaiting-quality-review"
    state_payload = json.loads(
        (review_rerun.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["quality_review_required_stage"] == "review"
    assert state_payload["quality_review_required_stage_run_id"] == "stage-0009-review"
    assert state_payload["stale_downstream_stages"] == ["qa"]
    _write_stage_quality_audit(review_rerun.bundle_root, stage="review")

    qa_rerun = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    assert qa_rerun.status == "awaiting-quality-review"
    state_payload = json.loads(
        (qa_rerun.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["quality_review_required_stage"] == "qa"
    assert state_payload["quality_review_required_stage_run_id"] == "stage-0010-qa"
    assert state_payload["stale_downstream_stages"] == []
    assert [item["stage_run_id"] for item in state_payload["completed_stage_runs"]][-3:] == [
        "stage-0008-implement",
        "stage-0009-review",
        "stage-0010-qa",
    ]


def test_black_box_live_product_evaluation_request_remediation_from_qa_starts_new_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    monkeypatch.setattr(
        live_orchestration,
        "_run_ui_remediation_job",
        _fake_remediation_ui_job,
    )
    qa_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="qa",
    )
    _write_stage_quality_audit(
        qa_checkpoint.bundle_root,
        stage="qa",
        flow_decision="request-remediation",
        remediation_request={
            "source_stage": "qa",
            "source_ids": ["risk-1"],
            "operator_note": "Fix QA risk.",
        },
    )

    remediated = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=qa_checkpoint.run_id,
    )

    state_payload = json.loads(
        (remediated.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert remediated.status == "awaiting-quality-review"
    assert state_payload["quality_review_required_stage"] == "implement"
    assert state_payload["quality_review_required_stage_run_id"] == "stage-0009-implement"
    assert state_payload["handled_quality_stage_run_ids"] == ["stage-0008-qa"]
    assert state_payload["stale_downstream_stages"] == ["review", "qa"]


def test_black_box_live_product_evaluation_invalid_remediation_audit_keeps_quality_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )
    review_checkpoint = _continue_product_evaluation_until_stage(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
        stage="review",
    )
    _write_stage_quality_audit(
        review_checkpoint.bundle_root,
        stage="review",
        flow_decision="request-remediation",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=review_checkpoint.run_id,
    )

    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert result.status == "awaiting-quality-review"
    assert state_payload["quality_review_required_stage"] == "review"
    assert "missing Source stage" in state_payload["quality_review_reason"]
    assert not (result.bundle_root / "stage-audits" / "stage-0008-implement.json").exists()


def test_black_box_live_e2e_implement_audit_surfaces_untracked_product_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        implement_untracked_product_file="src/utils/error.ts",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0006-implement.json").read_text(
            encoding="utf-8"
        )
    )
    implementation = audit_payload["implementation"]
    assert implementation["tracked_changed_files"] == ["feature.txt"]
    assert implementation["product_untracked_files"] == ["src/utils/error.ts"]
    assert implementation["harness_untracked_files"] == ["aidd.example.toml"]
    assert implementation["setup_baseline_untracked_files"] == ["setup.log"]
    assert audit_payload["implementation_policy"]["status"] == "pass"
    assert audit_payload["implementation_policy"]["findings"] == []
    assert audit_payload["implementation_policy"]["warnings"] == [
        "New untracked product files require manual code-quality review: "
        "src/utils/error.ts"
    ]
    audit_markdown = (
        result.bundle_root / "stage-audits" / "stage-0006-implement.md"
    ).read_text(encoding="utf-8")
    assert "### New Untracked Product Files" in audit_markdown
    assert "`src/utils/error.ts`" in audit_markdown
    assert "### Harness Or Config Untracked Files" in audit_markdown
    assert "`aidd.example.toml`" in audit_markdown
    assert "### Setup-Baseline Untracked Files" in audit_markdown
    assert "`setup.log`" in audit_markdown


def test_black_box_live_e2e_cli_prints_manual_quality_stop_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manual_stop_path = tmp_path / "bundle" / "manual-quality-stop.md"
    manual_stop_path.parent.mkdir(parents=True)
    manual_stop_path.write_text("# Manual Quality Stop\n", encoding="utf-8")
    result = BlackBoxLiveE2EResult(
        scenario_id="AIDD-TEST-LIVE-BLACKBOX",
        run_id="eval-live-test",
        runtime_id="opencode",
        status="manual-quality-stop",
        bundle_root=manual_stop_path.parent,
        flow_report_path=manual_stop_path.parent / "flow-report.md",
        verdict_path=manual_stop_path.parent / "verdict.md",
        summary_path=manual_stop_path.parent / "summary.md",
        first_failure_note="Manual stage quality audit chose `stop-not-counted`.",
        operator_action_request_path=None,
        quality_review_request_path=manual_stop_path.parent
        / "stage-quality-audits"
        / "idea.md",
        manual_quality_stop_path=manual_stop_path,
    )
    monkeypatch.setattr(
        live_orchestration,
        "run_black_box_live_e2e",
        lambda **_kwargs: result,
    )

    exit_code = live_orchestration.main(
        [
            "harness/scenarios/live/fake.yaml",
            "--runtime",
            "opencode",
        ]
    )

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "Manual quality stop:" in output
    assert manual_stop_path.as_posix() in output
    assert "Verdict path:" not in output


def test_black_box_live_product_evaluation_pass_after_all_stage_audits_lists_manual_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
    )

    result = _run_product_evaluation_to_terminal(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["status"] == "pass"
    assert state_payload["completed_stages"] == list(STAGES)
    assert "quality_review_required_stage" not in state_payload
    assert "quality_review_required_path" not in state_payload
    assert "quality_review_decision" not in state_payload
    assert "quality_review_reason" not in state_payload
    grader_payload = json.loads(
        (result.bundle_root / "grader.json").read_text(encoding="utf-8")
    )
    manual_artifacts = grader_payload["manual_quality_artifacts"]
    assert manual_artifacts["required_for_counted_clean"] is True
    assert [item["stage"] for item in manual_artifacts["stage_quality_audits"]] == list(
        STAGES
    )
    assert [item["stage_run_id"] for item in manual_artifacts["stage_quality_audits"]] == [
        f"stage-{index:04d}-{stage}"
        for index, stage in enumerate(STAGES, start=1)
    ]
    assert all(item["exists"] for item in manual_artifacts["stage_quality_audits"])
    assert [item["kind"] for item in manual_artifacts["final_reports"]] == [
        "flow-quality-report",
        "code-quality-report",
        "quality-report",
    ]
    assert all(not item["exists"] for item in manual_artifacts["final_reports"])


def test_black_box_live_product_evaluation_writes_navigation_bundle_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        product_evaluation=True,
        implement_untracked_product_file="src/untracked-helper.ts",
    )

    result = _run_product_evaluation_to_terminal(
        scenario_path=scenario_path,
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    summary_json = result.bundle_root / "product-evaluation-bundle-summary.json"
    summary_markdown = result.bundle_root / "product-evaluation-bundle-summary.md"
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    assert payload["scope"] == "navigation-evidence"
    assert payload["quality_scoring"] == {
        "runner_owned_quality_scoring": False,
        "summary_computes_counted_clean": False,
        "counted_clean_source": "manual quality-report.md only",
    }
    assert [
        item["flow_decision"] for item in payload["stage_quality_audits"]
    ] == ["continue"] * len(STAGES)
    assert all(item["exists"] for item in payload["stage_quality_audits"])
    assert payload["repair_counts"]["runner_stage_repair_attempts"] == 0
    assert payload["remediation"]["request_count"] == 0
    assert [item["kind"] for item in payload["final_reports"]] == [
        "flow-quality-report",
        "code-quality-report",
        "quality-report",
    ]
    assert all(not item["exists"] for item in payload["final_reports"])
    assert payload["target_workspace"]["tracked_product_files"] == ["feature.txt"]
    assert payload["target_workspace"]["untracked_product_files"] == [
        "src/untracked-helper.ts"
    ]
    assert payload["target_workspace"]["known_harness_files"] == ["aidd.example.toml"]
    assert payload["terminal_flow_state_verdict_consistency"]["consistent"] is True
    assert payload["terminal_flow_state_verdict_consistency"]["flow_state_status"] == "pass"
    assert payload["terminal_flow_state_verdict_consistency"]["verdict_status"] == "pass"

    verdict_text = (result.bundle_root / "verdict.md").read_text(encoding="utf-8")
    assert "- Status: `pass`" in verdict_text
    assert "counted-clean" not in verdict_text
    grader_payload = json.loads(
        (result.bundle_root / "grader.json").read_text(encoding="utf-8")
    )
    assert grader_payload["execution"]["status"] == "pass"
    serialized_grader = json.dumps(grader_payload)
    assert "counted-clean" not in serialized_grader
    assert "summary_computes_counted_clean" not in serialized_grader

    markdown = summary_markdown.read_text(encoding="utf-8")
    assert "not-runner-owned" in markdown
    assert "manual `quality-report.md` only" in markdown
    assert "`src/untracked-helper.ts`" in markdown


def test_black_box_live_e2e_compacts_setup_baseline_ignored_files_in_stage_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup_command = (
        "printf '.venv/\\n' > .gitignore; "
        "mkdir -p .venv; "
        "i=0; "
        "while [ $i -lt 80 ]; do "
        "printf x > .venv/file-$i.txt; "
        "i=$((i+1)); "
        "done"
    )
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        setup_commands=(setup_command,),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    target_repo_root = Path(state_payload["target_repo_root"])
    workspace_baseline_context = (
        target_repo_root
        / ".aidd"
        / "workitems"
        / "WI-LIVE-BLACKBOX"
        / "context"
        / "workspace-baseline.md"
    ).read_text(encoding="utf-8")
    assert "## Baseline Ignored Files" in workspace_baseline_context
    assert "- Count: `80`" in workspace_baseline_context
    assert "- Full list:" in workspace_baseline_context
    assert "final workspace evidence report after the run" in workspace_baseline_context
    assert "- Omitted path count: `55`" in workspace_baseline_context
    assert ".venv/file-0.txt" in workspace_baseline_context
    assert ".venv/file-79.txt" not in workspace_baseline_context
    assert len(workspace_baseline_context) < 20_000

    evidence_payload = json.loads(
        (result.bundle_root / "target-workspace-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    assert ".venv/file-79.txt" in evidence_payload["classification"][
        "baseline_ignored_files"
    ]


def test_black_box_live_e2e_records_non_gating_stage_result_validator_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        stage_result_validator_verdict="fail",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0001-idea.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["validator_verdict"] == "pass"
    assert audit_payload["consistency_findings"] == [
        {
            "kind": "stage-result-validator-verdict-mismatch",
            "severity": "warning",
            "non_gating": True,
            "stage_result_validator_verdict": "fail",
            "audit_validator_verdict": "pass",
            "message": (
                "stage-result.md declares a validator verdict that differs from "
                "the canonical stage-audit validator verdict."
            ),
        }
    ]
    audit_markdown = (
        result.bundle_root / "stage-audits" / "stage-0001-idea.md"
    ).read_text(encoding="utf-8")
    assert "## Consistency Findings" in audit_markdown
    assert "non-gating=True" in audit_markdown


def test_black_box_live_e2e_records_non_gating_stage_result_next_action_skip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        stage_result_direct_qa_next_action_stage="implement",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    expected_finding = {
        "kind": "stage-result-next-action-skips-canonical-stage",
        "severity": "warning",
        "non_gating": True,
        "stage": "implement",
        "expected_next_stage": "review",
        "mentioned_later_stages": ["qa"],
        "message": (
            "stage-result.md next actions mention a later downstream stage "
            "without naming the immediate canonical next stage."
        ),
    }
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0006-implement.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["stage_state"] == "passed"
    assert audit_payload["consistency_findings"] == [expected_finding]
    audit_markdown = (
        result.bundle_root / "stage-audits" / "stage-0006-implement.md"
    ).read_text(encoding="utf-8")
    assert "## Consistency Findings" in audit_markdown
    assert "`stage-result-next-action-skips-canonical-stage`" in audit_markdown
    assert "expected-next-stage=review" in audit_markdown
    assert "mentioned-later-stages=qa" in audit_markdown

    grader_payload = json.loads(
        (result.bundle_root / "grader.json").read_text(encoding="utf-8")
    )
    implement_audit = next(
        item
        for item in grader_payload["stage_audits"]
        if item["stage_run_id"] == "stage-0006-implement"
    )
    assert implement_audit["consistency_findings"] == [expected_finding]


def test_black_box_live_e2e_records_non_gating_stage_result_next_action_missing_exact_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        stage_result_generic_next_action_stage="research",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    expected_finding = {
        "kind": "stage-result-next-action-missing-immediate-stage",
        "severity": "warning",
        "non_gating": True,
        "stage": "research",
        "expected_next_stage": "plan",
        "message": (
            "stage-result.md next actions do not name the immediate canonical "
            "next stage."
        ),
    }
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0002-research.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["stage_state"] == "passed"
    assert audit_payload["consistency_findings"] == [expected_finding]
    audit_markdown = (
        result.bundle_root / "stage-audits" / "stage-0002-research.md"
    ).read_text(encoding="utf-8")
    assert "`stage-result-next-action-missing-immediate-stage`" in audit_markdown
    assert "expected-next-stage=plan" in audit_markdown


def test_black_box_live_e2e_records_non_gating_target_workspace_pollution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        stray_top_level_workitems_stage="qa",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    assert not (result.bundle_root / "quality-report.md").exists()
    evidence_payload = json.loads(
        (result.bundle_root / "target-workspace-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    stray_path = "workitems/WI-LIVE-BLACKBOX/stages/qa/stage-result.md"
    assert evidence_payload["classification"][
        "unexpected_top_level_workitems_files"
    ] == [stray_path]
    assert evidence_payload["classification"][
        "unexpected_non_aidd_untracked_files"
    ] == [stray_path]
    assert evidence_payload["non_gating_findings"] == [
        {
            "kind": "unexpected-top-level-workitems-artifact",
            "manual_quality_implication": (
                "Treat this as severe deliverable pollution; a clean manual "
                "deliverable decision should normally be `not-counted` unless the "
                "artifact is removed before final quality review."
            ),
            "message": (
                "A stage/control artifact was written under top-level `workitems/` "
                "instead of the canonical `.aidd/workitems/` workspace."
            ),
            "path": stray_path,
            "severity": "high",
        }
    ]
    evidence_markdown = (
        result.bundle_root / "target-workspace-evidence.md"
    ).read_text(encoding="utf-8")
    assert "Execution verdict impact: `none`" in evidence_markdown
    assert stray_path in evidence_markdown
    grader_payload = json.loads(
        (result.bundle_root / "grader.json").read_text(encoding="utf-8")
    )
    assert grader_payload["execution"]["status"] == "pass"
    serialized_grader = json.dumps(grader_payload)
    assert "quality_gate" not in serialized_grader
    assert "counting_status" not in serialized_grader


def test_black_box_live_e2e_records_non_gating_ignored_workspace_pollution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        setup_commands=(
            "printf '.venv/\\ncoverage/\\n.pdm-build/\\n.pytest_cache/\\n"
            "__pycache__/\\n*.pyc\\n' > .gitignore",
        ),
        ignored_pollution_stage="qa",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    evidence_payload = json.loads(
        (result.bundle_root / "target-workspace-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(
        evidence_payload["classification"]["unexpected_ignored_workspace_files"]
    ) == {
        ".venv/pyvenv.cfg",
        "coverage/index.html",
        ".pdm-build/wheel",
        ".pytest_cache/CACHEDIR.TAG",
        "package/__pycache__/module.pyc",
    }
    assert [
        finding["kind"] for finding in evidence_payload["non_gating_findings"]
    ] == [
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
    ]
    evidence_markdown = (
        result.bundle_root / "target-workspace-evidence.md"
    ).read_text(encoding="utf-8")
    assert "- New ignored files:" in evidence_markdown
    assert ".venv/pyvenv.cfg" in evidence_markdown
    grader_payload = json.loads(
        (result.bundle_root / "grader.json").read_text(encoding="utf-8")
    )
    assert grader_payload["execution"]["status"] == "pass"


def test_black_box_live_e2e_cleans_successful_verify_ignored_residue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        setup_commands=(
            "printf '.pytest_cache/\\n.ruff_cache/\\ncoverage/\\n"
            "__pycache__/\\n*.pyc\\n' > .gitignore",
        ),
        verify_commands=(
            "mkdir -p .pytest_cache .ruff_cache coverage package/__pycache__",
            "printf cache > .pytest_cache/CACHEDIR.TAG",
            "printf ruff > .ruff_cache/CACHEDIR.TAG",
            "printf cov > coverage/.coverage.verify",
            "printf pyc > package/__pycache__/module.pyc",
            "test -f .aidd/workitems/WI-LIVE-BLACKBOX/stages/qa/output/stage-result.md",
        ),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    verify_payload = json.loads(
        (result.bundle_root / "verify-transcript.json").read_text(encoding="utf-8")
    )
    cleanup = verify_payload["workspace_cleanup"]
    assert cleanup["scope"] == "post-verify-known-ignored-residue"
    assert cleanup["execution_verdict_impact"] == "none"
    assert cleanup["errors"] == []
    assert set(cleanup["removed_paths"]) == {
        ".pytest_cache",
        ".ruff_cache",
        "coverage",
        "package/__pycache__",
    }

    evidence_payload = json.loads(
        (result.bundle_root / "target-workspace-evidence.json").read_text(
            encoding="utf-8"
        )
    )
    assert evidence_payload["classification"]["unexpected_ignored_workspace_files"] == []
    assert evidence_payload["non_gating_findings"] == []
    target_root = Path(evidence_payload["target_repo_root"])
    assert not (target_root / ".pytest_cache").exists()
    assert not (target_root / ".ruff_cache").exists()
    assert not (target_root / "coverage").exists()
    assert not (target_root / "package" / "__pycache__").exists()

    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    verify_step = next(step for step in steps if step["action"] == "verify")
    assert verify_step["classification"] == "pass"
    assert verify_step["details"]["workspace_cleanup"]["removed_paths"]


def test_black_box_live_e2e_preserves_manual_quality_report_without_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    manual_report = result.bundle_root / "quality-report.md"
    manual_report_text = "\n".join(
        (
            "# Live E2E Quality Report",
            "",
            "## Decision",
            "- Run integrity decision: clean",
            "- Deliverable quality decision: counted-clean",
            "- Overall decision: counted-clean",
            "",
            "## Notes",
            "- This report is intentionally human-authored and must not be parsed.",
            "- machine_quality_gate: fail",
            "",
        )
    )
    manual_report.write_text(manual_report_text, encoding="utf-8")

    refreshed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=result.run_id,
    )

    assert refreshed.status == "pass"
    assert manual_report.read_text(encoding="utf-8") == manual_report_text
    grader_payload = json.loads((refreshed.bundle_root / "grader.json").read_text())
    serialized_grader = json.dumps(grader_payload)
    assert "quality" not in grader_payload
    assert "counted-clean" not in serialized_grader
    assert "machine_quality_gate" not in serialized_grader


def test_black_box_live_e2e_follow_up_proof_is_explicit_manual_only_lineage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        enable_next_flow_follow_up_proof=True,
    )

    lineage_path = result.bundle_root / "next-flow-lineage.json"
    assert lineage_path.exists()
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    assert lineage["enabled"] is True
    assert lineage["manual_only"] is True
    assert lineage["automation_lane"] == "manual"
    assert lineage["launched_child_flow"] is False
    assert lineage["source_run_id"] == result.run_id
    assert lineage["source_work_item_id"] == "WI-LIVE-BLACKBOX"
    assert lineage["child_work_item_id"].startswith("WI-LIVE-BLACKBOX-FOLLOW-UP-")
    assert lineage["child_work_item_lineage"] == {
        "source_run_id": result.run_id,
        "source_work_item_id": "WI-LIVE-BLACKBOX",
    }
    assert lineage["source_artifact_paths"] == [
        "workitems/WI-LIVE-BLACKBOX/stages/qa/output/qa-report.md"
    ]
    follow_up_request = Path(lineage["follow_up_request_path"])
    assert follow_up_request.exists()
    assert f"Source run: `{result.run_id}`" in follow_up_request.read_text(
        encoding="utf-8"
    )
    checkpoint = json.loads(
        (result.bundle_root / "next-flow-checkpoint.json").read_text(encoding="utf-8")
    )
    optional_lineage = checkpoint["optional_lineage_metadata"]
    assert optional_lineage["child_flow_enabled"] is True
    assert optional_lineage["child_flow_required"] is False
    assert optional_lineage["child_work_item_id"] == lineage["child_work_item_id"]
    assert optional_lineage["lineage_artifact"] == lineage_path.as_posix()


def test_black_box_live_e2e_blocks_for_questions_and_continues_after_answers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        block_stage="idea",
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert first.status == "blocked"
    first_grader = json.loads((first.bundle_root / "grader.json").read_text(encoding="utf-8"))
    assert first_grader["steps"][-1]["action"] == "stop"
    first_next_flow = json.loads(
        (first.bundle_root / "next-flow-checkpoint.json").read_text(encoding="utf-8")
    )
    assert first_next_flow["terminal_status"] == "blocked"
    assert first_next_flow["flow_complete_visible"] is False
    assert first_next_flow["next_flow_actions"]["operator_decision"]["decision"] == "blocked"
    assert first_next_flow["source_run_summary"]["questions"]["total_count"] == 1
    assert first_next_flow["source_run_summary"]["questions"]["answered_count"] == 0
    request_markdown = (first.bundle_root / "operator-action-request.md").read_text(
        encoding="utf-8"
    )
    assert "launching operator-agent" in request_markdown
    assert "`- Q1 [resolved] answer text`" in request_markdown
    request_payload = json.loads(
        (first.bundle_root / "operator-action-request.json").read_text(encoding="utf-8")
    )
    answers_path = Path(request_payload["answers_path"])
    answers_path.write_text(
        "# Answers\n\n- Q1 [resolved] Implement the behavior described by the task.\n",
        encoding="utf-8",
    )
    manifest_payload = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    manifest_payload["feature_source"]["tasks"][0][
        "title"
    ] = "mutated title that must not replace the selected task snapshot"
    scenario_path.write_text(yaml.safe_dump(manifest_payload, sort_keys=False), encoding="utf-8")

    resumed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert resumed.status == "pass"
    assert resumed.run_id == first.run_id
    assert (resumed.bundle_root / "answer-analysis.md").exists()
    state_payload = json.loads(
        (resumed.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    metadata_payload = json.loads(
        (resumed.bundle_root / "harness-metadata.json").read_text(encoding="utf-8")
    )
    assert state_payload["install"]["artifact_identity"] == "ai_driven_dev_v2-test.whl"
    assert metadata_payload["aidd_install"]["artifact_identity"] == "ai_driven_dev_v2-test.whl"
    steps = json.loads((resumed.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    assert any(
        step["action"] == "answer-questions" and step["classification"] == "pass"
        for step in steps
    )
    resumed_grader = json.loads((resumed.bundle_root / "grader.json").read_text(encoding="utf-8"))
    assert resumed_grader["steps"][-1]["action"] == "finish"
    assert resumed_grader["execution"]["first_failure_note"] is None
    resumed_next_flow = json.loads(
        (resumed.bundle_root / "next-flow-checkpoint.json").read_text(encoding="utf-8")
    )
    assert resumed_next_flow["terminal_status"] == "pass"
    assert resumed_next_flow["source_run_summary"]["questions"]["answered_count"] == 1
    assert resumed_grader["selected_task"]["title"] == "exercise live black-box evaluator"
    assert "First Failure Boundary: `none`" in (
        resumed.bundle_root / "log-analysis.md"
    ).read_text(encoding="utf-8")
    assert "- none" in (resumed.bundle_root / "validator-report.md").read_text(
        encoding="utf-8"
    )


def test_black_box_live_e2e_does_not_resume_blocked_run_without_run_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        block_stage="idea",
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    second = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert first.status == "blocked"
    assert second.status == "blocked"
    assert second.run_id != first.run_id
    assert second.bundle_root != first.bundle_root


def test_black_box_live_e2e_adds_suffix_when_generated_run_id_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box.derive_run_id",
        lambda *, scenario_id, runtime_id: "fixed-live-run",
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    second = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert first.run_id == "fixed-live-run"
    assert second.run_id == "fixed-live-run-r2"
    assert first.status == "pass"
    assert second.status == "pass"


def test_black_box_live_e2e_marks_stale_running_run_resumable(tmp_path: Path) -> None:
    report_root = tmp_path / "reports"
    state_path = report_root / "stale-run" / "flow-state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "running",
                "next_action": "run-stage",
                "current_stage": "plan",
                "completed_stages": ["idea", "research"],
                "evaluator_pid": 99999999,
            }
        ),
        encoding="utf-8",
    )

    assert _find_resume_state(report_root=report_root, run_id="stale-run") == state_path

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload["status"] == "interrupted-resumable"
    assert payload["interruption"]["reason"] == "stale-running-state"


def test_black_box_command_timeout_kills_child_process_group(tmp_path: Path) -> None:
    child_pid_path = tmp_path / "child.pid"
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib, subprocess, time; "
            f"path=pathlib.Path({str(child_pid_path)!r}); "
            "child=subprocess.Popen(['sleep', '30']); "
            "path.write_text(str(child.pid), encoding='utf-8'); "
            "time.sleep(30)"
        ),
    )

    result = _run_black_box_command(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=2.0,
    )

    assert result.exit_code == 124
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))
    for _ in range(20):
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:
        pytest.fail(f"child process {child_pid} survived command group timeout cleanup")


def test_black_box_command_no_progress_stops_live_process(tmp_path: Path) -> None:
    progress_file = tmp_path / "placeholder.txt"
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib, time; "
            f"path=pathlib.Path({str(progress_file)!r}); "
            "path.write_text('started\\n', encoding='utf-8'); "
            "print('provider started', flush=True); "
            "time.sleep(5)"
        ),
    )

    def _probe() -> dict[str, object]:
        if not progress_file.exists():
            return {"exists": False}
        stat = progress_file.stat()
        return {"exists": True, "mtime_ns": stat.st_mtime_ns, "size": stat.st_size}

    result = _run_black_box_command(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=5.0,
        no_progress_timeout_seconds=1.0,
        progress_probe=_probe,
    )

    assert result.exit_code == 125
    assert result.transcript.timed_out is False
    assert result.no_progress is True
    assert result.no_progress_details is not None
    assert result.no_progress_details["reason"] == "provider-no-progress"
    assert "provider-no-progress before completed stage artifact" in str(
        result.no_progress_details["message"]
    )
    assert "provider started" in result.no_progress_details["stdout_tail"]


def test_black_box_command_no_progress_allows_live_artifact_heartbeats(
    tmp_path: Path,
) -> None:
    progress_file = tmp_path / "progress.txt"
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib, time; "
            f"path=pathlib.Path({str(progress_file)!r}); "
            "\nfor index in range(5):\n"
            "    path.write_text(str(index), encoding='utf-8')\n"
            "    time.sleep(0.1)\n"
        ),
    )

    def _probe() -> dict[str, object]:
        if not progress_file.exists():
            return {"exists": False}
        stat = progress_file.stat()
        return {"exists": True, "mtime_ns": stat.st_mtime_ns, "size": stat.st_size}

    result = _run_black_box_command(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=5.0,
        no_progress_timeout_seconds=1.0,
        progress_probe=_probe,
    )

    assert result.exit_code == 0
    assert result.no_progress is False
    assert result.transcript.timed_out is False


def test_black_box_command_emits_operator_heartbeat_without_polluting_transcript(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime_log_path = tmp_path / "runtime.log"
    command = (
        sys.executable,
        "-c",
        "import time; time.sleep(0.35)",
    )

    result = _run_black_box_command(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=5.0,
        no_progress_timeout_seconds=3.0,
        heartbeat_label="run-stage `idea`",
        heartbeat_interval_seconds=0.1,
        heartbeat_runtime_log_path=runtime_log_path,
    )

    captured = capsys.readouterr()
    assert result.exit_code == 0
    assert result.stdout_text == ""
    assert result.stderr_text == ""
    assert captured.out == ""
    assert "[aidd live] run-stage `idea` still running after" in captured.err
    assert "last signal: process-started" in captured.err
    assert "hard timeout: 5s" in captured.err
    assert "no-progress timeout: 3s" in captured.err
    assert (
        f"runtime log: {runtime_log_path.as_posix()} "
        "(waiting for first runtime event)" in captured.err
    )
    assert (
        "next evidence: stage command is alive; "
        "waiting for runtime output or file activity" in captured.err
    )


def test_black_box_command_heartbeat_explains_file_activity_before_runtime_log(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runtime_log_path = tmp_path / "runtime.log"
    progress_file = tmp_path / "progress.txt"
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib, time\n"
            "path = pathlib.Path('progress.txt')\n"
            "for index in range(4):\n"
            "    path.write_text(str(index), encoding='utf-8')\n"
            "    time.sleep(0.08)\n"
        ),
    )

    def _probe() -> dict[str, object]:
        if not progress_file.exists():
            return {"exists": False}
        stat = progress_file.stat()
        return {"exists": True, "mtime_ns": stat.st_mtime_ns, "size": stat.st_size}

    result = _run_black_box_command(
        command=command,
        cwd=tmp_path,
        environment=dict(os.environ),
        timeout_seconds=5.0,
        no_progress_timeout_seconds=3.0,
        progress_probe=_probe,
        heartbeat_label="run-stage `qa`",
        heartbeat_interval_seconds=0.1,
        heartbeat_runtime_log_path=runtime_log_path,
    )

    captured = capsys.readouterr()
    assert result.exit_code == 0
    assert result.stdout_text == ""
    assert result.stderr_text == ""
    assert "last signal: watched-files" in captured.err
    assert (
        "next evidence: stage files changed before first runtime event; "
        "inspect artifacts or wait" in captured.err
    )


def test_black_box_live_e2e_records_active_step_while_stage_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        timeout_stage="idea",
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._stage_command_timeout_seconds",
        lambda scenario: 2.0,
    )
    original_run_black_box_command = _run_black_box_command
    stage_command_started = threading.Event()
    release_stage_command = threading.Event()

    def _run_black_box_command_with_stage_barrier(*args: object, **kwargs: object):
        command = kwargs.get("command")
        if command is None and args:
            command = args[0]
        if isinstance(command, tuple | list):
            command_parts = list(command)
            if (
                len(command_parts) >= 3
                and command_parts[1:3] == ["stage", "run"]
                and "idea" in command_parts
            ):
                stage_command_started.set()
                release_stage_command.wait(timeout=5.0)
        return original_run_black_box_command(*args, **kwargs)

    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._run_black_box_command",
        _run_black_box_command_with_stage_barrier,
    )
    result_box: list[object] = []
    errors: list[BaseException] = []

    def _target() -> None:
        try:
            result_box.append(
                run_black_box_live_e2e(
                    scenario_path=scenario_path,
                    runtime_id="opencode",
                    work_root=work_root,
                    report_root=report_root,
                )
            )
        except BaseException as exc:  # pragma: no cover - surfaced by assertion below
            errors.append(exc)

    thread = threading.Thread(target=_target)
    thread.start()

    active_step: dict[str, object] | None = None
    assert stage_command_started.wait(timeout=15.0)
    for _ in range(20):
        state_paths = sorted(report_root.glob("*/flow-state.json"))
        if state_paths:
            state_path = state_paths[0]
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            raw_active_step = payload.get("active_step")
            if isinstance(raw_active_step, dict):
                active_step = raw_active_step
                break
        time.sleep(0.05)
    release_stage_command.set()

    thread.join(timeout=10.0)

    assert not thread.is_alive()
    assert errors == []
    assert result_box
    assert active_step is not None
    assert active_step["action"] == "run-stage"
    assert active_step["stage"] == "idea"
    assert active_step["timeout_seconds"] == 2.0
    assert active_step["no_progress_timeout_seconds"] == 1800.0
    command = active_step["command"]
    assert isinstance(command, list)
    assert command[1:3] == ["stage", "run"]


def test_live_interruption_handlers_are_noop_outside_main_thread() -> None:
    errors: list[BaseException] = []

    def _target() -> None:
        try:
            with _live_interruption_handlers():
                pass
        except BaseException as exc:  # pragma: no cover - surfaced by assertion below
            errors.append(exc)

    thread = threading.Thread(target=_target)
    thread.start()
    thread.join(timeout=2.0)

    assert not thread.is_alive()
    assert errors == []


def test_black_box_live_e2e_interruption_rewrites_flow_report_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)
    original_run_black_box_command = live_orchestration._run_black_box_command

    def _interrupt_idea_stage(*args: object, **kwargs: object) -> BlackBoxCommandResult:
        command = kwargs.get("command")
        if isinstance(command, tuple) and command[1:4] == ("stage", "run", "idea"):
            raw_timeout_seconds = kwargs.get("timeout_seconds")
            transcript = HarnessCommandTranscript(
                command=" ".join(command),
                exit_code=130,
                stdout_text="stage started\n",
                stderr_text="",
                duration_seconds=0.1,
                timed_out=False,
                timeout_seconds=(
                    float(raw_timeout_seconds)
                    if isinstance(raw_timeout_seconds, int | float)
                    else None
                ),
            )
            raise LiveE2EInterrupted(
                "Synthetic test interruption.",
                signum=2,
                command_result=BlackBoxCommandResult(
                    command=command,
                    transcript=transcript,
                ),
                cleanup={"signal": 2},
            )
        return original_run_black_box_command(*args, **kwargs)

    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._run_black_box_command",
        _interrupt_idea_stage,
    )

    with pytest.raises(LiveE2EInterrupted):
        run_black_box_live_e2e(
            scenario_path=scenario_path,
            runtime_id="opencode",
            work_root=work_root,
            report_root=report_root,
        )

    state_paths = list(report_root.glob("*/flow-state.json"))
    assert len(state_paths) == 1
    state_payload = json.loads(state_paths[0].read_text(encoding="utf-8"))
    assert state_payload["status"] == "interrupted-resumable"
    flow_report = (state_paths[0].parent / "flow-report.md").read_text(encoding="utf-8")
    assert "- Status: `interrupted-resumable`" in flow_report


def test_black_box_live_e2e_defers_repeated_interrupt_while_recording_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)
    original_run_black_box_command = live_orchestration._run_black_box_command
    original_write_steps = live_orchestration._write_steps
    second_interrupt_seen = False

    def _interrupt_idea_stage(*args: object, **kwargs: object) -> BlackBoxCommandResult:
        command = kwargs.get("command")
        if isinstance(command, tuple) and command[1:4] == ("stage", "run", "idea"):
            transcript = HarnessCommandTranscript(
                command=" ".join(command),
                exit_code=130,
                stdout_text="stage started\n",
                stderr_text="",
                duration_seconds=0.1,
                timed_out=False,
                timeout_seconds=None,
            )
            raise LiveE2EInterrupted(
                "Synthetic test interruption.",
                signum=2,
                command_result=BlackBoxCommandResult(
                    command=command,
                    transcript=transcript,
                ),
                cleanup={"signal": 2},
            )
        return original_run_black_box_command(*args, **kwargs)

    def _write_steps_with_repeated_interrupt(
        bundle_root: Path,
        steps: list[dict[str, object]],
    ) -> None:
        nonlocal second_interrupt_seen
        latest = steps[-1] if steps else {}
        if (
            not second_interrupt_seen
            and latest.get("action") == "stop"
            and latest.get("classification") == "infra-fail"
        ):
            second_interrupt_seen = True
            signal.raise_signal(signal.SIGINT)
        original_write_steps(bundle_root, steps)

    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._run_black_box_command",
        _interrupt_idea_stage,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._write_steps",
        _write_steps_with_repeated_interrupt,
    )

    with pytest.raises(LiveE2EInterrupted):
        run_black_box_live_e2e(
            scenario_path=scenario_path,
            runtime_id="opencode",
            work_root=work_root,
            report_root=report_root,
        )

    assert second_interrupt_seen
    state_paths = list(report_root.glob("*/flow-state.json"))
    assert len(state_paths) == 1
    bundle_root = state_paths[0].parent
    state_payload = json.loads(state_paths[0].read_text(encoding="utf-8"))
    steps_payload = json.loads((bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    flow_report = (bundle_root / "flow-report.md").read_text(encoding="utf-8")
    assert state_payload["status"] == "interrupted-resumable"
    assert steps_payload[-1]["action"] == "stop"
    assert steps_payload[-1]["classification"] == "infra-fail"
    assert "- Status: `interrupted-resumable`" in flow_report


def test_black_box_live_e2e_fails_required_interview_without_blocked_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        interview_required=True,
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    assert result.first_failure_note is not None
    assert "Required interview flow was not observed" in result.first_failure_note
    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    assert any(
        step["action"] == "verify"
        and step["classification"] == "fail"
        and "blocking question stop" in step["decision"]
        for step in steps
    )
    assert "Required interview flow was not observed" in (
        result.bundle_root / "validator-report.md"
    ).read_text(encoding="utf-8")


def test_black_box_live_e2e_blocks_for_questions_found_by_public_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        inspect_block_stage="idea",
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert first.status == "blocked"
    request_payload = json.loads(
        (first.bundle_root / "operator-action-request.json").read_text(encoding="utf-8")
    )
    assert request_payload["stage"] == "idea"
    answers_path = Path(request_payload["answers_path"])
    answers_path.write_text(
        "# Answers\n\n- Q1 [resolved] Implement the behavior described by the task.\n",
        encoding="utf-8",
    )

    resumed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert resumed.status == "pass"
    steps = json.loads((resumed.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    assert any(
        step["action"] == "inspect-stage"
        and step["stage"] == "idea"
        and step["classification"] == "blocked"
        for step in steps
    )
    assert any(
        step["action"] == "answer-questions" and step["classification"] == "pass"
        for step in steps
    )


def test_black_box_live_e2e_reports_first_unresolved_signal_after_resolved_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        block_stage="idea",
        fail_stage="plan",
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    request_payload = json.loads(
        (first.bundle_root / "operator-action-request.json").read_text(encoding="utf-8")
    )
    Path(request_payload["answers_path"]).write_text(
        "# Answers\n\n- Q1 [resolved] Implement the behavior described by the task.\n",
        encoding="utf-8",
    )

    resumed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert resumed.status == "fail"
    assert resumed.first_failure_note is not None
    assert "plan" in resumed.first_failure_note
    assert "idea" not in resumed.first_failure_note
    assert "run-stage stage `plan`" in (
        resumed.bundle_root / "log-analysis.md"
    ).read_text(encoding="utf-8")


def test_black_box_live_e2e_does_not_reblock_on_historical_log_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        log_blocking_text=True,
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    assert all(
        not (step["action"] == "inspect-stage" and step["classification"] == "blocked")
        for step in steps
    )


def test_black_box_live_e2e_reports_stage_failure_from_step_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        fail_stage="plan",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    assert result.first_failure_note is not None
    assert "plan" in result.first_failure_note
    assert "run-stage" in (result.bundle_root / "log-analysis.md").read_text(encoding="utf-8")
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0003-plan.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["stage_state"] == "failed"
    assert audit_payload["validator_verdict"] == "fail"
    assert audit_payload["primary_artifact"]["present"] is True
    assert "/output/" not in audit_payload["primary_artifact"]["path"]


def test_black_box_live_e2e_reconciles_timed_out_stage_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        timeout_stage="idea",
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._stage_command_timeout_seconds",
        lambda scenario: 2.0,
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    target_workspace_root = Path(state_payload["target_workspace_root"])
    metadata_path = (
        target_workspace_root
        / "reports"
        / "runs"
        / "WI-LIVE-BLACKBOX"
        / result.run_id
        / "stages"
        / "idea"
        / "stage-metadata.json"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert [entry["status"] for entry in metadata["status_history"]] == [
        "executing",
        "failed",
    ]
    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    timeout_step = next(
        step
        for step in steps
        if step["action"] == "run-stage" and step["stage"] == "idea"
    )
    assert timeout_step["commands"][0]["timed_out"] is True
    assert timeout_step["commands"][0]["timeout_seconds"] == 2.0
    assert timeout_step["details"]["timeout_reconciliation"]["previous_status"] == "executing"
    assert timeout_step["details"]["timeout_reconciliation"]["reconciled_status"] == "failed"
    assert timeout_step["evidence_paths"]
    reconciliation_path = Path(timeout_step["evidence_paths"][0])
    assert reconciliation_path.exists()
    reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    assert reconciliation["reconciled"] is True
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0001-idea.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["stage_state"] == "failed"
    assert audit_payload["stage_metadata_status"] == "failed"
    assert audit_payload["classifications"]["frontend_checkpoint"] == "skipped"
    run_transcript = json.loads(
        (result.bundle_root / "run-transcript.json").read_text(encoding="utf-8")
    )
    assert run_transcript["timed_out"] is True
    assert run_transcript["timeout_seconds"] is None
    assert run_transcript["timeout_policy"]["stage_command_timeout_seconds"] == 2.0
    assert run_transcript["timeout_policy"]["no_progress_timeout_seconds"] == 1800.0
    stage_timing = json.loads(
        (result.bundle_root / "stage-timing.json").read_text(encoding="utf-8")
    )
    run_stage_step = next(
        step
        for step in stage_timing["steps"]
        if step["step"] == "run-stage" and step["stage"] == "idea"
    )
    assert run_stage_step["timed_out"] is True
    assert run_stage_step["timeout_seconds"] == 2.0


def test_black_box_live_e2e_marks_provider_no_progress_as_infra_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        no_progress_stage="idea",
        product_evaluation=True,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._stage_command_timeout_seconds",
        lambda scenario: 5.0,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box_orchestration._stage_no_progress_timeout_seconds",
        lambda scenario: 1.0,
    )
    manual_evidence = tmp_path / "provider-no-progress-browser-evidence"
    manual_evidence.mkdir()
    (manual_evidence / "browser-notes.md").write_text(
        "# Browser Notes\n\n"
        "- Desktop UI showed the failed idea stage after provider no-progress.\n"
        "- Runtime logs and artifact surfaces stayed reachable for triage.\n",
        encoding="utf-8",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        manual_frontend_evidence=manual_evidence,
    )

    assert result.status == "infra-fail"
    assert not (result.bundle_root / "stage-quality-audits").exists()
    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["status"] == "infra-fail"
    assert state_payload["error"] == "provider-no-progress before completed stage artifact"
    target_workspace_root = Path(state_payload["target_workspace_root"])
    metadata_path = (
        target_workspace_root
        / "reports"
        / "runs"
        / "WI-LIVE-BLACKBOX"
        / result.run_id
        / "stages"
        / "idea"
        / "stage-metadata.json"
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert [entry["status"] for entry in metadata["status_history"]] == [
        "executing",
        "failed",
    ]

    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    no_progress_step = next(
        step
        for step in steps
        if step["action"] == "run-stage" and step["stage"] == "idea"
    )
    assert no_progress_step["classification"] == "infra-fail"
    assert no_progress_step["commands"][0]["timed_out"] is False
    assert no_progress_step["commands"][0]["no_progress"] is True
    assert no_progress_step["commands"][0]["timeout_seconds"] == 5.0
    no_progress_details = no_progress_step["commands"][0]["no_progress_details"]
    assert no_progress_details["reason"] == "provider-no-progress"
    assert no_progress_details["no_progress_timeout_seconds"] == 1.0
    assert "observed_paths" in no_progress_details["observed_files"]
    assert no_progress_step["details"]["no_progress_reconciliation"]["previous_status"] == (
        "executing"
    )
    assert no_progress_step["details"]["no_progress_reconciliation"][
        "reconciled_status"
    ] == "failed"
    assert no_progress_step["evidence_paths"]
    reconciliation_path = Path(no_progress_step["evidence_paths"][0])
    assert reconciliation_path.exists()
    reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    assert reconciliation["reason"] == "provider-no-progress"
    assert reconciliation["reconciled"] is True

    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "stage-0001-idea.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_payload["classifications"]["stage_run"] == "infra-fail"
    assert audit_payload["classifications"]["frontend_checkpoint"] == "pass"

    frontend_payload = json.loads(
        (result.bundle_root / "frontend-checkpoints.json").read_text(encoding="utf-8")
    )
    no_progress_post_stage = [
        checkpoint
        for checkpoint in frontend_payload["checkpoints"]
        if checkpoint["stage"] == "idea" and checkpoint["phase"] == "post-stage"
    ]
    assert no_progress_post_stage
    assert no_progress_post_stage[-1]["classification"] == "pass"
    frontend_markdown = (result.bundle_root / "frontend-checkpoints.md").read_text(
        encoding="utf-8"
    )
    assert "## idea / post-stage" in frontend_markdown
    assert "- Phase: `post-stage`" in frontend_markdown
    manual_payload = frontend_payload["manual_visual_evidence"]
    imported_root = result.bundle_root / "manual-frontend-evidence"
    assert manual_payload["status"] == "imported"
    assert manual_payload["non_gating"] is True
    assert manual_payload["files"] == ["browser-notes.md"]
    assert manual_payload["bundle_path"] == imported_root.as_posix()
    assert (imported_root / "browser-notes.md").read_text(
        encoding="utf-8"
    ).startswith("# Browser Notes")
    assert "## Manual Browser Evidence" in frontend_markdown
    assert "`browser-notes.md`" in frontend_markdown

    run_transcript = json.loads(
        (result.bundle_root / "run-transcript.json").read_text(encoding="utf-8")
    )
    assert run_transcript["timed_out"] is False
    assert run_transcript["timeout_policy"]["stage_command_timeout_seconds"] == 5.0
    assert run_transcript["timeout_policy"]["no_progress_timeout_seconds"] == 1.0

    stage_timing = json.loads(
        (result.bundle_root / "stage-timing.json").read_text(encoding="utf-8")
    )
    run_stage_step = next(
        step
        for step in stage_timing["steps"]
        if step["step"] == "run-stage" and step["stage"] == "idea"
    )
    assert run_stage_step["timed_out"] is False
    assert run_stage_step["no_progress"] is True
    assert run_stage_step["no_progress_timeout_seconds"] == 1.0

    log_analysis = (result.bundle_root / "log-analysis.md").read_text(encoding="utf-8")
    assert "provider-no-progress before completed stage artifact" in log_analysis
    assert "- No-Progress Timeout: `1.000s`" in log_analysis

    state_payload = json.loads(
        (result.bundle_root / "flow-state.json").read_text(encoding="utf-8")
    )
    assert state_payload["manual_frontend_evidence_source"] == (
        manual_evidence.resolve().as_posix()
    )
    metadata_payload = json.loads(
        (result.bundle_root / "harness-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["black_box"]["manual_frontend_evidence"] == (
        imported_root.as_posix()
    )


def test_black_box_live_e2e_marks_adapter_timeout_in_run_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        adapter_timeout_stage="review",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    timeout_step = next(
        step
        for step in steps
        if step["action"] == "run-stage" and step["stage"] == "review"
    )
    assert timeout_step["classification"] == "fail"
    assert timeout_step["commands"][0]["timed_out"] is False
    assert timeout_step["commands"][0]["timeout_seconds"] == 14400.0
    assert "Adapter outcome: timeout" in timeout_step["commands"][0]["stdout_text"]

    run_transcript = json.loads(
        (result.bundle_root / "run-transcript.json").read_text(encoding="utf-8")
    )
    assert run_transcript["timed_out"] is True
    assert run_transcript["timeout_seconds"] is None
    assert run_transcript["timeout_policy"] == {
        "global_flow_timeout_seconds": None,
        "no_progress_timeout_seconds": 1800.0,
        "runtime_config_source": "aidd.example.toml",
        "scope": "per-stage-command",
        "stage_command_timeout_seconds": 14400.0,
    }
    assert run_transcript["commands"][0]["timed_out"] is True

    stage_timing = json.loads(
        (result.bundle_root / "stage-timing.json").read_text(encoding="utf-8")
    )
    review_stage = next(
        stage for stage in stage_timing["stages"] if stage["stage"] == "review"
    )
    assert review_stage["attempts"][0]["timed_out"] is True
    assert review_stage["attempts"][0]["runtime_exit_classification"] == "timeout"


def test_implementation_verification_evidence_shape_uses_validator_patterns() -> None:
    shape = _implementation_verification_evidence_shape(
        "# Implementation Report\n\n"
        "## Touched files\n\n"
        "- `src/router/common.case.test.ts` - add parity tests.\n\n"
        "## Verification\n\n"
        "- `npx vitest run src/router/ src/utils/url.test.ts` -> "
        "8 test files passed, 561 tests passed, 20 skipped.\n"
        "- `npx tsc --noEmit --project tsconfig.spec.json` -> 0 type errors.\n"
    )

    assert shape == {
        "backed_evidence_line_count": 2,
        "outcome_claim_line_count": 2,
        "has_executable_or_not_run_evidence": True,
    }


def test_black_box_live_e2e_stops_when_public_inspection_fails_after_stage_pass(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        inspect_fail_command="run logs",
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    assert result.first_failure_note is not None
    assert "inspect-stage stage `idea`" in result.first_failure_note
    steps = json.loads((result.bundle_root / "flow-steps.json").read_text(encoding="utf-8"))
    inspect_steps = [step for step in steps if step["action"] == "inspect-stage"]
    assert inspect_steps[0]["classification"] == "fail"
    assert "public inspection failed" in (
        result.bundle_root / "flow-state.json"
    ).read_text(encoding="utf-8")
    next_flow_payload = json.loads(
        (result.bundle_root / "next-flow-checkpoint.json").read_text(encoding="utf-8")
    )
    assert next_flow_payload["terminal_status"] == "fail"
    assert next_flow_payload["flow_complete_visible"] is False
    assert next_flow_payload["next_flow_actions"]["operator_decision"]["decision"] == "blocked"
    assert next_flow_payload["source_run_summary"]["blockers"]
    assert "Default decision: `blocked`" in (
        result.bundle_root / "next-flow-checkpoint.md"
    ).read_text(encoding="utf-8")


def test_black_box_live_e2e_reports_setup_infra_failure_and_partial_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        setup_commands=("printf 'setup failed\\n'; exit 3",),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "infra-fail"
    assert (result.bundle_root / "setup-transcript.json").exists()
    setup_payload = json.loads(
        (result.bundle_root / "setup-transcript.json").read_text(encoding="utf-8")
    )
    assert setup_payload["commands"][0]["exit_code"] == 3
    assert (result.bundle_root / "flow-state.json").exists()


def test_black_box_live_e2e_reports_install_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)

    def _fail_install(*, work_root: Path, run_id: str, repository_root: Path | None) -> None:
        _ = work_root, run_id, repository_root
        raise RuntimeError("install failed")

    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box.prepare_local_wheel_install",
        _fail_install,
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    assert "install failed" in (result.bundle_root / "verdict.md").read_text(encoding="utf-8")
