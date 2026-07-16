from __future__ import annotations

import json
from pathlib import Path

from aidd.harness.live_e2e_flow_state import find_resume_state


def _write_state(report_root: Path, run_id: str, payload: dict[str, object]) -> Path:
    path = report_root / run_id / "flow-state.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_stale_running_reconstruction_is_idempotent(tmp_path: Path) -> None:
    state_path = _write_state(
        tmp_path,
        "stale-run",
        {
            "schema_version": 2,
            "status": "running",
            "next_action": "run-stage",
            "evaluator_pid": 99999999,
        },
    )

    assert find_resume_state(report_root=tmp_path, run_id="stale-run") == state_path
    first_payload = state_path.read_bytes()
    assert find_resume_state(report_root=tmp_path, run_id="stale-run") == state_path

    assert state_path.read_bytes() == first_payload


def test_terminal_state_can_be_reloaded_without_rewriting(tmp_path: Path) -> None:
    state_path = _write_state(
        tmp_path,
        "complete-run",
        {
            "schema_version": 2,
            "status": "pass",
            "next_action": "finish",
            "evaluator_pid": 99999999,
        },
    )
    original = state_path.read_bytes()

    assert find_resume_state(report_root=tmp_path, run_id="complete-run") == state_path
    assert find_resume_state(report_root=tmp_path, run_id="complete-run") == state_path
    assert state_path.read_bytes() == original
