from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from aidd.cli import main as cli_main
from aidd.core.run_store import persist_stage_status, run_manifest_path, work_item_runs_root
from aidd.core.stage_graph import StageAdvancementSummary
from aidd.core.stage_registry import resolve_expected_output_documents
from aidd.core.stages import STAGES
from aidd.core.state_machine import StageState
from aidd.core.workspace import WorkspaceBootstrapService

runner = CliRunner()
_RUNTIME_COMMANDS: dict[str, str] = {
    "generic-cli": "python-generic",
    "claude-code": "claude-fake",
    "codex": "codex-fake",
    "opencode": "opencode-fake",
}


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "aidd.test.toml"
    config_path.write_text(
        (
            "[workspace]\n"
            'root = ".aidd"\n\n'
            "[runtime.generic_cli]\n"
            f'command = "{_RUNTIME_COMMANDS["generic-cli"]}"\n\n'
            "[runtime.claude_code]\n"
            f'command = "{_RUNTIME_COMMANDS["claude-code"]}"\n\n'
            "[runtime.codex]\n"
            f'command = "{_RUNTIME_COMMANDS["codex"]}"\n\n'
            "[runtime.opencode]\n"
            f'command = "{_RUNTIME_COMMANDS["opencode"]}"\n'
        ),
        encoding="utf-8",
    )
    return config_path


def _seed_required_context(workspace_root: Path, *, work_item: str) -> None:
    bootstrap = WorkspaceBootstrapService(root=workspace_root)
    bootstrap.bootstrap_work_item(work_item=work_item)
    bootstrap.seed_request_context(
        work_item=work_item,
        request_text=f"Run workflow test for {work_item}.",
        project_root=workspace_root.parent,
        force=True,
    )


def _write_fake_project_change(project_root: Path) -> None:
    path = project_root / "src" / "example.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("SYNTHETIC_IMPLEMENTATION = True\n", encoding="utf-8")


def _write_fake_stage_outputs(
    workspace_root: Path,
    *,
    work_item: str,
    stage: str,
) -> None:
    for draft_path in resolve_expected_output_documents(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ):
        if stage == "tasklist" and draft_path.name == "tasklist.md":
            content = """# Tasklist

## Task summary

One implementation-ready task used by the workflow test double.

## Ordered tasks

### TL-1 — Execute the synthetic implementation

- Outcome: The synthetic implementation stage succeeds.
- Dominant deliverable: The fixture implementation report is produced.
- In scope: `src/example.py` and `tests/cli/test_run_workflow.py`.
- Acceptance criteria:
  - TL-1-AC1: Implement is dispatched once through task execution.

## Dependencies

- TL-1: none

## Verification notes

- TL-1: workflow dispatch assertion
"""
        elif stage == "implement" and draft_path.name == "implementation-report.md":
            content = """# Implementation Report

## Selected task

- Task id: `TL-1`

## Change summary

The synthetic implementation completed the selected workflow dispatch task and recorded evidence.

## Touched files

- `src/example.py` - synthetic implementation change for the workflow double.

## Verification notes

- `TL-1-AC1`: `python -c 'print(1)'` -> pass (workflow dispatch assertion).

## Follow-up notes

- none
"""
        else:
            content = f"# {draft_path.stem.title()}\n\nSynthetic output for {stage}.\n"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(content, encoding="utf-8")
        published_path = draft_path.parent / "output" / draft_path.name
        published_path.parent.mkdir(parents=True, exist_ok=True)
        published_path.write_text(content, encoding="utf-8")


def _mark_fake_stage_succeeded(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> None:
    _write_fake_stage_outputs(
        workspace_root,
        work_item=work_item,
        stage=stage,
    )
    persist_stage_status(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        status=StageState.SUCCEEDED.value,
    )


def _write_black_box_runtime_script(tmp_path: Path) -> Path:
    documents = {
        "idea": {
            "idea-brief.md": (
                "# Idea Brief\n\n"
                "## Problem statement\n\n"
                "The operator needs a bounded local workflow smoke.\n\n"
                "## Desired outcome\n\n"
                "Produce a small implementation plan with durable AIDD evidence.\n\n"
                "## Constraints\n\n"
                "- Keep workflow state inside `.aidd/`.\n\n"
                "## Open questions\n\n"
                "- none\n"
            ),
            "stage-result.md": (
                "# Stage result\n\n"
                "## Stage\n\nidea\n\n"
                "## Attempt history\n\n- attempt-0001\n\n"
                "## Status\n\nsucceeded\n\n"
                "## Produced outputs\n\n- idea-brief.md\n\n"
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
        },
        "plan": {
            "plan.md": (
                "# Plan\n\n"
                "## Goals\n\n- Deliver a reviewable local workflow smoke plan.\n\n"
                "## Out of scope\n\n- Provider setup changes are excluded.\n\n"
                "## Milestones\n\n- M1: Run the bounded workflow.\n\n"
                "## Implementation strategy\n\n"
                "- Use request-aware init and explicit runtime execution.\n\n"
                "## Risks\n\n- Risk: missing provider; mitigation: use configured wrapper lane.\n\n"
                "## Dependencies\n\n- Idea stage output.\n\n"
                "## Verification approach\n\n- Inspect run metadata, logs, and artifacts.\n\n"
                "## Verification notes\n\n"
                "- M1: Validate CLI inspection commands.\n"
            ),
            "stage-result.md": (
                "# Stage result\n\n"
                "## Stage\n\nplan\n\n"
                "## Attempt history\n\n- attempt-0001\n\n"
                "## Status\n\nsucceeded\n\n"
                "## Produced outputs\n\n- plan.md\n\n"
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
        },
        "research": {
            "research-notes.md": (
                "# Research Notes\n\n"
                "## Scope\n\n"
                "Evaluate the deterministic local workflow smoke path.\n\n"
                "## Sources\n\n"
                "- [S1] Local request context (`context/intake.md`), access date: 2026-05-07.\n\n"
                "## Findings\n\n"
                "- Request-aware init provides the required first-stage context ([S1]).\n\n"
                "## Trade-offs\n\n"
                "- A wrapper runtime keeps this regression deterministic.\n\n"
                "## Evidence trace\n\n"
                "- Init context finding -> [S1]\n\n"
                "## Open questions\n\n"
                "- none\n"
            ),
            "stage-result.md": (
                "# Stage result\n\n"
                "## Stage\n\nresearch\n\n"
                "## Attempt history\n\n- attempt-0001\n\n"
                "## Status\n\nsucceeded\n\n"
                "## Produced outputs\n\n- research-notes.md\n\n"
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
        },
    }
    script_path = tmp_path / "black_box_runtime.py"
    script_path.write_text(
        "\n".join(
            (
                "import os",
                "from pathlib import Path",
                f"documents_by_stage = {documents!r}",
                "stage = os.environ['AIDD_STAGE']",
                "root = Path(os.environ['AIDD_WORKSPACE_ROOT'])",
                "stage_root = root / 'workitems' / os.environ['AIDD_WORK_ITEM'] / 'stages' / stage",
                "stage_root.mkdir(parents=True, exist_ok=True)",
                "for name, content in documents_by_stage[stage].items():",
                "    (stage_root / name).write_text(content, encoding='utf-8')",
                "print(f'black-box-runtime stage={stage}')",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return script_path


def test_run_executes_runnable_stages_in_dependency_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []
    _seed_required_context(workspace_root, work_item="WI-010")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == "generic-cli"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        _mark_fake_stage_succeeded(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if stage == "implement":
            _write_fake_project_change(tmp_path)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-010",
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
    assert executed_stages == list(STAGES)
    assert "stage_bounds=idea->qa" in result.stdout
    assert "Workflow progress: stage=qa status=succeeded" in result.stdout
    assert "Workflow summary:" in result.stdout
    assert "- qa: status=succeeded attempts=0" in result.stdout
    assert "Workflow run completed:" in result.stdout


def test_run_stops_when_stage_execution_returns_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []
    _seed_required_context(workspace_root, work_item="WI-011")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == "generic-cli"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        if stage == "idea":
            _mark_fake_stage_succeeded(
                workspace_root=root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
            return
        persist_stage_status(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.FAILED.value,
        )
        raise typer.Exit(code=1)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-011",
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
    assert executed_stages == ["idea", "research"]
    assert "stage_bounds=idea->qa" in result.stdout
    assert "Workflow stopped at stage 'research'." in result.stdout
    assert "Workflow summary:" in result.stdout
    assert "- research: status=failed attempts=0" in result.stdout


@pytest.mark.parametrize("selected_runtime", ("claude-code", "codex", "opencode"))
def test_run_dispatches_workflow_for_supported_non_generic_runtimes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selected_runtime: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []
    _seed_required_context(workspace_root, work_item="WI-012")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == selected_runtime
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        _mark_fake_stage_succeeded(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if stage == "implement":
            _write_fake_project_change(tmp_path)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-012",
            "--runtime",
            selected_runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert executed_stages == list(STAGES)
    assert f"AIDD run: work_item=WI-012 runtime={selected_runtime}" in result.stdout
    assert "stage_bounds=idea->qa" in result.stdout
    assert "Workflow run completed:" in result.stdout


def test_run_rejects_unsupported_runtime_with_nonzero_exit() -> None:
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-013",
            "--runtime",
            "unsupported-runtime",
        ],
    )

    assert result.exit_code == 2, result.output
    assert "AIDD run: work_item=WI-013 runtime=unsupported-runtime" in result.stdout
    assert "Unsupported runtime 'unsupported-runtime' for workflow execution." in result.stdout
    assert "Failure classification: unsupported-runtime" in result.stdout


def test_run_requires_explicit_runtime_for_product_execution() -> None:
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-013",
        ],
    )

    assert result.exit_code != 0
    assert "Missing option '--runtime'" in result.output
    assert "explicit" in result.output
    assert "runtime" in result.output
    assert "id" in result.output


def test_run_reports_actionable_missing_intake_context(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)

    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-MISSING-INTAKE",
            "--runtime",
            "generic-cli",
            "--from-stage",
            "idea",
            "--to-stage",
            "idea",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code != 0
    assert "missing required inputs:" in result.output
    assert "workitems/WI-MISSING-INTAKE/context/intake.md" in result.output


def test_run_black_box_local_project_from_request_init_through_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local_project = tmp_path / "local-project"
    local_project.mkdir()
    runtime_script = _write_black_box_runtime_script(tmp_path)
    runtime_command = f"{shlex.quote(sys.executable)} {shlex.quote(runtime_script.as_posix())}"
    config_path = _write_config(local_project)
    config_text = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        config_text.replace(_RUNTIME_COMMANDS["generic-cli"], runtime_command),
        encoding="utf-8",
    )
    monkeypatch.chdir(local_project)

    init_result = runner.invoke(
        cli_main.app,
        [
            "init",
            "--work-item",
            "WI-BLACKBOX",
            "--request",
            "Implement a deterministic local workflow smoke.",
            "--root",
            ".aidd",
        ],
    )
    assert init_result.exit_code == 0, init_result.output

    run_result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-BLACKBOX",
            "--runtime",
            "generic-cli",
            "--from-stage",
            "idea",
            "--to-stage",
            "plan",
            "--root",
            ".aidd",
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    for command in (
        ["run", "show", "--work-item", "WI-BLACKBOX", "--root", ".aidd"],
        [
            "run",
            "logs",
            "--work-item",
            "WI-BLACKBOX",
            "--stage",
            "plan",
            "--root",
            ".aidd",
        ],
        [
            "run",
            "artifacts",
            "--work-item",
            "WI-BLACKBOX",
            "--stage",
            "plan",
            "--root",
            ".aidd",
        ],
    ):
        inspect_result = runner.invoke(cli_main.app, command)
        assert inspect_result.exit_code == 0, inspect_result.output

    assert (local_project / ".aidd" / "workitems" / "WI-BLACKBOX").exists()
    assert (
        local_project
        / ".aidd"
        / "workitems"
        / "WI-BLACKBOX"
        / "stages"
        / "plan"
        / "output"
        / "plan.md"
    ).exists()


@pytest.mark.parametrize("selected_runtime", ("generic-cli", "claude-code", "codex", "opencode"))
def test_run_manifest_persists_runtime_specific_command_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selected_runtime: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    monkeypatch.chdir(tmp_path)
    config_path = _write_config(tmp_path)
    _seed_required_context(workspace_root, work_item="WI-014")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == selected_runtime
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        _mark_fake_stage_succeeded(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )
        if stage == "implement":
            _write_fake_project_change(tmp_path)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-014",
            "--runtime",
            selected_runtime,
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    run_ids = sorted(
        path.name
        for path in work_item_runs_root(
            workspace_root=workspace_root,
            work_item="WI-014",
        ).iterdir()
    )
    assert run_ids
    manifest = json.loads(
        run_manifest_path(
            workspace_root=workspace_root,
            work_item="WI-014",
            run_id=run_ids[-1],
        ).read_text(encoding="utf-8")
    )
    assert manifest["runtime_id"] == selected_runtime
    assert manifest["workflow_bounds"] == {"start": "idea", "end": "qa"}
    assert manifest["config_snapshot"]["runtime_command"] == _RUNTIME_COMMANDS[selected_runtime]


def test_run_stops_for_non_generic_runtime_when_stage_execution_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []
    _seed_required_context(workspace_root, work_item="WI-015")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert runtime == "codex"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        if stage == "idea":
            _mark_fake_stage_succeeded(
                workspace_root=root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
            )
            return
        persist_stage_status(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            status=StageState.FAILED.value,
        )
        raise typer.Exit(code=1)

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-015",
            "--runtime",
            "codex",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert executed_stages == ["idea", "research"]
    assert "stage_bounds=idea->qa" in result.stdout
    assert "Workflow stopped at stage 'research'." in result.stdout
    assert "Workflow summary:" in result.stdout


def test_run_reports_non_generic_noop_path_with_nonzero_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)

    def _fake_select_next_runnable_stage(
        *,
        workspace_root: Path,
        work_item: str,
        run_id: str,
        stage_start: str | None = None,
        stage_end: str | None = None,
    ) -> str | None:
        _ = workspace_root, work_item, run_id, stage_start, stage_end
        return None

    def _fake_summarize_workflow_advancement(
        *,
        workspace_root: Path,
        work_item: str,
        run_id: str,
        stage_start: str | None = None,
        stage_end: str | None = None,
    ) -> tuple[StageAdvancementSummary, ...]:
        _ = workspace_root, work_item, run_id, stage_start, stage_end
        return (
            StageAdvancementSummary(
                stage="idea",
                current_status=None,
                can_run=False,
                reason="no runnable stage available",
                dependencies=tuple(),
                missing_prerequisites=tuple(),
                blocked_upstream_stages=tuple(),
                failed_upstream_stages=tuple(),
            ),
        )

    def _unexpected_stage_run(**_: object) -> None:
        raise AssertionError("stage_run should not be called when no stage is runnable")

    monkeypatch.setattr(cli_main, "select_next_runnable_stage", _fake_select_next_runnable_stage)
    monkeypatch.setattr(
        cli_main,
        "summarize_workflow_advancement",
        _fake_summarize_workflow_advancement,
    )
    monkeypatch.setattr(cli_main, "stage_run", _unexpected_stage_run)
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-016",
            "--runtime",
            "opencode",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 1, result.output
    assert "AIDD run: work_item=WI-016 runtime=opencode" in result.stdout
    assert "Workflow stopped: no runnable stage is currently available." in result.stdout


def test_run_respects_custom_stage_bounds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    workspace_root = tmp_path / ".aidd"
    config_path = _write_config(tmp_path)
    executed_stages: list[str] = []
    _seed_required_context(workspace_root, work_item="WI-017")

    def _fake_stage_run(
        *,
        stage: str,
        work_item: str,
        runtime: str,
        run_id: str | None,
        root: Path | None,
        config: Path,
        log_follow: bool,
    ) -> None:
        assert work_item == "WI-017"
        assert runtime == "generic-cli"
        assert run_id is not None
        assert root is not None
        assert config == config_path
        _ = log_follow
        executed_stages.append(stage)
        _mark_fake_stage_succeeded(
            workspace_root=root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
        )

    monkeypatch.setattr(cli_main, "stage_run", _fake_stage_run)
    result = runner.invoke(
        cli_main.app,
        [
            "run",
            "--work-item",
            "WI-017",
            "--runtime",
            "generic-cli",
            "--from-stage",
            "idea",
            "--to-stage",
            "tasklist",
            "--root",
            str(workspace_root),
            "--config",
            str(config_path),
            "--no-log-follow",
        ],
    )

    assert result.exit_code == 0, result.output
    assert executed_stages == ["idea", "research", "plan", "review-spec", "tasklist"]
    assert "stage_bounds=idea->tasklist" in result.stdout
