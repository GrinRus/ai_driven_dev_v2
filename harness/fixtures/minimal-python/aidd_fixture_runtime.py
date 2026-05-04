import os
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


def _stage_result(stage: str, primary_output: str) -> str:
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

- advance

## Terminal state notes

Ready.
"""


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
        "stage-result.md": _stage_result("idea", "idea-brief.md"),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
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
        "stage-result.md": _stage_result("research", "research-notes.md"),
        "validator-report.md": VALIDATOR_REPORT,
        "questions.md": QUESTIONS,
        "answers.md": ANSWERS,
    }


def _plan_documents() -> dict[str, str]:
    return {
        "plan.md": """# Plan

## Goals

- Preserve project-set evidence for `api` and `web` throughout the plan stage.

## Out of scope

- Multi-repository orchestration is excluded from this deterministic lane.

## Milestones

- M1: Persist project-set context in the work item context tree.
- M2: Include project-set context in stage brief and attempt input bundle evidence.

## Implementation strategy

- Deliver M1 before M2 so downstream artifacts can reference the same project ids.

## Risks

- R1: Project ownership can become ambiguous; mitigation: verify stable ids in artifact evidence.

## Dependencies

- Existing project-set resolver and stage preparation services.

## Verification approach

- Run deterministic harness checks against the fixture project roots.

## Verification notes

- M1: verify `project-set.md` lists both declared project ids.
- M2: verify `artifact-index.json` and `input-bundle.md` preserve project-set context.
""",
        "stage-result.md": _stage_result("plan", "plan.md"),
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

    documents_by_stage = {
        "idea": _idea_documents,
        "research": _research_documents,
        "plan": _plan_documents,
    }
    try:
        documents = documents_by_stage[stage]()
    except KeyError:
        documents = {
            "stage-result.md": _stage_result(stage, "stage-result.md"),
            "validator-report.md": VALIDATOR_REPORT,
            "questions.md": QUESTIONS,
            "answers.md": ANSWERS,
        }

    for name, content in documents.items():
        (stage_root / name).write_text(content, encoding="utf-8")
    print(f"fixture-runtime stage={stage}")


if __name__ == "__main__":
    main()
