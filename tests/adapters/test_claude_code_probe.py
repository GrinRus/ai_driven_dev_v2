from __future__ import annotations

import sys
from pathlib import Path

from aidd.adapters.claude_code.probe import discover_command, probe


def test_discover_command_supports_arguments() -> None:
    discovered = discover_command(f"{sys.executable} --version")
    assert discovered == sys.executable


def test_discover_command_returns_none_for_invalid_syntax() -> None:
    assert discover_command('"unterminated') is None


def test_probe_marks_missing_command_unavailable() -> None:
    report = probe("definitely-missing-aidd-claude-command")
    assert report.available is False
    assert report.command == "definitely-missing-aidd-claude-command"


def test_probe_discovers_existing_command_path() -> None:
    command_name = Path(sys.executable).name
    report = probe(command_name)
    assert report.available is True
    assert Path(report.command).name == command_name
