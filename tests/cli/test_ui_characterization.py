from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from test_ui import (
    _payload,
    _prepare_completed_qa_run,
    _prepare_run,
    _service,
)

from aidd.cli.ui import OperatorUiService, UiRunJobStore
from aidd.core.mutation_lease import RunMutationConflict
from aidd.core.remediation import mark_downstream_stale
from aidd.core.run_store import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    RUN_RUNTIME_EXIT_METADATA_FILENAME,
    persist_stage_status,
    run_attempt_root,
)
from aidd.core.runtime_operator import (
    RuntimeOperatorRequest,
    append_operator_request,
    load_operator_decisions,
)
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
)

_EXPECTED = json.loads(
    (
        Path(__file__).parents[1]
        / "fixtures"
        / "operator_ui_characterization.json"
    ).read_text(encoding="utf-8")
)


def _response_snapshot(response: Any) -> dict[str, object]:
    body: object
    if response.content_type.startswith("application/json"):
        body = json.loads(response.body.decode("utf-8"))
    else:
        body = None
    snapshot: dict[str, object] = {
        "status": response.status,
        "content_type": response.content_type,
    }
    if body is not None:
        snapshot["body"] = body
    return snapshot


class _ConflictService(OperatorUiService):
    def _start_stage_job(self, payload: dict[str, Any]) -> object:
        raise RunMutationConflict(
            "Run mutation conflict: characterized owner already exists."
        )


def test_ui_route_contract_characterization(tmp_path: Path) -> None:
    service = _service(tmp_path / ".aidd")
    conflict = _ConflictService(service.options)

    actual = {
        "get_static": _response_snapshot(service.handle_get("/operator.js", {})),
        "get_unknown": _response_snapshot(service.handle_get("/missing", {})),
        "post_mutation_conflict": _response_snapshot(
            conflict.handle_post(
                "/api/stage/run",
                {"stage": "plan", "runtime": "codex"},
            )
        ),
        "post_unknown": _response_snapshot(service.handle_post("/missing", {})),
    }

    assert actual == _EXPECTED["routing"]
    assert files("aidd.cli.static").joinpath("operator.js").read_bytes()


def test_ui_job_retention_and_cancellation_characterization() -> None:
    def clock() -> datetime:
        return datetime(2026, 7, 16, 12, 0, tzinfo=UTC)

    store = UiRunJobStore(
        max_live_log_bytes=40,
        max_log_response_bytes=12,
        now=clock,
    )
    job_id = store.create(kind="stage", stage="plan")
    store.append_chunk(job_id, stream="stdout", text="a" * 50)
    store.append_chunk(job_id, stream="stderr", text="b" * 50)
    page = store.logs(job_id, cursor=0)
    assert {
        "oldest_cursor": page["oldest_cursor"],
        "truncated": page["truncated"],
        "dropped_bytes": page["dropped_bytes"],
        "has_more": page["has_more"],
    } == _EXPECTED["log_cursor_gap"]

    store.wait_for_operator(
        job_id,
        result={"waiting_for_operator": True},
        message="waiting",
    )
    cancelled = store.cancel(job_id)
    assert {
        "status": cancelled["status"],
        "previous_status": cancelled["previous_status"],
        "cancel_state": cancelled["cancel_state"],
        "exit_code": cancelled["exit_code"],
    } == _EXPECTED["job_cancellation"]


def test_ui_approval_cas_and_terminal_rejection_characterization(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    service = _service(workspace_root)
    job_id = service._jobs.create(kind="stage", stage="plan")
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    request = RuntimeOperatorRequest(
        id="opr-characterized",
        runtime_id="codex",
        stage="plan",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "python -m pytest -q"},
        created_at_utc="2026-07-16T12:00:00Z",
    )
    append_operator_request(
        path=attempt_path / OPERATOR_REQUESTS_FILENAME,
        request=request,
    )
    service._jobs.set_attempt_path(job_id, attempt_path)
    service._jobs.wait_for_operator(
        job_id,
        result={"waiting_for_operator": True},
        message="waiting",
    )
    route = f"/api/jobs/{job_id}/operator-requests/{request.id}/decision"
    initial = service.handle_post(
        route,
        {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
    )
    idempotent = service.handle_post(
        route,
        {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
    )
    conflict = service.handle_post(
        route,
        {"action": RuntimeOperatorDecisionAction.DENY.value},
    )
    decisions = load_operator_decisions(attempt_path / OPERATOR_DECISIONS_FILENAME)
    winner = decisions[0]
    assert {
        "initial_status": initial.status,
        "idempotent_status": idempotent.status,
        "conflict_status": conflict.status,
        "decision_action": winner.action.value,
        "decision_source": winner.source.value,
        "durable_decision_count": len(decisions),
    } == _EXPECTED["approval_cas"]

    terminal_job = service._jobs.create(kind="stage", stage="plan")
    service._jobs.complete(
        terminal_job,
        result={},
        exit_code=0,
        message="completed",
    )
    terminal = service.handle_post(
        f"/api/jobs/{terminal_job}/operator-requests/{request.id}/decision",
        {"action": RuntimeOperatorDecisionAction.ALLOW_ONCE.value},
    )
    terminal_snapshot = {
        "status": terminal.status,
        "body": json.loads(terminal.body.decode("utf-8")),
    }
    terminal_snapshot["body"]["error"] = terminal_snapshot["body"]["error"].replace(
        terminal_job,
        "<job-id>",
    )
    assert terminal_snapshot == _EXPECTED["terminal_decision_rejection"]


def _dashboard_summary(payload: dict[str, object]) -> dict[str, object]:
    dashboard = payload["dashboard"]
    assert isinstance(dashboard, dict)
    handoff = dashboard["terminal_handoff"]
    return {
        "active_stage": dashboard["active_stage"],
        "next_action": dashboard["next_action"]["action"],
        "terminal_handoff": None if handoff is None else handoff["status"],
    }


def test_ui_dashboard_state_characterization(tmp_path: Path) -> None:
    running_root = tmp_path / "running"
    running_service = _service(running_root)
    running_job = running_service._jobs.create(kind="stage", stage="idea")
    running_payload = _payload(running_service.handle_get("/api/dashboard", {}))
    running = _dashboard_summary(running_payload)
    running["active_job_status"] = running_payload["active_job"]["status"]  # type: ignore[index]
    assert running_job
    assert running == _EXPECTED["dashboard_running"]

    failure_root = tmp_path / "failure"
    _prepare_run(failure_root)
    persist_stage_status(
        workspace_root=failure_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        status="failed",
    )
    failure_attempt = run_attempt_root(
        workspace_root=failure_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    (failure_attempt / RUN_RUNTIME_EXIT_METADATA_FILENAME).write_text(
        json.dumps(
            {
                "exit_code": 130,
                "exit_classification": "cancelled",
                "adapter_outcome": "cancelled",
                "completed_at_utc": "2026-07-16T12:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    failure_payload = _payload(
        _service(failure_root).handle_get(
            "/api/dashboard",
            {"run_id": ["run-ui"]},
        )
    )
    failure = _dashboard_summary(failure_payload)
    failure["first_failure"] = failure_payload["dashboard"]["first_failure"]["kind"]  # type: ignore[index]
    assert failure == _EXPECTED["dashboard_runtime_failure"]

    stale_root = tmp_path / "stale"
    _prepare_completed_qa_run(stale_root)
    mark_downstream_stale(
        workspace_root=stale_root,
        work_item="WI-UI",
        run_id="run-ui",
        invalidated_by="rem-characterized",
    )
    stale_payload = _payload(
        _service(stale_root).handle_get(
            "/api/dashboard",
            {"stage": ["qa"], "run_id": ["run-ui"]},
        )
    )
    stale = _dashboard_summary(stale_payload)
    stale["stale_stages"] = [
        item["stage"]
        for item in stale_payload["dashboard"]["stages"]  # type: ignore[index]
        if item["stale"]
    ]
    assert stale == _EXPECTED["dashboard_stale_remediation"]

    terminal_root = tmp_path / "terminal"
    _prepare_completed_qa_run(terminal_root)
    terminal_payload = _payload(
        _service(terminal_root).handle_get(
            "/api/dashboard",
            {"stage": ["qa"], "run_id": ["run-ui"]},
        )
    )
    terminal = _dashboard_summary(terminal_payload)
    terminal["final_qa_status"] = terminal_payload["dashboard"]["terminal_handoff"][  # type: ignore[index]
        "final_qa_status"
    ]
    assert terminal == _EXPECTED["dashboard_terminal_qa"]


def test_ui_blocked_approval_dashboard_characterization(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _prepare_run(workspace_root)
    attempt_path = run_attempt_root(
        workspace_root=workspace_root,
        work_item="WI-UI",
        run_id="run-ui",
        stage="plan",
        attempt_number=1,
    )
    append_operator_request(
        path=attempt_path / OPERATOR_REQUESTS_FILENAME,
        request=RuntimeOperatorRequest(
            id="opr-pending",
            runtime_id="codex",
            stage="plan",
            kind=RuntimeOperatorRequestKind.SHELL,
            payload={"command": "npm install"},
            created_at_utc="2026-07-16T12:00:00Z",
        ),
    )
    payload = _payload(
        _service(workspace_root).handle_get(
            "/api/dashboard",
            {"stage": ["plan"], "run_id": ["run-ui"]},
        )
    )
    dashboard = payload["dashboard"]
    assert {
        "active_stage": dashboard["active_stage"],  # type: ignore[index]
        "next_action": dashboard["next_action"]["action"],  # type: ignore[index]
        "approval_status": dashboard["active_stage_view"]["diagnostics"]["approvals"][  # type: ignore[index]
            "status"
        ],
        "terminal_handoff": dashboard["terminal_handoff"],  # type: ignore[index]
    } == _EXPECTED["dashboard_blocked_approval"]
