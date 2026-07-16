from __future__ import annotations

import hashlib
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path

from aidd.core.models.run import RunArtifactIndex
from aidd.core.stage_registry import resolve_prompt_pack_paths

_GIT_SHA_LENGTH = 40
_PACKAGE_NAME = "ai-driven-dev-v2"


def classify_resource_source(resource_root: Path) -> str:
    if resource_root.name == "_resources":
        return "packaged"
    if (resource_root / "contracts").is_dir() and (resource_root / "prompt-packs").is_dir():
        if (resource_root / "pyproject.toml").exists():
            return "repository"
        return "custom"
    return "custom"


def resolve_repository_git_sha(repository_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    candidate = completed.stdout.strip()
    if completed.returncode != 0 or len(candidate) != _GIT_SHA_LENGTH:
        return None
    if any(char not in "0123456789abcdef" for char in candidate.lower()):
        return None
    return candidate


def resolve_resource_revision(
    *,
    resource_root: Path,
    resource_source: str,
    repository_git_sha: str | None,
) -> str | None:
    if repository_git_sha is not None:
        return repository_git_sha
    if resource_source != "packaged":
        return None

    for revision_filename in ("RESOURCE_REVISION", "REVISION"):
        revision_path = resource_root / revision_filename
        if not revision_path.is_file():
            continue
        revision = revision_path.read_text(encoding="utf-8").strip()
        if revision:
            return revision
    try:
        return f"package:{package_version(_PACKAGE_NAME)}"
    except PackageNotFoundError:
        return None


def collect_prompt_pack_provenance(
    *,
    stage_target: str,
    contracts_root: Path,
    resource_root: Path,
) -> tuple[RunArtifactIndex.PromptPackProvenanceEntry, ...]:
    prompt_pack_paths = resolve_prompt_pack_paths(
        stage=stage_target,
        contracts_root=contracts_root,
    )
    return collect_prompt_file_provenance(
        prompt_pack_paths=tuple(
            (resource_root / prompt_path).resolve(strict=False) for prompt_path in prompt_pack_paths
        ),
        resource_root=resource_root,
    )


def collect_prompt_file_provenance(
    *,
    prompt_pack_paths: tuple[Path, ...],
    resource_root: Path,
) -> tuple[RunArtifactIndex.PromptPackProvenanceEntry, ...]:
    resolved_root = resource_root.resolve(strict=False)
    entries: list[RunArtifactIndex.PromptPackProvenanceEntry] = []
    for prompt_path in prompt_pack_paths:
        resolved_path = prompt_path.resolve(strict=False)
        if not resolved_path.is_relative_to(resolved_root):
            raise ValueError(f"Prompt pack path escapes resource root: {prompt_path}")
        entries.append(
            RunArtifactIndex.PromptPackProvenanceEntry(
                path=resolved_path.relative_to(resolved_root).as_posix(),
                sha256=_sha256_hex(resolved_path),
            )
        )
    return tuple(entries)


def _sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


__all__ = [
    "classify_resource_source",
    "collect_prompt_file_provenance",
    "collect_prompt_pack_provenance",
    "resolve_repository_git_sha",
    "resolve_resource_revision",
]
