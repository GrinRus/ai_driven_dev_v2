from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from browser_tests.browser_harness import BrowserDiagnostics
from browser_tests.rendered_assertions import collect_accessibility_violations
from browser_tests.rendered_geometry import collect_geometry_violations

SCHEMA_VERSION = 1
DEFAULT_DIAGNOSTIC_LIMIT = 100
DEFAULT_VALUE_LIMIT = 500
_SAFE_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")


@dataclass(frozen=True, slots=True)
class BrowserCleanupStatus:
    page_closed: bool
    context_closed: bool
    browser_closed: bool
    server_stopped: bool
    workspace_removed: bool


@dataclass(frozen=True, slots=True)
class BrowserViewportEvidence:
    fixture: str
    viewport_width: int
    viewport_height: int
    document_width: int
    document_height: int
    screenshot_path: str
    dom_measurements: dict[str, Any]
    console_errors: tuple[str, ...]
    page_errors: tuple[str, ...]
    failed_requests: tuple[str, ...]
    blocked_requests: tuple[str, ...]
    http_statuses: tuple[tuple[str, int], ...]
    dropped_diagnostics: int
    accessibility_results: tuple[str, ...]
    geometry_results: tuple[str, ...]


_DOM_MEASUREMENTS = r"""
() => {
  const bounds = (element) => {
    const rect = element.getBoundingClientRect();
    return {
      selector: element.id ? `#${CSS.escape(element.id)}` : element.tagName.toLowerCase(),
      left: Number(rect.left.toFixed(1)),
      top: Number(rect.top.toFixed(1)),
      width: Number(rect.width.toFixed(1)),
      height: Number(rect.height.toFixed(1)),
    };
  };
  return {
    sticky_headers: Array.from(document.querySelectorAll("[data-aidd-sticky-header]"))
      .map(bounds),
    primary_actions: Array.from(document.querySelectorAll("[data-aidd-primary-action]"))
      .map(bounds),
    scroll_owners: Array.from(document.querySelectorAll("body *"))
      .filter((element) => {
        const style = getComputedStyle(element);
        return ["auto", "scroll"].includes(style.overflowY)
          && element.scrollHeight > element.clientHeight + 1;
      })
      .map(bounds),
  };
}
"""


class BrowserEvidenceWriter:
    def __init__(
        self,
        root: Path,
        *,
        diagnostic_limit: int = DEFAULT_DIAGNOSTIC_LIMIT,
        value_limit: int = DEFAULT_VALUE_LIMIT,
    ) -> None:
        if diagnostic_limit < 1 or value_limit < 1:
            raise ValueError("browser evidence bounds must be positive")
        self.root = root
        self.diagnostic_limit = diagnostic_limit
        self.value_limit = value_limit
        self._viewports: list[BrowserViewportEvidence] = []

    def _bounded_values(self, values: list[str]) -> tuple[tuple[str, ...], int]:
        retained = tuple(value[: self.value_limit] for value in values[: self.diagnostic_limit])
        return retained, max(0, len(values) - len(retained))

    def capture(
        self,
        *,
        fixture: str,
        page: Page,
        diagnostics: BrowserDiagnostics,
    ) -> BrowserViewportEvidence:
        if _SAFE_NAME.fullmatch(fixture) is None:
            raise ValueError(f"unsafe browser fixture name: {fixture!r}")
        viewport = page.viewport_size
        if viewport is None:
            raise ValueError("browser evidence requires an explicit viewport")
        screenshot_root = self.root / "screenshots"
        screenshot_root.mkdir(parents=True, exist_ok=True)
        screenshot_name = f"{fixture}-{viewport['width']}x{viewport['height']}.png"
        screenshot_path = screenshot_root / screenshot_name
        page.screenshot(path=screenshot_path, full_page=False)

        console_errors, console_dropped = self._bounded_values(diagnostics.console_errors)
        page_errors, page_dropped = self._bounded_values(diagnostics.page_errors)
        failed_requests, failed_dropped = self._bounded_values(diagnostics.failed_requests)
        blocked_requests, blocked_dropped = self._bounded_values(diagnostics.blocked_requests)
        statuses = tuple(diagnostics.http_statuses[: self.diagnostic_limit])
        status_dropped = max(0, len(diagnostics.http_statuses) - len(statuses))
        document_size = page.evaluate(
            "() => ({width: document.documentElement.scrollWidth, "
            "height: document.documentElement.scrollHeight})"
        )
        record = BrowserViewportEvidence(
            fixture=fixture,
            viewport_width=viewport["width"],
            viewport_height=viewport["height"],
            document_width=document_size["width"],
            document_height=document_size["height"],
            screenshot_path=screenshot_path.relative_to(self.root).as_posix(),
            dom_measurements=page.evaluate(_DOM_MEASUREMENTS),
            console_errors=console_errors,
            page_errors=page_errors,
            failed_requests=failed_requests,
            blocked_requests=blocked_requests,
            http_statuses=statuses,
            dropped_diagnostics=(
                console_dropped
                + page_dropped
                + failed_dropped
                + blocked_dropped
                + status_dropped
            ),
            accessibility_results=tuple(
                violation.render()
                for violation in collect_accessibility_violations(page)
            ),
            geometry_results=tuple(
                violation.render() for violation in collect_geometry_violations(page)
            ),
        )
        self._viewports.append(record)
        return record

    def commit(self, *, cleanup: BrowserCleanupStatus) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        report_path = self.root / "browser-evidence.json"
        temporary_path = report_path.with_suffix(".json.tmp")
        payload = {
            "schema_version": SCHEMA_VERSION,
            "viewports": [asdict(record) for record in self._viewports],
            "cleanup": asdict(cleanup),
        }
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(report_path)
        return report_path
