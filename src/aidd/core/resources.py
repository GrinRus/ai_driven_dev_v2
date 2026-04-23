from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_PACKAGED_RESOURCES_DIRNAME = "_resources"


@dataclass(frozen=True, slots=True)
class ResourceLayout:
    source: str
    root: Path
    contracts_root: Path
    stage_contracts_root: Path
    document_contracts_root: Path
    prompt_packs_root: Path


def _has_resource_tree(root: Path) -> bool:
    return (root / "contracts").is_dir() and (root / "prompt-packs").is_dir()


def _classify_resource_source(root: Path) -> str:
    if root.name == _PACKAGED_RESOURCES_DIRNAME:
        return "packaged"
    if _has_resource_tree(root) and (root / "pyproject.toml").exists():
        return "repository"
    return "custom"


def _repository_root_from(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if _has_resource_tree(candidate) and (candidate / "pyproject.toml").exists():
            return candidate
    return None


def _build_layout(*, root: Path) -> ResourceLayout:
    resolved_root = root.resolve(strict=False)
    return ResourceLayout(
        source=_classify_resource_source(resolved_root),
        root=resolved_root,
        contracts_root=resolved_root / "contracts",
        stage_contracts_root=resolved_root / "contracts" / "stages",
        document_contracts_root=resolved_root / "contracts" / "documents",
        prompt_packs_root=resolved_root / "prompt-packs",
    )


def resolve_resource_layout() -> ResourceLayout:
    package_root = Path(__file__).resolve(strict=False).parent.parent
    packaged_root = package_root / _PACKAGED_RESOURCES_DIRNAME
    if _has_resource_tree(packaged_root):
        return _build_layout(root=packaged_root)

    repository_root = _repository_root_from(package_root)
    if repository_root is not None:
        return _build_layout(root=repository_root)

    cwd_repository_root = _repository_root_from(Path.cwd().resolve(strict=False))
    if cwd_repository_root is not None:
        return _build_layout(root=cwd_repository_root)

    raise FileNotFoundError(
        "Could not resolve AIDD runtime resources. Expected packaged resources under "
        f"'{packaged_root.as_posix()}' or a repository checkout containing "
        "'contracts/' and 'prompt-packs/'."
    )


def resolve_resource_layout_from_contracts_root(contracts_root: Path) -> ResourceLayout:
    resolved_contracts_root = contracts_root.resolve(strict=False)
    if resolved_contracts_root.name != "stages":
        raise ValueError(
            "contracts_root must point to a stage contracts directory ending in "
            f"'contracts/stages': {resolved_contracts_root.as_posix()}"
        )
    if resolved_contracts_root.parent.name != "contracts":
        raise ValueError(
            "contracts_root must point to a stage contracts directory ending in "
            f"'contracts/stages': {resolved_contracts_root.as_posix()}"
        )
    return _build_layout(root=resolved_contracts_root.parent.parent)


def default_stage_contracts_root() -> Path:
    return resolve_resource_layout().stage_contracts_root


def default_document_contracts_root() -> Path:
    return resolve_resource_layout().document_contracts_root


def resolve_prompt_pack_path(*, prompt_reference: str, contracts_root: Path) -> Path:
    layout = resolve_resource_layout_from_contracts_root(contracts_root)
    relative_prompt_path = Path(prompt_reference)
    if relative_prompt_path.is_absolute():
        return relative_prompt_path.resolve(strict=False)
    return (layout.root / relative_prompt_path).resolve(strict=False)


__all__ = [
    "ResourceLayout",
    "default_document_contracts_root",
    "default_stage_contracts_root",
    "resolve_prompt_pack_path",
    "resolve_resource_layout",
    "resolve_resource_layout_from_contracts_root",
]
