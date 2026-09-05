from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_agent_instructions import check_agent_instructions, main


def _workspace(
    root: Path, *, metadata: str = "name: sample\ndescription: Inspect local evidence."
) -> Path:
    (root / "AGENTS.md").write_text("# Repository rules\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    skill = root / ".agents/skills/sample/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(f"---\n{metadata}\n---\n\nRead local evidence.\n", encoding="utf-8")
    return skill


def test_repository_agent_instructions_are_structurally_valid() -> None:
    assert check_agent_instructions(Path(__file__).resolve().parents[1]) == ()


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ("name: wrong\ndescription: Valid", "does not match directory"),
        ("name: UPPER\ndescription: Valid", "name must be lowercase"),
        ("name: sample\ndescription: []", "description must be a nonempty string"),
        ("name: sample\ndescription: ' '", "description must be a nonempty string"),
        ("name: [", "invalid YAML"),
        ("- sample", "frontmatter must be a mapping"),
    ],
)
def test_invalid_skill_metadata_reports_actionable_errors(
    tmp_path: Path,
    metadata: str,
    expected: str,
) -> None:
    _workspace(tmp_path, metadata=metadata)
    assert any(expected in error for error in check_agent_instructions(tmp_path))


@pytest.mark.parametrize("text", ["# No metadata\n", "---\nname: sample\n"])
def test_skill_frontmatter_is_required_and_closed(tmp_path: Path, text: str) -> None:
    skill = _workspace(tmp_path)
    skill.write_text(text, encoding="utf-8")
    assert any("frontmatter" in error for error in check_agent_instructions(tmp_path))


def test_local_reference_resolution_and_fenced_examples(tmp_path: Path) -> None:
    skill = _workspace(tmp_path)
    reference = skill.parent / "references/guide with spaces.md"
    reference.parent.mkdir()
    reference.write_text("Read `AGENTS.md`.\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/owned.py").touch()
    with skill.open("a", encoding="utf-8") as handle:
        handle.write(
            "[Guide](<references/guide with spaces.md>)\n"
            "[Encoded guide](references/guide%20with%20spaces.md)\n"
            "[Source](../../../src/owned.py#section) and `src/owned.py:12`.\n"
            "[Remote](https://example.invalid/unreachable) and [Section](#section).\n"
            "Read `runtime.log`, `.aidd/reports/example.md`, and `docs/<task>.md`.\n"
            "```markdown\n[Generated output](missing.md)\n`src/missing.py`\n```\n"
        )
    assert check_agent_instructions(tmp_path) == ()
    reference.unlink()
    errors = check_agent_instructions(tmp_path)
    assert len(errors) == 2
    assert all("missing local reference" in error and "SKILL.md:" in error for error in errors)


def test_reference_definitions_and_skill_inline_paths_are_checked(tmp_path: Path) -> None:
    skill = _workspace(tmp_path)
    with skill.open("a", encoding="utf-8") as handle:
        handle.write("[Guide][guide]\n[guide]: references/missing.md\nRead `src/missing.py`.\n")
    errors = check_agent_instructions(tmp_path)
    assert len(errors) == 2
    assert any("references/missing.md" in error for error in errors)
    assert any("src/missing.py" in error for error in errors)


@pytest.mark.parametrize(
    "reference",
    (
        "[Guide](references/missing.md?view=raw)",
        "[Guide](references/missing.md 'Guide title')",
        '[Guide](references/missing.md "Guide title")',
        "[Guide](references/missing.md (Guide title))",
        "[Guide][missing]",
        "[Guide][]",
    ),
)
def test_markdown_reference_variants_cannot_hide_missing_targets(
    tmp_path: Path,
    reference: str,
) -> None:
    skill = _workspace(tmp_path)
    with skill.open("a", encoding="utf-8") as handle:
        handle.write(reference + "\n")
    assert check_agent_instructions(tmp_path)


def test_reference_labels_are_case_insensitive_and_inline_examples_are_ignored(
    tmp_path: Path,
) -> None:
    skill = _workspace(tmp_path)
    with skill.open("a", encoding="utf-8") as handle:
        handle.write(
            "[Repo][REPO rules]\n[repo rules]: ../../../AGENTS.md\n"
            "Literal syntax: `[Example](missing.md)` and `[Example][missing]`.\n"
        )
    assert check_agent_instructions(tmp_path) == ()


def test_missing_skill_entrypoint_and_claude_import_fail(tmp_path: Path) -> None:
    skill = _workspace(tmp_path)
    skill.unlink()
    (tmp_path / "CLAUDE.md").write_text("@missing.md\n", encoding="utf-8")
    errors = check_agent_instructions(tmp_path)
    assert any("missing SKILL.md" in error for error in errors)
    assert any("missing.md" in error for error in errors)


def test_cli_reports_failure_without_executing_documented_commands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    skill = _workspace(tmp_path)
    with skill.open("a", encoding="utf-8") as handle:
        handle.write("```bash\ntouch DO-NOT-CREATE\n```\nRead `src/absent.py`.\n")
    assert main(["--root", str(tmp_path)]) == 1
    assert "missing local reference" in capsys.readouterr().err
    assert not (tmp_path / "DO-NOT-CREATE").exists()
