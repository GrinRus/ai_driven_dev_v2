from __future__ import annotations

import re

from aidd.core.task_plan import TaskCard, TaskPlanParseError, parse_task_plan
from aidd.validators.cross_document_rules.context import (
    CrossDocumentContext,
    extract_section_lines,
    workspace_relative,
)
from aidd.validators.models import ValidationFinding, ValidationIssueLocation

TASKLIST_PLAN_MILESTONE_CODE = "CROSS-TASKLIST-PLAN-MILESTONE"
TASKLIST_PLAN_DEPENDENCY_CODE = "CROSS-TASKLIST-PLAN-DEPENDENCY"
TASKLIST_PLAN_VERIFICATION_CODE = "CROSS-TASKLIST-PLAN-VERIFICATION"

_MILESTONE_ID_PATTERN = re.compile(r"\b(M[1-9]\d*)\b", re.IGNORECASE)
_COMMAND_PREFIXES = (
    "uv ",
    "pytest ",
    "python ",
    "ruff ",
    "mypy ",
    "git ",
    "npm ",
    "pnpm ",
    "yarn ",
    "cargo ",
    "go test",
)


def _ordered_milestones(plan_text: str) -> tuple[str, ...]:
    milestones: list[str] = []
    for _, line in extract_section_lines(plan_text, "Milestones"):
        match = re.match(
            r"^\s*[-*+]\s+`?(M[1-9]\d*)`?(?:\s*:\s*|\s+)",
            line,
            re.IGNORECASE,
        )
        if match is not None:
            milestones.append(match.group(1).upper())
    return tuple(dict.fromkeys(milestones))


def _task_milestones(task: TaskCard) -> tuple[str, ...]:
    authored_text = "\n".join(
        (
            task.outcome,
            task.context or "",
            *(criterion.text for criterion in task.acceptance_criteria),
            task.verification,
        )
    )
    return tuple(
        dict.fromkeys(
            match.group(1).upper()
            for match in _MILESTONE_ID_PATTERN.finditer(authored_text)
        )
    )


def _milestone_dependencies(plan_text: str) -> tuple[tuple[str, str], ...]:
    edges: list[tuple[str, str]] = []
    for _, line in extract_section_lines(plan_text, "Dependencies"):
        if not re.search(r"\b(depends? on|after|requires?)\b", line, re.IGNORECASE):
            continue
        ids = [match.group(1).upper() for match in _MILESTONE_ID_PATTERN.finditer(line)]
        if len(ids) >= 2:
            edges.extend((ids[0], dependency) for dependency in ids[1:])
    return tuple(dict.fromkeys(edges))


def _verification_commands(plan_text: str) -> dict[str, tuple[str, ...]]:
    commands: dict[str, list[str]] = {}
    for _, line in extract_section_lines(plan_text, "Verification notes"):
        milestone_match = _MILESTONE_ID_PATTERN.search(line)
        if milestone_match is None:
            continue
        milestone = milestone_match.group(1).upper()
        for value in re.findall(r"`([^`]+)`", line):
            normalized = value.strip()
            if normalized.casefold().startswith(_COMMAND_PREFIXES):
                commands.setdefault(milestone, []).append(normalized)
    return {key: tuple(dict.fromkeys(values)) for key, values in commands.items()}


def _has_ancestor_milestone(
    *,
    task_id: str,
    milestone: str,
    dependencies: dict[str, tuple[str, ...]],
    task_milestones: dict[str, tuple[str, ...]],
) -> bool:
    pending = list(dependencies.get(task_id, ()))
    visited: set[str] = set()
    while pending:
        dependency = pending.pop()
        if dependency in visited:
            continue
        visited.add(dependency)
        if milestone in task_milestones.get(dependency, ()):
            return True
        pending.extend(dependencies.get(dependency, ()))
    return False


def validate_tasklist_plan(context: CrossDocumentContext) -> tuple[ValidationFinding, ...]:
    if context.stage != "tasklist" or context.tasklist_text is None or context.plan_text is None:
        return ()
    try:
        task_plan = parse_task_plan(context.tasklist_text)
    except TaskPlanParseError:
        return ()
    milestones = _ordered_milestones(context.plan_text)
    if not milestones:
        return ()
    known = set(milestones)
    positions = {milestone: index for index, milestone in enumerate(milestones)}
    mappings = {task.id: _task_milestones(task) for task in task_plan.tasks}
    tasklist_relative = workspace_relative(context.tasklist_path, context.workspace_root)
    findings: list[ValidationFinding] = []

    for task in task_plan.tasks:
        task_line = next(
            (
                number
                for number, line in enumerate(context.tasklist_text.splitlines(), start=1)
                if re.match(rf"^###\s+{re.escape(task.id)}\b", line.strip())
            ),
            None,
        )
        mapped = mappings[task.id]
        unknown = tuple(item for item in mapped if item not in known)
        if not mapped or unknown:
            detail = "no plan milestone" if not mapped else "unknown " + ", ".join(unknown)
            findings.append(
                ValidationFinding(
                    TASKLIST_PLAN_MILESTONE_CODE,
                    f"Task `{task.id}` maps to {detail}; cite an existing milestone id.",
                    "high",
                    ValidationIssueLocation(tasklist_relative, task_line),
                )
            )
    covered = {
        milestone
        for mapped in mappings.values()
        for milestone in mapped
        if milestone in known
    }
    for milestone in milestones:
        if milestone not in covered:
            findings.append(
                ValidationFinding(
                    TASKLIST_PLAN_MILESTONE_CODE,
                    f"Plan milestone `{milestone}` is not covered by any task card.",
                    "high",
                    ValidationIssueLocation(tasklist_relative),
                )
            )

    dependencies = {task.id: task.dependencies for task in task_plan.tasks}
    for task in task_plan.tasks:
        current_positions = [positions[item] for item in mappings[task.id] if item in positions]
        for dependency_id in task.dependencies:
            dependency_positions = [
                positions[item] for item in mappings.get(dependency_id, ()) if item in positions
            ]
            if (
                current_positions
                and dependency_positions
                and max(dependency_positions) > min(current_positions)
            ):
                findings.append(
                    ValidationFinding(
                        TASKLIST_PLAN_DEPENDENCY_CODE,
                        (
                            f"Task `{task.id}` depends on `{dependency_id}`, which maps to a later "
                            "plan milestone."
                        ),
                        "high",
                        ValidationIssueLocation(tasklist_relative),
                    )
                )

    for target, prerequisite in _milestone_dependencies(context.plan_text):
        if target not in known or prerequisite not in known:
            continue
        for task in task_plan.tasks:
            if target not in mappings[task.id]:
                continue
            if prerequisite in mappings[task.id] or _has_ancestor_milestone(
                task_id=task.id,
                milestone=prerequisite,
                dependencies=dependencies,
                task_milestones=mappings,
            ):
                continue
            findings.append(
                ValidationFinding(
                    TASKLIST_PLAN_DEPENDENCY_CODE,
                    (
                        f"Task `{task.id}` covers `{target}` but its dependency chain does not "
                        f"preserve plan prerequisite `{prerequisite}`."
                    ),
                    "high",
                    ValidationIssueLocation(tasklist_relative),
                )
            )
    for milestone, commands in _verification_commands(context.plan_text).items():
        mapped_verification = "\n".join(
            task.verification for task in task_plan.tasks if milestone in mappings[task.id]
        )
        for command in commands:
            if command not in mapped_verification:
                findings.append(
                    ValidationFinding(
                        TASKLIST_PLAN_VERIFICATION_CODE,
                        (
                            f"Tasks mapped to `{milestone}` must preserve authored verification "
                            f"command `{command}` exactly."
                        ),
                        "high",
                        ValidationIssueLocation(tasklist_relative),
                    )
                )
    return tuple(findings)
