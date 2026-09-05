from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from aidd.adapters.runtime_artifacts import RUNTIME_EXIT_METADATA_FILENAME
from aidd.cli.main import _active_prompt_pack_paths, _prefix_stream_chunk, app
from aidd.cli.stage_run import (
    StageInteractOptions,
    StageRepairExtensionOptions,
    StageRunOptions,
    _CliRuntimeOperatorDecisionProvider,
    _resolve_stage_run_config,
    _write_run_manifest,
    prepare_stage_interaction,
    run_stage_interact_command,
    run_stage_repair_extension_command,
)
from aidd.config import ProjectConfig, ProjectSetConfig
from aidd.core.project_set import persist_project_set_context, resolve_project_set
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    RUN_RUNTIME_JSONL_FILENAME,
    RUN_RUNTIME_LOG_FILENAME,
    create_run_manifest,
    persist_stage_status,
    run_attempt_artifact_index_path,
)
from aidd.core.runtime_operator import RuntimeOperatorRequest
from aidd.core.stage_runner import prepare_stage_bundle
from aidd.core.workspace import WorkspaceBootstrapService
from aidd.runtime_permissions import (
    RuntimeOperatorDecisionAction,
    RuntimeOperatorDecisionSource,
    RuntimeOperatorRequestKind,
)
from aidd.validators.models import ValidationFinding
from aidd.validators.reports import render_validator_report

runner = CliRunner()


def _materialize_project_set_context(tmp_path: Path, workspace_root: Path, work_item: str) -> None:
    (tmp_path / "services" / "api").mkdir(parents=True)
    (tmp_path / "apps" / "web").mkdir(parents=True)
    persist_project_set_context(
        workspace_root=workspace_root, work_item=work_item,
        project_set=resolve_project_set(
            repository_root=tmp_path,
            project_set=ProjectSetConfig(projects=(
                ProjectConfig(id="api", root=Path("services/api")),
                ProjectConfig(id="web", root=Path("apps/web")),
            )),
        ),
    )


@pytest.mark.parametrize("attempt_mode", ("initial", "repair", "intervention"))
@pytest.mark.parametrize("project_set", (False, True))
def test_substantive_only_runtime_leaves_workflow_records_to_aidd(
    tmp_path: Path, attempt_mode: str, project_set: bool
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SUBSTANTIVE"
    run_id = "run-substantive"
    WorkspaceBootstrapService(root=workspace_root).bootstrap_work_item(work_item=work_item)
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    if project_set:
        _materialize_project_set_context(tmp_path, workspace_root, work_item)
    plan = _valid_plan_output_documents()["plan.md"]
    if attempt_mode == "intervention":
        final_plan = plan.replace(
            "- Risk: Missing constraints; mitigation: clarify assumptions.",
            "- Risk: Migration failure; mitigation: keep a tested rollback path.",
        )
    else:
        final_plan = plan
    initial_plan = "# Plan\n\nIncomplete plan.\n" if attempt_mode == "repair" else plan
    writer = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents={"plan.md": initial_plan},
        next_documents={"plan.md": final_plan},
        exit_code=0,
        extra_stdout_lines=("substantive-only writes=plan.md",),
    )
    config = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer.as_posix())}",
        max_repair_attempts=1 if attempt_mode == "repair" else 0,
    )
    common_args = [
        "plan", "--work-item", work_item, "--runtime", "generic-cli", "--run-id", run_id,
        "--root", str(workspace_root), "--config", str(config), "--no-log-follow",
    ]
    result = runner.invoke(app, ["stage", "run", *common_args])
    assert result.exit_code == 0, result.output
    if attempt_mode != "repair":
        assert "Stage attempts: 1" in result.output
        assert "Repair retry scheduled" not in result.output
    if attempt_mode == "intervention":
        result = runner.invoke(
            app,
            ["stage", "interact", *common_args, "--request", "Add migration rollback risks"],
        )
        assert result.exit_code == 0, result.output
        assert "Repair retry scheduled" not in result.output

    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    output = stage_root / "output"
    assert (output / "plan.md").read_text(encoding="utf-8") == final_plan
    stage_result = (output / "stage-result.md").read_text(encoding="utf-8")
    assert "succeeded" in stage_result
    assert "review-spec" in stage_result
    assert "## Attempt history" in stage_result
    if project_set:
        assert "## Project-set evidence" in stage_result
        assert f"`workitems/{work_item}/context/project-set.md`" in stage_result
        for project_id, root in (("api", "services/api"), ("web", "apps/web")):
            assert f"`{project_id}`" in stage_result
            assert f"`{root}`" in stage_result
    assert "Verdict: `pass`" in (output / "validator-report.md").read_text(encoding="utf-8")
    attempt_number = 1 if attempt_mode == "initial" else 2
    artifact_path = run_attempt_artifact_index_path(
        workspace_root=workspace_root, work_item=work_item, run_id=run_id, stage="plan",
        attempt_number=attempt_number,
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["attempt_mode"] == attempt_mode
    assert "substantive-only writes=plan.md" in (
        artifact_path.parent / RUN_RUNTIME_LOG_FILENAME
    ).read_text(encoding="utf-8")
    if attempt_mode == "repair":
        assert "(`initial`) -> failed validation" in stage_result
        assert "(`repair`) -> succeeded" in stage_result
        assert (stage_root / "repair-brief.md").is_file()
    if attempt_mode == "intervention":
        assert (stage_root / "operator-requests" / "request-0001.md").is_file()


@pytest.mark.parametrize("failure", ("substantive", "lookalike-runtime-draft"))
@pytest.mark.parametrize("project_set", (False, True))
def test_bootstrap_reconciliation_preserves_real_failures_and_runtime_draft_evidence(
    tmp_path: Path, failure: str, project_set: bool
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-BOOTSTRAP-FAIL"
    WorkspaceBootstrapService(root=workspace_root).bootstrap_work_item(work_item=work_item)
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    if project_set:
        _materialize_project_set_context(tmp_path, workspace_root, work_item)
    documents = {"plan.md": _valid_plan_output_documents()["plan.md"]}
    runtime_draft = "# Stage result\n\nStage not run yet.\n\nRuntime-authored extra evidence.\n"
    if failure == "substantive":
        documents["plan.md"] = "# Plan\n\nInvalid substantive output.\n"
    else:
        documents["stage-result.md"] = runtime_draft
    writer = _write_runtime_writer_script(tmp_path=tmp_path, documents=documents, exit_code=0)
    config = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer.as_posix())}",
        max_repair_attempts=0,
    )
    result = runner.invoke(app, [
        "stage", "run", "plan", "--work-item", work_item, "--runtime", "generic-cli",
        "--run-id", "run-bootstrap-fail", "--root", str(workspace_root), "--config", str(config),
        "--no-log-follow",
    ])

    assert result.exit_code == 1, result.output
    assert "action=stop state=failed" in result.output
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    assert not (stage_root / "output" / "plan.md").exists()
    assert (stage_root / "plan.md").read_text(encoding="utf-8") == documents["plan.md"]
    assert "Verdict: `fail`" in (stage_root / "validator-report.md").read_text(encoding="utf-8")
    if failure == "lookalike-runtime-draft":
        artifact_path = run_attempt_artifact_index_path(
            workspace_root=workspace_root, work_item=work_item, run_id="run-bootstrap-fail",
            stage="plan", attempt_number=1,
        )
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        evidence_path = workspace_root / artifact["documents"]["runtime_stage_result_draft"]
        assert evidence_path.read_text(encoding="utf-8") == runtime_draft


@pytest.mark.parametrize("attempt_mode", ("initial", "repair", "intervention"))
@pytest.mark.parametrize("project_set", (False, True))
def test_substantive_only_runtime_routes_completion_blockers_to_interview(
    tmp_path: Path, attempt_mode: str, project_set: bool
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OWNERSHIP-BLOCKED"
    WorkspaceBootstrapService(root=workspace_root).bootstrap_work_item(work_item=work_item)
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    if project_set:
        _materialize_project_set_context(tmp_path, workspace_root, work_item)
    plan = _valid_plan_output_documents()["plan.md"]
    blocked_plan = plan + "\n## Blockers\n\nOperator scope approval is required.\n"
    question = "- Q1 [blocking] May the approved scope expand to include migration fallback?\n"
    blocked_documents = {"plan.md": blocked_plan, "questions.md": "# Questions\n\n" + question}
    first_documents = {
        "initial": blocked_documents,
        "repair": {"plan.md": "# Plan\n\nIncomplete plan.\n"},
        "intervention": {"plan.md": plan},
    }[attempt_mode]
    writer = _write_runtime_writer_script(
        tmp_path=tmp_path, documents=first_documents, next_documents=blocked_documents,
        exit_code=0,
    )
    config = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer.as_posix())}",
        max_repair_attempts=1 if attempt_mode == "repair" else 0,
    )
    common_args = [
        "plan", "--work-item", work_item, "--runtime", "generic-cli", "--run-id", "run-blocked",
        "--root", str(workspace_root), "--config", str(config), "--no-log-follow",
    ]
    result = runner.invoke(app, ["stage", "run", *common_args])
    if attempt_mode == "intervention":
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, [
            "stage", "interact", *common_args, "--request", "Add migration fallback",
        ])

    assert result.exit_code == 1, result.output
    assert "action=wait state=blocked" in result.output
    assert "Blocking questions are unresolved." in result.output
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    stage_result = (stage_root / "stage-result.md").read_text(encoding="utf-8")
    assert "## Status\n\n- Status: `blocked`" in stage_result
    assert "Q1" in stage_result
    assert (stage_root / "plan.md").read_text(encoding="utf-8") == blocked_plan
    assert "[blocking]" in (stage_root / "questions.md").read_text(encoding="utf-8")
    assert "[resolved]" not in (stage_root / "answers.md").read_text(encoding="utf-8")
    published_plan = stage_root / "output" / "plan.md"
    if published_plan.exists():
        assert published_plan.read_text(encoding="utf-8") != blocked_plan


def test_cli_operator_decision_provider_returns_tty_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "s")
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="implement",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "npm install"},
        cwd=tmp_path,
    )

    decision = _CliRuntimeOperatorDecisionProvider().request_decision(
        request,
        requests_path=tmp_path / "operator-requests.jsonl",
        decisions_path=tmp_path / "operator-decisions.jsonl",
    )

    assert decision is not None
    assert decision.request_id == request.id
    assert decision.action is RuntimeOperatorDecisionAction.ALLOW_FOR_SESSION
    assert decision.source is RuntimeOperatorDecisionSource.CLI


def test_cli_operator_decision_provider_no_tty_returns_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    request = RuntimeOperatorRequest.create(
        runtime_id="codex",
        stage="implement",
        kind=RuntimeOperatorRequestKind.SHELL,
        payload={"command": "npm install"},
        cwd=tmp_path,
    )

    decision = _CliRuntimeOperatorDecisionProvider().request_decision(
        request,
        requests_path=tmp_path / "operator-requests.jsonl",
        decisions_path=tmp_path / "operator-decisions.jsonl",
    )

    assert decision is None


def _materialize_plan_inputs(*, workspace_root: Path, work_item: str) -> None:
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
    )
    for index, path in enumerate(bundle.expected_input_bundle, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Input {index}\n\nPrepared.\n", encoding="utf-8")


def _valid_plan_output_documents(
    *,
    include_repair_brief: bool = False,
    repair_trace: bool = False,
) -> dict[str, str]:
    repair_trace_line = "- repaired against `repair-brief.md`\n" if repair_trace else ""
    documents = {
        "plan.md": (
            "# Plan\n\n"
            "## Goals\n\n- Deliver a reviewable execution plan.\n\n"
            "## Out of scope\n\n- Runtime migration is excluded.\n\n"
            "## Milestones\n\n- M1: Draft and validate plan.\n\n"
            "## Implementation strategy\n\n- Use staged, document-first increments.\n\n"
            "## Risks\n\n- Risk: Missing constraints; mitigation: clarify assumptions.\n\n"
            "## Dependencies\n\n- Research artifacts from prior stage.\n\n"
            "## Verification approach\n\n- Run structural and semantic checks.\n\n"
            "## Verification notes\n\n"
            "- M1: Validate highest-risk milestone with targeted tests.\n"
        ),
        "stage-result.md": (
            "# Stage result\n\n"
            "## Stage\n\nplan\n\n"
            "## Attempt history\n\n- attempt-0001\n\n"
            "## Status\n\nsucceeded\n\n"
            "## Produced outputs\n\n- plan.md\n\n"
            f"## Validation summary\n\n- structural: pass\n{repair_trace_line}\n"
            "## Blockers\n\n- none\n\n"
            "## Next actions\n\n- advance\n\n"
            "## Terminal state notes\n\nReady.\n"
        ),
        "validator-report.md": (
            "# Validator Report\n\n"
            "## Summary\n\n- Total issues: 0\n\n"
            "## Structural checks\n\n- none\n\n"
            "## Semantic checks\n\n- none\n\n"
            "## Cross-document checks\n\n- none\n\n"
            "## Result\n\n- Verdict: `pass`\n"
        ),
        "questions.md": "# Questions\n\n- none\n",
        "answers.md": "# Answers\n\n- none\n",
    }
    if include_repair_brief:
        documents["repair-brief.md"] = (
            "# Failed checks\n\n- none\n\n"
            "## Required corrections\n\n- none\n\n"
            "## Relevant upstream docs\n\n- none\n"
        )
    return documents


def _repair_trigger_plan_output_documents() -> dict[str, str]:
    return {
        "plan.md": "# Plan\n\nInsufficient detail for a reviewable plan.\n",
        "stage-result.md": (
            "# Stage result\n\n"
            "## Stage\n\nplan\n\n"
            "## Attempt history\n\n- attempt-0001\n\n"
            "## Status\n\nsucceeded\n\n"
            "## Produced outputs\n\n- plan.md\n\n"
            "## Validation summary\n\n- structural: pending\n\n"
            "## Blockers\n\n- none\n\n"
            "## Next actions\n\n- retry\n\n"
            "## Terminal state notes\n\nNeeds correction.\n"
        ),
        "validator-report.md": (
            "# Validator Report\n\n"
            "## Summary\n\n- Total issues: 3\n\n"
            "## Structural checks\n\n- pending\n\n"
            "## Semantic checks\n\n- pending\n\n"
            "## Cross-document checks\n\n- pending\n\n"
            "## Result\n\n- Verdict: `fail`\n"
        ),
        "questions.md": "# Questions\n\n- none\n",
        "answers.md": "# Answers\n\n- none\n",
    }


def _blocked_question_output_documents() -> dict[str, str]:
    documents = _valid_plan_output_documents()
    documents["questions.md"] = (
        "# Questions\n\n"
        "- `Q1` `[blocking]` Confirm whether the rollout must include migration fallback.\n"
    )
    documents["answers.md"] = "# Answers\n\n- none\n"
    return documents


def _write_runtime_writer_script(
    *,
    tmp_path: Path,
    documents: dict[str, str],
    exit_code: int,
    next_documents: dict[str, str] | None = None,
    extra_stdout_lines: tuple[str, ...] = (),
) -> Path:
    script_path = tmp_path / f"runtime_writer_{exit_code}.py"
    script_lines = [
        "import os",
        "import sys",
        "from pathlib import Path",
        f"first_documents = {documents!r}",
        f"next_documents = {next_documents!r}",
        "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
        (
            "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM'] / "
            "'stages' / os.environ['AIDD_STAGE']"
        ),
        (
            "attempts_root = root / 'reports' / 'runs' / os.environ['AIDD_WORK_ITEM'] / "
            "os.environ['AIDD_RUN_ID'] / 'stages' / os.environ['AIDD_STAGE'] / 'attempts'"
        ),
        (
            "attempt_count = sum("
            "1 for child in attempts_root.iterdir() "
            "if child.is_dir() and child.name.startswith('attempt-')"
            ") if attempts_root.exists() else 0"
        ),
        (
            "documents = first_documents if (attempt_count <= 1 or next_documents is None) "
            "else next_documents"
        ),
        "stage_root.mkdir(parents=True, exist_ok=True)",
        "for name, content in documents.items():",
        "    (stage_root / name).write_text(content, encoding='utf-8')",
        "print('runtime-output-line')",
        *[f"print({line!r})" for line in extra_stdout_lines],
        "print('runtime-error-line', file=sys.stderr)",
        f"raise SystemExit({exit_code})",
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return script_path


def _write_native_runtime_writer_script(
    *,
    tmp_path: Path,
    runtime: str,
    documents: dict[str, str],
) -> Path:
    script_path = tmp_path / f"native_{runtime}_writer.py"
    script_lines = [
        "import os",
        "import sys",
        "from pathlib import Path",
        f"runtime = {runtime!r}",
        f"documents = {documents!r}",
        "args = sys.argv[1:]",
        "if '--stage' in args or '--prompt-pack' in args:",
        "    print('unexpected adapter flag', file=sys.stderr)",
        "    raise SystemExit(31)",
        "if runtime == 'codex':",
        "    stdin_text = sys.stdin.read()",
        "    if '# AIDD stage runtime request' not in stdin_text:",
        "        print('missing stdin stage request', file=sys.stderr)",
        "        raise SystemExit(32)",
        "    if '-' not in args:",
        "        print('missing stdin sentinel', file=sys.stderr)",
        "        raise SystemExit(33)",
        "elif runtime == 'opencode':",
        "    if '--dir' not in args or '--file' not in args:",
        "        print('missing native opencode flags', file=sys.stderr)",
        "        raise SystemExit(34)",
        "    prompt_file = Path(args[args.index('--file') + 1])",
        "    prompt_text = prompt_file.read_text(encoding='utf-8')",
        "    if '# AIDD stage runtime request' not in prompt_text:",
        "        print('missing prompt-file stage request', file=sys.stderr)",
        "        raise SystemExit(35)",
        "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
        (
            "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM'] / "
            "'stages' / os.environ['AIDD_STAGE']"
        ),
        "stage_root.mkdir(parents=True, exist_ok=True)",
        "for name, content in documents.items():",
        "    (stage_root / name).write_text(content, encoding='utf-8')",
        "print('native-runtime-ok')",
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return script_path


def _write_native_opencode_provider_error_script(*, tmp_path: Path) -> Path:
    script_path = tmp_path / "native_opencode_provider_error.py"
    payload = {
        "type": "error",
        "timestamp": 1779816678585,
        "sessionID": "ses_test",
        "error": {
            "name": "APIError",
            "data": {
                "message": "usage limit reached",
                "statusCode": 403,
            },
        },
    }
    script_lines = [
        "import json",
        "import sys",
        f"payload = {payload!r}",
        "args = sys.argv[1:]",
        "if '--dir' not in args or '--file' not in args:",
        "    print('missing native opencode flags', file=sys.stderr)",
        "    raise SystemExit(34)",
        "print(json.dumps(payload))",
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return script_path


def _write_cli_config(
    *,
    tmp_path: Path,
    runtime_command: str,
    claude_code_command: str = "claude",
    codex_command: str = "codex",
    opencode_command: str = "opencode",
    qwen_command: str = "qwen",
    max_repair_attempts: int = 2,
) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            'root = ".aidd"\n\n'
            "[runtime.generic_cli]\n"
            f'command = "{runtime_command}"\n\n'
            "[runtime.claude_code]\n"
            f'command = "{claude_code_command}"\n\n'
            "[runtime.codex]\n"
            f'command = "{codex_command}"\n\n'
            "[runtime.opencode]\n"
            f'command = "{opencode_command}"\n\n'
            "[runtime.qwen]\n"
            f'command = "{qwen_command}"\n\n'
            "[repair]\n"
            f"max_attempts = {max_repair_attempts}\n"
        ),
        encoding="utf-8",
    )
    return config_path


def _prepare_cli_repair_extension_workspace(
    *,
    tmp_path: Path,
    documents: dict[str, str],
    exit_code: int = 0,
) -> tuple[Path, Path, Path]:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-CLI-REPAIR-EXTENSION"
    run_id = "run-cli-repair-extension"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=documents,
        exit_code=exit_code,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
    )
    options = StageRunOptions(
        stage="plan",
        work_item=work_item,
        runtime="generic-cli",
        run_id=run_id,
        root=workspace_root,
        config=config_path,
        log_follow=False,
    )
    runtime_config = _resolve_stage_run_config(options)
    _write_run_manifest(options=options, runtime_config=runtime_config, run_id=run_id)
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="plan",
        status="failed",
    )
    stage_root = workspace_root / "workitems" / work_item / "stages" / "plan"
    stage_root.mkdir(parents=True, exist_ok=True)
    (stage_root / "validator-report.md").write_text(
        render_validator_report(
            (
                ValidationFinding(
                    code="SEM-PLACEHOLDER-CONTENT",
                    message="Replace the placeholder content.",
                ),
            )
        ),
        encoding="utf-8",
    )
    (stage_root / "repair-brief.md").write_text(
        "# Repair brief\n\nRepair budget status: `repair-budget-exhausted`.\n",
        encoding="utf-8",
    )
    return workspace_root, config_path, stage_root


def test_stage_repair_extension_cli_runs_one_explicit_attempt_and_streams_evidence(
    tmp_path: Path,
) -> None:
    workspace_root, config_path, stage_root = _prepare_cli_repair_extension_workspace(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "repair-extension",
            "plan",
            "--work-item",
            "WI-CLI-REPAIR-EXTENSION",
            "--run-id",
            "run-cli-repair-extension",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--non-interactive",
            "--log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Repair-extension preview" in result.stdout
    assert "Automatic repair budget" in result.stdout
    assert "Repair-extension preflight: action=reopened" in result.stdout
    assert "Validator evidence:" in result.stdout
    assert "Stage run result: action=advance state=succeeded" in result.stdout
    metadata = json.loads(
        (
            workspace_root
            / "reports"
            / "runs"
            / "WI-CLI-REPAIR-EXTENSION"
            / "run-cli-repair-extension"
            / "stages"
            / "plan"
            / "stage-metadata.json"
        ).read_text(encoding="utf-8")
    )
    assert metadata["repair_extension_grant"]["stage"] == "plan"
    assert metadata["repair_history"][-1]["trigger"] == "repair-extension"
    assert (stage_root / "output" / "plan.md").exists()


def test_stage_repair_extension_cli_refuses_implicit_non_interactive_authorization(
    tmp_path: Path,
) -> None:
    workspace_root, config_path, _ = _prepare_cli_repair_extension_workspace(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "repair-extension",
            "plan",
            "--work-item",
            "WI-CLI-REPAIR-EXTENSION",
            "--run-id",
            "run-cli-repair-extension",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 2, result.output
    assert "requires operator confirmation" in result.stdout


def test_stage_repair_extension_cli_does_not_schedule_automatic_retry_after_failure(
    tmp_path: Path,
) -> None:
    workspace_root, config_path, _ = _prepare_cli_repair_extension_workspace(
        tmp_path=tmp_path,
        documents={},
        exit_code=3,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "repair-extension",
            "plan",
            "--work-item",
            "WI-CLI-REPAIR-EXTENSION",
            "--run-id",
            "run-cli-repair-extension",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--non-interactive",
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "Repair retry scheduled" not in result.stdout
    assert "Adapter outcome: non_zero_exit" in result.stdout


def test_stage_repair_extension_command_propagates_cancellation(
    tmp_path: Path,
) -> None:
    workspace_root, config_path, _ = _prepare_cli_repair_extension_workspace(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )
    options = StageRepairExtensionOptions(
        stage="plan",
        work_item="WI-CLI-REPAIR-EXTENSION",
        runtime="generic-cli",
        run_id="run-cli-repair-extension",
        root=workspace_root,
        config=config_path,
        non_interactive=True,
        log_follow=False,
        cancel_requested=lambda: True,
    )

    with pytest.raises(typer.Exit) as exc_info:
        run_stage_repair_extension_command(options)

    assert exc_info.value.exit_code == 1


def test_stage_repair_extension_cli_blocks_second_grant(tmp_path: Path) -> None:
    workspace_root, config_path, _ = _prepare_cli_repair_extension_workspace(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )
    args = [
        "stage",
        "repair-extension",
        "plan",
        "--work-item",
        "WI-CLI-REPAIR-EXTENSION",
        "--run-id",
        "run-cli-repair-extension",
        "--runtime",
        "generic-cli",
        "--root",
        str(workspace_root),
        "--config",
        str(config_path),
        "--non-interactive",
        "--no-log-follow",
    ]

    first = runner.invoke(app, args)
    second = runner.invoke(app, args)

    assert first.exit_code == 0, first.output
    assert second.exit_code == 1, second.output
    assert "already used" in second.stdout


def test_ui_selector_override_is_capability_checked_and_recorded_in_manifest(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command="python")
    options = StageRunOptions(
        stage="idea",
        work_item="WI-UI-SELECTOR",
        runtime="codex",
        run_id="run-ui-selector",
        root=workspace_root,
        config=config_path,
        log_follow=False,
        model_override="gpt-5.6-luna",
        reasoning_effort_override="high",
    )

    runtime_config = _resolve_stage_run_config(options)

    assert runtime_config.runtime_model == "gpt-5.6-luna"
    assert runtime_config.runtime_reasoning_effort == "high"
    assert runtime_config.runtime_model_source == "ui-selection"
    assert runtime_config.runtime_reasoning_effort_source == "ui-selection"
    _write_run_manifest(options=options, runtime_config=runtime_config, run_id=options.run_id)
    manifest = json.loads(
        (
            workspace_root
            / "reports"
            / "runs"
            / "WI-UI-SELECTOR"
            / "run-ui-selector"
            / "run-manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["config_snapshot"]["runtime_selection"] == {
        "model_source": "ui-selection",
        "reasoning_effort_source": "ui-selection",
        "requested_model": "gpt-5.6-luna",
        "requested_reasoning_effort": "high",
    }


def _write_native_runtime_cli_config(
    *,
    tmp_path: Path,
    runtime: str,
    runtime_command: str,
) -> Path:
    config_path = tmp_path / f"aidd.{runtime}.native.toml"
    runtime_section = "codex" if runtime == "codex" else "opencode"
    config_path.write_text(
        "\n".join(
            (
                "[workspace]",
                'root = ".aidd"',
                "",
                f"[runtime.{runtime_section}]",
                f"command = {json.dumps(runtime_command)}",
                'mode = "native"',
                "",
                "[repair]",
                "max_attempts = 2",
                "",
            )
        ),
        encoding="utf-8",
    )
    return config_path


def _write_intervention_runtime_script(
    *,
    tmp_path: Path,
    documents: dict[str, str],
) -> Path:
    script_path = tmp_path / "intervention_runtime.py"
    script_lines = [
        "import os",
        "import sys",
        "from pathlib import Path",
        f"documents = {documents!r}",
        "if os.environ.get('AIDD_ATTEMPT_MODE') != 'intervention':",
        "    print('missing intervention attempt mode', file=sys.stderr)",
        "    raise SystemExit(41)",
        "request_path = Path(os.environ.get('AIDD_OPERATOR_REQUEST_PATH', ''))",
        "if not request_path.exists():",
        "    print('missing operator request path', file=sys.stderr)",
        "    raise SystemExit(42)",
        "request_text = request_path.read_text(encoding='utf-8')",
        "if 'Add migration rollback risks' not in request_text:",
        "    print('missing operator request text', file=sys.stderr)",
        "    raise SystemExit(43)",
        "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
        (
            "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM'] "
            "/ 'stages' / os.environ['AIDD_STAGE']"
        ),
        "stage_root.mkdir(parents=True, exist_ok=True)",
        "for name, content in documents.items():",
        "    (stage_root / name).write_text(content, encoding='utf-8')",
        "print('intervention-runtime-ok')",
    ]
    script_path.write_text("\n".join(script_lines) + "\n", encoding="utf-8")
    return script_path


def _run_id_for_work_item(*, workspace_root: Path, work_item: str) -> str:
    run_id = latest_run_id(workspace_root=workspace_root, work_item=work_item)
    assert run_id is not None
    return run_id


def test_stage_run_executes_generic_cli_stage_and_streams_with_log_follow(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-001")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command=runtime_command)

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-001",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Live-log follow mode enabled for runtime stream output." in result.stdout
    assert "[generic-cli:plan:stdout] runtime-output-line" in result.stdout
    assert "[generic-cli:plan:stderr] runtime-error-line" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-001")
    assert f"run_id={run_id}" in result.stdout
    assert (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    ).exists()
    runtime_log_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / RUN_RUNTIME_LOG_FILENAME
    )
    assert runtime_log_path.exists()
    runtime_log = runtime_log_path.read_text(encoding="utf-8")
    assert "runtime-output-line" in runtime_log
    assert "runtime-error-line" in runtime_log
    metadata_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-001"
        / run_id
        / "stages"
        / "plan"
        / "stage-metadata.json"
    )
    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["repair_history"] == []


def test_stage_run_continues_canonical_next_stage_in_explicit_unbounded_run(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-STEPWISE"
    run_id = "run-stepwise"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command=runtime_command)
    initial_options = StageRunOptions(
        stage="research",
        work_item=work_item,
        runtime="generic-cli",
        run_id=run_id,
        root=workspace_root,
        config=config_path,
        log_follow=False,
    )
    runtime_config = _resolve_stage_run_config(initial_options)
    _write_run_manifest(
        options=initial_options,
        runtime_config=runtime_config,
        run_id=run_id,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage="research",
        status="succeeded",
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--run-id",
            run_id,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            workspace_root
            / "reports"
            / "runs"
            / work_item
            / run_id
            / "run-manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["stage_target"] == "research"
    assert "AIDD stage run: stage=plan" in result.stdout


def test_stage_run_without_log_follow_omits_stream_prefixes(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-002")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command=runtime_command)

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-002",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "[generic-cli:plan:stdout]" not in result.stdout
    assert "[generic-cli:plan:stderr]" not in result.stdout


def test_stage_run_resolves_runtime_resources_from_outside_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "external-project"
    project_root.mkdir(parents=True)
    workspace_root = project_root / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-EXT")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(tmp_path=project_root, runtime_command=runtime_command)
    monkeypatch.chdir(project_root)

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-EXT",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        workspace_root / "workitems" / "WI-EXT" / "stages" / "plan" / "output" / "plan.md"
    ).exists()
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-EXT")
    runtime_log_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-EXT"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / RUN_RUNTIME_LOG_FILENAME
    )
    assert runtime_log_path.exists()
    runtime_log = runtime_log_path.read_text(encoding="utf-8")
    assert "runtime-output-line" in runtime_log
    assert "runtime-error-line" in runtime_log


def test_stage_run_returns_nonzero_when_runtime_fails(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-003")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents={},
        exit_code=3,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command=runtime_command)

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-003",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "action=stop state=failed" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-003")
    metadata_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-003"
        / run_id
        / "stages"
        / "plan"
        / "stage-metadata.json"
    )
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"


@pytest.mark.parametrize(
    "runtime",
    ("claude-code", "codex", "opencode", "qwen"),
)
def test_stage_run_executes_supported_non_generic_runtime(
    tmp_path: Path,
    runtime: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-007")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        claude_code_command=runtime_command,
        codex_command=runtime_command,
        opencode_command=runtime_command,
        qwen_command=runtime_command,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-007",
            "--runtime",
            runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"AIDD stage run: stage=plan work_item=WI-007 runtime={runtime} " in result.stdout
    assert f"[{runtime}:plan:stdout] runtime-output-line" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-007")
    runtime_log_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-007"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / RUN_RUNTIME_LOG_FILENAME
    )
    assert runtime_log_path.exists()
    assert "runtime-output-line" in runtime_log_path.read_text(encoding="utf-8")
    runtime_exit_metadata_path = runtime_log_path.parent / RUNTIME_EXIT_METADATA_FILENAME
    assert runtime_exit_metadata_path.exists()
    runtime_exit_metadata = json.loads(runtime_exit_metadata_path.read_text(encoding="utf-8"))
    assert runtime_exit_metadata["schema_version"] == 1
    assert runtime_exit_metadata["exit_code"] == 0
    assert runtime_exit_metadata["runtime_log_char_count"] >= len("runtime-output-line\n")


@pytest.mark.parametrize("runtime", ("codex", "opencode"))
def test_stage_run_executes_native_provider_mode_without_adapter_flags(
    tmp_path: Path,
    runtime: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-017")
    writer_script = _write_native_runtime_writer_script(
        tmp_path=tmp_path,
        runtime=runtime,
        documents=_valid_plan_output_documents(),
    )
    if runtime == "codex":
        runtime_command = (
            f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())} "
            "exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
        )
    else:
        runtime_command = (
            f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())} "
            "run --format json --dangerously-skip-permissions"
        )
    config_path = _write_native_runtime_cli_config(
        tmp_path=tmp_path,
        runtime=runtime,
        runtime_command=runtime_command,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-017",
            "--runtime",
            runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert f"[{runtime}:plan:stdout] native-runtime-ok" in result.stdout
    assert (
        workspace_root / "workitems" / "WI-017" / "stages" / "plan" / "output" / "plan.md"
    ).exists()


def test_stage_run_stops_on_native_opencode_zero_exit_provider_error(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-OPENCODE-ERR"
    run_id = "run-opencode-provider-error"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    error_script = _write_native_opencode_provider_error_script(tmp_path=tmp_path)
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(error_script.as_posix())} "
        "run --format json --dangerously-skip-permissions"
    )
    config_path = _write_native_runtime_cli_config(
        tmp_path=tmp_path,
        runtime="opencode",
        runtime_command=runtime_command,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "opencode",
            "--run-id",
            run_id,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "[opencode:plan:stdout]" in result.stdout
    assert "usage limit reached" in result.stdout
    assert "Stage run result: action=stop state=failed" in result.stdout
    assert "Stage attempts: 1" in result.stdout
    assert "Adapter outcome: provider_error" in result.stdout
    assert "Repair retry scheduled" not in result.stdout
    runtime_log_path = (
        workspace_root
        / "reports"
        / "runs"
        / work_item
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
        / RUN_RUNTIME_LOG_FILENAME
    )
    assert runtime_log_path.exists()
    runtime_exit_metadata = json.loads(
        (runtime_log_path.parent / RUNTIME_EXIT_METADATA_FILENAME).read_text(encoding="utf-8")
    )
    assert runtime_exit_metadata["exit_code"] == 0
    assert runtime_exit_metadata["exit_classification"] == "provider_error"


def test_stage_interact_creates_operator_request_and_runs_current_run(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-INT"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-int",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    writer_script = _write_intervention_runtime_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}",
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "interact",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--run-id",
            "run-int",
            "--request",
            "Add migration rollback risks",
            "--target-document",
            "plan.md",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    request_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "plan"
        / "operator-requests"
        / "request-0001.md"
    )
    assert result.exit_code == 0, result.output
    assert "AIDD stage interaction: stage=plan" in result.stdout
    assert "Intervention attempt: 1" in result.stdout
    assert "Operator request:" in result.stdout
    assert "operator-requests" in result.stdout
    assert "request-0001.md" in result.stdout
    assert request_path.exists()
    assert "Add migration rollback risks" in request_path.read_text(encoding="utf-8")
    artifact_index = run_attempt_artifact_index_path(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-int",
        stage="plan",
        attempt_number=1,
    )
    artifact_payload = json.loads(artifact_index.read_text(encoding="utf-8"))
    assert artifact_payload["documents"]["operator_request"].endswith(
        "operator-requests/request-0001.md"
    )


def test_stage_interact_reuses_synchronously_prepared_request(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-INT-PREPARED"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-int",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    writer_script = _write_intervention_runtime_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}",
    )
    options = StageInteractOptions(
        stage="plan",
        work_item=work_item,
        runtime="generic-cli",
        run_id="run-int",
        root=workspace_root,
        config=config_path,
        request="Add migration rollback risks",
        target_documents=("plan.md",),
        log_follow=False,
    )

    prepared = prepare_stage_interaction(options)
    request_root = prepared.operator_request.request_path.parent
    assert [path.name for path in request_root.glob("request-*.md")] == [
        "request-0001.md"
    ]

    run_stage_interact_command(
        StageInteractOptions(
            stage=options.stage,
            work_item=options.work_item,
            runtime=options.runtime,
            run_id=options.run_id,
            root=options.root,
            config=options.config,
            request=options.request,
            target_documents=options.target_documents,
            log_follow=False,
            prepared_interaction=prepared,
        )
    )

    assert [path.name for path in request_root.glob("request-*.md")] == [
        "request-0001.md"
    ]


def test_stage_interact_reports_original_intervention_attempt_when_repair_retries(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-INT-REPAIR"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-int",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_repair_trigger_plan_output_documents(),
        exit_code=0,
        next_documents=_valid_plan_output_documents(repair_trace=True),
    )
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}",
        max_repair_attempts=1,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "interact",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--run-id",
            "run-int",
            "--request",
            "Add migration rollback risks",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Repair retry scheduled: attempt=2" in result.stdout
    assert "Stage attempts: 2" in result.stdout
    assert "Intervention attempt: 1" in result.stdout
    assert "Intervention attempt: 2" not in result.stdout


def test_stage_interact_supports_request_file_and_rejects_bad_target(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-INT-FILE"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    create_run_manifest(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id="run-int",
        runtime_id="generic-cli",
        stage_target="plan",
        config_snapshot={"mode": "test"},
    )
    request_file = tmp_path / "request.md"
    request_file.write_text("Add migration rollback risks\n", encoding="utf-8")
    writer_script = _write_intervention_runtime_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
    )
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}",
    )

    file_result = runner.invoke(
        app,
        [
            "stage",
            "interact",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--run-id",
            "run-int",
            "--request-file",
            str(request_file),
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )
    bad_target = runner.invoke(
        app,
        [
            "stage",
            "interact",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--run-id",
            "run-int",
            "--request",
            "Add migration rollback risks",
            "--target-document",
            "workitems/WI-INT-FILE/stages/research/research-notes.md",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
        ],
    )

    assert file_result.exit_code == 0, file_result.output
    assert bad_target.exit_code != 0
    assert "outside current stage scope" in bad_target.output


def test_stage_run_rejects_unknown_runtime() -> None:
    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-001",
            "--runtime",
            "pi-mono",
        ],
    )

    assert result.exit_code != 0
    assert "Unsupported runtime 'pi-mono'" in result.output


def test_stage_run_requires_explicit_runtime() -> None:
    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-001",
        ],
    )

    assert result.exit_code != 0
    assert "Missing option '--runtime'" in result.output
    assert "explicit" in result.output
    assert "runtime" in result.output
    assert "id" in result.output


def test_stage_run_reports_actionable_missing_intake_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_cli_config(tmp_path=tmp_path, runtime_command="python missing.py")

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "idea",
            "--work-item",
            "WI-MISSING-INTAKE",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
        ],
    )

    assert result.exit_code != 0
    assert "Stage input preflight failed: missing required input document" in result.output
    assert "workitems/WI-MISSING-INTAKE/context/intake.md" in result.output


def test_stage_run_retries_after_repair_and_succeeds_within_budget(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-004")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_repair_trigger_plan_output_documents(),
        next_documents=_valid_plan_output_documents(repair_trace=True),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        max_repair_attempts=2,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-004",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Repair brief prepared:" in result.stdout
    assert "Stage attempts: 2" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-004")
    assert (
        workspace_root / "reports" / "runs" / "WI-004" / run_id / "stages" / "plan" / "attempts"
    ).exists()
    assert (
        workspace_root
        / "reports"
        / "runs"
        / "WI-004"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0002"
        / RUN_RUNTIME_LOG_FILENAME
    ).exists()
    repair_brief_path = (
        workspace_root / "workitems" / "WI-004" / "stages" / "plan" / "repair-brief.md"
    )
    assert repair_brief_path.exists()
    assert "Repair attempt context" in repair_brief_path.read_text(encoding="utf-8")
    assert (
        workspace_root / "workitems" / "WI-004" / "stages" / "plan" / "output" / "plan.md"
    ).exists()
    stage_result_text = (
        workspace_root / "workitems" / "WI-004" / "stages" / "plan" / "output" / "stage-result.md"
    ).read_text(encoding="utf-8")
    assert "- Attempt `1` (`initial`) -> failed validation." in stage_result_text
    assert "- Attempt `2` (`repair`) -> succeeded." in stage_result_text
    first_index = json.loads(
        run_attempt_artifact_index_path(
            workspace_root=workspace_root,
            work_item="WI-004",
            run_id=run_id,
            stage="plan",
            attempt_number=1,
        ).read_text(encoding="utf-8")
    )
    repair_index = json.loads(
        run_attempt_artifact_index_path(
            workspace_root=workspace_root,
            work_item="WI-004",
            run_id=run_id,
            stage="plan",
            attempt_number=2,
        ).read_text(encoding="utf-8")
    )
    assert first_index["attempt_mode"] == "initial"
    assert repair_index["attempt_mode"] == "repair"
    first_prompt_names = {
        Path(entry["path"]).name for entry in first_index["prompt_pack_provenance"]
    }
    repair_prompt_names = {
        Path(entry["path"]).name for entry in repair_index["prompt_pack_provenance"]
    }
    assert "repair.md" not in first_prompt_names
    assert "intervention.md" not in first_prompt_names
    assert "repair.md" in repair_prompt_names
    assert "intervention.md" not in repair_prompt_names


def test_stage_run_repairs_duplicate_attempt_history_found_after_normalization(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-POST-NORMALIZATION"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item=work_item)
    invalid_documents = _valid_plan_output_documents()
    invalid_documents["stage-result.md"] = invalid_documents["stage-result.md"].replace(
        "## Attempt history\n\n- attempt-0001\n\n",
        "## Attempt history\n\n"
        "- Attempt 1 (`initial`): first claim.\n"
        "- Attempt 1 (`initial`): duplicate claim.\n\n",
    )
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=invalid_documents,
        next_documents=_valid_plan_output_documents(repair_trace=True),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        max_repair_attempts=2,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            work_item,
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Repair retry scheduled: attempt=2" in result.stdout
    assert "Stage attempts: 2" in result.stdout
    assert "Final post-normalization stage-result validation failed" not in result.output


def test_stage_run_stops_when_repair_budget_is_exhausted(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-005")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_repair_trigger_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        max_repair_attempts=1,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-005",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "Repair brief prepared:" in result.stdout
    assert "Stage attempts: 2" in result.stdout
    assert "action=stop state=failed" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-005")
    metadata_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-005"
        / run_id
        / "stages"
        / "plan"
        / "stage-metadata.json"
    )
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert [entry["outcome"] for entry in payload["repair_history"]] == [
        "failed validation",
        "failed validation",
    ]


def test_stage_run_blocks_on_runtime_native_question_event(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-QUESTION")
    question_event = json.dumps(
        {
            "event": "question_raised",
            "question_id": "Q1",
            "question": "Confirm the rollout owner.",
            "policy": "blocking",
        }
    )
    runtime_documents = _valid_plan_output_documents()
    runtime_documents.pop("answers.md")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=runtime_documents,
        exit_code=0,
        extra_stdout_lines=(question_event,),
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command="python",
        claude_code_command=runtime_command,
    )

    result = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-QUESTION",
            "--runtime",
            "claude-code",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "Stage run result: action=wait state=blocked" in result.stdout
    assert "Blocking questions are unresolved." in result.stdout
    assert "Questions:" in result.stdout
    assert "Answers:" in result.stdout
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-QUESTION")
    questions_text = (
        workspace_root / "workitems" / "WI-QUESTION" / "stages" / "plan" / "questions.md"
    ).read_text(encoding="utf-8")
    assert "Confirm the rollout owner." in questions_text
    answers_text = (
        workspace_root / "workitems" / "WI-QUESTION" / "stages" / "plan" / "answers.md"
    ).read_text(encoding="utf-8")
    assert "- none" in answers_text

    attempt_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-QUESTION"
        / run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0001"
    )
    assert (attempt_path / RUN_RUNTIME_JSONL_FILENAME).exists()
    assert (attempt_path / RUN_EVENTS_JSONL_FILENAME).exists()
    artifact_index = json.loads(
        run_attempt_artifact_index_path(
            workspace_root=workspace_root,
            work_item="WI-QUESTION",
            run_id=run_id,
            stage="plan",
            attempt_number=1,
        ).read_text(encoding="utf-8")
    )
    assert artifact_index["logs"]["runtime_jsonl"].endswith("/attempt-0001/runtime.jsonl")
    assert artifact_index["logs"]["events_jsonl"].endswith("/attempt-0001/events.jsonl")


def test_stage_run_resumes_blocked_stage_after_answers_are_provided(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-006")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_blocked_question_output_documents(),
        next_documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        max_repair_attempts=1,
    )

    first_run = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-006",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert first_run.exit_code == 1, first_run.output
    assert "action=wait state=blocked" in first_run.stdout
    blocked_run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-006")
    answers_path = workspace_root / "workitems" / "WI-006" / "stages" / "plan" / "answers.md"
    answers_path.write_text(
        ("# Answers\n\n- `Q1` `[resolved]` Include migration fallback in the first rollout.\n"),
        encoding="utf-8",
    )

    resumed_run = runner.invoke(
        app,
        [
            "stage",
            "run",
            "plan",
            "--work-item",
            "WI-006",
            "--runtime",
            "generic-cli",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert resumed_run.exit_code == 0, resumed_run.output
    assert (
        "Detected blocked stage metadata on the latest run; attempting resume."
        in resumed_run.stdout
    )
    assert "Resuming blocked stage after answers were detected." in resumed_run.stdout
    assert f"run_id={blocked_run_id}" in resumed_run.stdout
    assert "Stage attempts: 1" in resumed_run.stdout
    assert (
        workspace_root
        / "reports"
        / "runs"
        / "WI-006"
        / blocked_run_id
        / "stages"
        / "plan"
        / "attempts"
        / "attempt-0002"
        / RUN_RUNTIME_LOG_FILENAME
    ).exists()
    metadata_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-006"
        / blocked_run_id
        / "stages"
        / "plan"
        / "stage-metadata.json"
    )
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert payload["status"] == "succeeded"


def test_prefix_stream_chunk_formats_multiline_follow_output() -> None:
    formatted = _prefix_stream_chunk(
        runtime="claude-code",
        stage="plan",
        stream="stdout",
        chunk="line-1\nline-2\n",
        multi_stream=True,
    )

    assert formatted == ("[claude-code:plan:stdout] line-1\n[claude-code:plan:stdout] line-2\n")


def test_prefix_stream_chunk_leaves_single_stream_output_unchanged() -> None:
    original = "plain-line\n"
    formatted = _prefix_stream_chunk(
        runtime="claude-code",
        stage="plan",
        stream="stderr",
        chunk=original,
        multi_stream=False,
    )

    assert formatted == original


def test_active_prompt_pack_paths_selects_intervention_overlay() -> None:
    paths = (
        Path("prompt-packs/stages/plan/system.md"),
        Path("prompt-packs/stages/plan/run.md"),
        Path("prompt-packs/stages/plan/intervention.md"),
        Path("prompt-packs/stages/plan/repair.md"),
        Path("prompt-packs/stages/plan/interview.md"),
    )

    active = _active_prompt_pack_paths(
        prompt_pack_paths=paths,
        repair_mode=False,
        intervention_mode=True,
    )
    normal = _active_prompt_pack_paths(prompt_pack_paths=paths, repair_mode=False)
    repair = _active_prompt_pack_paths(prompt_pack_paths=paths, repair_mode=True)

    assert active == (
        Path("prompt-packs/stages/plan/system.md"),
        Path("prompt-packs/stages/plan/intervention.md"),
    )
    assert Path("prompt-packs/stages/plan/intervention.md") not in normal
    assert Path("prompt-packs/stages/plan/intervention.md") not in repair
