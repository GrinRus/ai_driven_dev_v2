from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copy2


@dataclass(frozen=True, slots=True)
class _ImportRule:
    category: str
    source_relative_dir: Path
    destination_relative_dir: Path
    allowed_suffixes: frozenset[str]


IMPORT_RULES: tuple[_ImportRule, ...] = (
    _ImportRule(
        category="contracts",
        source_relative_dir=Path("contracts/documents"),
        destination_relative_dir=Path("contracts/documents"),
        allowed_suffixes=frozenset({".md"}),
    ),
    _ImportRule(
        category="contracts",
        source_relative_dir=Path("contracts/stages"),
        destination_relative_dir=Path("contracts/stages"),
        allowed_suffixes=frozenset({".md"}),
    ),
    _ImportRule(
        category="prompt-packs",
        source_relative_dir=Path("prompt-packs"),
        destination_relative_dir=Path("prompt-packs"),
        allowed_suffixes=frozenset({".md", ".txt", ".yaml", ".yml"}),
    ),
    _ImportRule(
        category="scenarios",
        source_relative_dir=Path("harness/scenarios"),
        destination_relative_dir=Path("harness/scenarios"),
        allowed_suffixes=frozenset({".yaml", ".yml"}),
    ),
)

_ALLOWED_CATEGORIES = frozenset({rule.category for rule in IMPORT_RULES})
_BLOCKED_SEGMENTS = frozenset(
    {
        "hooks",
        ".hooks",
        "slash",
        "commands",
        ".claude",
        ".codex",
        ".opencode",
        ".pi-mono",
    }
)


@dataclass(frozen=True, slots=True)
class V1AssetImportSummary:
    copied_paths: tuple[Path, ...]
    skipped_existing_paths: tuple[Path, ...]
    skipped_blocked_paths: tuple[Path, ...]
    skipped_extension_paths: tuple[Path, ...]


def _normalize_include_categories(include_categories: tuple[str, ...] | None) -> frozenset[str]:
    if include_categories is None:
        return _ALLOWED_CATEGORIES

    normalized = frozenset(
        category.strip().lower() for category in include_categories if category.strip()
    )
    unknown = sorted(category for category in normalized if category not in _ALLOWED_CATEGORIES)
    if unknown:
        raise ValueError(
            "Unknown include category value(s): "
            + ", ".join(unknown)
            + ". Allowed: contracts, prompt-packs, scenarios."
        )
    if not normalized:
        raise ValueError("At least one include category must be provided.")
    return normalized


def _is_blocked_segment(segment: str) -> bool:
    normalized = segment.strip().lower()
    if normalized in _BLOCKED_SEGMENTS:
        return True
    return "hook" in normalized


def _contains_blocked_segment(relative_path: Path) -> bool:
    return any(_is_blocked_segment(part) for part in relative_path.parts)


def _iter_candidate_files(*, source_dir: Path) -> tuple[Path, ...]:
    if not source_dir.exists() or not source_dir.is_dir():
        return tuple()

    candidates: list[Path] = []
    for candidate in sorted(source_dir.rglob("*")):
        if not candidate.is_file():
            continue
        candidates.append(candidate)
    return tuple(candidates)


def import_v1_assets(
    *,
    source_root: Path,
    destination_root: Path,
    include_categories: tuple[str, ...] | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> V1AssetImportSummary:
    if not source_root.exists() or not source_root.is_dir():
        raise ValueError(f"source_root must be an existing directory: {source_root.as_posix()}")
    if destination_root.exists() and not destination_root.is_dir():
        raise ValueError(f"destination_root must be a directory: {destination_root.as_posix()}")
    destination_root.mkdir(parents=True, exist_ok=True)

    normalized_categories = _normalize_include_categories(include_categories)
    copied_paths: list[Path] = []
    skipped_existing_paths: list[Path] = []
    skipped_blocked_paths: list[Path] = []
    skipped_extension_paths: list[Path] = []

    for rule in IMPORT_RULES:
        if rule.category not in normalized_categories:
            continue

        source_dir = source_root / rule.source_relative_dir
        for source_path in _iter_candidate_files(
            source_dir=source_dir,
        ):
            if source_path.suffix.lower() not in rule.allowed_suffixes:
                skipped_extension_paths.append(source_path)
                continue
            relative_inside_rule = source_path.relative_to(source_dir)
            if _contains_blocked_segment(relative_inside_rule):
                skipped_blocked_paths.append(source_path)
                continue

            destination_path = (
                destination_root / rule.destination_relative_dir / relative_inside_rule
            ).resolve(strict=False)
            if destination_path.exists() and not overwrite:
                skipped_existing_paths.append(destination_path)
                continue

            copied_paths.append(destination_path)
            if dry_run:
                continue

            destination_path.parent.mkdir(parents=True, exist_ok=True)
            copy2(source_path, destination_path)

    return V1AssetImportSummary(
        copied_paths=tuple(copied_paths),
        skipped_existing_paths=tuple(skipped_existing_paths),
        skipped_blocked_paths=tuple(skipped_blocked_paths),
        skipped_extension_paths=tuple(skipped_extension_paths),
    )
