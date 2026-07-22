from __future__ import annotations

from pathlib import Path

from aidd.harness.scenarios import Scenario, ScenarioAuthoredTask


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _markdown(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _user_request_markdown(selected_task: ScenarioAuthoredTask) -> str:
    if selected_task.visible_request is not None:
        return _markdown(
            "# User Request",
            "",
            selected_task.visible_request.rstrip(),
        )
    return _markdown(
        "# User Request",
        "",
        f"Implement authored live task `{selected_task.task_id}`: {selected_task.title}",
        "",
        selected_task.summary.strip(),
        "",
        "## Intent",
        "",
        selected_task.intent,
        "",
        "## Target Change",
        "",
        selected_task.target_change,
    )


def _selected_task_markdown(selected_task: ScenarioAuthoredTask) -> str:
    if selected_task.visible_request is not None:
        return _markdown(
            "# Selected Task",
            "",
            f"- Task id: `{selected_task.task_id}`",
            f"- Title: {selected_task.title}",
            f"- Summary: {selected_task.summary.strip()}",
            "",
            "## Visible Product Request",
            "",
            selected_task.visible_request.rstrip(),
            "",
            "## Authored Task Constraints",
            "",
            f"- Intent: {selected_task.intent}",
            f"- Target change: {selected_task.target_change}",
            f"- Expected scope: {selected_task.expected_scope}",
            f"- Quality bar: {selected_task.quality_bar}",
            f"- Size rationale: {selected_task.size_rationale}",
        )
    return _markdown(
        "# Selected Task",
        "",
        f"- Task id: `{selected_task.task_id}`",
        f"- Title: {selected_task.title}",
        f"- Summary: {selected_task.summary.strip()}",
        f"- Intent: {selected_task.intent}",
        f"- Target change: {selected_task.target_change}",
        f"- Expected scope: {selected_task.expected_scope}",
        f"- Quality bar: {selected_task.quality_bar}",
        f"- Size rationale: {selected_task.size_rationale}",
    )


def bootstrap_live_work_item(
    *,
    working_copy_path: Path,
    scenario: Scenario,
    work_item: str,
    selected_task: ScenarioAuthoredTask,
    resolved_revision: str | None = None,
) -> Path:
    workspace_root = working_copy_path / ".aidd"
    work_item_root = workspace_root / "workitems" / work_item
    if not work_item_root.exists():
        raise RuntimeError(
            "Installed `aidd init` must create the live workspace before scenario "
            f"context is written: {work_item_root.as_posix()}"
        )

    context_root = work_item_root / "context"
    repository_revision = (
        resolved_revision
        or scenario.repo.revision
        or "unresolved-at-bootstrap"
    )
    target_task = scenario.task.strip()
    verify_command_lines = tuple(
        f"- `{command}`" for command in selected_task.verification
    )
    scenario_verify_command_lines = tuple(
        f"- `{command}`" for command in scenario.verify.commands
    )
    acceptance_criteria_lines = tuple(
        f"- AC-{index}: {criterion}"
        for index, criterion in enumerate(selected_task.acceptance_criteria, start=1)
    )
    selection_policy = (
        scenario.feature_source.selection_policy
        if scenario.feature_source is not None
        else "n/a"
    )

    context_documents = {
        "intake.md": _markdown(
            "# Intake",
            "",
            f"- Scenario: `{scenario.scenario_id}`",
            f"- Repository: `{scenario.repo.url}`",
            f"- Revision: `{repository_revision}`",
            f"- Operator objective: {target_task}",
            f"- Selected authored task: `{selected_task.task_id}` {selected_task.title}",
        ),
        "user-request.md": _user_request_markdown(selected_task),
        "selected-task.md": _selected_task_markdown(selected_task),
        "repository-state.md": _markdown(
            "# Repository State",
            "",
            f"- Target repository: `{scenario.repo.url}`",
            f"- Pinned revision: `{repository_revision}`",
            "- `.aidd/` is rooted inside the prepared target repository working copy.",
        ),
        "constraints.md": _markdown(
            "# Constraints",
            "",
            "- Keep durable outputs in Markdown and preserve runtime logs.",
            "- Respect the pinned repository revision and bounded patch scope.",
            (
                "- Preserve truthful live-scenario evidence instead of hiding blockers "
                "or no-op paths."
            ),
        ),
        "previous-decisions.md": _markdown(
            "# Previous Decisions",
            "",
            f"- Scenario id: `{scenario.scenario_id}`",
            (
                f"- Stage scope target: `{scenario.run.stage_start or 'idea'}` -> "
                f"`{scenario.run.stage_end or 'qa'}`"
            ),
            f"- Runtime targets: `{', '.join(scenario.runtime_targets)}`",
            f"- Authored task selection policy: `{selection_policy}`",
        ),
        "task-selection.md": _markdown(
            "# Task Selection",
            "",
            f"- Selected task id: `{selected_task.task_id}`",
            f"- Selected task title: {selected_task.title}",
            f"- Selected task intent: {selected_task.intent}",
        ),
        "diff-summary.md": _markdown(
            "# Diff Summary",
            "",
            (
                "- Diff summary is scoped to the live-scenario task and updated by "
                "downstream stage output."
            ),
            (
                "- Review findings should cite implementation evidence or acceptance "
                "criteria explicitly."
            ),
        ),
        "acceptance-criteria.md": _markdown(
            "# Acceptance Criteria",
            "",
            *acceptance_criteria_lines,
        ),
        "verification-output.md": _markdown(
            "# Verification Output",
            "",
            "## Authored Task Verification Intent",
            "",
            *verify_command_lines,
            "",
            "## Scenario Verification Commands",
            "",
            *scenario_verify_command_lines,
        ),
        "verification-artifacts.md": _markdown(
            "# Verification Artifacts",
            "",
            "- Eval bundle lives under `.aidd/reports/evals/<run_id>/`.",
            "- QA output should reference runtime logs, validator reports, and verdict artifacts.",
        ),
        "release-policy.md": _markdown(
            "# Release Policy",
            "",
            (
                "- Release and live-scenario evidence must stay explicit about what "
                "was actually proven."
            ),
        ),
    }
    if selected_task.allowed_write_scope:
        context_documents["allowed-write-scope.md"] = _markdown(
            "# Allowed Write Scope",
            "",
            *(f"- `{path}`" for path in selected_task.allowed_write_scope),
        )

    for name, content in context_documents.items():
        _write_text(context_root / name, content)

    return workspace_root


__all__ = ["bootstrap_live_work_item"]
