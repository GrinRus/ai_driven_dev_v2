from __future__ import annotations

from dataclasses import dataclass

import pytest

from aidd.harness.live_e2e_black_box_frontend import (
    frontend_checkpoint_timed_out,
    frontend_checkpoint_timeout_seconds,
    frontend_operator_surface_checks,
    frontend_probe_semantic_failure,
    frontend_probe_targets,
    frontend_running_probe_targets,
)


@dataclass
class _Context:
    run_id: str = "run-123"
    work_item: str = "item-456"
    prepared_working_copy: object | None = None


PRIMARY_OUTPUTS = {"plan": "plan.md"}


@pytest.mark.parametrize(
    ("name", "probe", "phase", "expected"),
    (
        ("page", {"ok": True, "body_preview": ""}, "post-stage", "UI page body is empty"),
        ("run-api", {"ok": True}, "post-stage", "API probe did not return a JSON object"),
        (
            "run-api",
            {"ok": True, "json_payload": {"run_id": "other"}},
            "post-stage",
            "run API response does not include current run_id",
        ),
        (
            "dashboard-api",
            {
                "ok": True,
                "json_payload": {
                    "dashboard": {
                        "run_id": "run-123",
                        "work_item": "item-456",
                        "stage": "plan",
                        "next_action": {"action": "run-stage", "enabled": True},
                    }
                },
            },
            "running-stage",
            "dashboard next action is not the running-stage wait state",
        ),
        (
            "stage-api",
            {"ok": True, "json_payload": {"run_id": "run-123", "stage": "plan"}},
            "post-stage",
            "stage API response does not include stage status/state",
        ),
        (
            "questions-api",
            {"ok": True, "json_payload": {"stage": "plan"}},
            "post-stage",
            "questions API response does not expose question state",
        ),
        (
            "logs-api",
            {"ok": True, "json_payload": {"stage": "plan"}},
            "post-stage",
            "logs API response does not expose log data",
        ),
        (
            "artifacts-api",
            {"ok": True, "json_payload": {"stage": "plan"}},
            "post-stage",
            "artifacts API response does not expose artifact list",
        ),
        (
            "tasks-api",
            {"ok": True, "json_payload": {"run_id": "run-123", "tasks": []}},
            "post-stage",
            "tasks API response does not expose task projection",
        ),
        (
            "run-api",
            {"ok": False, "status": 503},
            "post-stage",
            "probe returned non-2xx response",
        ),
    ),
)
def test_frontend_probe_semantic_failure_matrix(
    name: str,
    probe: dict[str, object],
    phase: str,
    expected: str,
) -> None:
    assert (
        frontend_probe_semantic_failure(
            ctx=_Context(),
            stage="plan",
            name=name,
            probe=probe,
            phase=phase,
            primary_stage_outputs=PRIMARY_OUTPUTS,
        )
        == expected
    )


def test_frontend_probe_semantic_failure_accepts_valid_running_dashboard() -> None:
    probe = {
        "ok": True,
        "json_payload": {
            "dashboard": {
                "run_id": "run-123",
                "work_item": "item-456",
                "stage": "plan",
                "next_action": {
                    "action": "wait-for-stage",
                    "enabled": False,
                    "stage": "plan",
                },
            }
        },
    }

    assert (
        frontend_probe_semantic_failure(
            ctx=_Context(),
            stage="plan",
            name="dashboard-api",
            probe=probe,
            phase="running-stage",
            primary_stage_outputs=PRIMARY_OUTPUTS,
        )
        is None
    )


def test_frontend_probe_targets_preserve_public_endpoint_order() -> None:
    targets = frontend_probe_targets(_Context(), "plan", primary_stage_outputs=PRIMARY_OUTPUTS)
    running_targets = frontend_running_probe_targets(_Context(), "plan")

    assert [name for name, _path in targets] == [
        "page",
        "dashboard-api",
        "run-api",
        "stage-api",
        "questions-api",
        "logs-api",
        "artifacts-api",
    ]
    assert [name for name, _path in running_targets] == [
        "page",
        "dashboard-api",
        "run-api",
        "stage-api",
        "logs-api",
    ]


def test_frontend_checkpoint_timeout_classification_is_phase_stable() -> None:
    assert frontend_checkpoint_timeout_seconds("post-stage") == 100.0
    assert frontend_checkpoint_timeout_seconds("running-stage") == 80.0
    assert frontend_checkpoint_timed_out(
        failure_reason=None,
        probes=({"error": "request timed out"},),
    )
    assert not frontend_checkpoint_timed_out(failure_reason="connection refused", probes=())


def test_running_surface_requires_disabled_wait_action_and_log_affordance() -> None:
    probes = [
        {"name": "page", "body_preview": "AIDD Operator Console", "ok": True},
        {
            "name": "run-api",
            "json_payload": {"run_id": "run-123", "work_item": "item-456"},
        },
        {
            "name": "dashboard-api",
            "json_payload": {
                "dashboard": {
                    "stage": "plan",
                    "next_action": {"action": "wait-for-stage", "enabled": False, "stage": "plan"},
                }
            },
        },
        {"name": "stage-api", "json_payload": {"stage": "plan", "status": "executing"}},
        {"name": "logs-api", "json_payload": {"available": False}},
    ]

    result = frontend_operator_surface_checks(
        ctx=_Context(),
        stage="plan",
        probes=probes,
        primary_stage_outputs=PRIMARY_OUTPUTS,
    )
    assert result["ok"] is False
    assert "artifact-surface-visible" in result["failed_checks"]
