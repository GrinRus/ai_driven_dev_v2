"""Deterministic runtime content only; AIDD owns workflow and interview records."""

import os
import re
from pathlib import Path


def _idea_documents() -> dict[str, str]:
    return {
        "idea-brief.md": """# Idea Brief

## Problem statement

Operators need deterministic project-set stage evidence that keeps declared project roots
visible across workflow artifacts.

## Desired outcome

Produce bounded idea, research, and plan evidence for the declared `api` and `web` project roots.

## Constraints

- Keep execution local to the repository workspace.
- Preserve project ids in downstream planning evidence.

## Open questions

- none
""",
    }


def _research_documents() -> dict[str, str]:
    return {
        "research-notes.md": """# Research Notes

## Scope

- Evaluate project-set evidence requirements for declared local roots.

## Sources

- [S1] docs/architecture/project-set-workspace.md (accessed 2026-05-04)

## Findings

- Project-set context must preserve stable project ids and local root ownership in artifacts [S1].

## Trade-offs

- none

## Evidence trace

- Project-set artifact ownership requirement -> [S1]

## Open questions

- none
""",
    }


def _plan_documents() -> dict[str, str]:
    return {
        "plan.md": """# Plan

## Goals

- Deliver three bounded fixture milestones while preserving project-set evidence.

## Out of scope

- Multi-repository orchestration is excluded from this deterministic lane.

## Milestones

- M1: Add a deterministic fixture marker.
- M2: Add a regression check for the marker.
- M3: Document the completed fixture behavior.

## Implementation strategy

- Deliver M1 before M2 and M2 before M3.

## Risks

- R1: Fixture evidence can drift; mitigation: run the authored checks after every task.

## Dependencies

- M2 depends on M1.
- M3 depends on M2.

## Verification approach

- Run `python -m pytest -q` after M1, M2, and M3.

## Verification notes

- M1: `python -m pytest -q`
- M2: `python -m pytest -q`
- M3: `python -m pytest -q`
""",
    }


def _project_set_plan_documents() -> dict[str, str]:
    return {
        "plan.md": """# Plan

## Goals

- Deliver bounded implementation evidence for both declared project roots.

## Out of scope

- Review and QA progression are excluded from this implement-stage deterministic lane.

## Milestones

- M1: Add the API project marker under `services/api`.
- M2: Add the web project marker under `apps/web`.

## Implementation strategy

- Complete M1 before M2 and preserve task-local diffs for aggregate finalization.

## Risks

- R1: An outside-root edit could invalidate the project-set boundary; mitigation: verify
  aggregate finalization against each task diff.

## Dependencies

- M1 precedes M2.

## Verification approach

- Run the authored root-marker checks and inspect task-local diffs after M1 and M2.

## Verification notes

- M1: inspect the API task diff and marker path.
- M2: inspect the web task diff and marker path.

## Open questions

- none
""",
    }


def _review_spec_documents() -> dict[str, str]:
    return {
        "review-spec-report.md": """# Review Spec Report

## Readiness state

- `ready`

## Issue list

- I1: Severity: info. Evidence: `plan.md` M1-M3. Rationale: because the bounded
  deterministic fixture plan is ready for task decomposition.

## Strengths

- The milestones are bounded and dependency ordered.
- Every milestone repeats the same deterministic verification command.

## Recommendation summary

- R1 (priority 1): Proceed to task decomposition without blocking changes.

## Required changes

- none

## Decision

- `approved`
""",
    }


def _tasklist_documents() -> dict[str, str]:
    return {
        "tasklist.md": """# Tasklist

## Task summary

Apply three dependency-ordered changes to the deterministic minimal fixture.

## Ordered tasks

### TL-1 — Add fixture marker

- Outcome: Milestone M1 is complete when `src/minimal_app/fixture_marker.py` exists.
- Dominant deliverable: `src/minimal_app/fixture_marker.py`.
- In scope: `src/minimal_app/fixture_marker.py`.
- Acceptance criteria:
  - TL-1-AC1: The marker module exports `fixture_marker`.

### TL-2 — Add marker regression

- Outcome: Milestone M2 is complete when the fixture marker has a regression test.
- Dominant deliverable: `tests/test_fixture_marker.py`.
- In scope: `tests/test_fixture_marker.py`.
- Acceptance criteria:
  - TL-2-AC1: The regression test asserts the deterministic marker value.

### TL-3 — Document fixture behavior

- Outcome: Milestone M3 is complete when `FIXTURE_EVIDENCE.md` documents the marker.
- Dominant deliverable: `FIXTURE_EVIDENCE.md`.
- In scope: `FIXTURE_EVIDENCE.md`.
- Acceptance criteria:
  - TL-3-AC1: The document names the deterministic marker.

## Dependencies

- TL-1: none
- TL-2: TL-1
- TL-3: TL-2

## Verification notes

- TL-1: `python -m pytest -q`
- TL-2: `python -m pytest -q`
- TL-3: `python -m pytest -q`
""",
    }


def _is_project_set_implementation(work_item: str) -> bool:
    return work_item.startswith("WI-DETERMINISTIC-PROJECT-SET-IMPLEMENT-")


def _project_set_is_negative(work_item: str) -> bool:
    return work_item.endswith("NEGATIVE")


def _project_set_tasklist_documents() -> dict[str, str]:
    return {
        "tasklist.md": """# Tasklist

## Task summary

Execute one dependency-ordered implementation change in each declared project root.

## Ordered tasks

### TL-1 — Add the API project marker

- Outcome: M1 is complete and the API project marker exists under the declared `services/api` root.
- Dominant deliverable: `services/api/project-marker.py`.
- In scope: `services/api`.
- Execution mode: repository-change
- Acceptance criteria:
  - TL-1-AC1: The API project marker exists at `services/api/project-marker.py`.
- Dependencies: none
- Verification: `test -f services/api/project-marker.py`

### TL-2 — Add the web project marker

- Outcome: M2 is complete and the web project marker is recorded, with an explicit
  outside-root probe in the negative fixture.
- Dominant deliverable: `apps/web/project-marker.js`.
- In scope: `apps/web` and the intentional probe path `outside`.
- Execution mode: repository-change
- Acceptance criteria:
  - TL-2-AC1: The web project marker exists under the declared `apps/web` root.
- Dependencies: TL-1
- Verification: `test -f apps/web/project-marker.js`

## Dependencies

- TL-1: none
- TL-2: TL-1

## Verification notes

- TL-1: the API root marker is created under the declared `services/api` root.
- TL-2: the web root marker is created under the declared `apps/web` root; the negative fixture
  also preserves an outside-root change for aggregate finalization to reject.
""",
    }


def _selected_task(workspace_root: Path, work_item: str) -> str:
    path = workspace_root / "workitems" / work_item / "context" / "task-selection.md"
    if not path.exists():
        return "TL-1"
    match = re.search(r"Task id:\s*`([^`]+)`", path.read_text(encoding="utf-8"))
    return match.group(1) if match is not None else "TL-1"


def _apply_task_change(project_root: Path, task_id: str) -> tuple[str, str]:
    if task_id == "TL-1":
        path = project_root / "src/minimal_app/fixture_marker.py"
        path.write_text('fixture_marker = "deterministic-ci"\n', encoding="utf-8")
        return "src/minimal_app/fixture_marker.py", "TL-1-AC1"
    if task_id == "TL-2":
        path = project_root / "tests/test_fixture_marker.py"
        path.write_text(
            "from minimal_app.fixture_marker import fixture_marker\n\n\n"
            "def test_fixture_marker() -> None:\n"
            '    assert fixture_marker == "deterministic-ci"\n',
            encoding="utf-8",
        )
        return "tests/test_fixture_marker.py", "TL-2-AC1"
    path = project_root / "FIXTURE_EVIDENCE.md"
    path.write_text(
        "# Fixture evidence\n\nThe deterministic marker is `deterministic-ci`.\n",
        encoding="utf-8",
    )
    return "FIXTURE_EVIDENCE.md", "TL-3-AC1"


def _apply_project_set_change(
    project_root: Path,
    task_id: str,
    *,
    negative: bool,
) -> tuple[tuple[str, ...], str, str]:
    if task_id == "TL-1":
        path = project_root / "services/api/project-marker.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('project = "api"\n', encoding="utf-8")
        return (
            (path.relative_to(project_root).as_posix(),),
            "TL-1-AC1",
            "test -f services/api/project-marker.py",
        )
    if negative:
        web_path = project_root / "apps/web/project-marker.js"
        web_path.parent.mkdir(parents=True, exist_ok=True)
        web_path.write_text('export const project = "web";\n', encoding="utf-8")
        outside_path = project_root / "outside/rogue-marker.txt"
        outside_path.parent.mkdir(parents=True, exist_ok=True)
        outside_path.write_text("outside project-set probe\n", encoding="utf-8")
        return (
            (
                web_path.relative_to(project_root).as_posix(),
                outside_path.relative_to(project_root).as_posix(),
            ),
            "TL-2-AC1",
            "test -f apps/web/project-marker.js",
        )
    path = project_root / "apps/web/project-marker.js"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('export const project = "web";\n', encoding="utf-8")
    return (
        (path.relative_to(project_root).as_posix(),),
        "TL-2-AC1",
        "test -f apps/web/project-marker.js",
    )


def _project_set_implementation_documents(
    workspace_root: Path,
    work_item: str,
) -> dict[str, str]:
    task_id = _selected_task(workspace_root, work_item)
    touched_paths, acceptance_id, verification = _apply_project_set_change(
        workspace_root.parent,
        task_id,
        negative=_project_set_is_negative(work_item),
    )
    touched_lines = "\n".join(
        f"- `{path}` - implementation evidence for `{task_id}`." for path in touched_paths
    )
    return {
        "implementation-report.md": f"""# Implementation Report

## Summary

- Selected task: `{task_id}`.
- Completed `{task_id}` as a project-set implementation change for `{acceptance_id}`.

## Acceptance evidence

- `{acceptance_id}`: `{verification}` -> pass; the task-local deliverable is present.

## Touched files

{touched_lines}

## Verification

- `{task_id}` `{acceptance_id}`: `{verification}` -> pass
- `git diff --name-only` -> pass; touched {", ".join(f"`{path}`" for path in touched_paths)}
- `git status --ignored --short --untracked-files=all` -> pass; no ignored residue created.

## Verification notes

- `{verification}` -> pass for `{task_id}` and `{acceptance_id}`.

## Risks

- none

## Follow-up

- none

## Follow-up notes

- none
""",
    }


def _implement_documents(
    workspace_root: Path,
    work_item: str,
) -> dict[str, str]:
    task_id = _selected_task(workspace_root, work_item)
    touched_path, acceptance_id = _apply_task_change(workspace_root.parent, task_id)
    return {
        "implementation-report.md": f"""# Implementation Report

## Summary

- Selected task: `{task_id}`.
- Completed `{task_id}` as a bounded deterministic fixture change for `{acceptance_id}`.

## Acceptance evidence

- `{acceptance_id}`: `python -m pytest -q` -> pass; the generated deliverable
  and regression evidence cover this criterion.

## Touched files

- `{touched_path}` - implement the selected fixture deliverable.

## Verification

- `{task_id}` `{acceptance_id}`: `python -m pytest -q` -> pass
- `git diff --name-only` -> pass; touched `{touched_path}`
- `git status --ignored --short --untracked-files=all` -> pass; no ignored residue created.

## Verification notes

- `python -m pytest -q` -> pass for `{task_id}` and `{acceptance_id}`.

## Risks

- none

## Follow-up

- none

## Follow-up notes

- none
""",
    }


def _task_acceptance_evidence(*, evidence_path: str, outcome: str) -> str:
    notes = (
        ("TL-1", "TL-1-AC1", f"Marker module {outcome}."),
        ("TL-2", "TL-2-AC1", f"Marker regression {outcome}."),
        ("TL-3", "TL-3-AC1", f"Fixture documentation {outcome}."),
    )
    return "\n".join(
        (
            f"- Task: `{task_id}`; Acceptance: `{acceptance_id}`; "
            f"Status: `pass`; Evidence: `{evidence_path}`; Notes: {note}"
        )
        for task_id, acceptance_id, note in notes
    )


def _review_documents() -> dict[str, str]:
    implementation_path = (
        "workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/implementation-report.md"
    )
    task_evidence = _task_acceptance_evidence(
        evidence_path=implementation_path,
        outcome="recorded",
    )
    return {
        "review-report.md": f"""# Review Report

## Verdict

- `approved`

## Findings

- none

## Risks

- none

## Required follow-up

- none

## Task acceptance evidence

{task_evidence}
""",
    }


def _qa_documents() -> dict[str, str]:
    implementation_path = (
        "workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/implementation-report.md"
    )
    task_evidence = _task_acceptance_evidence(
        evidence_path=implementation_path,
        outcome="verified",
    )
    return {
        "qa-report.md": f"""# QA Report

## Verification summary

- `workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/implementation-report.md`
  and `workitems/WI-DETERMINISTIC-TASKS/stages/review/output/review-report.md` were verified.

## Release recommendation

- `proceed`

## Evidence

- EV-1: `workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/implementation-report.md`
- EV-2: `workitems/WI-DETERMINISTIC-TASKS/stages/review/output/review-report.md`

## Known issues

- none

## Readiness

- QA verdict: `ready`.

## Task acceptance evidence

{task_evidence}
""",
    }


def main() -> None:
    stage = os.environ["AIDD_STAGE"]
    workspace_root = Path(os.environ["AIDD_WORKSPACE_ROOT"])
    work_item = os.environ["AIDD_WORK_ITEM"]
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    stage_root.mkdir(parents=True, exist_ok=True)

    documents_by_stage = {
        "idea": _idea_documents,
        "research": _research_documents,
        "plan": _plan_documents,
        "review-spec": _review_spec_documents,
        "tasklist": _tasklist_documents,
        "review": _review_documents,
        "qa": _qa_documents,
    }
    if _is_project_set_implementation(work_item) and stage == "plan":
        documents = _project_set_plan_documents()
    elif _is_project_set_implementation(work_item) and stage == "tasklist":
        documents = _project_set_tasklist_documents()
    elif _is_project_set_implementation(work_item) and stage == "implement":
        documents = _project_set_implementation_documents(workspace_root, work_item)
    elif stage == "implement":
        documents = _implement_documents(workspace_root, work_item)
    else:
        documents = documents_by_stage[stage]()

    print(f"fixture-runtime substantive-only writes={','.join(sorted(documents))}")
    for name, content in documents.items():
        (stage_root / name).write_text(content, encoding="utf-8")
    print(f"fixture-runtime stage={stage}")


if __name__ == "__main__":
    main()
