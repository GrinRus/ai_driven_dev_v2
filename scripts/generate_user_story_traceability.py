"""Generate and validate the checked-in user-story traceability view."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

import yaml  # type: ignore[import-untyped]

from aidd.core.contracts import repo_root_from

REGISTRY_RELATIVE_PATH = Path("docs/product/user-story-traceability.yaml")
VIEW_RELATIVE_PATH = Path("docs/product/user-story-traceability.md")
SOURCE_RELATIVE_PATH = "docs/product/user-stories.md"
REQUIRED_GROUPS: tuple[str, ...] = (
    "contracts",
    "code",
    "tests",
    "scenarios",
    "evidence",
)
_USER_STORY_ID_PATTERN = re.compile(r"^###\s+(US-\d+)\b", re.MULTILINE)


@dataclass(frozen=True)
class StoryTrace:
    """Validated traceability data for one product story."""

    story_id: str
    title: str
    assessment: str
    references: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class TraceabilityRegistry:
    """Validated registry content used by both the writer and the check gate."""

    schema_version: int
    source: str
    stories: tuple[StoryTrace, ...]


def _mapping(value: object, *, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a mapping")
    return cast(dict[str, object], value)


def _non_empty_text(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context} must be a non-empty string")
    return value.strip()


def _relative_file(path_text: str, *, repo_root: Path, context: str) -> None:
    path = Path(path_text)
    if path.is_absolute():
        raise ValueError(f"{context} must be repository-relative: {path_text}")
    repo_root_resolved = repo_root.resolve()
    resolved = (repo_root / path).resolve()
    if not resolved.is_relative_to(repo_root_resolved):
        raise ValueError(f"{context} escapes the repository: {path_text}")
    if not resolved.is_file():
        raise ValueError(f"{context} references missing file: {path_text}")


def load_registry(
    registry_path: Path,
    *,
    repo_root: Path,
) -> TraceabilityRegistry:
    """Load and validate a traceability registry against the product stories and files."""

    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Unable to read registry {registry_path}: {exc}") from exc
    root = _mapping(payload, context="registry")

    schema_version = root.get("schemaVersion")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise ValueError("registry.schemaVersion must be an integer")
    if schema_version != 1:
        raise ValueError(f"unsupported registry schemaVersion: {schema_version}")

    source = _non_empty_text(root.get("source"), context="registry.source")
    if source != SOURCE_RELATIVE_PATH:
        raise ValueError(f"registry.source must be {SOURCE_RELATIVE_PATH}, got {source}")
    _relative_file(source, repo_root=repo_root, context="registry.source")
    declared_story_ids = _USER_STORY_ID_PATTERN.findall(
        (repo_root / source).read_text(encoding="utf-8")
    )
    if not declared_story_ids:
        raise ValueError(f"{source} does not declare any user-story IDs")

    policy = _mapping(root.get("referencePolicy"), context="registry.referencePolicy")
    path_format = _non_empty_text(
        policy.get("pathFormat"), context="registry.referencePolicy.pathFormat"
    )
    if path_format != "repository-relative":
        raise ValueError("registry.referencePolicy.pathFormat must be repository-relative")
    raw_groups = policy.get("requiredGroups")
    if not isinstance(raw_groups, list) or tuple(raw_groups) != REQUIRED_GROUPS:
        raise ValueError(f"registry.referencePolicy.requiredGroups must be {list(REQUIRED_GROUPS)}")

    raw_stories = root.get("stories")
    if not isinstance(raw_stories, list):
        raise ValueError("registry.stories must be a list")
    if len(raw_stories) != len(declared_story_ids):
        raise ValueError(
            "registry.stories must contain exactly one entry for every declared story: "
            f"expected {len(declared_story_ids)}, got {len(raw_stories)}"
        )

    stories: list[StoryTrace] = []
    registry_ids: list[str] = []
    for index, raw_story in enumerate(raw_stories, start=1):
        story = _mapping(raw_story, context=f"registry.stories[{index}]")
        story_id = _non_empty_text(story.get("id"), context=f"registry.stories[{index}].id")
        registry_ids.append(story_id)
        title = _non_empty_text(story.get("title"), context=f"registry.stories[{index}].title")
        assessment = _non_empty_text(
            story.get("assessment"), context=f"registry.stories[{index}].assessment"
        )
        references: dict[str, tuple[str, ...]] = {}
        for group in REQUIRED_GROUPS:
            raw_references = story.get(group)
            if not isinstance(raw_references, list) or not raw_references:
                raise ValueError(f"{story_id} must declare non-empty {group} references")
            normalized: list[str] = []
            for ref_index, raw_reference in enumerate(raw_references, start=1):
                reference = _non_empty_text(
                    raw_reference,
                    context=f"{story_id}.{group}[{ref_index}]",
                )
                _relative_file(
                    reference,
                    repo_root=repo_root,
                    context=f"{story_id}.{group}[{ref_index}]",
                )
                normalized.append(reference)
            if len(normalized) != len(set(normalized)):
                raise ValueError(f"{story_id}.{group} contains duplicate references")
            references[group] = tuple(normalized)
        stories.append(
            StoryTrace(
                story_id=story_id,
                title=title,
                assessment=assessment,
                references=references,
            )
        )

    if registry_ids != declared_story_ids:
        raise ValueError(
            "registry story IDs must match docs/product/user-stories.md in order: "
            f"expected {declared_story_ids}, got {registry_ids}"
        )
    if len(registry_ids) != len(set(registry_ids)):
        raise ValueError("registry story IDs must be unique")

    return TraceabilityRegistry(
        schema_version=schema_version,
        source=source,
        stories=tuple(stories),
    )


def _escape_table_text(value: str) -> str:
    return " ".join(value.replace("|", "\\|").splitlines()).strip()


def _reference_link(reference: str) -> str:
    relative = PurePosixPath(os.path.relpath(reference, start=VIEW_RELATIVE_PATH.parent.as_posix()))
    return f"[`{reference}`]({relative.as_posix()})"


def render_view(registry: TraceabilityRegistry) -> str:
    """Render a deterministic Markdown view from validated registry data."""

    lines = [
        "<!-- Generated by scripts/generate_user_story_traceability.py; do not edit. -->",
        "# User-story traceability",
        "",
        "This view is generated from "
        "[`user-story-traceability.yaml`](./user-story-traceability.yaml)"
        f" (schema version `{registry.schema_version}`). The source stories are "
        "[`user-stories.md`](./user-stories.md).",
        "",
        "Every story must retain non-empty contract, code, test, scenario, and evidence "
        "references. Paths are repository-relative and are checked for existence in CI.",
        "",
        "## Coverage summary",
        "",
        "| Story | Title | Assessment | Contracts | Code | Tests | Scenarios | Evidence |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for story in registry.stories:
        counts = [str(len(story.references[group])) for group in REQUIRED_GROUPS]
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{story.story_id}`",
                    _escape_table_text(story.title),
                    f"`{_escape_table_text(story.assessment)}`",
                    *counts,
                )
            )
            + " |"
        )

    for story in registry.stories:
        lines.extend(
            (
                "",
                f"## {story.story_id} — {_escape_table_text(story.title)}",
                "",
                f"Assessment: `{_escape_table_text(story.assessment)}`",
                "",
            )
        )
        for group in REQUIRED_GROUPS:
            lines.extend((f"### {group.capitalize()}", ""))
            lines.extend(f"- {_reference_link(reference)}" for reference in story.references[group])
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _check_or_write(*, registry_path: Path, view_path: Path, repo_root: Path, write: bool) -> int:
    try:
        registry = load_registry(registry_path, repo_root=repo_root)
        rendered = render_view(registry).encode("utf-8")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"traceability generation failed: {exc}", file=sys.stderr)
        return 1

    if write:
        view_path.parent.mkdir(parents=True, exist_ok=True)
        view_path.write_bytes(rendered)
        print(f"wrote byte-stable traceability view: {view_path}")
        return 0

    try:
        existing = view_path.read_bytes()
    except OSError as exc:
        print(f"traceability view check failed: unable to read {view_path}: {exc}", file=sys.stderr)
        return 1
    if existing != rendered:
        print(
            "traceability view is stale or non-deterministic; run with --write to regenerate it",
            file=sys.stderr,
        )
        return 1
    print(f"traceability view is byte-stable: {view_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate or byte-check the user-story traceability Markdown view."
    )
    parser.add_argument("--registry", type=Path, default=REGISTRY_RELATIVE_PATH)
    parser.add_argument("--output", type=Path, default=VIEW_RELATIVE_PATH)
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the existing output (the default)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the generated output",
    )
    args = parser.parse_args(argv)
    if args.check and args.write:
        parser.error("--check and --write are mutually exclusive")
    repo_root = repo_root_from(Path(__file__).resolve())
    registry_path = args.registry if args.registry.is_absolute() else repo_root / args.registry
    view_path = args.output if args.output.is_absolute() else repo_root / args.output
    return _check_or_write(
        registry_path=registry_path,
        view_path=view_path,
        repo_root=repo_root,
        write=args.write,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
