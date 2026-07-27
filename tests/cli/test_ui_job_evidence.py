from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.cli.ui import UiRunJobStore


def _attempt(
    tmp_path: Path,
    *,
    adapter_outcome: str,
    exit_classification: str,
    stage_status: str,
) -> Path:
    stage_root = tmp_path / "stages" / "implement"
    attempt_path = stage_root / "attempts" / "attempt-0003"
    attempt_path.mkdir(parents=True)
    (attempt_path / "runtime-exit.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "adapter_outcome": adapter_outcome,
                "exit_classification": exit_classification,
                "exit_code": 0 if adapter_outcome == "success" else 1,
                "stop_reason": (
                    None if adapter_outcome == "success" else adapter_outcome
                ),
            }
        ),
        encoding="utf-8",
    )
    (stage_root / "stage-metadata.json").write_text(
        json.dumps(
            {
                "status": stage_status,
                "updated_at_utc": "2026-07-26T10:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    return attempt_path


@pytest.mark.parametrize(
    ("transition", "job_status", "adapter_outcome", "cause_kind"),
    (
        ("complete", "completed", "success", "durable-stage-status"),
        ("fail", "failed", "runtime_failure", "adapter-outcome"),
        ("wait", "waiting-for-operator", "blocked", "adapter-outcome"),
        ("cancel", "cancelled", "cancellation", "adapter-outcome"),
    ),
)
def test_ui_job_store_retains_typed_terminal_evidence(
    tmp_path: Path,
    transition: str,
    job_status: str,
    adapter_outcome: str,
    cause_kind: str,
) -> None:
    store = UiRunJobStore()
    job_id = store.create(
        kind="remediation",
        work_item="WI-LIVE",
        run_id="run-live",
        stage="implement",
    )
    attempt_path = _attempt(
        tmp_path,
        adapter_outcome=adapter_outcome,
        exit_classification=adapter_outcome,
        stage_status="passed" if transition == "complete" else "executing",
    )
    store.set_attempt_path(job_id, attempt_path)

    if transition == "complete":
        store.complete(job_id, result={"completed": True}, exit_code=0, message="completed")
    elif transition == "fail":
        store.fail(job_id, message="runtime stopped", exit_code=1)
    else:
        store.wait_for_operator(
            job_id,
            result={
                "waiting_for_operator": True,
                "request_id": "request-1",
                "attempt_path": attempt_path.as_posix(),
            },
            message="waiting for operator decision",
        )
        if transition == "cancel":
            store.cancel(job_id)

    payload = store.view(job_id)
    evidence = payload["terminal_evidence"]
    assert isinstance(evidence, dict)
    assert evidence["work_item"] == "WI-LIVE"
    assert evidence["run_id"] == "run-live"
    assert evidence["stage"] == "implement"
    assert evidence["attempt_number"] == 3
    assert evidence["job_status"] == job_status
    assert evidence["adapter_outcome"] == adapter_outcome
    assert evidence["runtime_exit"]["artifact_path"] == (  # type: ignore[index]
        attempt_path / "runtime-exit.json"
    ).as_posix()
    assert evidence["durable_mutation_winner"]["status"] == (  # type: ignore[index]
        "passed" if transition == "complete" else "executing"
    )
    assert evidence["first_decisive_cause"]["kind"] == cause_kind  # type: ignore[index]
    assert evidence["operator_wait"]["request_id"] == (  # type: ignore[index]
        "request-1" if transition in {"wait", "cancel"} else None
    )
    assert evidence["cancellation"]["requested"] is (transition == "cancel")  # type: ignore[index]
