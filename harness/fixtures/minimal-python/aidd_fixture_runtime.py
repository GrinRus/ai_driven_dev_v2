import os
import re
from pathlib import Path

VALIDATOR_REPORT = """# Validator Report

## Summary

- Total issues: 0

## Structural checks

- none

## Semantic checks

- none

## Cross-document checks

- none

## Result

- Verdict: `pass`
"""

QUESTIONS = "# Questions\n\n## Questions\n\n- none\n"
ANSWERS = "# Answers\n\n## Answers\n\n- none\n"


def _stage_result(stage: str, primary_output: str, project_set_evidence: str = "") -> str:
    next_stage = {
        "idea": "research",
        "research": "plan",
        "plan": "review-spec",
        "review-spec": "tasklist",
        "tasklist": "implement",
        "implement": "review",
        "review": "qa",
        "qa": "complete",
    }[stage]
    return f"""# Stage result

## Stage

{stage}

## Attempt history

- attempt-0001

## Status

succeeded

## Produced outputs

- {primary_output}

## Validation summary

- structural: pass
- semantic: pass

## Blockers

- none

## Next actions

- advance to `{next_stage}`

{project_set_evidence}
## Terminal state notes

Ready.
"""


def _project_set_evidence(workspace_root: Path, work_item: str) -> str:
    project_set_path = workspace_root / "workitems" / work_item / "context" / "project-set.md"
    if not project_set_path.exists():
        return ""
    project_set_relative_path = f"workitems/{work_item}/context/project-set.md"
    lines = [
        "## Project-set evidence",
        "",
        f"- Context: `{project_set_relative_path}`",
    ]
    for line in project_set_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", line.strip())
        if match is None:
            continue
        lines.append(
            f"- `{match.group(1)}` at `{match.group(2)}` retained deterministic stage evidence."
        )
    lines.append("")
    return "\n".join(lines)


def _idea_documents(project_set_evidence: str) -> dict[str, str]:
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
        "stage-result.md": _stage_result("idea", "idea-brief.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _research_documents(project_set_evidence: str) -> dict[str, str]:
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
        "stage-result.md": _stage_result("research", "research-notes.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _plan_documents(project_set_evidence: str) -> dict[str, str]:
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
        "stage-result.md": _stage_result("plan", "plan.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _review_spec_documents(project_set_evidence: str) -> dict[str, str]:
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
        "stage-result.md": _stage_result(
            "review-spec", "review-spec-report.md", project_set_evidence
        ),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _tasklist_documents(project_set_evidence: str) -> dict[str, str]:
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
        "stage-result.md": _stage_result("tasklist", "tasklist.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
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


def _implement_documents(
    workspace_root: Path,
    work_item: str,
    project_set_evidence: str,
) -> dict[str, str]:
    task_id = _selected_task(workspace_root, work_item)
    touched_path, acceptance_id = _apply_task_change(workspace_root.parent, task_id)
    return {
        "implementation-report.md": f"""# Implementation Report

## Summary

- Selected task: `{task_id}`.
- Completed `{task_id}` as a bounded deterministic fixture change for `{acceptance_id}`.

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
        "stage-result.md": _stage_result(
            "implement", "implementation-report.md", project_set_evidence
        ),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
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


def _review_documents(project_set_evidence: str) -> dict[str, str]:
    implementation_path = (
        "workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/"
        "implementation-report.md"
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
        "stage-result.md": _stage_result("review", "review-report.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _qa_documents(project_set_evidence: str) -> dict[str, str]:
    implementation_path = (
        "workitems/WI-DETERMINISTIC-TASKS/stages/implement/output/"
        "implementation-report.md"
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
        "stage-result.md": _stage_result("qa", "qa-report.md", project_set_evidence),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def main() -> None:
    stage = os.environ["AIDD_STAGE"]
    workspace_root = Path(os.environ["AIDD_WORKSPACE_ROOT"])
    work_item = os.environ["AIDD_WORK_ITEM"]
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    stage_root.mkdir(parents=True, exist_ok=True)
    project_set_evidence = _project_set_evidence(workspace_root, work_item)

    documents_by_stage = {
        "idea": _idea_documents,
        "research": _research_documents,
        "plan": _plan_documents,
        "review-spec": _review_spec_documents,
        "tasklist": _tasklist_documents,
        "review": _review_documents,
        "qa": _qa_documents,
    }
    if stage == "implement":
        documents = _implement_documents(workspace_root, work_item, project_set_evidence)
    else:
        documents = documents_by_stage[stage](project_set_evidence)

    for name, content in documents.items():
        (stage_root / name).write_text(content, encoding="utf-8")
    print(f"fixture-runtime stage={stage}")


if __name__ == "__main__":
    main()
