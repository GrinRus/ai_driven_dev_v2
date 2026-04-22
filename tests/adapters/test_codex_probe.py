from __future__ import annotations

import sys
from pathlib import Path

from aidd.adapters.codex.probe import discover_command, discover_version, probe


def test_discover_command_supports_arguments() -> None:
    discovered = discover_command(f"{sys.executable} --version")
    assert discovered == sys.executable


def test_discover_command_returns_none_for_invalid_syntax() -> None:
    assert discover_command('"unterminated') is None


def test_discover_version_reads_python_version() -> None:
    version = discover_version(sys.executable)
    assert version is not None
    assert "Python" in version


def test_probe_marks_missing_command_unavailable() -> None:
    report = probe("definitely-missing-aidd-codex-command")
    assert report.available is False
    assert report.command == "definitely-missing-aidd-codex-command"
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
    assert report.supports_subagents is True


def test_probe_handles_nonzero_version_command(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake-codex-cli"
    fake_cli.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo \"codex-cli 0.1.0\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "echo \"ok\"\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)

    report = probe(str(fake_cli))
    assert report.available is True
    assert report.version_text == "codex-cli 0.1.0"
