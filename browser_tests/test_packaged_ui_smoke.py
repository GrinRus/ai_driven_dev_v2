from __future__ import annotations

import os
import re
import selectors
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

_INSTALL_COMMAND = "uv run --extra dev python -m playwright install chromium"
_UI_URL = re.compile(r"AIDD UI: (http://127\.0\.0\.1:\d+/)")


@contextmanager
def _smoke_ui(project_root: Path) -> Iterator[str]:
    process = subprocess.Popen(
        [
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
        ],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=os.name == "posix",
    )
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + 15.0
    output: list[str] = []
    url: str | None = None
    try:
        while time.monotonic() < deadline and process.poll() is None:
            if not selector.select(timeout=min(0.2, deadline - time.monotonic())):
                continue
            line = process.stdout.readline()
            output.append(line)
            match = _UI_URL.search(line)
            if match:
                url = match.group(1)
                break
        if url is None:
            pytest.fail("UI did not publish a loopback URL: " + "".join(output))
        yield url
    finally:
        selector.close()
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


def test_packaged_operator_ui_launches_in_chromium(tmp_path: Path) -> None:
    with _smoke_ui(tmp_path) as url, sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.fail(f"Chromium is not installed. Run: {_INSTALL_COMMAND}\n{exc}")
        try:
            page = browser.new_page()
            response = page.goto(url, wait_until="networkidle")
            assert response is not None and response.ok
            assert page.title() == "AIDD Operator Console"
            page.locator("#onboardingProjectForm").wait_for(state="visible")
            asset = page.request.get(f"{url}operator.css")
            assert asset.ok
            assert '@import url("/operator-layout.css")' in asset.text()
        finally:
            browser.close()
