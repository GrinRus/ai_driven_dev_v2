from __future__ import annotations

import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, Request, Route
from playwright.sync_api import Error as PlaywrightError

INSTALL_COMMAND = "uv run --extra dev python -m playwright install chromium"
VIEWPORTS: tuple[tuple[int, int], ...] = (
    (320, 568),
    (390, 844),
    (768, 1024),
    (1280, 900),
    (1440, 900),
)
_UI_URL = re.compile(r"AIDD UI: (http://127\.0\.0\.1:\d+/)")


@dataclass
class BrowserDiagnostics:
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)
    cancelled_requests: list[str] = field(default_factory=list)
    http_statuses: list[tuple[str, int]] = field(default_factory=list)
    blocked_requests: list[str] = field(default_factory=list)

    def assert_clean(self) -> None:
        assert self.console_errors == []
        assert self.page_errors == []
        assert self.failed_requests == []
        assert self.blocked_requests == []
        assert all(status < 400 for _, status in self.http_statuses)


@dataclass(frozen=True)
class BrowserPage:
    page: Page
    context: BrowserContext
    diagnostics: BrowserDiagnostics
    viewport: tuple[int, int]


class OperatorBrowserHarness:
    def __init__(self, *, browser: Browser, url: str, server_process: subprocess.Popen[str]):
        self.browser = browser
        self.url = url
        self.server_process = server_process
        self._contexts: list[BrowserContext] = []

    @contextmanager
    def open_page(self, viewport: tuple[int, int]) -> Iterator[BrowserPage]:
        width, height = viewport
        context = self.browser.new_context(viewport={"width": width, "height": height})
        self._contexts.append(context)
        page = context.new_page()
        diagnostics = BrowserDiagnostics()
        origin = urlsplit(self.url)
        expected_origin = (origin.scheme, origin.hostname, origin.port)

        def _route(route: Route) -> None:
            request_url = route.request.url
            parsed = urlsplit(request_url)
            if parsed.scheme in {"about", "data", "blob"}:
                route.continue_()
                return
            if (parsed.scheme, parsed.hostname, parsed.port) != expected_origin:
                diagnostics.blocked_requests.append(request_url)
                route.abort("blockedbyclient")
                return
            route.continue_()

        page.route("**/*", _route)
        page.on(
            "console",
            lambda message: diagnostics.console_errors.append(message.text)
            if message.type == "error"
            else None,
        )
        page.on("pageerror", lambda error: diagnostics.page_errors.append(str(error)))

        def _record_request_failure(request: Request) -> None:
            request_url = request.url
            failure = request.failure or "unknown failure"
            entry = f"{request_url}: {failure}"
            if failure == "net::ERR_ABORTED":
                diagnostics.cancelled_requests.append(entry)
                return
            diagnostics.failed_requests.append(entry)

        page.on(
            "requestfailed",
            _record_request_failure,
        )
        page.on(
            "response",
            lambda response: diagnostics.http_statuses.append((response.url, response.status)),
        )
        try:
            yield BrowserPage(
                page=page,
                context=context,
                diagnostics=diagnostics,
                viewport=viewport,
            )
        finally:
            context.close()
            self._contexts.remove(context)

    def close(self) -> None:
        for context in reversed(self._contexts):
            context.close()
        self._contexts.clear()
        self.browser.close()


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait(timeout=5.0)


def _start_ui(
    project_root: Path,
    *,
    work_item: str | None,
    timeout: float,
) -> tuple[str, subprocess.Popen[str]]:
    command = [
        sys.executable,
        "-m",
        "aidd.cli.main",
        "ui",
        "--host",
        "127.0.0.1",
        "--port",
        "0",
        "--root",
        ".aidd",
    ]
    if work_item is not None:
        command.extend(("--work-item", work_item))
    process = subprocess.Popen(
        command,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=os.name == "posix",
    )
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + timeout
    output: list[str] = []
    try:
        while time.monotonic() < deadline and process.poll() is None:
            remaining = deadline - time.monotonic()
            if not selector.select(timeout=min(0.2, remaining)):
                continue
            line = process.stdout.readline()
            output.append(line)
            match = _UI_URL.search(line)
            if match:
                return match.group(1), process
    finally:
        selector.close()
    _terminate_process_group(process)
    pytest.fail("UI did not publish a loopback URL before the deadline: " + "".join(output))


@contextmanager
def operator_browser_harness(
    project_root: Path,
    playwright: Playwright,
    *,
    work_item: str | None = None,
    startup_timeout: float = 15.0,
) -> Iterator[OperatorBrowserHarness]:
    project_root.mkdir(parents=True, exist_ok=True)
    workspace_root = project_root / ".aidd"
    url, server_process = _start_ui(
        project_root,
        work_item=work_item,
        timeout=startup_timeout,
    )
    try:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.fail(f"Chromium is not installed. Run: {INSTALL_COMMAND}\n{exc}")
        harness = OperatorBrowserHarness(
            browser=browser,
            url=url,
            server_process=server_process,
        )
        try:
            yield harness
        finally:
            harness.close()
    finally:
        _terminate_process_group(server_process)
        shutil.rmtree(workspace_root, ignore_errors=True)
