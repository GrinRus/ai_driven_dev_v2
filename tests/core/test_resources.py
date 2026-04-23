from __future__ import annotations

from pathlib import Path

from aidd.core.resources import (
    default_stage_contracts_root,
    resolve_prompt_pack_path,
    resolve_resource_layout,
    resolve_resource_layout_from_contracts_root,
)


def test_default_resource_layout_resolves_runtime_owned_assets() -> None:
    layout = resolve_resource_layout()

    assert layout.source in {"repository", "packaged"}
    assert layout.stage_contracts_root.exists()
    assert layout.document_contracts_root.exists()
    assert layout.prompt_packs_root.exists()


def test_default_stage_contracts_root_contains_known_stage_manifest() -> None:
    contracts_root = default_stage_contracts_root()

    assert contracts_root.exists()
    assert (contracts_root / "plan.md").exists()


def test_resolve_resource_layout_from_contracts_root_supports_custom_tree(
    tmp_path: Path,
) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    (tmp_path / "contracts" / "documents").mkdir(parents=True)
    (tmp_path / "prompt-packs" / "stages" / "plan").mkdir(parents=True)

    layout = resolve_resource_layout_from_contracts_root(contracts_root)

    assert layout.source == "custom"
    assert layout.root == tmp_path
    assert layout.stage_contracts_root == contracts_root


def test_resolve_prompt_pack_path_uses_resource_root_from_contracts_root(tmp_path: Path) -> None:
    contracts_root = tmp_path / "contracts" / "stages"
    contracts_root.mkdir(parents=True)
    prompt_path = tmp_path / "prompt-packs" / "stages" / "plan" / "system.md"
    prompt_path.parent.mkdir(parents=True)
    prompt_path.write_text("# Prompt\n", encoding="utf-8")

    resolved = resolve_prompt_pack_path(
        prompt_reference="prompt-packs/stages/plan/system.md",
        contracts_root=contracts_root,
    )

    assert resolved == prompt_path
