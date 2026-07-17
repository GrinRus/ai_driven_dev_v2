from __future__ import annotations

import re
from dataclasses import dataclass

LOCAL_TASK_STATUSES = frozenset({"planned", "next", "soon", "parked", "blocked", "done"})
CONTAINER_STATUSES = frozenset({"planned", "done"})
BACKLOG_STATUS_BY_SECTION = {
    "Next": "next",
    "Soon": "soon",
    "Parking lot": "parked",
}

_WAVE_RE = re.compile(r"^## Wave (?P<wave>\d+) .*\(`(?P<status>[^`]+)`\)$")
_EPIC_RE = re.compile(r"^### Epic W(?P<wave>\d+)-E(?P<epic>\d+) .*\(`(?P<status>[^`]+)`\)$")
_SLICE_RE = re.compile(
    r"^#### Slice W(?P<wave>\d+)-E(?P<epic>\d+)-S(?P<slice>\d+) "
    r".*\(`(?P<status>[^`]+)`\)$"
)
_TASK_RE = re.compile(
    r"^- `(?P<id>W(?P<wave>\d+)-E(?P<epic>\d+)-S(?P<slice>\d+)-T(?P<task>\d+))` "
    r"\((?P<status>[^)]+)\) (?P<title>\S.*)$"
)
_LOCAL_TASK_ID_RE = re.compile(r"^W\d+-E\d+-S\d+-T\d+$")
_BACKLOG_ENTRY_RE = re.compile(r"^- `(?P<id>[^`]+)`")
_DEPENDENCY_RE = re.compile(r"W\d+-E\d+-S\d+-T\d+")


@dataclass(frozen=True)
class RoadmapTask:
    task_id: str
    wave: int
    epic: int
    slice: int
    task: int
    status: str
    dependencies: frozenset[str]


@dataclass(frozen=True)
class BacklogEntry:
    task_id: str
    section: str


def _task_blocks(lines: list[str]) -> list[tuple[re.Match[str], list[str]]]:
    starts = [
        (index, match)
        for index, line in enumerate(lines)
        if (match := _TASK_RE.match(line))
    ]
    return [
        (
            match,
            lines[
                index + 1 : starts[position + 1][0]
                if position + 1 < len(starts)
                else len(lines)
            ],
        )
        for position, (index, match) in enumerate(starts)
    ]


def parse_roadmap(roadmap: str) -> tuple[tuple[RoadmapTask, ...], tuple[str, ...]]:
    lines = roadmap.splitlines()
    errors: list[str] = []
    wave: int | None = None
    epic: int | None = None
    slice_number: int | None = None

    for line_number, line in enumerate(lines, start=1):
        if line.startswith("## Wave ") and not _WAVE_RE.match(line):
            errors.append(f"line {line_number}: malformed wave heading")
        elif line.startswith("### Epic ") and not _EPIC_RE.match(line):
            errors.append(f"line {line_number}: malformed epic heading")
        elif line.startswith("#### Slice ") and not _SLICE_RE.match(line):
            errors.append(f"line {line_number}: malformed slice heading")
        elif re.match(r"^- `W\d+-E\d+-S\d+-T\d+` [A-Z]", line):
            errors.append(f"line {line_number}: local task has no explicit status")

        if match := _WAVE_RE.match(line):
            wave = int(match["wave"])
            epic = None
            slice_number = None
            if match["status"] not in CONTAINER_STATUSES:
                errors.append(f"line {line_number}: invalid wave status {match['status']!r}")
        elif match := _EPIC_RE.match(line):
            if wave != int(match["wave"]):
                errors.append(f"line {line_number}: epic is outside its wave")
            epic = int(match["epic"])
            slice_number = None
            if match["status"] not in CONTAINER_STATUSES:
                errors.append(f"line {line_number}: invalid epic status {match['status']!r}")
        elif match := _SLICE_RE.match(line):
            if (wave, epic) != (int(match["wave"]), int(match["epic"])):
                errors.append(f"line {line_number}: slice is outside its epic")
            slice_number = int(match["slice"])
            if match["status"] not in CONTAINER_STATUSES:
                errors.append(f"line {line_number}: invalid slice status {match['status']!r}")
        elif match := _TASK_RE.match(line):
            identity = (int(match["wave"]), int(match["epic"]), int(match["slice"]))
            if (wave, epic, slice_number) != identity:
                errors.append(f"line {line_number}: task {match['id']} is outside its slice")
            if match["status"] not in LOCAL_TASK_STATUSES:
                errors.append(f"line {line_number}: invalid task status {match['status']!r}")

    tasks = tuple(
        RoadmapTask(
            task_id=match["id"],
            wave=int(match["wave"]),
            epic=int(match["epic"]),
            slice=int(match["slice"]),
            task=int(match["task"]),
            status=match["status"],
            dependencies=frozenset(
                dependency
                for line in block
                if line.strip().startswith("- Dependencies:")
                for dependency in _DEPENDENCY_RE.findall(line)
            ),
        )
        for match, block in _task_blocks(lines)
    )
    seen: set[str] = set()
    for task in tasks:
        if task.task_id in seen:
            errors.append(f"duplicate roadmap task definition: {task.task_id}")
        seen.add(task.task_id)
    return tasks, tuple(errors)


def parse_backlog(backlog: str) -> tuple[BacklogEntry, ...]:
    section: str | None = None
    entries: list[BacklogEntry] = []
    for line in backlog.splitlines():
        if line.startswith("## "):
            section = line.removeprefix("## ")
            continue
        if section in BACKLOG_STATUS_BY_SECTION and (match := _BACKLOG_ENTRY_RE.match(line)):
            entries.append(BacklogEntry(task_id=match["id"], section=section))
    return tuple(entries)


def roadmap_backlog_integrity_errors(roadmap: str, backlog: str) -> tuple[str, ...]:
    tasks, roadmap_errors = parse_roadmap(roadmap)
    errors = list(roadmap_errors)
    by_id = {task.task_id: task for task in tasks}
    entries = parse_backlog(backlog)
    queued_ids: set[str] = set()

    for entry in entries:
        if not _LOCAL_TASK_ID_RE.fullmatch(entry.task_id):
            errors.append(f"backlog entry is not a local task: {entry.task_id}")
            continue
        if entry.task_id in queued_ids:
            errors.append(f"duplicate backlog entry: {entry.task_id}")
        queued_ids.add(entry.task_id)
        task = by_id.get(entry.task_id)
        if task is None:
            errors.append(f"backlog task is absent from roadmap: {entry.task_id}")
            continue
        expected = BACKLOG_STATUS_BY_SECTION[entry.section]
        if task.status == "done":
            errors.append(f"terminal task is queued: {entry.task_id}")
        if task.status != expected:
            errors.append(
                f"backlog status mismatch for {entry.task_id}: "
                f"{entry.section} requires {expected}, "
                f"roadmap has {task.status}"
            )

    for task in tasks:
        if task.status in BACKLOG_STATUS_BY_SECTION.values() and task.task_id not in queued_ids:
            errors.append(f"queued roadmap status is absent from backlog: {task.task_id}")

    next_tasks = [
        by_id[entry.task_id]
        for entry in entries
        if entry.section == "Next" and entry.task_id in by_id
    ]
    soon_entries = (
        entry
        for entry in entries
        if entry.section == "Soon" and entry.task_id in by_id
    )
    for entry in soon_entries:
        task = by_id[entry.task_id]
        direct_successor = any(
            (
                (task.wave, task.epic, task.slice, task.task)
                == (current.wave, current.epic, current.slice, current.task + 1)
            )
            or (
                (task.wave, task.epic, task.slice, task.task)
                == (current.wave, current.epic, current.slice + 1, 1)
                and current.task
                == max(
                    candidate.task
                    for candidate in tasks
                    if (candidate.wave, candidate.epic, candidate.slice)
                    == (current.wave, current.epic, current.slice)
                )
            )
            for current in next_tasks
        )
        explicit_dependency = any(current.task_id in task.dependencies for current in next_tasks)
        if not direct_successor and not explicit_dependency:
            errors.append(f"Soon task is not a successor of Next: {task.task_id}")

    return tuple(errors)
