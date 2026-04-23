from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from aidd.harness.eval_runner import run_eval_scenario
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.runner import HarnessCommandTranscript


def _run(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_source_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", path.as_posix()])
    _run(["git", "config", "user.email", "tests@example.com"], cwd=path)
    _run(["git", "config", "user.name", "AIDD Tests"], cwd=path)
    (path / "README.md").write_text("repo\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-m", "init"], cwd=path)


def _write_fake_aidd(
    path: Path,
    *,
    exit_code: int,
    stdout_lines: tuple[str, ...] = ("fake aidd",),
    write_plan_outputs: bool = False,
) -> None:
    print_lines = tuple(f"printf '%s\\n' {line!r}" for line in stdout_lines)
    write_outputs_lines: tuple[str, ...] = tuple()
    if write_plan_outputs:
        write_outputs_lines = (
            "output_root=\".aidd/workitems/$AIDD_HARNESS_WORK_ITEM/stages/plan/output\"",
            "mkdir -p \"$output_root\"",
            (
                "printf '# Stage result\\n\\n- status: succeeded\\n' "
                "> \"$output_root/stage-result.md\""
            ),
            (
                "printf '# Validator report\\n\\n## Result\\n\\n- Verdict: `pass`\\n' "
                "> \"$output_root/validator-report.md\""
            ),
        )
    path.write_text(
        "\n".join(
            (
                "#!/bin/sh",
                *print_lines,
                *write_outputs_lines,
                f"exit {exit_code}",
            )
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _write_scenario_manifest(
    *,
    path: Path,
    repo_url: str,
    setup_commands: tuple[str, ...],
    verify_commands: tuple[str, ...],
    interview_required: bool,
    runtime_targets: tuple[str, ...] = ("opencode",),
    work_item: str = "WI-EVAL-RUNNER",
    aidd_command: tuple[str, ...] | None = None,
    stage_start: str = "plan",
    stage_end: str = "plan",
    workflow_bundle: dict[str, object] | None = None,
) -> None:
    aidd_invocation: dict[str, object] = {"work_item": work_item}
    if aidd_command is not None:
        aidd_invocation["command"] = list(aidd_command)
    payload = {
        "id": "AIDD-TEST-EVAL-RUNNER",
        "task": "exercise eval orchestration",
        "repo": {"url": repo_url},
        "setup": {"commands": list(setup_commands)},
        "verify": {"commands": list(verify_commands)},
        "stage_scope": {"start": stage_start, "end": stage_end},
        "interview": {"required": interview_required},
        "runtime_targets": list(runtime_targets),
        "aidd_invocation": aidd_invocation,
    }
    if workflow_bundle is not None:
        payload["workflow_bundle"] = workflow_bundle
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _assert_bundle_basics(bundle_root: Path) -> None:
    assert (bundle_root / "harness-metadata.json").exists()
    assert (bundle_root / "install-transcript.json").exists()
    assert (bundle_root / "setup-transcript.json").exists()
    assert (bundle_root / "run-transcript.json").exists()
    assert (bundle_root / "verify-transcript.json").exists()
    assert (bundle_root / "teardown-transcript.json").exists()
    assert (bundle_root / "runtime.log").exists()
    assert (bundle_root / "validator-report.md").exists()
    assert (bundle_root / "verdict.md").exists()
    assert (bundle_root / "summary.md").exists()
    assert (bundle_root / "log-analysis.md").exists()
    assert (bundle_root / "grader.json").exists()


def _install_result_for_fake_aidd(fake_aidd: Path) -> HarnessInstallResult:
    return HarnessInstallResult(
        install_channel="uv-tool",
        artifact_source="local-wheel",
        artifact_identity="ai_driven_dev_v2-test.whl",
        artifact_path=fake_aidd,
        install_home=fake_aidd.parent / "install-home",
        tool_bin_dir=fake_aidd.parent,
        installed_command=(fake_aidd.as_posix(),),
        command_transcripts=(
            HarnessCommandTranscript(
                command="uv tool install --force /tmp/ai_driven_dev_v2-test.whl",
                exit_code=0,
                stdout_text="installed\n",
                stderr_text="",
                duration_seconds=0.25,
            ),
        ),
        duration_seconds=0.25,
    )


def _install_result_for_fake_published_aidd(
    fake_aidd: Path,
    *,
    artifact_identity: str = "ai-driven-dev-v2==9.9.9",
) -> HarnessInstallResult:
    return HarnessInstallResult(
        install_channel="uv-tool",
        artifact_source="published-package",
        artifact_identity=artifact_identity,
        artifact_path=None,
        install_home=fake_aidd.parent / "install-home",
        tool_bin_dir=fake_aidd.parent,
        installed_command=(fake_aidd.as_posix(),),
        command_transcripts=(
            HarnessCommandTranscript(
                command=f"uv tool install --force {artifact_identity}",
                exit_code=0,
                stdout_text="installed\n",
                stderr_text="",
                duration_seconds=0.25,
            ),
        ),
        duration_seconds=0.25,
    )


def test_eval_runner_pass_status(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd"
    _write_fake_aidd(fake_aidd, exit_code=0, write_plan_outputs=True)
    scenario_path = tmp_path / "scenario-pass.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-PASS",
        aidd_command=(fake_aidd.as_posix(),),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    assert result.first_failure_boundary.category == "none"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `pass`" in verdict_text


def test_eval_runner_live_scenario_uses_installed_artifact_and_writes_install_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live"
    _write_fake_aidd(fake_aidd, exit_code=0, write_plan_outputs=True)
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-LIVE",
        aidd_command=("missing-live-command",),
    )
    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_local_wheel_install",
        lambda *, workspace_root, run_id: _install_result_for_fake_aidd(fake_aidd),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    _assert_bundle_basics(result.bundle_root)
    metadata_payload = yaml.safe_load(
        result.bundle_root.joinpath("harness-metadata.json").read_text(encoding="utf-8")
    )
    install_payload = yaml.safe_load(
        result.bundle_root.joinpath("install-transcript.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["aidd_install"]["install_channel"] == "uv-tool"
    assert metadata_payload["aidd_install"]["artifact_source"] == "local-wheel"
    assert metadata_payload["execution_context"]["resource_source"] == "packaged"
    assert result.run_id in metadata_payload["execution_context"]["target_repository_cwd"]
    assert install_payload["step"] == "install"
    assert install_payload["command_count"] == 1


def test_eval_runner_live_scenario_writes_runtime_config_for_published_package_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-published"
    _write_fake_aidd(fake_aidd, exit_code=0, write_plan_outputs=True)
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-published.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("generic-cli",),
        work_item="WI-EVAL-LIVE-PUBLISHED",
        aidd_command=("missing-live-command",),
    )
    monkeypatch.setenv("AIDD_EVAL_PUBLISHED_PACKAGE_SPEC", "ai-driven-dev-v2==9.9.9")
    monkeypatch.setenv(
        "AIDD_EVAL_GENERIC_CLI_COMMAND",
        "python /tmp/release-live-proof-runtime.py",
    )
    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_published_package_install",
        lambda *, workspace_root, run_id, package_spec: _install_result_for_fake_published_aidd(
            fake_aidd,
            artifact_identity=package_spec,
        ),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="generic-cli",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    metadata_payload = yaml.safe_load(
        result.bundle_root.joinpath("harness-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata_payload["aidd_install"]["artifact_source"] == "published-package"
    working_copy_path = Path(metadata_payload["execution_context"]["target_repository_cwd"])
    live_config_path = working_copy_path / "aidd.example.toml"
    assert live_config_path.exists()
    live_config_text = live_config_path.read_text(encoding="utf-8")
    assert '[runtime.generic_cli]' in live_config_text
    assert 'command = "python /tmp/release-live-proof-runtime.py"' in live_config_text


def test_eval_runner_live_generic_cli_uses_release_proof_helper_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-generic"
    _write_fake_aidd(fake_aidd, exit_code=0, write_plan_outputs=True)
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-generic.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("generic-cli",),
        work_item="WI-EVAL-LIVE-GENERIC",
        workflow_bundle={"release_proof_runtime": "generic-cli"},
    )
    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_local_wheel_install",
        lambda *, workspace_root, run_id: _install_result_for_fake_aidd(fake_aidd),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="generic-cli",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    metadata_payload = yaml.safe_load(
        result.bundle_root.joinpath("harness-metadata.json").read_text(encoding="utf-8")
    )
    working_copy_path = Path(metadata_payload["execution_context"]["target_repository_cwd"])
    live_config_text = (working_copy_path / "aidd.example.toml").read_text(encoding="utf-8")
    assert "release_live_proof_runtime.py" in live_config_text


def test_eval_runner_live_generic_cli_requires_explicit_command_source(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-generic-missing-command.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("generic-cli",),
        work_item="WI-EVAL-LIVE-GENERIC-MISSING",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="generic-cli",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "AIDD_EVAL_GENERIC_CLI_COMMAND" in verdict_text


def test_eval_runner_fail_status_for_verification_non_zero(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-fail.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("exit 9",),
        interview_required=False,
        work_item="WI-EVAL-FAIL",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text


def test_eval_runner_fails_for_non_generic_runtime_real_invocation(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-runtime-gate.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-RUNTIME-GATE",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text
    assert "AIDD run exited with non-zero status" in verdict_text


def test_eval_runner_blocked_status_when_answers_file_missing(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-blocked.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=(
            "test -f .aidd/workitems/WI-EVAL-BLOCKED/stages/idea/answers.md",
        ),
        interview_required=True,
        work_item="WI-EVAL-BLOCKED",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "blocked"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `blocked`" in verdict_text


def test_eval_runner_infra_fail_status_for_setup_error(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    scenario_path = tmp_path / "scenario-infra.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("exit 7",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-INFRA",
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "infra-fail"
    _assert_bundle_basics(result.bundle_root)
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `infra-fail`" in verdict_text


def test_eval_runner_fails_when_run_reports_unsupported_runtime_classification(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-unsupported"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        stdout_lines=(
            "AIDD run: work_item=WI-EVAL-UNSUPPORTED runtime=opencode",
            "Failure classification: unsupported-runtime",
        ),
    )
    scenario_path = tmp_path / "scenario-unsupported.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-UNSUPPORTED",
        aidd_command=(fake_aidd.as_posix(),),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text
    assert "unsupported-runtime classification" in verdict_text


def test_eval_runner_fails_when_run_completes_as_noop(tmp_path: Path) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-noop"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        stdout_lines=("Workflow run completed: no runnable stages found.",),
    )
    scenario_path = tmp_path / "scenario-noop.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-NOOP",
        aidd_command=(fake_aidd.as_posix(),),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text
    assert "no-op execution is non-pass" in verdict_text
    assert result.first_failure_boundary.category == "scenario-verification"


def test_eval_runner_fails_pass_status_when_required_outputs_are_missing(
    tmp_path: Path,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-missing-outputs"
    _write_fake_aidd(fake_aidd, exit_code=0)
    scenario_path = tmp_path / "scenario-missing-outputs.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        work_item="WI-EVAL-MISSING-OUTPUTS",
        aidd_command=(fake_aidd.as_posix(),),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="opencode",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text
    assert "Required stage output artifacts are missing" in verdict_text
