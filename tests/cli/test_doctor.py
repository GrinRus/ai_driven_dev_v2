from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from aidd.adapters.base import CapabilityReport
from aidd.cli import main as cli_main

runner = CliRunner()

_POST_W9_DOCTOR_FOOTER = (
    "Workflow and stage execution are available on maintained runtimes. "
    "Remaining roadmap work focuses on release-channel verification and "
    "durable non-generic live E2E evidence."
)


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            "root = \".aidd\"\n\n"
            "[runtime.generic_cli]\n"
            "command = \"python-generic\"\n\n"
            "[runtime.claude_code]\n"
            "command = \"claude-fake\"\n\n"
            "[runtime.codex]\n"
            "command = \"codex-fake\"\n\n"
            "[runtime.opencode]\n"
            "command = \"opencode-fake\"\n"
        ),
        encoding="utf-8",
    )
    return config_path


def _fake_capability_report(runtime_id: str, command: str) -> CapabilityReport:
    return CapabilityReport(
        runtime_id=runtime_id,
        available=True,
        command=command,
        version_text="test-version",
        supports_raw_log_stream=True,
        supports_structured_log_stream=False,
        supports_questions=True,
        supports_resume=False,
        supports_subagents=False,
        supports_non_interactive_mode=True,
        supports_working_directory_control=True,
        supports_env_injection=True,
    )


def test_doctor_reports_post_w9_footer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_config(tmp_path)
    monkeypatch.setattr(
        cli_main,
        "probe_generic_cli",
        lambda command: _fake_capability_report("generic-cli", command),
    )
    monkeypatch.setattr(
        cli_main,
        "probe_claude_code",
        lambda command: _fake_capability_report("claude-code", command),
    )
    monkeypatch.setattr(
        cli_main,
        "probe_codex",
        lambda command: _fake_capability_report("codex", command),
    )
    monkeypatch.setattr(
        cli_main,
        "probe_opencode",
        lambda command: _fake_capability_report("opencode", command),
    )

    result = runner.invoke(cli_main.app, ["doctor", "--config", str(config_path)])

    assert result.exit_code == 0, result.output
    normalized_stdout = " ".join(result.stdout.split())
    expected_footer = " ".join(_POST_W9_DOCTOR_FOOTER.split())
    assert expected_footer in normalized_stdout
