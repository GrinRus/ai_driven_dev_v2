from __future__ import annotations

import json
from pathlib import Path

import pytest

from aidd.harness.result_bundle import (
    copy_or_link_run_artifacts,
    ensure_result_bundle_layout,
    write_command_transcripts,
    write_harness_metadata,
)
from aidd.harness.runner import (
    HarnessAiddRunResult,
    HarnessCommandTranscript,
    HarnessSetupResult,
    HarnessTeardownResult,
    HarnessVerificationResult,
)
from aidd.harness.scenarios import (
    Scenario,
    ScenarioCommandSteps,
    ScenarioRepoSource,
    ScenarioRunConfig,
)


def _build_scenario() -> Scenario:
    return Scenario(
        scenario_id="AIDD-TEST-BUNDLE-COMPLETENESS",
        task="Verify result-bundle completeness",
        repo=ScenarioRepoSource(
            url="https://github.com/example/repo",
            default_branch="main",
            revision=None,
        ),
        setup=ScenarioCommandSteps(commands=("echo setup",)),
        run=ScenarioRunConfig(
            stage_start="plan",
            stage_end="qa",
            runtime_targets=("generic-cli",),
            patch_budget_files=3,
            timeout_minutes=10,
            interview_required=False,
        ),
        verify=ScenarioCommandSteps(commands=("echo verify",)),
        runtime_targets=("generic-cli",),
        raw={"id": "AIDD-TEST-BUNDLE-COMPLETENESS"},
    )


def _build_transcript(*, command: str, exit_code: int = 0) -> HarnessCommandTranscript:
    return HarnessCommandTranscript(
        command=command,
        exit_code=exit_code,
        stdout_text=f"stdout:{command}",
        stderr_text=f"stderr:{command}",
        duration_seconds=0.25,
    )


def _write_run_artifact_sources(
    *, source_root: Path, status: str
) -> tuple[Path, Path, Path]:
    source_root.mkdir(parents=True, exist_ok=True)
    runtime_log_path = source_root / "runtime.log"
    validator_report_path = source_root / "validator-report.md"
    verdict_path = source_root / "verdict.md"
    runtime_log_path.write_text(f"{status}:runtime-log\n", encoding="utf-8")
    validator_report_path.write_text(
        f"# Validator report\n\n- Outcome: `{status}`\n",
        encoding="utf-8",
    )
    verdict_path.write_text(f"# Verdict\n\n{status}\n", encoding="utf-8")
    return runtime_log_path, validator_report_path, verdict_path


def _assert_required_bundle_files(layout_root: Path) -> None:
    required_artifact_names = (
        "harness-metadata.json",
        "install-transcript.json",
        "setup-transcript.json",
        "run-transcript.json",
        "verify-transcript.json",
        "teardown-transcript.json",
        "runtime.log",
        "validator-report.md",
        "verdict.md",
    )
    for artifact_name in required_artifact_names:
        artifact_path = layout_root / artifact_name
        assert artifact_path.exists(), artifact_name
        assert artifact_path.is_file(), artifact_name


@pytest.mark.parametrize(
    ("status", "run_exit_code", "expect_run_command"),
    [
        ("pass", 0, True),
        ("fail", 1, True),
        ("blocked", None, False),
    ],
)
def test_result_bundle_completeness_for_terminal_outcomes(
    tmp_path: Path,
    status: str,
    run_exit_code: int | None,
    expect_run_command: bool,
) -> None:
    run_id = f"eval-run-{status}"
    layout = ensure_result_bundle_layout(workspace_root=tmp_path, run_id=run_id)
    runtime_log_path, validator_report_path, verdict_path = _write_run_artifact_sources(
        source_root=tmp_path / f"sources-{status}",
        status=status,
    )

    aidd_run_result: HarnessAiddRunResult | None = None
    setup_result: HarnessSetupResult | None = None
    verification_result: HarnessVerificationResult | None = None
    teardown_result: HarnessTeardownResult | None = None
    if run_exit_code is not None:
        setup_result = HarnessSetupResult(
            executed_commands=("echo setup",),
            command_transcripts=(_build_transcript(command="echo setup"),),
            duration_seconds=0.25,
        )
        aidd_run_result = HarnessAiddRunResult(
            command=(
                "uv",
                "run",
                "aidd",
                "run",
                "--work-item",
                f"WI-{status}",
                "--runtime",
                "generic-cli",
            ),
            runtime_id="generic-cli",
            work_item=f"WI-{status}",
            exit_code=run_exit_code,
            stdout_text=f"{status}:stdout",
            stderr_text=f"{status}:stderr",
            duration_seconds=1.0,
            command_transcript=_build_transcript(
                command=f"uv run aidd run --work-item WI-{status} --runtime generic-cli",
                exit_code=run_exit_code,
            ),
        )
        verification_result = HarnessVerificationResult(
            executed_commands=("echo verify",),
            aidd_exit_code=run_exit_code,
            command_transcripts=(_build_transcript(command="echo verify"),),
            duration_seconds=0.25,
        )
        teardown_result = HarnessTeardownResult(
            executed_commands=("echo teardown",),
            command_transcripts=(_build_transcript(command="echo teardown"),),
            duration_seconds=0.25,
        )

    write_harness_metadata(
        layout=layout,
        scenario=_build_scenario(),
        runtime_id="generic-cli",
        work_item=f"WI-{status}",
        status=status,
        aidd_run_id=None if aidd_run_result is None else f"run-{status}",
        aidd_run_result=aidd_run_result,
        aidd_artifact_references={"runtime_log": runtime_log_path.as_posix()},
    )
    write_command_transcripts(
        layout=layout,
        setup_result=setup_result,
        aidd_run_result=aidd_run_result,
        verification_result=verification_result,
        teardown_result=teardown_result,
    )
    copy_or_link_run_artifacts(
        layout=layout,
        runtime_log_path=runtime_log_path,
        validator_report_path=validator_report_path,
        verdict_path=verdict_path,
    )

    _assert_required_bundle_files(layout.run_root)

    metadata_payload = json.loads(layout.harness_metadata_path.read_text(encoding="utf-8"))
    run_payload = json.loads(layout.run_transcript_path.read_text(encoding="utf-8"))
    assert metadata_payload["status"] == status
    if expect_run_command:
        assert run_payload["command_count"] == 1
        assert run_payload["exit_code"] == run_exit_code
    else:
        assert run_payload["command_count"] == 0
        assert run_payload["exit_code"] is None
