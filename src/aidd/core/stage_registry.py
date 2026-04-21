from __future__ import annotations

from pathlib import Path

from aidd.core.stage_manifest import StageManifest
from aidd.core.stages import STAGES, is_valid_stage

DEFAULT_STAGE_CONTRACTS_ROOT = Path("contracts/stages")


class StageManifestLoadError(ValueError):
    """Raised when a stage manifest cannot be loaded from contracts."""


def all_stages() -> tuple[str, ...]:
    return STAGES


def stage_contract_path(stage: str, contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT) -> Path:
    if not is_valid_stage(stage):
        raise StageManifestLoadError(f"Unknown stage: {stage}")
    return contracts_root / f"{stage}.md"


def _extract_section_lines(markdown_text: str, heading: str) -> list[str]:
    target_heading = f"## {heading}".lower()
    in_section = False
    section_lines: list[str] = []

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped.lower() == target_heading
            continue
        if in_section:
            section_lines.append(raw_line)

    return section_lines


def _extract_bullets(markdown_text: str, heading: str) -> tuple[str, ...]:
    items: list[str] = []
    for line in _extract_section_lines(markdown_text=markdown_text, heading=heading):
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        item = stripped.removeprefix("- ").strip().strip("`")
        if item:
            items.append(item)
    return tuple(items)


def _extract_paragraph(markdown_text: str, heading: str) -> str | None:
    lines = _extract_section_lines(markdown_text=markdown_text, heading=heading)
    parts = [line.strip() for line in lines if line.strip()]
    if not parts:
        return None
    return " ".join(parts)


def load_stage_manifest(
    stage: str,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> StageManifest:
    contract_path = stage_contract_path(stage=stage, contracts_root=contracts_root)
    if not contract_path.exists():
        raise StageManifestLoadError(f"Stage contract file not found: {contract_path}")

    markdown_text = contract_path.read_text(encoding="utf-8")
    required_inputs = _extract_bullets(markdown_text=markdown_text, heading="Required inputs")
    required_outputs = _extract_bullets(markdown_text=markdown_text, heading="Primary output")
    purpose = _extract_paragraph(markdown_text=markdown_text, heading="Purpose")

    try:
        return StageManifest.from_document_paths(
            stage=stage,
            required_inputs=required_inputs,
            required_outputs=required_outputs,
            purpose=purpose,
        )
    except ValueError as exc:
        raise StageManifestLoadError(
            f"Invalid stage contract model for stage '{stage}' at {contract_path}."
        ) from exc


def load_all_stage_manifests(
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> dict[str, StageManifest]:
    return {
        stage: load_stage_manifest(stage=stage, contracts_root=contracts_root)
        for stage in STAGES
    }
