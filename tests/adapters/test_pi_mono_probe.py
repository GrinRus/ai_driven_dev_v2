from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from aidd.adapters.pi_mono.probe import (
    detect_capability_flags,
    discover_command,
    discover_version,
    probe,
)


def test_discover_command_supports_arguments() -> None:
    discovered = discover_command(f"{sys.executable} --version")
    assert discovered == sys.executable


def test_discover_command_returns_none_for_invalid_syntax() -> None:
    assert discover_command('"unterminated') is None


def test_discover_version_returns_identity_for_python() -> None:
    version_text = discover_version(sys.executable)
    assert version_text is not None
    assert "Python" in version_text


def test_probe_marks_missing_command_unavailable() -> None:
    report = probe("definitely-missing-aidd-pi-mono-command")
    assert report.available is False
    assert report.command == "definitely-missing-aidd-pi-mono-command"
    assert report.version_text is None
    assert report.supports_raw_log_stream is False
    assert report.supports_subagents is False
    assert report.supports_non_interactive_mode is False


def test_probe_discovers_existing_command_path() -> None:
    command_name = Path(sys.executable).name
    report = probe(command_name)
    assert report.available is True
    assert Path(report.command).name == command_name
    assert report.version_text is not None
    assert report.supports_raw_log_stream is True


def test_detect_capability_flags_parses_help_markers() -> None:
    help_text = "\n".join(
        [
            "Usage: pi-mono --json --resume --non-interactive --cwd PATH --env KEY=VALUE",
            "Subagent mode supported",
            "Ask-user questions interactively",
        ]
    )

    detected = detect_capability_flags(help_text)

    assert detected["supports_structured_log_stream"] is True
    assert detected["supports_questions"] is True
    assert detected["supports_resume"] is True
    assert detected["supports_subagents"] is True
    assert detected["supports_non_interactive_mode"] is True
    assert detected["supports_working_directory_control"] is True
    assert detected["supports_env_injection"] is True


def test_probe_derives_capabilities_from_help_text(monkeypatch: pytest.MonkeyPatch) -> None:
    probe_module = importlib.import_module("aidd.adapters.pi_mono.probe")
    monkeypatch.setattr(probe_module, "discover_command", lambda _: "/tmp/pi-mono")
    monkeypatch.setattr(probe_module, "discover_version", lambda _: "pi-mono 1.2.3")
    monkeypatch.setattr(
        probe_module,
        "discover_help_text",
        lambda _: "pi-mono --json --resume --non-interactive --cwd --env subagent question",
    )

    report = probe_module.probe("pi-mono")

    assert report.available is True
    assert report.version_text == "pi-mono 1.2.3"
    assert report.supports_structured_log_stream is True
    assert report.supports_questions is True
    assert report.supports_resume is True
    assert report.supports_subagents is True
    assert report.supports_non_interactive_mode is True
    assert report.supports_working_directory_control is True
    assert report.supports_env_injection is True


def test_probe_handles_malformed_version_output(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake-pi_mono-cli-malformed-version"
    fake_cli.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo \"???\"\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"--help\" ]; then\n"
        "  echo \"--non-interactive\"\n"
        "  exit 0\n"
        "fi\n"
        "echo \"ok\"\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)

    report = probe(str(fake_cli))

    assert report.available is True
    assert report.version_text == "???"
    assert report.supports_non_interactive_mode is True
