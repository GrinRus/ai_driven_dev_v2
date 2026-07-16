from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from aidd.adapters.process_supervisor import OwnedProcessSupervisor
from aidd.adapters.qwen.live import _parse_json_line, _read_complete_event_lines
from aidd.adapters.runtime_execution import RuntimeSubprocessSpec, StageRuntimeRequest
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.core.runtime_operator import (
    RuntimeOperatorDecision,
    RuntimeOperatorRequest,
    load_operator_decisions,
)
from aidd.core.stage_models import AdapterExecutionStatus
from aidd.runtime_catalog import RuntimeExecutionMode
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeInteractionMode,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimePermissionPolicy,
)


class _DecisionProvider:
    def __init__(self, action: RuntimeOperatorDecisionAction) -> None:
        self.action = action
        self.requests: list[RuntimeOperatorRequest] = []

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> RuntimeOperatorDecision:
        _ = requests_path, decisions_path
        self.requests.append(request)
        return RuntimeOperatorDecision(
            request_id=request.id,
            action=self.action,
            source=RuntimeOperatorDecisionSource.CLI,
            reason="qwen fake decision",
        )


class _NoDecisionProvider:
    def __init__(self) -> None:
        self.requests: list[RuntimeOperatorRequest] = []

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> None:
        _ = requests_path, decisions_path
        self.requests.append(request)
        return None


class _CancelDuringDecisionProvider:
    def __init__(self, cancel: list[bool]) -> None:
        self.cancel = cancel

    def request_decision(
        self,
        request: RuntimeOperatorRequest,
        *,
        requests_path: Path,
        decisions_path: Path,
    ) -> None:
        _ = request, requests_path, decisions_path
        self.cancel[0] = True
        return None


def _request(
    tmp_path: Path,
    *,
    timeout_seconds: float = 5.0,
    prompt_size: int = 0,
    cancel_requested: Callable[[], bool] | None = None,
) -> StageRuntimeRequest:
    repo = tmp_path / "repo"
    workspace = tmp_path / ".aidd"
    repo.mkdir(exist_ok=True)
    workspace.mkdir(exist_ok=True)
    stage_brief = workspace / "stage-brief.md"
    prompt_pack = workspace / "prompt-pack.md"
    stage_brief.write_text("# Stage brief\n" + ("x" * prompt_size), encoding="utf-8")
    prompt_pack.write_text("# Prompt pack\n", encoding="utf-8")
    return StageRuntimeRequest(
        runtime_id="qwen",
        execution_mode=RuntimeExecutionMode.NATIVE,
        permission_policy=RuntimePermissionPolicy.BROKERED,
        interaction_mode=RuntimeInteractionMode.LIVE,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        timeout_seconds=timeout_seconds,
        stage="implement",
        work_item="WI-QWEN",
        run_id="run-qwen",
        workspace_root=workspace,
        stage_brief_path=stage_brief,
        prompt_pack_paths=(prompt_pack,),
        repository_root=repo,
        project_roots=(repo,),
        cancel_requested=cancel_requested,
    )


def _fake_qwen(
    tmp_path: Path,
    *,
    scenario: str = "approval",
    with_descendant: bool = False,
) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    script = bin_dir / "qwen"
    script.write_text(
        f"#!{sys.executable}\n"
        f"scenario = {scenario!r}\n"
        f"with_descendant = {with_descendant!r}\n"
        "import json, subprocess, sys, time\n"
        "if '--help' in sys.argv:\n"
        "    print('--approval-mode --output-format --json-file --input-file')\n"
        "    raise SystemExit(0)\n"
        "if with_descendant:\n"
        "    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "if scenario == 'hang':\n"
        "    time.sleep(10)\n"
        "    raise SystemExit(3)\n"
        "if scenario == 'bidirectional':\n"
        "    sys.stdout.write('y' * 200000)\n"
        "    sys.stdout.flush()\n"
        "    print(len(sys.stdin.read()))\n"
        "    raise SystemExit(0)\n"
        "if scenario == 'active_wait':\n"
        "    sys.stdin.read()\n"
        "    time.sleep(10)\n"
        "    raise SystemExit(3)\n"
        "json_file = sys.argv[sys.argv.index('--json-file') + 1]\n"
        "input_file = sys.argv[sys.argv.index('--input-file') + 1]\n"
        "event = {'type': 'control_request', 'payload': {'request_id': 'qwen-1', "
        "'kind': 'shell', 'tool_name': 'shell', 'command': 'npm install'}}\n"
        "with open(json_file, 'a', encoding='utf-8') as handle:\n"
        "    if scenario == 'duplicate_malformed':\n"
        "        handle.write('{not-json}\\n')\n"
        "    handle.write(json.dumps(event) + '\\n')\n"
        "    if scenario == 'duplicate_malformed':\n"
        "        handle.write(json.dumps(event) + '\\n')\n"
        "deadline = time.time() + 4\n"
        "while time.time() < deadline:\n"
        "    try:\n"
        "        lines = open(input_file, encoding='utf-8').read().splitlines()\n"
        "    except FileNotFoundError:\n"
        "        lines = []\n"
        "    for line in lines:\n"
        "        payload = json.loads(line)\n"
        "        if payload.get('type') == 'confirmation_response':\n"
        "            print(json.dumps({'received': payload}))\n"
        "            raise SystemExit(0 if payload.get('allowed') else 2)\n"
        "    time.sleep(0.05)\n"
        "raise SystemExit(3)\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_qwen_live_transport_resumes_after_provider_decision(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path)
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=f"{fake_qwen} --approval-mode yolo --output-format stream-json",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    assert provider.requests[0].payload["command"] == "npm install"
    assert result.operator_decisions_path is not None
    assert load_operator_decisions(result.operator_decisions_path)[-1].action is (
        RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION
    )
    qwen_input = [
        json.loads(line)
        for line in (attempt_path / "qwen-input.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert qwen_input[-1]["type"] == "confirmation_response"
    assert qwen_input[-1]["scope"] == "session"


def test_qwen_live_transport_blocks_without_provider_before_launch(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert not (attempt_path / "qwen-events.jsonl").exists()


def test_qwen_live_transport_rejects_custom_dual_file_command(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path)
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=f"{fake_qwen} --json-file custom.jsonl --input-file input.jsonl",
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert provider.requests == []
    assert not (attempt_path / "qwen-events.jsonl").exists()


def test_qwen_live_transport_ignores_malformed_and_duplicate_events(
    tmp_path: Path,
) -> None:
    fake_qwen = _fake_qwen(tmp_path, scenario="duplicate_malformed")
    provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED
    assert [request.id for request in provider.requests] == ["qwen-1"]
    confirmations = [
        json.loads(line)
        for line in (attempt_path / "qwen-input.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(confirmations) == 1
    assert confirmations[0]["request_id"] == "qwen-1"


def test_qwen_event_reader_preserves_every_incomplete_byte_boundary(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "qwen-events.jsonl"
    event = {
        "type": "control_request",
        "payload": {
            "request_id": "qwen-fragmented",
            "kind": "shell",
            "reason": "проверка",
        },
    }
    encoded = (json.dumps(event, ensure_ascii=False) + "\n").encode()

    for split_at in range(1, len(encoded)):
        events_path.write_bytes(encoded[:split_at])
        offset, lines = _read_complete_event_lines(
            events_path=events_path,
            read_offset=0,
        )
        assert offset == 0
        assert lines == ()

        with events_path.open("ab") as handle:
            handle.write(encoded[split_at:])
        offset, lines = _read_complete_event_lines(
            events_path=events_path,
            read_offset=offset,
        )
        assert offset == len(encoded)
        assert len(lines) == 1
        assert _parse_json_line(lines[0]) == event


def test_qwen_event_reader_commits_malformed_complete_line_before_partial_tail(
    tmp_path: Path,
) -> None:
    events_path = tmp_path / "qwen-events.jsonl"
    events_path.write_bytes(b"{not-json}\n{\"type\":")

    offset, lines = _read_complete_event_lines(
        events_path=events_path,
        read_offset=0,
    )

    assert offset == len(b"{not-json}\n")
    assert len(lines) == 1
    assert _parse_json_line(lines[0]) is None

    with events_path.open("ab") as handle:
        handle.write(b"\"message\"}\n")
    offset, lines = _read_complete_event_lines(
        events_path=events_path,
        read_offset=offset,
    )
    assert offset == events_path.stat().st_size
    assert _parse_json_line(lines[0]) == {"type": "message"}


@pytest.mark.parametrize(
    "action",
    [RuntimeOperatorDecisionAction.DENY, RuntimeOperatorDecisionAction.CANCEL],
)
def test_qwen_live_transport_deny_or_cancel_fails_stage(
    tmp_path: Path,
    action: RuntimeOperatorDecisionAction,
) -> None:
    fake_qwen = _fake_qwen(tmp_path)
    provider = _DecisionProvider(action)
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == f"permission-denied: {action.value}"
    exit_metadata = json.loads(
        (attempt_path / "runtime-exit.json").read_text(encoding="utf-8")
    )
    expected_classification = (
        "cancelled"
        if action is RuntimeOperatorDecisionAction.CANCEL
        else "denied"
    )
    expected_outcome = (
        "cancellation"
        if action is RuntimeOperatorDecisionAction.CANCEL
        else "denial"
    )
    assert exit_metadata["exit_classification"] == expected_classification
    assert exit_metadata["adapter_outcome"] == expected_outcome
    assert exit_metadata["exit_code"] is None


def test_qwen_live_transport_blocks_when_provider_has_no_decision(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path)
    provider = _NoDecisionProvider()
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.BLOCKED_FOR_OPERATOR
    assert result.pending_operator_request_ids == ("qwen-1",)
    assert provider.requests[0].id == "qwen-1"
    assert (attempt_path / "operator-requests.jsonl").exists()
    assert (attempt_path / "qwen-events.jsonl").exists()
    assert (attempt_path / "qwen-input.jsonl").read_text(encoding="utf-8") == ""
    exit_metadata = json.loads(
        (attempt_path / "runtime-exit.json").read_text(encoding="utf-8")
    )
    assert exit_metadata["exit_classification"] == "blocked"
    assert exit_metadata["adapter_outcome"] == "blocked"
    assert exit_metadata["exit_code"] is None
    assert (attempt_path / "runtime.log").exists()


def test_qwen_live_transport_timeout_fails_stage(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path, scenario="hang")

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path, timeout_seconds=0.2),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=_DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE),
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == "qwen-live: timeout"
    timeout_metadata = json.loads(
        (tmp_path / "attempt" / "runtime-exit.json").read_text(encoding="utf-8")
    )
    assert timeout_metadata["exit_classification"] == "timeout"
    assert timeout_metadata["adapter_outcome"] == "timeout"


@pytest.mark.parametrize("phase", ("startup", "active", "approval"))
def test_qwen_live_transport_persists_cancelled_outcome(
    tmp_path: Path,
    phase: str,
) -> None:
    cancel = [False]
    started_at = time.monotonic()

    def cancel_requested() -> bool:
        if phase == "approval":
            return cancel[0]
        return time.monotonic() - started_at >= 0.1

    scenario = {
        "startup": "hang",
        "active": "active_wait",
        "approval": "approval",
    }[phase]
    provider = (
        _CancelDuringDecisionProvider(cancel)
        if phase == "approval"
        else _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE)
    )
    attempt_path = tmp_path / "attempt"

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(_fake_qwen(tmp_path, scenario=scenario)),
        request=_request(tmp_path, cancel_requested=cancel_requested),
        attempt_path=attempt_path,
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is AdapterExecutionStatus.FAILED
    assert result.details == "qwen-live: cancelled"
    assert json.loads((attempt_path / "runtime-exit.json").read_text(encoding="utf-8"))[
        "exit_classification"
    ] == "cancelled"
    assert result.adapter_outcome is not None
    assert result.adapter_outcome.value == "cancellation"
    assert (attempt_path / "runtime.log").exists()
    if phase == "approval":
        assert (attempt_path / "qwen-input.jsonl").read_text(encoding="utf-8") == ""


def test_qwen_live_supervises_output_before_large_prompt_delivery(tmp_path: Path) -> None:
    fake_qwen = _fake_qwen(tmp_path, scenario="bidirectional")

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(fake_qwen),
        request=_request(tmp_path, prompt_size=2_000_000),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=_DecisionProvider(
            RuntimeOperatorDecisionAction.ALLOW_ONCE
        ),
    )

    assert result.resolved_status is AdapterExecutionStatus.SUCCEEDED


@pytest.mark.skipif(os.name == "nt", reason="process groups are POSIX-specific")
@pytest.mark.parametrize("stop_mode", ("timeout", "denial", "cancellation", "blocked"))
def test_qwen_live_terminal_paths_stop_descendants(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stop_mode: str,
) -> None:
    launched: list[OwnedProcessSupervisor] = []
    original_launch = OwnedProcessSupervisor.launch.__func__

    def capture_launch(
        cls: type[OwnedProcessSupervisor],
        spec: RuntimeSubprocessSpec,
    ) -> OwnedProcessSupervisor:
        supervisor = original_launch(cls, spec)
        launched.append(supervisor)
        return supervisor

    monkeypatch.setattr(
        OwnedProcessSupervisor,
        "launch",
        classmethod(capture_launch),
    )
    started_at = time.monotonic()

    def cancel_requested() -> bool:
        return time.monotonic() - started_at >= 0.1

    provider: _DecisionProvider | _NoDecisionProvider
    if stop_mode == "denial":
        provider = _DecisionProvider(RuntimeOperatorDecisionAction.DENY)
    elif stop_mode == "blocked":
        provider = _NoDecisionProvider()
    else:
        provider = _DecisionProvider(RuntimeOperatorDecisionAction.ALLOW_ONCE)

    result = get_runtime_adapter_surface("qwen").execute_stage_request(
        configured_command=str(
            _fake_qwen(
                tmp_path,
                scenario="hang" if stop_mode in {"timeout", "cancellation"} else "approval",
                with_descendant=True,
            )
        ),
        request=_request(
            tmp_path,
            timeout_seconds=0.2 if stop_mode == "timeout" else 5.0,
            cancel_requested=cancel_requested if stop_mode == "cancellation" else None,
        ),
        attempt_path=tmp_path / "attempt",
        base_env={},
        operator_decision_provider=provider,
    )

    assert result.resolved_status is not AdapterExecutionStatus.SUCCEEDED
    assert len(launched) == 1
    assert launched[0].process_group_exists() is False
