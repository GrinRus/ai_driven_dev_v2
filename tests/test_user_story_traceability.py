from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.generate_user_story_traceability import (
    REGISTRY_RELATIVE_PATH,
    REQUIRED_GROUPS,
    VIEW_RELATIVE_PATH,
    TraceabilityRegistry,
    load_registry,
    main,
    render_view,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _registry_payload() -> dict[str, object]:
    payload = yaml.safe_load(
        (_repo_root() / REGISTRY_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    assert isinstance(payload, dict)
    return payload


def test_checked_in_traceability_view_matches_deterministic_render() -> None:
    repo_root = _repo_root()
    registry = load_registry(repo_root / REGISTRY_RELATIVE_PATH, repo_root=repo_root)
    view = render_view(registry)

    assert isinstance(registry, TraceabilityRegistry)
    assert view == render_view(registry)
    assert (repo_root / VIEW_RELATIVE_PATH).read_text(encoding="utf-8") == view
    for story in registry.stories:
        for group in REQUIRED_GROUPS:
            assert story.references[group]
            for reference in story.references[group]:
                assert f"[`{reference}`]" in view


def test_traceability_cli_check_rejects_stale_output(tmp_path: Path) -> None:
    output = tmp_path / "traceability.md"
    arguments = ["--output", str(output), "--write"]

    assert main(arguments) == 0
    original = output.read_bytes()
    assert main(["--output", str(output), "--check"]) == 0

    output.write_bytes(original + b"\n")
    assert main(["--output", str(output), "--check"]) == 1


@pytest.mark.parametrize("group", ("tests", "scenarios"))
def test_traceability_generation_rejects_missing_required_group(
    tmp_path: Path,
    group: str,
) -> None:
    payload = _registry_payload()
    stories = payload["stories"]
    assert isinstance(stories, list)
    first_story = stories[0]
    assert isinstance(first_story, dict)
    first_story[group] = []

    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match=rf"US-01 must declare non-empty {group} references"):
        load_registry(registry_path, repo_root=_repo_root())
    assert (
        main(
            [
                "--registry",
                str(registry_path),
                "--output",
                str(tmp_path / "traceability.md"),
                "--write",
            ]
        )
        == 1
    )


def test_traceability_generation_rejects_duplicate_reference(tmp_path: Path) -> None:
    payload = _registry_payload()
    stories = payload["stories"]
    assert isinstance(stories, list)
    first_story = stories[0]
    assert isinstance(first_story, dict)
    references = first_story["tests"]
    assert isinstance(references, list) and references
    first_story["tests"] = [references[0], references[0]]

    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="US-01.tests contains duplicate references"):
        load_registry(registry_path, repo_root=_repo_root())
