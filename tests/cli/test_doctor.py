from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aidd.adapters.base import CapabilityReport
from aidd.adapters.surface import get_runtime_adapter_surface
from aidd.cli import main as cli_main

runner = CliRunner()

_CURRENT_DOCTOR_FOOTER = (
    "Adapter probe checks transport availability; execution readiness checks "
    "the configured AIDD command and mode."
)


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            'root = ".aidd"\n\n'
            "[runtime.generic_cli]\n"
            'command = "python-generic"\n\n'
            "[runtime.claude_code]\n"
            'command = "claude-fake"\n\n'
            "[runtime.codex]\n"
            'command = "codex-fake"\n\n'
            "[runtime.opencode]\n"
            'command = "opencode-fake"\n'
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


def test_doctor_reports_current_footer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_config(tmp_path)
    doctor_module = importlib.import_module("aidd.cli.doctor")
    monkeypatch.setattr(
        doctor_module,
        "get_runtime_adapter_surface",
        lambda runtime_id: replace(
            get_runtime_adapter_surface(runtime_id),
            probe=lambda command: _fake_capability_report(runtime_id, command),
        ),
    )

    result = runner.invoke(cli_main.app, ["doctor", "--config", str(config_path)])

    assert result.exit_code == 0, result.output
    normalized_stdout = " ".join(result.stdout.split())
    expected_footer = " ".join(_CURRENT_DOCTOR_FOOTER.split())
    assert expected_footer in normalized_stdout
