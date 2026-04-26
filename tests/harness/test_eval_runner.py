from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

from aidd.harness.eval_runner import run_eval_scenario
from aidd.harness.install_artifact import HarnessInstallResult
from aidd.harness.runner import HarnessCommandTranscript

_PRIMARY_OUTPUTS: dict[str, str] = {
    "idea": "idea-brief.md",
    "research": "research-notes.md",
    "plan": "plan.md",
    "review-spec": "review-spec-report.md",
    "tasklist": "tasklist.md",
    "implement": "implementation-report.md",
    "review": "review-report.md",
    "qa": "qa-report.md",
}


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
    write_stage_outputs: tuple[str, ...] = tuple(),
    review_status: str = "approved",
    qa_verdict: str = "ready",
) -> None:
    print_lines = tuple(f"printf '%s\\n' {line!r}" for line in stdout_lines)
    write_outputs_lines: list[str] = []
    for stage in write_stage_outputs:
        output_root = f'.aidd/workitems/$AIDD_HARNESS_WORK_ITEM/stages/{stage}/output'
        primary_filename = _PRIMARY_OUTPUTS[stage]
        if stage == "review":
            primary_content = (
                "# Review Report\n\n"
                f"- Review status: `{review_status}`\n"
                "- Findings: none\n"
            )
        elif stage == "qa":
            primary_content = (
                "# QA Report\n\n"
                f"- QA verdict: `{qa_verdict}`\n"
                "- EV-001: runtime.log\n"
            )
        else:
            primary_content = f"# {stage.title()} Output\n\n- generated for test coverage\n"
        write_outputs_lines.extend(
            (
                f'output_root="{output_root}"',
                'mkdir -p "$output_root"',
                (
                    "printf '%b' '# Stage result\\n\\n- status: succeeded\\n' "
                    '> "$output_root/stage-result.md"'
                ),
                (
                    "printf '%b' '# Validator report\\n\\n## Result\\n\\n- Verdict: `pass`\\n' "
                    '> "$output_root/validator-report.md"'
                ),
                f"printf '%b' {primary_content!r} > \"$output_root/{primary_filename}\"",
            )
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


def _put_fake_provider_on_path(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    executable_name: str,
) -> Path:
    bin_dir = tmp_path / "provider-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    executable_path = bin_dir / executable_name
    executable_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable_path.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir.as_posix()}:{os.environ.get('PATH', '')}")
    return executable_path


def _clear_live_runtime_command_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIDD_EVAL_CLAUDE_CODE_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_CODEX_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_GENERIC_CLI_COMMAND", raising=False)
    monkeypatch.delenv("AIDD_EVAL_OPENCODE_COMMAND", raising=False)


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
    live: bool = False,
    quality_commands: tuple[str, ...] | None = None,
) -> None:
    aidd_invocation: dict[str, object] = {"work_item": work_item}
    if aidd_command is not None:
        aidd_invocation["command"] = list(aidd_command)
    payload = {
        "id": "AIDD-TEST-EVAL-RUNNER",
        "scenario_class": "live-full-flow" if live else "deterministic-stage",
        "feature_size": "small",
        "automation_lane": "manual" if live else "ci",
        "canonical_runtime": runtime_targets[0],
        "task": (
            "Run the installed AIDD operator against the selected issue and preserve "
            "full-flow audit evidence."
            if live
            else "exercise eval orchestration"
        ),
        "repo": {"url": repo_url},
        "setup": {"commands": list(setup_commands)},
        "verify": {"commands": list(verify_commands)},
        "stage_scope": {"start": stage_start, "end": stage_end},
        "interview": {"required": interview_required},
        "runtime_targets": list(runtime_targets),
        "aidd_invocation": aidd_invocation,
    }
    if live:
        payload["feature_source"] = {
            "mode": "curated-issue-pool",
            "selection_policy": "first-listed",
            "issues": [
                {
                    "id": "123",
                    "title": "exercise live issue selection",
                    "url": "https://github.com/example/repo/issues/123",
                    "summary": "Use the first curated issue as the deterministic full-flow seed.",
                    "labels": ["bug", "live-e2e"],
                }
            ],
        }
        payload["quality"] = {
            "commands": list(
                quality_commands or ("printf 'quality\\n' > quality.log",)
            ),
            "rubric_profile": "live-full",
            "require_review_status": "approved",
            "allowed_qa_verdicts": ["ready", "ready-with-risks"],
            "code_review_required": True,
        }
    else:
        payload["feature_source"] = {
            "mode": "fixture-seed",
            "selection_policy": "fixture-owned",
            "fixture_path": "harness/fixtures/minimal-python",
            "seed_id": "eval-runner-fixture-seed",
            "summary": "Use a deterministic local fixture seed for eval runner tests.",
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
    assert (bundle_root / "quality-transcript.json").exists()
    assert (bundle_root / "teardown-transcript.json").exists()
    assert (bundle_root / "issue-selection.json").exists()
    assert (bundle_root / "runtime.log").exists()
    assert (bundle_root / "validator-report.md").exists()
    assert (bundle_root / "verdict.md").exists()
    assert (bundle_root / "quality-report.md").exists()
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
    _write_fake_aidd(fake_aidd, exit_code=0, write_stage_outputs=("plan",))
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
    issue_selection_payload = yaml.safe_load(
        result.bundle_root.joinpath("issue-selection.json").read_text(encoding="utf-8")
    )
    assert issue_selection_payload["selected_issue"] is None
    assert (
        issue_selection_payload["fixture_seed"]["fixture_path"]
        == "harness/fixtures/minimal-python"
    )
    assert issue_selection_payload["scenario_class"] == "deterministic-stage"


def test_eval_runner_live_scenario_uses_installed_artifact_and_writes_install_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name="opencode",
    )
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        write_stage_outputs=tuple(_PRIMARY_OUTPUTS),
    )
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("opencode",),
        work_item="WI-EVAL-LIVE",
        aidd_command=("missing-live-command",),
        stage_start="idea",
        stage_end="qa",
        live=True,
        quality_commands=("printf 'quality\\n' > quality.log",),
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
    assert result.quality_gate == "pass"
    assert result.quality_verdict == "ready"
    issue_selection_payload = yaml.safe_load(
        result.bundle_root.joinpath("issue-selection.json").read_text(encoding="utf-8")
    )
    assert issue_selection_payload["selected_issue"]["id"] == "123"
    quality_transcript_payload = yaml.safe_load(
        result.bundle_root.joinpath("quality-transcript.json").read_text(encoding="utf-8")
    )
    assert quality_transcript_payload["command_count"] == 1
    grader_payload = yaml.safe_load(
        result.bundle_root.joinpath("grader.json").read_text(encoding="utf-8")
    )
    assert grader_payload["execution"]["status"] == "pass"
    assert grader_payload["quality"]["quality_gate"] == "pass"
    assert grader_payload["quality"]["dimension_scores"]["flow_fidelity"]["score"] == 3


def test_eval_runner_live_codex_native_default_passes_without_env_override(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name="codex",
    )
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-codex"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        write_stage_outputs=tuple(_PRIMARY_OUTPUTS),
    )
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-codex.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("codex",),
        work_item="WI-EVAL-LIVE-CODEX",
        aidd_command=("missing-live-command",),
        stage_start="idea",
        stage_end="qa",
        live=True,
        quality_commands=("printf 'quality\\n' > quality.log",),
    )
    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_local_wheel_install",
        lambda *, workspace_root, run_id: _install_result_for_fake_aidd(fake_aidd),
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="codex",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "pass"
    metadata_payload = yaml.safe_load(
        result.bundle_root.joinpath("harness-metadata.json").read_text(encoding="utf-8")
    )
    working_copy_path = Path(metadata_payload["execution_context"]["target_repository_cwd"])
    live_config_text = (working_copy_path / "aidd.example.toml").read_text(encoding="utf-8")
    assert 'command = "codex exec --full-auto --skip-git-repo-check --json -"' in live_config_text
    assert 'mode = "native"' in live_config_text


def test_eval_runner_live_missing_native_provider_fails_before_repo_prep(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    monkeypatch.setenv("PATH", "")
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-missing-provider.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("codex",),
        work_item="WI-EVAL-LIVE-MISSING-PROVIDER",
        aidd_command=("missing-live-command",),
        stage_start="idea",
        stage_end="qa",
        live=True,
    )
    repo_prep_called = False

    def _unexpected_repo_prep(**_: object) -> object:
        nonlocal repo_prep_called
        repo_prep_called = True
        raise AssertionError("repo prep should not run when provider preflight fails")

    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_scenario_repository",
        _unexpected_repo_prep,
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="codex",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    assert repo_prep_called is False
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "Live runtime command executable is not available" in verdict_text


def test_eval_runner_live_scenario_writes_runtime_config_for_published_package_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-published"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        write_stage_outputs=tuple(_PRIMARY_OUTPUTS),
    )
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
        stage_start="idea",
        stage_end="qa",
        live=True,
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


def test_eval_runner_live_quality_failure_does_not_change_execution_verdict(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name="opencode",
    )
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-quality-fail"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        write_stage_outputs=tuple(_PRIMARY_OUTPUTS),
    )
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-live-quality-fail.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("opencode",),
        work_item="WI-EVAL-LIVE-QUALITY-FAIL",
        aidd_command=("missing-live-command",),
        stage_start="idea",
        stage_end="qa",
        live=True,
        quality_commands=("exit 11",),
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
    assert result.quality_gate == "fail"
    quality_transcript_payload = yaml.safe_load(
        result.bundle_root.joinpath("quality-transcript.json").read_text(encoding="utf-8")
    )
    assert quality_transcript_payload["command_count"] == 0
    quality_report = result.quality_report_path.read_text(encoding="utf-8")
    assert "quality commands failed" in quality_report


def test_eval_runner_live_generic_cli_uses_release_proof_helper_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
    source_repo = tmp_path / "source"
    _init_source_repo(source_repo)
    fake_aidd = tmp_path / "fake-aidd-live-generic"
    _write_fake_aidd(
        fake_aidd,
        exit_code=0,
        write_stage_outputs=tuple(_PRIMARY_OUTPUTS),
    )
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
        stage_start="idea",
        stage_end="qa",
        live=True,
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
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_live_runtime_command_env(monkeypatch)
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
        stage_start="idea",
        stage_end="qa",
        live=True,
    )
    repo_prep_called = False

    def _unexpected_repo_prep(**_: object) -> object:
        nonlocal repo_prep_called
        repo_prep_called = True
        raise AssertionError("repo prep should not run when live preflight fails")

    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_scenario_repository",
        _unexpected_repo_prep,
    )

    result = run_eval_scenario(
        scenario_path=scenario_path,
        runtime_id="generic-cli",
        workspace_root=tmp_path / ".aidd",
    )

    assert result.status == "fail"
    assert repo_prep_called is False
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
    _write_fake_aidd(fake_aidd, exit_code=0, write_stage_outputs=("idea", "plan"))
    scenario_dir = tmp_path / "harness" / "scenarios" / "live"
    scenario_dir.mkdir(parents=True)
    scenario_path = scenario_dir / "scenario-missing-outputs.yaml"
    _write_scenario_manifest(
        path=scenario_path,
        repo_url=source_repo.as_uri(),
        setup_commands=("printf 'setup\\n' > setup.log",),
        verify_commands=("printf 'verify\\n' > verify.log",),
        interview_required=False,
        runtime_targets=("opencode",),
        work_item="WI-EVAL-MISSING-OUTPUTS",
        aidd_command=("missing-live-command",),
        stage_start="idea",
        stage_end="qa",
        live=True,
    )
    monkeypatch = pytest.MonkeyPatch()
    _clear_live_runtime_command_env(monkeypatch)
    _put_fake_provider_on_path(
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        executable_name="opencode",
    )
    monkeypatch.setattr(
        "aidd.harness.eval_runner.prepare_local_wheel_install",
        lambda *, workspace_root, run_id: _install_result_for_fake_aidd(fake_aidd),
    )
    try:
        result = run_eval_scenario(
            scenario_path=scenario_path,
            runtime_id="opencode",
            workspace_root=tmp_path / ".aidd",
        )
    finally:
        monkeypatch.undo()

    assert result.status == "fail"
    verdict_text = result.verdict_path.read_text(encoding="utf-8")
    assert "- Status: `fail`" in verdict_text
    assert "Required stage output artifacts are missing" in verdict_text
