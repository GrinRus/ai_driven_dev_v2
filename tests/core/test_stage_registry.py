from __future__ import annotations

from pathlib import Path

import pytest

from aidd.core.stage_registry import (
    StageManifestLoadError,
    all_stages,
    load_all_stage_manifests,
    load_stage_manifest,
)


def test_load_stage_manifest_parses_required_inputs_outputs(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    (contracts_root / "idea.md").write_text(
        "\n".join(
            [
                "# Stage Contract: `idea`",
                "",
                "## Purpose",
                "",
                "Shape the incoming request into a reviewable brief.",
                "",
                "## Primary output",
                "",
                "- `idea-brief.md`",
                "- `stage-result.md`",
                "",
                "## Required inputs",
                "",
                "- `context/intake.md`",
                "- `context/user-request.md`",
            ]
        )
        + "\n",
        encoding="utf-8",
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


def test_load_all_stage_manifests_reads_all_known_stages() -> None:
    manifests = load_all_stage_manifests()

    assert set(manifests) == set(all_stages())
    assert manifests["idea"].stage == "idea"
    assert manifests["qa"].stage == "qa"
