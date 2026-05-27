from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from aidd.core.stages import STAGES
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.live_e2e_black_box import (
    _harness_environment,
    _implementation_verification_evidence_shape,
    run_black_box_live_e2e,
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
    monkeypatch.delenv("AIDD_EVAL_GENERIC_CLI_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_OPENCODE_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_QWEN_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_LIVE_E2E_RUN_ID", raising=False)
    monkeypatch.delenv("AIDD_EVAL_PUBLISHED_PACKAGE_SPEC", raising=False)


def _write_fake_aidd(
    path: Path,
    *,
    fail_stage: str | None = None,
    timeout_stage: str | None = None,
    block_stage: str | None = None,
    ui_operator_request_stage: str | None = None,
    ui_operator_request_command: str = "pwd",
    internal_operator_decision_stage: str | None = None,
    inspect_block_stage: str | None = None,
    inspect_fail_command: str | None = None,
    log_blocking_text: bool = False,
) -> None:
    path.write_text(
        f"""#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PRIMARY_OUTPUTS = {json.dumps(_PRIMARY_OUTPUTS)}
FAIL_STAGE = {fail_stage!r}
TIMEOUT_STAGE = {timeout_stage!r}
BLOCK_STAGE = {block_stage!r}
UI_OPERATOR_REQUEST_STAGE = {ui_operator_request_stage!r}
UI_OPERATOR_REQUEST_COMMAND = {ui_operator_request_command!r}
INTERNAL_OPERATOR_DECISION_STAGE = {internal_operator_decision_stage!r}
INSPECT_BLOCK_STAGE = {inspect_block_stage!r}
INSPECT_FAIL_COMMAND = {inspect_fail_command!r}
LOG_BLOCKING_TEXT = {log_blocking_text!r}


def option(args: list[str], name: str, default: str = "") -> str:
    if name not in args:
        return default
    index = args.index(name)
    if index + 1 >= len(args):
        return default
    return args[index + 1]


def write_stage_outputs(stage: str, work_item: str, run_id: str) -> None:
    output_root = Path(".aidd") / "workitems" / work_item / "stages" / stage / "output"
    output_root.mkdir(parents=True, exist_ok=True)
    root = output_root.parent
    if not (root / "questions.md").exists():
        (root / "questions.md").write_text(
            "# Questions\\n\\nNo blocking or non-blocking questions remain.\\n"
        )
    if not (root / "answers.md").exists():
        (root / "answers.md").write_text("# Answers\\n\\nNo questions were raised.\\n")
    (output_root / "stage-result.md").write_text(
        "# Stage\\n\\n"
        f"{{stage}}\\n\\n"
        "## Attempt history\\n\\n"
        "- Attempt `1` (`initial`) -> succeeded.\\n\\n"
        "## Status\\n\\n"
        "- `succeeded`\\n"
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
        text = (
            "# Implementation Report\\n\\n"
            "## Verification\\n\\n"
            "- Result: `pass`; command: `pytest -q`; evidence: `runtime.log`.\\n"
        )
    else:
        text = f"# {{stage}} output\\n\\n- generated by fake AIDD\\n"
    (output_root / primary).write_text(text)

    stage_root = (
        Path(".aidd") / "reports" / "runs" / work_item / run_id / "stages" / stage
    )
    attempt_root = stage_root / "attempts" / "attempt-0001"
    attempt_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {{
                "status": "succeeded",
                "status_history": [{{"status": "succeeded"}}],
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
                body = f"<html><body>AIDD UI {{work_item}}</body></html>".encode()
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
                if self.path.startswith("/api/run"):
                    payload = {{
                        "run_id": run_id,
                        "work_item": work_item,
                        "status": "succeeded",
                    }}
                elif self.path.startswith("/api/stage"):
                    payload = {{
                        "run_id": run_id,
                        "work_item": work_item,
                        "stage": stage,
                        "status": "succeeded",
                    }}
                elif self.path.startswith("/api/questions"):
                    payload = {{
                        "work_item": work_item,
                        "stage": stage,
                        "state": "resolved",
                        "questions": [],
                    }}
                elif self.path.startswith("/api/logs"):
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
    quality_commands: tuple[str, ...] = ("printf 'quality\\n' > quality.log",),
    interview_required: bool = False,
    frontend_checkpoints: bool = True,
    runtime_targets: tuple[str, ...] = ("opencode",),
    acceptance_criteria: tuple[str, ...] = ("The fake AIDD stages complete.",),
) -> None:
    payload = {
        "id": "AIDD-TEST-LIVE-BLACKBOX",
        "scenario_class": "live-full-flow-interview" if interview_required else "live-full-flow",
        "feature_size": "small" if not interview_required else "large",
        "automation_lane": "manual",
        "canonical_runtime": runtime_targets[0],
        "task": "exercise black-box live evaluator",
        "repo": {"url": repo_url},
        "setup": {"commands": list(setup_commands)},
        "aidd_invocation": {"work_item": "WI-LIVE-BLACKBOX"},
        "verify": {"commands": list(verify_commands)},
        "quality": {
            "commands": list(quality_commands),
            "rubric_profile": "live-full",
            "require_review_status": (
                "approved-with-conditions" if interview_required else "approved"
            ),
            "allowed_qa_verdicts": ["ready", "ready-with-risks"],
            "code_review_required": True,
        },
        "stage_scope": {"start": "idea", "end": "qa"},
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
                    "quality_bar": "Quality evidence is complete.",
                    "size_rationale": "Small test fixture.",
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


def _prepare_live_test(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    runtime_targets: tuple[str, ...] = ("opencode",),
    fail_stage: str | None = None,
    timeout_stage: str | None = None,
    block_stage: str | None = None,
    ui_operator_request_stage: str | None = None,
    ui_operator_request_command: str = "pwd",
    internal_operator_decision_stage: str | None = None,
    setup_commands: tuple[str, ...] = ("printf 'setup\\n' > setup.log",),
    quality_commands: tuple[str, ...] = ("printf 'quality\\n' > quality.log",),
    interview_required: bool = False,
    frontend_checkpoints: bool = True,
    acceptance_criteria: tuple[str, ...] = ("The fake AIDD stages complete.",),
    inspect_block_stage: str | None = None,
    inspect_fail_command: str | None = None,
    log_blocking_text: bool = False,
) -> tuple[Path, Path, Path]:
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name=runtime_targets[0],
    )
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(
        fake_aidd,
        fail_stage=fail_stage,
        timeout_stage=timeout_stage,
        block_stage=block_stage,
        ui_operator_request_stage=ui_operator_request_stage,
        ui_operator_request_command=ui_operator_request_command,
        internal_operator_decision_stage=internal_operator_decision_stage,
        inspect_block_stage=inspect_block_stage,
        inspect_fail_command=inspect_fail_command,
        log_blocking_text=log_blocking_text,
    )
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=setup_commands,
        quality_commands=quality_commands,
        interview_required=interview_required,
        frontend_checkpoints=frontend_checkpoints,
        runtime_targets=runtime_targets,
        acceptance_criteria=acceptance_criteria,
    )
    monkeypatch.setattr(
        "aidd.harness.live_e2e_black_box.prepare_local_wheel_install",
        lambda *, work_root, run_id, repository_root: _install_result_for_fake_aidd(
            fake_aidd
        ),
    )
    return scenario_path, tmp_path / "work-root", tmp_path / ".aidd" / "reports" / "evals"


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
    assert result.quality_gate == "warn"
    assert result.counting_status == "pending-operator-analysis"
    assert result.bundle_root == report_root / result.run_id
    for filename in (
        "flow-state.json",
        "flow-steps.json",
        "flow-report.md",
        "operator-actions.jsonl",
        "verdict.md",
        "grader.json",
        "log-analysis.md",
        "quality-report.md",
        "stage-timing.json",
        "repair-history.md",
        "install-transcript.json",
        "setup-transcript.json",
        "run-transcript.json",
        "verify-transcript.json",
        "quality-transcript.json",
        "teardown-transcript.json",
        "acceptance-coverage.json",
        "acceptance-coverage.md",
        "operator-quality-analysis-validation.json",
        "ui-ux-checkpoints.json",
        "ui-ux-checkpoints.md",
    ):
        assert (result.bundle_root / filename).exists(), filename

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
    for stage in STAGES:
        assert (result.bundle_root / "stage-audits" / f"{stage}.json").exists()
        assert (result.bundle_root / "stage-audits" / f"{stage}.md").exists()
    for stage in STAGES:
        stage_audit = json.loads(
            (result.bundle_root / "stage-audits" / f"{stage}.json").read_text(
                encoding="utf-8"
            )
        )
        assert stage_audit["stage_state"] == "passed"
        assert stage_audit["unresolved_questions"] is False
    grader_payload = json.loads((result.bundle_root / "grader.json").read_text(encoding="utf-8"))
    assert grader_payload["execution"]["status"] == "pass"
    assert grader_payload["quality"]["machine_quality_gate"] == "pass"
    assert grader_payload["quality"]["quality_gate"] == "warn"
    assert grader_payload["quality"]["counting_status"] == "pending-operator-analysis"
    assert grader_payload["quality"]["acceptance_coverage_status"] == "missing"
    assert grader_payload["quality"]["ui_ux_gate"] == "pass"
    assert len(grader_payload["stage_audits"]) == len(STAGES)
    assert grader_payload["steps"][-1]["action"] == "finish"
    assert "Stage Audit Evidence" in (result.bundle_root / "quality-report.md").read_text(
        encoding="utf-8"
    )
    metadata_payload = json.loads(
        (result.bundle_root / "harness-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["temp_layout"]["work_root"] == work_root.as_posix()
    assert metadata_payload["temp_layout"]["report_root"] == report_root.as_posix()
    assert metadata_payload["black_box"]["ui_ux_evidence"]["gate"] == "pass"
    frontend_payload = json.loads(
        (result.bundle_root / "frontend-checkpoints.json").read_text(encoding="utf-8")
    )
    assert frontend_payload["enabled"] is True
    assert len(frontend_payload["checkpoints"]) == len(STAGES)
    assert all(
        checkpoint["classification"] == "pass"
        for checkpoint in frontend_payload["checkpoints"]
    )
    ui_ux_payload = json.loads(
        (result.bundle_root / "ui-ux-checkpoints.json").read_text(encoding="utf-8")
    )
    assert ui_ux_payload["ui_ux_gate"] == "pass"
    assert ui_ux_payload["checkpoints"][0]["screenshot"]["status"] == "skipped"
    operator_validation = json.loads(
        (result.bundle_root / "operator-quality-analysis-validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert operator_validation["present"] is False
    acceptance_payload = json.loads(
        (result.bundle_root / "acceptance-coverage.json").read_text(encoding="utf-8")
    )
    assert acceptance_payload["acceptance_coverage_status"] == "missing"


def test_black_box_live_e2e_records_complete_acceptance_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        acceptance_criteria=(
            "Result command evidence runtime log",
        ),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    coverage = json.loads(
        (result.bundle_root / "acceptance-coverage.json").read_text(encoding="utf-8")
    )
    assert coverage["acceptance_coverage_status"] == "complete"
    assert coverage["criteria"][0]["status"] == "confirmed"
    assert coverage["criteria"][0]["evidence_refs"]
    grader_payload = json.loads((result.bundle_root / "grader.json").read_text(encoding="utf-8"))
    assert grader_payload["quality"]["acceptance_coverage_status"] == "complete"


def test_black_box_live_e2e_refreshes_counted_clean_after_operator_analysis(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        acceptance_criteria=("Result command evidence runtime log",),
    )

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    assert first.counting_status == "pending-operator-analysis"
    (first.bundle_root / "operator-quality-analysis.md").write_text(
        "\n".join(
            (
                "# Operator Quality Analysis",
                "",
                "## Machine Result",
                "- Execution verdict: pass",
                "- Quality gate: pass",
                "- QA verdict: ready",
                "- Review status: approved",
                "",
                "## Decision",
                "- Decision: counted-clean",
                "",
                "## Blockers",
                "- none",
                "",
            )
        ),
        encoding="utf-8",
    )

    refreshed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert refreshed.status == "pass"
    assert refreshed.quality_gate == "pass"
    assert refreshed.counting_status == "counted-clean"
    validation = json.loads(
        (refreshed.bundle_root / "operator-quality-analysis-validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert validation["valid"] is True
    assert validation["decision"] == "counted-clean"


def test_black_box_live_e2e_rejects_invalid_operator_counted_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(tmp_path, monkeypatch)

    first = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )
    (first.bundle_root / "operator-quality-analysis.md").write_text(
        "\n".join(
            (
                "# Operator Quality Analysis",
                "",
                "## Machine Result",
                "- Execution verdict: pass",
                "- Quality gate: pass",
                "- QA verdict: ready",
                "- Review status: approved",
                "",
                "## Decision",
                "- Decision: counted-clean",
                "",
                "## Blockers",
                "- none",
                "",
            )
        ),
        encoding="utf-8",
    )

    refreshed = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
        run_id=first.run_id,
    )

    assert refreshed.counting_status == "pending-operator-analysis"
    validation = json.loads(
        (refreshed.bundle_root / "operator-quality-analysis-validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert validation["valid"] is False
    assert "incomplete acceptance coverage" in "\n".join(validation["findings"])


def test_black_box_live_e2e_blocks_for_questions_and_continues_after_answers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        block_stage="idea",
        quality_commands=("command -v fake-aidd >/dev/null",),
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
        quality_commands=("command -v fake-aidd >/dev/null",),
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
        quality_commands=("command -v fake-aidd >/dev/null",),
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


def test_black_box_live_e2e_fails_required_interview_without_blocked_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        interview_required=True,
        quality_commands=("command -v fake-aidd >/dev/null",),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "fail"
    assert result.quality_gate == "fail"
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
        quality_commands=("command -v fake-aidd >/dev/null",),
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
        quality_commands=("command -v fake-aidd >/dev/null",),
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
        quality_commands=("command -v fake-aidd >/dev/null",),
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
        (result.bundle_root / "stage-audits" / "plan.json").read_text(encoding="utf-8")
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
        "aidd.harness.live_e2e_black_box_orchestration._flow_timeout_seconds",
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
    assert timeout_step["details"]["timeout_reconciliation"]["previous_status"] == "executing"
    assert timeout_step["details"]["timeout_reconciliation"]["reconciled_status"] == "failed"
    assert timeout_step["evidence_paths"]
    reconciliation_path = Path(timeout_step["evidence_paths"][0])
    assert reconciliation_path.exists()
    reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    assert reconciliation["reconciled"] is True
    audit_payload = json.loads(
        (result.bundle_root / "stage-audits" / "idea.json").read_text(encoding="utf-8")
    )
    assert audit_payload["stage_state"] == "failed"
    assert audit_payload["stage_metadata_status"] == "failed"
    assert audit_payload["classifications"]["frontend_checkpoint"] == "skipped"


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


def test_black_box_live_e2e_quality_failure_is_additive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario_path, work_root, report_root = _prepare_live_test(
        tmp_path,
        monkeypatch,
        quality_commands=("printf 'quality failed\\n'; exit 5",),
    )

    result = run_black_box_live_e2e(
        scenario_path=scenario_path,
        runtime_id="opencode",
        work_root=work_root,
        report_root=report_root,
    )

    assert result.status == "pass"
    assert result.quality_gate == "fail"
    quality_payload = json.loads(
        (result.bundle_root / "quality-transcript.json").read_text(encoding="utf-8")
    )
    assert quality_payload["commands"][0]["exit_code"] == 5


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
