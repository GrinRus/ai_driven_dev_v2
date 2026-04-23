from __future__ import annotations

from pathlib import Path

from aidd.core.workspace import init_workspace
from aidd.harness.scenarios import Scenario


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _markdown(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def bootstrap_live_work_item(
    *,
    working_copy_path: Path,
    scenario: Scenario,
    work_item: str,
    resolved_revision: str | None = None,
) -> Path:
    workspace_root = working_copy_path / ".aidd"
    init_workspace(root=workspace_root, work_item=work_item)

    context_root = workspace_root / "workitems" / work_item / "context"
    repository_revision = (
        resolved_revision
        or scenario.repo.revision
        or "unresolved-at-bootstrap"
    )
    target_task = scenario.task.strip()
    verify_commands = ", ".join(scenario.verify.commands)

    context_documents = {
        "intake.md": _markdown(
            "# Intake",
            "",
            f"- Scenario: `{scenario.scenario_id}`",
            f"- Repository: `{scenario.repo.url}`",
            f"- Revision: `{repository_revision}`",
            f"- Task: {target_task}",
        ),
        "user-request.md": _markdown(
            "# User Request",
            "",
            target_task,
        ),
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
        ),
        "review-context.md": _markdown(
            "# Review Context",
            "",
            f"- Review the live-scenario artifacts for `{scenario.scenario_id}`.",
            "- Keep the verdict tied to repository evidence, validator output, and runtime logs.",
        ),
        "task-selection.md": _markdown(
            "# Task Selection",
            "",
            "- Selected task id: `TL-2`",
            f"- Selected task intent: {target_task}",
        ),
        "allowed-write-scope.md": _markdown(
            "# Allowed Write Scope",
            "",
            (
                "- Limit edits to the minimal repository and `.aidd/` artifacts "
                "needed for this scenario."
            ),
            "- Keep scenario changes reviewable and bounded.",
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
            "- AC-1: installed AIDD runs from the target repository root.",
            "- AC-2: required workflow artifacts are produced for the selected work item.",
            "- AC-3: scenario verification commands pass without hiding failures.",
        ),
        "verification-output.md": _markdown(
            "# Verification Output",
            "",
            "- Scenario verification commands:",
            f"- `{verify_commands}`",
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

    for name, content in context_documents.items():
        _write_text(context_root / name, content)

    return workspace_root


__all__ = ["bootstrap_live_work_item"]
