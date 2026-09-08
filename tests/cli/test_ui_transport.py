from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any

import pytest
from test_ui import _service

from aidd.cli import ui as ui_module
from aidd.cli.ui import OperatorUiService
from aidd.cli.ui_transport import OperatorUiTransport
from aidd.core.mutation_lease import RunMutationConflict


def _payload(response: Any) -> object:
    assert response.content_type == "application/json; charset=utf-8"
    return json.loads(response.body.decode("utf-8"))


class _ConflictService(OperatorUiService):
    def _start_stage_job(self, payload: dict[str, Any]) -> object:
        raise RunMutationConflict("Run mutation conflict: characterized transport failure.")


def test_transport_composes_existing_codec_and_router_without_reimplementing_them(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path / ".aidd")

    assert isinstance(service._transport, OperatorUiTransport)
    assert service._transport.router is service._router
    assert "OperatorUiRouter(" not in inspect.getsource(ui_module)
    assert "handler_for(" not in inspect.getsource(ui_module)


@pytest.mark.parametrize("project_name", ["project-a", "project-b"])
def test_transport_endpoint_contracts_are_stable_per_project(
    tmp_path: Path,
    project_name: str,
) -> None:
    service = _service(tmp_path / project_name / ".aidd")

    success = service.handle_get("/api/onboarding/state", {})
    assert success.status == 200
    success_payload = _payload(success)
    assert isinstance(success_payload, dict)
    assert success_payload["setup_required"] is False
    context = success_payload["context"]
    assert isinstance(context, dict)
    assert context["work_item"] == "WI-UI"

    validation = service.handle_post("/api/stage/run", {})
    assert validation.status == 400
    assert _payload(validation) == {"error": "stage is required."}

    not_found = service.handle_get("/api/does-not-exist", {})
    assert not_found.status == 404
    assert _payload(not_found) == {"error": "not found"}


def test_transport_preserves_explicit_failure_shape(tmp_path: Path) -> None:
    service = _ConflictService(_service(tmp_path / ".aidd").options)

    response = service.handle_post(
        "/api/stage/run",
        {"stage": "plan", "runtime": "codex"},
    )

    assert response.status == 409
    assert _payload(response) == {
        "error": "Run mutation conflict: characterized transport failure."
    }
