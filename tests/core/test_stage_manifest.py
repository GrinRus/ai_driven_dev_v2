from __future__ import annotations

import pytest

from aidd.core.stage_manifest import StageDocumentDeclaration, StageManifest


def test_stage_manifest_from_document_paths_exposes_required_path_lists() -> None:
    manifest = StageManifest.from_document_paths(
        stage="plan",
        required_inputs=("workitems/WI-001/stages/research/research-report.md",),
        required_outputs=("workitems/WI-001/stages/plan/plan.md", "stage-result.md"),
        purpose="Convert research findings into an execution plan.",
    )

    assert manifest.stage == "plan"
    assert manifest.purpose == "Convert research findings into an execution plan."
    assert manifest.required_input_paths == (
        "workitems/WI-001/stages/research/research-report.md",
    )
    assert manifest.required_output_paths == (
        "workitems/WI-001/stages/plan/plan.md",
        "stage-result.md",
    )


def test_stage_manifest_rejects_unknown_stage() -> None:
    with pytest.raises(ValueError, match="Unknown stage"):
        StageManifest.from_document_paths(
            stage="unknown-stage",
            required_inputs=("context/intake.md",),
            required_outputs=("idea-brief.md",),
        )


def test_stage_manifest_rejects_duplicate_required_documents() -> None:
    with pytest.raises(ValueError, match="Duplicate document declaration"):
        StageManifest.from_document_paths(
            stage="idea",
            required_inputs=("context/intake.md", "context/intake.md"),
            required_outputs=("idea-brief.md",),
        )

    with pytest.raises(ValueError, match="Duplicate document declaration"):
        StageManifest.from_document_paths(
            stage="idea",
            required_inputs=("context/intake.md",),
            required_outputs=("idea-brief.md", "idea-brief.md"),
        )


def test_stage_document_declaration_rejects_empty_or_absolute_path() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        StageDocumentDeclaration(path="  ")

    with pytest.raises(ValueError, match="must be relative"):
        StageDocumentDeclaration(path="/abs/path.md")


def test_stage_manifest_requires_input_and_output_declarations() -> None:
    with pytest.raises(ValueError, match="at least one required input"):
        StageManifest.from_document_paths(
            stage="plan",
            required_inputs=(),
            required_outputs=("plan.md",),
        )

    with pytest.raises(ValueError, match="at least one required output"):
        StageManifest.from_document_paths(
            stage="plan",
            required_inputs=("research.md",),
            required_outputs=(),
        )
