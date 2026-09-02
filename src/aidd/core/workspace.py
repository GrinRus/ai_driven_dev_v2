from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aidd.core.identifiers import (
    SafeIdentifier,
    contained_component_path,
    resolve_contained_component,
)
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
WORKITEM_CONTEXT_INTAKE_FILENAME = "intake.md"
WORKITEM_CONTEXT_USER_REQUEST_FILENAME = "user-request.md"
WORKITEM_CONTEXT_REPOSITORY_STATE_FILENAME = "repository-state.md"

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
REQUEST_CONTEXT_FILENAMES: tuple[str, ...] = (
    WORKITEM_CONTEXT_INTAKE_FILENAME,
    WORKITEM_CONTEXT_USER_REQUEST_FILENAME,
    WORKITEM_CONTEXT_REPOSITORY_STATE_FILENAME,
)

_STAGE_FILE_TEMPLATES: dict[str, str] = {
    "questions.md": "# Questions\n\nNo questions yet.\n",
    "answers.md": "# Answers\n\nNo answers yet.\n",
    "validator-report.md": "# Validator report\n\nNo validator output yet.\n",
    "stage-result.md": "# Stage result\n\nStage not run yet.\n",
}


def workspace_workitems_root(root: Path) -> Path:
    resolve_contained_component(
        root,
        WORKSPACE_WORKITEMS_DIRNAME,
        label="workspace workitems directory",
    )
    return root / WORKSPACE_WORKITEMS_DIRNAME


def workspace_config_root(root: Path) -> Path:
    return root / WORKSPACE_CONFIG_DIRNAME


def workspace_reports_root(root: Path) -> Path:
    return root / WORKSPACE_REPORTS_DIRNAME


def workspace_traces_root(root: Path) -> Path:
    return root / WORKSPACE_TRACES_DIRNAME


def work_item_root(root: Path, work_item: str) -> Path:
    workitems_root = workspace_workitems_root(root)
    safe_work_item = SafeIdentifier.parse(work_item, label="work_item")
    resolve_contained_component(
        workitems_root,
        safe_work_item.value,
        label="work_item",
    )
    return workitems_root / safe_work_item.value


def work_item_context_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_CONTEXT_DIRNAME


def work_item_stages_root(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_STAGES_DIRNAME


def work_item_metadata_path(root: Path, work_item: str) -> Path:
    return work_item_root(root=root, work_item=work_item) / WORKITEM_METADATA_FILENAME


def stage_root(root: Path, work_item: str, stage: str) -> Path:
    return contained_component_path(
        work_item_stages_root(root=root, work_item=work_item),
        stage,
        boundary_root=root,
        label="stage",
    )


def stage_input_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_INPUT_DIRNAME


def stage_output_root(root: Path, work_item: str, stage: str) -> Path:
    return stage_root(root=root, work_item=work_item, stage=stage) / STAGE_OUTPUT_DIRNAME


def create_workspace_tree(root: Path, work_item: str) -> Path:
    item_root = work_item_root(root=root, work_item=work_item)
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
    operator_contracts = (
        "contracts/documents/operator-request.md",
        "contracts/documents/user-request.md",
    )
    stage_contracts = tuple(f"contracts/stages/{stage}.md" for stage in STAGES)
    return common_contracts + operator_contracts + stage_contracts


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
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

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


@dataclass(frozen=True, slots=True)
class WorkItemContextSeedResult:
    intake_path: Path
    user_request_path: Path
    repository_state_path: Path
    overwritten: bool

    @property
    def paths(self) -> tuple[Path, Path, Path]:
        return (
            self.intake_path,
            self.user_request_path,
            self.repository_state_path,
        )


def _normalized_request_text(request_text: str) -> str:
    normalized = request_text.strip()
    if not normalized:
        raise ValueError("Request text must be non-empty.")
    return normalized


def _relative_workspace_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _render_intake_markdown(*, work_item: str, request_text: str) -> str:
    return (
        "# Intake\n\n"
        "## Work item\n\n"
        f"- `{work_item}`\n\n"
        "## Operator request\n\n"
        f"{request_text}\n\n"
        "## Context documents\n\n"
        "- `user-request.md` preserves the original request text.\n"
        "- `repository-state.md` captures the local project root observed during init.\n"
    )


def _request_body_from_markdown(markdown: str) -> str:
    lines = markdown.splitlines()
    if lines and lines[0].strip().casefold() == "# user request":
        lines = lines[1:]
    return "\n".join(lines).strip()


def _render_user_request_markdown(
    *,
    request_text: str,
    title: str | None = None,
    brief: str | None = None,
    context: str | None = None,
    constraints: str | None = None,
    additional_information: str | None = None,
) -> str:
    if (
        title is None
        and brief is None
        and context is None
        and constraints is None
        and additional_information is None
    ):
        return "# User request\n\n" f"{request_text}\n"

    normalized_title = (title or "").strip()
    normalized_brief = (brief if brief is not None else request_text).strip()
    if not normalized_brief:
        raise ValueError("Request brief must be non-empty for structured request context.")
    if not normalized_title:
        normalized_title = normalized_brief.splitlines()[0].strip()[:160]
    if not normalized_title:
        raise ValueError("Request title must be non-empty for structured request context.")
    sections = [
        ("Title", normalized_title),
        ("Brief", normalized_brief),
    ]
    for heading, value in (
        ("Context", context),
        ("Constraints", constraints),
        ("Additional information", additional_information),
    ):
        normalized = (value or "").strip()
        if normalized:
            sections.append((heading, normalized))
    body = "\n\n".join(f"## {heading}\n\n{value}" for heading, value in sections)
    return "# User request\n\n" f"{body}\n"


def _render_repository_state_markdown(
    *,
    project_root: Path | None,
    workspace_root: Path,
) -> str:
    project_root_line = (
        "- Project root: not recorded\n"
        if project_root is None
        else f"- Project root: `{project_root.resolve(strict=False).as_posix()}`\n"
    )
    return (
        "# Repository state\n\n"
        "## Init snapshot\n\n"
        f"{project_root_line}"
        f"- AIDD workspace root: `{workspace_root.resolve(strict=False).as_posix()}`\n"
        "- Source: `aidd init --request` or `aidd init --request-file`\n"
    )


def seed_work_item_context(
    *,
    root: Path,
    work_item: str,
    request_text: str,
    project_root: Path | None = None,
    force: bool = False,
    request_title: str | None = None,
    request_brief: str | None = None,
    request_context: str | None = None,
    request_constraints: str | None = None,
    request_additional_information: str | None = None,
) -> WorkItemContextSeedResult:
    normalized_request = _normalized_request_text(
        request_brief if request_brief is not None else request_text
    )
    context_root = work_item_context_root(root=root, work_item=work_item)
    context_root.mkdir(parents=True, exist_ok=True)
    target_paths = tuple(context_root / filename for filename in REQUEST_CONTEXT_FILENAMES)
    existing_paths = tuple(path for path in target_paths if path.exists())
    if existing_paths and not force:
        existing = ", ".join(_relative_workspace_path(root, path) for path in existing_paths)
        raise FileExistsError(
            "Request context documents already exist for work item "
            f"'{work_item}': {existing}. Use --force-context to overwrite them."
        )

    intake_path = context_root / WORKITEM_CONTEXT_INTAKE_FILENAME
    user_request_path = context_root / WORKITEM_CONTEXT_USER_REQUEST_FILENAME
    repository_state_path = context_root / WORKITEM_CONTEXT_REPOSITORY_STATE_FILENAME
    user_request_markdown = _render_user_request_markdown(
        request_text=normalized_request,
        title=request_title,
        brief=request_brief,
        context=request_context,
        constraints=request_constraints,
        additional_information=request_additional_information,
    )
    user_request_path.write_text(user_request_markdown, encoding="utf-8")
    intake_path.write_text(
        _render_intake_markdown(
            work_item=work_item,
            request_text=_request_body_from_markdown(user_request_markdown),
        ),
        encoding="utf-8",
    )
    repository_state_path.write_text(
        _render_repository_state_markdown(project_root=project_root, workspace_root=root),
        encoding="utf-8",
    )
    return WorkItemContextSeedResult(
        intake_path=intake_path,
        user_request_path=user_request_path,
        repository_state_path=repository_state_path,
        overwritten=bool(existing_paths),
    )


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

    def seed_request_context(
        self,
        *,
        work_item: str,
        request_text: str,
        project_root: Path | None = None,
        force: bool = False,
        request_title: str | None = None,
        request_brief: str | None = None,
        request_context: str | None = None,
        request_constraints: str | None = None,
        request_additional_information: str | None = None,
    ) -> WorkItemContextSeedResult:
        return seed_work_item_context(
            root=self.root,
            work_item=work_item,
            request_text=request_text,
            project_root=project_root,
            force=force,
            request_title=request_title,
            request_brief=request_brief,
            request_context=request_context,
            request_constraints=request_constraints,
            request_additional_information=request_additional_information,
        )
