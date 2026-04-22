from __future__ import annotations

import sys
from pathlib import Path

from aidd.adapters.codex.probe import (
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


def test_discover_version_reads_python_version() -> None:
    version = discover_version(sys.executable)
    assert version is not None
    assert "Python" in version


def test_detect_capability_flags_reads_advertised_flags() -> None:
    help_text = """
    --jsonl stream machine-readable events
    --non-interactive run without prompts
    --resume continue run
    --cwd set working directory
    --env KEY=VALUE inject environment variable
    subagent mode
    """
    flags = detect_capability_flags(help_text)

    assert flags["supports_structured_log_stream"] is True
    assert flags["supports_non_interactive_mode"] is True
    assert flags["supports_resume"] is True
    assert flags["supports_working_directory_control"] is True
    assert flags["supports_env_injection"] is True
    assert flags["supports_subagents"] is True


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
    assert report.supports_subagents is False


def test_probe_handles_nonzero_version_command(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake-codex-cli"
    fake_cli.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo \"codex-cli 0.1.0\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "if [ \"$1\" = \"--help\" ]; then\n"
        "  echo \"--jsonl --non-interactive --resume --cwd --env subagent\"\n"
        "  exit 0\n"
        "fi\n"
        "echo \"ok\"\n",
        encoding="utf-8",
    )
    fake_cli.chmod(0o755)

    report = probe(str(fake_cli))
    assert report.available is True
    assert report.version_text == "codex-cli 0.1.0"
    assert report.supports_structured_log_stream is True
    assert report.supports_non_interactive_mode is True
    assert report.supports_resume is True
    assert report.supports_working_directory_control is True
    assert report.supports_env_injection is True
    assert report.supports_subagents is True


def test_probe_handles_malformed_version_output(tmp_path: Path) -> None:
    fake_cli = tmp_path / "fake-codex-cli-malformed-version"
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
