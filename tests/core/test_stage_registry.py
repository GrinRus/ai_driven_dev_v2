from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.stage_registry import (
    StageManifestLoadError,
    all_stages,
    load_all_stage_manifests,
    load_stage_manifest,
    resolve_expected_output_documents,
    resolve_required_input_documents,
    resolve_validator_targets,
)


def _write_stage_contract(
    *,
    contracts_root: Path,
    stage: str,
    required_inputs: tuple[str, ...],
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    (contracts_root / f"{stage}.md").write_text(
        "\n".join(
            [
                f"# Stage Contract: `{stage}`",
                "",
                "## Purpose",
                "",
                "Shape the incoming request into a reviewable brief.",
                "",
                "## Primary output",
                "",
                *[f"- `{item}`" for item in required_outputs],
                "",
                "## Required inputs",
                "",
                *[f"- `{item}`" for item in required_inputs],
                "",
                "## Prompt pack",
                "",
                *[f"- `{item}`" for item in prompt_pack_paths],
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _touch_contract_references(
    *,
    repo_root: Path,
    required_outputs: tuple[str, ...],
    prompt_pack_paths: tuple[str, ...],
) -> None:
    documents_root = repo_root / "contracts" / "documents"
    documents_root.mkdir(parents=True, exist_ok=True)
    for output in required_outputs:
        (documents_root / output).write_text("# Contract\n", encoding="utf-8")

    for prompt_path in prompt_pack_paths:
        target = repo_root / prompt_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Prompt\n", encoding="utf-8")


def test_load_stage_manifest_parses_required_inputs_outputs(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md", "stage-result.md")
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="idea",
        required_inputs=("context/intake.md", "context/user-request.md"),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    manifest = load_stage_manifest(stage="idea", contracts_root=contracts_root)

    assert manifest.stage == "idea"
    assert manifest.purpose == "Shape the incoming request into a reviewable brief."
    assert manifest.required_input_paths == ("context/intake.md", "context/user-request.md")
    assert manifest.required_output_paths == ("idea-brief.md", "stage-result.md")


def test_load_stage_manifest_fails_when_contract_file_missing(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)

    with pytest.raises(StageManifestLoadError, match="not found"):
        load_stage_manifest(stage="idea", contracts_root=contracts_root)


def test_load_stage_manifest_fails_when_prompt_pack_reference_is_missing(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md", "stage-result.md")
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="idea",
        required_inputs=("context/intake.md", "context/user-request.md"),
        required_outputs=required_outputs,
        prompt_pack_paths=("prompt-packs/stages/idea/system.md",),
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=(),
    )

    with pytest.raises(StageManifestLoadError, match="missing prompt-pack path"):
        load_stage_manifest(stage="idea", contracts_root=contracts_root)


def test_load_stage_manifest_fails_when_document_contract_is_missing(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md", "stage-result.md")
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="idea",
        required_inputs=("context/intake.md", "context/user-request.md"),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=("stage-result.md",),
        prompt_pack_paths=prompt_paths,
    )

    with pytest.raises(StageManifestLoadError, match="missing document contract reference"):
        load_stage_manifest(stage="idea", contracts_root=contracts_root)


def test_load_all_stage_manifests_reads_all_known_stages() -> None:
    manifests = load_all_stage_manifests()

    assert set(manifests) == set(all_stages())
    assert manifests["idea"].stage == "idea"
    assert manifests["qa"].stage == "qa"


def test_resolve_required_input_documents_maps_context_and_upstream_paths(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"

    resolved = resolve_required_input_documents(
        stage="implement",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert resolved == (
        workspace_root / "workitems" / "WI-001" / "stages" / "tasklist" / "output" / "tasklist.md",
        workspace_root / "workitems" / "WI-001" / "context" / "repository-state.md",
    )


def test_resolve_required_input_documents_rejects_workspace_escape(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    required_outputs = ("idea-brief.md", "stage-result.md")
    prompt_paths = ("prompt-packs/stages/idea/system.md",)
    _write_stage_contract(
        contracts_root=contracts_root,
        stage="idea",
        required_inputs=("../../../../../outside.md",),
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )
    _touch_contract_references(
        repo_root=tmp_path,
        required_outputs=required_outputs,
        prompt_pack_paths=prompt_paths,
    )

    with pytest.raises(StageManifestLoadError, match="escapes workspace"):
        resolve_required_input_documents(
            stage="idea",
            work_item="WI-001",
            workspace_root=tmp_path / ".aidd",
            contracts_root=contracts_root,
        )


def test_resolve_expected_output_documents_and_validator_targets(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"

    expected_outputs = resolve_expected_output_documents(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
    )
    validator_targets = resolve_validator_targets(
        stage="idea",
        work_item="WI-001",
        workspace_root=workspace_root,
    )

    assert expected_outputs == (
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "idea-brief.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "stage-result.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "validator-report.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "repair-brief.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "questions.md",
        workspace_root / "workitems" / "WI-001" / "stages" / "idea" / "answers.md",
    )
    assert validator_targets == expected_outputs
