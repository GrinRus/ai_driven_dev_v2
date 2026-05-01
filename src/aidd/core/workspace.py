from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.stages import STAGES

WORKSPACE_CONFIG_DIRNAME = "config"
WORKSPACE_REPORTS_DIRNAME = "reports"
WORKSPACE_TRACES_DIRNAME = "traces"
WORKSPACE_WORKITEMS_DIRNAME = "workitems"
WORKSPACE_REPORTS_RUNS_DIRNAME = "runs"
WORKSPACE_REPORTS_EVALS_DIRNAME = "evals"
WORKSPACE_TRACES_SESSIONS_DIRNAME = "sessions"
WORKSPACE_TRACES_REPLAYS_DIRNAME = "replays"

WORKITEM_CONTEXT_DIRNAME = "context"
WORKITEM_STAGES_DIRNAME = "stages"

STAGE_INPUT_DIRNAME = "input"
STAGE_OUTPUT_DIRNAME = "output"
DEFAULT_CONTRACT_REFERENCES_FILENAME = "default-contract-files.md"
WORKITEM_METADATA_FILENAME = "work-item.json"

RESERVED_STAGE_FILENAMES: tuple[str, ...] = (
    "stage-brief.md",
    "questions.md",
    "answers.md",
    "validator-report.md",
    "repair-brief.md",
    "stage-result.md",
)

_STAGE_FILE_TEMPLATES: dict[str, str] = {
    "questions.md": "# Questions\n\nNo questions yet.\n",
    "answers.md": "# Answers\n\nNo answers yet.\n",
    "validator-report.md": "# Validator report\n\nNo validator output yet.\n",
    "stage-result.md": "# Stage result\n\nStage not run yet.\n",
}


def workspace_workitems_root(root: Path) -> Path:
    return root / WORKSPACE_WORKITEMS_DIRNAME


def workspace_config_root(root: Path) -> Path:
    return root / WORKSPACE_CONFIG_DIRNAME


def workspace_reports_root(root: Path) -> Path:
    return root / WORKSPACE_REPORTS_DIRNAME


def workspace_traces_root(root: Path) -> Path:
    return root / WORKSPACE_TRACES_DIRNAME


def work_item_root(root: Path, work_item: str) -> Path:
    return workspace_workitems_root(root) / work_item


def work_item_context_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_CONTEXT_DIRNAME


def work_item_stages_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_STAGES_DIRNAME


def work_item_metadata_path(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_METADATA_FILENAME


def stage_root(root: Path, work_item: str, stage: str) -> Path:
    return work_item_stages_root(root=root, work_item=work_item) / stage


def stage_input_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_INPUT_DIRNAME


def stage_output_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_OUTPUT_DIRNAME


def create_workspace_tree(root: Path, work_item: str) -> Path:
    workspace_config_root(root).mkdir(parents=True, exist_ok=True)
    (workspace_reports_root(root) / WORKSPACE_REPORTS_RUNS_DIRNAME).mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_reports_root(root) / WORKSPACE_REPORTS_EVALS_DIRNAME).mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_traces_root(root) / WORKSPACE_TRACES_SESSIONS_DIRNAME).mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_traces_root(root) / WORKSPACE_TRACES_REPLAYS_DIRNAME).mkdir(
        parents=True,
        exist_ok=True,
    )

    item_root = work_item_root(root=root, work_item=work_item)
    work_item_context_root(root=root, work_item=work_item).mkdir(parents=True, exist_ok=True)

    for stage in STAGES:
        stage_input_root(root=root, work_item=work_item, stage=stage).mkdir(
            parents=True,
            exist_ok=True,
        )
        stage_output_root(root=root, work_item=work_item, stage=stage).mkdir(
            parents=True,
            exist_ok=True,
        )

    return item_root


def _starter_stage_file_contents(stage: str) -> dict[str, str]:
    stage_brief = (
        "# Stage\n\n"
        f"{stage}\n\n"
        "# Goal\n\n"
        "Describe the intended outcome for this stage run.\n\n"
        "# Inputs\n\n"
        "- none\n\n"
        "# Outputs\n\n"
        "- none\n\n"
        "# Constraints\n\n"
        "- keep output in Markdown\n\n"
        "# Open questions\n\n"
        "- none\n"
    )
    return {"stage-brief.md": stage_brief, **_STAGE_FILE_TEMPLATES}


def _default_contract_reference_paths() -> tuple[str, ...]:
    common_contracts = tuple(f"contracts/documents/{name}" for name in RESERVED_STAGE_FILENAMES)
    stage_contracts = tuple(f"contracts/stages/{stage}.md" for stage in STAGES)
    return common_contracts + stage_contracts


def seed_default_contract_references(root: Path, work_item: str) -> Path:
    references_path = work_item_context_root(root=root, work_item=work_item) / (
        DEFAULT_CONTRACT_REFERENCES_FILENAME
    )
    if references_path.exists():
        return references_path

    lines = [
        "# Default contract files",
        "",
        "The workspace is initialized with these contract references:",
        "",
    ]
    lines.extend(f"- `{path}`" for path in _default_contract_reference_paths())
    references_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return references_path


def seed_work_item_metadata(root: Path, work_item: str) -> Path:
    metadata_path = work_item_metadata_path(root=root, work_item=work_item)
    if metadata_path.exists():
        return metadata_path

    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {
        "schema_version": 1,
        "work_item_id": work_item,
        "created_at_utc": now,
        "updated_at_utc": now,
        "stage_order": list(STAGES),
    }
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata_path


def init_workspace(root: Path, work_item: str) -> Path:
    item_root = create_workspace_tree(root=root, work_item=work_item)
    seed_work_item_metadata(root=root, work_item=work_item)
    seed_default_contract_references(root=root, work_item=work_item)

    for stage in STAGES:
        stage_root_path = stage_root(root=root, work_item=work_item, stage=stage)
        for filename, content in _starter_stage_file_contents(stage).items():
            file_path = stage_root_path / filename
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    return item_root


@dataclass(frozen=True)
class WorkspaceBootstrapService:
    root: Path

    def bootstrap_work_item(self, work_item: str) -> Path:
        return init_workspace(root=self.root, work_item=work_item)
