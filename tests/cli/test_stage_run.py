from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aidd.cli.main import _prefix_stream_chunk, app
from aidd.core.run_lookup import latest_run_id
from aidd.core.run_store import RUN_RUNTIME_LOG_FILENAME
from aidd.core.stage_runner import prepare_stage_bundle

runner = CliRunner()


def _materialize_plan_inputs(*, workspace_root: Path, work_item: str) -> None:
    bundle = prepare_stage_bundle(
        workspace_root=workspace_root,
        work_item=work_item,
        stage="plan",
    )
    for index, path in enumerate(bundle.expected_input_bundle, start=1):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Input {index}\n\nPrepared.\n", encoding="utf-8")


def _valid_plan_output_documents(*, include_repair_brief: bool = True) -> dict[str, str]:
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
            "## Produced outputs\n\n- plan.md\n- repair-brief.md (no repair needed)\n\n"
            "## Validation summary\n\n- structural: pass\n\n"
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
        "print('runtime-error-line', file=sys.stderr)",
        f"raise SystemExit({exit_code})",
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
    max_repair_attempts: int = 2,
) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            "root = \".aidd\"\n\n"
            "[runtime.generic_cli]\n"
            f"command = \"{runtime_command}\"\n\n"
            "[runtime.claude_code]\n"
            f"command = \"{claude_code_command}\"\n\n"
            "[runtime.codex]\n"
            f"command = \"{codex_command}\"\n\n"
            "[runtime.opencode]\n"
            f"command = \"{opencode_command}\"\n\n"
            "[repair]\n"
            f"max_attempts = {max_repair_attempts}\n"
        ),
        encoding="utf-8",
    )
    return config_path


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
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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


def test_stage_run_without_log_follow_omits_stream_prefixes(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-002")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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
    run_id = _run_id_for_work_item(workspace_root=workspace_root, work_item="WI-002")
    runtime_log_path = (
        workspace_root
        / "reports"
        / "runs"
        / "WI-002"
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
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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
    ("claude-code", "codex", "opencode"),
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
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
    config_path = _write_cli_config(
        tmp_path=tmp_path,
        runtime_command=runtime_command,
        claude_code_command=runtime_command,
        codex_command=runtime_command,
        opencode_command=runtime_command,
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
    assert (
        f"AIDD stage run: stage=plan work_item=WI-007 runtime={runtime} "
        in result.stdout
    )
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


def test_stage_run_retries_after_repair_and_succeeds_within_budget(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-004")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_repair_trigger_plan_output_documents(),
        next_documents=_valid_plan_output_documents(include_repair_brief=False),
        exit_code=0,
    )
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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


def test_stage_run_stops_when_repair_budget_is_exhausted(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-005")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_repair_trigger_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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


def test_stage_run_resumes_blocked_stage_after_answers_are_provided(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _materialize_plan_inputs(workspace_root=workspace_root, work_item="WI-006")
    writer_script = _write_runtime_writer_script(
        tmp_path=tmp_path,
        documents=_blocked_question_output_documents(),
        next_documents=_valid_plan_output_documents(),
        exit_code=0,
    )
    runtime_command = (
        f"{shlex.quote(sys.executable)} {shlex.quote(writer_script.as_posix())}"
    )
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
        (
            "# Answers\n\n"
            "- `Q1` `[resolved]` Include migration fallback in the first rollout.\n"
        ),
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

    assert formatted == (
        "[claude-code:plan:stdout] line-1\n"
        "[claude-code:plan:stdout] line-2\n"
    )


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
