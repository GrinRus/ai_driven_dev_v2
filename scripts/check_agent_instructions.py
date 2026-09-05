"""Check repository agent entrypoints, skill metadata, and concrete local references.

This is a structural check. It never executes documented commands, contacts providers,
or attempts to infer whether arbitrary prose agrees with product behavior.
It recognizes Markdown links and explicit inline repository/skill paths, excluding
fenced examples and generated runtime artifacts. Workflow tests cover command examples.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Iterator, Sequence
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml  # type: ignore[import-untyped]

_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
    }
)
_ROOT_PATH_PREFIXES = (
    ".agents/",
    ".github/",
    "src/",
    "tests/",
    "browser_tests/",
    "scripts/",
    "docs/",
    "contracts/",
    "prompt-packs/",
    "harness/",
)
_ROOT_FILENAMES = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "CONTRIBUTING.md",
        "Makefile",
        "pyproject.toml",
        "uv.lock",
    }
)
_LINK_RE = re.compile(
    r"\[[^\]\n]*\]\((<[^>\n]+>|[^\s)]+)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\)"
)
_REFERENCE_RE = re.compile(r"^\s*\[(?P<label>[^\]]+)\]:\s*(?P<target><[^>]+>|\S+)")
_REFERENCE_USE_RE = re.compile(r"\[([^\]\n]+)\]\[([^\]\n]*)\]")
_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _prose_lines(text: str) -> Iterator[tuple[int, str]]:
    """Skip fenced examples, retaining source line numbers for diagnostics."""
    fence: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker:
            run = marker[0]
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not stripped[len(run) :].strip():
                fence = None
            continue
        if fence is None:
            yield number, line


def _concrete_path(value: str) -> bool:
    return not any(character in value for character in "<>*?{$}") and "..." not in value


def _reference_target(root: Path, document: Path, value: str, *, code: bool) -> Path | None:
    value = value.strip("<>")
    # Inline code is checked only when it explicitly names a repository or skill path.
    # Names such as runtime.log and .aidd/... are generated artifacts, not repo references.
    if code:
        if not _concrete_path(value) or any(character.isspace() for character in value):
            return None
        if not (
            value.startswith((*_ROOT_PATH_PREFIXES, "references/", "./", "../"))
            or value in _ROOT_FILENAMES
            or value.endswith(("/AGENTS.md", "/SKILL.md"))
        ):
            return None
        value = re.sub(r":\d+(?:-\d+)?$", "", value)
        value = value.split("#", 1)[0]
        if value.startswith(_ROOT_PATH_PREFIXES):
            return root / value
        local = document.parent / value
        return local if local.exists() or value not in _ROOT_FILENAMES else root / value
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    path = unquote(parsed.path)
    return document.parent / path if _concrete_path(path) else None


def _skill_errors(path: Path, text: str) -> list[str]:
    if not text.startswith("---\n"):
        return ["missing YAML frontmatter"]
    match = re.search(r"^---\s*$", text[4:], re.MULTILINE)
    if match is None:
        return ["unclosed YAML frontmatter"]
    try:
        metadata = yaml.safe_load(text[4 : 4 + match.start()])
    except yaml.YAMLError as exc:
        return [f"invalid YAML frontmatter: {exc}"]
    if not isinstance(metadata, dict):
        return ["frontmatter must be a mapping"]
    errors: list[str] = []
    name = metadata.get("name")
    if not isinstance(name, str) or len(name) >= 64 or _NAME_RE.fullmatch(name) is None:
        errors.append(
            "name must be lowercase letters/digits/hyphens and shorter than 64 characters"
        )
    elif name != path.parent.name:
        errors.append(f"name {name!r} does not match directory {path.parent.name!r}")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("description must be a nonempty string")
    if not text[4 + match.end() :].strip():
        errors.append("skill body is empty")
    return errors


def instruction_documents(root: Path) -> tuple[Path, ...]:
    documents: set[Path] = set()
    for directory, directories, files in os.walk(root):
        directories[:] = [
            name
            for name in directories
            if name not in _IGNORED_DIRECTORIES and not name.startswith(".aidd")
        ]
        if "AGENTS.md" in files:
            documents.add(Path(directory) / "AGENTS.md")
    skills_root = root / ".agents" / "skills"
    documents.update(skills_root.rglob("*.md"))
    for relative in (
        "CLAUDE.md",
        "CONTRIBUTING.md",
        "docs/agent-development.md",
        ".github/pull_request_template.md",
    ):
        path = root / relative
        if path.is_file():
            documents.add(path)
    return tuple(sorted(documents))


def check_agent_instructions(root: Path) -> tuple[str, ...]:
    root = root.resolve()
    errors: list[str] = []
    for relative in ("AGENTS.md", "CLAUDE.md"):
        if not (root / relative).is_file():
            errors.append(f"{relative}: missing agent entrypoint")
    skills_root = root / ".agents" / "skills"
    if not skills_root.is_dir():
        errors.append(".agents/skills: missing skill directory")
    if skills_root.is_dir():
        skill_directories = [path for path in sorted(skills_root.iterdir()) if path.is_dir()]
        if not skill_directories:
            errors.append(".agents/skills: no skills discovered")
        for directory in skill_directories:
            if not (directory / "SKILL.md").is_file():
                errors.append(f"{directory.relative_to(root)}: missing SKILL.md")
    for document in instruction_documents(root):
        relative_path = document.relative_to(root)
        text = document.read_text(encoding="utf-8")
        if document.name == "SKILL.md":
            errors.extend(f"{relative_path}: {error}" for error in _skill_errors(document, text))
        prose = tuple(_prose_lines(text))
        reference_labels = {
            " ".join(match["label"].casefold().split())
            for _, line in prose
            if (match := _REFERENCE_RE.match(line))
        }
        for number, line in prose:
            markdown = _CODE_RE.sub("", line)
            references = [(match[1], False) for match in _LINK_RE.finditer(markdown)]
            if match := _REFERENCE_RE.match(markdown):
                references.append((match["target"], False))
            else:
                for match in _REFERENCE_USE_RE.finditer(markdown):
                    label = " ".join((match[2] or match[1]).casefold().split())
                    if label not in reference_labels:
                        errors.append(
                            f"{relative_path}:{number}: undefined reference label {label!r}"
                        )
            references.extend((match[1], True) for match in _CODE_RE.finditer(line))
            if document.name == "CLAUDE.md" and line.startswith("@"):
                references.append((line[1:].strip(), False))
            for value, code in references:
                target = _reference_target(root, document, value, code=code)
                if target is not None and not target.exists():
                    errors.append(f"{relative_path}:{number}: missing local reference {value!r}")
    return tuple(errors)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = check_agent_instructions(args.root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"checked {len(instruction_documents(args.root))} agent instruction documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
