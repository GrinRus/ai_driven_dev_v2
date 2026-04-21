from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES

WORKSPACE_CONFIG_DIRNAME = "config"
WORKSPACE_REPORTS_DIRNAME = "reports"
WORKSPACE_TRACES_DIRNAME = "traces"
WORKSPACE_WORKITEMS_DIRNAME = "workitems"

WORKITEM_CONTEXT_DIRNAME = "context"
WORKITEM_STAGES_DIRNAME = "stages"

STAGE_INPUT_DIRNAME = "input"
STAGE_OUTPUT_DIRNAME = "output"

RESERVED_STAGE_FILENAMES: tuple[str, ...] = (
    "questions.md",
    "answers.md",
    "validator-report.md",
    "repair-brief.md",
    "stage-result.md",
)

_RESERVED_STAGE_FILE_CONTENTS: dict[str, str] = {
    "questions.md": "# Questions\n\nNo questions yet.\n",
    "answers.md": "# Answers\n\nNo answers yet.\n",
    "validator-report.md": "# Validator report\n\nNo validator output yet.\n",
    "repair-brief.md": "# Repair brief\n\nNo repair requested yet.\n",
    "stage-result.md": "# Stage result\n\nStage not run yet.\n",
}


def workspace_workitems_root(root: Path) -> Path:
    return root / WORKSPACE_WORKITEMS_DIRNAME


def work_item_root(root: Path, work_item: str) -> Path:
    return workspace_workitems_root(root) / work_item


def work_item_context_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_CONTEXT_DIRNAME


def work_item_stages_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_STAGES_DIRNAME


def stage_root(root: Path, work_item: str, stage: str) -> Path:
    return work_item_stages_root(root=root, work_item=work_item) / stage


def stage_input_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_INPUT_DIRNAME


def stage_output_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_OUTPUT_DIRNAME


def init_workspace(root: Path, work_item: str) -> Path:
    item_root = work_item_root(root=root, work_item=work_item)
    work_item_context_root(root=root, work_item=work_item).mkdir(parents=True, exist_ok=True)

    for stage in STAGES:
        stage_root_path = stage_root(root=root, work_item=work_item, stage=stage)
        stage_input_root(root=root, work_item=work_item, stage=stage).mkdir(
            parents=True,
            exist_ok=True,
        )
        stage_output_root(root=root, work_item=work_item, stage=stage).mkdir(
            parents=True,
            exist_ok=True,
        )
        for filename, content in _RESERVED_STAGE_FILE_CONTENTS.items():
            file_path = stage_root_path / filename
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    return item_root
