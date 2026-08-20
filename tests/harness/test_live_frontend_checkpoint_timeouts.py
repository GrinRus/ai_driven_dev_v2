from __future__ import annotations

import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import ClassVar

import pytest

from aidd.harness import live_e2e_black_box_orchestration as orchestration


class _ProbeProcess:
    def __init__(self, return_code: int | None = None) -> None:
        self.return_code = return_code

    def poll(self) -> int | None:
        return self.return_code


class _DelayedHandler(BaseHTTPRequestHandler):
    delay_seconds: ClassVar[float] = 0.0

    def do_GET(self) -> None:  # noqa: N802
        time.sleep(self.delay_seconds)
        body = b'{"status":"ok"}'
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            return

    def log_message(self, format: str, *args: object) -> None:
        return


def _serve_delayed_response(delay_seconds: float) -> tuple[ThreadingHTTPServer, str]:
    handler = type("DelayedHandler", (_DelayedHandler,), {"delay_seconds": delay_seconds})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}/"


def test_frontend_checkpoint_budgets_cover_cold_start_and_sequential_probes() -> None:
    assert orchestration.FRONTEND_CHECKPOINT_STARTUP_TIMEOUT_SECONDS == 30.0
    assert orchestration.FRONTEND_CHECKPOINT_PROBE_TIMEOUT_SECONDS == 10.0
    assert orchestration._frontend_checkpoint_timeout_seconds("running-stage") == 80.0
    assert orchestration._frontend_checkpoint_timeout_seconds("post-stage") == 100.0


def test_http_probe_accepts_response_beyond_legacy_two_second_boundary() -> None:
    server, url = _serve_delayed_response(2.1)
    try:
        result = orchestration._http_probe(url)
    finally:
        server.shutdown()
        server.server_close()

    assert result["ok"] is True
    assert result["status"] == 200
    assert result["json_payload"] == {"status": "ok"}


def test_http_probe_timeout_is_bounded_and_classified_truthfully() -> None:
    server, url = _serve_delayed_response(0.2)
    started = time.monotonic()
    try:
        result = orchestration._http_probe(url, timeout_seconds=0.02)
    finally:
        duration_seconds = time.monotonic() - started
        server.shutdown()
        server.server_close()

    assert duration_seconds < 1.0
    assert result["ok"] is False
    assert result["status"] is None
    assert "timed out" in str(result["error"]).lower()
    assert orchestration._frontend_checkpoint_timed_out(
        failure_reason="One or more UI/API probes returned a non-2xx response.",
        probes=[result],
    )


def test_task_flow_public_task_probe_retries_transient_connection_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {"ok": False, "status": None, "error": "connection refused"},
        {"ok": True, "status": 200, "json_payload": {"tasks": ["T1"]}},
    ]
    monkeypatch.setattr(orchestration, "_http_probe", lambda _url: responses.pop(0))
    monkeypatch.setattr(orchestration.time, "sleep", lambda _seconds: None)

    payload, surface = orchestration._task_flow_public_task_probe(
        base_url="http://127.0.0.1:12345",
        run_id="run-1",
        process=_ProbeProcess(),  # type: ignore[arg-type]
    )

    assert payload == {"tasks": ["T1"]}
    assert surface["status"] == "read"
    assert surface["attempt_count"] == 2
    assert [item["status"] for item in surface["probe_attempts"]] == [None, 200]  # type: ignore[index]


def test_task_flow_public_task_probe_retains_terminal_unavailable_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        orchestration,
        "_http_probe",
        lambda _url: {"ok": False, "status": None, "error": "connection refused"},
    )
    monkeypatch.setattr(orchestration.time, "sleep", lambda _seconds: None)

    payload, surface = orchestration._task_flow_public_task_probe(
        base_url="http://127.0.0.1:12345",
        run_id="run-1",
        process=_ProbeProcess(),  # type: ignore[arg-type]
    )

    assert payload is None
    assert surface["status"] == "unavailable"
    assert surface["error"] == "connection refused"
    assert surface["attempt_count"] == orchestration.TASK_FLOW_PUBLIC_TASK_PROBE_ATTEMPTS
    assert surface["process_state"] == "running"
    assert len(surface["probe_attempts"]) == orchestration.TASK_FLOW_PUBLIC_TASK_PROBE_ATTEMPTS  # type: ignore[arg-type]
