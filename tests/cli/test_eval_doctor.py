from __future__ import annotations

import os
from pathlib import Path

import yaml
from typer.testing import CliRunner

from aidd.cli.main import app

runner = CliRunner()


def _write_live_scenario(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": "AIDD-LIVE-DOCTOR-TEST",
        "scenario_class": "live-full-flow",
        "feature_size": "small",
        "automation_lane": "manual",
        "canonical_runtime": "codex",
        "task": "exercise eval doctor",
        "repo": {"url": "https://example.invalid/repo.git"},
        "setup": {"commands": ["true"]},
        "verify": {"commands": ["true"]},
        "stage_scope": {"start": "idea", "end": "qa"},
        "runtime_targets": ["codex"],
        "live_flow": {
            "driver": "stepwise-black-box",
            "checkpoint_policy": "after-each-step",
            "answer_policy": "agent-decides",
            "frontend_checkpoints": True,
        },
        "interview": {"required": False},
        "feature_source": {
            "mode": "authored-task-pool",
            "selection_policy": "first-listed",
            "tasks": [
                {
                    "id": "TASK-123",
                    "title": "task",
                    "summary": "task",
                    "intent": "exercise eval doctor",
                    "target_change": "validate runtime readiness",
                    "expected_scope": "test fixture only",
                    "acceptance_criteria": ["doctor passes"],
                    "verification": ["true"],
                    "quality_bar": "doctor evidence is clear",
                    "size_rationale": "small test fixture",
                }
            ],
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_eval_doctor_reports_native_live_readiness(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("AIDD_EVAL_CODEX_COMMAND", raising=False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then exit 0; fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir.as_posix()}:{os.environ.get('PATH', '')}")
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "scenario.yaml"
    _write_live_scenario(scenario_path)

    result = runner.invoke(app, ["eval", "doctor", str(scenario_path), "--runtime", "codex"])

    assert result.exit_code == 0, result.output
    normalized_stdout = " ".join(result.stdout.split())
    assert "Execution readiness" in normalized_stdout
    assert "pass" in normalized_stdout
    assert "native" in normalized_stdout


def test_eval_doctor_reports_codex_native_auth_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("AIDD_EVAL_CODEX_COMMAND", raising=False)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ]; then\n"
        "  echo 'not logged in' >&2\n"
        "  exit 7\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir.as_posix()}:{os.environ.get('PATH', '')}")
    scenario_path = tmp_path / "harness" / "scenarios" / "live" / "scenario.yaml"
    _write_live_scenario(scenario_path)

    result = runner.invoke(app, ["eval", "doctor", str(scenario_path), "--runtime", "codex"])

    assert result.exit_code == 0, result.output
    normalized_stdout = " ".join(result.stdout.split())
    assert "Execution readiness" in normalized_stdout
    assert "fail" in normalized_stdout
    assert "provider-auth" in normalized_stdout
    assert "blocker" in normalized_stdout
