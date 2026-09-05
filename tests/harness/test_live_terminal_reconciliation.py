from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.harness.live_e2e_black_box_steps import BlackBoxCommandResult
from aidd.harness.live_terminal_reconciliation import (
    LiveTerminalReconciliationError,
    run_live_terminal_reconciliation,
)
from aidd.harness.runner import HarnessCommandTranscript


def _result(*, stdout: str, exit_code: int = 0, stderr: str = "") -> BlackBoxCommandResult:
    return BlackBoxCommandResult(
        command=("aidd", "stage", "reconcile-terminal"),
        transcript=HarnessCommandTranscript(
            command="aidd stage reconcile-terminal",
            exit_code=exit_code,
            stdout_text=stdout,
            stderr_text=stderr,
            duration_seconds=0.01,
        ),
    )


def _payload(
    working_copy: Path,
    *,
    expected_state: str = "executing",
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "work_item": "WI-LIVE",
        "run_id": "run-live",
        "stage": "idea",
        "expected_state": expected_state,
        "reason": "stage-command-timeout",
        "reconciled": True,
        "evidence_path": (
            working_copy
            / ".aidd/reports/runs/WI-LIVE/run-live/stages/idea/"
            "terminal-reconciliation.json"
        ).as_posix(),
    }
    payload.update(overrides)
    return payload


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    working_copy: Path,
    command_result: BlackBoxCommandResult,
    *,
    expected_state: str = "executing",
):
    calls: list[dict[str, object]] = []

    def fake_run(**kwargs: object) -> BlackBoxCommandResult:
        calls.append(kwargs)
        return command_result

    monkeypatch.setattr(
        "aidd.harness.live_terminal_reconciliation._run_black_box_command",
        fake_run,
    )
    result = run_live_terminal_reconciliation(
        installed_command=("venv/bin/aidd",),
        working_copy=working_copy,
        environment={"PATH": "/bin"},
        work_item="WI-LIVE",
        run_id="run-live",
        stage="idea",
        expected_state=expected_state,
        reason="stage-command-timeout",
    )
    return result, calls


def test_harness_invokes_installed_public_terminal_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    working_copy = tmp_path / "target"
    working_copy.mkdir()
    payload = _payload(working_copy)

    result, calls = _invoke(
        monkeypatch,
        working_copy,
        _result(stdout=json.dumps(payload)),
    )

    assert result.payload == payload
    assert calls[0]["cwd"] == working_copy
    assert calls[0]["command"] == (
        "venv/bin/aidd",
        "stage",
        "reconcile-terminal",
        "idea",
        "--work-item",
        "WI-LIVE",
        "--run-id",
        "run-live",
        "--expected-state",
        "executing",
        "--reason",
        "stage-command-timeout",
        "--root",
        ".aidd",
    )


def test_harness_passes_validating_state_to_public_reconciliation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    working_copy = tmp_path / "target"
    working_copy.mkdir()
    payload = _payload(working_copy, expected_state="validating")

    result, calls = _invoke(
        monkeypatch,
        working_copy,
        _result(stdout=json.dumps(payload)),
        expected_state="validating",
    )

    assert result.payload["expected_state"] == "validating"
    assert calls[0]["command"][calls[0]["command"].index("--expected-state") + 1] == (
        "validating"
    )


@pytest.mark.parametrize(
    "override",
    (
        {"run_id": "wrong-run"},
        {"evidence_path": "/tmp/escaped.json"},
    ),
)
def test_harness_rejects_untrusted_reconciliation_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    override: dict[str, object],
) -> None:
    working_copy = tmp_path / "target"
    working_copy.mkdir()

    with pytest.raises(LiveTerminalReconciliationError):
        _invoke(
            monkeypatch,
            working_copy,
            _result(stdout=json.dumps(_payload(working_copy, **override))),
        )


def test_harness_rejects_failed_reconciliation_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    working_copy = tmp_path / "target"
    working_copy.mkdir()

    with pytest.raises(LiveTerminalReconciliationError, match="exit 7"):
        _invoke(
            monkeypatch,
            working_copy,
            _result(stdout="", stderr="failed", exit_code=7),
        )
